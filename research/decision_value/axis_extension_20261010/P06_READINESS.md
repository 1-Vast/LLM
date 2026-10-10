# P0.6 readiness after P0.5R-Extension

The **file-local 39-gene data-axis prerequisite is satisfied** for `c44.h5ad` (SW1088) and `c45.h5ad` (SW1271) at `arcinstitute/State-Tahoe-Filtered@fdf87abece385feea6fa5e9944ab46e173b6af50`. Both files have 39/39 unique numerical matches against all 62,710 source genes, with the unchanged `log1p(stored normalized X)` transform and `1e-5` absolute tolerance. Maximum discrepancies are `1.441582098138383e-07` and `1.4611107745921004e-07`, respectively; see `QUALIFIED_CERTIFICATE.json` and `VERIFIED.json`.

**P0.6 execution remains unreleased.** No P0.6 sentinel expression has been acquired, no new P0.6 RNA execution protocol has been frozen, and no observation reliability or A-to-B transfer has been demonstrated. This reevaluation supersedes the axis prerequisite assessment only; the original `../axis_recovery_20261010/p06/READINESS.md` and failed P0.5R results remain unchanged. P2 and production promotion remain closed.

## Evidence scope and exclusions

c44 uses 252 already exposed cells: 224 historical controls, 19 later discovery cells and 9 previously read consistency cells. Its new RNA cost is zero. This is retrospective joint identity evidence, not a fresh holdout. c45 adds 11 adaptively selected cells to the existing discovery panel, while the old 14 consistency cells remain exposed consistency checks. Exact additional received payload is 133,564 bytes. The first parser failure and the separately frozen offline reconstruction amendment are retained.

The 11 new c45 rows are all full-QC, plate1, 0.05 uM treatment cells. `C45_SELECTION_VERIFIED.json` and its frozen selection checks verify no overlap with prior discovery/consistency rows, protected control rows, reserved sentinel labels or reserved pooled sample IDs. Thus these 11 rows do not consume plate6/plate14 sentinel or DMSO pools. The next protocol must nevertheless recompute complete file-and-row exclusion sets from **all** prior manifests, including the c44 union and c45 extension; it must not treat exposed rows as untouched evaluation cells.

The full 2,000-gene data axis and STATE checkpoint output axis remain uncertified. The old c40/c44 250-cell noise plan remains blocked because c40 is not qualified; a c44/c45 certificate cannot release that study. The certified endpoint is the equally positive 39-gene expression mean (`w_j = +1/39`), not a signed apoptosis score or viability measurement.

## Metadata-supported next design

The retained metadata support six 5 uM treatments on both plate6 and plate14 in both lines: Ritonavir, Docetaxel, Retinoic acid, Ciclopirox, Tofacitinib and Fusidic acid. Each of the 24 line-by-plate treatment strata has at least 50 full-QC cells. There are only **12 distinct pooled treatment sample IDs**, shared across lines, not 24 independent cultures. Source methods identify plate14 as a biological replicate of plate6; the source-wide exposure duration is 24 hours, with no separately verified per-sample time column.

The previous metadata audit reports these DMSO pools after its then-current exclusions. They are inputs to a new audit, not a frozen row allocation:

| File | Plate | Samples | Full-QC counts | Previously eligible counts |
|---|---|---|---|---|
| c44 | plate6 | smp_2069 / smp_2070 | 148 / 167 | 108 / 127 |
| c44 | plate14 | smp_2837 / smp_2838 | 122 / 132 | 82 / 92 |
| c45 | plate6 | smp_2069 / smp_2070 | 237 / 305 | 237 / 305 |
| c45 | plate14 | smp_2837 / smp_2838 | 130 / 131 | 130 / 131 |

## Required freeze before any P0.6 expression read

1. **Inputs and allocation:** bind the new data-axis certificate, source revision, exact endpoint coordinates and weights, source/QC/sample metadata hashes, treatment identities and units. Recompute exclusions and freeze every selected HDF5 row, role, sample and plate. Select rows using metadata alone; retain disjoint treated subsets for within-source sampling checks without calling them independent cultures.
2. **Controls and reference:** freeze matched DMSO rows, actual group sizes, reference construction and weights. A 0.5/0.5 combination of the two DMSO sample means per plate is an available new endpoint definition, not recovered historical weighting. Keep reference uncertainty shared across comparisons; do not duplicate a shared control as independent evidence. Compute scalar mean variance using actual post-QC `n_g`, retaining gene covariance; state the assumptions behind cell-level uncertainty.
3. **Source-repeat estimands:** preregister within-source disjoint-cell stability and matched plate6-to-plate14 treatment-minus-reference agreement. Distinguish sampling variance from culture/source disagreement. Fix missingness, QC failures, equivalent-effect handling, interval construction and stopping rules before expression is opened. Two lines and two source plates cannot certify population-level reliability or causal variance components.
4. **Cost and execution:** freeze exact physical ranges, cached-range reuse, expected new bytes, received-body cap, request/retry policy, parser code, verifier and failure receipts. The earlier 32-cell proposal would use 768 treated plus 256 control cells: 8,192,000 bytes of full-HVG float32 payload alone. Its proposed 10,000,000-byte cap was never frozen and does not authorize reads; metadata, failure bodies and any auxiliary ranges require explicit accounting in the new cap.
5. **Verification and conclusions:** require independent arithmetic reconstruction and provenance/cost checks. Fix numerical ties and favor no propagation when choices are scientifically indistinguishable. Report observation-channel reliability first; do not adjust MAP feedback or use evaluation B to choose thresholds. Any later transfer/decision experiment needs its own frozen protocol and untouched qualifying biological units.

This is a readiness reevaluation, not the new execution freeze. A future P0.6 study may proceed after these specific artifacts exist and pass preflight. Even a successful source-repeat study would not release P2: stable incremental A-to-B decision value, harms, costs and independent confirmation remain separate gates.

Authoritative inputs: `QUALIFIED_CERTIFICATE.json`, `VERIFIED.json`, `C44_UNION.json`, `C45_SELECTION_VERIFIED.json`, `C45_NUMERIC_RECONSTRUCTED.json`; `../axis_recovery_20261010/p06/READINESS.md`; `../observation_reliability/literature/UPDATED_SENTINELS.json` and `SOURCE_QUALIFICATION.json`; prior control and row manifests. No new source fetch was performed for this reevaluation.
