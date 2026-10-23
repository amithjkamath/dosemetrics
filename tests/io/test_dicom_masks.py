"""
Tests for rasterising RTSTRUCT contours onto a grid.

Contours are squares in physical coordinates on a grid with 1 mm pixels, so the
expected masks can be counted by hand.
"""

import numpy as np

from dosemetrics.io.dicom_io import _generate_mask_from_contours


def square(low, high, z):
    """A closed square contour with corners at (low, low) and (high, high) mm."""
    return np.array(
        [[low, low, z], [high, low, z], [high, high, z], [low, high, z]], dtype=float
    )


class TestContourMasks:
    """Contours to masks: plane assignment, holes and islands."""

    spacing = (1.0, 1.0, 1.5)
    origin = (0.0, 0.0, 0.0)

    def test_grid_finer_than_contours_fills_every_slice(self):
        # Contours every 3 mm at z = 3, 6, 9; grid slices every 1.5 mm
        contours = [square(2.5, 7.5, z) for z in (3.0, 6.0, 9.0)]

        mask = _generate_mask_from_contours(contours, (10, 12, 12), self.spacing, self.origin)

        filled = [i for i in range(10) if mask[i].any()]
        # Three 3 mm planes make 9 mm: six 1.5 mm slices, z = 3.0 ... 10.5
        assert filled == [2, 3, 4, 5, 6, 7]
        assert all(mask[i].sum() == 25 for i in filled)

    def test_halfway_slices_survive_rounded_grid_spacing(self):
        # A TCIA case: CT contours every 3.27 mm, dose planes every 1.6349999 mm, so
        # every other dose plane lies halfway between two contours, give or take 1e-5
        planes = [-362.83 + 3.27 * k for k in range(10)]
        contours = [square(2.5, 7.5, z) for z in planes]
        origin = (0.0, 0.0, -400.4349879)

        mask = _generate_mask_from_contours(contours, (60, 12, 12), (1.0, 1.0, 1.6349999), origin)

        assert int(mask.any(axis=(1, 2)).sum()) == 2 * len(planes)

    def test_gap_between_contour_planes_stays_empty(self):
        # Contoured at z = 3, 6 and again at z = 30, 33: nothing in between
        contours = [square(2.5, 7.5, z) for z in (3.0, 6.0, 30.0, 33.0)]

        mask = _generate_mask_from_contours(contours, (25, 12, 12), self.spacing, self.origin)

        assert not mask[6:19].any()
        assert mask[4].any() and mask[20].any()

    def test_nested_contours_are_holes(self):
        contours = [square(0.5, 9.5, 3.0), square(3.5, 6.5, 3.0)]

        mask = _generate_mask_from_contours(contours, (4, 12, 12), self.spacing, self.origin)

        assert mask[2].sum() == 81 - 9
        assert not mask[2, 4:7, 4:7].any()

    def test_contour_running_off_the_grid_is_clipped(self):
        contours = [square(-4.5, 4.5, 3.0)]  # centres -4 ... 4, the grid starts at 0

        mask = _generate_mask_from_contours(contours, (4, 12, 12), self.spacing, self.origin)

        assert mask[2].sum() == 5 * 5
        assert mask[2, :5, :5].all()

    def test_separate_contours_are_islands(self):
        contours = [square(0.5, 3.5, 3.0), square(5.5, 8.5, 3.0)]

        mask = _generate_mask_from_contours(contours, (4, 12, 12), self.spacing, self.origin)

        assert mask[2].sum() == 9 + 9
