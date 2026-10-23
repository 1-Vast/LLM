# Independent response-law revision critic

Verdict: NONE_NEW_CORE / ONE_NEW_PRIMARY_GATE_LIMIT. Independent report before current-phase peer reports. One new2025primary provides an actual transferable common/individual mechanism algorithm; one2026learned-optimizer primary was accidentally re-retrieved but is explicitly old project evidence, not a new discovery. No biological values read or fitted, no author code run, no previous mathematical example repeated, and no numerical toy executed in this phase.

## Historical scope

Read complete log/20261022/update_rule_renewal/DECISION.md and intervention_program_renewal/DECISION.md, then the historical feedback_law_discovery/critic report to verify the duplicated optimizer reference. Preserve literal fixed-constraint/projected-ridge, ESG calibration/cancellation, routed-gradient, certificate-pruning, low-rank probe and exposed functional-panel stops.

Especially preserve the old teacher dispute: rewriting the same local target as a synthetic gradient does NOT prove the full external-query-trained teacher already exists. Prior static synthetic-gradient meta-training differs from query-only outer supervision unless an actual source establishes equality. A newly specified finite-cost update structure could be valuable even if a direct model can represent its eventual predictions. No generic “all adaptation is refitting” argument is used below.

## New original: CICME

Yu, Pychynski and Huber, *Causal Mechanism Estimation in Multi-Sensor Systems Across Multiple Domains*, arXiv2507.17792v4, manuscript20August2025, https://arxiv.org/html/2507.17792v4. Original HTML SHA2560db438d7e62fbd5234f7f0e92bcada5e848b4b170c04781e7021b59cdce87d52, receipt and text projection retained. No matching title/ID was found in the bounded prior local Markdown/JSON query, apart from this new receipt; no exhaustive novelty clearance claimed.

Actually read FCM/additive-noise assumptions, SectionIII Algorithms1–4, HSIC equation8, penalty equations9–10, linear-Gaussian simulated scenario setup, metrics and stated power/optimization limitations. Author numerical performance was read but not independently replicated. This is multi-domain causal discovery/estimation, not a measured drug or later-task updater inheritance result.

Concrete algorithm:

1. Pool observed domain datasets and fit NOTEARS-MLP (or another continuous causal discovery model) on observed variables X.
2. For each fitted node function f_j, test dependence of pooled residual R_j=X_j−f_j(X) on the domain index D with HSIC, using a gamma approximation for its null statistic. Mark nodes stable when p>alpha.
3. Refit individual domains, either copying and freezing all parameters of stable node MLPs (CICME-f), or adding an MSE penalty tying their inferred incoming adjacency weights to the pooled weights (CICME-l).

This is a precise mask-construction/transfer operation rather than merely saying “causal modules.” The two variants are genuinely different: fixing function parameters is stronger than penalizing input-weight norms, and a graph-support/adjacency penalty need not preserve a full response function. The algorithm uses observed multivariate domain data with sufficient variation and additive independent errors; causal identifiability additionally depends on the declared functional/noise class. The showcased experiments are simulated linear Gaussian with equal error variances except stated scenarios, not empirical validation under arbitrary latent confounding or changing measurement channels.

The implementation pools the outcome-bearing domains before detecting stable nodes. It therefore is not automatically a source-only mask transferred to an unseen domain. A held-domain functional benchmark must charge all target support labels needed to test stability and estimate changed mechanisms; future query outcomes cannot enter mask selection. A newly encountered domain can invalidate a source-stable mechanism. That is an empirical transfer question, not solved by finding common functions among already observed domains.

## Precise population-level limitation of the stability gate

Let D be equally likely +1 or−1, independent of X~Normal(0,1), and let epsilon~Normal(0,1) be independent. In domain d,

    Y=d*X+epsilon.

These are two ordinary linear additive-noise mechanisms with the same parent X, identical input support and equal root/noise variance. Their conditional response laws differ: E[Y|X=x,D=d]=d*x. Under squared-error pooled fitting, the population conditional mean ignoring D is f_pool(x)=0, since the domain signs balance. The pooled residual is R=Y. Yet

    Law(R|D=+1)=Law(R|D=−1)=Normal(0,2),

so R is independent of D and the population HSIC is zero. This is not low power, an unseen input-support trick or a small-sample alpha error. Marginal residual-domain independence fails to distinguish opposite conditional response laws. A population independence test will find precisely the advertised null even though the response mechanism changed.

This targets the inference “p>alpha implies domain-invariant response mechanism.” With CICME-f's copied pooled function, the frozen conditional mean stays0 rather than the domain mean d*x; true conditional-mean squared error is E[X²]=1 instead of0. With noisy endpoint scoring, the corresponding expected errors are2 versus irreducible1. These are analytic Gaussian expectations, not executed simulations or a paper reproduction. No statement is made that every NOTEARS initialization/regularization discovers this ideal f exactly or that CICME-l must incur the same error. Indeed norm-based adjacency penalties can allow different signs/functions, and finite penalties can permit correction.

The pooled heterogeneous law is not one additive-noise mechanism with independent pooled noise; this is exactly the hazard when using the pooled fit as a stability detector. The counterexample does not refute a correctly stated single-domain identifiability theorem or the paper's reported finite scenarios. It isolates a missing sufficient condition for interpreting marginal residual stability as invariant mechanisms, even with infinite observations. A graph being unchanged is also not the same as its conditional response law being unchanged.

A lawful distinguishing statistic exists with the same observed X,Y,D: E[XY|D=d]=d. Conditional invariance testing or a direct domain-interaction predictor can detect the difference. They require no extra biological modality. Replacing HSIC(R,D) by a justified conditional test would be a conventional potential repair requiring its own finite-sample/split assumptions; this review does not nominate it as a new method or run it on old panels.

## Strong fair direct comparisons

If adopting a common/individual response-law idea for drug effects, direct arms must receive the exact same observed states, interventions, domain labels, support outcomes, fitted feature map and acquisition budget. Necessary comparators include domain-conditioned response regression with interactions/varying coefficients; shared-plus-context residual/multitask models; pooled and per-domain refit; source initialization and masked/block finetuning; the actual CICME freeze and adjacency-penalty variants; ordinary continual/replay adaptation; and the prior learned-optimizer/teacher alternatives with matched search cost. For planning claims add the same legal AL/mixture/equal-budget search.

A baseline denied node observations or true domain support while the causal model receives them is not fair. Conversely granting a baseline an exact global optimizer for free would erase a real finite-update contribution artificially. Count pooled discovery, HSIC calculations, refits and hyperparameter selection, and compare actual held-domain functional predictions/decisions, not only graph SHD. Graph discovery improvement can be scientifically useful, but it does not establish a drug decision or world-model benefit by itself.

The algorithm's explicit stable-mask construction is known prior work. Copying its selection and freezing into a virtual-cell agent cannot be our novel operator. A separate empirically validated biological restriction or cheaper reliable adaptation could still be a contribution; none is authenticated in this report. Pairwise direction tests or causal-module labels cannot substitute for that evidence.

## Revisited2026optimizer: duplicate evidence, real finite-cost idea

*Lightweight and Versatile Learned Optimization by Recombination of Gradient History*, arXiv2610.09604v1,7October2026, https://arxiv.org/html/2610.09604v1. Re-downloaded original SHA256e94b0974bf43c44a99f4d83e85c1638a1d0eb43326b2be6c0b69dcc4b91f020c. A combined local search returned many prior hits, but I fetched before individually resolving them. The focused follow-up confirms repeated old reading in feedback_law_discovery and other historical phases; retain this as avoidable duplicate retrieval, not one of two new primaries.

Re-read the actual per-group update delta_theta=−sum_h alpha_h*S_h with disjoint multiresolution gradient-history averages and learned group-shared coefficients. It has an actual bounded-history/computation design, rather than arbitrary local-target notation. It trains a compact optimizer across trajectories and reports zero-shot target-model performance, but that is source-trained optimizer transfer, not evidence that the improvement strategy recursively improves itself or localizes biological mechanism changes. Generalizing to cell support/query tasks requires legal task gradients, independent task splits and comparison with the same-history learned optimizer; scalar functional residual conditioning is not itself a new contribution. No new historical optimizer toy, author benchmark, GPU training or cost claim was reproduced.

## Falsifiable gap and disposition

A viable new response-law revision candidate must specify (a) an observed conditional failure recurring on genuinely later functional tasks, (b) exactly how legal feedback selects/changes a response law, (c) what restriction prevents confusing context/measurement or input redistribution with that change, and (d) a real statistical/computational advantage beyond the matched conditional/multitask/masked/learned-optimizer controls. Full causal identification is not needed for a useful forecast; unvalidated mechanistic names are also not enough.

Test a newly proposed stable-law certificate against the symmetric sign-reversal case before assigning biological meaning. Stop an invariance claim if its statistics cannot distinguish changed conditional laws on common input support. Stop new-operator promotion if it merely reproduces CICME masks/freezing or a known history optimizer without a new property. Do not infer global impossibility or demand a full RSI asset before any small conventional diagnostic. No current new candidate survives to justify a biological run in this phase.

World-model, agent, updater inheritance, joint and improved-improver contributions remain NOT_ESTABLISHED. The specific historical teacher novelty remains unresolved as previously recorded; this new source does not settle it. Full goal ACTIVE / NOT_ACHIEVED.

## Record

Four public GETs, all200: two noisy/refined official arXiv searches; one new CICME original; one duplicated optimizer original. Projection scripts use the standard library. Local duplicate-search output was broad but the title-specific follow-up resolved the distinction. No API, biological data download/read/fit, numerical experiment, author-code execution or new toy run. All records log/20261023/response_law_revision/critic/, all code research/response_law_revision_20261023/critic/. Native agent exact model/token/currency unavailable, not invented.
