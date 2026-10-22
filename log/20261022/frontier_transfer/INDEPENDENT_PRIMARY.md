# Independent primary-source position — sealed before peer review

2026-10-22. Decision: **NO_PROMOTION of a new core**. Three in-window primary papers are authenticated at full HTML level; a fourth is rejected on its true first-submission date. There is one concrete, unpromoted diagnostic below. It asks whether response-conditioned two-step acquisition has any advantage on CiPA before spending effort on a learned world/update model. It does not rename standard Bayesian design as innovation.

Scope: read REPORT header, next_asset/DECISION.md, strategy_rethink/RESULT_DECISION.md and cipa_calibration_probe/PROTOCOL.md. Also searched prior RSI review and read its DECISION.md. No biological values, source/CiPA fitting outputs, TG later14, AZ413 or CiPA later8/9 outcomes were read. No numerical experiment was executed. No production or previous research artifact was edited. This position precedes reading any new peer review. Parent must arrange actual cross-position debate; this document is not that debate.

## Authenticated papers and exclusions

All eight requests returned HTTP 200. Exact body, headers, requested/final URL, UTC acquisition timestamp, byte length and SHA256 are in sources/*receipt.json. Extracted text is a convenience derivative; original HTML is authoritative. First dates below come from the arXiv submission-history section, not the ID prefix, HTTP Last-Modified, current abstract wording or conference year. DOI below is the arXiv repository DOI displayed on the primary abstract page, not a claimed journal publication DOI.

| Paper | Primary ID / DOI | First submission UTC | Read version / content | Window decision |
|---|---|---|---|---|
| V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning | 2506.09985 / 10.48550/arXiv.2506.09985 | 2025-06-11 17:57:09 | v1 full HTML, especially sections 2.1, 3.1–3.2 and 4; abstract history reports only v1 | eligible CV |
| Self-Adapting Language Models (SEAL) | 2506.10943 / 10.48550/arXiv.2506.10943 | 2025-06-12 17:48:13 | v1 full HTML, sections 3.1–3.2 and Algorithm 1; current abstract is v2, 2025-09-18 16:17:30 | eligible NLP |
| Darwin Gödel Machine | 2505.22954 / 10.48550/arXiv.2505.22954 | 2025-05-29 00:26:15 | v1 full HTML, sections 3–4 and Appendix A.4; current abstract is v3, 2026-03-12 23:47:40; v2 2025-09-26 16:36:03 | eligible learning-to-improve; not newly discovered here |
| Titans: Learning to Memorize at Test Time | 2501.00663 / 10.48550/arXiv.2501.00663 | **2024-12-31 22:32:03** | v1 full HTML, section 3.1 | **excluded from requested 2025–2026 first-release cohort** |

Primary links: https://arxiv.org/html/2506.09985v1 ; https://arxiv.org/html/2506.10943v1 ; https://arxiv.org/html/2505.22954v1 ; https://arxiv.org/html/2501.00663v1 . This is a bounded review, not exhaustive novelty certification. No newly first-released 2026 paper was qualified in this search. DGM's 2026 revision must not be sold as a 2026 invention; the operational reading here is v1. No code checkout, authors' experiment replication or PDF visual inspection was done.

## What operations the papers actually contribute

**V-JEPA 2.** Eq. 1 predicts masked patch embeddings against a stop-gradient EMA teacher. After pretraining, the encoder is frozen. In section 3.1 the action-conditioned predictor is trained on actual aligned frame/end-effector sequences; actions are differences of adjacent end-effector states. "Unlabeled" means no task/reward/success annotation, not absent action/state measurements. The post-training objective is

`L(phi) = mean_k ||P_phi(a_<=k,s_<=k,E(x_<=k))-E(x_(k+1))||_1 + ||P_phi^[2](a_1:2,s_1,E(x_1))-E(x_3)||_1`.

The second term explicitly feeds a predicted representation back into the predictor. In practice rollout T=2, even though the illustration shows T=4. Eq. 5 plans actions minimizing final latent distance to a goal; section 3.2 uses the **ordinary cross-entropy method and receding-horizon control**, executes the first action, observes, then replans. The useful transferable operation is training/evaluating a model under its own two-step predicted inputs and replanning after real feedback. It is not the mere encoder/world-model label.

CiPA has static intervention bundles, no authenticated same-cell before/after trajectories. Drug dose code is not time; site order is not a cellular transition. Thus a V-JEPA cellular dynamics rollout is not licensed. A *research-state* transition after querying a legal bundle is legitimate, but is an epistemic solver update, not observed cell evolution. Standard model-based active learning/dual control already covers that formulation. Frozen functional coordinates `(EAD fraction, measurement fraction, conditional ddFPDc)` could be useful inductive structure, yet the current protocol already supplies them to strong conventional refits. No representational novelty is cleared.

**SEAL.** Section 3.1 explicitly calls itself meta-learning. Its action is a self-edit specifying generated adaptation data and/or update settings, not merely an answer. At current solver parameters theta: `e ~ pi_theta(e|C)`, `theta' = SFT(theta,e)`, `r = heldout_performance(theta')`. Its outer ReST-EM uses rejection sampling plus SFT on successful edits (or the best edit in its knowledge task). Since reward depends on the current starting solver, edits sampled/scored against a previous solver may be stale; it regenerates and re-evaluates on-policy. This is a precise operation that unconditional source-best rankings omit: **the value of an update is conditional on the solver being updated**.

Transfer: generate a mask/weighting or loss operator from paid calibration residuals, apply it to a fixed solver, score on disjoint source functional conditions, then train the generator on that improvement. But synthetic labels are not paid biological evidence. A finite operator menu is contextual algorithm selection; continuous loss weights are bilevel reweighting/learned optimization. An LLM emitting those weights does not break that equivalence. Prior log/rsi_later_task_literature/DECISION.md already reserves SEAL, editable improvers, diagnosis and inheritance as close precedents. SEAL is not a new proposed core here. Its ARC experiment selected 11 training/8 evaluation tasks solvable by the chosen base TTT protocol; that empirical scope is not evidence for arbitrary biological adaptation.

**DGM.** Algorithm 1 maintains an archive of valid self-editing agents; parent agents modify their own implementation, children are evaluated, and valid children enter the archive even without monotonic improvement. This permits nonbest stepping stones and makes the mutation machinery editable. A transfer would be executable assay-selection/update programs with a bounded evaluator and an archive. That is open-ended program search/evolutionary algorithm design, already covered in the previous RSI review. Its additional code flexibility and evaluation cost do not repair CiPA calibration information or qualify a new biological operator. It does not by itself prove the required common-start C4 improvement at equal feedback/compute. Do not repeat its headline solver gains as C4 proof for this project.

**Titans exclusion and equivalence.** Section 3.1's `S_t=eta_t S_(t-1)-theta_t grad l(M_(t-1);x_t)` and `M_t=(1-alpha_t)M_(t-1)+S_t` explicitly amount to gradient descent with momentum and weight decay on an associative-memory loss. This is a useful negative control against renaming online optimization as memory innovation; it is not counted as a 2025 source.

## Specific failure being addressed

The RKT categorical checkpoint lost to uniform old policy by -0.00006221793545108101 despite +0.007878737193642515 oracle headroom. Its logits have exactly source-best ranking: the source S0 subtraction is constant over candidate programs. This only rejects that exact unconditional prior/grammar/partition. It does not test whether *observed update failure at the current solver state* changes the value of the next action. We will not tune or reopen that stopped grammar.

CiPA's registered linear-design baseline updates `A` from feature geometry only, not observed feedback; its uncertainty policy is also fixed before responses. Ordinary refit and acquired-control program selection are substantial baselines, however. Thus a distinct factual question remains: can actual paid feedback change which subsequent control is useful enough to beat these strong controls? This could fail because the four control drugs cannot identify transferable residual structure, or succeed as completely conventional outcome-adaptive design. No CiPA result is available to this reviewer, so no claimed failure pattern is invented.

## One minimal diagnostic, not a promoted innovation

Suggested next eligibility experiment only after the ordinary probe's frozen decision: **finite two-step outcome-conditioned planning over real source residual archetypes**, then exact refit. This tests the operational part of V-JEPA replanning and SEAL's solver-conditional update value without expensive learned latent dynamics. It remains an ordinary Bayesian/empirical-model design comparator.

Definitions: physical source site `s` supplies a complete residual-function archetype on compatible observed bundles; `b(d)` is the cross-fitted source baseline. For candidate archetype `s`, predicted target response is `y_s(d)=b(d)+r_s(d)`. Each head retains its native validity mask; E/M distributions and H conditional observations remain separate. Source same-cell/platform matching and fallback must be frozen before any fit; missing H is not imputed as an outcome. The state `h_t` consists of legal acquired bundle IDs, observed values/masks and the current ordinary solver coefficients. All transition updates `U(h,q,y)` are exact executions of the same fixed ordinary updater, not a new fit family.

Use an empirical posterior over source archetypes

`w_s(h) proportional w_s(empty) * exp[-sum_(q in h) ell_valid(y(q),y_s(q)) / tau]`,

where `ell_valid` uses the protocol's distinct observed heads and source scale. This exponential weighting is a generalized-Bayes design convention, not a calibrated likelihood claim. `tau` must be source-selected inside nested physical-site CV; a finite preregistered grid and all costs are mandatory. This is the only extra ordinary tuning parameter. If fewer than two eligible donor archetypes remain in a fold, abort this diagnostic rather than synthesize an archetype or redefine the task.

Let `R_s(h)` be the fixed 96-bundle evaluation loss of the current solver against source archetype `s`, with the original population/masks. At a source replay, all quantities are derived from the training physical sites; the held-out site's noncontrol outcomes are used only by its evaluator. At deployment, no development noncontrol truth enters `R_s`.

`V_0(h) = sum_s w_s(h) R_s(h)`

`V_k(h) = min_(q in unqueried_controls) sum_s w_s(h) V_(k-1)(U(h,q,y_s(q)))`, for k=1,2.

Each simulated response is a hypothesis, not an acquired observation. Execute only the first chosen query, pay one bundle, obtain its real values/mask, update state/posterior and replan until eight actual bundles have been bought. Costs include every simulation/refit and every true query. Never treat simulation branches as new wet-lab observations. The terminal forecast uses the same ordinary updater as the baseline; only the query choice changes. Source and target caches must not share withheld values. Lexicographic ties, source masks and missingness handling must be fixed before execution.

This is materially different from static source-best ranking because both the posterior and the next selected action depend on the *observed* residuals and the current updated solver. It is **not** materially distinct from classical posterior-predictive experimental design or finite-horizon model-based active learning; the recursion above is a Bellman lookahead. That is the strongest equivalence objection, and it stands. Therefore this is a necessary cheap diagnostic for an information channel, not a new-method recommendation.

Necessary modules: legal finite feedback API; frozen ordinary solver/update; cross-fitted source residual archetypes and exact masks; state-conditioned one/two-step utility calculation; sealed evaluator. Not necessary: LLM, expression encoder, image pretraining, learned dynamics, open-ended code modification, archive or long-term neural memory.

Cheapest staged falsification: (1) source1–5 nested physical-site replay only; check that different real feedback histories actually change planned actions; compare full feedback with a source-frozen ranking and with a within-source permuted residual-history negative control. No action difference means the alleged feedback channel is inactive. (2) Only if source-only evidence clears a preregistered gate, evaluate once on existing dev6/7 using the same16 controls/eight queries/96 evaluation pool and all original E/M/H component scores. The frozen ordinary primary probe must remain intact; append a separately registered experiment. No later8/9 use is needed or authorized here.

Success must require improvement over **every** same-information ordinary comparator from the registered probe, plus one-step lookahead and the exact same empirical posterior predictive estimator without planning. Require lower combined loss on both dev sites and no worsening in any pooled component. In addition require full-feedback planning to beat its response-blind/permuted ablations. A positive result licenses only a separate estimate of practical effect and confirmation; it does not establish a novel core, world, inherited policy or C4. If ordinary Bayesian design reproduces the effect, keep its useful operation and reject novelty. If two-step and one-step tie, stop rollout expansion. If source eligibility, action-dependence or any registered performance gate fails, stop this exact diagnostic rather than expand models, tune controls or open reserve sites.

One important limitation: only five physical source sites and two dev sites exist here. Their repeated query orders are not independent tasks. Source archetypes may be too few and too confounded by cell/platform for an identifiable posterior; this is an explicit possible abort, not a reason to multiply task counts. Defining a stable practical superiority margin remains a preregistration responsibility; the proposed sign gates are an opportunity screen, not a clinical claim.

## What would actually be needed for a core

A source-trained improvement rule would need a biologically justified invariant/constraint unavailable to generic raw-feature meta-learning, or a demonstrable budget advantage whose mechanism cannot be reproduced by the ordinary posterior/refit/search controls. It must predict *which update helps at a given solver state*, not merely reconstruct observed response. Later common-start old/new policy swaps would still be needed for C4, with solver inheritance separately controlled. None of the four inspected papers supplies that missing biological invariant. No assembly of these paper names fills it.

## Retained acquisition/extraction failures

First extraction attempt imported unavailable bs4 and failed with ModuleNotFoundError before creating text outputs. Replaced by standard-library HTMLParser. A PowerShell rg invocation passed a literal path glob and failed with OS error123; reran using rg -g. The initial multi-file context read and several long tool outputs were truncated; narrower reads supplied the relevant decisions/method sections. No HTTP acquisition failed, no failed receipt was overwritten, and no biological result exists to hide. See FAILURES.md and source receipts.
