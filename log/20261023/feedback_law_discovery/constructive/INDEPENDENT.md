# One attempted feedback law: exchangeable assay writes, chronological biological state

2026-10-23. **ONE_PRELIMINARY_RESTRICTION_FOR_ADVERSARIAL_REVIEW; no biological-fit/core GO.** Proposed restriction: for parallel functional assays collected at the same biological checkpoint, changing the record serialization order or grouping must not change the inferred response law; actual exposure/washout chronology remains an ordered input. Enforce this distinction while source-training a learned updater. Novelty and utility are unestablished; competent set predictors and batch inference already satisfy much of this constraint, so they may eliminate the candidate immediately. This is an actual attempted operation, not another claim that memory architectures alone solve the goal.

## Full objective and limits read

The user objective remains virtual-cell intervention/function learning plus autonomous research, inherited updater benefits, and eventually an improved improver under common-start/equal-budget comparison. Actual functional utility, strong direct/refit/CL/AL/mixture/search comparators and world/agent/inheritance/joint decomposition remain required. Read functional_mechanism_frontier ROOT_REVIEW/DECISION and retained prior scoped STOPs. This does not revisit old Norman residuals, nullspace protection, CDK/Emerald menus, scalar attenuation, target-label renaming, transport or missing identity sources.

## New original methods and failures

Three purposeful HTTP requests only, receipts/body/hash retained:

* An official arXiv query for test-time learning plus dynamics/system identification returned503,126bytes. It was not retried or treated as evidence of no literature.
* **Titans: Learning to Memorize at Test Time**, arXiv2501.00663v1,2025. Original HTML482711bytes; SHA2564299f82339eed910b80f982068efb2156517a1cc8cb9d43fc29d0d48b7dcca3e.
* **It's All Connected: A Journey Through Test-Time Memorization, Attentional Bias, Retention, and Online Optimization**, MIRAS, arXiv2504.13173v1,2025. Original HTML593751bytes; SHA256c5818c6bdea8a36f7483ca425e194a648b894f4223c5dc69360c9192b4b56450.

Actual bounded Titans§3.1and MIRAS memory/optimizer passages were read after standard-library full HTML projection. Broad search output included author Results snippets and was truncated; no author numerical result is reproduced or used as our evidence. No author code imported/run, paid API, biological arrays, protected labels, reserve or model fit. Local PowerShell brace-path syntax failed once during duplicate search; corrected to explicit filenames. Existing Markdown search found related generic update literature, not an authenticated identical source in its bounded matches; no comprehensive novelty claim. Native exact model/cost unavailable.

Titans actually uses a learned memory with gradient-surprise momentum and forgetting:

    S_t = eta_t S_(t−1) − theta_t grad_M ell(M_(t−1), x_t),
    M_t = (1−alpha_t) M_(t−1) + S_t,
    ell = ||M(k_t)−v_t||².

The source explicitly describes eta/theta as data-dependent and association k/v projections as outer-trained. This already implements learning how to write/forget at test time, not merely static retrieval. It does not claim that parallel biological assay permutations are time trajectories.

MIRAS explicitly organizes design into memory architecture, attentional-bias loss, retention regularization and optimizer, including a Mesa-style full-history least-squares memory optimized by Newton methods, not just SGD/delta updates. Thus substituting a nonlinear memory loss or Newton solver is not sufficient novelty. Its FTRL/learning-retaining formalism supplies a strong ordinary cumulative-objective comparator. These sources change the next experiment: test an **assay-specific consistency constraint against these concrete learned/sequential and cumulative alternatives**, rather than claim surprise memory or retained gradients as our invention.

## Exact candidate restriction and update

At one fixed patient/cell context checkpoint c, let H_c be the complete legally available biological exposure/time history, and phi_c its frozen measured state representation. An observation o contains unique physical assayID, intervention/dose, endpoint/time, actual functional outcome, controls/precision metadata and acquisition conditions. Drug outcomes are measurements on separate aliquots at the same defined checkpoint; their file-arrival order is not biological time. Fresh independent replicate wells are distinct observations, not duplicate records.

Let theta0be a source-trained functional/world predictor, h a fast update state, eta inherited parameters of a learned optimizer and ell_eta a learned source objective. A single package update is explicitly

    U_eta(h,S; H_c,phi_c) = h − a_eta(h,S,H_c,phi_c)
                               * grad_h [sum_(o in S) ell_eta(f_(theta0,h)(phi_c,H_c,action_o), y_o, metadata_o)],

where package aggregation is a sum with fixed whole-assay normalization. This is a conventional learned objective/step updater; source learning must not claim that interface is new. A one-step or fixed-Kversion is frozen before outcomes; Kcannot increase for favorable tasks. theta0/H_care not silently rewritten by assay order.

The proposed new restriction concerns **compositions of U**, not its scalar loss name. For disjoint packages A,Bfrom that same checkpoint:

    Q(U(U(h,A),B)) ≈ Q(U(U(h,B),A)) ≈ Q(U(h,A∪B)),

where Qis the vector of functional predictions on a predeclared source-only query-action set. This is output-level exchangeability and partition consistency, not equality of unidentifiable hidden states. Duplicate identical assayIDs are deduplicated before any model sees them; that is data hygiene rather than the innovation. Distinct technical replicates retain their identity and likelihood weight. Do not impose these relations across different physical exposure times or repeated sequential treatments.

Train eta on whole source-context episodes with real future query outcomes and a fixed consistency penalty:

    L_eta = L_query(Q(U(U(h0,A),B)), y_query)
          + gamma * ||Q(U(U(h0,A),B)) − Q(U(U(h0,B),A))||²
          + gamma * ||Q(U(U(h0,A),B)) − Q(U(h0,A∪B))||².

Here gamma and source package sampler are predeclared/selected only within a charged source budget; this report launches no search. Labels for source query loss are genuine released source functional assays, not world-model rollouts. Counterfactual prediction evaluations for the consistency terms are charged, and source-query ground truth never enters target updates. At deployment eta is retained but hstarts at the same reset h0for each independent context; actual biological H_cis provided to every comparator. This is inherited **updater** testing, not a revised improverG.

## Why the constraint might matter at finite cost

A sequential learned memory can treat the last large functional residual as a recency/surprise cue. With scarce real feedback and arbitrary lab batching, it might learn a serialization artifact rather than a reusable drug-response update. Cumulative batch refit/set predictors do not have this particular defect. The candidate hypothesis is that imposing the correct same-checkpoint invariance reduces source-task sample requirements for a compact nonlinear updater, while retaining history-dependent action/function reasoning. It is not more expressive than unrestricted direct prediction and offers no asserted compute superiority: each source step costs multiple unrolls; cumulative refit may be cheaper at these dataset sizes.

A plausible world-model value would need a state-conditioned intervention response representation that transfers the constrained updates better than a matched direct episodic representation. Merely encoding c/drugIDs or satisfying commutativity is not a virtual cell contribution. The biological history dimension remains explicit precisely so the rule does not erase true path dependence.

## Small exact falsifiers before any biological run

**Serialization failure:** for a scalar memory with U(h,y)=(h+y)/2and h0=0, outcomes yA=0,yB=1give AB1/2versus BA1/4. These are the same physical observations and thus cannot legitimately indicate different posterior biology under the declared fixed-checkpoint contract. This is a counterexample to the unrestricted memory's invariance, not an executed biological result or refutation of Titans' language sequence objective.

**Restriction failure:** if Ais drug exposure and Bis washout performed on the same living lineage, ABand BAare different physical interventions. Enforcing commutation there can erase real resistance/recovery. Measurement drift, different assay times/aliquots or nonignorable selection also invalidate the assumed exchangeable package; a recorded time/history feature alone cannot fix unmeasured batch biology. These circumstances must stop/narrow the contract, not become hidden exception gates.

**No headroom:** if a same-information set predictor, ordinary cumulative refit or meta-learned additive sufficient-statistic model already has low error and exact consistency, zero consistency error from our model proves nothing. Source randomized-order training of the same learned updater is an especially strong cheap baseline; if it matches the explicit constraint at equal source-compute budget, stop the proposed training contribution. Hardcoding Uvia a union-of-all-observations set encoder would execute an ordinary conditional predictor, not demonstrate this learned-update restriction's separate value.

## Actual functional endpoint and minimal executable source-only contract

One already authenticated exposed source is BeatAML2: previously documented local normalized baselineRNA, sample mapping and probit_curve_fits_v4_dbgap include dbgap_subject_id/dbgap_rnaseq_sample/inhibitor/AUCwith patient grouping. Actual task is ex-vivo dose-response AUCcompletion in a newly revealed patient/context, not clinical response and not repeated in-cell drug administration. That asset's low-rank state-model branch is STOP. This proposal does not retune that representation, reopen a protected fold or claim the already exposed data as confirmation. It would use existing exposed source only for a **new updater consistency falsifier**, with frozen inputs/partitions/functional targets after opposing review. No values or loaders executed here.

Minimal next experiment if approved: select one already exposed, historically lawful source partition; freeze wholepatient grouping, fixed same-checkpoint action/probe packages and existing assay/control normalization. Source-train the same compact updater twice from identical theta0/h0: ordinary source-query loss versus the above consistency objective, matching total optimizer steps/FLOPs/evaluated package orders rather than giving the constrained arm extra source exposures. Include randomized-order training, direct set predictor and cumulative ordinary refit from the outset. Reveal the same small whole-assay support package to every arm; evaluate only held-out drug AUCand numerical ranking within each source context, plus permutation/grouping sensitivity on exactly the same acquired observations. No adaptive policy or different exposure histories initially; those would change the contract.

This is executable from released functional data in principle without a new wet assay, but it requires a fresh pre-access protocol and checking existing source exposure/STOPboundaries. It does not become a new independent later task merely by splitting patients again. All histories/replicate IDs and normalization provenance are required. If no same-checkpoint block can be authenticated from existing metadata, stop this candidate rather than resume an asset qualification loop.

Strong comparators must receive all purchased baseline/state/drug/response/control/history information: direct ridge/kernel/nonlinear conditional completion, union refit, replay/regularized CL, ordinary ALwhere later allowed, simple mixture, same-law cumulative/set implementation, source-trained learned optimizer without consistency, randomized-order augmented optimizer, and equal-total-budget program search over the same choices. Compare same-state/no-state architectures separately; no lawfully unavailable queryRNAis gifted to our model. Extra unrolls and source tuning count against the constraint.

Necessary source success requires materially lower held-out functional AUCerror **and** predeclared useful nomination/ranking loss than the strongest matched opponent, with reduced arbitrary serialization sensitivity. Lower consistency penalty alone is not useful. An assay-derived practical margin is not manufactured here; protocol/review must define one before new numerical reads. Stop if randomized-order training or set/refit controls match it, if functional performance worsens despite invariance, if history-dependent biology was collapsed, or if source compute cancels any benefit. No gates, auxiliary residual heads or posthoc subgroups to rescue it.

## Novelty, inheritance and recommendation

The underlying SGD/metaobjective, set invariance and semigroup consistency all have substantial prior art; this pass has **not** established the combination as novel. The only potentially substantive contribution is the typed distinction between parallel assay updates and biological chronology, with a measured finite-source-budget advantage for learned functional response revision. This is weaker than an identified biochemical sharing law and must be challenged accordingly. It may be merely a correct engineering constraint already captured by a strong direct set model; that is an explicit stop, not a reason to weaken opponents.

If the bounded functional test is positive, later contexts must compare inherited eta versus reset eta at common predictor/task starts and equal early+late budget. Agent utility needs a separately tested acquisition policy; joint world/agent/updater benefit needs factorial controls. RSIlevel3requires G1versusG0from common eta/history/budget on fresh tasks; learning etaonce with a fixed metaobjective is not that test.

Recommendation: **GO_TO_ADVERSARIAL_REVIEW_ONLY** for this one attempted consistency-constrained updater, no fit/core/performance GO. If reviewers identify an exact existing operation/benchmark rendering the restriction merely ordinary set-conditioning without finite-budget headroom, record failure rather than another architecture proposal. No new HTTP, biological-label opening or execution follows automatically.
