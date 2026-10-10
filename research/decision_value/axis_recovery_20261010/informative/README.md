# Named-summary guidance for informative axis calibration

Public named summaries provide a useful alternative to sampling more all-zero
controls. Exact HTTP ranges recovered 39 endpoint columns from the 65.7 MB
plate-1 Parquet table without downloading the complete table. The discovery
received 2,440,824 measurable body bytes across 97 HTTP responses, including
redirects. One narrow Hugging Face Viewer filter timed out before any body was
delivered; transport bytes before delivery are unmeasured. No paired-cell RNA or
LLM API was acquired in this directory.

The pinned summary revision is
`tahoebio/tahoe-de-rhaister@c7963cf334bec0683225d41c9586d900ca6303a2`.
Official Tahoe cell metadata identifies SW 1088 as CVCL_1715 / ACH-000437 and
SW 1271 as CVCL_1716 / ACH-000890. All 92 consulted treatment labels join official
plate-1 sample metadata. The six protected P0.6 labels and their 12 pooled samples
have no overlap with this plate-1 scope.

All five unresolved c44 genes have positive deltas somewhere in the named
plate-1 summary: CD38 in 12 conditions, PLCB2 in 9, IFNB1 in 4, F2 in 25, and TNF
in 11. The corresponding counts for c45 are 9, 4, 5, 11, and 8. A deterministic
greedy rule proposes three c44 and four c45 calibration conditions, at 0.05 uM.
The proposal allocates 32 cells per condition, split into 16 discovery and 16
holdout cells: 224 cells and 1,792,000 HVG payload bytes, before CSR and metadata.
Exact full-QC eligibility and row selection belong to the separate calibration
protocol. This directory has not read those cells.

These values are observability hints. The README describes linear normalized
deltas, whereas the released Rhaister producer applies `log1p(X_hvg)` in its HVG
path. Neither establishes the exact preprocessing lineage of the pinned STATE
filtered files. Positive deltas are not target expression means, per-cell
nonzero probabilities, or numerical axis certificates. All 39 declared index
names agree with the official static 2,000-gene list; that agreement does not
authenticate any actual c44/c45 stored column or checkpoint output.

`EXPOSURES.json` permanently excludes all 94 consulted treatment pooled samples
and both potential plate-1 reference-control samples, across every shared cell
line. It records rowwise exposure of 39 genes over 4,443 rows and aggregate footer
statistics for all 2,000 genes. These units cannot be used as independent terminal
decision validation. The producer's exact reference grouping remains unknown.

`COVERAGE.json` records the retrieved evidence and limits. `SELECTION.json` stores
the finite calibration proposal. `NETWORK.jsonl` and `sources/` retain measurable
successful and failed bodies, hashes, response-range information, and redacted
signed redirect locations. The complete table hash was not recomputed from
partial ranges. `VERIFIED.json` records a separate offline reconstruction of all
coverage counts, selected-condition values, identities, and exclusion joins.

From the isolated repository root:

```powershell
python research/decision_value/axis_recovery_20261010/informative/verify.py
```

This verifier makes zero network calls and does not import the acquisition or
summary producer. No scientific gate is released by this discovery.
