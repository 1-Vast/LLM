# Actual reciprocal cross-review: saved-result audit

2026-10-23 Asia/Shanghai. After completing my independent result review, I read `result_interpretation_independent.md` and `DECISION.md`. I sent the interpretation reviewer two concrete challenges through the collaboration channel and received explicit replies; no new experiment, retraining, or protected-label access occurred.

## Independent agreement

The interpretation review independently reproduces the saved MSEs, 14.0321% versus 15.9343% relative gains, +1.9022 percentage-point difference, and 4/5 positive paired fold differences. It correctly treats these as overlapping-training folds in one biological context, not five independent tasks. It also correctly refuses to interpret the chosen endpoint's larger raw MSE or higher MSE/quadratic ratio as an easier/cleaner task. Our results agree on retaining the exact predeclared descriptive direction while refusing new-method, WM, agent, inheritance, and RSI claims.

## Challenge 1: ten unselected candidates did not meet the stop heuristic

I challenged the risk that `selected_nuclear_stop_heuristic_unmet == 0` could erase the 10/80 nuclear candidate/refit records that reach 2,000 iterations without satisfying the objective-change heuristic. All are RNA inner candidates at penalty .0005, and none is selected. The peer explicitly agreed that “all fits converged” would be false and that all selected inner/outer fits meeting the heuristic is the valid limited statement.

The peer strengthened the objection: these unselected candidates still participate in the argmin, so non-selection does not make their finite optimization irrelevant. I agree. The saved result belongs to the fixed finite algorithm and fixed search menu. It does not certify fully optimized candidate objectives or method optimality. This does not overturn the arithmetic or the predeclared fixed-recipe directional branch, and neither reviewer recommends outcome-driven reruns, dropping candidates, or extra search.

## Challenge 2: compute cost is not matched

I challenged the unequal fit costs: RNA nuclear takes 71.08 seconds versus identity nuclear 7.28 seconds, approximately 9.77×. The peer explicitly agreed that matching labels/folds/three-candidate menus does not equalize total computation. A cheaper strong predictor or additional same-cost prediction/search opportunities remain unexcluded explanations. WM necessity and equal-total-budget superiority are not established.

`DECISION.md` already discloses unequal computation and qualifies outer stopping. Both reviewers recommend including the specific 10-candidate and 9.77× observations so those limitations are reviewable rather than only generic caveats.

## Clarification of absolute gain

I asked the peer to narrow the statement that the larger absolute gain rules out a solely ratio-denominator phenomenon. The peer clarified that this rules out only the pure arithmetic case of constant absolute gain with a changing denominator. It does not eliminate target scaling, different priors, residual structure, guide efficacy, or survivor selection. I agree; no causal alignment claim follows.

## Final cross decision

**No unresolved substantive disagreement.** Preserve `DESCRIPTIVE_DIRECTION_SUPPORTED` for the fixed finite recipe, with explicit convergence and cost limits. No method promotion, causal interpretation, noise repair, architecture expansion, or RSI escalation is warranted. Stop this endpoint-comparison branch after recording and sealing it; proceed only through a distinct mechanism gate with strong same-information and total-cost controls. This cross-review is an actual exchange of challenges and replies, not independent arithmetic replication or biological confirmation.

## Final corrective-state check

After the exchange, I inspected the actual updated files. `DECISION.md` now explicitly records all ten unselected inner candidates reaching 2,000 iterations, limits the zero flag to selected fits, and reports 71.08 versus 7.28 seconds (9.77×). `audit.py` now asserts exact endpoint/model coverage for score rows, exact endpoint/fold/model coverage for fold rows, and exact endpoint/fold/model coverage for selection records. Together with the existing row counts, these close the saved-key coverage limitation identified in my independent review. These are disclosure and saved-output audit corrections; no model fit, prediction, scientific outcome, or predeclared decision rule changed. I did not rerun the sealing audit as part of this cross-review.
