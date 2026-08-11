"""
Tests for tail-error metrics in dosemetrics.metrics.dose_comparison.

Covers ``compare_max_error``, ``compare_error_percentile``,
``compare_tail_error`` and ``compute_isolated_extrema``.

These metrics exist because a mean over millions of voxels cannot see a small
number of badly wrong ones, so the tests that matter most are the ones pinning
that distinction: a single large deviation must move the tail metrics while
leaving MAE almost unchanged, and salt-and-pepper speckle must be detected in a
distribution whose agreement with a reference is otherwise good.
"""

import numpy as np
import pytest

from dosemetrics.dose import Dose
from dosemetrics.metrics import dose_comparison
from dosemetrics.structures import Target


SPACING = (2.0, 2.0, 3.0)
ORIGIN = (0.0, 0.0, 0.0)


@pytest.fixture
def flat_dose():
    """Uniform 50 Gy distribution."""
    return Dose(np.full((20, 20, 10), 50.0), SPACING, ORIGIN)


@pytest.fixture
def spiked_dose():
    """Uniform 50 Gy with one voxel 30 Gy too high."""
    arr = np.full((20, 20, 10), 50.0)
    arr[10, 10, 5] = 80.0
    return Dose(arr, SPACING, ORIGIN)


@pytest.fixture
def target_structure():
    """A Target covering part of the grid."""
    mask = np.zeros((20, 20, 10), dtype=bool)
    mask[5:15, 5:15, 2:8] = True
    return Target("PTV", mask)


class TestCompareMaxError:
    def test_identical_doses_give_zero(self, flat_dose):
        assert dose_comparison.compare_max_error(flat_dose, flat_dose) == 0.0

    def test_finds_the_single_worst_voxel(self, flat_dose, spiked_dose):
        assert dose_comparison.compare_max_error(flat_dose, spiked_dose) == 30.0

    def test_is_symmetric(self, flat_dose, spiked_dose):
        a = dose_comparison.compare_max_error(flat_dose, spiked_dose)
        b = dose_comparison.compare_max_error(spiked_dose, flat_dose)
        assert a == b

    def test_never_below_mae(self, flat_dose, spiked_dose):
        mae = dose_comparison.compare_mae(flat_dose, spiked_dose)
        assert dose_comparison.compare_max_error(flat_dose, spiked_dose) >= mae

    def test_structure_restricts_the_search(self, flat_dose, target_structure):
        """A spike outside the structure must not be reported."""
        arr = np.full((20, 20, 10), 50.0)
        arr[0, 0, 0] = 90.0  # outside the target mask
        outside = Dose(arr, SPACING, ORIGIN)
        assert dose_comparison.compare_max_error(flat_dose, outside) == 40.0
        assert (
            dose_comparison.compare_max_error(
                flat_dose, outside, structure=target_structure
            )
            == 0.0
        )

    def test_shape_mismatch_raises(self, flat_dose):
        other = Dose(np.zeros((5, 5, 5)), SPACING, ORIGIN)
        with pytest.raises(ValueError, match="shapes must match"):
            dose_comparison.compare_max_error(flat_dose, other)


class TestCompareErrorPercentile:
    def test_percentile_100_equals_max_error(self, flat_dose, spiked_dose):
        p100 = dose_comparison.compare_error_percentile(
            flat_dose, spiked_dose, percentile=100.0
        )
        mx = dose_comparison.compare_max_error(flat_dose, spiked_dose)
        assert p100 == pytest.approx(mx)

    def test_single_spike_leaves_low_percentiles_at_zero(self, flat_dose, spiked_dose):
        """One voxel in 4000 is far below the 99th percentile."""
        assert (
            dose_comparison.compare_error_percentile(
                flat_dose, spiked_dose, percentile=99.0
            )
            == 0.0
        )

    def test_monotone_in_percentile(self, flat_dose):
        rng = np.random.default_rng(0)
        noisy = Dose(np.full((20, 20, 10), 50.0) + rng.normal(0, 2, (20, 20, 10)),
                     SPACING, ORIGIN)
        values = [
            dose_comparison.compare_error_percentile(flat_dose, noisy, percentile=p)
            for p in (50.0, 75.0, 90.0, 99.0, 100.0)
        ]
        assert all(a <= b + 1e-9 for a, b in zip(values, values[1:])), values

    @pytest.mark.parametrize("bad", [-1.0, 100.5])
    def test_out_of_range_percentile_raises(self, flat_dose, spiked_dose, bad):
        with pytest.raises(ValueError, match="percentile must be"):
            dose_comparison.compare_error_percentile(
                flat_dose, spiked_dose, percentile=bad
            )


class TestCompareTailError:
    def test_fraction_one_equals_mae(self, flat_dose):
        rng = np.random.default_rng(1)
        noisy = Dose(np.full((20, 20, 10), 50.0) + rng.normal(0, 3, (20, 20, 10)),
                     SPACING, ORIGIN)
        tail = dose_comparison.compare_tail_error(flat_dose, noisy, fraction=1.0)
        mae = dose_comparison.compare_mae(flat_dose, noisy)
        assert tail == pytest.approx(mae)

    def test_equals_mean_of_worst_k(self, flat_dose):
        """Construct a distribution whose worst 10% is known exactly."""
        arr = np.full(1000, 50.0)
        arr[:100] = 60.0  # exactly 10% of voxels are 10 Gy off
        evaluated = Dose(arr.reshape(10, 10, 10), (1.0, 1.0, 1.0), ORIGIN)
        reference = Dose(np.full((10, 10, 10), 50.0), (1.0, 1.0, 1.0), ORIGIN)
        assert dose_comparison.compare_tail_error(
            reference, evaluated, fraction=0.1
        ) == pytest.approx(10.0)

    def test_monotone_non_increasing_in_fraction(self, flat_dose):
        rng = np.random.default_rng(2)
        noisy = Dose(np.full((20, 20, 10), 50.0) + rng.normal(0, 3, (20, 20, 10)),
                     SPACING, ORIGIN)
        values = [
            dose_comparison.compare_tail_error(flat_dose, noisy, fraction=f)
            for f in (1.0, 0.5, 0.25, 0.1, 0.01)
        ]
        assert all(a <= b + 1e-9 for a, b in zip(values, values[1:])), values

    def test_between_mae_and_max(self, flat_dose):
        rng = np.random.default_rng(3)
        noisy = Dose(np.full((20, 20, 10), 50.0) + rng.normal(0, 3, (20, 20, 10)),
                     SPACING, ORIGIN)
        mae = dose_comparison.compare_mae(flat_dose, noisy)
        tail = dose_comparison.compare_tail_error(flat_dose, noisy, fraction=0.1)
        mx = dose_comparison.compare_max_error(flat_dose, noisy)
        assert mae <= tail <= mx

    @pytest.mark.parametrize("bad", [0.0, -0.1, 1.5])
    def test_out_of_range_fraction_raises(self, flat_dose, spiked_dose, bad):
        with pytest.raises(ValueError, match="fraction must be"):
            dose_comparison.compare_tail_error(flat_dose, spiked_dose, fraction=bad)


class TestComputeIsolatedExtrema:
    def test_smooth_distribution_has_none(self):
        """The property that makes the metric meaningful: no false positives."""
        z, y, x = np.mgrid[0:20, 0:20, 0:20]
        smooth = 60.0 * np.exp(-((z - 10) ** 2 + (y - 10) ** 2 + (x - 10) ** 2) / 50.0)
        result = dose_comparison.compute_isolated_extrema(
            Dose(smooth, SPACING, ORIGIN)
        )
        assert result["n_isolated"] == 0

    def test_detects_a_dropout_voxel(self):
        arr = np.full((20, 20, 20), 60.0)
        arr[10, 10, 10] = 0.0  # a black speckle in a high-dose region
        result = dose_comparison.compute_isolated_extrema(
            Dose(arr, SPACING, ORIGIN), deviation=5.0
        )
        assert result["n_dropout"] == 1
        assert result["n_hotspot"] == 0

    def test_distinguishes_hotspots_from_dropouts(self):
        arr = np.full((20, 20, 20), 60.0)
        arr[5, 5, 5] = 0.0
        arr[15, 15, 15] = 120.0
        result = dose_comparison.compute_isolated_extrema(
            Dose(arr, SPACING, ORIGIN), deviation=5.0
        )
        assert result["n_dropout"] == 1
        assert result["n_hotspot"] == 1
        assert result["n_isolated"] == 2

    def test_low_dose_speckle_is_ignored_by_default(self):
        """relative_threshold=0.5 restricts the search to the treated volume."""
        arr = np.full((20, 20, 20), 60.0)
        arr[:, :, :5] = 10.0          # low-dose region
        arr[10, 10, 2] = 0.0          # speckle inside it
        result = dose_comparison.compute_isolated_extrema(
            Dose(arr, SPACING, ORIGIN), deviation=5.0
        )
        assert result["n_isolated"] == 0
        # Searching the whole volume finds it.
        everywhere = dose_comparison.compute_isolated_extrema(
            Dose(arr, SPACING, ORIGIN), deviation=5.0, relative_threshold=0.0
        )
        assert everywhere["n_dropout"] == 1

    def test_deviation_threshold_is_respected(self):
        arr = np.full((20, 20, 20), 60.0)
        arr[10, 10, 10] = 57.0  # only 3 Gy below its neighbourhood
        d = Dose(arr, SPACING, ORIGIN)
        assert dose_comparison.compute_isolated_extrema(d, deviation=5.0)["n_isolated"] == 0
        assert dose_comparison.compute_isolated_extrema(d, deviation=2.0)["n_dropout"] == 1

    def test_is_invisible_to_mae(self):
        """The reason the metric is needed, stated as a test."""
        reference = np.full((20, 20, 20), 60.0)
        evaluated = reference.copy()
        evaluated[10, 10, 10] = 0.0
        ref_dose = Dose(reference, SPACING, ORIGIN)
        eval_dose = Dose(evaluated, SPACING, ORIGIN)

        mae = dose_comparison.compare_mae(ref_dose, eval_dose)
        assert mae < 0.01, "one bad voxel in 8000 should barely move MAE"
        assert dose_comparison.compute_isolated_extrema(eval_dose)["n_dropout"] == 1
        assert dose_comparison.compare_max_error(ref_dose, eval_dose) == 60.0

    def test_reports_evaluated_volume_and_fraction(self):
        arr = np.full((10, 10, 10), 60.0)
        arr[5, 5, 5] = 0.0
        result = dose_comparison.compute_isolated_extrema(Dose(arr, SPACING, ORIGIN))
        # The region is defined by the local median, so the dropout voxel is
        # inside the region it corrupts rather than excluded by its own value.
        assert result["n_evaluated"] == 1000
        assert result["fraction_isolated"] == pytest.approx(1 / 1000)

    def test_all_zero_dose_returns_nan_fraction(self):
        result = dose_comparison.compute_isolated_extrema(
            Dose(np.zeros((10, 10, 10)), SPACING, ORIGIN)
        )
        assert result["n_evaluated"] == 0
        assert np.isnan(result["fraction_isolated"])

    @pytest.mark.parametrize("bad", [2, 4, 1])
    def test_invalid_neighborhood_raises(self, bad):
        with pytest.raises(ValueError, match="neighborhood_size"):
            dose_comparison.compute_isolated_extrema(
                Dose(np.full((10, 10, 10), 60.0), SPACING, ORIGIN),
                neighborhood_size=bad,
            )

    def test_invalid_relative_threshold_raises(self):
        with pytest.raises(ValueError, match="relative_threshold"):
            dose_comparison.compute_isolated_extrema(
                Dose(np.full((10, 10, 10), 60.0), SPACING, ORIGIN),
                relative_threshold=1.5,
            )


class TestPublicAPI:
    def test_exported_from_module(self):
        for name in (
            "compare_max_error",
            "compare_error_percentile",
            "compare_tail_error",
            "compute_isolated_extrema",
        ):
            assert name in dose_comparison.__all__
            assert hasattr(dose_comparison, name)
