# Public ordered-axis authority audit

An independently checked **candidate** 2,000-gene list was recovered. Exact
dataset-axis and checkpoint-decoder lineage remain unproven. This assessment is
bounded to the retained sources; it does not assert that no other public asset
exists. No expression data were requested and no maintainer was contacted.

## Positive evidence

The public dataset `tahoebio/tahoe-de-rhaister` at
`c7963cf334bec0683225d41c9586d900ca6303a2` publishes
`definition/static_2k_genes.json`. The primary `tahoebio/Rhaister` model/code release
at `75fed20a1d97b05a09bf25c5341762141882106a` publishes byte-identical
`splits/tahoe/static_2k_genes.json`.

The SHA256 is
`6a29f993fbf166ed0c07eea58517b61a63c92ffec9e5fe8c9588593e7a8fa243`.
Both contain 2,000 unique symbols. All 39 legacy endpoint coordinate/symbol
declarations agree. All previously authenticated c40/c44 endpoint coordinates
agree with this candidate list: respectively 27 and 34. Unresolved coordinates
are not authenticated by their agreement with a declared symbol.

Safe parsing of the exact `ST-HVG-Tahoe` zeroshot metadata establishes 2,000 input,
HVG and output dimensions, but `var_dims.pkl` and `hparams.yaml` both list the
same **62,710** unique full-gene names. The candidate list is a strictly increasing
subset of that full order. `var_dims.gene_dim` is 62,710 whereas
`hparams.gene_dim` is 2,000; neither numeric field identifies the selected subset.
The tiny `data_module.torch` archive contains configuration, not an ordered gene
list. External pickle metadata is read with a restricted unpickler allowing only
NumPy dtype/scalar globals; released source files are inspected as text.

## Missing provenance and scale boundary

The exact release trees inspected are:

| Release | Revision | Entries | Finding |
|---|---|---:|---|
| `arcinstitute/State-Tahoe-Filtered` | `fdf87abece385feea6fa5e9944ab46e173b6af50` | 52 | 50 c*.h5ad files, generalization.toml and .gitattributes; no separate ordered map |
| `arcinstitute/ST-HVG-Tahoe` | `ca6b751972493f8448e3256d1340ae70ad43e1e7` | 98 | Reviewed trees and small zeroshot metadata do not identify the exact 2,000-gene subset |

Pinned STATE preprocessing (`9bbfe78a434a55205e4de834e1ea99f85f7a3add`)
preserves var order when applying a highly-variable mask. That recipe only
determines an order when the actual training/release mask and input are known.
Pinned cell-load (`9ba45e59f6f8117bb7a21371ad38d67175586d53`) can fall back
to full var names when no HVG mask/list is supplied. This is a possible explanation
for the dimensional metadata discrepancy, not proof of training lineage.

Rhaister's public producer config refers to private-path
`plate*_full_filtered.h5ad.gz` and `gene_symbol`; inspected STATE files use
`var/gene_name`. No retained manifest links the Rhaister list to the precise
STATE dataset or checkpoint releases. Rhaister's dataset README calls cell_eval
deltas linear normalized, while its released producer applies
`log1p(obsm[X_hvg])` in HVG mode. Named summary statistics may guide the selection
of calibration conditions; their scale is not certified as STATE observations.

Public STATE issues #268/#279 identify the missing-map question but provide no
authoritative answer. PR #246 proposes storing HVG names and is unmerged in the
retained response. Broader ST-Tahoe discussion must not be applied to this exact
HVG release without evidence.

## Verification and allowed next step

Run from any directory with Python, NumPy and PyYAML:

```text
python path/to/authority/audit.py --verify
```

`AUDIT.json` records the bounded source assessment and independently recomputed
positive comparisons. `RECEIPTS.json` accounts for 49 public requests and
2,569,778 response-body bytes, all HTTP 200, below the 5,000,000-byte authority
cap. `REUSED_SOURCES.json` identifies locally reused, already retained evidence;
it adds zero network bytes. `CLOSURE.json` hashes every retained source and
verification input. `VERIFICATION.json` records an offline PASS; this checks
receipt integrity and computed comparisons, not an exhaustive proof of absence.

The candidate map can guide a separately frozen, informative **file-local**
calibration. Every required coordinate must be authenticated against all actual
source genes on discovery and holdout cells. Authentication for one file does
not certify another file or the checkpoint decoder. The old DMSO audit and
sentinel experiment remain unchanged.
