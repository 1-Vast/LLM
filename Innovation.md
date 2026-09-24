> **File summary**
> - **Path**: `Innovation.md`
> - **Purpose**: Research-design document: core innovation, secondary innovations, novelty, evaluation.
> - **Core points**: the agent remains primary and the virtual cell secondary; decision-directed repair of mechanistic contrasts is the sole candidate methodological contribution, not an established innovation; repair targets the missing biological conditions that make evidence interpretable; the audited 60-case replay is a development suite and does not establish novelty, biological attribution, or virtual-cell benefit.
> - **Interfaces / data**: `K=(h_i,h_j,Δ,q,a,𝒴,ρ,𝒟)` contrast object; `maestro-evaluate --policy ablation`; `intervention_profile.json`; literature links inline.
> - **Depends on**: `README.md`, `task.md`, `src/maestro/`, `src/virtual_cell/`, `data/evaluation/`.

# MAESTRO: Innovation Design Centered on an LLM Agent

Updated: 2026-09-15.

## Latest measured validation

The latest full maestro regression passed **865 tests**, with no failures, errors or skips.
The later [model/agent validation](research/model_validation_results.md) supersedes earlier
statements that no new model was trained. Twelve small neural fits (two input designs,
three seeds, primary and control-disjoint sensitivity runs), ridge/zero baselines and trained
model serving were executed on authentic raw SciPlex3 expression. Chemical structure plus
baseline RNA lowered held-out molecule error by 3.02% versus the matched neural comparator;
the post-primary disjoint-control sensitivity gave 6.64%. Neither run significantly beat
zero shift. This is limited single-study predictive benefit, not functional multimodal
validation. The existing chemistry derivative's original identity/licence remains unverified.

The 58-case agent replay matched the strong outcome-aware selector exactly; full-system
prediction shuffling changed no decisions or action sequences. Six engagement cases did not
establish superiority over catalogue expansion or independent living-cell mechanism discovery.
These negative controls weaken the current core claim. Publication-level novelty, a general
virtual cell and independent mechanism discovery remain research targets; engineering and
the small dose-anchored regressor are not relabelled as methodological innovations.

## Current maestro-environment revision

This later revision uses the actual `D:/anaconda/envs/maestro/python.exe` (Python 3.11.16).
The original 836-test baseline passed in that environment. The preceding integration suite records 851 tests,
zero failures/errors/skips; the live public smoke test passed both registered stops.
All 33 live calls across successful and failed attempts cost USD 0.03115490 at recorded rates. It supersedes the earlier Python 3.14
run as the environment basis; final test counts and live-provider failures are recorded in
`log/20260915/README.md` and `log/20260915/agent_revision/`.

Implemented: complete JSON action catalogues and tool/knowledge payloads reach the planner;
source aliases and overlapping evidence constrain exact coverage; multimodal information
visibility is explicit; live-provider dry replay uses bounded costs and frozen hypothesis IDs.
The provider's optional thinking switch prevents structured calls exhausting their entire output
allocation before returning JSON. Failures remain in the experiment record, with no template
substitution or invented measurements. See `research/CONTRACTS.md` for field semantics.

The candidate core contribution remains decision-directed biological mechanism-contrast repair.
The present changes repair necessary engineering and evaluation contracts. They do not establish
SOTA biological performance, a general virtual cell, functional multimodal benefit or publication-level
novelty. A matched-catalogue, matched-budget, independent-case comparison against strong adaptive
and exact controls remains necessary; the falsifiable protocol is in `research/README.md`.

## September 15 Implementation Reconciliation

This section is the authoritative reconciliation of the original design, the September 15
research revision, and the code that is actually executable. Later sections retain the study
history and detailed literature comparison. A statement marked **implemented** is supported by
source and tests. A statement marked **research target** remains a hypothesis or evaluation plan.

### Contribution and responsibility boundary

The only candidate core contribution is **counterexample-driven joint repair of measurement and
interpretation**. The main agent must turn a concrete failed decision obligation into a typed,
executable plan change, or retract an over-strong claim, and then score that repair only against a
subsequent qualified result. Counterexamples constrain the plan; they are not newly discovered
biological facts. Generic tool use, multi-agent organization, task graphs, active learning,
abstention, and virtual-cell prediction all have close prior art and are not independent novelty
claims.

The current implementation has one production orchestrator, not an implemented society of
specialist agents. It parses a natural-language task, maintains competing hypotheses and case
state, asks an LLM-backed router to select registered tools, calls a bounded virtual-cell adapter,
selects evidence under a declared budget, imports external results, and reflects before replanning.
Specialist subagents and learned repair policies are **research targets**. Their presence in the
target diagram must not be reported as current runtime behavior.

Responsibility is deliberately asymmetric:

| Component | Owns | Must not claim |
|---|---|---|
| Main agent | research intent, hypotheses, plan edits, tool choice, budget use, stop/defer, final action | numerical truth, an unmeasured result, or a biological mechanism from prose alone |
| Registered tools | typed data transformations, declared model calls, receipts and refusal codes | authority beyond their schema, source, task type, or evidence kind |
| Knowledge base | source identity, source cluster, access status, claim lineage, retraction and scoped retrieval | that literature is a case-specific measurement or independent validation of a constrained model |
| Virtual cell | applicability assessment and planning-only predictions for served endpoints | target engagement, functional inhibition, measured phenotype, mechanism confirmation, or clinical efficacy |
| Result admission | condition, quantity, independent-unit, quality and interpretation checks | promotion of predictions or retrieved prose to real measurements |

The evidence flow is `source -> retrieved constraint -> scoped context -> tool/model receipt ->
candidate decision -> external result -> admission gate -> hypothesis update`. Evidence kinds do
not silently upgrade along this path. `data/knowledge/research_sources.json` preserves the research
notes, source versions and access limitations. `data/knowledge/biological_constraints.json`
contains 79 loadable, source-linked constraints from 26 registered source records. The
pre-edit package contained 77 constraints and 24 sources; the earlier count of 30 was incorrect. The knowledge
package loaded successfully in the September 15 verification; it remains literature evidence, not
case truth.

### Executable structured handoff

**Implemented.** Each planned or observed round is serialized as `maestro.round.v1` with four
layers: evidence/comparability, world-model assessment, decision, and execution/update. The
contract rejects missing or malformed safety fields. The three required fields are:

| Field | Meaning and constraint | Failure behavior |
|---|---|---|
| `in_distribution` | Boolean decision gate in L2; only an explicit model value of `true` licenses in-domain use. Raw model uncertainty remains `null` inside the prediction payload. | missing/non-boolean is rejected; unsupported or unknown queries write `false` plus `abstain_reason` |
| `rejected[]` | Every unselected candidate in L3, with its selector-provided reason | non-array, empty reason, or chosen-and-rejected identity is rejected |
| `contradiction_flag` | Whether an admitted real result removed an entering hypothesis in L4 | non-boolean is rejected; `true` without a set-membership belief delta is rejected |

Tool outputs are strict JSON objects with `schema_version=1.0`, a structured `payload`, evidence
kind, input/tool/output hashes, state transitions, plan version and declared cost. The multi-step
`select_and_execute_many` policy exposes each prior structured receipt to the router, stops on an
explicit null or duplicate call, permits 0 to 32 calls, and shares one declared tool budget. Tool
cost is not token cost, laboratory cost, or turnaround time.

### Existing optimization, not a second solver

**Implemented through `src/maestro/acquisition.py`; no parallel optimization system is introduced.**
For required hypotheses `H`, an executable action set `S`, declared detection probability `p_a`,
and optional weight `w_h`, the exact selector maximizes

```text
sum over h in H of w_h * (1 - product over source components g of (1 - max p_a in selected g distinguishing h))
```

subject to: all selected action prerequisites are measured, every action belongs to the declared
candidate pool, action costs are finite and nonnegative, and `sum(cost_a) <= budget`. Ties minimize
cost, then action count, then identifier order. The objective is declared expected coverage, not
causal utility, information gain, biological validity, or experimental success. A missing
`detection_power` is explicitly recorded as an assumed-certain execution rather than hidden.

Source-overlap components are frozen over the executable menu. Within a component, max(p)
is a conservative union bound; conditional independence is assumed between components and
reported explicitly. Registered source aliases are resolved by the main agent and tool adapter.
Missing source IDs retain a named, unverified independent-trial assumption. This fixes duplicate
evidence inflation; it is not a new biological information-gain estimator.

Exact enumeration is supported only for at most 16 executable candidates. A larger pool returns
status `too_large`, executes nothing, and emits `exact_candidate_limit_exceeded` for every
candidate. The main-agent L3 handoff now preserves those exact refusal codes instead of replacing
them with a generic selector reason. `select_and_execute_many` remains the existing sequential
tool-composition policy; it is not an optimizer and does not change the expected-coverage
objective.

One optimization call uses one homogeneous, preregistered cost unit. Wet-lab studies should name
the scalar unit as wells, or use a preregistered conversion while reporting raw wells and
turnaround days separately. Record retrieval, model inference, wells, reagents and calendar days
are never interchangeable by default. The verified public dry run used one record-retrieval unit
and incurred 0 new wells and 0 turnaround days. It does not demonstrate laboratory savings.

### Biological anchor and residual identifiability

**Implemented as a fail-closed contract, not validated as a learned biological model.** A virtual
cell query is assessed for request validity, registered context/control, supported intervention
mode, checkpoint identity and endpoint expressibility before inference. Its prediction can rank a
declared action only when lineage matches, applicability is true, `in_distribution` is explicitly
true, the endpoint is served, and reliability has not been revoked. Prediction never satisfies a
measured premise.

The latent functional residual `r` follows the September 15 revision section 10 and
`src/virtual_cell/realization.py`. Without a measured functional-strength anchor or an independently
validated identifying measurement model, `r` supports ordinal comparison only. A monotone
reparameterization such as `r' = r^2` preserves observable responses after the paired response-map
change while changing the reported percentage. Same-drug self-combination, even under a declared
composition rule and validated dose window, is a structural constraint and does not by itself
license an absolute functional percentage. It does not identify arbitrary off-diagonal drug-drug
interaction either.

### Report-grounded latent representation and multimodality

The user supplied the 70-page v4 report during the current revision and authorized using its
research direction. Page 14 distinguishes State cell-set attention, Stack inference-time context
learning and Cell-JEPA latent prediction; pages 46-47 separately discuss functional realization.
The report does not define a standalone "potential attention" method. The supporting direction
is therefore task-qualified latent representation and measured functional realization, with no
invented attention architecture. Source identity and page mapping are retained in
`research/report_provenance.json`; current checks and boundaries are in `research/README.md`.

The existing low-cost scalar multimodal adapter now implements page 51's information-timing
boundary: optional `visibility` declares stage, available record IDs, acquisition cost and units.
Unavailable values are excluded before pairing and directional QC. Omitted visibility is marked
retrospective-only with unknown acquisition cost. These are caller declarations, not proof of
payment or trusted access control. No raw-image encoder, joint embedding or calibrated multimodal
risk predictor has been trained or validated. RNA, protein, occupancy, activity and morphology
remain different quantities; missing modalities are never imputed as observations.

### End-to-end dry-run evidence

**Verified on September 15 with public PRISM data and a reviewed deterministic planner template.**
This is retrospective software validation, not an autonomous-LLM or confirmatory biological
experiment. The chain was:

```text
public PRISM case
  -> data_profile receipt
  -> virtual_cell_query receipt
  -> applicability and endpoint refusal before prediction
  -> budgeted evidence decision and preregistered outcomes
  -> missing-result arm: awaiting_result
  -> public-fit import arm: result_quality_failed
  -> zero mechanism updates in both arms
```

The virtual-cell refusal was `query_unsupported`, with the concrete limitations
`readout_not_served:viability`, `control_dataset_unregistered:prism`, and missing registered input.
Both tool calls completed with structured receipts. Both round files contained
`in_distribution=false`, `rejected=[]`, and `contradiction_flag=false`. The missing-result arm made
no observation and stopped at `awaiting_result`. The imported PRISM fitted curve was retained for
audit but failed the independent-unit, biological-QC and matched-functional-assay requirements, so
it did not eliminate a hypothesis. API cost was USD 0 because the planner was a reviewed template.

Final repository-wide software acceptance records **836 tests, 0 failures, 0 errors and 0 skipped**
in `log/20260915/final_validation.xml`; the console record is retained beside it. The research
migration manifest accounts for all 765 former `research/` file records: 13 were mapped to the
source registry, 14 to the retained audit record, and 738 duplicate snapshots or generated
deliveries were discarded. The old `research/` directory was then deleted; the current revision restores a compact
`research/` directory for source checks, contract documentation and research targets; the user-supplied September
15 revision remains at its original `outputs/Innovation_深度研究修订版_20260915.md` path as a source
artifact.

### What is and is not established

**Established by software tests and the dry run:** strict layer contracts; structured multi-step
tool receipts; named tool/model refusals; exact expected-coverage selection up to 16 candidates;
safe refusal above the cap; source-linked knowledge loading; virtual-cell endpoint/applicability
gating; real-result admission boundaries; and no fabricated observation when a result is absent.

**Not established:** autonomous LLM scientific advantage; proposal-specific benefit over a strong
complete planner; a general virtual-cell model; calibrated benefit of the local State checkpoint
for MAESTRO decisions; biological validity of a generated mechanism; absolute residual-function
scale without measurement; raw-image multimodal benefit; prospective discovery; wet-lab closure;
independent human adjudication; or a sub-journal-level contribution. The high-value research target
is to show, on frozen independent cases and equal capabilities/budgets, that counterexample-driven
repair reduces wrong actions or cost relative to strong adaptive and exact controls, and that this
advantage transfers with the agent-generated patch rather than with a larger action catalogue.

**Research continuity constraint (user direction, 2026-09-12):** preserve the core innovation and the genetic-versus-pharmacological mechanism-contrast problem. Adjust implementation, supporting models, comparators, and validation first. The core-preserving remediation plan (recorded on 2026-09-12) reconciled the latest 64-page report and the independent contribution review, specified combinatorial optimization for larger action spaces, and recorded the authorized USD 5 total paid-test ceiling. No change of the core problem is warranted by the current evidence.

Based on README.md, task.md, the user-supplied reports including the v3 compilation, the current implementation audit, and the research sources linked below. This document defines the target method, not a statement that every component is implemented. The September 12 independent audit (see `log/20260912/README.md`) supersedes the earlier interpretation of the 60-case results. The robotics-informed solution and validation plan (same record) specified the corrective work and the 2026 prior-art boundary. New algorithmic advantages and biological results remain unverified.

## 0. Agent-First Direction and Scope

The target system accepts a user's natural-language question and datasets, retrieves relevant literature and database records, composes and executes registered bioinformatics and paper-derived model tools, consults a virtual-cell world model when applicable, and returns a reproducible answer with explicit evidence limits.

**Two architectural cores: the agent is primary; the virtual cell is secondary. One decision-making main agent coordinates multiple specialist subagents.** The main agent owns the research objective, global evidence state, hypotheses, workflow revisions, resource allocation, and final decision. Subagents perform bounded retrieval, biological data analysis, prediction, and verification tasks. In the target architecture, executable capabilities are exposed through versioned adapters under `tools/`; implementations and model weights may live elsewhere. The virtual cell is the applicability-bounded, revocable prediction core. Architectural importance does not imply an additional methodological novelty claim or independent decision authority.

This platform vision is broader than the first paper's evaluation task. Descriptive analysis, gene-set interpretation, and prediction requests should receive their appropriate workflow; they must not be forced into a genetic-versus-pharmacological mechanism diagnosis. The first falsifiable research claim remains cell-intrinsic mechanism-contrast repair. General autonomous biological problem solving is a longer-term capability target, not a validated result.

The detailed proposed architecture, tool contracts, operations-research formulation, and implementation gates were specified on 2026-09-11 and are summarized in `log/20260911/README.md`. Newly written or revised Markdown documentation uses English; original source titles and filesystem paths may retain their original language.

The research extension in [Downstream Task Specification](D:/MAESTRO/task.md) places the main agent at Intervention Design, reuses qualified representation/prediction methods, and adds provenance-aware multi-omics evidence and explicitly validated cross-scale bridges. Drug response, target identification/validation, drug combination/synergy, and toxicity are four downstream test families with separate qualification gates, not four core innovations. Intervention optimization chooses a biologically desirable action; evidence acquisition decides what to learn; decision-directed contrast repair connects them when interpretation prerequisites are missing. Multi-scale prediction and joint representations remain optional task-qualified support, not assumed capabilities of the current prototype.

## 1. Summary: One Candidate Core Contribution and Three Supporting Directions

**Candidate core contribution: decision-directed repair of mechanistic contrasts.** An LLM agent identifies a missing or invalid biological condition that prevents existing evidence from distinguishing action-relevant explanations, proposes a feasible change to the intervention or measurement plan, and evaluates whether new qualified observations repair that interpretive gap. English name: **Decision-Directed Repair of Mechanistic Contrasts**. The project keeps the MAESTRO name. The contribution is a falsifiable research hypothesis; generic replanning, task-graph repair, uncertainty routing, and multi-agent orchestration already have precedents.

**Operational definition:** the main agent identifies a specific failed interpretation or decision prerequisite, proposes a minimal change to a typed evidence workflow, obtains a feasible resource-bounded plan from an optimization tool, and checks the original repair promise against subsequently acquired real evidence. Minimality is relative to a declared candidate pool and edit/cost criterion. Neither an LLM's explanation nor a solver's feasibility certificate proves biological identifiability.

The research object is therefore the agent's **repair policy over evidence workflows**, specifically its treatment of intervention realization, mode comparability, endpoint validity, time alignment, and alternative explanations. Each repair must connect a documented interpretive failure to an observable follow-up and a bounded decision update. Hierarchical delegation, tool registries, virtual-cell prediction, and combinatorial optimization are supporting mechanisms. Their inclusion is not itself a novelty claim. The central question is whether this biological operation improves decisions beyond strong adaptive planning after equalizing tools, observations, ordinary prerequisite handling, and resource budgets.

| Contribution tier (not architectural priority) | Direction | Role |
|---|---|---|
| Candidate core | Decision-directed repair of mechanistic contrasts | LLM constructs, checks, revises the verification question and controls evidence acquisition and the decision loop |
| Supporting direction 1 | Functional intervention semantics | Turns nominal dose, measured functional quantities, mode, spectrum, and time course into concrete evidence prerequisites; no universally identified functional scalar is assumed |
| Supporting contribution 2 | Mechanism-contrast-driven, revocable virtual cell | The secondary architectural core; compares readouts and conditions within applicability, returning prediction and boundary rather than mechanism truth |
| Optional later direction 3 | Real-result-supervised repair-strategy learning | Test learning only after qualified trajectories exist and the frozen policy has demonstrated incremental value |

These directions serve one methodological claim; the table ranks research contributions, not architectural cores. In particular, the virtual cell remains the secondary architectural core. Supporting directions become contribution claims only after independent ablation. None requires a new foundation model, multimodal pretraining, or all-purpose drug discovery.

**Graph-support extension and implementation priority.** Use query-specific graph support, verified retrieval, and contradictory evidence to guide repair and qualify model influence. Graph completeness is not a universal extrapolation bound, and graph fusion is established prior art. Keep reasoning-graph updates distinct from predictor-graph updates. Unified evidence admission (F08) must precede scientific contrast validation (F03); the 2026-09-11 remediation record documents implementation in that order. Contract repairs do not establish biological validity. Combination tests must evaluate interactions and functional endpoints separately from expression reconstruction. The earlier literature findings and design decisions remain in the 2026-09-11 record.

**Latest research refinement.** The 2026-09-11 action, memory and topology review specified bounded skills, checked shared evidence, scoped and retractable memory, conditional specialist collaboration and failure diagnosis. It qualified Stack context transfer separately from unproven singles-to-combination synthesis, recorded local combination-data limitations, and identified residual context-truncation and joint-outcome-mapping problems. These strengthen the existing core claim; no production architecture or biological advantage is claimed by this design update.

**Core hypothesis to test: under the same LLM, tools, initial evidence, ordinary feasibility handling, and total budget, repair of biologically invalid or indistinguishable mechanism contrasts reduces unsupported development actions and the cost of reaching an admissible action beyond a qualified fixed procedure, reactive outcome-aware selection, and hypothesis-expansion/VOI planning.** The oracle is independently adjudicated and can admit several actions or justified deferral. Improvement against weak or deliberately disabled controls is insufficient.

**Cross-domain innovation is an explicit route.** The project may transfer an existing robotics method into an inadequately addressed biological setting; it need not invent every planning component anew. Cite the source method and define the transferred operation, biological assumptions, closest bioinformatics precedents, and measured benefit. Absence of an equivalent biological application in the checked literature supports a candidate transfer contribution, not an exhaustive claim of first use. A faithful transfer with a valid biological evaluation can be valuable without a new general-purpose algorithm.

## 2. Current Task and Research Boundary

First task: mechanism diagnosis and functional calibration when a genetic dependency and a pharmacological phenotype disagree. Reasoning unit: `target or necessary target set + intervention strategy + cell context + time and phenotype endpoint + existing evidence + unresolved prerequisites`.

The agent distinguishes or retains: incomplete functional perturbation, genetic/pharmacological mode non-equivalence, necessary multi-target activity, feedback compensation, context dependence, unknown mechanism — co-existing, never forced into one label. Final decisions: continue, revise realization, change mode, preserve or remove a multi-target activity, revise attribution, defer, or stop; applied only to the current program, never a permanent "valid/invalid target" label.

First round is cell-intrinsic; prioritize incomplete perturbation, mode non-equivalence, attribution. Complex compensation stays pending-evidence. Multi-drug, multicellular, immune, spatial settings need condition-matched measurements first. **The sequential state is the evidence already obtained and its uncertainty; different rounds usually come from different samples or wells, not one cell as a trajectory.**

## 3. Inheriting and Advancing the Two Research Reports

The table below preserves references to the original 68-page report and 23-page judgment. They are not page numbers in the newer 63-page v3 compilation.

| Source | Existing judgment | Treatment here |
|---|---|---|
| Report 56–57, 4.4 | LLM generates hypotheses, compiles to queries, compares divergence | Keep compilation; advance to a real evidence plan with prerequisite measurement, condition match, interpretation boundary |
| Report 58–59, 4.5 | Adversarial test, capability boundary, abstain | Auxiliary mechanism; after model exit the agent still retrieves and selects real evidence |
| Report 63–64 | World model vs decision-maker split, evaluate first | Keep short loop and external checks; depth set by measured cost and reliability |
| Judgment 2–7 | Cross-intervention diagnosis; MDA covers hypothesis, inference, value of information | Accept novelty constraint; general loop and VOI are not original algorithms |
| Judgment 9–10 | Functional need and realization strength | Biological anchor and decision entry of the core |
| Judgment 11–15 | Limited real evidence menu, hold-out, budget match, module swap | Evaluation design; do not assume paired data or collaboration in place |

New emphasis: an independently ablatable operation — when a mechanism contrast is indiscriminable, the LLM locates the failure, edits the question directionally, and states which real results constrain which judgment after the edit. Tightenings (merged): "query a KO" ≠ "predict under a mechanism" without the mechanism variable and intervention semantics; discrimination is an existing tradition; large divergence does not guarantee exclusion; conformal guarantees need matching assumptions; stepwise-success product is a conditional model, not a fixed decision-point rule.

**v3 integration:** retain modality-specific evidence, independently reviewed action sets, and the separation between prediction and measurement. Self-combination consistency does not generally identify a biological residual-function percentage; a direct measurement model or sufficient structural assumptions are needed. Multimodal disagreement is a candidate follow-up signal, not automatic model failure. These optional directions do not become prerequisites for the agent contribution. The September 12 audit gives the counterexamples and updates the version-sensitive OPAL evidence.

## 4. Why Use an LLM Agent, and How to Test Its Necessity

The valuable difficulty is pre-ordering: what language describes the intervention, whether two records mean the same functional change, which prerequisite a negative result constrains, what to change next. The LLM takes the continuous roles:

| LLM strength | Role in MAESTRO | Constraint and verification |
|---|---|---|
| Cross-source semantics | Distinguish binding, inhibition, removal, duration | Each extraction cites source and condition; unknown stays missing |
| Composition and analogy | Build competing explanations, spot missing dimensions | Analogy only proposes; give source and a weakening observation |
| Tool planning | Decompose divergence into measurement, control, endpoint, branch | Registered executable tools only; check parameters and limits |
| Feedback revision | Fix realization, observation, applicability, or mechanism | Keep old prediction; record edit target; no rewrite of history |
| Cross-case abstraction | Learn gap→repair mapping | Test on new targets, series, pattern combinations |

The target architecture has one main decision agent and several specialist subagents; the existing prototype is not yet this complete hierarchy. Statistical and optimization tools handle explicit numerical objectives and constraints, and the virtual cell handles supported prediction. The main agent interprets the scientific task, generates and repairs candidate workflows, evaluates evidence returned by specialists, and owns the final evidence-bounded decision. A deterministic evidence validator enforces update rules; no agent can bypass it.

This allocation is a design hypothesis, not proof that an LLM is necessary. Compare reviewed templates and non-LLM candidate generation with the same executor and optimizer. A validator can reject an infeasible action or unsupported evidence promotion; it cannot settle a biological dispute merely by applying a permissive hand-authored rule. Persistent scientific uncertainty calls for an informative measurement or qualified deferral. The audited terminal-prompt comparison does not justify handing all scientific decisions to rules.

### 4.1 Hierarchical Responsibility

| Role | Bounded responsibility | Output to the main agent |
|---|---|---|
| Main decision agent | Form the task contract and competing explanations; choose repair target; allocate resources; decide or defer | Versioned plan, decision rationale, accepted evidence, remaining limits |
| Evidence research subagent | Retrieve primary literature and database records; extract conditions and contradictory findings | Source-linked claims, condition tables, provenance and missing fields |
| Bioinformatics subagent | Inspect supplied data and execute suitable registered analysis workflows | Artifacts, effect estimates, QC and independent-unit metadata |
| Simulation subagent | Select supported virtual-cell/model tools and bind candidate-specific queries | Predictions with input/model lineage, applicability and calibration status |
| Verification subagent | Check sources, analysis validity, condition match and alternative explanations | Structured objections and repair counterexamples, not an independent final verdict |

Subagents may use multiple registered tools within their task and budget. They cannot change the global endpoint, authorize a stage decision, promote predictions to measurements, or overwrite accepted evidence. Parallel work is used only for independent tasks; a downstream analysis waits for required upstream artifacts. Disagreement triggers source/assumption checks rather than majority voting. Multi-agent execution must be compared with a resource-matched single-agent variant.

## 5. Core Mechanism: Construct, Check, and Repair a Mechanism Contrast

### 5.1 Basic Object

\[
K=(h_i,h_j,\Delta,q,a,\mathcal{Y},\rho,\mathcal{D})
\]

| Symbol | Content |
|---|---|
| \(h_i,h_j\) | Two competing explanations or factor combinations; others retained |
| \(\Delta\) | Key prerequisites and evidence gaps where they differ |
| \(q\) | Conditions for informativeness: functional perturbation, time match, specificity, detection power |
| \(a\) | Executable evidence plan, may include prerequisite measurement and a short branch |
| \(\mathcal{Y}\) | Predefined outcome classes, including failure, ambiguity, out-of-prediction |
| \(\rho\) | Interpretation rule: which variables each outcome constrains, how to update, when still indiscriminable |
| \(\mathcal{D}\) | Staged development action and its minimum evidence requirement |

"Minimize difference prerequisites" only trims unnecessary ones in the current set; it claims no global minimal experiment.

### 5.2 Construction

Ask which credible explanations lead to different actions (e.g., incomplete functional perturbation → fix realization; mode non-equivalence → evaluate another mode). The LLM identifies common and difference prerequisites and generates a plan that checks them; if explanations temporarily share a staged action, lower their fine-discrimination priority but retain them. The plan must state comparison objects, measured conditions, readout and time, prediction basis, possible results, interpretation boundary, cost — never only "do RNA-seq".

### 5.3 Check

Three levels: (1) execution and source — tool availability, field completeness, citation match, explicit condition, largely deterministic; (2) interpretation prerequisite — is the compared functional state measured, can the control handle alternatives, needs source evidence and domain review; (3) decision discrimination — would results change the action after noise and unknowns, else current value is limited. "Currently indiscriminable" is a formal output; record ability as unknown rather than fabricate exact value of information from LLM self-report.

### 5.4 Repair

The candidate biological operation: after an interpretive failure, generate a constrained edit from the specific cause. Routine tool retries and prerequisite completion remain available to all competent controls.

| Indiscriminable cause | Candidate repair | Interpretation boundary |
|---|---|---|
| Intervention realization unclear | Add proximal function, protein amount, realization-condition measurement | Realization-insufficient result constrains parameters, not the whole target mechanism |
| Endpoint similar across mechanisms | Change readout or time within capability | New readout needs relevance and detection-power basis |
| Genetic/pharmacological modes incomparable | Build matching mode/spectrum/time control | "Same-name target" ≠ functional equivalence |
| Tools cannot express the mechanism | Switch tool or use real measurement | No prompt-forced mechanism-specific prediction |
| Real result incompatible with explanations | Revise prerequisites, add testable factor | New mechanism tested from a new version; old prediction kept |
| No measurement resolves the divergence | Defer, state needed evidence | Language reasoning does not break unidentifiability |

State "which field changed, triggered by what, what discrimination expected"; re-checking is allowed, cost-free untestable stories are not. **The LLM composes and rewrites questions under existing capabilities; it invents no nonexistent results or devices. In retrospective evaluation all methods share one real evidence menu.**

### 5.5 Updating Evidence When Conditions Are Unmet

An unmet quality or prerequisite is not discarded: it enters the real-evidence base with an explicit constraint target (function→realization params; failure→detection/feasibility; matched+discriminative→stronger update to the mechanism contrast). Probabilistic realization marginalizes realization strength and measurement uncertainty over unknowns; version one may use reviewed sets and intervals to avoid unreliable exact posteriors.

### 5.6 Relation to Value of Information

With a credible distribution, reuse classic decision theory:

\[
R(b_t)=\min_d\mathbb{E}_{h,\theta\sim b_t}[L(d,h,\theta)]
\]

\[
\mathrm{NetVoI}(a)=R(b_t)
-\mathbb{E}_{y\mid a,b_t}[R(b_{t+1}^{a,y})]
-\lambda C(a).
\]

\(\theta\) includes realization and observation parameters; \(C(a)\) records resource and time. **These formulas are existing methods, not the innovation; the innovation is how the LLM generates and repairs \(a\), states \(y\)'s interpretation conditions, and what new evidence triggers revision.** Selection includes stop (net value insufficient) and defer (no feasible re-measurement); budget exhaustion alone proves no mechanism.

### 5.7 Combinatorial Optimization Supports the Repair Policy

Represent a proposed evidence workflow as a typed AND/OR graph: AND prerequisites require jointly available inputs or measured conditions; OR branches represent valid alternative tools or evidence paths. Select and schedule instantiated actions under cost, time, compute, assay compatibility, shared-control, source-dependence, and precedence constraints. The optimizer is a registered tool; it does not invent biological utility or decide which scientific question the user meant.

Use budgeted coverage/set cover only as a transparent baseline for a fixed, reviewed capability matrix. The proposed primary formulation is dependency-aware selection of short evidence bundles, followed by resource-constrained scheduling and replanning after observed outcomes. A MILP or CP-SAT solver can check a bounded candidate pool; small instances should also be enumerated to verify the formulation. Solver gaps concern this finite mathematical model, not the completeness of LLM-generated candidates or biological optimality.

Prerequisite measurements and confirmatory comparisons can be complementary: each may have zero immediate decision value while their combination is useful. Therefore decision utility need not be submodular, and adaptive-greedy approximation guarantees cannot be assumed. [Golovin and Krause, revised adaptive-submodularity paper](https://arxiv.org/abs/1003.3967v5) supplies conditions to examine, not a ready-made guarantee for this task. [PDDLStream](https://arxiv.org/abs/1802.08705) motivates separating semantic plan proposals from specialized constraint checks; [resource-constrained scheduling](https://developers.google.com/optimization/scheduling/job_shop) supplies established execution machinery.

The intended loop is `main-agent proposal -> specialist evidence/constraint checks -> solver plan or diagnostic -> main-agent targeted repair -> execution -> validated observation -> original-promise assessment`. A failed measurement is still a real observation; scheduling a measurement never pre-certifies its success. Potential mechanism updates are conditional on its realized QC and interpretation conditions. The detailed design distinguishes expected evidence availability, actual condition satisfaction, and final decision authorization.

### 5.8 A Repair Promise and Three Explicit Monitoring Levels

Attach a versioned record to each proposed edit: `contrast_id, failed_condition, evidence_refs, competing_explanations, proposed_edit, observable_outcome_classes, permitted_updates, unresolved_alternatives, cost, expiry_condition`. These are proposed extensions of the existing contrast/check/repair ledger, not new runtime APIs already implemented.

Check three different properties: **execution validity** (the action ran on the specified inputs); **measurement validity** (the result passed the relevant QC and condition match); **interpretation validity** (the qualified observation supports the specified update without excluding unresolved alternatives). A passed execution check cannot imply a measured condition or resolved mechanism. Retain `pending`, `supported`, `contradicted`, and `inconclusive` outcomes rather than equating plan adoption with gap closure.

Compile a small number of reviewed recovery branches for known failures; invoke bounded agent replanning when actual evidence invalidates those branches or exposes a new interpretive gap. Preserve the original contract and measured history. Revisions change a prospective plan, not historical outcomes or held-out scoring criteria. Recovery budgets must include the up-front compilation cost, later calls, failed measurements, and prerequisites.

## 6. Supporting Directions in Detail

### 6.1 Functional Intervention Semantics

`mode + nominal dose + measured functional state + protein abundance + spectrum + time course + context + evidence source`, each value tagged measured/estimated/unknown with its readout. Functional state starts small; add dimensions only when needed. This layer is the repair input; its claim holds only if verified on identified missing variables, changed next experiment, and dropped wrong actions — fields or embeddings alone do not carry it.

Keep RNA abundance, protein abundance, occupancy, proximal activity, viability and selectivity as different quantities. Pan-essentiality does not resolve target attribution, and low baseline RNA does not prove zero target-mediated activity. Unknown values must remain unknown; self-combination equality or a high graph-coverage score cannot manufacture biological identification.

### 6.2 Virtual Cell: Auxiliary Predictor

Request binds a concrete mechanism contrast and plan (context, intervention, readout, time). Output: `prediction or interval + calibration basis + supported variables + applicability domain + unsupported requests and reasons`. Roles: compare readouts/times, judge signal-vs-noise, assist short-branch comparison. A general \(p(y\mid a,c)\) ≠ mechanism-conditioned \(p(y\mid a,c,h)\); only a model supporting the mechanism and functional variables (or a validated adapter) gives mechanism-discriminating prediction, and expression change is not efficacy/synergy truth without survival/function support. Applicability is per-contrast; agreement of several models is not verification. Dependency is revocable: on out-of-scope extrapolation, miscalibration, or unsupported variable, lower influence and switch to tool/real evidence/re-measurement; predictions stay in planning, never enter the evidence base. Without a virtual cell the agent still works; if no gain after adding one, drop the contribution claim.

### 6.3 Optional Later Real-Result-Supervised Repair Learning

Object: `evidence → contrast → cause → repair → real result → update/decision`. Version one uses a frozen LLM; later, domain-reviewed real results train a small adapter or preference policy over add-prerequisite / change-readout / change-mode / revise-mechanism / re-check / defer. Signal comes from comparable plans under the same evidence state; failure cases include unsupported prerequisites, infeasible experiments, denying targets without verified perturbation, model-as-measurement, baseless mechanism addition, repeated deferral. Reward uses decision loss, waste, cost, contrast completeness — not another LLM judging narrative. A single snapshot is not a multi-step trajectory for offline RL; real trajectories need action, observation, cost, source.

## 7. Example: Same Negative Phenotype, Different Handling

Illustration only, not a finding or validated plan. Initial evidence: genetic perturbation lowers survival; a nominal inhibitor gives no matching phenotype. Candidate explanations: insufficient inhibition, protein removal changed an unaffected function, spectrum/attribution issue. The agent picks the realization-vs-mode divergence; the check finds only dose and endpoint survival, no functional-inhibition trajectory, so "negative phenotype supports mode non-equivalence" lacks a prerequisite.

**First repair:** add proximal functional measurement in the phenotype window, with a branch:

| Real result | Update and next step |
|---|---|
| Insufficient functional change | Strengthen realization-insufficient; evaluate fixing condition; cannot stop program |
| Sufficient change, still no phenotype | Lower realization-insufficient; enter mode/spectrum contrast |
| Poor measurement quality | Improve or change readout; retain uncertainty |

**Second repair:** if acute removal and inhibition durations mismatch, change the comparison; extra phenotype difference prompts orthogonal/rescue verification. One stronger BRD4 degrader or one failed rescue does not prove a specific mechanism. Two "ineffective" endpoints can trigger different actions via different functional-realization evidence; test whether the agent uses this, not a drug's classic mechanism. The Judgment p.14 AKT/BET case is not re-confirmed here and cannot serve as an unseen-target blind test.

## 8. 2026 Literature Basis and Novelty Boundary

Counted by formal year; 2026 preprints marked. The table lists existing abilities and operations this design must add.

| Original work | Existing ability | Overlap to avoid |
|---|---|---|
| [HUME, RSS 2026](https://www.roboticsproceedings.org/rss22/p181.html) | Generate, verify, update uncertain hypotheses, feed planning | Joint representation borrowed; open hypothesis precedented |
| [When to Act, Ask, or Learn, RSS 2026](https://www.roboticsproceedings.org/rss22/p142.html) | Distinguish ambiguity from capability gap, calibrate | Routing of uncertainty/gap/inapplicability borrowed; not original |
| [ELVIS, RSS 2026](https://www.roboticsproceedings.org/rss22/p182.html) | Branches + uncertainty reward bound imagination error | Short rollout, revocable dependency; no robot-reward extrapolation |
| [Counterfactual VLA, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Peng_Counterfactual_VLA_Self-Reflective_Vision-Language-Action_Model_with_Adaptive_Reasoning_CVPR_2026_paper.html) | Post-action rollout and correction | Pre-action check borrowed; language counterfactual ≠ causal ID. Preprint 2025 |
| [When to Think and When to Look, CVPR 2026](https://proj-visual-thinking.jing.vision/) | Re-attend visual evidence when uncertain | Migrate to missing-prerequisite re-check. Preprint 2025 |
| [Value of Information, ACL 2026](https://aclanthology.org/2026.acl-long.1987/) | Link decision gain with query cost | Decision-directed selection; VOI not new |
| [When Silence Is Golden, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/7718914dfe7d5a657bf6261b5f431021-Abstract-Conference.html) | Joint abstention and reasoning training | Defer in learning/eval; prompt caution ≠ calibration |
| [GOLLuM, Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01283-z) | GP marginal likelihood joins language and surrogate | Supervise probability with data; do not rename as diagnosis innovation |
| [Model Discovery Agent, 2026 preprint v4](https://arxiv.org/html/2608.09696v4) | LLM mechanisms, Bayes, EIG, task VOI | Closest baseline; "open mechanism + VOI" insufficient to differentiate |
| [Learning the ARTS of Search, 2026 preprint](https://arxiv.org/html/2606.21891v1) | Checks execution, splits hypothesis vs implementation | "failure ≠ hypothesis error" precedented; prove biological increment |
| [VCR-Agent, 2026 preprint](https://arxiv.org/abs/2604.11661) | Mechanism graph, retrieval, verifier | Graph/prereq exist; must add real-evidence action and repair |
| [Robin, Nature 2026](https://www.nature.com/articles/s41586-026-10652-y); [Co-Scientist, Nature 2026](https://www.nature.com/articles/s41586-026-10644-y) | Hypothesis generation, critique, workflows | Base abilities, not differentiation |

MDA v4 §3 and A.9 discuss task-related VOI; VCR-Agent already structured prerequisites — do not overclaim. **The sought difference is a joint operation: for unrealized or incomparable intervention-semantics conditions, the LLM auto-generates and revises an evidence plan with interpretation constraints; proven by equal-resource decision gain and cross-case repair.** Not guaranteed "first"; if removing repair leaves performance unchanged, or fixed rules match, lower the core claim.

### 8.1 Robotics Transfer Candidates Checked on 2026-09-12

| Primary source and status | Transfer into MAESTRO | Evidence boundary |
|---|---|---|
| [AgentChord, RSS 2026](https://www.roboticsproceedings.org/rss22/p180.html); [method and limitations](https://arxiv.org/html/2605.11951v1) | Compile evidence workflows with a few anticipated recovery branches; monitor actual execution | Recovery graphs are borrowed; assay success cannot be assumed, and biological interpretation can require a new measurement |
| [HUME, RSS 2026, full text](https://arxiv.org/html/2607.06501v1) | Treat missing intervention conditions as uncertain hypotheses and plan their verification | Its stated assumptions about sufficient verification conditions motivate testing biological assay sufficiency explicitly |
| [Uncertainty-Aware Policy Steering, RSS 2026](https://www.roboticsproceedings.org/rss22/p142.html) | Distinguish ambiguous objectives, missing evidence and unavailable capability | Calibration must be re-established for the biological decision pipeline |
| [Do What You Say, ICRA 2026 publication record](https://research.nvidia.com/publication/2026-06_do-what-you-say-steering-vision-language-action-models-runtime-reasoning-action) | Compare the promised scientific measurement with the actual tool and assay output | Reasoning-action consistency is not evidence that the scientific premise is true |
| [Motion-Uncertainty-Aware Next-Best-View, RSS 2026](https://www.roboticsproceedings.org/rss22/p176.html) | Select a feasible next assay/readout/time over plausible biological states | Decision relevance replaces geometric coverage; valid outcome models or reviewed sets are required |
| [ELVIS, RSS 2026](https://www.roboticsproceedings.org/rss22/p182.html) | Limit reliance on imagined branches as model uncertainty increases | Do not import its critic-based control mechanism as a biological uncertainty guarantee |
| [HALO memory retrieval, RSS 2026](https://www.roboticsproceedings.org/rss22/p010.html) | Retrieve task-relevant evidence without flooding the current decision state | Sparse memory must preserve the full public task contract and unresolved contradictory evidence |
| [SafeMem, September 8 preprint](https://arxiv.org/abs/2609.08444v1) | Use persistent relational memory to inform risk and replanning | The arXiv record lists CoRL 2026; proceedings were not independently checked. An LLM risk score is not biological calibration |

The selected transfer is **recovery-augmented planning for biological interpretation**, with active measurement selection and qualified predictive support. Generic workflow recovery and structured memory already occur in biology: [BioMaster, Patterns 2026](https://pubmed.ncbi.nlm.nih.gov/42630761/) and [PRAXIS, 2026 preprint](https://arxiv.org/abs/2605.23169) are additional close neighbors. The transfer claim must concern the specified mechanistic decision task, not merely introducing task graphs, memory or debugging into bioinformatics. The detailed plan distinguishes faithful robotics transfer, biological adaptation and empirically unverified additions.

The 2026-09-11 platform review also checked [CellVoyager, Nature Methods 2026](https://www.nature.com/articles/s41592-026-03029-6), [GeneAgent, Nature Methods 2025](https://www.nature.com/articles/s41592-025-02748-6), and [BATCHIE, Nature Communications 2025](https://www.nature.com/articles/s41467-024-55287-7). Autonomous biological data analysis, database-backed claim verification, and adaptive batch experimentation already have direct precedents. MAESTRO must demonstrate its intervention-condition repair increment rather than claim these capabilities as new. The detailed design separates hierarchical execution, candidate generation, optimization, and predictive assistance in evaluation.

## 9. How to Prove Benefit Comes from the Agent Core

### 9.1 Core Evaluation Scenarios

Three types, reported separately: (1) **prerequisite missing** — same negative result, different realization/comparability, different next step; (2) **observation equivalence** — multiple mechanisms indistinguishable, but menu holds a justified other readout/time/mode; (3) **insufficient explanation set** — qualified evidence uncovered, needs revision or defer, not forced classification. Also keep no-repair, no-extra-measurement, and truly-unsolvable cases to block always-repair / always-experiment / always-defer cheating.

### 9.2 Fair Evaluation Environment

All strategies share initial evidence, sources, tools, real-result menu, budget. Retrospective experiments reveal only existing results; missing ones are not filled by the virtual cell. A public panel proving only response prediction proves only that layer. Retrospective "discriminability repair" may compose menu measurements and revise the plan; new conditions outside the menu are pending prospective, not scored speculative. Keep final and adaptation-stage results separate; group by source, target family, series; treat multiple citations of one experiment as a source cluster. Admit pretraining contamination cannot be excluded. Endpoints, action set, minimum evidence freeze before testing; the agent may revise the next question, not the criterion.

### 9.3 Required Controls and Ablations

| Control | Increment tested |
|---|---|
| Rule procedure and budget-matched review | Whether a complex agent is warranted |
| Same LLM/tools, ordinary suggestion | Whether structured mechanism contrast adds value |
| Simple predictor + EIG/VOI; MDA-style expansion | Whether gain exceeds general active design |
| Compilation and ordinary prerequisite/retry handling kept, biological contrast repair off | Whether the specific biological repair operation is necessary |
| Qualified biological workflow vs faithful robotics recovery-graph transfer | Whether the cross-domain transfer itself provides a biological benefit |
| Faithful robotics transfer vs explicit biological interpretation monitoring | Whether the domain adaptation adds value beyond direct transfer |
| Repair replaced by same-budget random legal edit | Whether gain is only from retrying |
| Single main agent vs main agent with specialists, matched total resources | Whether delegation improves execution independently of repair or extra calls |
| Fixed candidate pool: coverage/greedy vs dependency-aware bundle optimization | Whether optimization handles prerequisites and complementary actions better |
| Frozen candidate pool vs agent-generated/repaired candidate pool | Separate semantic workflow construction from solver quality |
| Remove functional semantics or prerequisite constraint | Whether intervention semantics changes update/action |
| No / always / applicability-scoped / shuffled virtual cell | Net contribution of auxiliary model and its applicability |
| Frozen vs learned repair, unseen-entity split | Whether secondary learning transfers |

Do not grant MAESTRO stronger tools or extra truth and attribute the gap to reasoning. A modeled upper bound on missing semantics may measure loss but is not a deployable method.

### 9.4 Main Metric and Failure Criteria

Main metric: **wrong development-action rate at a fixed real budget**. Acceptable actions pre-defined by independent review, allowing multiple actions and suitable defer; report wrong advance, wrong abandon, defer coverage, over-deferral separately so "reject all" cannot win. Auxiliary: cost to same standard, repair-success rate, waste ratio, wrong-update rate, hold-out calibration/prospection. Repair success needs real result or review, not self-assessment. Unit is case or target cluster, not cells or calls; seed is algorithm variance, not replicate. The core claim weakens or fails if: fixed rule or same-budget retry matches; only explanation score rises while action rate holds; no drop without directed repair; gain only in classic cases or one simulator; system cannot run without virtual cell while gain is all predictor; repair relies on post-changing criteria or pseudo-truth completion.

### 9.5 Audited Development Measurement (2026-09-12)

The 60-case package uses DepMap 24Q2 and PRISM Repurposing 19Q4 records. The September 12 independent audit (see `log/20260912/README.md`) reproduced all six offline arms and recorded 161 passing tests, but found BRAF and EGFR in both development and test. The cases were also used in repeated debugging. Treat this package as a development and contract-compliance suite, not a gene-disjoint confirmatory benchmark. A timestamped frozen evaluation protocol is required before calling a new experiment preregistered.

| Policy | Supported decisions under the current convention | Mean evidence cost |
|---|---:|---:|
| Fixed procedure | 40/60 | 1.833 |
| Prediction-value heuristic | 56/60 | 1.667 |
| Directed repair | 60/60 | 1.167 |
| Repair disabled | 40/60 | 0.833 |
| Random legal edit | 43/60 | 1.700 |
| Reactive outcome-aware selection | 60/60 | 1.167 |

The last policy is re-evaluated after observations; it is not a strictly frozen one-shot plan. Its tie with directed repair leaves the distinctive contribution unproven. Removing repair also removes useful prerequisite handling, so the 20-case drop does not isolate biological contrast repair. Strong controls must retain ordinary feasibility handling.

| Provider arm | Correct | Over-deferral | Invalid submission | Tokens |
|---|---:|---:|---:|---:|
| Ordinary LLM | 29/60 | 31 | 0 | 452,004 |
| MAESTRO LLM | 30/60 | 20 | 10 | 709,663 |
| MAESTRO LLM with rule decisions | 60/60 | 0 | 0 | 322,042 |

The completed provider reports total 987 calls and 1,483,709 tokens; earlier probes and aborted runs are additional campaign cost. All three provider arms acquired oracle-decisive evidence in the 40 cases requiring additional informative evidence. The other 20 cases do not establish acquisition capability. These provider runs were inspected, not repeated by the independent reviewer.

Terminal information is not matched: the LLM's final prompt can lose the public outcome declarations when no executable actions remain, while the deterministic rule still reads them. Consequently, these results do not establish that the LLM is intrinsically poor at terminal decisions or that scientific authority should move to the rule. Format errors, convention disagreement, scientific uncertainty and information loss require separate diagnosis.

Some generated biological interpretations exceed what the source assays identify. Reachability and alternative-path waste scoring also have reproducible counterexamples. The 60/60 result therefore demonstrates conformity to the current software convention, not correct mechanism attribution. This evaluation explicitly disables the virtual cell, so it provides no evidence for predictive assistance.

**Claim status:** useful reproducible engineering progress; no established methodological advantage over strong adaptive selection, no independent biological attribution result, and no demonstrated agent–virtual-cell decision gain. The original run artifacts remain the historical record. The robotics-informed plan defines the corrections, matched controls and new held-out evaluation needed to change this status.

### 9.6 Corrected Instrument and Its First Measurement (2026-09-12)

The defects above were corrected in code and pinned by regression tests written to fail first; the 2026-09-12 execution report lists every change and its location. The immutable public contract is now separate from the shrinking executable menu and reaches every terminal policy at zero budget; RNA abundance, protein abundance, target occupancy, proximal activity, viability and selectivity are distinct typed quantities with no automatic substitution; target genes are allocated to one partition globally before balancing; the comparator is selected from release metadata rather than from the response it will return; and one shared feasibility rule decides execution, scoring and planning, so a decision the scorer calls reachable is a decision the environment will actually execute.

The 60-case package is frozen as development and regression data. A corrected 58-case package was rebuilt from the same releases: 40 target genes with an empty development/test gene intersection, typed quantities, an outcome-blind menu, and eight comparator records that reveal as quality-failed and therefore license nothing.

| Policy | Supported decisions | Mean evidence cost | Mean redundant cost |
|---|---:|---:|---:|
| Fixed procedure | 43/58 | 1.793 | 1.379 |
| Prediction-value heuristic | 52/58 | 1.672 | 0.845 |
| Directed repair | 58/58 | 1.259 | 0.328 |
| Repair disabled | 43/58 | 0.741 | 0.328 |
| Random legal edit | 44/58 | 1.672 | 1.190 |
| Reactive outcome-aware selection | 58/58 | 1.259 | 0.328 |

Directed repair and reactive outcome-aware selection again emit **identical ordered acquisitions in every case**, now on an independently constructed package. An exact enumerating optimizer over the same public contract also selects the same bundle in 58 of 58 cases, and matches an independent brute-force search in 58 of 58. The evidence-selection problem in this package is therefore solved exactly in milliseconds, and the tie is a property of the action grammar — one interpretation field per action, unit costs, a two-purchase budget, and a declared outcome mapping on every separating action — not of the repair implementation. Under that grammar the two policies are the same policy, so **this benchmark family cannot test the distinctive contribution**, and no solver beyond enumeration is warranted. Separating them requires a richer grammar: several suppliers of one premise at different cost and interpretive strength, budgets that bind before a premise is resolvable, and continuations that depend on the observed result. That construction is the next piece of work, not a claim already made.

### 9.7 Typed Premises and the Qualified Instrument (2026-09-13)

Five further contract defects were reproduced independently against the code and then repaired,
with 47 regression tests added and the suite moving from a freshly rerun 179 to 226, no regressions.
The [2026-09-13 day record](D:/MAESTRO/log/20260913/README.md)
records each defect, its counterexample and its fix location. Three of them bear directly on the
repair operation. A prerequisite field is no longer discharged by its own name: each case declares
what the field must mean, and admission compares that declaration against the quantity, entity,
site, units, context, time and quality the supplying record actually carries. On the rebuilt
58-case package this is measured both ways — the correctly typed supplier discharges the premise in
27 of 27 cases, and retyping only that supplier, changing no name and no record, blocks the
dependent action in 27 of 27. A truncated search no longer reports a proven optimum. Evidence that
arrives after one hypothesis remains is no longer discarded, so a contradiction is reported as a
contradiction rather than scored as a resolved contrast.

This does not add a contribution. It is the same repair operation with a premise that can be checked
against a measurement, which is what "directed" was always meant to mean.

The secondary core was then re-evaluated under a protocol declared before scoring
([follow-up report](D:/MAESTRO_pruned_log_20260914/20260913/real_path/REPORT.md)). **Two earlier statements are
withdrawn**: that State combined with the shared response reached r 0.304, "94% of an attainable
ceiling of 0.324", and that the scores bound generalization from above. When the measured target and
every fitted comparator use disjoint vehicle wells, the development-mean predictor falls from r 0.21
to 0.03 and becomes worse than predicting no change, so most of the earlier combined agreement was
shared vehicle noise. State's own agreement survives (r 0.20 to 0.22), and one development-fitted
scale lowers squared error below no change by 0.000205 (drug-bootstrap 95% interval -0.000230 to
-0.000181, about 4%). Raw State remains worse than no change, largely through sampling noise of its
basal cells: querying 64 cells per condition instead of the observed count lowers its raw squared
error from 0.0087 to 0.0051. Zeroing or permuting treated expression leaves every prediction bitwise
unchanged. NCI-H596 is not among the five contexts this checkpoint was evaluated on as held out, so
these are retrospective scores with unknown, probably in-sample, pretraining overlap: neither
zero-shot nor a bound. The [day record](D:/MAESTRO/log/20260913/README.md) keeps the original numbers.

It also settles what the secondary core may be used for here. The eight-axis match to the
genetic-pharmacological benchmark fails on endpoint, perturbation representation, dose, context,
time, controls and feature schema, and chemical identity matches lexically only. The framework now
refuses the corresponding bridge by contract — the RNA-to-viability connector returns
`quantity_mismatch`, `entity_mismatch`, `units_mismatch` and `no_validation_basis` — instead of
leaving the refusal to a reader's judgement. **No transcriptomic prediction may be read as viability,
target engagement or genetic dependency in this workspace.**

A third block asked the question that precedes accuracy, and it constrains the secondary core further
([mechanism analysis](D:/MAESTRO_pruned_log_20260914/20260913/mechanism/MANUSCRIPT.md), with the declaration frozen by
digest before any outcome existed). The endpoints a mechanism decision needs here are gene sets: ERK
feedback output, the mitotic programme, an integrated-stress panel. The checkpoint emits 2000 highly
variable coordinates, and those coordinates carry 2 of 41, 2 of 10, 2 of 60 and 0 of 5 of their genes;
a score computed only from them tracks the measured full-space endpoint at r = 0.21, 0.37 and 0.02.
**The endpoint is not representable in this model's output space**, a refusal that is available before
any inference and independent of calibration, and the audit returns it by name
(`endpoint_not_representable_in_output_space`). The measured pillars were assembled for the same
conditions from competition binding, the c39 transcriptome and PRISM: at the exposures the screen
actually used, 19 of 124 eligible conditions occupy only the designated target while 98 occupy at
least one other measured target, and MAPK-directed compounds suppress the ERK-feedback signature in a
dose-ordered way (mean z -0.19, -0.94, -1.29) while interferon and mitotic controls do not. The
compound-specific part of that relation is not established: the declared bootstrap excludes zero but
the declared within-dose permutation does not (p = 0.168), because occupancy is nearly determined by
dose. Movement at 24 h is unrelated to 5-day viability AUC (Spearman -0.02 over 26 compounds), which
is one more reason the RNA-to-viability bridge stays refused.

Finally, the submission contract that produced the 2026-09-12 invalid-submission rate was repaired:
`decision_ready`, `additional_evidence_available` and `required_missing_premises` are now three
fields rather than one boolean, because a policy that can decide while the menu is still open had no
way to say so. Re-scoring the frozen responses offline, at no cost, rescues 21 of 116 submissions,
all of them in cases with an open menu. The terminal-information comparison itself does not move:
paired discordance stays 10 versus 2, McNemar exact two-sided p = 0.0386, under both contracts.

### 9.8 The discriminating instrument and its first measurement (2026-09-14)

The recorded blocker was that the action grammar could not separate a check-and-repair
loop from a reactive selector, so the core claim was unidentifiable rather than
supported or refuted. That blocker is now a measured statement rather than an open
problem. `src/evaluation/contingent.py` adds the missing grammar and the operation that
plays on it, and `src/evaluation/contingent_suite.py` scores every policy on ten
declared finite models against the exact reference in `evaluation.adaptive_reference`.
The full report is `D:/MAESTRO_pruned_log_20260914/20260914/contingent/REPORT.md`.

Four results, each computed rather than asserted:

1. **The recorded tie is a property of the grammar.** On a family that mirrors the
   frozen package, every policy attains the optimum. Add a second supplier of the same
   premise at a different price and reliability, hold the budget at the reliable route's
   cost, and the exact optimum is 3.000 while the recorded strongest control pays 3.500
   and defers on half the probability mass. The exit criterion the 2026-09-13 record
   set — a provable divergence on a constructed instance, before any real data is
   spent — is met.
2. **Required lookahead depth tracks the repair structure.** On a chain of premises,
   each with a fragile and a reliable supplier, the depth that attains the optimum is
   one more than the chain length (3 at two links, 4 at three), and every shallower
   policy — including the reactive control — acquires nothing and defers with
   probability 1. A fixed horizon is therefore a choice about which instances to solve,
   not a bound that holds.
3. **The recorded baseline maximised the wrong objective.** A control that buys
   expected entropy reduction per unit cost pays 3.000 where pricing the decision pays
   2.000. Value of information computed against the decision rule is established prior
   art and is cited as motivation, not claimed as an addition.
4. **A new metric, and an uncomfortable value for it.** `unsupported_attribution`
   measures the probability mass on which a policy returns a causal attribution while
   a supported explanation would have called for a different action. On a family where
   isolating the two causes costs more than acting on the prior, **the exact reference
   itself returns an un-isolated attribution on 68% of the mass**. Under the loss
   convention used since 2026-09-12, attributing on the prior is cheaper than measuring.
   An ambiguity-aware repair that refuses that attribution pays 1.52 expected loss for
   the refusal. The evidence boundary stated in this project's documentation is
   therefore not enforced by its own loss function; it has to be a constraint on the
   policy, and this family is what makes its price checkable.

What this does not establish: that any family corresponds to a real decision (the real
grounding is a separate workstream); that the ambiguity-aware policy attains the
reference where the exact search is intractable (here the reference is exact and cheap,
and the policy is measured against it rather than substituted for it); and that the
loss convention should stay as it is — item 4 is evidence that it should not. Two of the
ten families separate nothing, and `unsupported_attribution` fires on exactly one; both
are reported as null results in the instrument's own record.

### 9.9 Late-block update: the operator set, and what is now measured (2026-09-13)

Four further blocks were written in the same session and are recorded in
`D:/MAESTRO_pruned_log_20260914/20260913/`. They change the *operator* the claim rests on and the *credit rule* that
decides whether the operator counts, not the claim, the task, or the asymmetry between the
two architectural cores. A paper-shaped synthesis of all of them is
`D:/MAESTRO_pruned_log_20260914/20260913/synthesis/MANUSCRIPT.md`; every number below is reproduced by
`D:/MAESTRO_pruned_log_20260914/20260913/verification/verify_blocks.py`.

**The grammar the claim needs.** An action may now declare an *interpretation gate*: the premise
without which it is legal and uninterpretable, returning a qualified outcome that moves no
belief. Suppliers declare a *detection power*, the chance they return a qualified result at all,
so two assays answering one question are no longer distinguished by price alone. A
`CompositionRule` admits a two-stage plan that shares a control and therefore costs less than the
sequence, while carrying its own gate-failure branch. The exact reference
(`evaluation.adaptive_reference`) scores all of it, and reports bounds rather than an optimum
when a search truncates.

**Two separations, each with the control that removes it.** The action-space value of the
composition is 0.60 of expected loss on the interpretation-gated family and 1.00 in the ceiling
case, and it is exactly 0.00 with a zero saving and 0.00 when the readout needs no gate. The
search-rule gap is separate: on a family with two gates of different cost and reliability a
price-first reactive control pays 1.00 more than the optimum, and on a family where a decisive
prior makes acquisition worthless it spends 2.20 that the optimum does not.

**The real package, both ways.** On `real_v3` the retyping repair is worth **0.000 in 58 of 58
cases**, and that is a bound on every policy restricted to the unrepaired menu at any depth,
because the menu is redundantly decisive. Reading each case's own prerequisite as an
interpretation gate — one field per readout, no case file edited — makes the composed plan
admissible in 27 of 58 cases, and under a declared shared-control saving of 0.5 its exact value
is strictly positive in **21 of 58** at the shipped budget (median 0.5) and in 21 of 58 at
budget 1.5 (median **2.5**, a feasibility gain rather than a discount), with **exactly 0 cases
at a zero saving**. The per-case saving threshold is 0.05 for 21 cases and 1.05 for 6. The
saving is a declared laboratory quantity that no local data measures, and the sweep says so
rather than assuming a value.

Read beside the one local measurement of that premise rather than after it: the frozen NCI-H596
engagement table gives the gate a qualification coverage of **0.1129** at condition level and
0.1135 at drug level, with a break-even first-stage cost below **0.4515** of the loss it avoids,
and decision relevance 0.7865 where the premise is measured
(`D:/MAESTRO_pruned_log_20260914/20260913/repair_v2/gating_measure/gate_economics.json`). The composition certificate
therefore prices the operator under declared economics, and on that real record the correct
action is deferral rather than composition.

**Credit is now a certificate rather than a comparison.** `src/maestro/licence.py` records four
gates per repair-produced measurement — typed input validity, declared outcome support, context
and time identifiability, and incremental utility over the exact menu-only optimum — and
separates `updates_licensed` (gates i-iii: a qualified result may update the contrast) from
`repair_credited` (all four: the repair earned something the menu did not already allow). On the
frozen cases the typing repair licenses 27 of 27 updates and is credited 0 times; the
composition repair is credited 21 times. The two audit rates — unlicensed updates, and readouts
bought without a passing gate — read 0.000 on the compliant path and 1.000 on a constructed
violation.

**The framework now executes what it measures.** Four agent-path defects were reproduced and
fixed: the check treated a gated readout as interpretable, the backward chain never bought the
gate, the policy substituted the cheapest supplier for the one the repair chose, and a composed
repair was recorded as "no registered repair" with no promise to score. Five tests pin the
fixes; on the shipped package they are inert (no shipped case declares a gate and the default
policy carries no composition rule) and the recorded ablation reproduces case for case:
58/58, 43/58, 44/58, 58/58, with the reactive control identical to 1e-9.

**The secondary core, priced.** A prediction is worth the plan change it gets right and exactly
nothing where the plan does not move: value is positive in the 7 plan-changing cells of a 5x3
grid and exactly 0.000 in the other 8, a wrong claim costs what a right one earns (0.375), and
requiring a coverage-claiming interval trades that up-side for the down-side. A miscalibrated
predictor costs 0.75 per case, and revocation stops paying after a three-case latency and
recovers 1.50 over five. On local data the secondary core still has no licensed plan-changing
role: the endpoint is not representable in the checkpoint's output space and the premise it
would have to price qualifies 11.3 % of the time.

**Claim status after these blocks.** The methodological claim is no longer unidentifiable: the
separations exist, each with the control that removes it, and the credit rule is a certificate
against an exact bound. It is still not established, and nothing here is a biological result.
The remaining gap is narrower and specific: a case where the *agent's own* proposal, rather than
a declared re-reading of a prerequisite, earns the credit; outcome models that come from records
rather than author declarations; an LLM arm scored against the rule arm at matched budget; and a
discriminating pilot with independent biological adjudication.

### 9.10 The objective, the agent's own proposal, and the 2026 robotics boundary (2026-09-15)

**Source note, recorded 2026-09-14.** The day record this section was written against, and the
block reports it cites, were **deleted** on 2026-09-14 at the owner's instruction, so that `log/`
holds the record up to that working day and nothing later. Every number below is kept as it was
written and is **no longer checkable against its cited file**; the deletion receipt, with each
path, size and SHA-256, is `D:/MAESTRO_pruned_log_20260914/_DELETIONS_after_20260914.json`. The
robotics memo it cites, `reference/prior_art_2026_robotics/ROBOTICS.md`, is untouched.

Three things changed, and none of them changes the task, the claim, or the asymmetry
between the two architectural cores. Evidence as written: the 2026-09-15 day record, its
`admissible` and `llm_proposal_arm` reports (all three since deleted), and
`reference/prior_art_2026_robotics/ROBOTICS.md`; reproduced by
`D:/MAESTRO_pruned_log_20260914/20260913/verification/verify_blocks.py` (10 of 10 checks).

**The evidence boundary is now a constraint, and the two recorded anomalies dissolve.**
Under the convention used since 2026-09-12 a policy may return a causal attribution on the
prior whenever measuring costs more than being wrong on average, which is why the exact
reference attributed without isolation on 68% of one family's mass and why the repair was
certified at 0.000 on `real_v3`. `src/evaluation/admissible.py` makes the framework's own
licensing rule a constraint on the policy class and solves both classes with the same
exhaustive dynamic program. Results: the boundary costs **0.000** on nine of the ten
recorded families and **0.680** where it binds; re-pricing the repair policy against the
admissible tail — one operator, no new search — attains the admissible reference exactly
on all ten families and improves the family where it previously lost by **0.840**; and on
`licensing_gap`, an instance built so that the only licensed route is a repair, the
repair's exact value is **0.000 under the shipped objective and 0.250 under the admissible
one**, with four controls returning it to 0.000 and the window bounded by decision
quantities (**3.000**, the expected loss of attributing on the prior, and **4.000**, the
deferral) rather than tuned.

**The frozen package cannot test the boundary, and that is a certificate.** All 58
`real_v3` cases carry a uniform prior, which makes deferring the Bayes decision at the root
and the root decision licensed; with a determinate outcome model and a unit-cost single
decisive action, licensed and decisive coincide. The successor package therefore has a
written specification rather than a wish: a **measured, skewed prior**, and a licensed
route whose cost falls inside `[expected loss of the unlicensed decision, deferral]`.

**The agent's own proposal was measured, and it found the framework's operator.** In the
2026-09-15 `llm_proposal_arm` block (since deleted; see the source note above), a model is shown a problem's public declarations — the
repair catalogue deliberately hidden — and returns one repair from a three-operator typed
language that the framework compiles and scores exactly under the admissible objective.
Two runs of sixteen problems: **5 of 16 compiled** overall, **5 of 6 and 4 of 6 where a
premise is missing**, every compiled proposal **novel** (no catalogue identifier), and
every one **reaching the catalogue's certified value once prices are anchored to the
framework's declarations** (0.25 and 0.25 on the two families where the bundle is worth
buying, 0.00 on both controls). Two honest negatives: the model's own price declarations
are optimistic by up to 6.5x, so the as-declared value (11.45 and 9.82 in total) is not the
measurement; and where nothing is missing the model still proposes a measurement and is
refused by name, so the framework — not the model — is what detects that the menu was
already sufficient. Nine and seven of sixteen problems produced non-JSON content recorded
as provider failures, so every rate is a lower bound.

**The 2026 robotics scan narrows the novelty boundary again.** `reference/prior_art_2026_robotics/`
ran 24 recorded queries across OpenReview, the arXiv HTML endpoint and Crossref, then
fetched and extracted the abstract of twelve sources (all 200, all non-empty). Eight
mechanisms transfer; the three that bear on the block above are compositional shielding
(factorised permissions provably exclude behaviour that is safe only through
coordination — the single-agent analogue of the licensing gap), shield synthesis read as a
**design-time analytic instrument rather than a runtime constraint** (which is what the
admissible certificate does), and the reasoning–execution boundary formalized as a **typed
contract** (arXiv 2608.29379) — which is prior art for typed premises, so the claim moves
onto the type of a *measured quantity* gating the claim it discharges, plus the composition
that repairs the gap. Two open findings gain routes: F07 maps to conformal calibration of
the gate's detection power, F09 to a repair-catalogue lifecycle.

**Claim status is unchanged.** Gate G1 is 394 tests, 0 failed, all of which are contract
counts. G2 stays FAIL. G3 stays **INCONCLUSIVE** — the separations exist, the measurement
device is repaired, and the repair is now the agent's own proposal and is credited on
constructed instances; what is still missing is a **real** case with a measured prior and
a licensed route inside the window, and an independent biological adjudication of it.

What this does not establish: no biological result, no measured (as opposed to declared)
price list, no claim that the model knows when not to repair, and no exactness for the
re-priced repair outside the declared suite's bounded search.

### 9.11 The evaluation protocol the claim is scored through (2026-09-14, late)

The governing report ranks evaluation infrastructure ahead of every modelling direction, and two
of its four closure conditions are protocol matters. The replay path now prices actions in wells
and turnaround days, holds back a result partition no policy can query, names every refused
query, records the candidates each step passed over, and writes the section 37 score table with a
section 29 exit verdict. The record and its pre-registration are in `log/20260914/README.md` and
`data/evaluation/preregistrations/20260914_evaluation_protocol.md`.

Three measured facts on `real_v3` bear on this document. **Every acquisition by every arm is a
record retrieval costing 0 wells and 0 days**, so the cost differences quoted in sections 9.5 to
9.9 are counts of lookups, not laboratory cost. **The declared prediction value is removed from
the loop** under the pre-registered rule: the heuristic that reads it makes 6 incorrect decisions,
the same selector with the values switched off also makes 6, and with the values shuffled it makes
15. The expectation that removal would hurt was wrong and is recorded as wrong. **The recorded
ablation reproduces exactly**: 58/58, 43/58, 44/58 and 58/58. The table's own verdict is that it
supports no comparison, because four of its six rows (response model with EIG/VOI, retrieval
agent, MDA-style explicit hypotheses, shuffled world model) have no offline arm and no
adjudication was blind.

### 9.12 The first case package where the repair decides (2026-09-14, night)

Sections 9.9 to 9.11 left one thing unchanged: on the frozen `real_v3` package the certified value
of a correctly typed repair is **0.000 in 58 of 58 cases**, and the repair measured there is a case
author's retyping rather than the agent's own proposal. `data/evaluation/cases/engagement_v1/`
answers that on real records, and it does so without closing gate G2.

**What the package is.** Six cases over two biological contexts and five source clusters, screened
from 865 candidates. Each states a genetic-versus-pharmacological discordance out of released
records - a CRISPR dependency, a fitted phenotype curve, a curated target annotation - and offers a
menu of retrievals that cannot settle it. The premise that would settle it, whether the compound
engages its annotated target in that context, is supplied by no registered action. A typed
capability registry publishes what each local release could supply, with coverage and price and no
value, and a policy has to name the missing premise and propose a capability for it. The framework
compiles the proposal through the same typed admission the executor uses, or refuses it by name;
the compiled action's result is still hidden until it is bought.

**What is measured.** The engagement call is calibrated on the release's own vehicle channels: the
threshold is the 95th percentile of vehicle-versus-vehicle absolute effects on a calibration half
of 32 vehicle groups, and the held-out half gives a measured false-positive rate of **0.03583**
(bound **0.03677** over 108,890 samples). On the four cases where the premise is missing and
coverable, the proposing arms buy one released engagement record for 1.0 and reach a licensed
non-deferral decision, while `fixed_expert`, `outcome_aware_selection` and `maestro_core` all
defer. The certificate prices that as a bound on every menu-restricted policy at any depth:
menu-only admissible optimum **4.000**, closed **1.000**, certified value **3.000** per case, and
**0.000** where the premise already licenses the action or no capability covers the context.
Laboratory cost is **0 wells and 0 turnaround days** for every arm, because every purchasable
action is a retrieval and the one action priced as a new measurement is registered unavailable.

**Two negatives are recorded with it.** First, the catalogue-expansion control - admit every
compilable capability in advance, then select once - reaches the same six decisions, so on this
package the credit belongs to the registry's *content* and not to the proposal step; the claim that
the agent's proposal is what earns the credit is therefore still unsupported. Second, on
Dasatinib/ABL1 the engagement call is negative and the package licenses `revise_attribution`, while
the always-hidden binding record lists ABL1 as a 4.7 nM high-confidence target of that compound.
The registered annotation-recovery rate is **7 of 12 (0.583, Wilson 0.320 to 0.807)**, so a
negative call is weak evidence and every `not_engaged` conclusion here inherits that weakness. The
disagreement is recorded rather than resolved, and the pre-registration's addendum records that the
originally registered selection rule produced **zero** repairable cases before exactly one
requirement was dropped with its reason.

**What it still does not establish.** G2 coverage is not met - three of four required case types,
and the two empty types were left empty rather than filled by moving a threshold. No adjudication
was blind to the arms' outputs, so no row here is evidence for the core claim. The certificate is
computed on declared outcome models, and priced with the measured call error the same repair is
worth 2.632 at the measured tolerance and 1.000 or 0.000 under the recorded exclusion tolerance: a
measurement that can be wrong excludes nothing, which is a property of the tolerance rather than of
the repair.

## 10. Minimal Landing Path

Design document only; attachments do not prove wet-lab, paired data, compute, or timeline are secured. **Step 1:** correct splits, terminal information, evidence typing, executable reachability and cost accounting; freeze the existing cases as development data. **Step 2:** qualify independent biological cases and compare matched terminal decisions before drawing conclusions about LLM authority. **Step 3:** extend the existing contrast/check/repair objects with observable repair promises and a few monitored recovery branches; preserve ordinary prerequisite handling in all controls and compare a faithful robotics transfer with biological adaptation. **Step 4:** expose qualified model adapters under `tools/`, add one frozen predictor with a separate calibration set, and compare no-model, simple-model, qualified-model and shuffled-model decision outcomes. **Step 5:** expand specialist delegation or learn a repair policy only after repeatable gain and valid real trajectories exist. No pre-commitment to long-horizon RL or a new foundation model is made.

## 11. Design Rationale and Trade-off Summary

| Option | Basis | Trade-off |
|---|---|---|
| Stronger virtual cell / Cellular JEPA | Shifts to representation/prediction | Not main line |
| Main agent with specialist subagents | Required target architecture; division of work and bounded local autonomy | Supporting implementation; compare with one agent at matched resources |
| Combinatorial selection and scheduling | Established optimization methods encode dependencies and budgets | Supporting mechanism; semantic utility and biology still require evidence |
| Open hypothesis + Bayes + VOI | Covered by MDA | Baseline to beat |
| Only functional fields + credibility interface | May be tidying | Auxiliary, prove via ablation |
| Directed repair of mechanism contrast | Transfers recovery planning to biological interpretation conditions and tests real decision benefit | Sole candidate core contribution; novelty and gain remain to be demonstrated |

Value: from "a mechanism may hold" to "why the experiment cannot yet decide, and how to get enough evidence"; LLM value is generating/revising questions from heterogeneous descriptions; virtual-cell value is better prediction for supported branches.

> This work proposes MAESTRO, a mechanism-contrast repair agent for genetic–pharmacological evidence conflict. A main decision agent coordinates specialist subagents to compile competing explanations into typed evidence workflows with measured prerequisites and interpretation boundaries. When intervention realization, condition matching, or observation quality prevents a decision, the main agent revises the relevant workflow and uses constrained optimization to select feasible evidence bundles. Registered bioinformatics tools and an applicability-bounded virtual cell supply analyses and predictions. The study tests, with resource-matched controls, whether directed repair reduces wasted evidence acquisition and wrong development actions, and checks repair promises against independent real outcomes.

## Appendix: Local Research Basis

- [Project README.md](D:/MAESTRO/README.md): goals, roles, scope.
- [Project task.md](D:/MAESTRO/task.md): first falsifiable problem and evidence action.
- [Virtual-cell and Agent research brief](D:/MAESTRO/reference/vc/Virtual-Cells-and-Agents_Research-Brief.pdf): 23 pp, SHA-256 `64ddf888…f800`; the research judgment, renamed in place. Uses task shrink, novelty, functional realization, evidence menu, independent evaluation.
- Virtual-cell and Agent research report, 68 pp: **no longer present in `reference/vc/`**. Earlier citations to pages 56-59 and 63-64 rest on text extracted while it was available and were not re-opened on 2026-09-12.
- Latest compilation, 64 physical pages, SHA-256 `dc2a5b9f…29dc`: supplied outside the repository. Its section 43 is physical page 47 and its section 45 is physical page 49; the earlier 63-page compilation is also absent, so printed footer numbers must not be substituted for physical page indices when comparing the two.
- [Robotics-informed solution and validation plan](D:/MAESTRO/log/20260912/README.md): cross-domain contribution boundary, concrete remediation, paired tests and staged decision gates.
- [General virtual-cell implementation report](D:/MAESTRO/log/20260913/README.md): the typed-premise repair, the honest search status, the contradiction verdict, the backend catalog, and the frozen-checkpoint qualification with its measured boundaries.
- Late blocks of the same session: [interpretation gates and composition](D:/MAESTRO_pruned_log_20260914/20260913/repair_v2/REPORT.md), [the composition repair on the frozen cases](D:/MAESTRO_pruned_log_20260914/20260913/real_composition/REPORT.md), [the priced secondary core](D:/MAESTRO_pruned_log_20260914/20260913/prediction_value/REPORT.md), [the agent path](D:/MAESTRO_pruned_log_20260914/20260913/agent_path/REPORT.md), [the four-gate licence certificate](D:/MAESTRO_pruned_log_20260914/20260913/licence_certificate/REPORT.md), the [contingent instrument](D:/MAESTRO_pruned_log_20260914/20260914/contingent/REPORT.md), its [real-case certificate](D:/MAESTRO_pruned_log_20260914/20260914/real_cases/REPORT.md), the [paper-shaped synthesis](D:/MAESTRO_pruned_log_20260914/20260913/synthesis/MANUSCRIPT.md) and the [independent reproduction](D:/MAESTRO_pruned_log_20260914/20260913/verification/VERIFICATION.md).
- Reference assets re-verified on 2026-09-13 by digest and page count, not by filename: the 23-page brief and the 64-page compilation are as recorded above; the 68-page report and the 63-page compilation remain absent.

Attachment content is research material; suggestions, timelines, citations are not execution orders or verified facts. Novelty-central papers are linked inline; unchecked details stay as audit items.
