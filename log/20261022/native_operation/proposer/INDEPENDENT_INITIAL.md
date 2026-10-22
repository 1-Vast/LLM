# Independent constructive operation, prior to peer reading

2026-10-22. One candidate only. Status: **HYPOTHESIS; algebraic minimal falsifier proposed; NO_PROMOTION**. I have not read any current native_operation peer files. Root asked for native construction, authentic 2025–2026 mechanisms, finite-budget advantages rather than a universal expressibility veto, no new fits or assay decoding, and preservation of all stopped routes/reserves. Root later clarified that a parameter-learned proposal policy can operationally meet Level 3 if its improved-improver effect is independently tested; novel algorithms and operational RSI are different claims. This clarification informed the design below. No peer candidate or verdict was supplied.

The requested advertised model selection was gpt-6-astra/high, as reported in the task. This is not independent backend attestation. No DeepSeek calls occurred. Original user Karpathy rules apply. Git HEAD is ed2e360093d25e577ea02a5011d54d13b32ec8f1. Existing dirty files were inspected and not changed. No on-disk AGENTS.md appeared in root/research/log direct checks; the prior audit reports a recursive search found none.

## Scientific bottleneck and the single proposed operation

For a cancer treatment schedule, exposure to A before B may change signaling and subsequent sensitivity differently from B before A. Predicting an endpoint independently for every schedule wastes combinatorial structure. Fitting every biochemical rate from sparse signaling observations can spend an equally unaffordable measurement budget. The proposed operation directly measures the **local noncommutation of two interventions after cancelling the background dynamics**, then inserts that measured composition rule into a world operator. The scientific task would be choosing drug order to increase a measured apoptosis/viability outcome, while respecting a measured healthy-cell or toxicity constraint if that outcome is actually available. This is a research schedule-selection task, not a clinical recommendation.

Candidate: **drift-cancelled intervention-bracket expansion**. Name is descriptive, not a novelty claim. The biological content is a measured local response to exchanging action order. Feedback can make an initially commutative action world noncommutative. The claim is local composition and finite-budget schedule decision value, not recovery of a unique biochemical graph.

This is distinct from the stopped antibiotic history-state split and stopped one-eta TG clock: no histories are partitioned into hidden states, no temporal warp is fitted, no old labels are reopened. However, it has a very close conventional reduction to controlled-system identification and second-order path-signature regression, addressed below.

## Formal operation and executable rule

Assume a common initial measured state x, smooth local vector fields, equal short pulse length h, and matched washout/vehicle handling. During vehicle the generator is f0; under action a it is f0+fa. Let X_ab be the measured state after a for h followed by b for h. Zero denotes vehicle. For vector fields define [u,v](x)=Dv(x)u(x)-Du(x)v(x), with chronological composition stated explicitly to avoid a sign convention error.

Use the six actual measured treatment sequences ab, ba, a0, 0a, 0b, b0:

    c_ab(h) = (X_ab - X_ba - X_a0 + X_0a - X_0b + X_b0) / h**2
            = [fa,fb](x) + O(h).

Proof: X_ab-X_ba = h**2([f0,fb]+[fa,f0]+[fa,fb])+O(h**3). Subtracting the two corresponding one-action/vehicle differences cancels both f0 terms. Ordinary action order alone does not cancel drift. Directly interpreting X_ab-X_ba as [fa,fb] is invalid in general.

For affine local fields use augmented observed coordinates z=(1,x), generators A0,Aa,Ab, and B_ab=Ab Aa-Aa Ab. Then c_ab approximates B_ab z. Do not assert that this vector identifies the full matrix or a molecular edge. At one start it identifies only the action of the bracket on that start. Repeated initial contexts are needed to estimate a field, and the constant coordinate stays zero.

Minimal mutable world representation is a table of measured first-order action increments and pairwise signed composition corrections on a predeclared observed coordinate system. For short schedules with the same action multiset, use

    prediction(w) = symmetric_multiset_prediction(w)
                  + 0.5 * sum_ab I_ab(w) * h**2 * c_ab
                  + measured_background_order_terms(w).

Here I_ab is the signed pair-order count (+1 for a before b, -1 for b before a, summing repeated occurrences). Include measured background terms from a0/0a; silently dropping these would undo drift cancellation. For ab versus ba, the bracket part differs by h**2*c_ab. This is a local second-order approximation; arbitrary long schedules, changing cell composition, irreversibility, delayed exposure and saturation can invalidate it.

Rule update from feedback: start with c_ab=0 for unmeasured pairs. Select a six-sequence bundle, form its c_ab estimate with replicate-aware covariance, and insert the antisymmetric rule c_ba=-c_ab only if a predeclared interval excludes zero and a fresh duration/sequence check passes. A failed higher-order closure check retains the failure and rejects extrapolation. It does not license claiming a latent mediator, adding arbitrary rules, or reopening evaluation outcomes. To keep the candidate minimal, **do not implement nested brackets yet**. Such expansion is a possible later hypothesis requiring its own stencil and falsifier, not a second candidate in this phase.

## Why there might be a finite-budget advantage

There are quadratically many pair brackets but factorially many orders for a fixed set of distinct drugs. If low-order local composition is valid and only a small subset of action pairs is noncommutative, sparse bracket measurements can predict new orderings without identifying all microscopic rates. This is a conditional representational/computational advantage over fully enumerating schedules or identifying a needlessly large biochemical ODE. It is **not** an information-theoretic lower bound against all ordinary methods. The same signal can be exploited by a strong ordinary signature model.

At very small h, division by h**2 amplifies independent endpoint noise: six independent equal-variance state measurements give variance 6*sigma**2/h**4. Shorter pulses reduce truncation bias while increasing variance; extrapolating h to zero is not free. For matched correlated measurements the full covariance is required. The actual budget must include every well, washout/control, replicate and two pulse lengths, not count a six-sequence stencil as one experimental observation.

Necessary modules are only (1) this local signed composition world, (2) a bundle selector, and (3) a separately evaluated inherited proposal rule if justified. No LLM planner, latent-state encoder, multi-agent voting, retrieval system, or unconstrained code generator is mathematically required.

## Strongest ordinary reduction, not a universal veto

The second-order signed-pair formula is exactly an order-feature/signature regression model with the six-sequence contrast used as an estimator. A faithfully implemented second-order controlled ODE/Magnus or BCH expansion can compute the identical update. Thus the candidate does not have an established new algorithm merely because it edits world rules or uses six controls. The constructive mechanism is useful to test, but **novelty must not be claimed if its whole behavior is reproduced by this matched-input, matched-cost ordinary baseline**.

Required comparator suite: direct schedule predictor with time/order/dose features; ordinary refit and continuous/replay update; a controlled ODE or bilinear state-space model with identical observed coordinates and allowed action semantics; sparse first/second-order path-signature regression with the same stencils; active design maximizing expected decision value; fixed selector plus the bracket world; ordinary mixture of direct and dynamic models; and equal-cost random/heuristic/Bayesian proposal search. Give all methods identical six-sequence bundles, error/covariance information, published knowledge, permissible expansion rules, model selection opportunities and test access. Charge numerical solver and proposal costs separately. It is unfair to use only order-blind direct prediction or fully unstructured black-box program search.

The decisive innovation objection is therefore a **specific executable reduction**, not a statement that every world model is representable by a predictor. It remains logically possible that constrained adaptive measurement/expansion yields better finite-budget science; that would need evidence against the faithful conventional version, rather than a new name.

## Native improver and genuine RSI test

The proposal rule can rank unmeasured bracket bundles using features available before outcomes: initial disagreement between direct and composition models, source-estimated uncertainty, reachable terminal utility sensitivity, and stencil cost. Use a small regularized logistic score q_theta(phi), trained on earlier tasks' actual per-cost downstream improvement outcomes; choose argmax q_theta(phi)/cost. Fixed source scaling, learning rate/grid and rejection handling must be frozen. This changes **which future world-rule improvement is attempted**, not just the world's fitted coefficients.

This is ordinary contextual proposal learning and could still produce valid operational Level-3 evidence; algorithmic novelty is separate. For the improved-improver test, compare theta_new and theta_old from the **same fresh downstream world state**, candidate library, data, remaining assay budget, compute/fit budget and feedback access. Include unchanged theta_old given the extra cost that trained theta_new; model-only transfer, experience replay and frozen learned heuristic; and equal-budget Bayesian/program-search proposers. Later biological groups must be independent and outcomes not used to select theta_new. Score improvement per total charged cost, probability of finding an effective rule, and eventual scientific utility—not just best final predictive score.

World, selector, inheritance and joint effects need factorial controls. World benefit means improved actual order-selection utility versus direct prediction under fixed selection. Agent benefit means adaptive bundle selection beats fixed/ordinary design using the same world. Inheritance benefit means later rule acquisition improves beyond transferred model state and ordinary replay. Joint effect is the interaction, not a sum of separate wins. No such test has happened here.

## Frontier source authentication and transfer limits

Authenticated arXiv2505.22954v1 HTML, Darwin Gödel Machine (first submission 2025-05-29), and the abstract endpoint, which now identifies a 2026-03-12 v3. Source receipts bind exact URLs/status/bytes/hashes. The v1 primary HTML describes an archive of agents, sampling an existing agent, self-modification, and empirical downstream evaluation; nonwinning ancestors can serve as stepping stones. Its mechanism motivates retaining rejected local composition models/certificates for later proposal learning instead of discarding all failed expansions. Biological adaptation is to archive measured local rule failures and the acquisition policy, with costly assay-grounded evaluation and separate common-start tests. DGM does **not** supply the Lie-bracket stencil, causal identification or biological evidence. The archive alone has already been explored in MAESTRO and is not claimed as a new core.

A bounded Crossref2025–2026 title search for learning/Lie brackets returned algebra/control papers, not an authenticated matching frontier-learning mechanism. Metadata is retained; no inference of novelty from this unsuccessful search. Thus **the requested substantial 2025–2026 core-mechanism transfer is presently unqualified**. Classical composition theory is the main technical ancestry. Do not sell DGM as if it solved this scientific operation.

## Real measurements and data gate

Europe PMC authenticates Lee et al., *Sequential application of anticancer drugs enhances cell death by rewiring apoptotic signaling networks*, Cell2012, DOI10.1016/j.cell.2012.03.031, PMID22579283, PMC3501264. This authenticates a relevant real biological study identity, not the existence of the exact needed replay corpus. The bounded EuropePMC fullTextXML GET returned HTTP500 and is saved as a failure; no supplement was decoded. Do not assume that paper's schedules are short equal pulses, complete washouts, independent starts, or complete six-sequence/two-duration bundles. No disease-specific efficacy claim is made from its title.

The real experiment requires all six sequences at two predeclared pulse lengths; shared biological initial-state definition; exact drug, dose, pulse/washout timestamps; vehicle controls; well/run/biological replicate identity; matched molecular-state readouts; and independently measured later functional endpoints for candidate schedules. Molecular and functional measurements may need parallel wells; no destructive assay is treated as repeated measurement of the same cell. Identity matching must separate biological replicates from technical wells. Real multi-context tasks must support source, development and later whole-context separation. If those requirements are absent, the candidate is **BLOCKED for real replay**, not biologically disproved. No existing stopped corpus is implicitly requalified.

## Minimal falsifiers and decision

First, an exact synthetic algebra audit of noncommuting affine generators should verify that the six-term stencil cancels arbitrary drift to second order, equals the ordinary second-order signature/controlled-generator calculation, has antisymmetry, and fails to justify finite-duration exactness. This is an implementation/theory falsifier only, never biological success. A sign error or noncancelling drift rejects the literal operation before any data work.

Second, before numerical access, qualify metadata for the full measured bundle and independent later functional target. If no usable bundle exists, stop this data route without importing simulation feedback.

Third, freeze a smallest real pilot on source/development only. At the shorter and longer durations, test bracket scaling against replicate noise, then assess unseen-order functional decisions against strongest matched ordinary signature and controlled-ODE baselines. Stop this exact expansion if the order correction is indistinguishable from noise at the necessary utility margin, systematically fails the duration check, or is matched by the simpler implementation within a predeclared useful-gain margin. No threshold/split/reserve rescue is allowed. Numerical utility margins require actual endpoint units/replicate design and therefore cannot honestly be fixed from the current unqualified metadata.

Independent recommendation: **NO_PROMOTION; allow only the bounded algebraic falsifier and biological/source qualification if root selects this candidate**. I do not recommend a new fit or building an RSI stack. A concrete intervention operation has been generated, with a plausible finite-budget rationale and an explicit ordinary reduction. At present it lacks an authenticated suitable biological corpus, a substantive new frontier transfer, and a demonstrated difference from the strongest ordinary method. Full MAESTRO objective remains ACTIVE/NOT_ACHIEVED.

Before sealing, the corrected historical-source search identified Lee2012 in intervention_schedule_qualification/DECISION.md, which I then read. Its GSE30516 metadata contain erlotinib-only transcript sampling and explicitly STOP that archive as a full drug-order benchmark. This strengthens the data limitation; no recommendation here reopens that stopped configuration. That historical decision is included among input hashes. The exact six-sequence corpus remains unqualified, and no further retrieval is authorized merely to rescue this source.

Also before sealing, root supplied a historical commutator antecedent path and the titles NetworkWorldModels2610.01048v1 and AutoNovo2610.16232v1, with an instruction to read them only after this seal. I have not read those files or either paper. This message and its warning that noncommutation alone does not establish novelty are disclosed; this is independent reasoning with common instructions, not blinding to all root communications.

Resource ledger at initial seal: five HTTP GETs (four success, one HTTP500), one failed optional-parser invocation then standard-library correction, one failed Windows glob search then corrected search, and one no-op patch attempt rejected because its expected partial line did not match. Zero predictive fits, zero assay-value conversions, zero protected-reserve accesses, zero DeepSeek calls. All new code is under research/native_operation_20261022; evidence is under log/20261022/native_operation/proposer. The source acquisition returned about3.17MB of paper/metadata content, not a biological data download.
