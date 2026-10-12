# Supplementary Material

[Supplementary_Material.docx](Supplementary_Material.docx) contains **Supplementary Fig. S1** and **Supplementary Table S1**. Figure and table numbering each begins at S1. Both use **NEW_D1 processed data**. System values are presented after denoising and other data processing.

Fig. S1 shows normal-incidence system BRDF, rotationally reconstructed reference and signed system-minus-reference distributions for the red, green, yellow and blue tiles at 550 nm. Table S1 contains 64 sample-channel combinations: four BRDF tiles and four BTDF PMMA samples across 430, 460, 490, 520, 550, 590, 630 and 660 nm. Signal-weighted discrepancies are **2.81% BRDF**, **6.74% BTDF**, and **5.00% overall**.

## Files

- [Supplementary_Material.docx](Supplementary_Material.docx): combined figure and editable 64-row table.
- [Supplementary_Material_preview.pdf](Supplementary_Material_preview.pdf): combined PDF preview.
- [Figure_S1_data/](Figure_S1_data/): Fig. S1 in PNG/PDF/SVG, full-precision arrays and CSV.gz grids for the four 550 nm samples, angle axes, masks, reference values, differences and reproduction scripts. Its [README](Figure_S1_data/README.md), [caption](Figure_S1_data/CAPTION.md), [requirements](Figure_S1_data/requirements.txt) and [checksums](Figure_S1_data/CHECKSUMS.sha256) accompany the data.
- [Supplementary_Table_S1.pdf](Supplementary_Table_S1.pdf): standalone table.
- [editable_sources/Supplementary_Table_S1.docx](editable_sources/Supplementary_Table_S1.docx): editable standalone table.
- [Supplementary_Table_S1_full_precision.csv](Supplementary_Table_S1_full_precision.csv): all 64 sample-channel values and flags.
- [Supplementary_Table_S1_aggregate_results.csv](Supplementary_Table_S1_aggregate_results.csv): group numerators, denominators and discrepancies for NEW_D1.
- [Supplementary_Table_S1_notes.txt](Supplementary_Table_S1_notes.txt): table definitions and formulas.
- [Supplementary_Table_S1_source_rows.csv](Supplementary_Table_S1_source_rows.csv): the 64 selected NEW_D1 source rows.
- [source_inputs/](source_inputs/): source snapshots used to generate the table, aggregate results and low-signal flags.
- [data_series_comparison.csv](data_series_comparison.csv): separately labeled BASE_D0 and NEW_D1 summaries; the supplement uses NEW_D1.
- [build_table_s1.py](build_table_s1.py) and [build_table_s1_pdf.py](build_table_s1_pdf.py): standalone table generation scripts.

## Definitions

Q_CD is dimensionless. System and reference use the same validity mask within 10-70 degrees and cos(theta)dOmega weights. The reference azimuthal distribution is rotationally reconstructed from principal-plane scans under the normal-incidence symmetry approximation for diffuse samples. No full-hemisphere normalization is applied.

Signed relative discrepancy (%) is `100*(Q_CD_sys/Q_CD_ref-1)` when `abs(Q_CD_ref)>1e-12`; positive means a larger system integral. Signed values are retained.

Signal-weighted group discrepancy (%) is `100*sum(abs(Q_CD_sys-Q_CD_ref))/sum(abs(Q_CD_ref))`. All group cases enter the sum; this differs from an arithmetic mean of signed row percentages. PDF/DOCX integrals show 8 significant digits and signed percentages show 4 decimals; CSV values retain full precision.

Low-signal flags retain the prior category `most_cells_below_prior_signal_criterion`, equivalent to `weighted_fraction_below_prior_20_5DN_criterion>=0.5`. The six cases are 5_430, 7_430, 7_460, 7_490, 7_520 and 7_550. All flagged cases enter the aggregates.

## Reproduction

Run the following commands from this directory. The table commands create a new output directory named `regenerated`; it is generated output rather than an input included in this folder. Explicit input arguments avoid the scripts' original-project default paths.

```sh
python build_table_s1.py --source source_inputs/integrals_64cases.csv --aggregates source_inputs/aggregate_summary.csv --flags source_inputs/sample_channel_quality_flags.csv --series NEW_D1 --output-dir regenerated
python build_table_s1_pdf.py --directory regenerated
```

Python requirements: python-docx for the editable table; reportlab, pypdf and python-docx for the PDF. The PDF script also uses the installed Windows Times New Roman fonts at `C:/Windows/Fonts` (times.ttf, timesbd.ttf and timesi.ttf). Generating the PDF on another operating system requires adapting that font configuration.

Fig. S1 can be checked and replotted directly from the arrays included in this folder:

```sh
python Figure_S1_data/scripts/verify_package.py
python Figure_S1_data/scripts/plot_comparison.py --data-dir Figure_S1_data/data --output-dir replot
```

The second command creates a new output directory named `replot`. Figure dependencies are NumPy and Matplotlib, with versions listed in the figure requirements file. Keep the figure directory structure so the plotting script can import its accompanying alignment helper.

The included scripts reproduce the standalone table and Fig. S1. The combined Word/PDF files are provided as assembled reading versions. The 64-row CSV supports recalculation of group discrepancies; the included angular arrays cover only the four BRDF samples at 550 nm. Recalculating all 64 integrals from angular distributions requires the remaining final angular arrays and the integration procedure, which are outside this folder. Re-exporting from a saved final run with the figure export script also requires that external source run.
