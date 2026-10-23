# Independent saved-result arithmetic and design audit

Reviewer: matched_audit; 2026-10-23 Asia/Shanghai. No models were retrained. No development/protected labels or another result review were read. Read the saved RESULT, OOF, score, fold, selection, and cost files and the audit implementation; independently recomputed saved-prediction arithmetic with `research/norman_matched_guide_20261022/review_saved.py`. Computed evidence is in `result_audit_calculations.json`.

## Verdict

**PASS for the limited predeclared descriptive direction.** The saved OOF predictions reproduce the reported endpoint MSEs and fold MSEs. The within-endpoint RNA-over-identity relative gains are 14.0321% for average and 15.9343% for chosen: difference **+1.9022 percentage points**, satisfying the predeclared `delta > 0` direction. This is not independent biological validation and not evidence of causal guide alignment, noise correction, world-model necessity, or RSI.

| Endpoint | Identity nuclear MSE | RNA nuclear MSE | Absolute MSE difference | Relative RNA gain |
|---|---:|---:|---:|---:|
| Average | 0.001309713446 | 0.001125933476 | 0.000183779969 | 14.0321% |
| Chosen | 0.002862468211 | 0.002406354712 | 0.000456113499 | 15.9343% |

The five average fold gains are 14.8192%, 7.7915%, 21.3788%, 15.7008%, and 10.1201%; chosen gains are 15.5660%, 11.9224%, 25.4206%, 14.9382%, and 11.1152%. RNA completion improves over identity completion in all five folds for both endpoints. The paired chosen-minus-average fold differences are +0.7468, +4.1309, +4.0418, **−0.7625**, and +0.9950 percentage points. Thus the cross-endpoint direction is positive in **4/5**, not 5/5 folds. Folds overlap in their training sets and share genes, so these are not five independent biological tasks; no significance or transfer claim follows.

## Accounting, selection, and stop flags

- Fit accounting is 180 total: 20 quadratic fits and 40 each for direct RNA ridge, fusion ridge, identity nuclear, and RNA nuclear. There are 40 inner-selection records, each with three candidates and a selected parameter equal to the minimum saved validation MSE.
- There are 80 nuclear candidate/refit records. **10 records do not meet the numerical stop heuristic**: every RNA-nuclear inner candidate at penalty 0.0005, across both endpoints and five folds, reaches the 2,000-iteration limit. All ten of these candidates are unselected. Every RNA-nuclear selection is 0.05 with its selected inner candidate meeting the heuristic; all selected outer nuclear refits meet it. Therefore `selected_nuclear_stop_heuristic_unmet == 0` is accurate but must not be paraphrased as “all fits converged.” The heuristic is objective-change stability, not an optimization certificate.
- Measured fit times sum to approximately 79.00 seconds: RNA nuclear 71.08 seconds, identity nuclear 7.28, fusion ridge 0.42, direct RNA ridge 0.22, quadratic 0.0035. Total wall time is 79.81 seconds. Hence the menu/label budget is matched but the model families are **not total-compute matched**. RNA nuclear consumes about 9.77× identity nuclear fit time in this finite implementation.

## Audit coverage and limits

`audit.py` checks the frozen pair-fold hash, source-only membership, 3,107 unique pairs/102 genes, endpoint truth identity, all saved aggregate and fold metrics, inner and validation pair lists against sorted outer training, argmin selection, cost counts, stop flags, acquisition body hashes and predecessor continuity. This is useful local saved-artifact verification. It does not reconstruct candidate validation predictions, certify the optimizer, provide an independent biological replicate, or repair historical provenance beyond the checked predecessor files. Its count assertions do not by themselves establish complete unique coverage of every endpoint/fold/model key, though the reviewed `compare.py` fixed loops and independently checked metric rows provide additional coverage for this run.

The full 102-gene RNA SVD/correlation preprocessing is label-free and transductive, and each endpoint changes both pair estimand and matched single-gene priors. Chosen MSE is larger on its different target; it should not be ranked against average MSE as if targets were identical. Chosen RNA MSE / quadratic MSE is 0.51374 versus average 0.45365: the descriptive conclusion depends on the specified identity-nuclear comparator, and is not a universal statement that chosen labels make prediction easier.

## Research consequence

Retain this as a qualified common-panel capability asset and report the supported predeclared direction. Do not add an agent, editor, inheritance, or RSI module on this evidence. Any next mechanism needs its own novel, falsifiable claim and same-information strong controls; protected labels remain unopened. No outcome-driven extra parameter search or rerun is warranted by these results.
