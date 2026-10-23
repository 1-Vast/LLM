# Explicit sparse-count convention, before fitting

Author public cell-line-barcoding.qmd was acquired with receipt by independent reviewer. Its opening paragraph explicitly names Barcodes_Palbo_study and Barcodes_Abema_study and says long-format inputs compile the same raw barcode data. It calls its table S2, whereas retained publisher artifact is designated S3; the exact sheet-name match is positive correspondence evidence, not proof of exporter byte identity.

Code lines279–283 and1026–1030 pivot barcode count tables with values_fill=0; lines319–323 and1043–1047 do the analogous fraction transform. These support an author-style sparse-zero convention for barcode/sample pairs absent from the long representation. They do not identify the missingness mechanism of every omitted S3 cell or biological extinction.

For this exploratory first numerical run, declare omitted selected Count cells as zero under that convention, count/report omissions per sample, retain positive observed counts without frequency filtering, normalize each assay. Explicit invalid nonblank values remain errors. This replaces the initial no-imputation default transparently after concrete input failure and source evidence, before any fit/result. The experiment is conditional on this sparse-zero convention, not confirmation of raw assay completeness. No S4 N/A is affected.

Only the selected Count cells and barcode IDs enter prepared arrays. The bounded missingness diagnostic additionally inspected six adjacent treated Fraction encodings, all absent; earlier whole-row over-decoding is disclosed in READ_FAILURE_AND_AMENDMENT.md. We do not re-describe those cells as unopened.

The model, grids, losses, splits and stopping interpretation remain unchanged. Any positive result needs observation/missingness sensitivity or better raw-data correspondence before mechanistic or functional interpretation. If conventional baselines explain the results, no new world-model rule is inferred.
