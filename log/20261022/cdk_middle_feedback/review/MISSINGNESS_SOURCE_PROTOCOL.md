# Exact author-source missingness check

2026-10-22, before the request. Parent supplies the exact public author path linked in the user-provided source attachment:

`https://github.com/douglas-russo/GuarducciAbravanel2026_barcoding-scRNAseq/blob/main/cell-line-barcoding.qmd`

Retrieve exactly its raw equivalent `https://raw.githubusercontent.com/douglas-russo/GuarducciAbravanel2026_barcoding-scRNAseq/main/cell-line-barcoding.qmd`, at most 2,000,000 bytes, one HTTP attempt, recording status, redirects, final URL, bytes and SHA256. No archive, dataset, workbook, source-tree inventory or assay output is fetched. A 404 is recorded before any separately scoped branch lookup. No retry.

Read author source code only to establish whether absent barcode/sample table entries are explicitly treated as zero and whether the processing context authenticates non-detection rather than an unmeasured assay. Search missingness handling and the import/merge/normalization path. Do not execute the R code, decode S3/S4 cells, run fits, render embedded outputs or interpret numerical biological outcomes. Static code constants/column labels are code, not new response measurements.

All request bytes/receipts/review under this log review directory. Fetch/check code under `research/cdk_middle_feedback_20261022/`. Keep prior parsing failures and frozen files intact. A zero convention requires source evidence; absence of such evidence remains unresolved rather than an instruction to impute.
