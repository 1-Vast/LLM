# Independent exact recomputation and cross-review

2026-10-22, `/root/recursive_distinct`.

My independent audit was sealed first as `RECURSION_AUDIT.md`, SHA256 `c7850e542d014af23e605ac4b3867e6af63e9fc3179781c1fa14dce6b97f5c71`. I then read `NOVELTY_AUDIT.md` and the parent's `UPPER_BOUND_PROTOCOL.md`. They address the material objections: original Q already has actual block repairs; the saved molecular action is molecular-loss-only; primary final models and secondary selection models remain separate; lawful B1 fallback is retained; an oracle is free optimistic action selection rather than an equal-budget deployment; .09 precision@5 and .40 end-to-end hits remain distinct; and conclusions are conditional on the exposed finite sample/menu. No fatal logical issue remains for that bounded calculation.

`independent_recompute.py` was independently implemented from the CSV/identity contract, without reading or importing `upper_bound.py` or reading its result. Code SHA256 `997feb2528ce46b7e714816f73de7872917482f73fd06feb1abf20e4af6f58ad` was sealed before execution. It uses exact `fractions.Fraction`, canonicalizes precision to legal fifths after a 1e-10 check, checks input hashes/bytes/schema/arm completeness/cell-lineage identity, checks within-cell support/target-count/prevalence consistency, and aggregates stocks within lineage then lineages. It computes all four menus, every tied stock argmax, the shared-action-per-lineage bound, and the three prespecified baseline differences. It also verifies menu monotonicity and dominance over each fixed member.

After the parent's primary-completion signal, the independent script ran once successfully at `2026-10-22T09:10:23Z`, HEAD `47a0e2dea5a7dd42379fa17eb3621caf6bd0114c`. Internal wall time was 0.12318090000007942 seconds; process CPU time 0.046875 seconds. Output `INDEPENDENT_RECOMPUTE.json`, SHA256 `21f964e7421e786aad2d3be027db43b68925bc5d5a0a400cfcdb39ec50781d68`. No biological fit, old update, router fit, new matrix decode or API call occurred. There were no computation errors or retries.

Only after this independent output existed did I open the primary result. `compare_independent.py` compared completed artifacts without rerunning the calculators. `INDEPENDENT_MATCH.json` records exact agreement across all three tables and twelve menus for baseline means, oracle envelopes, single-action-per-lineage envelopes, all three paired comparator differences and their hit conversion, margin decisions, every stock maximum and every tied maximizing action.

## Independently recovered main result

Primary original final table: seven stocks, seven lineages, twenty saved actions.

| Menu | Oracle precision@5 | Difference versus fixed B1:none | Difference versus Cmol | Difference versus B1:kernel2 |
|---|---:|---:|---:|---:|
| R only | 18/35 | -1/5 | -6/35 | -1/35 |
| R + B1 | 5/7 | 0 | 1/35 | 6/35 |
| R + B1 + Cmol | 5/7 | 0 | 1/35 | 6/35 |
| all twenty saved | 27/35 | 2/35 | 3/35 | 8/35 |

The primary B1 baseline is 5/7. The repair-with-fallback oracle equals B1 exactly; adding Cmol does not change it. Even the all-saved superset improves by only 2/35 precision@5 = 2/7 hits among five nominations, below the frozen 9/100 precision@5 = 9/20-hit margin. All-saved versus Cmol is also below that margin (3/35). Gains against the weaker B1:kernel2 do not alter the primary stopping rule.

The secondary sel_eval table's all-twenty envelope gain over B1 is 1/25, and the separate selection grid table's all-twenty-six gain is 2/25. Both are below .09 with equal-lineage weighting. They remain separate exposed strata and are not pooled with final or used to add final actions. In both, the R+B1 and R+B1+Cmol envelope gain over B1 is zero.

## Small reporting distinction, not an arithmetic failure

The independent `oracle_switching_gain` subtracts the best fixed action **inside that declared menu**. The primary field `versus_hindsight_best_fixed` subtracts the best fixed action in the **entire saved table**. These are different descriptive references, so the comparison deliberately does not demand equality. For R-only on final the former is zero, the latter -1/5. Label the primary field explicitly as table-global; do not call it within-menu switching regret. Neither difference affects the named-baseline gate.

## Decision

STOP routing this saved Q repair menu, including B1/Cmol fallbacks and the full saved superset, for the fixed useful-gain contract on these exposed final backgrounds. Do not collect residual diagnostics or fit a selector for it. This follows even for a clairvoyant, cost-free selector, so LLM selection, contextual selection and further search restricted to these exact saved actions cannot repair the opportunity failure on this sample.

The result does not rule out a new trajectory+joint-loss action, probability ensembles that synthesize new rankings, new supports, different models or new data. Those would be separate research proposals rather than exceptions to the tested menu. It does not prove a population impossibility or show that any agent/improver has improved itself. Existing PTV STOP remains scoped and the overall research goal remains unachieved.
