# Frozen cached-menu opportunity bound

2026-10-22. Protocol precedes scalar decoding by the new analysis. Code/table identities and arm labels were inspected; old outcomes remain exposed, so this is explicitly a new derived **development/falsification** analysis and never a preregistered independent experiment. Full goal ACTIVE / NOT_ACHIEVED.

## Scientific question and novelty of this analysis

Original Q already compared unchanged, head-only functional, trajectory-only molecular and joint repair on the same three support drugs and remaining target drugs. Ordinary direct/kernel and molecular conditional comparators exist. We do not rerun any of them. Prior mean contrasts do not determine whether *selecting different saved repair procedures for different backgrounds* could meet the fixed useful-gain threshold. The new finite-menu upper envelope answers this necessary opportunity question before spending on residual features or fitting a router. It is not a new learning algorithm or RSI test.

Primary cached source is `research/dual_core_innovation_validation_20261021/RUN/final_eval/Q_per_background.csv`, SHA256 `051b90151bc3d1d7dbabe8d08491f357946ee21f446f32bc36a5f3f75dc58b29`, 12,624 bytes, seven distinct lineages, twenty saved arms per cell. All final backgrounds use the original final-training regime. Do not pool selection/final to fit a cross-background rule: their base training regimes differ and original-final models saw selection labels. Secondary tables `sel_eval/Q_per_background.csv` and `selection/sel_Q_M1.csv` have the exact identities in CACHED_TABLE_IDENTITIES.json; describe each independently without using their different grids to supplement the final menu.

## Fixed menus and comparators

R is exactly four saved arms: `M1:none:0:0`, `M1:func:10:0.0001`, `M1:mol:10:0.0001`, `M1:both:10:0.0001`.

In particular the saved molecular arm uses trajectory parameters and molecular-only loss. It is not an unexecuted trajectory-parameter update with joint functional+molecular loss; the saved functional arm similarly has functional-only loss. A failing bound cannot exclude those different, unexecuted actions. We do not silently expand the scope of the old menu or run those actions to rescue it.

Calculate separately:

1. R-only oracle, which may be worse than a conventional baseline.
2. R + `B1:none` fallback oracle, the correct optimistic envelope for a repair router allowed to fall back to B1.
3. R + `B1:none` + `Cmol` oracle, representing a larger menu including a standard same-molecular-information predictor.
4. All *already saved* arms in that source table, including all ordinary kernel arms, as an even more optimistic universal finite-menu envelope. No new training/grid or selection-table parameters enter the primary table.

Primary comparator is pre-existing fixed `B1:none`; report `Cmol` and `B1:kernel2` separately, plus each table's hindsight best fixed arm strictly labeled as a descriptive oracle fixed policy. Do not select the primary comparator from the new outcomes. Including B1/Cmol in an envelope does not make a positive result evidence of molecular repair information, state prediction, agent contribution or RSI. Report when the winning actions are conventional.

## Exact finite-sample quantities and opportunity rule

Utility is recorded precision@5 on the original Q target pool after removing all three support drugs. Convert to exact integer hits out of five, asserting every value is within 1e-10 of a legal fifth. All arm rows within a cell must share target count, support count and prevalence. Equal-weight cells within each lineage, then equal-weight lineages. For duplicate stocks, allow cell-specific oracle choice before lineage averaging; this is an optimistic bound for any stock-aware policy, not extra independent tasks. Also report the more restrictive single-action-per-lineage oracle.

For a menu A and fixed baseline B, calculate exactly

`U(A) = mean_lineage mean_stock max_(a in A) precision5(stock,a)`

and `U(A) - J(B)`. Every policy selecting one saved arm per stock is pointwise bounded by this envelope. This is not a bound for per-drug blending, new model parameters, new observations, different supports, or actions outside the saved menu. No ensemble is inserted for free. The all-arm oracle may include various pre-existing hyperparameters but is optimistically exempted from their search costs; it is not an equal-budget performance claim.

Use the historical Q/R useful decision margin **0.09 precision@5 = 0.45 hits per five nominations**, not the distinct historical E margin of 0.40 hits. Freeze this interpretation before decoding. If even R+B1 fallback cannot reach +0.09 versus B1 on the recorded seven-lineage target task, do not collect new residual diagnostics or fit a router for that menu. If the full saved-arm superset also fails, stop its broader finite-menu route. If an envelope reaches the margin, it establishes only optimistic room; additional leakage-safe cross-fitted diagnostic learnability and total-cost comparisons remain necessary. No automatic GO for RSI.

Both a passing and failing envelope are conditional on the existing fitted models and observed exposed tasks. No population confidence interval or general impossibility claim is made. Label-informed oracle gains can be noisy and optimistic; do not bootstrap them into confirmation. Keep stage-specific and per-background values so the bound is inspectable. The hindsight best fixed policy and oracle switching regret are descriptive only.

## Verification, costs and stopping

Validate CSV hashes against metadata; unique cell/arm; complete declared menu per cell; group consistency; finite legal hit counts; oracle >= each constituent arm; fallback envelope cannot decrease when expanding the menu; lineage averaging; exact fractions and the margin conversion. A small synthetic test must catch using max of means instead of mean of maxima and incorrectly stopping a router without its lawful fallback. Independently recompute the result from source CSV in a second implementation after the primary script is frozen.

No new raw matrix, tensor outcome, protected reserve, biological predictor fit, update run, DeepSeek call or wet experiment is authorized by this protocol. Budget is one primary exact computation plus one independent recomputation on tiny existing CSVs. Legacy base-model/source costs remain historical and do not become zero; no cumulative-cost superiority is claimed. Record current HEAD, code and protocol SHA256, inputs, timestamps, CPU/wall seconds and actual errors. All evidence/results in this log tree, code/tests in research/repair_information_opportunity_20261022/.
