# Independent native improver position

2026-10-22. Requested selection: gpt-6.1-sol / high, as advertised by the parent task; this is not backend attestation. Native reasoning, zero DeepSeek calls. No current peer proposal or conclusion has been read. Inputs are bound in INDEPENDENT_SEAL.json. The parent supplied one direct evaluation clarification before this position: learned parameters of a proposal/search/update policy may instantiate operational Level3 if they improve finding later improvements from the same fresh start at equal total cost; code self-editing is unnecessary. Ordinary metaoptimization can instantiate this capability without being a novel algorithm. I adopt that clarification, rather than conflating parameterization with capability level.

## One explicit candidate, not a claimed invention

Scientific bottleneck: feedback about a drug can update a virtual-cell model in several directions. An early molecular response may mark target engagement, adaptive resistance, injury, or selective survival. The largest reduction of expression error need not improve a later treatment decision. A useful update rule should learn which observed discrepancies to act on, from independently measured downstream utility, rather than equating expression fidelity with drug-discovery value.

Represent the common-start world by theta. After legally acquiring support observations D, compute M assay-stratified gradients g_m = gradient_theta L_m(theta; D). A stratum is fixed by authenticated measurement type or time, not by response-derived outcome labels. An improver with inherited coefficients beta proposes one world update:

    G = [g_1, ..., g_M]
    theta_plus(beta) = theta - eta G beta

Its externally validated utility is R(theta_plus), evaluated on disjoint drugs/biological groups after the support observations and update proposal are fixed. On source episodes, update the *improver*, not the deployed world:

    beta_next = beta + rho gradient_beta R(theta - eta G beta)
              = beta - rho eta G^T gradient_theta R(theta_plus)

When the drug utility is nonsmooth or the world has no valid differentiation path to it, use the same paired external-validation difference estimator for every metaoptimizer. This costs its actual two validations; it is not free differentiable access to unobserved assay outcomes. All coefficients, step sizes and outer selection opportunities count against search budget. Do not introduce new observations by differentiating through a world model.

The inheritable object is beta and a versioned, fixed gradient-combination rule. It changes the procedure for producing the next model improvement. Evidence for Level3 would require old-beta versus new-beta finding better updates on independent later tasks from identical theta, support data, feedback and costs. Transferring theta alone is Level1; transferring a selected update/program alone is at most Level2. No such biological result is present here. This formulation therefore does not claim RSI merely because coefficients change.

## Native assessment and faithful conventional control

The closest conventional control is a bilevel learned optimizer with update direction -eta G beta and the identical outer utility, differentiation/finite-difference oracle, initialization, coefficient constraint (if any), steps and data. It implements the candidate exactly, including the beta update. This is an operation-level identity, not an objection that an arbitrarily expressive universal learner could eventually emulate it. Any numerical advantage over this control indicates a budget, information, implementation or random-stream mismatch. It cannot support novelty in this explicit rule.

A contextual bandit over a frozen finite beta menu is a second relevant control when derivative-free evaluation is required. It need not equal the differentiable learner at finite budget, and equivalence is not asserted. A full joint refit on the same observed assays, calibrated multivariate regression, ordinary continual learning, fixed gradient mixtures, AL/KG with matching paid assay bundles, and equal-budget program search remain substantive distinct comparators. Their inferiority cannot be inferred from the exact learned-optimizer identity. In particular, a new-beta versus old-beta gain could be real operational improved-improver evidence while still having no novel algorithmic contribution.

Decision: **DEFER RSI as an innovation core; STOP this exact gradient-recombination rule as a new MAESTRO mechanism.** A bounded symbolic/synthetic check can establish its computation, its conditional finite-budget effect and the identical conventional control. It cannot repair the novelty problem, qualify a corpus, or establish drug-discovery benefit. No new assay fit or value decode is justified to rescue it.

## Finite theoretical falsifiers

For a locally quadratic external loss F(theta)=||theta-target||^2/2, minimizing F(theta-eta G beta) is ordinary least squares in beta. An ordinary meta-gradient update is exactly beta_next = beta + rho eta G^T(theta-eta G beta-target). This identity is finite-dimensional and testable without expressivity assumptions.

If all g_m are collinear, G beta is one scalar times a common direction. In that restricted case the candidate adds no direction beyond ordinary scalar step-size tuning; compare a learned step size. Noncollinearity is necessary for this candidate's directional benefit, not sufficient for biological utility. A two-gradient example can beat a fixed mixture in one paid update yet tie the conventional meta-gradient implementation identically. This is a useful falsifier of novelty-by-gain, not a theorem against finite-budget learned improvers generally.

Further finite failure criteria for any future distinct operation are: same-start later utility no better than fixed/ordinary metaoptimizer after charging source training; benefit disappears when coefficients are permuted or the world is replaced by a strong direct model; apparent improvement comes solely from another outer validation query; no calibrated relationship between the update's molecular loss and useful intervention ranking. Do not add unrelated failures to define an impossible universal standard.

## Biological measurement and actual corpus boundary

A credible transfer needs pre-intervention state and support response, independently measured later functional utility, and authenticated drug/dose/time/lineage or donor/run joins. Molecular strata should distinguish measurement types whose discordance is scientifically interpretable. A causal dynamical interpretation additionally needs longitudinal state/function linkage; separate endpoint populations do not automatically supply it. Meta-training requires multiple independently grouped source episodes and later episodes untouched by rule development, with entire patient/run groups held out. Fixed public replay can test conditional prediction and decisions if scoped honestly; it is not a new performed experiment.

None of the inspected current corpora is newly qualified for this rule. The exact MSE nomination policy failed its opportunity gate, so this proposal does not retune its thresholds or access its development/later outcomes. CiPA sites support statistical grouped prediction, without authenticated well/donor trajectories; sites8/9 stay protected. TG later14 and AZ413 remain unopened, and their failed specific configurations are not restarted. Existing successful software loops and small descriptive mixtures do not establish this new world/update/improver effect. An asset search is not authorized by a novelty failure alone; a different operation needs its own falsifiable bottleneck first.

## Primary 2025–2026 transfer and its limits

Two primary arXiv full-HTML sources were retrieved afresh, with status200, exact URLs/titles/body hashes and complete bodies retained in PRIMARY_SOURCE_RECEIPTS.json. Publication/version identity also appears in the paper bodies: Self-Adapting Language Models (SEAL),2506.10943v2,18Sep2025; Lightweight and Versatile Learned Optimization by Recombination of Gradient History,2610.09604v1,07Oct2026. This authenticates source identity/contents at the retrieved version, not author performance or peer-reviewed status.

SEAL Figure1 and Methods3 describe an outer RL loop that evaluates generated self-edits by downstream performance and improves the edit-generation policy. The structural transfer is external post-update value as the training signal for the update proposer. Biological redesign is necessary because an unmeasured functional drug outcome is not an automatically available text answer, independent biological tasks are scarce, and intervention decisions have paid feedback/censoring. No exact assay-gradient method is attributed to SEAL.

The2026gradient-history paper Sections2.1–2.5 proposes learned scalar coefficients combining stored gradient directions, trained on trajectories. The structural transfer is a restricted directional basis, reducing the metaoptimizer's output dimension. Replacing temporal gradient slots by assay/time losses changes the data axes and interpretation; it does not by itself create a new learning operation. Its baseline paragraph uses default Adam/SGD hyperparameters; a faithful MAESTRO evaluation would additionally tune ordinary controls at matched cost. Neither paper demonstrates biological efficacy, this candidate's superiority, nor an irreducible virtual-cell/agent contribution. No exhaustive novelty search is claimed.

## Bounded next action and cost

Implement only the two-gradient counterexample, the exact conventional reduction and the collinear degeneration, recording all generated numbers as synthetic. This checks the claimed finite operation without decoding any biological data. The current position is sealed before any peer read. Root may subsequently request opposing discussion; preserve initial content unchanged. Costs so far: two successful primary-paper HTTP GETs, one retained local import failure, zero biological scalar accesses, zero predictive/biological fits, zero LLM API calls and no protected-reserve access.
