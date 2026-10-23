# Norman functional contract: independent update-rule assessment

Decision: **NO_CANDIDATE for a substantively distinct new update rule in this review.** One concrete ordinary capability question remains open; it is not rejected for using standard algorithms. No new mechanism is invented to fill the slot. No current peer draft was opened before sealing. Only local source text/code and historical reports were read; zero HTTP, response/expression values, numeric supplemental tables, model fits, or protected reserves. Author notebook source was inspected, not executed.

## Source operation already established

The local Norman 2019 primary text, `root_sources/primary_bioc.source.txt`, describes a growth-based CRISPRa interaction map in K562. It selected 112 genes with single-activation growth effects, then profiled selected pairs and all constituent singles by Perturb-seq. The full study is not an unselected genome-wide unbiased target population. Genetic activation is not gene inhibition or pharmacological treatment. These limitations still permit a useful conditional interaction-prioritization experiment.

The original Figure 6 already does **single-perturbation RNA side information + a limited subset of functional pair observations → remaining functional interactions**. It reports a modest relationship between transcription-profile similarity and GI-profile similarity, then explicitly constrains a matrix factorization so similar transcriptional effects encourage similar interaction profiles. This prior directly closes any claim that simply propagating sparse functional feedback through RNA geometry is a new mechanism.

The author `prediction.source.txt` makes the implementation concrete:

1. Restrict the target set using measured single-transcriptional effects (>10 DE genes under its stated test), excluding BAK1/BCL2L11. These original exclusions are source design, not new facts that we discovered.
2. Build `side = sqrtm(corr(raw_expr))` from single-perturbation expression after per-expression-feature min/max scaling.
3. Fit a quadratic expected double fitness from the two single fitnesses using observed doubles.
4. Subtract this expectation, use Maxide with the fixed side matrices to complete the residuals, and add the expected fitness back.
5. Derive predicted GI maps from the completed fitness map.

The code comments explicitly distinguish single fitness averaged across primary-map guides from the guide used for Perturb-seq. That intervention reconciliation must remain in any new contract. The notebook's zero-as-unobserved convention and use of entire source objects are implementation details to audit in a later faithful, isolated reproduction; they are not evidence here of a newly measured leak or a justification for arbitrary score comparisons.

`prediction_comparison.source.txt` additionally compares Maxide, scaled Maxide, KNN, SoftImpute, Bayesian PMF, GRALS/scaled GRALS and SVT. Hence a proposal cannot pretend that fixed RNA plus one weak mean predictor exhausts existing alternatives. The comparison notebook also resamples until every row has an observed entry for its scaling methods; any reproduced acquisition rule must account for that rather than silently granting extra coverage. I have not audited the imported Maxide implementation or proved its full objective equivalent to every proposed kernel estimator.

## History searched before proposing a rule

Used `rg` for Norman/Maxide, metric/geometry, residual-kernel and scoped STOP references, then focused reads of these decisions/source passages:

- `early_update_mechanism/DECISION.md`: positive-definite molecular-gradient transport and functional preconditioning had explicit ordinary bilevel implementations and conflict counterexamples. Swapping to unconstrained transport was ordinary multi-output regression. Do not relaunch these as “RNA reliability learning.”
- `update_rule_renewal/DECISION.md`: fixed nuisance constraints reduced to constrained ridge/Gauss–Newton; ESG edge-sign evidence had actual calibration/cancellation failures. Do not repair that sign gate or binomial counting on a new gene graph and call it a new rule. The local teacher's training-signal distinction was unresolved rather than globally disproved; it still lacks a distinct finite property.
- `strategy_rethink/RESULT_DECISION.md`: the conventional 12-program common-start opportunity screen actually ran and its learned proposal distribution lost to the fixed uniform comparator. Its specific exposed route arena/grammar stays stopped. Norman is a different asset, not permission to rerun or rename that grammar.
- `renewal_application/skeptic/CROSS.md` and `api_evidence_innovation/DECISION.md`: response geometry and functional residual propagation have already been proposed; an identical factorized model and training program must count as the same ordinary method. These records explicitly preserve ordinary empirical structure tests while rejecting invented operator novelty.
- `decision_update_mechanism/DECISION.md`: observed scalar feedback cannot certify a drug mechanism lesson, and a new purported support anchor must actually be observable under its paid contract.

An initial broad history search exceeded output limits; narrow follow-up reads above were used for the claims. No historical STOP is a blanket performance verdict on Norman. Conversely, merely switching the dataset does not restore novelty to a stopped literal operator.

## Why the tempting rule is ordinary, with a concrete reduction

Let x_i be paid single-gene RNA features, S the legally observed pair set, and r_S functional residuals after a common single-fitness baseline. A direct attempt is to learn which RNA directions or similarities deserve trust, then propagate the residuals with that geometry.

For a fixed symmetric pair feature map phi_ij and ridge parameter lambda, a kernel residual update has

    f_new(q) = f_base(q) + K(q,S) [K(S,S) + lambda I]^{-1} r_S.

This exactly equals ordinary ridge regression on phi for the same feature/kernel, residuals and penalty (the standard primal/dual identity). It is a specific equivalence, not an argument that all algorithms are equivalent. Replacing the fixed RNA kernel with K_W from a learned positive-semidefinite metric W, or tuning a convex mixture of RNA and identity/no-RNA kernels, is ordinary supervised metric/kernel learning. Learning W by post-update held-out functional loss is a bilevel/meta-learning objective; it does not by itself add a distinct rule. Learning graph edges from functional agreement instead gives supervised graph learning; actively choosing edges/pairs by uncertainty or expected error reduction is experimental design/active completion. Those are legitimate strong alternatives, not strawmen.

I have not performed a new exhaustive literature search on every such variant, nor established that the author's Maxide code already learns this W. The boundary is narrower: the source already establishes the fixed-side-information baseline, and the concrete adaptation operation available here can be explicitly implemented by standard metric/kernel learning. No new constraint, estimator, identifiable biological invariant, or finite-cost guarantee beyond that implementation has been supplied.

The scientific difficulty is also real. A residual on one observed interaction can reflect noisy fitness measurement, imperfect activation, an inappropriate single-fitness baseline, or true mismatch between transcriptional and functional similarity. Sparse residuals alone do not universally identify which explanation is correct. With unobserved pairs, multiple functions can agree on all paid outcomes and disagree on future pairs. Thus a promise to certify “this RNA edge is biologically unreliable” requires added assumptions or independent measurements; a prediction improvement would support useful calibration, not that causal interpretation. This is an identifiability caution, not a claim that supervised calibration cannot work statistically.

## Exactly one unresolved capability question, not a new-core candidate

**Does ordinary feedback calibration of the single-RNA geometry improve how a subsequent fixed amount of functional feedback changes unmeasured-pair predictions, beyond fixed RNA geometry and ordinary functional-only completion, on this prespecified target population?**

This is more specific than repeating Figure 6's RNA-versus-no-RNA comparison. It concerns whether an earlier functional support set can improve the geometry used to interpret a later support set. The original static-side prediction source inspected here does not answer that particular sequential contrast. Calling it unresolved does not claim no paper elsewhere has answered it.

If the parent chooses a capability-only test after data qualification, the minimum interpretable comparison uses the same initial predictor, earlier support, later support, hidden assessment pairs, expression inputs, fitting opportunities and total assay/compute accounting. Compare the fixed RNA kernel with a conventional calibrated kernel; include the same-information ordinary joint/refit model and functional-only completion so any gain cannot be credited merely to seeing more labels or refitting twice. A frozen-versus-updated geometry contrast can isolate in-episode construction adaptation, but the strongest ordinary adaptive competitor remains necessary. A fixed later support set is enough for this question; adding active acquisition or an LLM would introduce a second unqualified hypothesis.

Assessment pairs and target-gene grouping must be set before functional values influence tuning. Shared genes produce dependent edges; edge count is not independent task count, and random relabelings or repeated masks do not create new cell contexts. RNA assay costs apply to all profiles actually acquired, and absence of double RNA at deployment must be honored. One K562 interaction map can support a conditional prediction/update study; it does not alone establish across-context inheritance or improved next-generation improver efficiency.

The simplest falsification is failure of the calibrated geometry to improve the predeclared hidden prediction/decision endpoint over fixed geometry and the strongest ordinary same-information updater at the registered finite budget. Even a positive would initially be ordinary capability evidence. There is presently no outcome effect-size/noise/power contract in this role's permitted evidence, so I do not fabricate an assay count, threshold, or precision claim. No experiment is registered or run by this report.

## Final scope

NO_CANDIDATE applies to a substantively distinct new update mechanism from the inspected evidence. It does not close the one bounded ordinary capability question, the Norman asset, or empirical investigation of geometry reliability. Fig6/Maxide residual completion is existing work; ordinary metric learning and active completion cannot be renamed innovation. Mathematical identities above explain literal candidate collapse but do not prove equal finite behavior for every regularizer/optimizer. The actual unresolved issue is a conditional biological/statistical property of feedback transport, for which no new evidence or new algorithm is established here. Full WM/agent/inheritance/joint/improved-improver objective remains unachieved.
