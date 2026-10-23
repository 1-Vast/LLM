# Independent constructive review — shared intervention-operator repair

2026-10-23. Full objective ACTIVE / NOT_ACHIEVED. Independent review written before peer reports. Parent supplied only a TDAL primary-source lead, which was independently downloaded and examined. No protected labels, new biological values or model training used.

## One candidate, precisely specified

Application: prioritize combinations that produce a desired measured functional response while updating a prediction of intervention-induced cell state. Norman K562 CRISPRa is a target-interaction proxy, not a measured drug-treatment efficacy claim. Its 102-target chosen-guide panel is a qualified local functional asset; the completed matched-guide decision does not qualify later biological contexts.

Candidate: revise a **shared intervention-response operator** when measured functional counterexamples arrive. Let phi(a,b) be a fixed symmetric pair feature from legally observed single-perturbation RNA. A state model predicts z_hat=W phi; function is f_hat=beta^T z_hat plus the frozen main-effect baseline. On acquired functional residual r, use the minimum-Frobenius correction

    Delta W = eta * r * beta phi^T / (||beta||^2 ||phi||^2 + lambda).

The superficially attractive claim is that editing W rather than one output or one pair causes an interpretable response-program correction that propagates across unmeasured combinations. Store the operator plus an update gain/regularization rule, and later learn gain selection from earlier complete tasks. There is one state operator, one functional readout, one rank-one edit; no editor hierarchy or runtime LLM is needed.

**The candidate fails its first simplicity check as currently specified.** With w=W^T beta, the exact same predictions are produced by

    Delta w = eta * r * ||beta||^2 phi / (||beta||^2 ||phi||^2 + lambda).

This is ordinary normalized residual/online regression updating on the very same pair features. Also any v orthogonal to beta permits W -> W+v q^T with no change to functional predictions. Function-only feedback cannot identify those state corrections. This is a scoped algebraic statement about a linear state model and a fixed linear functional readout; it does not prove nonlinear worlds, multi-readout feedback or state measurements useless.

An actually executed seeded synthetic check matches five sequential operator/head updates to maximum absolute discrepancy 1.24e-14; a state perturbation with norm 53.50 changes functional predictions by only 1.07e-14. See OPERATOR_CHECK.json and research/function_update_renewal_20261023/constructive/operator_check.py. These are deterministic algebra checks, not biological evidence or five tasks.

## Strongest repair, and why it is not yet a promoted mechanism

Require **paired acquired state and function** at the intervention, so state discrepancy e_z can constrain operator components invisible to scalar function. A fixed correction Delta W=e_z phi^T/(||phi||^2+lambda) has real information absent from function-only updating. However its update is standard multivariate normalized regression; jointly learning W and beta is ordinary supervised multiview/multitask learning. Obtaining paired measurements can help without furnishing an algorithmic novelty. It also supplies extra information, which a same-information direct baseline must receive and whose acquisition cost must be charged.

Norman contains selected combination RNA, but this branch has not authenticated acquisition-bundle costs, source-only pair RNA endpoint joins, or a separate later biological task. The 132 selected combinations are not an independent campaign population, and cell/subsample/hash folds are not RSI tasks. Do not open their values merely to find a favorable gate. The immediate missing distinction is an identifiable, transportable restriction on W that gives useful prediction or decisions beyond direct multivariate regression under the **same paired observations**, not a larger updater search.

## Fresh 2025–2026 primary sources and implications

All exact bodies/URLs/statuses/byte hashes retained alongside this report. Search-engine/OpenAlex records are discovery metadata, not primary method evidence. Four original arXiv full HTML papers plus the independently acquired TDAL full HTML were examined; no claimed reproduction of their biological results.

1. **PatchWorld**, arXiv:2605.30880v1 (29 May 2026), https://arxiv.org/html/2605.30880v1. Abstract/Introduction and Methods explicitly induce executable belief-state programs from offline trajectories and accept counterexample-guided code repairs by replay score. It also reports reconstruction fidelity can improve while planning utility deteriorates. Transferable structure: failed predictions can supply executable counterexamples; needed adaptation: biological outputs are noisy nonreplayable populations, so literal exact-trace patch acceptance is invalid. Generic “functional counterexamples repair a world program” is already a close mechanism, not our novelty. The scalar-operator proposal is simpler but reducible, as shown above.

2. **SkillGrad**, arXiv:2605.27760v1 (26 May 2026), https://arxiv.org/html/2605.27760v1. Abstract/Introduction explicitly optimize structured skill artifacts from execution evidence, contrast failed and newly successful trajectories, accumulate diagnostic pattern memory, and apply layer-aware patches. The gradient analogy is expressly conceptual, not a numerical derivative. Replacing spreadsheet tasks with experiments, storing a research procedure and accumulating “momentum” would be a relabeling. Its task results are not evidence for measured cellular update transfer or improved-improver RSI here.

3. **AmbiModBench**, arXiv:2609.32527v1 (26 Sep 2026), https://arxiv.org/html/2609.32527v1. Abstract/Introduction/benchmark formulation separate training-mean background from target-specific prediction, test coordinate invariance, and distinguish representation coverage from sample count. This materially limits a state-world claim: raw RNA reconstruction correlation can remain strong with no target-specific functional usefulness. Its conditional ambiguity bounds require response-constraining assumptions; closeness alone does not identify a useful correction. It does not prove our functional residual is recoverable or a novelty theorem for a new updater.

4. **Reliable Algorithm Selection for Machine Learning-Guided Design**, arXiv:2503.20767v2 (2 Jul 2025), https://arxiv.org/html/2503.20767v2. Formalization/Methods choose design configurations via prediction-corrected held-out labels with multiplicity control; stated guarantees require known design/labeled density ratios and independent labeled data. Reusing a source corpus that influenced mechanism choice cannot be silently treated as its independent certification sample. A menu of updater programs with success-based acceptance is insufficient new contribution.

5. **Temporal Difference Active Learning (TDAL)**, arXiv:2610.22122v2 (lead supplied by parent; exact HTML acquired here), https://arxiv.org/html/2610.22122v2. Sections 3–4 explicitly learn acquisition online from feedback, use Hellinger change in hit probabilities to weight successor value, and create virtual leave-batch-out transitions by surrogate refits on already measured data. Its objective J_w is a feedback-discounted surrogate and equals undiscounted cumulative discoveries when w=1; larger prediction change is not automatically more true future utility. Nevertheless learned feedback-sensitive acquisition and synthetic transition reuse are direct precedents. Our candidate edits a state operator instead of learning q, but that implementation distinction is not substantive novelty while exactly reducible to ordinary scalar regression.

Two biorxiv API responses returned HTTP200 with only 79-byte error payloads rather than paper content. They do **not** authenticate PIE or the biological-response compound-representation paper. No claim from those full texts is made. One text-extraction attempt failed because bs4 is absent; retained WORK_AND_FAILURES.md documents this and the standard-library HTMLParser replacement.

## Smallest falsifiable continuation, if a nonreducible biological restriction is supplied

First qualify a measured intervention catalog with paired state/function and an actually distinct subsequent context or campaign. Freeze the intervention-state representation, functional target and paired-payload costs. Do not choose a new success margin from this proposal's nonexistent biological results. Prespecify a useful response/decision margin in the eventual task's units and verify dependence-aware precision permits detecting it.

At one common start, give identical paired feedback to: (i) no-update direct/state models, (ii) union-refit strong direct predictor with phi and measured state, (iii) multivariate online ridge plus scalar readout, (iv) continual update, (v) constrained operator repair, and (vi) a simple mixture of these. Charge initial state fitting, tuning and all unsuccessful edits. Freeze an ordinary hit-probability/uncertainty policy initially; only after an operator effect survives, compare active search, TDAL or faithful bounded approximation, and same-information direct policy using equal total computation, feedback and program-search opportunities. No repeated version of the stopped early-kernel mixture is authorized by this proposal.

Core falsifier: if direct multivariate regression or scalar equivalent reproduces the candidate's predictions/decisions at matched information/cost, stop the new-operator claim. If state prediction improves but chosen-intervention utility does not exceed the predeclared useful margin, stop the claimed WM decision contribution. If paired-state benefit vanishes when the direct model receives the same paid state, retain only an assay-information effect. If no independent later task exists, no inherited-update conclusion follows. Later inherited policy and old/new improver must be compared from a common later start; a stored operator alone is ordinary model inheritance, not RSI.

## Independent decision

**DO_NOT_FIT_CURRENT_LINEAR_OPERATOR / NO_NEW_CORE.** This is a precise candidate and an executed failure of its distinctness claim, not a discovered high-performance method. Retain the need for identifiable cross-readout corrections as a scientific constraint; do not represent that constraint, generic counterexample repair, TD learning, gain meta-learning or added paired assays as established algorithm novelty. No biological efficacy, world necessity, agent necessity, inheritance, joint effect or improved-improver result has been demonstrated. The complete project objective remains active.
