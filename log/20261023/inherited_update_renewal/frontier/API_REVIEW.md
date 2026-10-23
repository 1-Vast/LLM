# Independent review of retained API proposal

2026-10-23. I read only `inherited_update_renewal/api/PROPOSAL.md` and `RECEIPT.json` for this review before any root falsifier or peer report. The receipt records one actual `deepseek-flash` response, 630 prompt / 10,000 completion tokens, `finish_reason=length`; the proposal is visibly truncated after its minimum counterexample. No missing continuation is inferred.

## Assessment

The proposed operation is a precise restricted update, not merely a renamed agent loop:

\[
s_t=\arg\min_{J_Cs=0}\sum_h\|g_h(X)-J_Xs\|^2+\epsilon\|s\|^2,
\qquad
\theta_t^{post}=\theta_t^0+\alpha_t s_t,
\]

where historical post-minus-pre functional changes are first fitted in a shared forward-coordinate basis, then restricted to directions invisible on current controls, and only one new-task amplitude is estimated from paid feedback. This differs materially from CLAW's unrestricted context→LoRA adapter generator: CLAW can generate arbitrary low-rank weight changes from transition context, whereas this proposal fixes a historical function-space direction and constrains current updates to a control-nullspace. It also differs from HarnessTTT and ExpEvolve, which learn a proposer/harness or program idea actions; neither specifies this intervention-anchored state update.

The proposal therefore deserves a **minimal falsification GO as a candidate**, while remaining **unpromoted as a core**. Its novelty is conditional on a real repeated structure: historical functional increments must align after forward-coordinate refitting, and current control measurements must remove nuisance directions while leaving a one-dimensional action-relevant residual. The claim is falsifiable and does not require dismissing it because its optimizer is least squares.

## Strong conventional competitors

The direct baselines must be stronger than a free minimum-norm fit. At identical paid controls, functional observations, and compute budget, fit:

1. an unconstrained direct residual model with the same historical features and ridge/empirical-Bayes shrinkage;
2. a constrained union refit that learns the same `J_C` nullspace but estimates its direction from current and historical observations jointly;
3. a rank-one/low-rank meta-update whose feature basis is selected by validation only on past tasks;
4. a fixed calibration/mixture and replay continual learner;
5. an equal-budget random/UCB direction search, with every queried direction evaluated on the same paid batch.

Otherwise the proposed direction gets a privileged prior and any gain cannot be attributed to the function-coordinate/nullspace mechanism. Hyperparameters, including epsilon and lambda_R, must be selected using leave-one-history-task-out only; current held-out functional labels cannot select X or a direction.

## Synthetic witness and its limitation

The supplied linear witness is arithmetically coherent: controls span the first four coordinates; the true direction is `e5+2e6`; a single feedback at `e5+e6` gives alpha=1 and predicts held-out `e6` exactly, while direct least squares predicts 1.5 versus truth 2. This demonstrates a possible finite-sample advantage of an informative inherited direction. It is not yet evidence of biological validity. A direct model with the same historical function-space features or a Bayesian structured prior could reproduce the advantage, so the witness only motivates, rather than proves, a real-data test.

## Required biological/data gate

The next experiment must use at least several genuinely distinct source tasks and an untouched later task/context with a lawful functional endpoint. A shared endpoint table may be scored offline for multiple clones after one measurement; its assay cost is paid once and each clone's fitting/evaluation cost is separately charged. If a proposed edit also changes acquisition, all methods need a common accessible response table or coupled randomization; a common feedback batch isolates updater effects only and cannot establish agent/acquisition benefits.

Predeclare success as improvement in held-out functional ranking utility (and report MSE/calibration) in a majority of held-out contexts, with no increase in total feedback or compute cost beyond the matched controls. Stop if the constrained direction loses to the same-nullspace union refit/direct residual model, if direction alignment collapses under leave-one-task-out, or if gains vanish under unit-preserving endpoint transformations and untrimmed measurements. A failure would reject this specific inherited direction, not all RSI.

## Decision

**CONDITIONAL GO TO MINIMAL FALSIFICATION; NO CORE PROMOTION.** The equation is sufficiently exact and potentially distinct to test, unlike the already stopped literal bounded API rule. It is not yet an RSI result: the inherited object is `s_t` (knowledge/capability), while Level 3 requires old versus updated proposer/improver checkpoints, common starting updater, equal history/budget, and improved future edit-discovery efficiency. CLAW, HarnessTTT and ExpEvolve provide direct controls and conceptual overlap that must be acknowledged in any claim.

All judgments are limited to the retained, truncated response. No generated code was executed and no biological outcome is claimed.
