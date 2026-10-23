# Decision utility of a learned model update: exact objective audit

2026-10-22. Read the full mandatory goal, functional_error_structure DECISION/CONTINUATION, revision_value_operation DECISION and my earlier independent record, and locally authenticated decision-focused-design primary passages and AssayLoop author-code excerpts. No current peer draft read, new network/data/model call, protected response access or computation on biological arrays. Full goal ACTIVE / NOT_ACHIEVED. All historical scoped STOPs remain. This is an independent objective/interface analysis, not an experiment or exhaustive literature clearance.

## Most concrete prior and exact scope

The already saved primary *Decision-Focused Sequential Experimental Design: A Directional Uncertainty-Guided Approach*, arXiv:2602.05340v1, defines in section 2 the finite decision oracle w*(chat)=argmin_{w in S} chat^T w with consistent tie breaking and the SPO loss

    L_SPO(chat,c) = c^T w*(chat) - c^T w*(c).

I read the local projection entries containing this definition and Algorithm 1's directional uncertainty, importance-weighted sequential sampling and model elimination/training. Receipt: update_value_qualification/skeptic/decision_focused_design.receipt.json, official HTML HTTP200, 837570 bytes, SHA256 16ca115a18df5f1515b3f39defeac0456b04313fe1e1f2924c8706db2fb8f945. The primary attributes SPO to Elmachtoub and Grigas (2022); their original paper was not separately opened here, so the authenticated 2026 primary is the direct local evidence for this definition and its use. The source genuinely optimizes downstream decision loss instead of MSE, not merely a family label.

For an exactly-K lowest-growth drug selection, let S={w in {0,1/K}^P:sum w=1}. The linear oracle is stable lowest-K selection of predicted pair-mean growth. A simplex S gives a single intervention. These are explicit finite feasible sets; no free global nonlinear solver is assumed.

Let a fixed legal source episode x consist of initial model M, observed support H and fixed candidate set. Let an update U_phi produce scores chat_phi(x) by a finite recurrence, followed by this selection oracle. With a common fixed pre-update score chat_0(x), the proposed revision loss is

    J_revision(phi;x,c) = c^T[w*(chat_phi(x))-w*(chat_0(x))]
                       = L_SPO(chat_phi(x),c)-L_SPO(chat_0(x),c).

The second term is independent of phi under the stated fixed starting point and history. Therefore minimizers, pairwise candidate ordering, and exact gradients wherever defined are unchanged by subtracting this baseline. Comparing updated versus old *true action utility*, under identical labels and episode weights, is exactly ordinary decision loss evaluated on the finite composed updater/predictor minus a constant. This is a precise objective reduction supported by an actual published loss, not a duplicated candidate code renamed ordinary.

Scope matters. The 2026 primary does not demonstrate this exact learned updater architecture, hidden-cell representation or improved-improver training. It supplies a real objective-level precedent; the composition above is my derivation. No whole-program finite-cost equivalence to its directional design algorithm is claimed. If M, H, the baseline policy or candidate set depends on phi, or objectives include other penalties/risk transforms, the constant-subtraction argument requires re-analysis. If each candidate is evaluated from a different state, the proposed comparison no longer isolates the updater.

## What the intervention framing adds and does not add

Holding M and H fixed while switching updater identifies an algorithmic component contrast on a complete historical response table. This is useful experimental design and differs from merely comparing unrelated final models. It does not create biological potential outcomes: cloned model state cannot clone a living culture. For sparse functional logs, legality still requires outcomes/support on actions where the resulting policies disagree, or explicit structural assumptions. The earlier revision_value_operation audit already proved the missing-support and adaptive-selection problems and paired-DR equality; no need to rerun those toys or claim a new estimator.

AssayLoop provides a second concrete, narrower precedent. Saved official rl.py excerpts specify finite GRPO acquisition rollouts with shared preobserved warm start, same-source true hit rewards, a frozen no-context reference and context_delta comparisons on the same remaining pool. The default telescope reward targets cumulative hit utility. Thus training a feedback-conditioned biological program for action outcomes rather than predictive MSE is already implemented. However it directly trains acquisition, not necessarily a separate learned update of a fixed predictor. I do not assert identical state/action semantics or revive the previously rejected claim that its already implemented telescope reward is a new repair.

## Finite computation and differentiation

For P candidates and fixed K, one evaluation costs the updater rollout plus score computation plus ordinary sort/selection (O(P log P) by the existing stable sort). Computing the before/after contrast adds a baseline selection/true-score sum; the baseline can be cached across updater candidates sharing the episode. Computing the oracle subtraction in SPO is likewise fixed across candidates and can be cached. Therefore paired evaluation itself does not establish an asymptotic advantage over the corresponding ordinary decision objective.

No exact differentiable optimizer is free. Hard argmin/topK is piecewise constant in scores: ordinary pathwise differentiation is zero almost everywhere and undefined at switching boundaries. A new training proposal must specify finite black-box search, a justified score-function estimator with randomized decisions, or a concrete differentiable surrogate and its cost/bias. A gradient through a soft decision surrogate is not the exact hard-decision revision gradient. Common-start or common-random-number evaluation may improve variance for some estimators, but that is not automatically guaranteed and is not novel merely by naming the model revision a causal intervention. Baseline subtraction can change approximate training trajectories if implemented with different variance reduction or selection noise; identical expected objectives alone do not prove identical finite algorithms.

## One minimal discriminator; no new candidate invented

NO_CANDIDATE at present. For any forthcoming single concrete updater, the shortest discriminator is to freeze its source episodes, initial states, finite update family, labels, tie rules, total rollout/search budget and random draws. Compare its exact revision objective to SPO evaluated on the same finite composed scores with the cached old-policy constant removed. Record whether candidate order and the chosen next update differ. If not, stop the claim that the baseline-relative objective is itself a new update mechanism; this is an algebraic unit check, not a biological experiment. If finite optimization differs, require the actual differing operation and measured cost/variance rather than treating the objective identity as whole-algorithm identity.

A genuinely useful learned updater could still beat ordinary MSE training on later tasks; that would establish a capability benefit, not originality of decision-focused supervision. Relevant fair controls then include an update with the same source-trained representation and decision loss, a direct history-conditioned action predictor, ordinary refits/ranking policies and equal-budget search over the same update family. All receive the same source outcome tables, support budget and initialization opportunities. Improved-improver evidence additionally requires changing the rule that generates/selects future updates and beating its earlier version at common fresh starts; source training U_phi alone does not establish that recursion.

No pilot is proposed from the broad objective difference alone. Await the parent's concrete candidate for cross-review. Do not reopen ALMANAC/decryptE/CDK stopped configurations or protected outcomes to manufacture a decision-loss win.

## Read failures and resources

One broad local search output was truncated; focused reads subsequently obtained the exact SPO definition and finite algorithm passages. One rg invocation using a literal PowerShell wildcard directory post_almanac* failed with invalid path syntax; replaced it with rg --files log/20261022 and a path filter. Neither failure supplied evidence or changed files. Zero new experiments, fits, API calls or downloads. No code added because this phase has only a written reduction and pending concrete implementation, not a second copy of old exact toys.
