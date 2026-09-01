# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
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
