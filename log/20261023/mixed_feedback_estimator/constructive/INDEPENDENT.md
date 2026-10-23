# Independent constructive estimator review

2026-10-23. Read the complete goal, update_law_search/DECISION.md and the exact feedback-transport, matched-guide and reliability decisions. No peer reports read. No protected, development or pair-RNA values opened. A synthetic witness ran once. This is an independently specified candidate and algebraic limitation, not a novelty clearance or biological experiment.

## One concrete candidate: anchored coordinatewise mixed-curvature correction

Application is genetic-combination target discovery, not measured drug efficacy. Use the unchanged named target expression coordinates, single effects x_a, x_b, and an already fitted state predictor m0_ab. The proposed restriction is

    q_ab = x_a elementwise-multiply x_b;
    m_theta(ab) = m0_ab + diag(theta) q_ab.

The same theta is shared across pairs and, only if separately validated, later contexts. Each named coordinate's mixed correction depends on the product of its two single responses. This is a strong diagonal mixed-Volterra restriction, not generic low rank, a target-specific lookup table or an arbitrary latent factorization. Its principal likely failure is cross-gene curvature: gene k's combination response can depend on other coordinates. It preserves the existing singles by applying the correction only to mixed-support interventions; no single-response evidence identifies theta.

Freeze a source-only fitted quadratic functional readout

    h(z) = intercept + w^T z + eta ||z||^2.

This restricted h is deliberately minimal and likely too rigid. Its source-only fitting contract needs explicit source single-function values and regularization; all direct comparators receive them. It cannot be fitted to held-out function labels. No successful h fit exists yet. eta=0 degenerates to a fixed-head linear regression.

For legal purchased pair-RNA set R and functional-feedback set F, estimate theta by the exact objective

    L(theta) = sum_R ||m_theta(i)-r_i||^2 / sigma_R^2
             + sum_F [h(m_theta(i))-y_i]^2 / sigma_F^2
             + lambda ||theta-theta_old||^2,
    subject to ||diag(theta) q_i|| <= radius for all source design rows i.

All scales, radius and lambda must be frozen or source-inner selected using a matched menu; no subjective biological force signs are imposed. The RNA sum is ordinary multi-output observation fitting; exact functional term is generally quartic in theta. Solve with a fixed, recorded projected nonlinear least-squares schedule from theta_old, compare best achieved objectives from a matched bounded multistart menu, and retain actual convergence diagnostics. Do not claim global optimum. An alternative convex local fit linearizes h, but has the exact scalar reduction below. No IFT or Sherman–Morrison is necessary.

## Strongest algebraic reduction and why varying gradients is insufficient

Let delta_theta be a local update, g_i=gradient h(m_old_i). Then

    delta_y_i = (q_i elementwise-multiply g_i)^T delta_theta.

For a dense tensor B and mixed features phi_i the same calculation gives scalar design phi_i tensor-product g_i on vec(B), with Frobenius-penalty kernel

    K_ij = (phi_i^T phi_j) (g_i^T g_j).

This holds even if every g_i differs. Thus changing gradients can increase identifiability relative to a constant gradient, but cannot by itself establish a nontrivial learning rule, world-model necessity or an advantage over same-information direct inference. Pair-RNA supplies additional constraints; granting it to only the state model would be unfair. Any direct predictor can fit this exact objective with the same state auxiliary targets and diagonal restriction. Calling the latter 'direct' versus 'world model' does not create a causal contribution difference.

The exact nonlinear h avoids the *linear* scalar-kernel equality because it adds eta ||diag(theta)q_i||^2 and updates the gradient with theta. However it is still ordinary nonlinear parameter regression. The simplest direct comparator can evaluate precisely h(m_theta), use the same initialization and run the same solver. No mathematical distinction remains against that comparator; possible gains would concern an empirically useful restriction, not an exclusive ability of a named architecture.

## Executed witness and its scope

research/mixed_feedback_estimator_20261023/constructive/witness.py ran under maestro Python. WITNESS.json records a two-dimensional local design [[3,8],[8,3]] recovering theta=[.2,-.3]. A separate same-q example has rank 1 under fixed gradient and rank 2 under changing gradients. Direct scalar least squares matches the supposed state update to 1.11e-16. This verifies local identifiability and the direct reduction; it is not biological support, an empirical gain or an independence theorem. No new biological values were read, no model was trained, no API invoked.

## Finite-budget experiment that could falsify usefulness, if independently promoted

Before reading pair RNA, freeze source-only pair membership and two held-out blocks: a state-prediction block and a disjoint functional-ranking block. Purchase state only on declared R; functional outcomes from legal source feedback F; direct controls receive the complete same normalized state payload, all prior state fitting, and all relevant acquisition costs. Pair RNA derived from an already fully processed source still has its complete conditioning/data cost; it is not automatically a sparse assay oracle. Do not use protected outcomes.

Primary functional gate: at a fixed total cost and matched selection menu, at least 5% relative source-OOF MSE reduction versus the strongest direct/union comparator, with positive paired reduction in at least 4/5 prespecified folds; ranking improvement must independently exceed the frozen top-budget hit-rate margin. The hit definition/margin must be set from a scientific endpoint contract before new values. These source folds are exploratory capability evidence, not independent tasks or significance. State gate: improve held-out mixed-state error, and reject the proposed diagonal restriction if it loses against equally regularized standard full bilinear/ridge residual prediction. Neither gate alone qualifies the full goal.

Necessary controls: additive state plus same h; function-only direct scalar kernel with q tensor g; direct nonlinear composition with the exact same objective; ordinary all-feedback union refit of the same theta; parameter-matched direct pair prediction; standard continual replay; random and ordinary variance-based active selection; fixed state+policy mixture; identical-cost program/hyperparameter search. The exact same-objective direct control may tie bitwise: in that event architecture naming has no contribution and no WM superiority should be claimed. The restriction may still be useful as a baseline but not a new agent core.

No procedure improvement or improved-improver mechanism is supplied by this estimator. Frozen choice of radius/lambda is hyperparameter selection; inherited theta is model-state inheritance. RSI requires independent subsequent tasks and common-start old/new improvement strategies. Adding agents to choose these values does not establish RSI.

## Independent decision

**NO_NOVEL_CORE_GO; optional conventional constrained-baseline hypothesis only.** The explicit estimator meets the mixed-support identifiability requirement, avoids the fixed-head linearity only when its exact nonlinear readout is used, and has a biologically anchored falsifiable restriction. It does not yet supply an independent new estimation mechanism, and the same-objective direct/union controls can reproduce it. Its diagonal restriction is a conventional quadratic-system identification assumption. No exhaustive prior-art claim is made. Do not buy pair RNA merely to test this architecture name. A stronger candidate needs a specific new constraint or solver/decision mechanism whose advantage remains against the same-objective control, or an independently supported scientific shared-law contribution beyond the conventional diagonal restriction.

Unresolved: whether normalized single-response products predict mixed state at all; whether h generalizes from singles to mixed states; whether the published processing supports a lawful state budget; and whether any shared correction recurs across genuine tasks. These require data/experiments, but none is evidence that the present formula is already novel. Historical STOPs remain unchanged; this review does not prove that all shared curvature estimators or state models are impossible.
