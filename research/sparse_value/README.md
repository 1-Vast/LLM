# Measurement Value, Cost, and Error Risk with Sparse References

This round makes local changes for two identified problems: fallback follow-up actions were not recomputed after the first measurement, and conditional measurement value could not be estimated when paired references were insufficient. Agents still select experiments and interpret real results; the world model supplies conditional readout distributions. The production architecture was not refactored, and the research model has not been promoted to the default.

## Fixed implementation errors

`research/sequence_audit/policies.py` now re-compares follow-up actions using the actually executed first measurement, its real result, the current legal menu, and the remaining budget. It no longer relies on a continuation that was absent from the original plan, and it never borrows a conditional branch from a different first measurement.

The 32 historical L1000 LT `implementation_defect` cases were replayed individually: the old behavior was reproduced exactly in **32/32** cases; after the fix, **32/32** continued measuring, with the same first measurement. All remained unresolved, adding 32 measurements and 192 assay-days, with no utility change. The engineering defect is fixed, but this is not a claim of biological decision benefit.

`P.arms(..., frozen_replay=True)` is used only to reproduce the old frozen experiment. The old `lincs_evaluate.py` and `replay.py` explicitly select this mode; new calls use the fixed behavior by default. Old experiment results were not overwritten. [Per-case proof](../../outputs/sparse_value/fallback/summary.json)

## Estimating sparse conditional branches from measured references

The new `model.py` uses measured references from the existing training fold and the registered interpreter to predict four outcomes: H1 match, H2 match, unresolved, and not detected. Wrong exclusions are always kept separate from correct exclusions.

For a hypothesis, an observed first-measurement result, and a target action:

1. **Local references** are samples from the same reference compound measured under both the source and target conditions, with a first result that matches.
2. **Parent references** are other samples under the same target condition and the same hypothesis/contrast. The entire local chemical identity/scaffold group is excluded from the parent set to avoid duplicate counting.
3. Each identity/scaffold group has total weight 1. SciPlex3 uses scaffolds; L1000 uses the existing connected components of identity/scaffold groups.
4. When parent references exist, use `alpha = local count + 2 × parent probability`. Parent probabilities use grouped counts with 0.5 smoothing for each label. The fixed 2 is a model weight; it does not count two real measurements or inflate support.
5. When no paired local sample exists but a target reference does, return an explicit `marginal_backoff`; when no target reference exists, return `value_unknown` rather than zero probabilities.

With no parent reference but a local reference, use only the local count with Jeffreys smoothing. The unconditional first-measurement distribution uses all target-reference counts with the same smoothing. A `pooling=False` ablation reproduces the limitation that only paired samples can provide service.

This depends on a specific transfer assumption: an unconditioned reference under the same hypothesis and target condition can provide limited information for a sparse conditional branch. **This does not recover the true conditional distribution from missing data.** Outputs retain local/parent reference identities, group counts, probabilities, model variance, and an upper bound on error probability so that failures of this assumption can be detected.

The model never receives held-out compound identities, true mechanism labels, or target measurements that have not been purchased. Both parent and local references come from the training fold. The interpreter's underlying training reference readouts still use leave-one-compound-out, so other references from the same scaffold may affect within-training similarity; outer grouped holdout preserves isolation, but optimistic bias in within-training probabilities still needs evaluation through held-out calibration.

## Agent decisions by net value

The new `policy.py` uses an explicit objective:

`Net value = P(correct decision) − 2 × P(wrong decision) − λ × expected number of measurements`.

For the first measurement, it enumerates conditional plans of at most two measurements and charges each branch according to its probability. For example, if two mutually exclusive neutral branches have probabilities 0.3 and 0.4 and both require a second measurement, the expected measurement count is **1.7**, not 2 or 3. Cost is part of the objective itself rather than merely a tie-breaker when returns are equal. Experimental days remain a hard budget and are reported separately.

After a real unresolved/not-detected result, the agent recomputes the value of remaining actions from the actual action and result; readout likelihood changes only **planning weights**, and does not turn the hypothesis set into a probabilistic posterior. QC failure consumes budget and triggers reselection using the unconditional prediction. Only a real measurement interpreted through registered rules updates evidence.

Stop reasons distinguish: no legal action; estimated net value is non-positive; or value is unknown for an action that has not been estimated. Even if the menu contains known non-positive actions and unknown actions at the same time, the policy does not claim that every action lacks value. When the validator itself cannot eliminate a hypothesis, prior smoothing cannot create fictitious experimental value.

The user chose to see the full cost-benefit curve, so this round reports all results for λ = **0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2**. λ is the value of one correct decision, not a currency amount, and is not treated as the user's actual cost. All baselines use the same λ for comparison.

## Frozen validation protocol

[protocol.json](protocol.json) and [freeze.json](freeze.json) froze the model, policy, cost grid, comparators, statistical method, and code hashes before the new replay. Parameters were not tuned from this round's holdout results. The old SciPlex3 and L1000 results were already used for problem diagnosis, so this round can only be called a **grouped holdout replay on existing data**, not independent new-data validation.

There are four tiers: SciPlex3 A/B and L1000 LT/T, each run with five folds. A single `run_matched` executes at most two measurements, non-decreasing time, no repeated actions, a shared QC-continue rule, and a shared budget. Comparisons include the old fallback, fixed fallback, original two-step policy, fixed sequence, and the unconditional discrimination selector.

At λ=0.02, three additional ablations are compared: `marginal-only`, which removes the conditional response distribution but keeps first-measurement planning weights; paired references only; and shuffled training mechanism labels. λ=0.02 is a frozen ablation display point, not a cost selected from the results.

The report covers correct rate, wrong rate, original utility, measurement count, days, same-cost net value, gain per additional measurement, stop reason, and predictive calibration of selected measurements. Intervals use 2,000 paired component/scaffold bootstraps; L1000 additionally reports batch-cohort sensitivity. Predictive uncertainty is diagnostic under the current model assumptions and does not cover parent-distribution estimation, conditional transfer, or batch bias; it cannot be called a validated 95% risk guarantee.

Prediction distributions come from QC-passing reference samples; future assay-failure probability has not been estimated, while the actual replay still charges the cost of failed measurements. The cost curve is therefore an empirical comparison under this dataset and execution rule, not an economically optimal conclusion transferable across laboratories.

## Observed results and supported claims

A total of **186,420 real-data replay records** were completed across 20 dataset/tier/fold combinations and 15 strategy/cost settings, all passing the shared execution-constraint checks. All model and analysis code hashes still match the frozen values.

**L1000 LT: the new method fixes part of the old fallback's “more measurements, low return” problem on this dataset.** At the prespecified ablation point λ=0.02, across 6,880 episodes:

| Strategy | Correct decisions | Wrong decisions | Total actual measurements |
|---|---:|---:|---:|
| Original fallback, retaining the early-stop defect | 815 | 34 | 6,666 |
| Fixed fallback | 815 | 34 | 6,698 |
| New sparse conditional-value policy | **851** | **27** | **6,357** |
| Simple marginal-only control | 836 | 22 | 6,274 |
| Unconditional discrimination selector | 832 | 30 | 6,702 |
| Fixed sequence | 732 | 39 | 13,312 |

Compared with the fixed fallback, the new method makes **341 fewer measurements, 36 more correct decisions, and 7 fewer wrong decisions**; mean original utility increases by 0.00727 [0.00062, 0.01454], and same-cost net value increases by **0.00826 [0.00157, 0.01540]**. The batch-clustered net-value interval is **[0.00032, 0.01597]**. The interval for the correct-rate increment alone, **[−0.00134, 0.01233]**, still crosses zero, so the point-estimate difference in correct counts is not a proven correct-rate improvement.

Compared with the simpler marginal-only method, net value increases by only **0.00049 [−0.00547, 0.00599]**; compared with the unconditional discrimination selector, by **0.00464 [−0.00187, 0.01104]**. Thus it is better than the old fallback here, but the complex conditional model has not been shown to be more practical than the simple reference method.

**Direct ablation of sparse-reference borrowing:** at λ=0.02, correct decisions in SciPlex3 A increase from **128/336** with paired-only to **152/336**, while wrong decisions remain **12/336** and 71 additional measurements are used; the net-value difference is **+0.0672 [0.0167, 0.1210]**. The tier B net-value difference is **+0.0387 [0.0177, 0.0586]**. This supports the repair direction that measured references can help estimate value when exact pairs are missing. However, the fixed sequence still has **215/336** correct decisions in tier A, so the new method does not close the full gap.

The complete cost grid below reports the new method minus fixed fallback mean net value, avoiding display of only a favorable price:

| Measurement cost λ | SciPlex3 A | SciPlex3 B | L1000 LT | L1000 T |
|---:|---:|---:|---:|---:|
| 0 | +0.0268 | −0.0079 | +0.0081 | +0.0075 |
| 0.005 | +0.0238 | −0.0113 | +0.0081 | +0.0067 |
| 0.01 | +0.0239 | −0.0123 | +0.0078 | +0.0061 |
| 0.02 | +0.0161 | −0.0100 | +0.0083 | +0.0049 |
| 0.05 | −0.0015 | −0.0123 | +0.0107 | +0.0085 |
| 0.1 | +0.0045 | −0.0163 | +0.0259 | +0.0021 |
| 0.2 | +0.0274 | +0.0075 | +0.0806 | +0.0294 |

The SciPlex3 A/B net-value intervals relative to the fallback cross zero at every listed price. The L1000 LT component interval is positive at every price; the T evidence changes with price, so universal benefit cannot be claimed. A high-price relative gain may only mean that fewer expensive measurements are taken: **at LT λ=0.2, the new method's own net value is −0.00552**, still below the zero net value of measuring nothing. “Smaller loss” cannot be described as “worth implementing.” Intervals against every baseline and every price are in the [full results](../../outputs/sparse_value/evaluation/report.md).

![Complete cost-to-net-value curves](../../outputs/sparse_value/evaluation/cost_curves.png)

[Measurement-count/correct-rate curve](../../outputs/sparse_value/evaluation/decision_frontier.png) · [wrong-rate curve](../../outputs/sparse_value/evaluation/wrong_risk.png) · [all statistics and batch sensitivity](../../outputs/sparse_value/evaluation/summary.json)

**Probability calibration remains insufficient.** On actually selected measurements at λ=0.02, correct-probability ECE is SciPlex3 A **0.139**, B **0.051**, L1000 LT **0.040**, and T **0.057**; tier A clearly overestimates success. LT's mean predicted wrong probability is 0.036 versus an observed 0.00425, so it remains conservative. Partial pooling does not remove all conditional-transfer and interpreter bias; output probabilities cannot be treated as exact risk guarantees.

The conclusion is: **the early-stop defect is fixed; the “sparse conditional prediction + explicit cost and error loss” policy is implemented and validated, with better net value than the existing fallback on L1000 LT, while evidence remains insufficient on SciPlex3 and superiority to simple marginal-only has not been shown.** This round delivers the complete cost-benefit curve as requested; it does not choose a price for the user or automatically switch the default policy.

## Tests and reproducibility

- In the `maestro` environment, Python 3.11.16: **1,326 runtime tests passed**; **68 related research tests passed**.
- Per-case before/after proof for 32 historical defects: the first measurement is unchanged and the follow-up executes correctly.
- The 185 SciPlex3 scaffold groups and 335 L1000 connected components do not cross outer training/test folds.
- Independent reruns of SciPlex3 A fold 1 (**720 records**) and L1000 T fold 1 (**8,820 records**) match exactly in every field.
- The 186,420 records have zero violations of budget, time ordering, duplicate-action, QC, or evidence-update constraints; code hashes match the frozen record.
- This round's numerical analysis and replay need no API; no new paid API request was made.

[Verification record](../../outputs/sparse_value/evaluation/verification.json)

## Reproduction commands

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m pytest research/sparse_value research/sequence_audit/test_sequence_audit.py -p no:cacheprovider
& 'D:\anaconda\envs\maestro\python.exe' research/sparse_value/verify_fallback.py
& 'D:\anaconda\envs\maestro\python.exe' research/sparse_value/evaluate.py
& 'D:\anaconda\envs\maestro\python.exe' research/sparse_value/analyze.py
& 'D:\anaconda\envs\maestro\python.exe' research/sparse_value/plot.py
& 'D:\anaconda\envs\maestro\python.exe' research/sparse_value/verify_replay.py
```

`evaluate.py` checks frozen code hashes. New records are written under `outputs/sparse_value/`; they do not overwrite the old `sequence_audit_20260926` results.

To call the new policy directly, the caller supplies measurement cost:

```python
from policy import make_policy
arm = make_policy(cost_per_measurement=chosen_price)
record = P.run_matched("sparse", arm, ctx, compound, truth, h1, h2, setting, qc_rule="continue")
```

Here `truth` is used only to score real-data replay; the policy and model do not receive it. In a real deployment, the agent's measurement interface must provide the result.
