# Control-source scout: sufficient for which future and which endpoint?

2026-10-31. Source scout and transfer development, not independent final challenge. Requested gpt-6.1-sol/high; effective serving settings not confirmed by available metadata. No fitting, synthetic execution, installation, protected-outcome access, or core edits.

The useful transfer is to define a state by its ability to distinguish **specified intervention futures and functional endpoints**, not by reconstruction of the current transcriptome. This is established control theory, not a new algorithm. It changes the admissible scientific question: whether two cultures that look the same now remain interchangeable under a declared future intervention menu. It does not establish that existing snapshot arrays can answer that question. The brief already states that exposed L1000/PRISM arrays cannot identify unmeasured longitudinal outcomes; none of these sources relaxes that boundary.

## Four selected originals and actual reading

Canonical registry: `D:/MAESTRO/reference/papers.tsv`. Its `local_path` values resolve relative to `D:/MAESTRO/reference/`. The first local search accidentally found a separate historical `_tmp_crossdomain/reference/papers.tsv` containing only a header; the resulting initial message was corrected before synthesis. The canonical library is populated. Exact absolute original paths, bytes, SHA256 and extracted-text paths are in [reuse_manifest.json](control_sources/reuse_manifest.json). Exact selected passages are preserved in [selected_passages.md](control_sources/selected_passages.md).

| Source | Original and locator read | What this reading supports |
|---|---|---|
| Singh, James & Rudary, *Predictive State Representations: A New Theory for Modeling Dynamical Systems*, UAI 2004; arXiv reissue 2012 | https://arxiv.org/pdf/1207.4167v1 ; PDF pp2–5, especially §3.2 belief update Eq2, §4 PSR Eq3/Theorem6 | Action-conditioned prediction can compress a complete observed history through a finite test basis if the system has finite linear dimension. |
| Baisero & Amato, *Reconciling Rewards with Predictive State Representations*, 2021 | https://arxiv.org/pdf/2106.03926v1 ; PDF pp2–5, §3 Proposition1/Theorem1 and §4 Eqs7–11 | Observation-predictive sufficiency need not preserve rewards, even with a nonlinear reward decoder. R-PSR adds future reward expectations to its basis. |
| Grimm et al., *Proper Value Equivalence*, NeurIPS 2021 | https://arxiv.org/pdf/2106.10316v2 ; PDF pp2–4, §3 Definition1, Propositions3–4 | A model can discard dynamics irrelevant to a specified policy set. Optimal-planning guarantee needs the sufficiently broad policy class in the theorem. |
| Sobanbabu et al., *Sampling-Based System Identification with Active Exploration for Legged Robot Sim2Real Learning*, SPI-Active, 2025 preprint | https://arxiv.org/html/2505.14266v1 ; §§3–4/Algorithm1, §7 and Appendix A.5 | Optimize executable command sequences for local parameter excitation, collect real trajectories, then refit. Useful prediction need not recover true physical parameters. |

These are method passages, not title/abstract-only reads. Appendix proofs were not fully audited; no source experiment was reproduced. SPI-Active's official abstract/history was refreshed successfully on 2026-10-31: submission v1 dated 20 May 2025. Its saved HTML was reused for methods. This is a verified real 2025 update, **not comprehensive 2025–2026 coverage** or a claim about the latest method. One HTTP request, no failure/redirect, 42,852 downloaded bytes; see [http_receipts.json](control_sources/http_receipts.json). No broad live discovery query was made. The previously saved TEB 2026 text was incidentally inspected while locating originals; its §§3.1–3.3 already couples task representation and exploration, so broad coupling novelty is unsupported. It is not a fifth selected transfer mechanism or a new online reading claim.

Exposure: before selecting these originals, I read an earlier `control_scout.md` to locate source lineage. Thus this scout is independent of the coordinator's current synthesis, but not blind to project history. No current preferred candidate draft or protected response was read.

## 1. Belief and predictive state: compress history, do not reconstruct missing history

The PSR source gives the ordinary belief update for a known POMDP:

`b(h a o)^T = b(h)^T T_a O_ao / [b(h)^T T_a O_ao 1]`.

This maintains uncertainty over latent states after the **available** action-observation history. Unrecorded treatment history can remain uncertain under a prior; the update does not reveal its actual realization.

PSR instead defines `D[h,q] = P(o_q | h, actions a_q imposed)`. If the complete system-dynamics matrix has rank `k`, take `k` independent test columns `Q`, set `z(h)=P(Q|h)`, and obtain

`P(q|h) = z(h)^T m_q`,

`z(h a o)^T = z(h)^T M_ao / [z(h)^T m_ao]`.

Theorem6 states equivalence between linear PSRs with `k` core tests and systems of linear dimension `k`. It is a representational statement about the complete controlled process, not a finite-data guarantee that arbitrary transcriptome embeddings have learned that state. Finite observation/action sets, appropriate stationary controlled-process specification, finite rank, valid/nonzero conditioning histories, and access or estimation of discriminating tests carry the derivation. Learning also needs support for relevant histories/actions. Observational treatment assignment under confounding does not automatically estimate imposed-action probabilities.

**Mapping.** History `h` becomes culture identity/branch ancestry plus recorded exposures, doses, durations, washout and measurements. A test `q` becomes an executable future treatment sequence and specified readout event. The state summarizes predicted future assay responses, not a claimed molecular identity. Dose, timing, residual compound, growth/death and assay calendar must enter the state/action definition when they change the future. A finite low-rank biological representation remains an empirical hypothesis.

**Decisive failure case.** If every measured future assay under every supported intervention has the same law for two preparations, their latent difference is observationally unavailable in that menu. A larger encoder, latent-state label or agent cannot recover it. Expand the intervention/readout menu only if an actual additional experiment exists. If two preparations merely have similar *current* RNA but differ on an actually measured future response, then current RNA is insufficient and history or an additional probe may help. These two cases must not be conflated.

## 2. R-PSR: an RNA-predictive state can still be wrong for drug selection

R-PSR §3 Proposition1 says a reward function of the observation-predictive state need not exist, even nonlinear. In its finite-POMDP notation `z(h)^T=b(h)^T U`, an exact linear reward decoder exists iff every column of the reward matrix lies in `col(U)`:

`R = U W`; equivalently `R_hat = U U^+ R = R`.

The ordinary least-squares projection `U^+R` can therefore lose a reward distinction that observations never preserve. The paper's load/unload counterexample merges states equivalent in observations but different in rewards, reversing the optimal behavior. This is a sharper warning than low transcriptome reconstruction accuracy.

R-PSR extends a future test `q` with a final endpoint action `a`, using intents

`r(q a | h) = P(q | h) E[R | h q, a]`.

Its token action `ζ` has reward one, so `r(q ζ|h)=P(q|h)` and `r(ε a|h)=E[R|h,a]`. The token is mathematical bookkeeping, not a physical experiment. A core basis of these expectations represents both observations and rewards for finite POMDPs. This does **not** manufacture missing endpoint labels or identify a clinical/causal mechanism.

**Mapping and change.** Preserve functional readouts, such as a declared viability, secretion or phenotype endpoint, in the predictive targets. Do not pretrain solely on RNA futures and then assume a small endpoint head can recover every lost distinction. Endpoint-specific sufficiency is relative to the action set, horizon and population; changing any of these requires a new check. An endpoint observed in an unrelated line, assay or time does not become a matched intent label through naming alone.

**Comparator and falsification.** Compare RNA-only state plus endpoint head, history plus action covariates with an ordinary endpoint predictor, and a reward-inclusive predictive basis using exactly the same admissible matched outcomes and capacity budget. If adding reward-inclusive state does not improve held-out *functional* predictions/rankings beyond the simple history predictor, no special representation benefit is shown. If two RNA-equivalent preparations differ in function and the state still merges them, its claimed functional sufficiency is falsified. No endpoint labels means park this test.

## 3. Proper value equivalence: preserve a declared decision problem, not all biology

With `T_pi v = E[r + γ v(s')]`, ordinary VE requires agreement on Bellman updates for specified policies/functions. PVE §3 Definition1 instead admits

`M_inf(Pi) = {m_tilde : V_tilde^pi = V^pi for every pi in Pi}`.

Distinct models may be in this class while assigning arbitrary dynamics to features irrelevant to those values. Proposition4 establishes optimal planning when equivalence covers the paper's full policy space; a few behavior-policy returns do not justify that conclusion for new policies. A finite list of known compound rankings is still a much weaker requirement than preservation of all intervention programs.

**Mapping.** Fix the endpoint, cost, horizon and executable intervention menu before asking which molecular detail may be discarded. This offers an explicit *lossy target*: a useful drug selector may be scientifically valuable without being a faithful whole-cell simulator. It does not identify which discarded biological variables are intrinsically unimportant outside this task.

**Comparator and falsification.** A direct history/action-to-functional-value predictor or ranking model is the simplest strong comparator; use the same labels and candidate menu. If one-step selection is the task, a recurrent world model is not automatically necessary. Test on held-out programs and independent cultures, then deliberately change endpoint or horizon as a scope stress test. Value preservation failing within the frozen task falsifies sufficiency; failure after changing the task narrows transportability. Predictive success alone cannot validate mechanistic claims.

## 4. SPI-Active 2025: change excitation before changing model size

SPI §3 fits a structured simulator to actual state-action clips by multi-step rollout error plus a parameter penalty:

`J(theta) = sum_k sum_t ||x_real[t+1,k] - x_sim[t+1,k;theta]||^2_W + ||theta-theta0||^2_Wtheta`.

§4 first obtains `theta1`, then chooses feasible commands for an existing multi-behavior controller by minimizing `tr(F(theta1,c)^(-1))`; it executes those commands on the real robot and refits. With the paper's Gaussian-noise/local-model approximation, in conventional Jacobian orientation

`F(theta,c) ≈ σ^-2 E sum_t J_t^T J_t`, where `J_t = ∂f(x_t,u_t;theta)/∂theta`.

Reducing a Cramér–Rao lower bound is a design rationale; it does not itself prove an estimator attains it. The source requires observed state-action trajectories, a parameterized simulator, repeated feasible real execution, approximately appropriate noise/model assumptions and an existing behavioral policy. It is offline; §7 says active excitation was limited to quadrupeds, not demonstrated on humanoids. It does not solve arbitrary partial observation.

Crucial negative evidence: Appendix A.5 reports an actual 4.7 kg added load but only about 2.44 kg fitted mass increase, with unexpectedly inflated roll/pitch inertias. The authors explicitly discuss insufficient excitation, parameter coupling and possible overfitting despite improved prediction/transfer. Thus identifying a decision-useful model is not identifying true physical parameters. The same distinction is mandatory for pathway/mechanism claims in virtual cells.

**Mapping.** Replace robot commands by a genuinely executable dose/time/washout/probe menu, trajectories by matched measured assay sequences, and uncertain physical parameters by a narrowly declared response family. Select experiments that separate response alternatives under that actual observation model. If only destructive cross-sectional samples exist, derive information from their marginal/branch likelihood; do not insert unobserved cell trajectories into `J_t`. Global parameter-information gain need not improve the functional decision.

**Comparator and falsification.** Equal-cost random/coverage selection and direct uncertainty or expected-decision-benefit selection, all using the same updater and experiment menu. First compare selectors at fixed predictor, then predictors at fixed selected measurements; otherwise more informative real labels are confounded with architecture. Higher Fisher score without better held-out endpoint prediction/calibration or decision utility rejects the acquisition rationale. Failure under plausible model misspecification is a reason to restrict or stop, not add a mechanistic interpretation.

## Smallest useful biological admission test, not executed

Before implementation, locate one real resource with the same preparation/history, at least two recorded pretreatments, a common future probe/intervention, and an independent matched functional endpoint. Destructive assays need valid sister-culture/branch provenance and an explicit population estimand; measured cells cannot be reused as living future subjects. Split independent cultures, donors/lines and treatment programs as required; individual cells from one culture are not independent held-out programs.

Freeze the future menu and endpoint. Ask whether known pretreatment/time/dose covariates improve prediction beyond current-RNA-plus-action under the same label budget. Use a simple history/action endpoint model before a PSR or recurrent model. Only after a reproducible history-dependent difference remains should one ask whether a compact reward-inclusive predictive basis preserves that difference on unseen histories/programs. Require both calibrated endpoint prediction and independent decision benefit, and record uncertainty/negative results. No such matched resource has been admitted by this scout, so this is a conditional research direction, not an authorized run or evidence of biological benefit.

The source-supported decision change is an admission rule: **a proposed state must specify the futures and endpoints it is sufficient for, and be tested on actual matched outcomes that distinguish its alternatives**. There is no supported novelty claim for predictive history states, reward-inclusive predictive states, task-oriented compression, or representation/exploration coupling. Any biological contribution would have to come from an experimentally grounded new interchangeability question or newly supported decision capability, plus target-field prior checks owned by the coordinator.
