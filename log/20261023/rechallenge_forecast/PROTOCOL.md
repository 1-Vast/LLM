# Frozen-design proposal: early feedback and future density across declared experiment files

2026-10-23. ACTIVE / NOT_ACHIEVED. Previous turn PROGRESS. This is a necessary ordinary functional forecast diagnostic, not a novel algorithm, clinical schedule recommendation, independent culture confirmation or RSI test. All code research/rechallenge_forecast_20261023/; all evidence this directory. No new Cell Density number has been decoded before this protocol draft.

## Data, units and lawful use

Use only cached transition_exp3.body/transition_exp4.body from log/20261023/rechallenge_task/root/, fixed Gitlab commit27f21feb7590ff6cfab9c5147796008a8d92d58d, DOI10.1038/s44320-025-00150-0. Treated sheets AAAA and ANAN have actual A-column times0/24/48/72/96 and B-column stained dish area-density responses. Evaluate raw released numeric scale without percent/fraction conversion or normalizing by day0. All finite raw values are retained; unknown/missing required values, duplicate/missing times, formulas or nonnumeric cells stop the whole comparison. No outlier filter, epsilon, clipping, endpoint deletion or alternative transform. Finite predictions outside physical range remain in losses and are not repaired.

Naive sheets and all other assays are unused. C/D/E/F simulated events/times are unused. Physical regimen is from primary: fresh treatment every24h, AAAA repeated TRAIL; ANAN TRAIL then TBQ then TRAIL then TBQ. C labels in Naive do not imply actual drug. Observations are sacrificed sibling dishes, not same-dish increments or cell-state transitions. Experiment3/4 are declared-file groups, with physical independence unresolved. Primary narrative and representative figure patterns are exposed, no security-blind claim.

Two reciprocal folds: source3→target4 and source4→target3. Source treated responses allfive times may train a method. Target both treated regimes only0/24/48 are feedback; predict72/96. All methods may use identical source responses, prefix and known schedules. Source curves include other-run future-time responses legally; target endpoints must not enter that fold's prediction. Because reciprocal folds reuse each other's labels as source, they are correlated development cross-validation, not a sealed test bank. Do NOT claim all query values were inaccessible across folds. Build per-fold legal data objects containing only source full and target prefix, and compute/seal BOTH folds' forecasts before scoring either target query. This prevents scoring-driven adaptation, not cross-fold security blindness.

## Fixed ordinary comparisons, no tuning or model selection

Let k=t/24, prefix k=0,1,2; h=3,4. For each same-regimen source curve s_k and target prefix y_k:

1. persistence: y2.
2. target_linear: OLS intercept+slope in k on three target prefix values.
3. target_last_interval: y2+(h-2)(y2-y1).
4. source_curve: s_h, no target-response update.
5. source_offset: s_h+mean_k(y_k-s_k).
6. source_affine: OLS y_k=a+b*s_k on prefix. If all source prefix values exactly equal, use intercept-only target prefix mean; no near-zero tolerance or other fallback.
7. source_residual_trend: s_h+OLS trend in k of (y_k-s_k).
8. source_event: ordinary additive area-change event model. Fit d_A and d_N as means of source successive density differences grouped by assigned intervention (AAAA A/A/A/A, ANAN A/N/A/N). Initialize each forecast at target y2; add d_A for third interval, then d_A or d_N for fourth. These are cohort-density differences, not empirical deaths or mechanistically identified cellular increments.
9. pooled_event_refit: same event model fit source eight differences plus four target-prefix differences, all equally weighted; same target y2 initialization. This is ordinary refitting, not a learned updater. No target query differences are used.

Pre-response review clarification: source contains6 A/2 N differences and target prefix3 A/1 N, so each pooled mean is exactly(2/3)source-event mean+(1/3)target-prefix event mean. With the same y2 initialization, pooled forecasts are exactly that fixed mixture of source-event and target-only-event forecasts. Check this algebraic identity computationally without adding a selected competitor. This defeats any new updater/RSI-operator claim even if the utility gate passes. A denotes the TRAIL20 regimen and N denotes the entire TBQ cocktail (including TRAIL10), not an independent single molecule. Report losses in released area-density units (squared for MSE), no inferred count or fraction/percent conversion.

source_affine/offset/residual are explicit strong same-regimen direct controls. source_event vs pooled_event_refit isolates that ordinary use of early feedback; comparison to other controls determines if its restricted event structure adds anything. No agent search or world-model necessity is assumed. Formula complexity differs slightly; record runtimes, no hardware-efficiency or equal-FLOPs superiority claim.

## Metrics, success and stops

Primary MSE over raw72/96 density values; secondary MAE. Report all predictions, truths, signed/squared/absolute errors, per-file/per-regimen and equal four-group aggregate. No p-values/bootstrap independence or fabricated clinically meaningful margin.

Narrow continuation gate: pooled_event_refit has strictly lower MSE than source_event AND persistence in EACH of the four target-file×regimen groups. This tests consistent ordinary update utility, not all-method superiority. If it fails, STOP_THIS_FIXED_POOLED_EVENT_UPDATE_CONFIGURATION; do not change weight, loss, time window, scale, group or nonlinear form to rescue it. If it passes but any simple direct control is as good/better in a group, record the counterexample; no new-core or inherited-rule GO. Even uniform numerical superiority is at most exposed-development ordinary utility pending independent tasks and a distinct update operation.

Before execution obtain independent source/protocol and critic/code reviews, preserve disagreements/corrections, freeze hashes. Once only actual numeric run; retain exceptions/partial artifacts, no delete-and-retry. Independent reconstruction and reciprocal result debate follow. All world/agent/U inheritance/joint/improved-improver claims remain unestablished. This diagnostic does not replace the required current-paper mechanism search or the final fair direct/refit/CL/AL/mixture/equal-budget program-search evaluation of any future actual innovation.
