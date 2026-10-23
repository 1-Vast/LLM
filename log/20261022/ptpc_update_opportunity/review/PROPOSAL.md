# One candidate: observed-state-anchored innovation repair

2026-10-22. Independent supporting-method role, frontier_distinct. **Proposal for bounded falsification, not an established novel core.** I read the PTPC source `generative_repair_renewal/source/archive_followup/RESULT.md`, CDK `DECISION.md`, relevant old Q/repair code and reports, and the original 2026 ProteinTalks publisher text/SI mechanism passages. No new PTPC Efficacy value, protein abundance, class count or performance table was read. No other role's new PTPC scientific draft was read. No fit, API call or new download was performed.

## 1. Concrete application and the one hypothesis

Application: offline prioritization of unqueried compounds by the author's **PTPC Efficacy annotation** in a new cell background, conditional on a declared cohort of measured 6 h proteomes and drug/context descriptors. A paid support acquisition may reveal that compound's 24 h proteome, Efficacy call, or both. New observations must change later predictions for other, still-unqueried compounds. This is a retrospective published-label task; the Efficacy horizon/cutoff and dose remain unqualified, so do not claim a calibrated fixed-dose viability benefit, prospective early clinical decision or dose causality.

Use HCT116 for development, A375 once for bounded selection, and keep NCI-H1975/NCI-H2170/Panc1005 unopened for a later frozen evaluation. Old 18 breast stocks/17 lineages may supply admitted source training, never a restored blind test. Keep all records of a background×compound, both times and all technical/biological repeats together. The 2,217 rows and repeated Sample_IDs are not independent acquisitions; retain the authenticated row/rep mapping rather than a many-to-many Sample_ID merge. All controls remain at their actual 6/24 h timestamps. Missing 0 h does not invalidate measured 6→24 prediction, but it prevents pretending that 6 h is an untreated baseline.

The candidate's **specific information hypothesis** is that a support Efficacy residual has two distinguishable parts: a response-state prediction error and an error in mapping actual response state to function. Ordinary label updating uses both together. If molecular repair already propagates the state error, propagating that whole label residual again can double-count it. A functional innovation anchored at the *observed* 24 h state could transfer the remaining error more safely to other compounds.

This is narrower than saying joint losses, state/head repair routing, repeated retraining or an archive is new. Only one new update operator is proposed below; there is no library of dozens of edits, no router fitted on five backgrounds, and no RSI generation at this stage.

## 2. Minimal executable operator

Let z6_d and z24_d be fixed source-normalized low-dimensional proteomic states with an explicit measurement mask. The encoder, whitening, protein vocabulary and transform are learned only on admitted source/development data. Fit a small differentiable transition F_theta(z6,d) predicting 24 h state and a calibrated head h_psi(z6,z24,d) in [0,1] predicting author Efficacy from an actual state. A direct residual-transition ridge is a necessary competitor; an ODE is not required by this proposal.

Give the world only a **two-dimensional shared transition correction** a. Before new-background support is opened, fix two source-derived parameter directions V=[v1,v2], for example the leading two directions of source held-background molecular gradient variation under a fixed source cross-fit. No target-label-selected directions or per-protein router are allowed. For compound d define

`J_d = derivative_a F_(theta + V a)(z6_d,d) at a=0`.

J_d is a state-by-two matrix. It says how the frozen transition's predicted state for that compound changes under the same two background-level model corrections. The candidate does not identify these directions as causal biochemical pathways. Source-derived low-rank structure is a standard regularizer, not itself a novelty claim.

For the accumulated paid molecular support M, form r_m,s=z24_s−F_theta(z6_s,s), with unobserved protein/state entries masked. Estimate one regularized correction by the small solve

`a_M = [Lambda + sum_s J_s' R_s^-1 J_s]^-1 sum_s J_s' R_s^-1 r_m,s`.

Here Lambda is a frozen positive ridge precision and R_s a source-fixed diagonal residual scale, not an invented measured assay-noise covariance. Then

`z24_t_repaired = F_theta(z6_t,t) + J_t a_M`

for every unqueried compound t. A molecular-only acquisition therefore changes both predicted state and the downstream Efficacy probability whenever the head is sensitive to that change.

For each paid functional support s in F, compute an anchor

`v_s = observed z24_s if s is also in M; otherwise z24_s_repaired`.

The **candidate operation** is the anchored innovation

`e_s = y_s − h_psi(z6_s, v_s, s)`.

Update unqueried function predictions by one ordinary regularized residual transfer using a fixed source-calibrated chemical/early-state kernel K_f:

`p_t_new = clip(h_psi(z6_t,z24_t_repaired,t) + k_f(t,F)[K_f(F,F)+lambda_f I]^-1 e_F, eps, 1−eps)`.

The head weights are frozen during this support update. The only state fit is the two-dimensional solve; the function transfer is a small support-kernel solve. Functional-only support reduces to an ordinary functional residual update. Paired molecular+functional support supplies the distinctive factual anchor. Recompute these equations from the entire accumulated paid support from a common initial model after each acquisition, so the implementation is not accidentally testing arbitrary query-order-dependent optimizer state.

Approximately fifteen lines of numerical operations suffice once source encoders/models are fixed. No LLM is needed to implement or select this operator. The target's own 24 h state/Efficacy may enter only after its paid acquisition; a whole proteomic assay is one acquisition, not one purchase per protein. All 6 h cohort assays must be charged or declared sunk common inputs equally for every method.

## 3. Why it could help, and the fastest algebraic counterexample

The frozen old repair backend adds 0.8 functional BCE and 0.2 molecular MSE, updating all model parameters after accumulated observations. Original Q separately changes head, trajectory or both on common supports. Neither implementation explicitly subtracts a label residual evaluated at the measured support state while independently transporting a state correction through a low-rank world sensitivity. The proposed innovation changes *which residual is transferred*, rather than relabeling the old update choices.

However, that distinction does not guarantee a new algorithm or a benefit. The strongest immediate counterexample is exact and should be checked before biological fitting. Suppose the head is affine h(z)=w'z+b and state correction transfers using the same scalar kernel weights A as functional correction. Then

`h(F_t + A(z24_M−F_M)) + A[y_M−h(z24_M)]`

`= h(F_t) + A[y_M−h(F_M)]`.

All molecular information cancels: the rule is exactly ordinary functional kernel updating. In this case even a beautiful state-repair plot establishes no incremental molecular capability. With J-derived matrix transport and a nonlinear head, cancellation need not hold, but it remains a measurable concern, not permission to assume nonlinearity is useful.

The **fastest empirical disproof** is correspondingly small: on development only, compare paired feedback to functional-only updating with the same support, and compare observed-state anchoring to the otherwise identical predicted-state anchoring. If unqueried predictions/rankings are equal within numerical precision, or the factual anchor does not improve held-compound calibration/selection over the ordinary update, stop this operator. Do not enlarge ranks, search protein subsets or edit the head repeatedly to force a distinction.

Another important failure mode: actual late state may be noisy or unrelated to the label's assay horizon. Then h(observed24) can be a worse anchor than h(predicted24), and this operator propagates nuisance measurement variation. Its low-rank J can also miss a drug-specific response shift, while a fixed chemical kernel can borrow the wrong functional error. These are direct falsifiable assumptions, not biological guarantees.

## 4. What is new versus which conventional explanation

The one proposed claim is **a useful structured bias in small-support repair**: separating observed-state-explained label error from the remaining functional innovation, while propagating molecular residuals through a shared transition sensitivity, can reduce negative transfer at matched information and resources. It is not a claim to invent innovations, residualization, multioutput conditioning, kernel regression, low-rank adapters or Bayesian updates.

| Conventional explanation | Required direct comparison / distinction |
| --- | --- |
| Ordinary same-data retraining | Same F/head, support masks, observations and validation budget; ordinary head-only, transition-only and joint refit, with source-tuned regularization. Our rule keeps source weights fixed and explicitly anchors the transferred label innovation at observed24. |
| Continual learning/replay | Conventional regularized/replay updates get the same source history and paid supports. The proposed shared-state correction does not itself constitute improved-improver RSI or a novel continual-learning principle. |
| Active learning | Fix the same support compounds first. Acquisition policy is not allowed to explain an update-rule advantage. A later policy comparison is separate. |
| Simple blend | Source-tuned convex combinations of drug/condition prior, direct early predictor and world score, including updating versions. The candidate changes scores through observed support residuals, but any claimed benefit must survive these inexpensive baselines. |
| Same-information direct predictor | A direct conditional kernel/ridge/logistic model receives the same z6, drug/context, measured support z24 and labels; include measured-state imputation plus ordinary residual updating and a small source-trained support-conditioned predictor. No withholding actual molecular information from this comparator. |
| Ordinary joint conditional/multioutput residual model | Include a source-calibrated joint state/function residual model or co-kriging/Schur-innovation update. If it implements the same conditioning effect or matches the operator, report an ordinary conditional-update explanation; do not claim a distinct core. |
| Existing optional gradient-conflict weighting | Not the candidate. The original 2026 SI already describes a gradient-cosine loss-weight option. Our operation changes the factual anchor and propagates residuals in output space, not just task weights. |
| Equal-budget small program search | Allow the same number of ordinary update candidates, calibration settings and source evaluations, including the predicted-anchor and observed-anchor operator if publicly specified. Charge candidate generation, failures, validation and later adaptation. No free legacy source search. |

The candidate may still turn out to be an ordinary structured conditional regression expressed in world-model coordinates. Algebraic equivalence to the general concept of regression is not a universal impossibility argument, but equivalence to a concrete equally informed, equally regularized conventional implementation would remove the distinctive-method explanation. The strongest defensible novelty currently is **unverified**. Its opportunity is a precise testable repair decomposition, not a proven first-of-its-kind algorithm. If the supporting role must nominate a ready publishable core now, the honest answer is that this candidate is not yet one.

## 5. 2026 first-party mechanism evidence actually read

Primary: Sun et al., *An operational perturbation proteomics-based virtual cell model*, Nature, published 9 September 2026, DOI [10.1038/s41586-026-11001-9](https://doi.org/10.1038/s41586-026-11001-9). I read the retained publisher abstract and the actual supplementary-text passages in `tmp/ptv1_src/si.txt`, under **“Rationale for informativeness of four time points”** (approximately lines 289–370) and the multi-task loss passage (approximately lines 520–570).

The SI explicitly states a shared perturbation-conditioned flow, multi-time state constraints, and additional binary efficacy supervision on trajectories. It also acknowledges empirical identifiability depends on regularization and initial-state/perturbation coverage. This is a concrete recent first-party rationale for using a common transition sensitivity to connect molecular and functional feedback. It does **not** prove that sparse PTPC 6/24 observations identify a vector field, that the label has a particular timing, or that support-state anchoring improves updates.

Crucially, the SI says reported results used fixed lambda=0.8 and describes an optional gradient-cosine conflict-weighting strategy that was not used. Thus adaptive task-weighting or prioritizing functional loss is already an explicit operation in the primary and must not be advertised here as the new mechanism. The publisher text available locally is a subscription preview, not a read full main Methods. The SI is original primary supplementary material, not a secondary summary. Exact main-paper implementation details beyond the read supplement remain unknown. No newer primary or independent nearest-neighbor-method full text was fetched; novelty against co-kriging/innovation-based assimilation is not certified by this reading.

## 6. Bounded qualification, success and stopping

Before any new numerical experiment, the parent should freeze a development-only label/coverage gate: decode permitted HCT116 author-Efficacy encodings, missing tokens, repeat consistency and 6/24 compound joins; leave the other backgrounds' labels unopened. Preserve mismatched/missing groups without selecting convenient class prevalence. If the target is not a usable class label or paired coverage is insufficient, stop this task contract, not all possible PTPC science. Unknown dose/cutoff limits interpretation without prohibiting prediction of a released author label.

The first operator experiment should use fixed paired support sets and complete-compound-held-out targets in HCT116. Source transformations/models/parameter directions must exclude held-out target labels and, for a fair new-background adaptation test, exclude that target background from source model fitting except the explicitly allowed development fitting arrangement. All methods get the same raw allowed information and source partitions. Run the linear-cancellation synthetic test first, then a bounded true-versus-shuffled paired-state control with identical masks and labels. The molecular contribution requires actual paired state to help beyond functional-only and mismatched/shuffled state, not merely a change in model hash.

Report unqueried author-label Brier/calibration, fixed-k selection and actual query counts; choose the primary utility and justified practical decision threshold in a later concrete protocol rather than importing old Q/E margins across different pools. If evaluating confirmed discoveries within a total screening budget, charge molecular assays and the support functional assays and compare against direct functional confirmation. A post-support top-k prediction score is not automatically a five-unit discovery yield.

Only if HCT116 demonstrates a noncollapsed operator and an advantage beyond the strongest direct/joint-conditional/refit/blend controls should A375 be opened once for the prespecified finite choice. Failure there stops this operator; do not tune on the three retained backgrounds. Freeze all code, source costs and analysis before their single later evaluation. With only three retained line-level units, any reported transfer is a small exposed-public-data estimation result, not a broad independent confirmation or enough tasks for arbitrary recursive generations.

Do not run LLM program evolution merely because an executable operator exists. If the operator eventually survives, its small correction basis, residual definition and source-calibrated scales could form a reusable U; showing a better U is still distinct from showing an editor E becomes better at constructing later U. The original A/B/C/D common-start, copied-program, frozen-improver and total-cost controls would still be required for inheritance and genuine RSI. No such benefit is claimed here.

**Supporter recommendation:** permit independent skeptical review of this one operator and its exact cancellation/conventional-conditioning counterexamples, then at most a bounded development qualification if it survives. It is materially more specific than “repair the world model” and is not already tested by the old saved-menu oracle. It may nevertheless fail novelty or performance quickly. Keep that failure cheap and recorded; do not rescue it with a wider menu or an agent wrapper.
