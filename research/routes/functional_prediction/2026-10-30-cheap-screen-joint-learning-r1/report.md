# Cheap-screen Agent × virtual-cell research round R1

**Date:** 2026-10-30 (Asia/Shanghai)  
**Status:** exploratory negative / candidate parked; overall user objective remains ACTIVE / NOT_ACHIEVED.

## Finding

The only frozen candidate in this round was a narrow empirical response restriction, not a new algorithm: after a preparation-specific no-drug calibration, the TNF effect on the IFNγ response would be a common multiplicative gain across five inhibitors. On the acquired CXCL9 assay, the restriction is not consistently supported. The constant-interaction comparator has lower mean absolute error in three of four preparation records, and 11 of 20 gain prediction envelopes do not overlap the observed technical-well ranges. The small gain advantage in one AsPC1 preparation does not repeat in its paired preparation. This closes the shared-gain line under these assay conditions.

The result is a scoped boundary. It does not establish a molecular mechanism, a new Agent policy, external transfer, or assay savings. The response is fluorescence from a capture-bead sandwich assay for secreted CXCL9; the exported PE channel is not a calibrated secretion concentration or a cell-count readout.

## Brief, evidence and closest prior

The round sought one simple, consequential Agent × virtual-cell principle for drug discovery using cheap public functional screens. A valid claim had to preserve the observed cell/background, drug, dose, time, endpoint and repeat identities. Generic active learning, VOI, hierarchical updates, logic-ODE wrappers and benchmark gains were comparators.

The closest current target prior is *Active learning-guided mechanistic modeling reveals context-specific regulators of CXCL9 expression in pancreatic cancer cells*, **Molecular Systems Biology** (2026), DOI `10.1038/s44320-026-00221-w`, PMC13434641. Its original paper and pinned repository already couple a prior-knowledge logic-ODE model to greedy/uncertainty acquisition and wet-lab drug-combination follow-up. Methods state two PDAC lines, 24-hour exposure, line-specific cytokine doses, 5 μM inhibitors, two independent screens with technical duplicates, and a CXCL9 bead assay. The paper also reports inhibitor-specific cytokine response patterns. A generic “Agent plus mechanistic virtual cell” claim therefore overlaps a direct prior.

Other inspected evidence sharpened the boundary: MultiVCDiff (Cell Reports Methods, 2026) joins perturbation-level averaged RNA with morphology but does not establish matched cell×drug×dose×time covariance; a 2025–2026 systematic drug-response comparison already owns ordinary basal/shared/perturbation/residual decompositions; ChemScreener (2026) is a direct active-learning hit-discovery comparator on WDR5 protein HTRF, not a cell functional endpoint; and the Cancer & Metabolism CAF/LPC screen (2025) already owns a two-assay environment-rescue-blocking criterion. Its advertised workbook could not be recovered completely, so it is not a qualified paired resource for reanalysis. Full locators and access limits are in [evidence audit](evidence/evidence_audit.md) and [blind source map](scout/source_map.md).

The blind cross-field scout found no defensible new principle. Sufficient Decision Proxies, learning-progress task allocation and CoDA-style failure controls map to ordinary decision-focused prediction, active multitask learning and residual-slice control. They remain useful comparators for a later round, not innovations here.

## Candidate I301.v1 and test

The candidate was frozen in [candidate_v1.md](development/candidate_v1.md). For preparation `p`, inhibitor `d`, and cytokine states 00/10/01/11, it predicted

```text
V[p,d] = Y[p,d,1,1] − Y[p,d,0,1]
U[p,d] = Y[p,d,1,0] − Y[p,d,0,0]
V[p,d] = κ[p] U[p,d],  κ[p] = V[p,0] / U[p,0].
```

The same-information rivals were additive response, a constant untreated interaction, and the no-drug dual-cytokine value. All five inhibitors and all four preparation records were fixed before target evaluation. No favorable subset, fitted drug-specific gain, target-informed normalization, synthetic data, later active-learning files or protected outcomes were used.

The independent design reviewer admitted the exact narrow MFI audit after clarifying that H_gain is ordinary proportional/rank-one response, that B_const is the essential comparator, and that the test cannot separate biological amplification from nonlinear assay/readout effects. All four control-only gates passed. The primary analysis used per-preparation/per-technical-well IQR trimming; the source R script instead pools the two labeled samples within each condition (and combines preparation files in its original experiment). This is a deliberate preparation-holdout analysis convention, not an exact source-code reproduction. A post hoc source-like sensitivity was run separately and did not change the negative direction.

## Observed result

The primary run used 192 wells from four official raw CSVs at repository commit `b654a45faf5a80cdb1b514188cc90af8c9565b85`: BxPC3 E3CA/P12 and E3CB/P14, AsPC1 E3DA/P12 and E3DB/P14. Each file contains four cytokine backgrounds, no inhibitor or one of five inhibitors, and two labeled technical samples. The endpoint column was never treated as a cell count; bead events were trimmed and summarized to two well means per condition.

| Preparation | Gain MAE | Additive MAE | Constant-interaction MAE | Gain − constant |
|---|---:|---:|---:|---:|
| E3CA | 0.907222 | 0.332121 | 0.447514 | +0.459708 |
| E3CB | 0.403401 | 0.635928 | 0.376609 | +0.026792 |
| E3DA | 0.489592 | 0.669859 | 0.499654 | −0.010062 |
| E3DB | 1.237203 | 1.338385 | 1.207022 | +0.030181 |

Errors are absolute prediction error divided by each preparation's untreated dual-minus-blank MFI. They are descriptive, not confidence intervals. The unweighted four-preparation means were 0.759354 (gain), 0.744073 (additive), 0.632700 (constant interaction), and 0.775231 (no-drug control). The source-like pooled-sample sensitivity gave gain/constant MAE pairs of (0.911970, 0.447325), (0.408933, 0.378174), (0.490819, 0.500479), and (1.279495, 1.261254), preserving the same three-of-four constant-interaction advantage.

The primary computation was independently reimplemented before the primary result was read: 1,205 scalar/hash/Boolean checks had zero discrepancies at relative `1e-9` / absolute `1e-7`. The independent calculation and source-like diagnostic are summarized in [review](review/numeric_review.md) and [source-like review](review/source_like_review.md). Detailed per-well result payloads remain local and are not part of this publication. Reproducibility of arithmetic is not scientific validation.

## Decision and limits

**I301.v1: PARKED / NOT SUPPORTED under the inspected CXCL9 MFI conditions.** Do not fit a drug-specific rescue, rename the ordinary rank-one relation, or promote any code to `src/` or `tools/`. The observed deviations are a useful assay-specific boundary: future Agent reuse must test direct joint conditions or a separately justified interaction model. Three calibration drug observations to avoid one joint target are more expensive than direct measurement, so no acquisition advantage was demonstrated.

The most useful next branch is a changed resource or question, not another sampler on this same matrix. A candidate would need a genuinely cheaper action contract, a matched independent functional endpoint or preparation, and a prospective comparison against direct measurement, random/fixed panels, ordinary shrinkage/interactions and the source's mechanistic active-learning baseline. The current files provide no such evidence. No core promotion is authorized by this round.

## Accounting and reproducibility

The declared round budget was six bounded search/expansion passes, 160 public requests, 512 MiB bodies, 30 CPU-minutes, and two DeepSeek support calls. This round used six substantive passes, at least 26 worker-ledger public requests (13 target evidence and 13 blind source scouting), four pinned source-code fetches, and two official model-document routes. The target pass saved 12,405,633 bytes including partial responses; the scout recorded 1,418,225 known bytes. One independent design pass, one independent numeric pass, one source-like diagnostic, and two isolated DeepSeek calls were completed. Effective native model settings and paid costs are unknown; DeepSeek requested `deepseek-flash`, returned telemetry, but effective backend and paid cost are unknown. No protected data, wet-lab work, GPU training, author code execution, installation or core-code change occurred.

Published files: [protocol v1.1](protocol_v1_1.md), [execution decision](review/execution_decision.json), [target audit](evidence/evidence_audit.md), [independent numeric review](review/numeric_review.md), and [round record](record.md). Raw assay exports, detailed numeric outputs, full source response bodies and the supplementary PDF remain in the local episode; this GitHub snapshot is not a complete data-level replay package.
