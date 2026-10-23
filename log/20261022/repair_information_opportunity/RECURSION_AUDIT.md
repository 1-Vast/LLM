# Independent recursion / repair-information audit

Status: REVISE the proposed new fitting experiment; GO for the strictly derived historical-menu oracle screen described below. No new core mechanism, learnable routing benefit, world-model necessity or RSI benefit is established.

Author: `/root/recursive_distinct`. Date: 2026-10-22. This opinion was formed from historical source code, protocols and reports, before reading any other new reviewer opinion or any numeric entries in the historical Q tables. No model, dataset or checkpoint was loaded; no training, prediction, API call or experiment was executed for this audit. Historical PTV final outcomes are already exposed. Protected reserve assets were not accessed.

## 1. Material correction to the starting premise

The original Q already implemented a substantial part of the proposed repair menu. In `research/dual_core_innovation_validation_20261021/ptv_feedback.py:14-15,29-48`:

| Saved arm | Parameters updated | Loss used |
|---|---|---|
| none | none | none |
| func | head_x, drugs_conv2, fc1, fc2 | functional BCE only |
| mol | linear_input, conv1, conv1_norm, conv2, f1, f2, layer_final | masked 24h molecular MSE only |
| both | union of these two blocks | 0.8 BCE + 0.2 molecular MSE |

Only the listed parameters are passed to AdamW. This is actual parameter-block updating, even though other parameters were not assigned `requires_grad=False`. The old Q must not be described as only a modality ablation with every parameter optimized. A changed state pathway can alter phenotype predictions through the unchanged `head_x`; molecular effects are not structurally blocked from phenotype. The old model's top-of-file claim of no cross-protein interactions is also not authoritative: GroupNorm introduces coupling, as the repair amendment already records.

`eval_Q.py:18-21,46-101` fixes three support drugs by training-only rates, excludes all three from target scoring, evaluates every repair from the same base model within a background, and already includes B1/M0/W functional-kernel updates plus Cmol. `final_eval.py:102-127` uses only the three ten-step, 1e-4 repair actions, not the larger standalone nine-action grid. This produces four M1 actions plus fifteen conventional score/kernel actions and Cmol, subject to Cmol availability.

Repair1 is a different experiment: its transfer uses two support drugs, functional feedback for the first and molecular feedback for the second; all parameters update after each observation (`run_replay.py:153-174`, `repair_model.py`). It does not supply the missing cross-background diagnostic routing comparison. Nor do its API-selected query programs answer fixed-feedback-packet repair routing.

Consequently, the **menu itself is old**, while the narrow question of whether support diagnostics predict which already defined action transfers best across backgrounds remains unanswered by these inspected implementations. A genuinely same-joint-loss state-only update would be a different, unexecuted action: old `mol` does not measure it. This distinction is essential to the scope of an oracle stopping conclusion.

## 2. Current revised assignment: historical-menu oracle first

During this audit the parent cancelled new repair fitting and proposed a derived necessary-condition screen on the saved original final Q table. I support that change. It is cheaper and more decisive than fitting a router when even a clairvoyant selector might lack useful headroom.

Use the seven original final backgrounds only as the primary stage: the original final M1 seed-0 checkpoint trained on dev+selection is common to them. Do not mix selection tasks, whose held-lineage training construction differs, or repair1, whose base model trained only on development lineages and whose drug pool differs. Do not rerun updates, add hyperparameters, change support drugs or access new reserves.

Prespecify the following finite sets by exact saved arm names:

1. R: M1 none / func / mol / both, with the saved ten-step settings.
2. R plus a B1:none fallback.
3. R plus Cmol, with a B1:none fallback when Cmol is unavailable; also permit the B1 action as an explicit choice if the intended set is a superset of item 2.
4. The complete saved twenty-arm set, conditional on authenticated availability. Its envelope is an intentionally generous superset diagnostic, not a new repair algorithm.

The primary comparator is the **fixed** B1:none already selected as the strong conventional reference; report Cmol and B1:kernel2 separately. Do not choose whichever comparator makes the envelope look favorable. Use Q's precision@5 margin 0.09, equivalent to 0.45 expected hits among five nominations. The agent experiment's 0.40-hit margin is a different contract.

Let s_ir be saved precision@5 for background i and available action r. For a fixed nonnegative set of background weights w_i summing to one, compute

    U(R, B1) = sum_i w_i * (max_{r in R_i} s_ir - s_i,B1).

For every selector that returns exactly one of those saved actions, including a randomized selector whose expected score is a convex combination of their saved scores, its observed mean advantage over B1 is at most U. Taking the maximum after averaging would answer the fixed-action question instead and is the wrong envelope. A selector able to synthesize a new ranking, average probabilities, acquire different feedback, change an update rule, or improve model parameters outside the menu is not covered by this inequality.

If U < 0.09, useful improvement of at least that size is impossible **for this finite menu on these exposed observations at those weights**, even with perfect action choice. Stop fitting a router for that exact contract. If U >= 0.09, the necessary condition passes and nothing more follows: no evidence of learnability, affordability, generalization or mechanism novelty has been produced. Equality should not silently become either a strict-positive success or a strict-below-margin stop.

## 3. Strongest logical objections and required corrections

1. **Scope escape is the largest risk.** Failing the old-menu envelope cannot rule out a new state-only update using functional plus molecular loss, a different trajectory model, a new action, a prediction ensemble, a different support acquisition policy, or virtual cells/RSI generally. Write `STOP_ROUTING_THIS_SAVED_MENU_ON_THIS_EXPOSED_CONTRACT`, not a universal stop. Conversely, adding unexecuted actions after seeing a failed envelope is a new proposal requiring a recorded reason and new precommitment, not repair of the same analysis.
2. **Selection and test-model mismatch.** Original Q selection and final should not be pooled as if they were identically initialized routing tasks. Keeping final seven separate avoids that mismatch for this necessary bound. It supplies no independent held-out evaluation: all seven are exposed historical data.
3. **Availability and pairing.** Reject duplicate cell/arm keys; check exact arm coverage, finite precision values, matching support count, target count and prevalence within each cell. Use code/provenance to establish unchanged target identities, not equal target counts alone. Cmol is conditionally emitted only when support measured-state features exist. Missing is not zero, and post hoc complete-case removal changes the contract. A declared B1 fallback preserves a total policy if B1 exists. The table alone cannot prove all target identities; record that limitation rather than pretending scalar equality authenticates them.
4. **Weights and replication.** Preserve the original per-background point-estimate weights for the primary historical comparison; identify unique lineages and any duplicate stocks explicitly. A per-stock argmax is at least as generous as forcing a shared action per lineage, so it remains an upper bound for that restricted selector. It must be called a per-stock oracle, and lineages remain the unit for any descriptive uncertainty. Drugs/proteins are not extra independent tasks.
5. **This is an optimistic performance bound, not a fair-budget measured algorithm.** The oracle freely sees target labels to choose actions; R+Cmol can receive all support information without acquisition or selection costs. That optimism is appropriate for a necessary screen. It cannot be reported as realized method performance, an equal-budget router/search comparison, or molecular information efficiency. A low envelope is especially informative under this generosity; a high one is not a deployable gain.
6. **Observed-score bound is not a biological-population bound.** The maximum exploits noise and can overstate real opportunity. Even U below margin is a mathematical statement about saved realized scores, not proof that an unseen-population expected effect is below margin. No additional router-fitting expenditure is justified merely by a noisy positive maximum. Intervals obtained by resampling a maximized table are descriptive and do not repair exposure or winner selection.
7. **Fallback ambiguity.** Specify whether Cmol/B1 is an availability fallback or an oracle-selectable two-action set. They differ if Cmol exists but performs worse. For the most generous stopping screen, use explicit R union {Cmol if available, B1}; name it that way. Do not decide fallback behavior from labels and later describe it as an operational rule.

For auditability, output all cells, exact available action sets, comparator score, rowwise maximum, all tied maximizing action names and difference; then derive the mean. Check monotonicity as sets expand. Ties can be resolved lexicographically for display without changing the bound. Verify the inequality for the fixed saved actions and any explicitly evaluated mixture of **scores**; averaging probabilities then reranking is a new action and is not a score mixture.

## 4. What would remain if a menu passed this screen

Do not infer a new core from a passed necessary gate. Old Q already contains ordinary parameter adaptation, and diagnostic action selection is ordinarily contextual algorithm selection. It may still have practical value, but a distinctive technical contribution needs an actual rule and evidence beyond that description.

Only a separately preregistered development study could ask whether molecular diagnostics add predictive information. A minimal version would compare a fixed low-dimensional functional diagnostic selector with the identical selector augmented by prespecified molecular residual features, source-best complete repair, ordinary contextual selectors using the same features, and complete finite search. All task-local repairs would start from one hash-bound checkpoint W0, use the same fixed three-drug packet and target exclusion, and use a common full-batch step schedule. Reusing sequential `FeedbackBackend.observe` would give different optimization histories as observations accumulate and would not be an adequate fixed-packet comparison. Cross-fitting must group entire lineages, standardize inside folds and keep any tuning inside source folds. Tiny independent n is a severe limitation.

No such fitting is authorized by this audit, and no new code for it was written. In particular, a new common-joint-loss state-only action would require fresh execution and cannot be smuggled into the saved-table screen.

## 5. Reusable evidence and substantive decision

- Reuse saved `RUN/final_eval/Q_per_background.csv` only after a separately sealed identity/availability/aggregation protocol. Do not run `final_eval.py` or `eval_Q.py` to regenerate it.
- Reuse `ptv_feedback.py`, `eval_Q.py`, and `final_eval.py` as provenance of the action definitions, support rule and metric; they are not new methods.
- Repair1's seeded `build_model`, `parameter_id`, input-only boundary and poisoning tests would be reusable for a future approved fixed-packet implementation, but the sequential observation optimizer itself is not the needed batch router evaluator.
- Keep original frozen files intact; new derived scripts belong under `research/`, and protocol, audit, hashes, outputs and decisions under `log/`.

**Decision:** GO for the bounded, derived historical-menu oracle necessary gate; REVISE the broader hypothesis to acknowledge original Q's existing block repairs; STOP new router fits until the gate is evaluated and independent reviewers agree on its exact limited interpretation. No RSI claim is supported here. Even a successful diagnostic selector would need later common-start improver transplantation and old/new improver comparisons to establish improved improvement, plus successor takeover to show inherited gains.
