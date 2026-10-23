# Independent attempt: query-design-balanced functional updating

2026-10-23. **ONE_PRECISE_ATTEMPT / NONE_QUALIFIED_AS_NEW_CORE.** Before updating a response predictor, balance the acquired history against the *already known unlabeled query-schedule design*, rather than give observations influence solely because they are newer or more numerous. This is a concrete possible explanation of negative feedback transfer under a misspecified predictor. The complete stated operation is ordinary regularized kernel/moment matching plus weighted refitting, however; it does not establish a distinct updater or explain the OLA result. No exposed-campaign selector, new fit or rescue follows.

## Goal, current empirical evidence and prohibitions

Read the full goal, organoid_schedule_forecast/DECISION.md and relevant earlier failure scopes. Preserve the actual FAC gain from additional released history, ridge MAE16.443506 to6.555352, and the OLA worsening8.870541 to9.773148. The mean/nearest-neighbor changes in the same campaign directions matter: they do not identify a ridge-specific failure or causal biological drift. More history also changes action coverage, and the dataset uses adaptive sampling. These facts motivate a *new hypothesis*, not a rule inferred to choose which campaign should update.

The fixed ridge configuration and previously stopped consistency, death-absorption, growth/survival, prior-only and paired-search claims remain stopped. No alpha/window/scale/feature/gate choice is tested on these exposed campaigns. Biological/measurement change, misspecification with design shift, coverage and noise remain competing explanations. Neither generation labels nor a new split of their59means creates independent later tasks. No current peer report read before sealing.

The full world/agent/updater-inheritance/joint/G1-over-G0 requirements remain. Conventional components may contribute, and a new basic mathematical operator is not required. Nevertheless one must specify a substantive finite-cost/biological advantage beyond a competent implementation of those same components; an exact standard procedure with no such difference cannot be promoted merely by giving it a cell-world name.

## Actual recent primary reading:3GETs

1. Official2025–2026 adaptive-data-collection plus regression/covariate-shift query,200,946bytes, SHA25631f943e04cf03e22cab960b259f22e9b591b3e0997fbb8b4326c1e6b9f059511. No entries: retained vocabulary-search failure, not evidence that the literature is absent.
2. Broader covariate-shift regression query,200,13091bytes, SHA2561f5ef5c2efc9d70b58bd99887c83327b9b62e4b8bd0c4e146a3148c64335838a. Other returned2025/2026 papers remain metadata/abstract leads only.
3. **Spectral Algorithms in Misspecified Regression: Convergence under Covariate Shift**, arXiv2509.05106v1, first release2025-09-05T13:42:27Z in retained official feed. Original https://arxiv.org/html/2509.05106v1,200,1238339bytes, SHA2560daa8c6d82ca36fa5de35f909a31373923e45d299ab6f9300b5e3aad24ec25e7. Exact ID/title searched against local md/json before download, no prior hit in that bounded check. No claim of exhaustive project/source novelty.

Actually read the weighted empirical operator/estimator definitions, spectral filter formulation and truncated density-ratio construction. The primary explicitly assumes different input marginals with the **same conditional output distribution**, importance weights dP_query/dP_history, spectral regularization and truncation for unbounded ratios. Kernel ridge is a special case; it cites much older importance-weighting/misspecification work rather than claiming importance weighting itself as new. Its statistical guarantees do not automatically hold for these finite adaptive schedules, unknown selection laws or changing biology/assays. Projection included theorem/result passages, but no author result is reproduced or used as our experimental evidence.

No biological arrays, old raw response tokens, model fit, author code, reserve, new tasks or paid API. Native agent model/token/currency unavailable.

## One executable attempted operation

At a forecast boundary let H={(x_i,y_i)}_(i=1..n) be all legally revealed schedule/terminal-response observations and Q={x*_j}_(j=1..m) the query schedules known before their outcomes. Use the same fixed legal raw action encoding phi(x) for every method, with scales fixed from initial source history. No cell state, physical-hour semantics or hidden future response is invented.

For a separately frozen feature map/regularization, compute nonnegative design weights by

    w*=argmin_(w>=0, sum w=n)
        ||sum_i w_i phi(x_i)/n - sum_j phi(x*_j)/m||²
        +(1/n)||w-1||².

Then update the common predictor by the same fixed regularized empirical loss using w* instead of unit weights:

    theta_new=argmin_theta sum_i w_i*ell(f_theta(x_i),y_i)/n
                              +lambda*Omega(theta).

No outcome in Q enters weights or fitting. All old/new observations remain legal; none is kept because it belongs to FAC or discarded because it belongs to OLA. Source history ordering does not determine weights. The proposal is not a frozen mixture of two predictors or validation-selected “update versus freeze” gate. The quadratic weight objective with fixed1penalty is an actual finite-dimensional convex program, not a request that an LLM invent a rule at evaluation time. No instance is executed here; any future implementation/protocol must bind numerical conventions before values are used.

The hypothesis is a finite-sample design correction: in a restricted misspecified response model, adaptive expansion of low-query-relevance schedules can move the fitted projection away from the future prediction target even if biology and assay law are constant. Matching known query design might mitigate this without needing time windows or observed query losses. It cannot repair arbitrary conditional P(y|x) shifts, absent overlap or action features that omit relevant interactions.

## Exact closest standard procedure and irreducible gap

The first stage is ordinary regularized nonnegative empirical moment/kernel-mean matching. The second is ordinary importance-weighted/refitted regression on those same weights. A conventional implementation receiving identical phi,H,Q,penalty and fitting budget performs **every step of this whole U**, not merely an approximation based on broad expressibility. That exact comparator must be included; no improvement over itself or new U invention can be claimed. The2025primary's weighted spectral/refit operator is a direct standard counterpart once weights are supplied, while ordinary estimated-weight approaches can match the weight stage too.

This does not prohibit a real scientific contribution based on an independently validated biological/design restriction or an efficient distinctive estimator. It identifies the current missing contribution: no measured source-independent feature/balance restriction, ratio-estimation advantage or usable independent task has yet been supplied. Replacing phi with a learned cell embedding would introduce a hypothesis, not remove the exact weighted-refit counterpart; direct models must receive the identical embedding.

## Two small analytic falsifiers, not experiments

**More feedback can hurt with no response shift.** Actions x=+1,-1 have stable noiseless response y=x, and a misspecified intercept-only predictor. Old history contains one of each, so prediction0 has squared error1 on a known all-+1query design. Add eight newly acquired-1observations: the ordinary unweighted fitted mean becomes-4/5 and query squared error81/25. Biology and P(y|x) never changed. An ordinary query-aware importance-weighted refit supported on the acquired+1action predicts1, error0. This example demonstrates a plausible class of explanation and the power of its exact ordinary control; it neither identifies the real OLA cause nor establishes that the proposed regularized approximate balance weights attain the oracle weights.

**Covariates cannot identify arbitrary conditional response shift.** Two future domains can have identical permitted H,Q and all controls yet opposite future response at an unmeasured query schedule. Any weights computed only from H's covariates/Q are identical; they cannot be right in both domains. Distinguishing input-distribution drift from changed response/measurement needs additional lawful same-condition feedback or justified invariance, not merely an action-distance score. Even matched repeated schedules alone confound biology with assay change unless appropriate measurement controls/replicates are present.

Matching a finite set of moments does not establish full support or exact density ratios. In a small discrete schedule space, unseen query regimes may lie outside history support; a feasible approximate-balancing optimizer is not an overlap certificate. Known query IDs and empirical frequencies do not reveal the original adaptive acquisition probabilities. Large or concentrated weights increase variance and effective sample-size loss; regularization may preserve bias. No general safe-update guarantee follows.

## Inputs, world and agent roles

Released schedule encodings, lawful past means and intended query inputs can support a component-level design diagnostic. Current data lack authenticated independent replicate/batch measurement controls sufficient to identify biological versus measurement shift. No RNA, intracellular state, cell trajectory or precise assay reliability is supplied by the new weighting procedure.

The current operation has **no demonstrated world-model role**: it is a direct functional predictor update. A later world could provide independently validated state/response features, but would need matched direct-feature controls and measured added value. The agent's actual available role would be planning a future query/acquisition distribution and logging its propensities before outcomes. This retrospective dataset supplies historical adaptive generations, not a new agent policy or counterfactual acquisition oracle. Active bridge/overlap measurement is a future experiment requiring a real permitted action pool and cost, not an extra free input. No such experiment is launched.

## Fair falsifiable study and stop

A new task must be independently justified and prospective relative to outcomes, with known query design, lawful history/grouping and a separately frozen biological/decision margin. FAC/OLA are hypothesis-development evidence only, not fresh tests or a source for campaign-specific weight rules. Compare identical-input weighted and unweighted direct models, ordinary estimated-density-ratio/KMM refit, fixed source model, ordinary shrinkage/recency/replay/CL, ordinary validation model selection, simple mixtures, shared-pool AL when real acquisition exists, and equal-total-cost program/hyperparameter search. All weight-estimation/tuning cost counts; do not give only the candidate query inputs or a cell embedding.

The finite scientific claim would be useful forecast/decision improvement under a predeclared action-design change, while retaining conditional-response stability checks. A win against unweighted cumulative ridge alone would establish ordinary weighting utility; matching the exact weighted opponent cannot establish a new mechanism. Stop if overlap is absent, conditional shift dominates, gains disappear against competent same-information weighting/direct/refit, practical margins fail, or the only positive comes from an exposed campaign selector. No new gamma/window/embedding/condition gate to rescue it.

Retaining a balanced predictor is predictor inheritance. Retaining a genuinely source-learned balance/update strategy would require common theta,H,Q and ordinary controls inheriting the same learned representation; no such strategy is learned here. Improved-improver requires G1/G0 later descendants from the same U/history with equal search cost, not inferred from any weighted loss reduction.

## Independent decision

**NONE qualified as a new core candidate.** The one simple attempted updater is executable and its finite-sample premise is falsifiable, but the whole method is standard query-aware weighting/refitting and the latest data do not distinguish the causal explanation or supply independent validation tasks. The smallest useful missing evidence is a lawful later functional task with genuine action-design variation and overlap/measurement context sufficient to separate coverage from conditional shift, plus a substantive restriction or efficiency gain beyond its exact ordinary counterpart. No posthoc selector or numerical experiment on FAC/OLA is proposed.
