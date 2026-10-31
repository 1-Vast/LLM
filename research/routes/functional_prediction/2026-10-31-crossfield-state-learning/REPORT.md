# Cross-field solutions for virtual-cell state learning

2026-10-31 (Asia/Shanghai). Targeted follow-up to the task-sufficient transfer MVP. Sources were actually read at selected-method-passage level; none of their results was reproduced. This report answers which established principles can change the research design. It does not certify an algorithmic novelty or admit a biological dataset.

## Main judgment

Other fields have mature answers to several mathematical parts of the problem: predictive states for partial observation, reward/value equivalence for task sufficiency, decision-focused learning for prediction-to-choice mismatch, active system identification for informative experiments, and causal transport for sharing conditional effects. They do not recover unmeasured intervention outcomes without assumptions or experiments.

Two productive changes follow. First, stop treating compactness and next-expression prediction as the central scientific advance; target the information needed to distinguish future functional choices. Second, distinguish a near-term decision-training baseline from a deeper biological claim about a history-dependent susceptibility state. The former can be studied on the exposed static data under a new exploratory protocol. The latter needs matched early measurements and next-action outcomes, but need not reconstruct the entire cell or demand individual-cell longitudinal observations.

The most consequential alternative is **action-contrast sufficiency**: a measured state may preserve which of two next treatments is better across histories even when absolute viability differs. This is weaker and more relevant to a fixed drug choice than full outcome-distribution equivalence. Its general statistical principle is established. A contribution would have to establish a nontrivial, experimentally delimited biological response relation, useful transfer and uncertainty boundaries beyond strong existing functional-profiling and response-panel methods.

## What each donor field solves

| Current issue | Established solution | Usable rule | Boundary |
|---|---|---|---|
| Current RNA/count misses treatment history | POMDP belief state; predictive-state representations (PSR) | Summarize recorded history by probabilities of specified future action/readout tests | Finite-rank/support and a correct observation process; no recovery of unrecorded history by naming a latent state |
| Molecular prediction is good but functional decision is wrong | Reward-inclusive PSR; proper value equivalence (PVE) | Include functional endpoints/values in the state targets | Preserving observations need not preserve rewards; a finite policy/action panel does not support arbitrary new drugs |
| PCA loses useful low-variance directions | VIB, supervised reduced rank/PLS, task-oriented latent prediction | Optimize outcome-relevant compression instead of variance explained | Joint labels and action support required; smaller vector alone does not reduce assay cost |
| Correlation improves while drug choice does not | Smart Predict, then Optimize (SPO) | Penalize the true cost of decisions induced by predictions | Established training principle; can help under finite-sample/model misspecification, not guaranteed benefit or new cell biology |
| Too many experiments, too little discriminating information | Active system identification; optimal experiment design | Choose feasible perturbations where competing models predict different measured results | Requires executable actions and real feedback; information gain may not lower decision regret |
| Two sources/histories have different endpoint baselines | Causal treatment-effect/transport theory | Test a common next-action contrast on overlapping early states | Assignment, overlap, eligibility and measurement semantics matter; no support means no identified contrast |
| Adding an organoid/Agent seems tempting | Compositional models and dual-control-style measurement policies | First identify an interaction or measurement that changes a held-out decision | Planning does not supply missing cell-cell/ECM/exposure biology |

## 1. A state can be defined by future tests

PSR represents a controlled history h by predictions of a set of core tests Q:

`z(h) = P(Q | h, imposed future actions)`.

Under the finite-linear-dimension assumptions in the original, other test probabilities can be read from this basis and updated recursively. The important transfer is operational: define a state by what it can predict after interventions, not by a coordinate system over the current measurement. This is old theory and cannot be claimed as MAESTRO's invention.

R-PSR sharpens the point. A state sufficient for predicting all observations can still fail to predict rewards. In its finite-POMDP formulation, a reward decoder needs the reward matrix to lie in the observation-test span. Adding a head cannot recover distinctions already discarded. A cellular analogy is a state that predicts RNA yet merges reversible arrest and durable loss of function. That analogy is a proposed scientific contrast, not an observed MAESTRO finding. Future death, recovery or secretion must enter the target family when those drive the decision.

PSR tests are conditional future predictions, not necessarily a set of harmless assays that can be executed on the very same cell. A destructive probe panel requires sibling cultures and a preparation/population estimand. The panel can alter its specimen; it must not be treated as passive sensing of an untouched future specimen.

Sources: Singh et al., UAI 2004, [arXiv:1207.4167](https://arxiv.org/abs/1207.4167), §§3.2-4; Baisero & Amato 2021, [arXiv:2106.03926](https://arxiv.org/abs/2106.03926), §3 Theorem1 and §4. Exact passages and original hashes: [control_sources.md](control_sources.md).

## 2. Preserve the decision, but declare which decision

MuZero is a concrete example of learning action-conditioned latent updates through reward/value/policy targets without requiring observation reconstruction. PVE formalizes incomplete models that preserve policy values. Its optimal-planning result depends on a sufficiently rich policy set; preserving returns of observed policies does not guarantee preservation of an excluded optimal policy. A drug never represented in training is not simply a new reward over unchanged dynamics.

VIB trades target information against retained input information, implemented by target likelihood plus an encoder KL penalty. A useful static biological form is `NLL(Y | z,A) + beta KL(q(z|X),p(z))`, where X is available before the claimed decision and A is the treatment descriptor. This is a conditional adaptation of a standard method, not an innovative cell mechanism. PLS and supervised reduced-rank regression should precede a stochastic nonlinear bottleneck.

TD-JEPA (2025 preprint; existing archive's ICLR 2026 status was not re-established here) predicts policy-conditioned successor features using actual one-step `(s,a,s')` transitions and a TD target. Reward-free does not mean transition-free. Its new-reward transfer does not establish unseen-drug or new-cell-dynamics transfer. Do not turn destructive unpaired cell snapshots or two unrelated assays into invented transitions.

Dreamer provides contrary evidence to a blanket task-only prescription. Its 2025 Nature original combines recurrent history, stochastic state, action dynamics, reconstruction and reward prediction. The Fig.6 ablation says performance rests predominantly on the unsupervised reconstruction signal in that setting. Thus keep reconstruction-versus-task supervision as a fair ablation; removing a decoder is neither universally better nor novel.

A deterministic compact map z=f(H) cannot contain information absent from H or outperform a Bayes-optimal full-H predictor by adding information. Practical benefits must come from finite-sample regularization, a valid inductive restriction, measurement cost, or computational constraints. An apparent win over a weak full-input baseline does not establish a new sufficient state.

Sources: [VIB](https://arxiv.org/abs/1612.00410), [MuZero](https://arxiv.org/abs/1911.08265), [PVE](https://arxiv.org/abs/2106.10316), [TD-JEPA](https://arxiv.org/abs/2510.00739); selected methods in [representation_sources.md](representation_sources.md). Hafner et al., Nature 2025, [10.1038/s41586-025-08744-2](https://doi.org/10.1038/s41586-025-08744-2), original World model/Critic learning/Fig.6 passages read; [root_notes.md](root_notes.md).

## 3. Train for the cost of selecting the wrong treatment

SPO measures the true cost of the decision induced by predicted parameters relative to the decision using true parameters. In a fixed drug menu, let a_hat minimize predicted endpoint loss; regret is `Y(a_hat)-min_a Y(a)` when lower is better. For a top-k selection, replace the singleton by the feasible set of k actions. This directly addresses the current correlation/selection disconnect.

Do not infer that decision loss always wins. If gaps between actions are tiny, a ranking error can be inconsequential; if the assay is noisy, optimizing the observed oracle can overfit measurement noise. Use replicate-aware endpoints, a frozen decision menu/orientation, headroom-aware practical margin and nested fit-only tuning. Preserve magnitude calibration so the model cannot improve ranking by distorting overall toxicity or efficacy. The specific SPO+ consistency result read here assumes continuous conditional cost distributions symmetric about their means, and the stated linear objective/feasible-set setting; it is not an arbitrary biological guarantee.

This is the most accessible next comparator on existing exposed data, but it is an ordinary predictive-utility study. Do not call it a dynamic Virtual Cell or claim clinical therapeutic benefit from selecting the most growth-inhibited cell line.

Source: Elmachtoub & Grigas, *Smart Predict, then Optimize*, Management Science 2022, [10.1287/mnsc.2020.3922](https://doi.org/10.1287/mnsc.2020.3922); actual inspected arXiv v5 (2020), [1710.08005](https://arxiv.org/abs/1710.08005), pp1-5. Original and Crossref receipts saved.

## 4. The deeper direction: use a challenge to expose hidden susceptibility

Active system identification changes the experiment when multiple models fit passive observations. SPI-Active (2025) selects executable robot commands using a local Fisher-information criterion, measures real trajectories, and refits. Its own appendix reports parameter compensation: fitted load and inertias need not equal true physical parameters despite better prediction. The biological lesson is to distinguish useful functional state from identified mechanism.

Candidate v1 uses a small standardized diagnostic perturbation panel as a state observation operator. A probe is worthwhile when it distinguishes otherwise aliased histories in a way that predicts a later therapeutic decision. Use the same action/readout and observed experimental budget for all models. Compare with ordinary response-panel ridge/covariance, history/count/exposure predictors, and fixed/random probe selection. Any acquisition advantage must be separated from an encoder advantage.

The main biological novelty objection is substantial: dynamic BH3 profiling already measures induced apoptotic priming with functional probes, predicts later death and motivates subsequent therapy. The 2025 ALK study explicitly relates 16 h DBP to 96 h death; its assay is destructive. It also reports a timed addition after 24 h lorlatinib in one experiment. Other captions called sequential do not specify delay/washout and must not be completed by inference. Thus early functional probes or probe-guided next therapy are already occupied concepts. Rhaister and related response-panel reconstruction also block a broad claim that a measured drug panel defines cell state.

The remaining research object is whether a defined response relation **closes across histories and transports to a reserved chemistry/preparation range**, and whether its violation reveals a specific missing, measurable component. This is a conditional scientific question with no demonstrated method novelty yet.

Sources: [SPI-Active](https://arxiv.org/abs/2505.14266), §§3-4/Alg1/Appendix A.5; [ALK functional-profiling study](https://doi.org/10.1038/s41419-025-07513-3), selected original results/methods; exact timing qualifications in [causal_sources.md](causal_sources.md).

## 5. A less demanding, decision-relevant claim: transport the action contrast

Let H be prior treatment history, S a measured state available before the next action A, and Y a later functional loss. Consider two allowed next actions and define

`tau(s,h) = E[Y(1)-Y(0) | S=s,H=h]`.

The proposed restriction is `tau(s,h)=tau(s)` on overlapping state support. History may shift both action outcomes equally: `E[Y(a)|S,H]=b(S,H)+g_a(S)`. Then absolute-response sufficiency fails, but `g_1(S)-g_0(S)` preserves the next-action comparison. This is a constructive algebraic possibility, not a new theorem or evidence it holds in cells. Risk-sensitive or threshold-based decisions may need more than a mean contrast; combination toxicity and absolute safety constraints must remain separate.

A state measured after H can be pre-treatment for A. Randomizing A after S can identify conditional next-action effects among the eligible surviving population; it does not identify the total effect of H on the original population. With destructive assays, random/exchangeable siblings are needed and precision is at the independent-preparation level. Ordinary longitudinal observational data instead need consistency, sequential exchangeability, positivity and a declared selection/censoring estimand. Adversarial balance or an embedding does not repair hidden confounding or zero action support.

A minimal design skeleton is two prior histories × two randomized next actions, with independent preparation repeats and early-state overlap. This is not a sample-size prescription. Freeze endpoints, exposure/carryover, dose/time, labels and equivalence margin using source-side assay precision and decision headroom. Test the history-by-action contrast at overlapping states; non-significance is not equivalence. Compare S-only with S-plus-known-history models and simple kinetic/count/exposure or functional-probe alternatives. Then evaluate a frozen law on a held history/preparation and, where supported, a held chemical family. If states do not overlap, history removal cannot be tested from that design.

The fresh [independent challenge](CHALLENGE.md) retains this as a bounded biological question and rejects methodological novelty. It adds three necessary restrictions: two histories can test their contrast but do not establish broad unseen-history transfer; use disjoint preparation blocks or a declared joint analysis rather than using target outcomes first for equivalence admission and again as independent confirmation; and use source-defined coarse state strata or a small justified contrast model in a small sample, since exact conditioning on a learned noisy continuous state is not estimable there. A collapsing encoder cannot manufacture valid state overlap. A held-out pretreatment chemotype with supported future actions is also different from holding out the future-action chemotype itself.

Transport theory further requires one relation across interventions, not separate per-drug calibrations fit using target test labels. The 2026 TraCA preprint makes this exact distinction: independent stochastic alignment kernels may be trivial, whereas a common kernel across interventions is the substantive constraint. Its graph/shift assumptions are not supplied by matching embeddings.

Sources: Bica et al., CRN, [arXiv:2002.04083](https://arxiv.org/abs/2002.04083), §3 and Appendix B; Pearl & Bareinboim [R-372](https://ftp.cs.ucla.edu/pub/stat_ser/r372.pdf), pp4-5,8-11; *Generalised Transportability via Causal Abstractions* (2026 preprint), [arXiv:2608.15645](https://arxiv.org/abs/2608.15645), §3.1-3.2 and §11. Exact readings and boundaries: [causal_sources.md](causal_sources.md).

## Priority and stop decisions

Priority updated after the separate [static decision baseline](../2026-10-31-decision-focused-selection-mvp/REPORT.md). Its top-10-membership ridge has saved-run active overlap .18684 and regret 1.12913, below raw-k20 .21203/.99476 and ordinary ridge .19857/1.03248. The original verifier remains FAIL, supplemental clarified saved-prediction arithmetic is PASS, and science remains INCONCLUSIVE. This parks that surrogate under its static input contract; it does not refute direct-regret/SPO training or all decision-focused learning. This is a subsequent run, not a result of the literature-reading round described below.

1. **Biological priority:** reuse existing functional-resource audits to locate authenticated history x supported subsequent-action endpoints. Before requiring a probe state, establish whether histories generate a consequential action-contrast change or preference reversal, with uncertainty and independent preparations. Existing static tables remain useful for static tasks but cannot certify the sequential relation.
2. **Core conditional question:** test whether inexpensive baseline growth/viability, and probes only if needed, preserve the next-action contrast across overlapping histories. Freeze a supported A/B menu first. Full outcome-distribution equivalence, rich omics, universal scaffold/MOA holdouts and a particular probe count are not entry requirements for this bounded claim.
3. **Independent transport:** freeze the relation and costs before independent preparation/history outcomes. Holdout of preparation chemistry is distinct from holdout of future-action chemistry. The latter needs separate descriptors/support and testing. Report magnitude equivalence, preference/sign and absolute safety separately.
4. **Engineering in parallel:** preserve and repair the earlier replay's noncomparable transforms/metrics in its own versioned work item. It cannot be interpreted as biological failure and need not block resource metadata qualification. No corrected numerical replay was executed in this update.
5. **Conditional organoid/Agent:** after independently established scientific and decision value, compare additive cell mixtures with a minimal interaction model and measured interaction interventions. Only then compare an Agent's discriminating measurement choices with deterministic VOI/POMDP, BO/active learning and fixed designs under equal costs.

A validated informative probe or bounded biological transfer law can remain valuable even if an ordinary ridge reads it as well as a complex encoder; that outcome removes a special representation claim, not automatically the measurement contribution. DBP and ordinary response-panel prediction remain close priors. Park the biological novelty claim when those existing methods already supply the same capability under matching conditions, or when overlap/precision/transport fails. The maintained [next-round design](../2026-10-31-task_sufficient_transfer_mvp_20261101/NEXT_ROUND_DESIGN.md) is the current operational route. No biological relation or eligible resource was established by this update.

## Correction to the previous all-arm replay interpretation

Static inspection of the frozen runner and independent runner confirms different algorithms, not just unexplained numerical disagreement:

- Main GAT: per-option reference covariance top-five removal. Replay: a single flattened PCA over all options.
- Main PCA/random/full-flat: transformed GAT residual. Replay: centered raw signature.
- Main hit metric: overlap of predicted and true most-sensitive residual top-10% sets. Replay: selects the opposite residual sign and counts raw LFC threshold hits. Regret shares the reversed choice direction.
- Main zero fingerprints: missing similarities. Replay: zero-similarity fallback neighbors.

These differences explain why equal raw/ridge predictions coexist with unequal decision metrics. No corrected numerical replay was executed here; all-arm verification remains unresolved. The earlier all-arm mismatch verdict is preserved, while its attribution solely to protocol underspecification is superseded. This finding does not invalidate the separate GAT 139-check study. See [root_notes.md](root_notes.md) and original `mvp_run.py` / `VERIFY_FULL_61/replay_full.py` in the previous episode.

## Coverage, budget and verification limits

Three real source scouts requested gpt-6.1-sol/high worked from the neutral brief before candidate v1; a fresh challenger received the frozen candidate before the persuasive synthesis. The coordinator verified primary passages and synthesized. Effective model settings, token use and monetary cost are unavailable. Shared requested model and common literature do not provide independent biological replication.

This is one local/source reconnaissance plus a directed recent-source refresh and final challenge, within the declared 36-request/100MiB ceiling. Canonical originals and source hashes were reused. New acquisition was limited to primary documents and identity/date checks; no native web search tool was exposed and no exhaustive 2025-2026 search was done. Some earlier registry venue claims were not newly verified and are not needed here. References include older foundations because they establish the solving principles; recent materials include SPI-Active 2025, Dreamer Nature 2025, TD-JEPA 2025, dynamic BH3 2025 and TraCA 2026 preprint. Peer review, selected source reading, software replay and biological validation are distinct.

No protected outcome arrays, model training, paid API, dependency install, wet experiment, Agent implementation or `src/`/`tools/` promotion occurred in this round. Independent challenge and final receipt totals are recorded below after return. Original sources and failed local extraction attempts are retained in the episode.

Independent review is complete in [CHALLENGE.md](CHALLENGE.md): no established method novelty; retain a conditional history-sensitive measurement/contrast-transfer question, with DBP and ordinary response-panel prediction as strong closest rivals. The review also confirms the key static transform differences. Its suggested larger feasibility design is a proposal, not a powered experiment or a qualified resource. Requested roles were control, representation and causal scouts plus one fresh challenger, all gpt-6.1-sol/high; effective serving metadata is unavailable. Actual receipt totals and source/relative-link checks for the earlier report version are in `verification.json`; its report hash does not certify this subsequent priority update. Current document hashes and scoped checks are recorded in [PRIORITY_UPDATE_VERIFICATION.json](../2026-10-31-task_sufficient_transfer_mvp_20261101/PRIORITY_UPDATE_VERIFICATION.json). There was no scientific fitting or numerical replay in this follow-up.
