# Supplementary Figure S1 data

**NEW_D1 processed data** for four normal-incidence BRDF samples at 550 nm. Columns show system BRDF, rotationally reconstructed reference and signed system-minus-reference values.

System values are presented after denoising and other data processing using NEW_D1 processed data.

## Files and data definitions

- figures: PNG, PDF and SVG versions of the 4×3 figure and display settings.
- data: lossless NPZ arrays, complete grid CSV.gz files, masks and color limits.
- scripts: plotting, final-source export and checksum/array verification scripts.
- provenance: final source hashes and array-field mappings.
- CAPTION.md: figure caption.
- CHECKSUMS.sha256: publication-copy file hashes.

Source fields are system=Bprocessed, reference=G and comparison domain=D1. Packaged reconstruction denotes the system array; difference is reconstruction minus reference. All maps use 401 theta rows and 1796 phi columns on the saved 0.2° angle-center grid. Arrays retain source float64 precision and Boolean masks. CSV numbers use 17 significant digits; missing values remain nan. Full grid values and masks are provided.

The visible domain is theta 10–70° and phi 0–359°, with 459834 comparison cells per sample. Gray cells lie outside the common display mask. The system/reference pair shares color limits within each row. Signed-difference scales are symmetric about zero and use the 99th percentile of absolute difference on the same mask. Colorbar extensions indicate values beyond the color scale; array values are unchanged.

## Reproduction

Run these commands from the Figure_S1_data directory and keep its structure. With NumPy and Matplotlib installed:

`python scripts/verify_package.py`

`python scripts/plot_comparison.py --data-dir data --output-dir replot`

The replot directory is generated output. For a new export from an externally saved final run, replace the example source/output paths below with your own paths; the final source run is not included in this folder:

`python scripts/build_from_final_run.py --source-run /path/to/zero_incidence_v1_2 --package-dir /path/to/new_package --limits-from data/color_limits.json`

This directory contains the publication copy. Source identifiers and exact field names are retained in the machine-readable provenance files.
