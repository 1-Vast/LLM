# P0.6 readiness — blocked, metadata only

P0.6 has **not run**. No P0.6 expression was fetched or read, no runner or tests were implemented, and no execution protocol was frozen. The prospective preparation code, manifests, protocol and copied text inputs have been removed. Three binary metadata copies are retained as read-only readiness audit inputs supporting the count and identity checks below, totalling 129,937 bytes. Their contents exactly match the authoritative calibration inputs; they do not authorize execution. Shell deletion was blocked by tool policy, and no further cleanup is required.

The required file-local 39-gene axis certificate failed. Independent offline verification reproduced 16/39 uniquely authenticated coordinates for `c44.h5ad` and 23/39 for `c45.h5ad`, using 74 paired cells. Every failed coordinate had multiple matching source-gene trajectories; none had no match, a uniquely wrong name, or inadequate registered nonzero support. Sparse numerical fingerprints therefore remain unidentifiable. This does not demonstrate incorrect gene names or biological failure of feedback. No alternate acceptance gate or P0.6 expression release follows from this result.

## Verified metadata available

The pinned filtered source is `arcinstitute/State-Tahoe-Filtered@fdf87abece385feea6fa5e9944ab46e173b6af50`. The target files are `c44.h5ad` (SW 1088, `CVCL_1715`, `ACH-000437`) and `c45.h5ad` (SW 1271, `CVCL_1716`, `ACH-000890`). Source sample, plate and exact treatment joins have been checked. The source-wide treatment duration is 24 hours; it is not a separately verified duration for every cell.

Six metadata-selected treatments have at least 50 full-QC cells in both target lines on plate6 and plate14. All concentrations are exactly 5 uM. Counts below are source full-QC counts, not observations acquired by P0.6.

| Treatment | c44 plate6 | c44 plate14 | c45 plate6 | c45 plate14 |
|---|---:|---:|---:|---:|
| Ritonavir | 128 | 177 | 131 | 229 |
| Docetaxel | 76 | 304 | 90 | 257 |
| Retinoic acid | 121 | 149 | 224 | 200 |
| Ciclopirox | 68 | 118 | 113 | 143 |
| Tofacitinib | 129 | 118 | 145 | 156 |
| Fusidic acid | 107 | 177 | 214 | 167 |

These are 24 line-by-plate strata but only 12 distinct pooled treatment sample IDs. They must not be counted as 24 independent cultures. The same pooled sample IDs occur across lines.

Matched DMSO controls are available as follows. The last column excludes earlier control-noise and axis/calibration rows using their retained manifests; it was checked without reading new expression.

| File | Plate | Sample | Full-QC cells | Eligible after exclusions |
|---|---|---|---:|---:|
| c44 | plate6 | smp_2069 | 148 | 108 |
| c44 | plate6 | smp_2070 | 167 | 127 |
| c44 | plate14 | smp_2837 | 122 | 82 |
| c44 | plate14 | smp_2838 | 132 | 92 |
| c45 | plate6 | smp_2069 | 237 | 237 |
| c45 | plate6 | smp_2070 | 305 | 305 |
| c45 | plate14 | smp_2837 | 130 | 130 |
| c45 | plate14 | smp_2838 | 131 | 131 |

## Historical budget feasibility, not execution authorization

The discarded preparation demonstrated metadata-only feasibility for 32 cells per stratum: 768 treated cells plus 256 control cells, with 8,192,000 bytes of full-HVG float32 payload. Its proposed 10,000,000-byte P0.6 received-body cap was never an executed or frozen experiment. The separate finite calibration actually received 24,533,272 measured body bytes within its 28,000,000-byte cap; the global 60,000,000-byte discovery cap was unchanged. Those calibration/discovery limits do not authorize new P0.6 expression or another calibration supplement.

## Prerequisites and scientific limits

The present finite calibration is closed and P0.6 remains blocked. Any future work needs a separately justified input-axis solution and review before a new expression protocol; it cannot silently relax the uniqueness gate, relabel ambiguous coordinates, or spend the old budget on another attempt.

A future reference defined as equal 0.5/0.5 weights for two pooled DMSO sample means would be a **new** reference endpoint, not a reproduction of historical control weights. Shared reference uncertainty must remain shared across candidate comparisons. The official pseudobulk method uses original plate data, normalization, named 2,000-HVG selection, all DMSO cells and depths 25–1,600. A filtered 39-gene, 8/16/32-cell adaptation would not reproduce that method.

Within-source disjoint cells are not independent cultures. Calibration allocation used expression-derived CSR presence in both roles, although the numerical holdout values were unopened at allocation. A file-local 39-gene certificate would not certify the full 2,000-gene axis, the STATE checkpoint decoder, other files or versions. RNA source disagreement is not a causal biological variance estimate, nor a viability or apoptosis measurement. The original c40/c44 control study remains blocked; the c44/c45 metadata cannot release it. No decision benefit or production promotion is claimed.

## Authoritative retained evidence

The three local audit inputs have these verified identities. Each source path is relative to this directory; these files contain categorical/QC codes or sample metadata, not P0.6 RNA observations.

| Retained audit input | Bytes | SHA256 | Authoritative source |
|---|---:|---|---|
| `inputs/c44.h5ad_CODES.npz` | 29,109 | `68fb38f188c74d91d2167c6dcad75e937af41f73fff07008255956b26063d14d` | `../calibration_v2/inputs/c44.h5ad_CODES.npz` |
| `inputs/c45.h5ad_CODES.npz` | 35,192 | `5816bfea99fe80bebd9df408cadd6fe6ea5990942252946b856fc75bb9a26574` | `../calibration_v2/inputs/c45.h5ad_CODES.npz` |
| `inputs/SAMPLES.parquet` | 65,636 | `33167f0ce28cff8357c503cda67d1c7fea200bff6918ee1de3c4f3549175b9d3` | `../calibration_v2/inputs/SAMPLES.parquet` |

- `../design/CALIBRATION_V2_VERIFIED.json`: independent numerical reconstruction and byte accounting.
- `../calibration_v2/RESULTS.json`, `CERTIFICATE.json`, `ROW_MANIFEST.json`: frozen finite-calibration result, acceptance gate and paired rows.
- `../calibration_v2/CENSUSES.json`, `inputs/*_CODES.npz`, `inputs/SAMPLES.parquet`: retained metadata for count reconstruction.
- `../../observation_reliability/literature/UPDATED_SENTINELS.json`, `SOURCE_QUALIFICATION.json`: sentinel identities, exact source joins and source-quality limits.
- `../../observation_reliability/CONTROL_PLAN.json` and `axis/PROTOCOL.json`: prior-row exclusions and the still-blocked old control design.
- `../design/METHODS_REVIEW.md`, `FETCH_RECEIPTS.json`, `sources/pseudobulk_correlation.py`: pinned official method review and receipts; no new expression.
