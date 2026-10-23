# Independent mechanism search: directed local-circuit feedback transport

2026-10-23. Independent role; no other new agent report read. Read the full goal objective and the fixed quadratic-interface, matched-guide, early-kernel-updater, functional-dynamics and intervention-dynamics decisions. All historical STOPs remain unchanged. This report evaluates **one** candidate and does not claim a novel method, biological performance, world-model necessity or RSI.

## Candidate and the actual question

Application: use limited new genetic-combination feedback to improve prediction of other combination growth outcomes. Existing ordinary RNA-conditioned completion improves source OOF functional MSE by 14–16%; it has not established that a particular *directed circuit error* recurs, so that error is a hypothesis rather than a discovered failure mode. CRISPRa growth is a target-combination discovery proxy, not measured drug efficacy.

Candidate: update a small directed feedback circuit in a cellular state equation, then transport that repair through the inverse local response operator to unmeasured combinations. Unlike the stopped positive-conjugate quadratic model, directed dynamics permit asymmetric responses. That extra expressivity does not, by itself, add an identifiable learning rule or a useful empirical constraint.

Let a declared state obey `dx/dt = f_theta(x) + B u`, and let `x*(u)` solve `f_theta(x*) + B u = 0`. Fix function readout `h_eta(x*)`. At a nonsingular local Jacobian `J = D_x f_theta(x*)`, an infinitesimal circuit edit gives

    delta x* = -J^{-1} D_theta f_theta(x*) delta theta.
    delta y = -grad h_eta(x*)^T J^{-1} D_theta f_theta(x*) delta theta.

The proposed reusable object is a restricted, independently justified family of circuit edits, rather than a freely chosen scalar correction. If a local row update has `J_new = J + e_i v^T`,

    J_new^{-1} = J^{-1}
       - (J^{-1} e_i v^T J^{-1}) / (1 + v^T J^{-1} e_i).

This is precisely Sherman–Morrison, not a new update algorithm. The first formula is ordinary implicit differentiation. Finite edits also change equilibrium, Jacobian and often the readout; a rank-one inverse identity alone is not the exact finite biological update. A valid local-circuit class could still provide sample or compute efficiency; known-family membership does not preclude that. However, **no independently supported edit class or new estimation/selection operation has been supplied here**, and an ordinary constrained refitter can use exactly this parameterization and inverse identity.

With scalar functional feedback `r`, the linearized measurement is only `r ≈ a^T delta theta`. An unrestricted circuit repair is nonidentifiable along `ker(a^T)`, even though those directions may alter later combinations. Multiple known feedbacks can reduce that nullspace; neither one-feedback nonidentifiability nor the previous scalar-equivalence STOP proves all multi-feedback nonlinear updates useless. A useful rule must identify which shared circuit parameters the legal observations constrain and demonstrate generalization beyond direct residual completion.

## Executed new counterexample: relaxing reciprocity does not identify finite combinations

No historical biological test was rerun. `research/update_law_search_20261023/mechanism/witness.py` executed a new deterministic mathematical witness, recorded in `WITNESS.json`:

    dx1/dt = -x1 + u1 + c*x1*x2
    dx2/dt = -x2 + u2.

Take `c` in `{-1/2, 0, 1/2}` and interventions in `[0,1]^2`. Every model has the same control state and Jacobian `-I`; every single-axis dose has the same equilibrium: `(u1,0)` or `(0,u2)`. Starting from zero, their complete single-axis trajectories also coincide because `x1*x2` remains zero. Nevertheless a simultaneous unit combination has state `(1/(1-c),1)`. For the identical readout `h(x)=x1+x2`, the three pair outcomes are `5/3, 2, 3`. All these equilibria are stable: eigenvalues are `-1+c*u2` and `-1`, negative on the declared domain.

Thus even perfect single-dose-axis endpoint information and the exact control Jacobian cannot identify mixed curvature. This is an elementary nonidentifiability witness, **not a new impossibility theorem, not an empirical account of Norman, not a claim of physical nonequilibrium**, and not evidence that paid pair feedback could not learn `c`. Existing pair function labels can identify this toy `c` when its readout/model is known; arbitrary real state operators are much less constrained. Joint-support state observations, known biochemical structure or targeted perturbations can resolve ambiguity. Single-only state trajectories are not automatically enough. This witness is distinct from retrying the prior potential sign test.

The same script separately verified the exact directed low-rank inverse identity to maximum discrepancy `2.220446049250313e-16`. That check supports only the mathematical reduction to a standard inverse update. No biological values were read or models fitted; no provider API calls or independent biological tasks occurred.

## Actual closest primary sources

1. **PerturbODE**, *Interpretable Neural ODEs for Gene Regulatory Network Discovery under Perturbations*, arXiv **2501.02409v2**, 2025-02-01. Newly retrieved original full HTML, 597,364 bytes, HTTP 200, retained `perturbode.body/.txt`, hash/URL in `PRIMARY_RECEIPTS.json`. Section 3.1 already learns `A sigma(alpha ∘ (B y-beta)) + sum_j s_j e_j - W y` with directed low-dimensional modules, shared nonlinear dynamics and intervention-specific shift strength; 3.2 implements perfect interventions by masking targeted rows. Sections 3.3–3.4 use ordinary end-to-end transport loss and optional stable-endpoint regularization. It compares heldout-TF responses, not our function-feedback repair or inherited-improver test. It blocks novelty for shared directed neural ODEs, finite nonlinear responses, local modules, shift/perfect inputs and ordinary feedback refitting. It does **not** establish exact equivalence to every future circuit-update algorithm.

2. Root supplied original primary text **Explicit Mechanistic Operators…**, `root_sources/PMC13605750.xml/.txt`, read as source material, not another agent conclusion. This is explicitly a **Perspective**, received/revised/accepted Aug–Sep 2026, with no new data, model implementation or performance result. It already proposes mechanistic-operator evaluation against capacity-matched static/learned-dynamical, late-fusion and rewired controls. It motivates the proper control structure, but supplies no positive result for this candidate.

3. Root supplied original **PertAdapt** text, `root_sources/PMC13341120.txt`, read as source material. It uses a frozen foundation model, GO-masked adapter, GEARS condition encoder and adaptive loss for sensitive/background genes. Its seven RNA perturbation collections are not seven functionally paired later tasks for this proposal. Neither adaptive loss nor pathway-masked sparse updates should be renamed a new RSI mechanism. I did not reproduce its results or inspect numerical datasets.

4. Actual registry searches also surfaced **Testing and overcoming the limitations of modular response analysis**, DOI `10.1093/bib/bbaf098` (2025), and **SPECTRA**, DOI `10.64898/2026.09.21.752624` (2026). The former attempted OUP primary URL returned 403 and latter bioRxiv full-text URL returned 429. Their full methods were **not verified**, and no equivalence or novelty claim relies on their titles/abstract metadata. Search bodies, projections and failed retrieval receipts are retained. Do not infer literature absence from these failures.

## Accessible data, lawful feedback and a discriminating experiment

Already qualified: Norman 103 single/control RNA profiles plus 3,160 source functional pairs and 1,051 previously exposed development pairs. Source OOF among shared genes remains exploratory within one K562 context. No new biological values opened in this role. Protected outcomes remain closed. Double-RNA values were explicitly excluded from the existing single-only protocol; they cannot be smuggled in as free world-model state. A **new paid-information protocol**, if later justified, could qualify source pair states from the acquired raw assets and give the complete payload to every direct control. Existing source records certify raw availability but not a new pair-state training/evaluation panel.

If an independently motivated restricted circuit law emerges, the minimal experiment is conditional functional-feedback transport within the source map, with task labels and output exposure declared as such:

* Freeze the circuit family and a small parameter budget *before* source outcome access for this candidate. Do not choose sparse edges from errors in the same heldout pairs. Split source pairs into earlier feedback, later feedback and untouched evaluation with target-incidence dependence reported. Use identical starts/feedback for all arms.
* Compare directed-state repair with the **same directed model using ordinary union refit**, exact implicit/Woodbury updates where applicable, RNA-conditioned nuclear completion, strong symmetric pair-feature nonlinear/direct regression, simple residual fusion and same-rank tensor/pairwise-feature regression. Include a constrained direct predictor with the same circuit-derived features; it receives all states, labels and priors.
* Primary proposed exploratory gate: at least 5% lower functional MSE than the strongest matched ordinary comparator, positive direction in at least four of five preregistered source folds, plus a preregistered combination-ranking utility at fixed feedback cost. Five shared-map folds are not five biological replications. Five percent is a **design choice**, not a noise-calibrated significant threshold. If measurement uncertainty/power cannot support that gate, revise prospectively rather than announce a pass.
* Stop if a standard constrained refit or direct circuit-feature model reproduces the gains at equal total cost, if source feedback cannot distinguish legal edits, if the functional/ranking increments are absent, or if stability relies on outcome-selected exclusions. Never fit new signed/dense-force variants to rescue the closed potential gate.

This is only a potential source capability pilot, not a current approved fit or an identified novel algorithm. Actual later-context function tasks are **not qualified here**. TF Atlas/PertAdapt RNA collections cannot stand in for later drug-function tasks. Any genuine subsequent task must keep intervention/function endpoints and feedback permissions authenticated; only then compare restart, pooling, warm-start/ordinary CL, inherited edit rules and raw-feature policies. Learned edit parameters are Level 1 adaptation. Inherited edit selection may be Level 2 only after later-task utility. Level 3 requires an updated improver to discover better *subsequent* edits than fixed and equal-cost search from common starts; none is present.

## Decision

**STOP_CURRENT_IMPLICIT_RESOLVENT_UPDATE_AS_A_NEW_CORE; REVISE_ONLY_WITH_DISTINCT_IDENTIFIABLE_EDIT_MECHANISM.** The exact proposed algebra reduces to implicit differentiation plus Sherman–Morrison, while directed neural state dynamics and ordinary refitting already have a direct primary precedent. This is a narrow operation-level decision, not a prohibition on all directed state models or constrained system identification. The witness also prevents promoting removal of reciprocity as a sufficient solution to combination identification.

No repeated circuit-error evidence, functional advantage, agent necessity, inheritance, joint gain or improved-improver benefit is established. Do not add editors, policy tiers or RSI layers to this candidate. If another independent candidate has a new verified update operation and an error it can fix, prioritize that rather than continuing this inverse-operator branch.

## Work/failure and exposure ledger

Three OpenAlex requests: all HTTP 200. Three primary requests: one HTTP 200, one 403, one 429. No downloads from blocked sources were retried. One broad local `rg` emitted excessive matches from one-line HTML and included a missing historical directory; follow-up used bounded Python source projections and the correct existing locations. No raw expression or functional outcome arrays, protected outcomes, other new reviewers' reports or private credentials were opened. One synthetic mathematical script executed once. All code is under `research/update_law_search_20261023/mechanism/`; all new evidence here. No author contact, no wet experiments and no new provider calls.
