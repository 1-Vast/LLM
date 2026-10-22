# Dead-stock information gate: target qualification abort

2026-10-22. **Decision: TARGET_QUALIFICATION_ABORT / ABORT_INVALID_TARGET.** Stop this registered HCT116 observation/transform configuration. The dead-channel information hypothesis has no performance result. The full virtual-cell/drug-discovery/agent/inheritance/RSI goal remains ACTIVE / NOT_ACHIEVED.

## Question, application and frozen comparison

The proposed application was early functional drug-response triage: use the same exported 0–24 h live-labeled prefix, time, concentration and opaque source context to predict the 72 h live-labeled image-panel mean. The exact target was log2(mean(intersect_live_cells)+1), not an authenticated whole-well viable-cell count. Would a full early dead-stock history improve this forecast beyond live-only, D0-only and D24-only information?

[The frozen protocol](HCT116_GATE_PROTOCOL.md) fixed eight leave-one-concentration-out folds, concentration-grouped inner selection and 14 same-budget direct configurations per information arm, with ordinary constant net growth and two-live-compartment/dead-clearance comparisons. Useful primary information gain required both 0.05 log2 units and 10% error reduction; a dynamic-history claim additionally required these margins over both D0 and D24. These grouped cross-fits were not a globally untouched confirmation set. Frames, images, wells, doses and optimizer starts are not independent research tasks.

Only the DoseResponse asset was used. The primary says it incorporates prior 0/12 micromolar data; this forbids treating its sibling Replicates CSV as an independent run. The actual dose label 12.5 was not silently equated with that prose. Source labels called seed remain opaque, not authenticated biological contexts or run identities. The Replicates values were not used.

## What ran and why it stopped

One attempt completed 192 prefix-only local kinetic fits across 96 wells and two information arms, using 768 starts. All starts reported numerical convergence and finite feasible values. The prefix cache was saved before future target access. The first outer fold then failed during training-label conversion with invalid_observed_readout. Some 72 h training values had already been converted: no claim of complete future-label blindness survives that attempt.

**Zero direct fits, validation trials, fold predictions, combined predictions or performance scores were produced.** The numerical convergence flags do not identify latent injury/birth/death parameters or establish useful predictions. The stopped session is terminal; the gate was not restarted.

[A separately registered post-failure diagnostic](TARGET_FAILURE_AUDIT_PROTOCOL.md) opened all 288 image-level 72 h live-labeled values and only the dead/total fields on invalid rows. It found four finite negative values, no missing/malformed/nonfinite values, all at 25 micromolar:

| Well / opaque context / image | Exported live | Total | Dead |
| --- | ---: | ---: | ---: |
| H7 / mcer-1e3 / 1 | -2 | 142 | 144 |
| H12 / mcer-3e3 / 1 | -24 | 357 | 381 |
| H12 / mcer-3e3 / 2 | -1 | 468 | 469 |
| H12 / mcer-3e3 / 3 | -15 | 472 | 487 |

H7's three-image mean is 26/3, positive but incompatible with the frozen per-image nonnegative guard. H12's mean is -40/3, so log2(mean+1) is undefined over the reals even if aggregation preceded qualification. This is not merely an overly strict image-level guard on otherwise valid well means.

All four bad rows exactly satisfy live=total-dead. The legal prefix also satisfies this approximately, with maximal absolute well-mean residual 7.82e-14. This authenticates difference-compatible arithmetic in the checked records; it does not identify exporter intent, background correction, mask overlap, a suitable signed likelihood or true viability. The entire source is not declared useless. Nonnegative total would not certify viability or answer the same question.

No clipping, well/dose/image deletion, imputation, target substitution, time-window change, new likelihood or rerun was used. Remaining future dead/total values stayed numerically closed except the four specified records. All 72 h live values are now diagnostically exposed and cannot be relabeled as blind confirmation. See the [exact diagnostic](data_auditor/target_failure_audit/DIAGNOSTIC.json), [report](data_auditor/target_failure_audit/REPORT.md) and [field-access debate](data_auditor/target_failure_audit/POST_FAILURE_CROSS.md).

## Independent review, opposition and novelty

Three positions produced independent drafts and then actual bidirectional challenges and replies:

- Mechanism advocate: [independent draft](advocate/INDEPENDENT.md), [initial cross-debate](advocate/CROSS.md), [post-failure independent draft](advocate/POST_FAILURE_INDEPENDENT.md), [raw exchange](advocate/POST_FAILURE_RAW.md), [final review](advocate/POST_FAILURE.md).
- Scientific skeptic: [independent draft](skeptic/INDEPENDENT.md), [initial cross-debate](skeptic/CROSS.md), [pre-run resolution](skeptic/PRE_RUN_RESOLUTION.md), [56-check post-run audit](skeptic/POST_RUN_AUDIT.json), [post-run review](skeptic/POST_RUN_REVIEW.md), [actual post-failure cross-examination](skeptic/POST_FAILURE_CROSS.md).
- Source/data auditor: [independent draft](data_auditor/DRAFT.md), [cross-outcome](data_auditor/CROSS_OUTCOME.md), [file-overlap addendum](data_auditor/SOURCE_OVERLAP_ADDENDUM.md), [target diagnostic and final cross-review](data_auditor/target_failure_audit/REPORT.md).

All three distinguish observation qualification failure from a negative channel-information result. They reject both global dismissal of the source and a total-target rescue. There is no unresolved disagreement on the present stop. The unresolved evidence concerns exporter semantics, negative-value construction, appropriate observation models and actual conditional information value.

Algorithmic novelty is currently **NONE**. BESTDR 2026 (DOI 10.1158/0008-5472.CAN-25-1181) already supplies joint birth/death inference and related measurement handling. Gross et al. 2023 (DOI 10.1038/s41467-023-39122-z) supplies phase-specific linear-chain/Erlang dynamics and measured combination final-count predictions. The 2026 ROS/proliferation feedback study (DOI 10.3389/fcell.2026.1756238) supplies another relevant dynamical feedback precedent. Two bounded recent-literature searches are retained, not claimed as exhaustive novelty clearance.

Under fixed known live-growth rate, a clearance-only change cannot alter future live dynamics. With unknown rates, ordinary joint inference may gain from dead observations; the fixed-rate identity does not prove general uselessness. Conversely, extra-channel predictive gain, if later established, would not itself identify turnover, establish a world-model advantage or imply an agent/RSI mechanism. The strict conditional empirical contrast is distinct from the component precedents, but this attempt did not measure it.

## Contribution status and retained historical stop

| Required claim | Current status |
| --- | --- |
| Full D history beyond identical live prefix, D0 and D24 | NOT_TESTED: invalid registered target |
| World dynamics beyond strong same-information direct prediction or ordinary fitting | NOT_TESTED |
| Agent decisions beyond fixed policy, active learning and equal-budget search | NOT_TESTED |
| Weight/procedure inheritance beyond ordinary retraining and continual learning | NOT_TESTED |
| Joint world-agent-inheritance utility beyond simple mixtures | NOT_TESTED |
| Improving the improvement strategy increases later improvement effectiveness | NOT_TESTED; no RSI result |

The previous [functional-dynamics decision](../functional_dynamics_gate/DECISION.md) remains unchanged: its simple net-growth/shrinkage configuration failed its useful-gain gate and exact Gamma–Poisson empirical-Bayes novelty was stopped. This aborted gate neither rescues that result nor adds a second performance negative. All 124 previously inventoried files remain byte-identical.

## Next source, success and stopping conditions

Two bounded primary-linked STACK landing requests corrected an access misconception. Version 2 is HTTP 200 with embedded dataset status 404; version 1 is an actual snapshot, DOI 10.17632/3pnv5wh5jm.1, dated 2017-04-30, CC BY 4.0. Its description specifies a 1,833-compound library and three live mKate2+/dead SG+ raw-result files with all-data and QC tabs, U-2OS/T98G at 5 micromolar. The paper's 1,819 screened compounds and the repository's 1,833 library members remain distinct pending actual QC/identity evidence.

The exact raw-file IDs, names, sizes and download routes remain unresolved because the landing defers its file list. An empty loading list is not evidence of absent raw data. [The retained metadata](root_stack/V1_PROJECTION.json) qualifies a source lead, not a numerical benchmark. This phase's source scope stopped after the two registered GETs; no raw workbook was downloaded.

The next bounded task is exact manifest acquisition from a documented/current service route or a route present in retained client resources, followed by measurement/identity qualification before numerical outcomes. Success requires actual version-bound raw-file records and accessible routes, then explicit assay/field definitions, fixed-panel aggregation, treatment timing, run/replicate identities and file overlap. A missing manifest or ambiguous biological identity must be recorded at its actual level; neither justifies guessed independence. Stop a bounded route on access failure, ambiguous snapshot identity or absent raw records; do not launch fitting from a landing description.

If a new measured task qualifies, it needs a new exposure declaration, frozen endpoints/splits/features/budgets and independent opposing review. Do not reopen the aborted HCT116 gate. Only a candidate that passes the smallest information and same-information direct-model gates should receive agent/inheritance/RSI modules and their distinct fair comparisons. No new core is promoted by this phase.

## Integrity, repairs and resources

[WORK_AND_FAILURES.md](WORK_AND_FAILURES.md) records the pre-data numerical fallback bug and repair, original failed test output, post-repair nine passing tests, the post-failure feature-coordinate wording ambiguity, a truncated advocate cache projection, source extraction/parser failures, and the non-fitting verifier's corrected audit-schema assumption. Frozen experiment code/protocol/cache were not amended after outcomes.

[VERIFICATION.json](VERIFICATION.json) reports 157 passing non-fitting checks, including preservation of all 124 previous-phase files; the independent skeptic has 56 passing checks and the target diagnostic has four passing scope canaries. These overlapping software/integrity checks are not biological sample sizes. Final completed-document hashes and navigation checks are in FINALIZATION.json and FINAL_FILE_INVENTORY.json.

Resources: eight public GETs, 659,764 retained HTTP-body bytes, zero DeepSeek calls, one stopped gate attempt, 192 prefix fits / 768 starts, zero direct fits, zero new wet-lab experiments and zero author contact. No scientific performance or RSI gain was obtained. The overall research goal remains active.
