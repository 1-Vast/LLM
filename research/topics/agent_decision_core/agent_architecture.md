# Agent architecture: knowledge, memory, context, delegation, reasoning

Design record for the parts of the agent that decide *what it knows* and *what it carries
forward*. Labels: **implemented**, **partial**, **design**, **unverified**.

---

## 1. Biological knowledge base

### 1.1 What it must supply

Constraints, not more text. A knowledge base that returns paragraphs moves the problem into the
prompt; one that returns *typed, conditioned claims* lets the deterministic layer check them.

**Record shape** (implemented in `agent/knowledge.py`):

```
claim( statement, source_id, context, evidence_kind, status,
       payload, source_lineage_ids, entities )
```

`evidence_kind ∈ {real_measurement, derived_analysis, retrieved_source, model_prediction,
prediction_derived_analysis}` and `status` is derived from it, never set independently. This is
the mechanism that stops a retrieved sentence from being read as a measurement.

**Relations to carry** (partial): `supports`, `contradicts`, `measures`, `derived_from`,
`uses_context`, `targets`, `requires`. Each relation is conditioned; see §1.3.

### 1.2 Admission, not retrieval, is the hard part

Four different questions are kept apart, because collapsing them is how a literature claim
becomes a premise:

| Question | Answered by |
|---|---|
| Is the file valid and parseable? | Schema and digest check |
| Did the underlying assay pass its own quality control? | The record's declared QC field |
| Do the conditions match this case? | Context, time, dose and replicate comparison |
| Is there statistical support at the required replication? | Independent-unit count against the rule's minimum |
| Is a development action authorized? | The interpretation rule, and only it |

An underlying historical measurement **can** qualify, but only after its original data,
conditions, QC and lineage are checked — not because it appears in a review.

### 1.3 Conditioned edges and source clusters

- **Conditioned edges** (design). Every relation carries the context, time window and
  perturbation state under which it was observed. Two edges that disagree across contexts
  coexist; they are never merged into one universally true edge. Merging is the failure that
  produces confident cross-context transfer.
- **Source clusters** (implemented, `maestro/provenance.py`). Several write-ups of one original
  experiment resolve to one cluster, so citing a finding three times does not narrow the
  compatible hypothesis set three times.

### 1.4 Acceptance tests

1. A retrieved claim with matching text and non-matching context does not satisfy the premise.
2. Two contradictory context-specific edges both survive ingestion and are both returned, with
   their contexts, for a query that spans them.
3. Three reports of one experiment contribute coverage once.
4. A claim whose QC field is absent is treated as unknown, never as passing.

---

## 2. Memory

### 2.1 Three registers

| Register | Holds | Lifetime | Promotion |
|---|---|---|---|
| **Working** | Current turn's task, intent, scratch state | The turn | Never promoted directly |
| **Episodic** | Round record: plan, selected action, result reference, reflection | Append-only | Only by an explicit outcome rule |
| **Conclusion** | Distilled finding plus its scope and limits | Retained, **revocable** | Requires a qualified result and a named rule |

Status is explicit on every entry (`proposed`, `derived`, `measured`), and retrieval renders it
(`MEMORY (not new evidence)`), so a remembered proposal cannot be re-read as a finding.
**Implemented**: `agent/memory.py` with scope, status and retraction; the three-register split
is **partial** — working and episodic exist, the conclusion register's promotion rule is design.

### 2.2 Star topology, and why not full connectivity

Records attach to a hub — the case — through typed spokes: `case → round → record`. Records do
not cross-link freely.

| Property | Star (`n` spokes) | Full connectivity |
|---|---|---|
| Edges | `n` | up to `n(n−1)/2` |
| Retraction of one record | Local: invalidate one spoke | Non-local: every incident edge must be found and repaired |
| Provenance of a claim | Exactly one path to its case and parent result | Many paths; "why is this believed" has no single answer |
| Context assembly cost | Linear in what the round touched | Grows with accumulated history |
| Failure mode | A missing spoke is visible | A stale edge is invisible and keeps a retracted record alive |

Genuine cross-references are kept as **typed parent identifiers on the record** (`parent_ids`),
which is a directed labelled pointer the retraction rule understands — not a free edge. So the
graph stays a forest of depth-2 stars with explicit lineage arrows, which is enough to answer
provenance and cheap enough to traverse every round.

**Hierarchy and traceability.** `case → round → record → field`. Every conclusion must resolve
to at least one qualified result identifier; a conclusion with no such path is not writable.

### 2.3 Tool descriptions carry negative conditions

Every manifest in `tools/` declares both:

```json
"use_when":        ["A complete registered prediction request is supplied ..."],
"do_not_use_when": ["A measured phenotype, target occupancy, causal mechanism,
                     unregistered perturbation or unvalidated cross-endpoint bridge
                     is required."]
```

**Implemented.** A description that states only the positive case invites use outside the
domain; the refusal condition is the operative half. The router shows both to the model and
refuses unregistered tools, unknown parameters and unsupported suffixes before execution.

### 2.4 Acceptance tests

1. Retracting a conclusion leaves no retrieval path that still returns it.
2. A remembered proposal is never rendered without its status.
3. A conclusion without a qualified parent result cannot be written.
4. Every registered tool declares at least one `do_not_use_when` entry.

---

## 3. Context assembly and compression

### 3.1 Ordered budget

1. **Mandatory core** — task and supplied evidence. If this alone exceeds the budget the turn
   refuses (`mandatory_task_state_exceeds_context_budget`) rather than truncating.
   **Implemented.**
2. **Structured compaction** — undeclared fields are dropped from rendered catalogues; a
   contrast names its plan by identifier. Measured on the shipped fixture: catalogue −23%,
   contrast −66%, combined repair payload −39%. **Implemented.**
3. **Conditioned summary** — a long retrieved source may be summarized, but its condition
   fields, evidence kind and source identifier are preserved verbatim. **Design.**
4. **Named omission** — whatever does not fit is listed by identifier and reason
   (`omitted_record_ids`, `omission_reasons`). **Implemented.**

### 3.2 The rule

> Compression may remove redundancy. It may not remove the fact that something was removed.

An omitted record keeps its identifier, so a later step can request re-expansion. A summary that
loses the condition fields is not a summary of usable evidence — it is a new, weaker claim.

### 3.3 What is deliberately never compressed

The registered action menu's typed fields, the open premise list, refusal reason codes, and the
provenance of anything that entered belief. These are small and they are exactly what the
deterministic layer reads.

---

## 4. Sub-agents and parallel research

### 4.1 Roles and limits

| Role | Bounded responsibility | Returns |
|---|---|---|
| Evidence researcher | Primary literature and database records | Conditioned claims, contradictions, missing fields |
| Dataset and QC analyst | Inspect supplied data, identities, controls, batches, replicate units | QC report, artifacts, admissible analyses |
| Multi-omics analyst | Differential, pathway, regulatory workflows | Effects, uncertainty, limitations |
| Simulation specialist | Applicability check and qualified prediction | Prediction with lineage and calibration status |
| Verification specialist | Audit sources, transformations, assumptions, alternatives | Structured objections, counterexamples |

Sub-agents **never** write global state, authorize a decision, promote a prediction, or
overwrite accepted evidence. Only the main agent plus the deterministic validator update belief.

### 4.2 Scheduling by dependency, not by ambition

Parallelism is decided by the **action topology** (`maestro/topology.py`, implemented): an
action points to actions that can supply one of its unmeasured premises. From it the runtime
derives the executable frontier, the shortest supplier chain to each blocked action, capability
gaps, and supply cycles. Independent work fans out; dependent work waits for its supplier.

The same rule already governs model queries (implemented): identical queries run once per
round; distinct ones may run concurrently under `max_parallel_predictions`; recording and
logging stay in request order, so the run record is identical whichever way dispatch happened.

### 4.3 Agreement is not evidence

Two sub-agents concurring is not independent confirmation, especially when they read the same
source cluster. Disagreement triggers a source and assumption check. Majority voting is not a
belief update. A hierarchy must be compared against a resource-matched single agent, reporting
actual calls, evidence, compute and latency — never by forcing wasteful calls to equalize counts.

---

## 5. Collaboration protocol and its failure modes

| Failure | Prevention | Status |
|---|---|---|
| Contradictory writes | Single writer for global state | implemented |
| A sub-result silently dropped | Round records have mandatory fields and **refuse to write** when incomplete | implemented (`maestro/handoff.py`) |
| Deadlock on a missing artifact | Supplier chains are depth-bounded; a missing supplier is reported as a named capability gap | implemented |
| Duplicated work | Reuse keyed on inputs; identical requests answered once per run | implemented |
| Consensus mistaken for evidence | Agreement recorded as agreement only | implemented |
| A malformed reply ending a run | Bounded back-prompt naming the violation; a second failure is recorded as one lost case, not a lost run | implemented |
| An edit adopted without verification | Deterministic re-check before adoption | implemented |

Every hand-off is a four-layer structured record — evidence, world model, decision, execution —
with mandatory `in_distribution`, `rejected[]` and `contradiction_flag` fields. An incomplete
record is refused and logged rather than written, because a written record with a missing
mandatory field reads later as though the field had been answered.

---

## 6. Deep reasoning without information loss

Three carriers keep unresolved material alive across steps:

1. **Named open premises.** The check returns exact missing prerequisite fields; the topology
   returns premises no registered action supplies. Both survive as identifiers, not prose.
2. **A path back to a result.** Promotion to a conclusion requires parent identifiers reaching a
   qualified result.
3. **Adopted separated from worked.** The repair ledger records the triggering failure, the
   changed field, the promised discriminating power, whether re-checking adopted the edit, and
   whether a later real result closed the promised gap.

**Anti-pattern this rules out:** summarizing a round into a sentence that drops the premise that
was still missing. The summary is allowed; dropping the identifier is not.

---

## 7. Judgment accuracy and error accumulation

### 7.1 The problem

Multi-step execution is where a plausible agent drifts from reality. Errors are not independent
across steps, so a constant per-step success probability is a simplifying model, not a law. The
dangerous errors are systematic: a premise assumed at step 2 quietly conditions steps 3 to 8.

### 7.2 Mitigations, all implemented

1. **Verification independent of the generator.** Every model-proposed edit is re-checked by
   deterministic code before adoption; the generator never grades itself.
2. **Bounded self-correction with named violations.** A contract violation, or a critic finding
   only the planner can satisfy, is named back once. A second failure raises or is handed to the
   deterministic check.
3. **Calibration ledgers with revocation.** A prediction interval that repeatedly misses is
   down-weighted then revoked for that readout and context. A typed judgment whose probability
   forecasts score no better than chance is revoked for that scope.
4. **Explicit unresolved state**, per §6.

### 7.3 What to measure

- **Per-step admissibility**: the fraction of steps whose output the deterministic layer accepts
  without repair.
- **Decision regret**: loss of the selected action against its hidden measured outcome, minus the
  best achievable in the menu.
- **Drift**: whether per-step admissibility declines with step index within a case. A declining
  curve is error accumulation; a flat curve at equal regret is not.
- **Revocation events**: how often a calibration ledger withdraws a source, and whether decisions
  improved after it did.

### 7.4 Acceptance tests

1. An edit that fails re-checking is never adopted, whatever confidence accompanied it.
2. A confidently wrong probability source loses influence after a bounded number of scored
   misses, and its later answers change no decision.
3. A provider failure mid-case is recorded as one lost case with a reason, and the run continues.
