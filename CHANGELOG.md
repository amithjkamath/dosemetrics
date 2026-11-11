# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Error-tail metrics** in `metrics.dose_comparison`, for the localized errors a
  mean cannot see. A single voxel wrong by 60 Gy in a 128³ volume moves mean
  absolute error by under 0.01 Gy, so a model can improve every mean-based score
  while leaving artifacts that are obvious on a dose display.
  - `compare_max_error()`: largest absolute dose difference.
  - `compare_error_percentile()`: a chosen percentile of absolute error;
    `percentile=100` reproduces `compare_max_error()`.
  - `compare_tail_error()`: mean of the worst `fraction` of absolute errors, i.e.
    the conditional value at risk (superquantile) at level `1 - fraction`.
    `fraction=1.0` reproduces `compare_mae()` exactly. More stable than the
    maximum, which is a single order statistic.
  - `compute_isolated_extrema()`: reference-free count of voxels deviating from
    their local median by more than a threshold, separated into `n_dropout` and
    `n_hotspot`. Detects salt-and-pepper artifacts in a distribution whose
    agreement with a reference is otherwise good. Both the search region and the
    dose scale are taken from the median-filtered volume, never from raw values —
    a dropout voxel is far below its surroundings, so thresholding on its own
    value would exclude it from the region it corrupts.
- 31 tests in `tests/metrics/test_tail_error.py`, including that a single bad
  voxel moves the tail metrics while leaving MAE effectively unchanged.
- Documentation: an "Error tail and localized artifacts" section in the
  quality-metrics user guide, and four rows in the classification table.

### Changed
- **`compute_isolated_extrema` gains `region` and `erode_region`.** Without a
  region the function searches the whole volume, which is wrong for the case it
  was written for: dose *predictions* are almost always masked, a masked
  prediction is exactly zero outside its mask, and where the mask is irregular an
  exterior zero sits in a neighbourhood whose median is still high and is
  flagged. Measured on real dose predictions, the unrestricted count was roughly
  fifty boundary voxels per patient against about one genuine artifact — the
  number described the mask, not the model, and inverted the ranking between two
  architectures. `erode_region` additionally drops the voxels just inside the
  boundary, whose median window still straddles it.
- **`Structure` voxel spacing is now optional and defaults to `None`** (was
  `(1.0, 1.0, 1.0)`). A structure is often a mask on a grid defined elsewhere,
  usually by a `Dose`; requiring the caller to restate that grid on every
  structure was friction, and the old default was wrong in two ways. Pairing a
  default-spacing structure with a real dose raised a compatibility error that
  said nothing actionable, and any metric reading `structure.spacing` computed a
  volume on a 1 mm grid — silently incorrect rather than failing.
  - A structure with `spacing=None` is compatible with any dose of matching
    shape; shape is still enforced, and explicitly stated spacing is still
    checked exactly as before.
  - `compute_dose_at_volume_cc` now takes the grid from the `Dose`, which is what
    is being sampled, rather than from the structure.
  - `Structure.volume_cc()` raises a clear error when spacing is unknown instead
    of returning a 1 mm-grid volume.
  - Callers that passed spacing explicitly are unaffected.
- **Relicensed from CC BY-NC-SA 4.0 to Apache License 2.0.** The Creative
  Commons licence prohibited commercial use, applied a viral ShareAlike term to
  derivative works, and carried no patent grant -- it was written for creative
  works, not software. It made DoseMetrics the only package in the ContourAId
  family that downstream products could not use. Apache-2.0 is permissive,
  grants patent rights expressly, and requires only that the copyright notice,
  licence and `NOTICE` travel with redistributed copies. Added `NOTICE`, and
  declared the licence as a PEP 639 SPDX expression (`License-Expression:
  Apache-2.0`), which raises the build requirement to `setuptools>=77.0.3`.
  Note that releases up to and including 0.4.1 remain published under the
  previous licence; the change applies from the next release onward.

### Fixed
- **`compare_dvh_score` did not reproduce OpenKBP DVH scores.** It is documented
  as "the complete OpenKBP DVH score", but its D0.1cc took the n-th hottest voxel
  exactly, whereas the challenge evaluator clamps to at least one voxel and takes
  a linearly interpolated percentile. On a 442-voxel brainstem the two disagree
  by about 1 Gy, enough to shift a published DVH score by ~0.8%.
  `compute_dose_at_volume_cc` gains an `interpolate` flag (default `False`, so
  existing callers are unaffected) and `compare_dvh_score` now uses
  `interpolate=True`. Verified against an external implementation on 60
  patient-plans: dose_score and DVH_score now agree to floating-point epsilon
  where DVH_score previously differed by up to 0.158 Gy per patient.
- Pinned `ipython>=8.18,<9`. matplotlib 3.8's `pyplot` imports `backend2gui`
  from `IPython.core.pylabtools`, which IPython 9 removed, so with
  `matplotlib~=3.8.2` every notebook calling `%matplotlib inline` failed --
  taking the whole documentation test suite with it. `uv.lock` is not tracked,
  so CI re-resolves on each run and picked up IPython 9 as soon as it was
  released. Lift this bound together with the matplotlib pin.

## [0.4.1] - 2026-08-16

### Added
- **`utils.compliance.evaluate_constraint()`**: scalar constraint evaluation
  (value, constraint type, level) -> (compliant, reason). Exposed so callers
  testing many hypothetical dose values against one constraint -- for example a
  family of DVH curves derived from contour variations -- reuse the constraint
  semantics instead of re-implementing them.
- **`utils.compliance.constraint_metric()`**: maps a constraint type to the
  dose-statistic column it is evaluated against.
- **`utils.plot.plot_dvh_band_from_curves()`**: draws a DVH band from an
  already-computed ensemble of curves on a shared dose axis, with optional
  min/max envelope. Works for any ensemble, not just multi-subject datasets.

### Changed
- `check_compliance()` now delegates to `evaluate_constraint()`. Output columns,
  compliance markers and reason strings are unchanged.
- `plot_dvh_band()` now delegates its drawing to `plot_dvh_band_from_curves()`
  after collecting and interpolating the per-subject DVHs. Behaviour unchanged.

## [0.3.0] - 2025-12-28

### Added
- **Dose Class**: New `Dose` class for managing 3D dose distributions separately from structures
- **StructureSet Class**: New `StructureSet` aggregation object for managing collections of radiotherapy structures
- **Structure Type Classification**: Proper OAR/Target/Avoidance distinction using enums
- **Bulk Operations**: Calculate statistics and DVH for all structures simultaneously via StructureSet
- **Enhanced I/O Functions**: New functions for loading data directly into StructureSet objects
  - `get_dose_and_structures_as_structure_set()`: Load from folder to StructureSet
  - `read_dose_and_mask_files_as_structure_set()`: Convert file lists to StructureSet
  - `create_structure_set_from_existing_data()`: Upgrade existing data to StructureSet
- **Factory Functions**: Convenient creation methods (`create_structure_set_from_folder()`, `create_structure_set_from_masks()`)
- **Comprehensive Test Suite**: 25+ tests for Dose class, 30+ tests for StructureSet
- **Documentation**: New tutorials for NIfTI I/O, DICOM I/O, and StructureSet usage

### Changed
- **BREAKING**: Separated dose data from Structure class - structures no longer directly contain dose data
- **BREAKING**: StructureSet objects now manage dose data for all structures
- **BREAKING**: Removed `set_dose_data()` and related methods from Structure class
- Improved multi-dose file handling - can now work with multiple RT-DOSE files per patient
- Enhanced spatial compatibility checking between dose grids and structures
- Updated all I/O functions to support the new architecture

### Fixed
- DICOM SliceThickness None handling in dose loading
- Multiple RT-DOSE file loading and management
- Spatial compatibility validation between dose and mask data

### Notes
- **Development Status**: Still in alpha - API may change in future versions
- Maintained backward compatibility for basic Structure operations
- All existing tests passing with new architecture

## [0.2.0] - 2025-08-08

### Changed
- **BREAKING**: Restructured repository to use src/ layout
- **BREAKING**: Reorganized modules into logical packages:
  - `dosemetrics.metrics`: Core dose calculation functions (DVH, scores, etc.)
  - `dosemetrics.io`: File I/O utilities for reading dose and mask data
  - `dosemetrics.utils`: Utility functions for compliance, plotting, etc.
- **BREAKING**: Moved Streamlit app code to separate `dosemetrics_app` package
- **BREAKING**: App-specific code (variations_tab.py) moved to `dosemetrics_app.tabs`
- Updated package configuration to exclude app code from PyPI distribution
- Added CLI entry point via `dosemetrics` command

### Added
- Command-line interface for basic operations
- Clear separation between library and application code
- Improved package structure following Python best practices
- Updated `pyproject.toml` to support src/ layout

### Removed
- App-specific modules are no longer part of the core library API
- Removed stray files from the root package namespace

## [0.1.x] - Previous versions
- Initial releases with flat package structure
