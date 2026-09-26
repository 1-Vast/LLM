# Downstream Tasks And Evaluation Contract

This file is the working contract for MAESTRO's downstream tasks, data boundaries, virtual-cell
roadmap, and evaluation gates. Detailed protocols, source excerpts, raw API probes, and engineering
measurements belong in [`research/`](research/README.md).

Status labels:

- **implemented** — present in `src/` or `tools/` and covered by a contract test;
- **partial** — a mechanism exists but does not cover the full stated design;
- **design** — specified here but not implemented;
- **unverified** — dependent on an external asset or service not verified in this workspace.

---

## 1. Objective

Given a desired biological state, current evidence, constraints, and a resource limit, MAESTRO must
answer:

> Which intervention or measurement should be selected next, why is it admissible, what would
> falsify the current explanation, and what observation should trigger revision?

The agent owns the objective, intervention design, evidence interpretation, workflow repair, stopping
decision, and final bounded action. The virtual cell supplies an applicability-bounded prediction for
a stated intervention. It does not choose the objective, establish causality, certify target
engagement, or replace an experiment. The agent must continue when the virtual cell abstains.

The primary scientific task is **cell-intrinsic genetic-pharmacological discordance**. Drug response,
target validation, combinations, and toxicity are downstream task families with separate gates; they
are not separate novelty claims.

## 2. System Boundary

### 2.1 Responsibility split

| Responsibility | Agent / decision core | Virtual cell |
|---|---|---|
| Objective | Defines the question and acceptable actions | Receives a stated objective |
| Evidence | Retrieves, qualifies, contrasts, and buys measurements | Consumes compatible inputs |
| Prediction | Interprets alternatives and limitations | Predicts a supported state change |
| Causality | Requires qualified measurements and interpretation rules | Never establishes causality |
| Uncertainty | Chooses measure, defer, abstain, or act | Reports uncertainty and applicability |
| Feedback | Updates case state from qualified results | Is scored against later measurements |

Representation, prediction, and intervention design are engineering capabilities. They are not Pearl's
association/intervention/counterfactual hierarchy: a conditional predictor does not identify
`p(Y | do(u))` by itself.

### 2.2 Evidence invariants

Evidence origin never strengthens through downstream use. A retrieved source, model prediction,
visual reading, typed judgment, or virtual-cell result remains its original kind after entering
context, memory, a prompt, a tool receipt, or a conclusion.

In particular:

- `model_prediction` never becomes `real_measurement`;
- a typed judgment never satisfies a measured premise;
- a virtual-cell prediction never proves engagement, mechanism, synergy, or efficacy;
- a regulatory assertion is a hypothesis unless qualified intervention evidence supports a narrower
  claim;
- a solver optimum is optimal only for its declared finite menu and assumptions.

## 3. Primary Task And Mechanism Contrast

The primary case contains competing explanations for a disagreement, such as incomplete functional
perturbation, intervention-mode non-equivalence, multi-target pharmacology, pathway compensation,
context dependence, or unresolved mechanism.

Each explanation must lead to a distinct development decision. A contrast is admissible only when:

1. open prerequisites are named;
2. the registered evidence plan is executable or has a bounded supplier chain;
3. planned outcomes differ between explanations;
4. each explanation maps to a different action or declared decision boundary;
5. the interpretation rule says what the result cannot establish.

The belief state is:

```text
B = (C, M, S)
```

- `C` — explanations still compatible with admitted evidence, represented as a set rather than an
  invented posterior;
- `M` — measured premises with quantity, entity, unit, condition, and time;
- `S` — admitted scope for each field, including plan limitation, feasibility, implementation, and
  mechanism contrast.

Only a qualified, condition-matched result whose interpretation rule targets `mechanism_contrast`
may remove an explanation from `C`. A typed judgment, retrieval result, or model prediction can
recommend a measurement but cannot perform that update.

## 4. Downstream Task Families

Each family remains pending until its qualification gate passes.

### Task 1 — Drug Response

Predict supported state and phenotype responses across context, dose, and time. The agent selects
readouts, controls, doses, and follow-up assays. Report endpoint error, ranking, interval calibration,
abstention risk, and fixed-budget decision loss. Stress tests include unseen context, unsupported dose
or time, missing control, and a transcriptional prediction incorrectly presented as phenotype validity.

### Task 2 — Target Identification And Validation

Determine which target or necessary target set could move a defined context toward a desired phenotype.
The agent integrates dependency, chemical response, pathway evidence, and contradictions, then designs
a functional-strength ladder and validation sequence. Stress tests include genetic-pharmacological
discordance, pan-lethal knockout, partial suppression, off-target phenocopy, context-specific
dependency, and necessary multi-target activity.

### Task 3 — Combination And Synergy

Require measured combination matrices with matched single-agent controls. Prespecify a reference model
and report sensitivity to alternatives. Transcriptomic interaction is not viability synergy, and
efficacy and toxicity remain separate outcomes. Stress tests include absent combination labels,
out-of-distribution pairs, schedule dependence, shared off-targets, and growth-rate confounding.

### Task 4 — Toxicity And Safety Liability

Prioritize in-vitro hazards while preserving activity. This cannot establish clinical safety or an
in-vivo therapeutic window from isolated cell assays. Stress tests include organ toxicity inferred
from one cell model, missing exposure, rare sensitive subpopulations, delayed toxicity, and pathway
activation mistaken for injury.

## 5. Data And Evidence Policy

Prefer assets that are already public, condition-level, inexpensive to process, and deployable from
inputs available before a candidate is measured: structure, dose, time, cell background, matched
control, and an existing observation when one is available.

Every asset records separately:

- access and preprocessing cost;
- training and inference cost;
- new-candidate measurement cost;
- source and source cluster;
- independent unit and replicate unit;
- condition, dose, time, batch, missingness, and detection limit;
- quantity, unit, assay, normalization, and processing version;
- licence and distribution membership.

Do not fabricate a paired modality. An imputed modality remains a prediction with uncertainty and is
not independent confirmation of its input. Missingness is not a silent zero. Unmatched samples must
not be joined by gene symbol alone.

Biological relations carry explicit species, tissue, cell type, context, perturbation, and time when
known. Known condition mismatches are excluded; unknown conditions are labelled unknown. Correlation,
regulatory association, and causal effect remain distinct. Attention and feature importance cannot
be registered as causal regulation. A causal-effect assertion requires an experimental perturbation
and declared controls.

Source clusters prevent multiple reports of one experiment from counting as independent replication.
Declared evidence lineage is traceable and retractable, but undeclared external-model training data
cannot be reconstructed.

Detailed asset costs and licences are recorded in [`research/asrg/02_data_and_costs.md`](research/asrg/02_data_and_costs.md).

## 6. Tool Qualification

Every local adapter requires a manifest, typed input and output schemas, source and version hashes,
supported task types and suffixes, applicability, explicit failure output, estimated cost, a
validation example, and both `use_when` and `do_not_use_when` conditions.

Qualification states are `discovered`, `packaged`, `reproduced`, `task_validated`, and `active`.
`active` does not mean universally valid. Dynamically retrieved code is never imported directly into
production.

Current manifest-scoped tools include dataset profiling, column summaries, table filtering,
evidence-bundle optimization, multimodal alignment, typed decision review, virtual-cell query, and
measured-signature retrieval (which annotated compound classes a measured SciPlex3-line response
resembles; 0.500 held-out class agreement against chance 0.059, see section 11).
Tool output is an observation or derived analysis; it does not become a mechanism conclusion.

The next conditional adapters are `condition_alignment`, `entity_normalization`,
`pseudobulk_differential`, `pathway_and_regulatory_analysis`, `perturbation_realization_qc`,
`primary_evidence_retrieval`, `virtual_cell_state`, `intervention_bundle_select`, and
`workflow_schedule`. Each remains conditional on a demonstrated task gap.

## 7. Agent, Typed Jev, And Uncertainty

The agent uses a bounded context containing task state, evidence cards, provenance, limitations,
memory, and named omissions. Mandatory task-state overflow refuses explicitly; an evidence card is
included atomically or omitted with an identifier and reason.

Typed Jev is a structured advisory processor. It may perform plan critique, evidence-sufficiency
scoring, ranking of registered actions, repair suggestions, applicability review, candidate regulator
ranking, and structured routing suggestions.

It may not update `C`, satisfy a premise, invent an action identifier, or turn a prediction into a
measurement. Its outputs are `model_prediction` and are audited by `tools/typed_decision_review/`.
An action-ranking scope must pass reproducibility and later outcome-based calibration before it can
break a deterministic tie. Unstable or revoked scopes are suppressed, while the original judgment
remains in the audit record.

Uncertainty is separated into observation noise, epistemic uncertainty, task-weight uncertainty, and
distribution shift. An uncertainty-weighted loss is not a predictive interval. Calibrate on disjoint
units, report interval coverage and width by context and endpoint, and evaluate selective risk as
the system abstains.

## 8. Virtual-Cell World Model Roadmap

The operational interface is `PredictionRequest`, `StatePrediction`, and `WorldModelRung`. A backend
is eligible only when it reports applicability, uncertainty, confidence, distribution membership,
limitations, request identity, model version, and an abstention reason. It is registered behind
`CompositeWorldModel`; it does not replace the agent.

### 8.1 Existing Ladder

The current ladder contains qualified baselines and optional State/dose-response backends. It keeps
simulation compute cost separate from experimental budget, routes by actual query support, preserves
backend disagreement, and converts contract violations into abstentions.

**SciPlex3 response rung (`sciplex_response`, implemented 2026-09-26).** Structure-nearest-neighbour
retrieval over measured 24 h responses in A549, K562 and MCF7. It is the first rung whose intervals
are CALIBRATED by a receipt: cross-conformal coverage 0.805 at 0.80 on held-out compounds. It
serves only readouts whose calibrated interval is narrower than predicting the average drug's
response, which on 2026-09-26 left the response magnitude alone (width ratio 0.730); all 41 Hallmark
readouts are refused by name. A compound already in the library is refused so that its measurement
is used. It stays planning-only: no arm passed the anchor-depth rule required for advisory ranking.
It answers 24 h only; the same release's A549 72 h cohort is not served, so a 72 h query is refused
by name (`time_not_supported:72h`) and the magnitude tie-break can never favour a later time point.

### 8.2 V-JEPA 2 Design Reference

**Status: design / conditional implementation.** The reference is:

- Assran et al., **V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction, and
  Planning**, arXiv preprint, June 2025, [arXiv:2506.09985](https://arxiv.org/abs/2506.09985).

Only two principles are borrowed:

1. learn predictive representations in latent space instead of reconstructing every raw input value;
2. condition a predictor on an action to forecast a future latent state and support bounded planning.

The paper's video, image, and robot results are external evidence for this representation-learning
pattern. They do not validate a virtual cell, identify biological mechanisms, or establish causal
effects.

The mapping is:

| V-JEPA 2 | Virtual cell | Boundary |
|---|---|---|
| Video state | Condition-specific cellular state | Context, assay, units, batch, and time are explicit |
| Masked latent | Masked gene, modality, time, or condition latent | Missingness is recorded and is not zero |
| Robot action | Intervention, mode, dose, and exposure | Stated intervention does not prove engagement |
| Future latent | Post-perturbation cellular state | Prediction is not measurement |
| Goal embedding | Declared target state and readout objective | Latent distance is not a mechanism verdict |
| MPC rollout | Bounded intervention/evidence planning | Only applicable actions may be rolled out |

### 8.3 Proposed Training Stages

**Stage A — condition-aware latent pretraining.** Encode RNA, protein, activity, occupancy,
chromatin, morphology, control state, context, and time. Predict masked or held-out latent states
using explicit gene-block, modality, time-point, condition, matched-control, and context-stratum
masks. The training manifest records source study, independent unit, quantity, unit, batch,
missingness, and preprocessing version.

**Stage B — intervention-conditioned transition.** With a qualified encoder, learn:

```text
z_t = Encoder(observed modalities, context, time)
z_(t+1) = Predictor(z_t, intervention, dose, duration, context)
readouts = Decoder(z_(t+1), requested_quantity)
```

Training requires matched controls and real perturbation outcomes. The intervention includes an
identifier, mode, intended targets, dose, unit, and exposure time. A declared target is metadata,
not proof of engagement. First evaluate short transitions; long rollouts, feedback, and combinations
require separate identifiability gates.

**Stage C — readout decoders and calibration.** Decode RNA, protein, activity/occupancy, morphology,
viability/proliferation, and chromatin as separate quantities. Each decoder keeps units, intervals,
calibration data, applicability domain, and limitations. A candidate objective is:

```text
L = lambda_latent L_masked_latent
  + lambda_readout L_readout
  + lambda_transition L_transition
  + lambda_calibration L_calibration
  + lambda_condition L_condition_consistency
```

Weights are frozen before held-out evaluation. A calibration loss does not prove final calibration.

### 8.4 Integration And Planning Boundary

The first implementation would be an optional `JEPACellStateRung` behind the existing world-model
interface. It accepts `PredictionRequest`, emits `StatePrediction`, preserves lineage and compute
cost, and returns a named refusal if no qualified checkpoint is available. It must not introduce a
second action schema or applicability vocabulary.

The model may predict a supported readout, rank candidate transitions, identify a readout that could
separate hypotheses, and support bounded model-predictive planning. The agent still owns the
objective, evidence plan, repair, stopping decision, and belief update.

The model may not establish engagement, binding, causality, synergy, or clinical safety; infer a
regulatory edge from latent proximity; combine incompatible contexts or batches; bypass topology,
budget, deterministic validation, or evidence interpretation; or continue after applicability
failure as if missing support were zero.

Planning is bounded:

```text
for action in registered_actions:
    if not applicable(action, current_profile):
        record abstention
    else:
        predict transition and readout with uncertainty
choose only through declared decision and budget rules
```

Predictions from different rungs are not averaged when quantities or applicability domains differ.
Disagreement is retained as a limitation. A rollout cannot create a biological replicate, source
cluster, or measured result.

### 8.5 Data And Evaluation Gates

Freeze a data card containing source clusters, independent units, species and cell context,
intervention/mode/dose/time, matched controls, readout quantity and units, batch, replicate unit,
missingness, preprocessing, and train/calibration/hidden-test membership.

Random cell splits are insufficient. At minimum, evaluate within-domain interpolation and hold out
cell context, intervention or scaffold, perturbation mode, dose/time, study cluster, and modality.
Unseen-context performance is not expected to be good automatically; a correct result can be an
abstention with a named reason.

Compare:

1. naive or train-mean readout;
2. current linear or dose-response baseline;
3. existing State or registered rung;
4. latent predictor without action conditioning;
5. action-conditioned predictor;
6. action-conditioned predictor with calibration and abstention.

Report separately masked latent error, endpoint error/ranking, interval coverage and width, Brier or
log score where applicable, abstention rate and reason, unsupported mechanism advancement, justified
deferral, decision regret, cost-to-admissible-action, and access/processing/compute/measurement cost.
A lower latent loss without endpoint calibration or decision-regret improvement is a negative result.

## 9. Evaluation Contract

Freeze before any hidden outcome is revealed:

- objective and weights;
- acceptable actions and stopping rules;
- visible evidence and tool pool;
- model versions and prompts;
- budgets and cost units;
- split units and outcome interpretation.

Score five levels separately: representation, prediction, intervention design, biological credibility,
and final decision quality. Never average them into one unqualified score.

Mandatory controls include no model, simple model, qualified model, applicability-scoped model,
prediction-shuffle, fixed workflow, one-shot selection, reactive replanning, repair-disabled, and
equal-budget random legal repair. Compare Jev and virtual-cell removal with the same visible inputs,
candidate menu, and budget.

Report error, ranking, calibration, abstention, unsupported advancement, justified deferral, decision
regret, cost-to-admissible-action, evidence cost, compute cost, provider spend, and latency.
Laboratory cost is wells and turnaround days with shared controls charged once.

The primary agent-level question is whether a component improves supported decisions at equal
resources. A lower prediction error alone is not an intervention-design result.

## 10. Research Sequence And Implementation Backlog

| Priority | Work item | Completion criterion |
|---|---|---|
| P0 | Freeze objective, endpoints, data visibility, and hidden outcomes | Digested protocol and independent case units |
| P0 | Qualify evidence and existing tools | Version, provenance, cost, applicability, and failure output |
| P0 | Complete one evidence-bounded agent loop | Contrast, tool call, repair, result import or justified deferral, stop reason |
| P0 | Establish policy baselines | Fixed, one-shot, reactive, and random legal repair under equal resources |
| P1 | Improve acquisition and repair | Lower unsupported decisions or measurement cost on independent cases |
| P1 | Evaluate virtual-cell and Jev contribution | Removal and enabled arms with decision-level metrics |
| Conditional | Train or adapt a virtual-cell rung | Demonstrated gap, simple baseline, held-out gain or calibrated abstention |
| Conditional | Add fusion, alignment, or combination model | Real labels, controlled comparison, incremental decision benefit |
| Later | Learned GRN dynamics, tissue scale, or complex polypharmacology | Identifiable target, dedicated data, matched controls, independent validation |

Do not build a large multi-agent ecosystem or a new encoder before one complete evidence-bounded
intervention design works with existing qualified tools. Do not add a modality or scale to fill a
diagram; add it only when it answers a defined question and has a measurable bridge.

## 11. Current Verified Status

Implemented and tested:

- structured task-state transport and explicit context-budget refusal;
- condition-aware biological assertions and source lineage/retraction;
- typed Jev critic with advisory-only judgments, calibration, and reproducibility gating;
- deterministic tool manifests, negative conditions, receipts, and cost boundaries;
- action topology and finite-menu evidence selection;
- virtual-cell applicability, uncertainty, abstention, lineage, and compute accounting;
- multimodal quantity, missingness, pairing, unit, and batch checks;
- `tools/typed_decision_review/` for replay/audit of Jev reviews;
- feature-label verification by cell-identity markers (`virtual_cell.identity_markers`), which found
  that the SciPlex3 Figshare release names every gene one column off;
- measured-signature retrieval (`tools/signature_retrieval/`) and the calibrated `sciplex_response`
  rung (section 8.1).

Existing offline and targeted regression suites pass. The Jev critic on/off trace comparison preserves
the deterministic check block and keeps all judgments as `model_prediction`.

**Biological depth, measured 2026-09-26** (pre-registered; `research/biological_depth/`,
`log/20260926/README.md`). SciPlex3 itself carries the biology: seven of ten literature anchors hold
(HSF1 induction by HSP90 inhibitors, glucocorticoid targets in A549, estrogen-response loss only in
MCF7, hypoxia genes under prolyl-hydroxylase inhibition, p53 activation sparing p53-null K562,
BCR-ABL inhibitors hitting K562, HDAC-inhibitor dominance). No virtual-cell arm reproduces more than
three of the seven for compounds it never saw, none beats predicting "no change" gene-wise, and no
arm meets the rule for advisory ranking. Structure retrieval carries the most direction beyond the
shared drug response; declared pathway annotations add a controlled +0.023; structural novelty is the
only uncertainty signal that works. DeepSeek and Jev cannot name a mechanism class from an anonymised
signature (0.100 and 0.075 against a 0.150 frequency prior), but follow a retrieval card to 0.425 and
0.475, while retrieval alone reaches 0.500.

**Measurement choice, measured 2026-09-26** (pre-registered; `research/dynamic_world_model/`,
`log/20260926/README.md`, block 2). On SciPlex3 at 24 h (three lines) and 72 h (A549), with a
deterministic validator that eliminates a hypothesis only on a detected, template-matching profile
and never on an absent response, no virtual-cell planner beat the current magnitude tie-break:
reference scenario cards through `select_expected_coverage` -0.044 [-0.083, -0.004] correct
decisions, a time-aware card policy +0.054 [-0.039, 0.152], cards given to DeepSeek +0.006
[-0.058, 0.069]. The magnitude tie-break itself is worth +0.386 over no world model. A gene-space
ridge transition predicts a compound's 72 h profile from its 24 h profile better than persistence
(cosine +0.283 [0.227, 0.336]) without improving the mechanism class it implies or any decision.
Multi-branch outcome predictions (each reference compound a branch) beat a single class mean
(log loss -0.599). The validator kept wrong eliminations near 1-2% per measurement where an
ungated nearest-class reading reached 26%. Post hoc, time decided the episodes: DNA
methyltransferase, BET and Aurora inhibitors become separable in A549 only at 72 h, a fixed 24 h
then 72 h protocol beat magnitude by +0.244, and DeepSeek without cards chose 72 h after every
undetected 24 h result; this is a hypothesis for an independent test, not a result.

**Prediction-to-measurement link, audited and repaired 2026-09-26** (pre-registered;
`research/acquisition_link/`, `log/20260926/README.md`, block 3).

Correction to the paragraph above, recorded the same day: "the current magnitude tie-break" is
the non-default budgeted path. The production controller (`from_workspace`, the CLI and the public
loop) selects on the power-aware path, which computed the virtual cell's priorities and only
logged them. On those menus it therefore chose exactly as the no-world-model arm: 0.172 correct
decisions in tier B, against 0.558 for magnitude.

The audit also found two further breaks:
- per-action queries stated the template's exposure time, so a 72 h action was ranked by a 24 h
  prediction;
- per-hypothesis outcome forecasts reached the selector only as one detection probability.

The repair is `maestro.acquisition.select_discriminating_action`. It is opt-in through
`discrimination_selection` and otherwise logged in shadow. It values a measurement by how the
registered rules would read it under each hypothesis, gates on wrong-elimination risk at the
utility's break-even, discounts thin support without deleting it, and ranks by a one-sided lower
bound.

On block 2's episodes it decided neither better nor worse than magnitude: tier B -0.019
[-0.053, +0.017], tier A +0.033 [-0.030, +0.089]. The verdict is INCONCLUSIVE. Its forecasts are
well calibrated (ECE 0.058 and 0.085).

Wiring magnitude into the power-aware path raised tier-B utility by +0.298, but failed its keep
rule in tier A and raised tier-B wrong eliminations by 0.044, so it is not enabled.

**Sequence stopping gap and independent validation 2026-09-26** (pre-registered;
`research/sequence_audit/`, `log/20260926/README.md`, block 4).

A contingent two-step policy (research code from the same day's follow-up) lost to the fixed
24 h then 72 h sequence on SciPlex3 because it bought fewer measurements. Its stops were mostly
uninformed (no paired references, or too few), not a code defect. The arms' different
QC-failure rules explained only 0.015 of the 0.274 gap.

One revision was frozen before any L1000 reading: a fixed-sequence fallback for uninformed stops.
On L1000 (four lines, 6 h and 24 h) it gained +0.0013 utility [+0.0002, +0.0026] and did not
beat the fixed sequence. The frozen verdict is SHADOW: opt-in, negligible, not promoted.

On L1000, with more references per class, most stops were informed. The fixed sequence beat the
planner only in the A549-only tier, where a 24 h first measurement leaves no legal
continuation.

Not yet demonstrated:

- improved decision regret on independent biological cases;
- lower cost-to-admissible-action from Jev or a virtual-cell predictor;
- better measurement choice from a virtual-cell planner (reference cards, a time-aware policy or a
  learned 24 h to 72 h transition) than from the current magnitude tie-break;
- a time-point selection rule confirmed on data it was not discovered on;
- a decision benefit from reading per-hypothesis forecasts through the registered rules
  (`select_discriminating_action`), or from letting magnitude break ties on the power-aware path;
- a contingent two-measurement policy, or its fixed-sequence fallback, that beats the fixed
  early-to-late sequence on independent data (`research/sequence_audit/`: SHADOW, negligible);
- a virtual-cell predictor with biological depth for unseen compounds: the V-JEPA-style latent model
  was built and tested (section 13.6) and neither beat PCA nor structure retrieval;
- causal mechanism, target engagement, clinical safety, or generalization to unsupported contexts.

## 12. Research Records And Sources

The research index is [`research/README.md`](research/README.md). Important records include:

- [`research/framework_optimization.md`](research/framework_optimization.md) — conditioned biology,
  Jev evidence context, modality costs, and verification;
- [`research/typed_decision_model.md`](research/typed_decision_model.md) — TypeSafe Jev contract;
- [`research/judgment_stability.md`](research/judgment_stability.md) — reproducibility and calibration;
- [`research/dynamic_networks.md`](research/dynamic_networks.md) — conditions and multimodal limits;
- [`research/asrg/03_experiment_protocol.md`](research/asrg/03_experiment_protocol.md) — frozen
  agent-policy evaluation protocol;
- [`research/agent_research_20260925.md`](research/agent_research_20260925.md) — literature review
  and task-state repair record;
- [`research/biological_depth/`](research/biological_depth/README.md) — pre-registered biological-depth
  test of the virtual cell and agent, the SciPlex3 label-offset finding, and the latent-model result.

External model references are design provenance. V-JEPA 2 is cited at
[arXiv:2506.09985](https://arxiv.org/abs/2506.09985); its reported video and robot results do not
validate the biological claims in this repository.

The final claim remains narrow: under a frozen protocol and equal resources, MAESTRO may demonstrate
better-supported decisions or lower cost-to-admissible-action on tested cases. No passing software
test licenses a claim about a target, mechanism, efficacy, clinical safety, or an untested biological
context.

## 13. Paper-Derived Extensions For Biological World Models

This section records the seven supplied papers as design sources. The research focus is deliberately
narrow:

1. **How to learn useful latent feature representations and latent transitions** from biological
   observations, interventions, time, and context.
2. **How those representations improve agents, virtual cells, and Typed Jev** without allowing a
   prediction to become a measurement or a belief update.

Their reported results are not results for MAESTRO. All proposed extensions must use the existing
biological conditions, source lineage, applicability, calibration, abstention, and deterministic
validation contracts.

### 13.1 Source Review

| Source | Main contribution relevant here | Transfer judgment |
|---|---|---|
| [`2506.09985v1.pdf`](<D:/论文/paper/2506.09985v1.pdf>) — V-JEPA 2 | Action-free latent prediction followed by action-conditioned latent dynamics and model-predictive planning | **Adopt as the core representation/transition template**, with biological masking and readout-specific calibration |
| [`zhou25t.pdf`](<D:/论文/paper/zhou25t.pdf>) — DINO-WM | Offline world model over pretrained features; goal-feature prediction and test-time action optimization | **Adopt offline latent transition and goal-conditioned planning**, but replace visual goal distance with declared biological readouts |
| [`2607.27599v1.pdf`](<D:/论文/paper/2607.27599v1.pdf>) — World Action Planner | VLM proposes plans, an action-conditioned world model imagines candidates, and search/optimization refines them | **Adopt the proposal → imagine → critique → search loop** for registered evidence actions; do not import pose-image robot assumptions |
| [`ICLR-2026-wimle-uncertaintyaware-world-models-with-imle-for-sampleefficient-continuous-control-Paper-Conference.pdf`](<D:/论文/paper/ICLR-2026-wimle-uncertaintyaware-world-models-with-imle-for-sampleefficient-continuous-control-Paper-Conference.pdf>) — WIMLE | IMLE captures multi-modal transitions; ensembles and latent sampling estimate uncertainty; confidence weights synthetic rollouts | **High-value biological extension** for heterogeneous cell responses and conflicting supervision; require endpoint calibration before use |
| [`s41586-026-10644-y.pdf`](<D:/论文/paper/s41586-026-10644-y.pdf>) — Co-Scientist | Multi-agent hypothesis generation, critique, tournament/ranking, literature grounding, and experimental validation | **Adopt the verification and experiment-feedback pattern**, not unconstrained hypothesis voting |
| [`s41586-026-10652-y.pdf`](<D:/论文/paper/s41586-026-10652-y.pdf>) — Robin | Literature agents and data-analysis agents form an iterative lab-in-the-loop loop; raw assay data informs follow-up hypotheses | **High-value biological workflow reference** for result ingestion, assay follow-up, and analysis provenance |
| [`2608.26701v1.pdf`](<D:/论文/paper/2608.26701v1.pdf>) — Accelerating Scientific Research with Gemini | Execution-grounded Co-Scientist extension across biology, materials, and computer science; reliability modules and human-in-the-loop autonomy levels | **Adopt execution logs, autonomy labels, and failure termination**; do not treat its case studies as a universal autonomous-discovery result |

### 13.2 Highest-Value Extension: A Stochastic Biological Latent Transition Model

The most promising combination is V-JEPA 2 + DINO-WM + WIMLE, adapted to biological states:

```text
z_t = Encoder(observed modalities, context, time)
z_(t+1,k) = Predictor(z_t, intervention, dose, duration, context, latent_code_k)
readout_k = Decoder(z_(t+1,k), requested_quantity)
```

Unlike a robot state, a cell state may have several plausible outcomes under the same recorded
intervention because of cell heterogeneity, partial observability, batch effects, and unmeasured
realization of the perturbation. A single conditional mean can therefore hide the biological modes
that matter for a decision. The proposed model should:

- learn latent state representations from masked RNA/protein/activity/chromatin/morphology data;
- learn short-horizon intervention-conditioned transitions from matched controls and real perturbation
  outcomes;
- represent multiple plausible transition modes rather than averaging them into one response;
- estimate epistemic and outcome uncertainty separately;
- decode each requested quantity with its own units, interval, calibration, and applicability;
- abstain when context, dose, time, intervention mode, or readout is unsupported.

This is a **design proposal**, not an implemented model. WIMLE's uncertainty-weighted synthetic
rollouts should be translated into a guarded planning rule: high-uncertainty imagined transitions
may suggest a measurement or be excluded from action ranking, but they must not be treated as
negative or positive biological evidence. Confidence weights must be learned and calibrated on
held-out biological units; they cannot be copied from the robot setting.

### 13.2.1 Representation-Learning Study Plan

The first study target is the representation, before adding an autonomous planner:

1. **Masked pretraining:** hide time blocks, feature groups, and modality-specific channels and
   predict their latent targets from the visible context.
2. **Biological factorization:** retain intervention, dose, duration, cell state, batch, and assay
   context as typed conditioning variables rather than mixing them into an unlabelled embedding.
3. **Transition learning:** predict short-horizon latent changes under matched controls and named
   interventions; test both deterministic and multi-modal predictors.
4. **Readout probes:** decode only declared quantities such as target engagement, pathway activity,
   viability, or morphology, with separate calibration per endpoint.
5. **Representation tests:** measure masked-prediction quality, cross-modal retrieval, temporal
   consistency, intervention sensitivity, batch robustness, and held-out-unit transfer.

The representation is useful only when it preserves distinctions needed by a downstream decision.
Low reconstruction or prediction error alone is insufficient. A latent feature is promoted when it
improves a prespecified decision metric while preserving applicability and abstention behavior.

### 13.2.2 Effect On Agents, Virtual Cells, And Typed Jev

The learned representation should be exposed through three bounded interfaces:

| Consumer | Benefit from latent features | Allowed output |
|---|---|---|
| Virtual cell | compact state, multi-step transition, intervention-conditioned counterfactual candidates | predicted state/readout with uncertainty and applicability |
| MAESTRO agent | compare mechanisms, rank registered evidence actions, select the next informative readout | advisory ranking or deferral; no direct belief update |
| Typed Jev | fast typed critique of context match, evidence sufficiency, missing premises, and candidate repairs | structured judgment with confidence, rationale fields, and abstention |

Typed Jev should consume latent summaries as **model predictions** with provenance, checkpoint, data
slice, and uncertainty attached. It can use them to narrow candidates, route a task, or flag that a
measurement is worth buying. It cannot call a latent distance causal evidence, certify target
engagement, or override `DeterministicValidator`. Repeated calls must be checked for stability; an
unstable recommendation loses action-selection authority.

### 13.3 Offline Latent Planning For Evidence Selection

DINO-WM and World Action Planner suggest a useful MAESTRO loop for a finite registered menu:

```text
Jev or planner proposes candidate evidence actions
    -> world model imagines supported state/readout transitions
    -> deterministic checks remove infeasible candidates
    -> acquisition.py evaluates cost, coverage, prerequisites, and source dependence
    -> only the first admissible action is executed or purchased
```

The world model can provide a prior ranking or a predicted discriminating readout. It cannot replace
the exact finite-menu selector, satisfy a missing premise, or update the hypothesis set. Planning
must be receding-horizon: after each qualified result, rebuild the current profile and re-evaluate
applicability instead of trusting a long imagined trajectory.

The robot papers' goal-image distance becomes a biological goal contract:

- a declared target state;
- a named endpoint and quantity;
- a matched control;
- acceptable uncertainty and interpretation boundary;
- a registered action whose result could change the decision.

Latent distance is only a proposal score. The final action is chosen by declared decision rules and
budget constraints.

**Status 2026-09-26: this loop was run and is not promoted.** Scenario cards (the validator's
outcome frequencies on measured reference compounds, per hypothesis and condition) supplied detection
power to `acquisition.py`, a time-aware variant conditioned step 2 on the step-1 outcome, and a
learned population transition forecast the compound's own next profile. None beat the current
magnitude tie-break or a fixed 24 h then 72 h protocol on held-out SciPlex3 compounds; the cards also
under-predicted success (ECE 0.101 and 0.154) and their two-reference refusal removed the 72 h
options that decided the slow-acting classes. See `research/dynamic_world_model/`.
**Update the same day (block 3):**
- The branches now reach a selector whole (`select_discriminating_action`, opt-in).
- One-reference branches are served and discounted rather than refused. This added 0.03 to 0.05
  correct decisions under both selectors.
- The result against magnitude is inconclusive.
- Post hoc: the selector's lower-bound ranking steered away from the thinly measured 72 h
  conditions.

See `research/acquisition_link/`.

**Update the same day (block 4):**
- On independent L1000 data, a two-step planner fed these reference branches was not
  distinguishable from the fixed sequence across four lines (utility +0.012 [-0.013, +0.039]).
- It was worse than the fixed sequence in A549 alone (utility -0.021 [-0.044, -0.001]).
- A fallback for uninformed stops changed almost nothing.

See `research/sequence_audit/`.

### 13.4 Closed-Loop Experimental Evidence From Co-Scientist And Robin

The two Nature papers support a complementary extension to the agent workflow:

1. Generate competing hypotheses under explicit constraints.
2. Generate a small set of registered assays that distinguish them.
3. Execute only an approved assay and record raw data, code, parameters, controls, and logs.
4. Run deterministic QC and qualified analysis tools.
5. Import results with source, independent unit, batch, quantity, and limitation metadata.
6. Update the contrast only through the existing interpretation rule.
7. Generate the next repair or measurement plan from the qualified result.

Co-Scientist's tournament and reflection mechanisms can be used for proposal prioritization, but
agreement among agents is not evidence. Robin's repeated analysis trajectories can be used for
robustness checks, but consensus cannot repair a bad input, an unpaired sample, or a failed assay.
The raw execution log remains authoritative for whether an experiment happened and what it returned.

The implementation opportunity is therefore a **result-ingestion and verification contract**, not a
free-form autonomous scientist:

- a missing raw log terminates the result path as `execution_unverified`;
- a failed QC result cannot close a mechanism gap;
- unsupported or unregistered follow-up assays become capability gaps;
- a paper or model-generated explanation remains advisory until a qualified result is imported;
- autonomy level and human intervention are recorded per round.

### 13.5 Biological Deep-Integration Targets

The paper ideas become useful to bioinformatics only when tied to specific quantities and conditions:

| Target | Proposed integration | Primary failure to test |
|---|---|---|
| Perturbation realization | Latent transition predicts RNA/protein/activity consequences of a stated intervention | RNA change is mistaken for target engagement |
| Mechanism contrast | Multi-modal imagined outcomes identify the readout most likely to separate explanations | Latent similarity is mistaken for causal discrimination |
| Heterogeneous response | WIMLE-style modes represent responder/non-responder or compensation branches | Modes are artifacts of batch or source duplication |
| Time-dependent feedback | Short transitions are composed only when time, intervention, and controls are matched | Snapshot association is called feedback |
| Assay planning | World-model ranking proposes a measurement, exact acquisition selects it | Model ranking bypasses prerequisites or budget |
| Result interpretation | Robin/Co-Scientist workflow feeds qualified raw results back to repair | Consensus masks failed or missing execution |
| Cross-scale reasoning | Separate decoders bridge RNA, protein, activity, morphology, and viability | An unvalidated bridge is treated as identity |

### 13.6 Implementation Order And Acceptance Gates

Implement in this order:

1. **P1 — representation baseline:** implement masked latent pretraining and endpoint probe
   evaluation on a small, frozen biological data slice;
2. **P1 — uncertainty and multimodality contract:** add a backend-independent representation for
   multiple predicted transitions, epistemic/aleatoric uncertainty, confidence, and abstention;
3. **P1 — offline latent transition prototype:** implement a small `JEPACellStateRung` or equivalent
   adapter behind `WorldModelRung`, with no checkpoint fallback and a named refusal;
4. **P1 — evidence-planning imagination:** connect bounded candidate rollouts to advisory ranking,
   while keeping `acquisition.py` authoritative;
5. **P1 — Jev and agent interface:** expose latent summaries to Typed Jev and agent critics, then
   test ranking quality, repeatability, abstention, and decision-level utility;
6. **P1 — execution-log ingestion:** add raw-artifact, QC, and result-lineage checks inspired by
   Robin and Co-Scientist;
7. **P2 — stochastic transition training:** test IMLE-style or another mode-covering objective on
   independent biological units;
8. **P2 — closed-loop agent evaluation:** compare with and without the world-model ranking and with
   and without experiment-feedback ingestion under equal budgets.

Before promotion from design to active tool/model, all of the following must pass:

- independent-unit splits and a frozen data card;
- masked latent performance at least matching the declared representation baseline;
- action-conditioned transition performance against a no-action baseline;
- endpoint-specific calibration and interval coverage;
- mode quality checked against held-out multi-modal outcomes, not visual plausibility;
- abstention and applicability contract tests;
- no synthetic rollout satisfies a measured premise or updates belief state;
- raw execution logs and failed QC produce explicit non-success states;
- decision regret, unsupported advancement, justified deferral, cost-to-admissible-action, and
  provider/compute cost are reported separately;
- an equal-resource agent comparison shows a prespecified decision-level gain, or the simpler model
  is retained and the negative result is recorded.

**Status 2026-09-26: items 1 and 3 were run, and the latent model is not promoted.** On SciPlex3
(2250 conditions, five-fold splits by structure skeleton, three seeds), a JEPA encoder was trained
with co-expression-module masks and different-cell views of one condition, then paired with a
dose-gated transition head that is exactly zero at vehicle dose. Against the same head on PCA and
masked-reconstruction encoders it gained nothing (JEPA minus PCA -0.001 [-0.020, 0.018]). Against
structure retrieval it was no better on the registered metric and worse by 0.063 on direction beyond
the shared drug response, and it reproduced three of seven literature anchors. Per the rule above,
the simpler model (structure retrieval) is retained and the negative result is recorded in
`log/20260926/README.md`. The representation was not the bottleneck worth attacking first: the 24 h
signal in most compound classes is small against replicate noise (replicate agreement 0.04 at 10 nM).

The papers support this roadmap but do not authorize a general autonomous discovery claim. The
operational default remains the current qualified virtual-cell ladder and MAESTRO evidence loop.
