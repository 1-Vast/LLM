# Independent opposing review: frontier mechanisms for virtual-cell RSI

Date: 2026-10-22. Author: native subagent frontier_opponent. This is the initial independent opinion, written before reading INDEPENDENT_PRIMARY.md, its seal contents, or any other current peer opinion. Directory listings revealed their existence only. I read the frozen-task protocol and authenticated primary source extracts. I performed no biological fit, read no numerical CiPA outcomes, and opened no later-site arrays.

## Decision

None of the four eligible papers establishes a new virtual-cell/drug-discovery mechanism by transfer alone. V-JEPA 2 supplies a useful separation between observational representation learning and action-conditioned dynamics; SEAL supplies a concrete reason to revalue an update against the current solver; DGM supplies an operational distinction between inheriting a solution and inheriting an improvement procedure. PhysiCalWorld supplies a concrete method of amortizing within-environment calibration from informative context. These are defensible mechanisms in their source domains. They are not evidence of usefulness, innovation, synergy, or RSI in CiPA.

The strongest minimal next question is whether the usefulness of the same paid feedback/update changes predictably with the solver and whether recomputing that value helps out of sample. This can be posed without an LLM, a neural world model, synthetic cellular labels, or a code-evolution framework. It is still ordinary solver-aware meta-learning/experimental design unless a further mechanism and comparator distinguish it. No new biological run should be initiated on this review alone; the frozen ordinary calibration probe must retain its protocol and interpretation.

## Source authentication and date eligibility

All ten cached arXiv response bodies (abstract and versioned HTML for each candidate) were checked against the corresponding receipt SHA256; all matched, and receipts record HTTP 200 and the expected arxiv.org URL. This validates the cached bytes against acquisition receipts; it does not independently prove every scientific claim. Abstract submission histories and v1 HTML, rather than search snippets, support the following judgments:

| Paper | First submission | Eligible in strict 2025–2026 window | Primary source used |
|---|---|---|---|
| V-JEPA 2 | 2025-06-11 | Yes | https://arxiv.org/html/2506.09985v1, sections 3.1–3.2 and 4 |
| Self-Adapting Language Models / SEAL | 2025-06-12 | Yes | https://arxiv.org/html/2506.10943v1, sections 3.1–3.2 and 4.1 |
| Darwin Gödel Machine / DGM | 2025-05-29 | Yes | https://arxiv.org/html/2505.22954v1, sections 3–6 and appendix A.2–A.4 |
| PhysiCalWorld | 2026-10-21 17:57:59 UTC | Yes | https://arxiv.org/html/2610.30125v1, sections 3.1–3.3, 4, 5 and appendices A.2/B |
| Titans | 2024-12-31 22:32:03 UTC | No | https://arxiv.org/abs/2501.00663, submission history |

Titans is excluded despite its 2501 identifier and the local calendar crossing to 2025 in some time zones. The declared eligibility uses the original UTC submission date. PhysiCalWorld is a genuine 2026-origin candidate; DGM's later revision does not make its mechanism a 2026 invention. This is an audit of supplied candidates, not an exhaustive frontier survey. The parent supplied only the newly authenticated PhysiCalWorld source pointer during independent preparation; no peer analysis of it was consulted.

## PhysiCalWorld: closer to the calibration task, with an unproven group assumption

Sections 3.1–3.3 encode an exploratory observation/action clip into one descriptor token and condition a world predictor on it. Joint training uses next-latent prediction error without supervised physical-parameter labels. Crucially, section 3.2 requires groups of episodes sharing the same underlying physical configuration. Appendix A.2 samples context from a different episode than the target prediction segment, avoiding target-future leakage. The descriptor is computed once and reused only while scene dynamics remain unchanged. The experiments cover four simulation environments; “no simulator required” refers to the learning formulation, not proof of an experiment conducted without simulated data.

The contact requirement matters more than the token architecture. Section 3.3 says prompts without contact/motion cannot reveal dynamics. Push-T uses a trained task-directed PPO collection policy because random actions do not reliably produce meaningful contact (appendix B.1), while other environments use random controls. Therefore the paper does not establish that arbitrary random controls or arbitrary convenient control drugs reveal the hidden aspects relevant to all target conditions. The limitations explicitly identify grouped-data availability, prompt quality and stationary physics as assumptions. Active informative prompt selection is future work, not an already demonstrated contribution to import.

The attractive static analogy is z_site = g(paid control responses), prediction = f(drug, dose, metadata, z_site), training context and targets on disjoint conditions of the same source group. This is a coherent hypothesis for functional laboratory calibration. At this level it is also a conditional neural process, amortized system identification, or hierarchical conditional prediction. A token alone provides no novel statistical mechanism. With the current three-head summary, the ordinary multivariate affine correction may already provide an effective low-dimensional context descriptor. A more elaborate encoder must beat that comparator and direct predictors receiving the same measured controls; it cannot win merely by monopolizing context.

Physical site identity is observed, but equality of a hidden response-generating configuration across all its exported conditions is not. Sites may differ in cell type, platform and unrecorded batch/run factors. The protocol has no well/run identifiers. Grouping by site is the valid split unit for withholding; it is not proof that all rows at that site share a stationary latent physiological mechanism. Contextual groups may be (site, cell type, platform), with all groups from a site withheld together; this still does not establish shared batch or transferable control response. The descriptor must therefore be called a functional calibration summary unless separate evidence supports physical interpretation.

There are five source physical sites, not hundreds of independent configurations. Push-T and Reacher each report 135 training configurations; repeated bundles within five sites do not supply the same cross-environment learning signal. A metadata eligibility check should first enumerate independent physical groups and whether each has disjoint, sufficiently informative controls and target conditions. If a stronger model requires redefining train/evaluation groups, obtaining additional outcomes, or treating each drug as a new physical environment, it changes the task and needs a new protocol. Existing site6/7 development information, once used for designing this descriptor, cannot be counted again as independent confirmation.

A minimal future comparison, if justified by the fixed ordinary probe, would keep a small fixed control set and compare the simplest source-trained conditional summary against offset/affine/multivariate calibration, mixed effects or kernel/context regression, and a small conditional neural-process baseline. An incorrect-context swap and a metadata-only descriptor can test whether correct within-group responses matter. They do not prove recovery of physical parameters. A beneficial descriptor would establish cross-condition contextual calibration; it would establish neither biological dynamics, agent improvement, nor inheritance.

## V-JEPA 2: valid operational lesson, invalid static-trajectory shortcut

The source explicitly says observational pretraining does not directly account for the causal effect of actions. It freezes the encoder and fits a separate predictor on temporally aligned robot frames and end-effector state signals. Actions are changes between adjacent end-effector states; the predictor uses teacher-forcing and a two-step rollout loss. At planning time, it minimizes latent distance to a goal image with the cross-entropy method and executes only the first action before observing and replanning. These details are visible in vjepa2_html_v1.txt around lines 355–409. “Unlabeled” means no extra task/reward/success annotation; it does not mean absence of action/state measurements.

Minimal transferable operation: learn a compact representation on abundant observations; then learn action-conditioned transitions from actual interventions; optimize sequences using predicted task-relevant future outcomes; reobserve after an action. This is a concrete representation-learning implementation of model predictive control. Cross-entropy optimization and receding-horizon control are not introduced by this paper, and using these names in biology does not establish algorithmic novelty.

For the present CiPA task, drug/dose is a treatment condition on an assay bundle, whereas selecting which bundle to reveal is an information-acquisition action. These are different intervention targets. Unordered single-dose bundles are not a biological trajectory. Ordering doses numerically, ordering laboratory IDs, or ordering acquired feedback does not create transitions of a continuing cell. Site 10's sequential dosing is explicitly excluded and cannot be added to rescue the analogy. There is no authenticated within-unit state trajectory or action history in the allowed task.

One can legitimately model transitions of the investigator's belief/solver after each query, using a static oracle. But the transition then describes learning, not cellular dynamics, and the appropriate comparators are Bayesian experimental design, active learning, value of information and belief-state/POMDP methods. Such a recasting cannot claim that the data support action-conditioned cellular rollouts. If a future genuinely dynamic asset is acquired, eligibility must establish action timing and dose, linked states, sampling windows, independent unit identity, censoring/measurement semantics, support for compared actions, and a meaningful terminal biological target before selecting a representation architecture.

A latent metric also needs task validation. A small latent distance to a nominal healthy state is not by itself equivalent to efficacy, cardiac safety, or an actionable dose schedule. A representation can discard a rare but decisive EAD signal while giving an excellent average predictive loss. The present protocol's separate EAD, measurement, and conditional continuous endpoints should not be replaced with an unvalidated embedding distance.

## SEAL: current-solver update valuation is testable, but not novel by assertion

SEAL generates self-edits (training examples and optionally update hyperparameters), applies an inner SFT update, then trains the edit generator using the resulting downstream score. The paper explicitly calls this meta-learning. Section 3.1 states that the reward depends on current model parameters, that old (state, action, reward) triples may become stale, and that rewards therefore must be computed using the current model. Its actual policy observation is context only, even though the formal state contains model parameters. Thus “solver-conditioned valuation” is a fair operational inference; an explicit learned conditioning interface over solver identity is a proposed extension, not a demonstrated component to attribute to SEAL.

The ARC implementation uses predefined transformation/hyperparameter tools and a curated 11-training/8-evaluation-task subset selected for solvability under optimal test-time-training configurations. This is useful proof of operation, not general evidence that arbitrary biological feedback can be rewritten into effective training labels. The knowledge task derives implications from supplied text; in CiPA a missing continuous outcome or an unmeasured condition cannot be filled with generated prose and treated as a measured fact.

Minimal transferable quantity: for solver state s, allowed feedback q and allowed update u, estimate the difference between the terminal loss before and after applying u to s with that feedback. Train or recompute this quantity only on source episodes. Current-solver revaluation means recomputing this value after s changes, rather than retaining rewards assigned under its ancestor. A generated acquisition policy, an update learner, and a cell simulator are all optional and should initially be omitted.

However, several apparent discoveries collapse to conventional procedures:

1. Choosing among residual offset, affine/ridge and trees using paid controls is algorithm selection or stacking; the current protocol already includes finite-program selection.
2. Selecting query points by expected risk reduction for a specified learner is learner-aware experimental design.
3. Re-estimating query values after the learner is updated is sequential value-of-information acquisition.
4. Learning a data-weighting/update strategy across tasks is meta-learning, whether or not an LLM emits the directives.

To justify further work, demonstrate a predictable solver-by-feedback/update interaction that changes optimal choices and yields prospective decision improvement over these controls. A solver interaction is necessary for the proposed motivation, not sufficient for novelty. Crossing two solvers and two queries and finding any rank reversal after inspecting results is too weak. Predefine a scientifically meaningful interaction, its direction or predictive rule, the response scale, and comparison population. Validate decisions on untouched task/site groups; do not reuse the interaction-discovery targets as confirmation.

On only five source physical sites, nominally many drug/dose bundles are not many independent adaptation environments. Leave-site-out evaluation and cross-fitting are essential, but do not create population replication. A positive source diagnostic would justify a narrow additional falsification step, not a broad learned policy or claims of generalizable solver-aware drug discovery. At target time, the evaluator's terminal labels must remain unavailable to update valuation; SEAL's training-time access to downstream answers is not permission to use target evaluation labels as adaptation reward.

## DGM: inheritance of a better predictor is not inheritance of a better improver

DGM modifies an agent's Python code, evaluates the child, and retains a branching archive. A selected parent implements a proposed modification using its own code-editing capabilities. Appendix A.3 also describes an external foundation model diagnosing evaluation logs and proposing the next feature. Therefore, DGM does not show that every component of the improvement process self-improves or that its foundation model weights evolve. The paper's limits section explicitly leaves weight-training changes to future work and acknowledges the assumption that coding benchmark skill reflects capacity for self-improvement.

The directly relevant ablation is DGM without self-improvement: the initial meta-agent repeatedly produces new agents. This tests whether improvements to the generating agent contribute beyond repeated fixed-generator search. The no-archive ablation separately tests branching exploration. Neither “archive exists” nor “children inherit code” is sufficient evidence for recursive improvement.

The domain-transfer difficulty is sharp. Improving CiPA prediction need not improve the ability to invent a better calibrator or acquisition rule. Coding competence is directly reused for code modification in DGM; electrophysiological prediction skill is not automatically reused for algorithm generation. Saving a better predictor to the next generation, retuning its regularizer, or retrieving a successful previous program could improve task score without improving the improvement operator.

Minimal credible recursive hypothesis: an inherited operator generates more useful future solver modifications on fresh tasks than a frozen ancestor operator, with the same parent solver, information, candidate-evaluation budget and resource allowance. This requires counterfactual reproduction tests. Hold the parent solver/state fixed and swap ancestor versus descendant improvement operators. Separately hold the operator fixed and swap solver state. Include a frozen-generator search with access to the same archive; include equivalent accumulated experience where feasible, so simple access to more logs is not credited to inherited capability. Report the full candidate distribution and failed descendants, not only the best-of-many endpoint.

One generation of transfer only establishes an improved search/update operator. Evidence for recursion requires the improved operator to participate in making subsequent improved operators, followed by fresh-task benefit. Increasing best-so-far score with cumulative compute is expected under ordinary search and is not acceleration. No large code-evolution platform is warranted until a small direct test distinguishes inherited operator competence from solver quality and search budget.

## Identification: what a serious joint test would have to isolate

Use a common frozen evaluation population, identical allowed information, identical paid assay budget and an explicit compute/candidate budget. The following are distinct hypotheses:

- World value: a learned predictive/transition representation improves the relevant task beyond strong direct predictors receiving the same information.
- Agent value: an acquisition/update policy improves decisions for a fixed solver/world beyond random, uncertainty and learner-aware design baselines.
- Inheritance value: inherited improvement behavior improves future modifications beyond inherited weights/code artifacts, archives and a frozen generator.
- Joint value: the combination improves beyond the full relevant individual and pairwise controls. A lower combined loss alone does not locate the cause.
- Recursive value: improvement of the improvement operator itself survives matched counterfactual tests and fresh tasks across generations.

Factorial interactions depend on outcome scale and evaluation noise. A nonzero interaction between two components should not be relabeled mechanistic synergy without showing which decision changed and why. The protocol already prohibits collapsing missing H into quiescence or treating the combined benchmarking loss as clinical utility. Those restrictions remain necessary for any cross-domain mechanism test.

## Proposed stopping rules and live-debate challenges

Stop the V-JEPA biological-dynamics route on this asset because the data do not encode the required within-unit trajectories. Keep belief/solver dynamics as an explicitly conventional design hypothesis if supported by the ordinary probe. Stop an SEAL-derived proposal if its strongest formulation is only choosing among pre-existing update families or recalculating expected information gain without a distinguishable mechanism. Stop DGM promotion if descendants only improve prediction, if advantage disappears when frozen search gets the same archive/evaluations, or if improver competence is never tested independently.

Questions for the constructive review after this note is sealed:

1. What exact state variable and transition are borrowed from V-JEPA, and what observed records identify that transition rather than an arbitrary ordering of independent bundles?
2. What decision-relevant object is recomputed under the current solver, and why is its benefit not already explained by ordinary sequential experimental design or meta-learning?
3. Which inherited component causes descendants to become better at generating improvements, and what swap test distinguishes it from inheriting a better predictor?
4. Which data support independent training, selection and confirmation of that claim, without consuming later reserve outcomes or reusing the development probe as a fresh test?

My initial position is conservative but not a universal impossibility claim: the source papers offer useful operational design lessons, while the current static asset supports at most a narrow solver/update-value diagnostic. Evidence could change this position if it supplies the missing identifying data and a minimal mechanism-specific result against the conventional alternatives.
