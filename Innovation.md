# MAESTRO: decision-directed repair of mechanistic contrasts

**Mechanism-Aware Evidence-driven Scientific Agent for Therapeutic Reasoning and Optimization**

An agent is given a biological question, a registered menu of measurements it may buy, and a
budget. It must decide what to do next, and eventually what to conclude. This document states
the contribution, the architecture that supports it, the formal decision layer, and the tests
that would refute it. Detailed designs live in [`research/`](research/README.md); the runnable
surface is described in [`README.md`](README.md); the downstream tasks and their gates are in
[`task.md`](task.md).

---

## 1. Problem

When a genetic dependency and a pharmacological phenotype disagree, the disagreement has at
least six live explanations: incomplete functional perturbation, intervention-mode
non-equivalence, multi-target pharmacology, pathway compensation, context dependence, and
unresolved mechanism. The usual failure is not that a model predicts the wrong number. It is
that **the evidence on hand cannot separate the explanations at all**, and the workflow
proceeds as though it could.

Two consequences follow. A measurement can pass its own quality control and still move no
belief, because an interpretation prerequisite was never measured. And a multi-step agent
compounds this: each unexamined step carries its unresolved premises forward silently, so a
confident final answer can rest on a gap introduced five steps earlier.

## 2. Claim

> **Decision-directed repair of mechanistic contrasts.** Given a contrast between two
> explanations that current evidence cannot separate, the agent locates the specific failed
> prerequisite, proposes a minimal change to the registered evidence plan, and checks the
> repair's promise against later qualified observations.

Operationally: identify a named interpretation failure → propose one change bounded by the
registered menu → obtain a resource-feasible plan → verify the promise against real results.
Minimality is relative to a declared candidate pool and cost criterion.

**Falsifiable form.** Under the same model, tools, initial evidence, feasibility handling and
total budget, directed repair reduces unsupported development actions and the cost of reaching
an admissible action, relative to (a) a fixed expert procedure, (b) reactive outcome-aware
selection, and (c) equal-budget random legal edits. If (b) or (c) matches it, the repair is not
what produced the difference.

**What is not claimed.** Generic replanning, task-graph repair, uncertainty routing,
hierarchical delegation and value-of-information planning all have precedents. None is claimed
as new. The claim is confined to the biological repair operation and its measured effect on
decisions.

## 3. System

Two architectural cores, unequal in authority:

- **The agent is primary.** It owns the objective, the belief state, the action choice, the
  repair, and the final bounded decision.
- **The virtual cell is secondary.** It supplies a conditional prediction with an applicability
  domain, and abstains outside it. It never certifies engagement, mechanism or efficacy.

A third model class now sits beside them: a **typed decision model** (Section 6) that returns
probabilistic answers to typed questions and cannot emit prose. Its calibration and
reproducibility are assessed separately; an ungraded answer is provisional.

| Layer | Directory | Responsibility |
|---|---|---|
| Decision core | `src/maestro/` | Contrast, check, repair, belief state, decision rules, action topology, judgment boundary |
| Agent runtime | `src/agent/` | Task interpretation, knowledge base, memory, context, planner, critics, orchestration |
| World model | `src/virtual_cell/` | Applicability-bounded prediction, calibration, artifact lineage |
| Evaluation | `src/evaluation/` | Replay environment, policy arms, hidden outcomes, cost ledgers |
| Tools | `tools/` | Manifest-scoped adapters the agent may invoke on supplied datasets |
| Data | `data/` | Local datasets, staged and digest-verified |
| Research | `research/` | Designs, protocols and analysis, synchronized as work proceeds |

**Implementation boundary.** The contrast checker, bounded repair, evidence ledger, action
topology, exact finite-menu coverage selector, virtual-cell adapter and typed critic have code
and tests. `tools/typed_decision_review/` validates recorded Jev reviews as advisory artifacts
for replay and audit. `tools/signature_retrieval/` compares a measured signature with measured
reference responses, and the `sciplex_response` rung serves the one readout that beat the
average drug response, with coverage-checked intervals (Section 8). General-purpose research sub-agents, automatic promotion into a conclusion memory
register, and outcome-based evidence that the policy improves biological decisions remain
design or evaluation work. Sections below distinguish those states where they matter.

**One invariant governs all of it.** Origin never strengthens through downstream use. A
retrieved claim, a model prediction, a visual reading and a typed judgment are all
`model_prediction` or `retrieved_source`; none becomes `real_measurement` by entering context,
memory, a prompt or a conclusion.

## 4. Agent architecture

### 4.1 Biological knowledge base

The knowledge base supplies **constraints**, not more text. Structured biological assertions
carry source lineage, evidence kind, claim level, method and explicit conditions
(`agent/biology.py`). Retrieval excludes known condition mismatches and labels missing
conditions as unknown; an unknown match may inform planning but cannot extend the matched
relation graph. Legacy free-text records do not acquire structured condition matches.

Three rules do most of the work:

1. **Context-specific contradictions coexist.** Opposite-sign assertions stay separate.
   Overlapping conditions produce review candidates, while known disjoint conditions do not;
   neither is automatically adjudicated. Coexpression, attention and feature importance cannot
   be registered as causal regulation; a declared causal effect requires a perturbation method
   and controls. This validates the assertion schema, not the underlying experiment.
2. **Source clusters count once.** Several write-ups of one original experiment are one source
   (`maestro/provenance.py`), so repeated citation cannot shrink the compatible hypothesis set
   twice. This is the structural-redundancy control (Section 7.3).
3. **Retrieval does not qualify.** A retrieved claim can motivate a plan; it satisfies a
   measured prerequisite only after its underlying data, conditions, quality control and
   lineage are checked.

The ledger can trace declared ancestors and descendants while respecting case visibility and
retraction. It cannot reconstruct undeclared training-data lineage for an external model.

### 4.2 Memory: three registers, star topology

| Register | Holds | Lifetime | Promotion rule |
|---|---|---|---|
| **Working** | The current turn's task, intent and scratch state | Stored per turn | No automatic promotion |
| **Episodic** | Round reflections and result references | Retained, revocable | No automatic promotion |
| **Conclusion (design)** | Distilled, reusable findings with their scope | Proposed | Would require a qualified result and a named rule |

**Star topology is the intended organization, not a fully enforced storage shape.** Current
memory entries have case scope and optional parent identifiers; retraction follows those
identifiers. A strict case → round → record graph and conclusion promotion gate remain design.
The proposed topology has three motivations:

- *Retraction is local.* Revoking a conclusion means invalidating one spoke, not walking an
  arbitrary graph. Under full connectivity, a retracted record leaves live edges behind it.
- *Retrieval fan-out is bounded.* A hub with `n` records has `n` edges instead of up to
  `n(n-1)/2`, so context assembly cost stays linear in what the round actually touched.
- *Provenance is inspectable.* Declared parent identifiers allow an audit to follow lineage;
  records without declared lineage do not gain a parent result by inference.

Cross-references that are declared (for example, a reflection's result identifier) are kept
as parent identifiers, which the retraction rule understands.

**Tool descriptions carry negative conditions.** Every manifest declares both `use_when` and
`do_not_use_when`. A capability description that only says what a tool is for invites use
outside its domain; the refusal condition is the part that prevents it. This is already the
contract for every adapter in `tools/`.

### 4.3 Context: budget and compression without silent loss

Context is assembled under a fixed budget with a strict order:

1. **Mandatory core** — the task, all structured task details and the supplied evidence. If
   this alone exceeds the budget,
   the turn **refuses** with `mandatory_task_state_exceeds_context_budget` rather than
   truncating. A silently truncated task is a wrong task.
2. **Structured compaction** — records render compactly: undeclared fields are omitted, a
   contrast names its plan by identifier instead of repeating the catalogue entry. Measured
   reduction on the shipped fixture: catalogue −23%, contrast −66%, combined repair payload
   −39%.
3. **Atomic evidence cards** — included records retain their statement, origin, source,
   conditions and limitations. Condition-preserving summarization of oversized cards is still
   design; the current builder includes or omits a whole card.
4. **Named omission** — anything that does not fit is listed in packet metadata by identifier
   with a reason (`omitted_record_ids`, `omission_reasons`) and logged by the orchestrator.
   The omission list is not currently guaranteed to appear in the model-visible prompt, and
   automatic re-expansion is not implemented.

The invariant: **compression may remove redundancy; it may not remove the fact that something
was removed.**

### 4.4 Sub-agents and parallel research

Bounded research sub-agents for retrieval, dataset analysis and verification are a proposed
extension; the runtime does not yet dispatch those roles. Current tool adapters and prediction
calls return structured outputs, while the orchestrator and deterministic validator control
admission and decisions.

The **action topology** (`maestro/topology.py`) reads the menu as a dependency graph: an action
points to actions that can supply one of its unmeasured premises. It derives the executable
frontier, supplier distance and capability gaps. This informs action planning; it does not
schedule general research sub-agents.

The same discipline is already applied to model queries: identical queries run once per round,
distinct ones may run concurrently, and recording stays in request order so the run record does
not depend on the dispatch mode.

**Agreement is not evidence.** If research roles are added, concurrence from roles reading the
same source cluster must not count as independent confirmation. Current repeated typed-model
answers measure reproducibility, not biological replication.

### 4.5 Protocols and collaboration failure

Coordination failures are distinct from being wrong about biology. Existing boundaries and
planned multi-role controls address five named ones:

| Failure | Mechanism that prevents it |
|---|---|
| Contradictory writes | Single writer: only the main agent plus the deterministic validator update global state |
| Silent dropping of a sub-result | Structured hand-off records validate mandatory fields; generic sub-agent hand-offs remain design |
| Deadlock on a missing artifact | Supplier chains are bounded in depth and report `no registered supplier` as a named capability gap instead of waiting |
| Duplicated work | Query and prediction reuse is keyed on the inputs, so an identical request is answered once per run |
| Consensus mistaken for evidence | Repeated model agreement affects critic reliability only; qualified results control belief updates |

Every hand-off is a structured record with its layers stated (evidence, world model, decision,
execution) and mandatory fields including distribution membership, what was rejected, and a
contradiction flag (`maestro/handoff.py`).

### 4.6 Deep reasoning without information loss

Three mechanisms carry unresolved material forward instead of letting it evaporate:

- **Open premises are named, not summarized.** The check returns the exact missing prerequisite
  fields; the topology returns the premises no registered action can supply. Both survive into
  the next round as identifiers.
- **Declared lineage can be traced.** Evidence records and reflections can name parent
  identifiers, and retraction follows descendants. A qualified-result gate for writing
  conclusion memory is still design.
- **Adopted is separated from worked.** The repair ledger records the triggering failure, the
  changed field, the promised discriminating power, whether re-checking adopted the edit, and
  whether a later real result closed the promised gap. "A repair was adopted" and "a repair
  worked" are different columns, which is what stops an unverified edit from reading as a
  success later.

### 4.7 Judgment accuracy and error accumulation

Multi-step execution is where a plausible agent drifts away from reality. A constant per-step
success probability is a simplifying model, not a law; real workflow errors are correlated,
and the dangerous ones are systematic rather than random. Four mitigations, all implemented:

1. **Verification independent of the generator.** Every model-proposed edit is re-checked by
   deterministic code before adoption. The generator never grades itself.
2. **Bounded self-correction with named violations.** A reply that breaks its declared contract,
   or fails a critic only the planner can satisfy, is named back to the model once. A second
   failure raises or is handed to the deterministic check — it is never retried indefinitely.
3. **Calibration ledgers with revocation.** A prediction interval that repeatedly misses is
   down-weighted and then revoked for that readout and context. A typed judgment whose
   probability forecasts score no better than chance is revoked for that scope. Influence is
   earned against later measurements and can be lost.
4. **Explicit unresolved state.** Because open premises and capability gaps are carried as
   identifiers, an unresolved item cannot be quietly absorbed into a summary.

The measurable target is not "fewer wrong tokens" but **per-step admissibility**: the fraction
of steps whose output the deterministic layer accepts, and the decision regret of the final
selected action against its hidden measured outcome.

## 5. The decision layer, formalized

### 5.1 Belief state

Let `H` be the registered explanation set for a case. The belief state is

```
B = (C, M, S)
```

- `C ⊆ H` — the explanations still **compatible** with admitted evidence. A **set, not a
  posterior**: no component may invent an unmeasured probability, so nothing here is a density.
- `M` — the set of **measured premises**, each with the quantity, entity, units, context and
  time that qualified it.
- `S` — the **admitted scope** per field: how strongly a field has been established
  (plan limitation, measurement feasibility, intervention implementation, mechanism contrast).

Update rule: only a qualified, condition-matched result whose interpretation rule targets
`mechanism_contrast` may remove an element of `C`. Every other result enters the update log
with a narrower scope. Exhausting `C` is `contradicted` — a reason to revise the premise, not a
licence to pick the nearest label.

### 5.2 Action space

```
A = A_evidence ∪ A_repair ∪ A_terminal
```

- `A_evidence` — registered measurements, each typed by prerequisites, what it supplies, its
  interpretation gate, cost in wells and turnaround days, declared expected outcomes per
  explanation, and detection power. Feasibility is decided by the topology, not by prose.
- `A_repair` — `keep`, a local edit within the current plan's neighbourhood, or a switch to a
  different response pattern before searching. These are search operators over the plan; they
  are **not** identified biological causes, and must not be read as such.
- `A_terminal` — continue, revise intervention, change intervention mode, preserve or remove a
  multi-target activity, revise attribution, defer, stop. Applied to the current program only,
  never as a permanent verdict on a target.

`Feasible(a | B)` holds when every open premise of `a` is measured, or a bounded supplier chain
exists that makes it runnable. An action whose open premises nothing on the menu supplies is a
**capability gap**: the honest response is to name it, not to substitute a weaker action.

### 5.3 Declared expected coverage (not biological value of information)

For budget `b`, the implemented finite-menu selector chooses the bundle `X ⊆ A_evidence`
maximizing declared weighted expected coverage, then minimizes cost and action count:

```
maximize   Σ_h w_h · P(X answers h)
subject to cost(X) ≤ b,  Feasible(x | B) for all x ∈ X
```

with `P(X answers h)` derived from each action's **declared** detection power, and actions
sharing a source component using a conservative maximum rather than pretending to be independent.
This is an auditable coverage heuristic for a declared menu, not a biological utility estimate
or a posterior value of information. Three rules keep it honest:

- **No self-reported probabilities.** A language model's stated confidence is not an input.
  Calibrated probabilities may enter only from a source the judgment ledger has graded against
  measured outcomes.
- **No assumed submodularity.** Complementary evidence can have zero individual value and high
  bundle value, so greedy information-per-cost ranking is not valid by default; small pools are
  solved exactly.
- **The selector does not price terminal deferral.** Deferral and stopping are handled by the
  decision layer, not treated as evidence actions in this coverage objective.

A solver optimum is optimal for the declared finite problem only. It is not a claim about
biological value of information. On 2026-09-26 detection power estimated from measured reference
compounds was tested as this selector's input and chose worse measurements than the current
magnitude tie-break (`research/dynamic_world_model/`), so a power estimate is not better than a
declaration merely because it is computed.

Beside this selector, `select_discriminating_action` (opt-in, 2026-09-26) chooses one next
measurement from per-hypothesis outcome forecasts. What a predicted reading would eliminate comes
from the registered interpretation rules, so the objective is rule-conditioned discrimination:
the correct minus the wrong elimination probability. It is bounded above by the total variation
between the hypotheses' predicted readings. The gap is the part no lawful elimination can use,
including every difference in absence.

A wrong-risk gate at the declared utility's break-even comes first; a Jeffreys lower bound then
ranks, so thin support is discounted rather than deleted. Its registered evaluation on seen
SciPlex3 episodes was inconclusive
([`research/acquisition_link/`](research/acquisition_link/README.md)). The same audit found that
the power-aware path, which production uses, had been logging and never using the virtual cell's
priorities.

## 6. The typed decision model

A text model can name an action that does not exist, assert a mechanism, or describe a result
nobody measured. The repository answers this with a contract parser, a critic loop and a
deterministic re-check. A model that **cannot emit text** removes the failure mode
structurally instead of catching it afterwards.

TypeSafe **Jev** answers typed questions and returns only structured values with calibrated
probabilities: yes/no, one option from a declared list, or a position on an ordered scale. Its
integration follows the architecture's own rule:

- Choice options are **exactly** the registered action identifiers, so an out-of-menu answer is
  inexpressible rather than merely rejected.
- Every answer becomes a `TypedJudgment` whose `satisfies_premise`, `eliminates_hypothesis` and
  `is_measurement` are fixed at false, and whose scope vocabulary contains no mechanism-contrast
  member.
- Probability forecasts are Brier-scored against later measured outcomes; a scope that stops
  calibrating is down-weighted and revoked.
- Confident answers become **advisory findings** to the repair planner. The deterministic check
  remains the authority.

### 6.1 Reproducibility is tested before calibration

A live run found the model answering one unchanged state differently: a ranking question moved
between two of five options across two identical calls. Brier grading cannot catch this in time,
because it waits for measured outcomes — the scarcest thing in the system — and grants full
influence until it has five of them.

Reproducibility needs no outcome. Writing `mu` and `sigma^2` for the mean and variance of the
probability a source returns for a fixed state, and `q` for the outcome's true probability,

```
E[(P - Y)^2] = q(1-q) + (mu - q)^2 + sigma^2
```

separates irreducible uncertainty, miscalibration and **instability**, and only the third is a
property of the source alone. Answering with the mean of `n` calls removes exactly
`sigma^2 (1 - 1/n)` of it. For a ranking the operative quantity is the chance that two identical
calls select the same action, which has an unbiased estimator from repeats and is itself the
weight: a source that reproduces 0.7 of the time counts 0.7.

Three consequences, all implemented:

- A scope that can change **which action is bought** must show agreement before it may break a
  tie. A scope that only comments may speak while unmeasured, carrying that label.
- Calibration and reproducibility fail independently — a source can be well calibrated on
  average while answering differently each time, or repeatably wrong — so the effective weight
  is the **smaller** of the two.
- Not having asked twice is not a finding. An unchecked preference is still forwarded and named
  as unchecked; only a **measured** disagreement withholds it.

Design, exact contract and what remains unverified:
[`research/typed_decision_model.md`](research/typed_decision_model.md). Derivation, thresholds
and cost: [`research/judgment_stability.md`](research/judgment_stability.md).

## 7. Coupling to biology

### 7.1 The contrast is the biological object

A contrast is `(h_i, h_j, Δ, q, a, Y, ρ, D)`: two competing explanations, the prerequisites
where they differ, the question, the planned action, the outcome categories, the update rule,
and the interpretation boundary. It is not ready until the plan is executable, its premises are
measured, its outcomes are declared to differ between the explanations, and the two explanations
lead to different development decisions.

### 7.2 Regulatory structure is dynamic, not a fixed graph

A regulatory network is not a static object the agent can consult once. Edges are conditional on
cell context, time and perturbation state, and the same pair of genes can be coupled in one
context and independent in another. The design consequences:

- **Every structured assertion carries its conditions.** Context, time window and the
  perturbation under which it was observed are part of the relation, not metadata attached later.
- **An edge is a hypothesis.** An inferred regulatory relation motivates a measurement; it never
  satisfies a premise and never licenses a mechanism claim. A typed judgment that ranks
  candidate regulators is labelled as a hypothesis in the state text and in the finding itself.
- **The reasoning graph and any predictor's graph stay separate.** A graph used to constrain a
  prediction cannot also serve as independent ground truth for that prediction.
- **Dynamics change what is reachable.** The supplier topology is recomputed per round against
  the current profile, so the available action frontier depends on what has already been
  measured. This is planning reachability, not a simulated dynamic GRN.

### 7.3 Complementarity and structural redundancy

Two evidence items are **complementary** when they constrain *different* open premises, and
**redundant** when they constrain the same premise through the same original experiment. The
distinction is enforced, not assumed:

- Source clusters collapse repeated reports of one experiment to one source, so redundancy
  cannot masquerade as replication.
- The exact selector reports expected coverage and a leave-one-quantity-out diagnostic over the
  selected bundle. These are declared-coverage diagnostics; they are not empirical modality
  gains until evaluated on held-out outcomes.
- Cost is split into access, preprocessing, compute and new measurement where supplied. Missing
  components remain invalid or unknown rather than being silently treated as free.

### 7.4 Multimodal, multiscale and inexpensive data

Preference order for a first-stage study: already-public, condition-level, inexpensive to
process, and deployable from inputs available *before* the candidate is measured — structure,
dose, time, cell background, and a matched control. A cross-scale bridge requires units,
parameter identity, calibration data, uncertainty and a scope; an unvalidated bridge is
presented as exploratory and paired with a measurement that could test it. Repeated use of one
dataset does not create independent confirmation at three scales. The multimodal adapter keeps
RNA, protein, activity, occupancy, morphology and chromatin as distinct quantities, and reports
known batch mismatches without inferring directional disagreement across them.

## 8. Evaluation

Five separate levels, never averaged into one score: representation quality, prediction quality,
intervention-design quality, biological credibility, and final decision quality.

- **Freeze first.** Objective, weights, candidate sets, visible evidence, model versions, prompts
  and budgets are digested before any hidden outcome is revealed.
- **Split by independent unit.** Molecular identity, and scaffold for a chemistry claim; a cell
  line with no adequate training support is an explicit extrapolation test, not an
  interchangeable coordinate. Cells are not biological replicates; the analysis unit is the
  compound or study cluster.
- **Score the selected action against its hidden measured outcome**, never a latent target
  against the model that produced it.
- **Report separately**: perturbation-specific error after removing systematic shift, ranking,
  decision regret, gain per expensive query, calibration and abstention, laboratory cost in
  wells and days, and provider spend.
- **Mandatory controls**: zero-effect and train-mean baselines, a linear predictor, retrieval,
  equal-budget random legal edits, repair disabled, and outcome-aware one-shot selection.
- **Diagnostic ablations**: scramble effect direction while preserving magnitude; change the
  available actions with the initial error fixed; propose an unsupported subgoal; permute batch
  labels. If scrambling direction does not collapse the measured gain, the metric is
  magnitude-driven and the result is an artifact.
- **Biological anchors and the zero arm.** Score pharmacology known from the literature on the
  measured data first and on out-of-fold predictions second, and always include an arm that
  predicts no change. On 2026-09-26 SciPlex3 carried seven of ten anchors while no predictor
  reproduced more than three, and the zero arm scored 0.130 on a centered specificity metric
  that the registered rule had treated as evidence of specificity: most drugs respond less than
  the average drug, so centering alone rewards predicting "less". Direction must be measured
  with the shared-response axis projected out
  ([`research/biological_depth/`](research/biological_depth/README.md)).
- **Verify feature identity biologically.** Cell-line identity markers found that the SciPlex3
  Figshare release names every gene one column off; no contract test could have caught it.
- **Score a measurement by the decision it enables, and never read absence as failure.** On
  2026-09-26 a model that predicted the next profile better than persistence did not choose better
  measurements, a fixed protocol beat every model-based policy in the time tier, and a validator
  that refuses to eliminate on an undetected response kept wrong eliminations near 1-2% where an
  ungated reading reached 26% ([`research/dynamic_world_model/`](research/dynamic_world_model/README.md)).
- **Check that the model's output reaches the decision.** On 2026-09-26 the production selector
  had been logging, not using, every virtual-cell prediction, and a 72 h action was being ranked
  by a 24 h answer. A comparison of planners had assumed a link that was not there
  ([`research/acquisition_link/`](research/acquisition_link/README.md)).
- **Compare sequence policies under identical sequence rules.** On 2026-09-26 the arms of a
  sequence comparison followed different QC-continuation rules. Matched in one runner, the rules
  changed the gap by only 0.015. What had looked like a planning defect was the planner honestly
  refusing to value continuations its sparse references could not support, and on independent
  L1000 data the matching fix changed almost nothing
  ([`research/sequence_audit/`](research/sequence_audit/README.md)).

Protocol in full: [`research/asrg/03_experiment_protocol.md`](research/asrg/03_experiment_protocol.md).

## 9. Novelty boundary

Prior art that this project does not claim: signature matching and reversal for compound
selection; forward prediction of chemical perturbation responses; inverse prediction of
perturbagens from a desired state; budgeted experimental design and active learning on a
budget; support-constrained action selection; planning in frozen representations; trust-region
search; hierarchical multi-agent orchestration; graph-constrained retrieval.

What remains defensible is narrow and measurable: **in a restricted-repair agent over a finite
registered menu, directed repair of an indiscriminable mechanism contrast — with measurement-
anchored selection, certified support, and calibrated critics that can be revoked — reduces
unsupported decisions and cost-to-admissible-action relative to equal-budget controls.**
Nothing in that sentence claims a new foundation model, a validated biological mechanism, or a
general-purpose discovery system.

## 10. Limits

The repository contains no validated biological model, no target-engagement claim, no clinical
recommendation, and no experimental result. The virtual cell was tested for biological depth on
2026-09-26 and did not show it for unseen compounds beyond response magnitude and a few strongly
stereotyped programs; a V-JEPA-style latent model did not improve on PCA or structure retrieval.
Virtual-cell-assisted measurement choice was tested the same day and did not beat the current
magnitude tie-break; a learned 24 h to 72 h population transition predicts profiles better than
persistence but improved no decision.
A distribution-aware selector that reads per-hypothesis forecasts through the registered rules
was added the same day (opt-in). Its decisions were not distinguishable from magnitude's on the
episodes it was designed after.
A prediction is never the outcome of an unmeasured experiment. A typed judgment is a statement about a model's own accuracy, not about biology. A
solver optimum is optimal only for the declared finite problem. An agent that passes every test
here has been shown to make better-supported decisions under a frozen protocol — which is not
the same as being right about a cell.
