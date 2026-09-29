# Dynamic regulatory structure, complementarity, and cheap multimodal data

Design record for how MAESTRO treats biological structure as **conditional and changing** rather
than as a fixed graph to consult. Labels: **implemented**, **partial**, **design**.

---

## 1. Why a static network is the wrong object

A regulatory network read as a fixed graph invites three errors the rest of the architecture is
built to prevent:

1. **Context erasure.** Two genes coupled in one cell context can be independent in another.
   A single edge asserted for "the organism" turns a context-specific observation into a
   universal claim.
2. **Time erasure.** An immediate-early response, a feedback rebound and a steady state give
   different couplings from the same intervention. An edge with no time window is not testable.
3. **Circular support.** A graph used to constrain a prediction cannot also serve as independent
   ground truth for that prediction. Read statically, that circularity is invisible.

The design consequence is not "use a better graph". It is that **an edge is a conditioned
hypothesis**, and the agent's job is to find the measurement that would move it.

## 2. The conditioned edge

```
edge( source, target, relation, sign?,
      context, time_window, perturbation_state,
      evidence_kind, source_cluster, limitations )
```

Rules (**partial**, with structured retrieval now implemented):

- Every edge carries context, time window and the perturbation state under which it was
  observed. These are part of the edge, not metadata attached later.
- Contradictory context-specific edges **coexist**. Merging them into one universally true edge
  is forbidden; a query that spans both contexts returns both, with their conditions.
- An inferred edge is `model_prediction` or `retrieved_source`. It motivates a measurement; it
  never satisfies a premise and never licenses a mechanism claim.
- The reasoning graph and any predictor's internal graph stay separate stores, with separate
  update paths.

**Where this already bites.** The typed decision model may rank caller-supplied candidate
regulators. Its answer is labelled a hypothesis in the state text and in the finding itself,
and carries "no network edge is evidence". **Implemented.**

**Implemented retrieval contract (2026-09-25).** `agent.biology.BiologicalRelation` stores
species, tissue, cell type, context, perturbation and time separately, alongside evidence
type, claim level, method, database version, publication and entity scales. The existing
evidence ledger stores these assertions with registered source lineage; package imports
remain atomic. Known condition mismatches are excluded, unknown conditions are exposed,
and only matching relations expand structural retrieval. Opposite signs in overlapping
conditions are review candidates, never automatically adjudicated conflicts. Source
retraction removes their influence. `trace_evidence` follows declared ancestors and
descendants within the current case scope. Automatic discovery of biological mechanisms
and validation of caller-declared experimental support remain outside this contract.

## 3. The action graph is dynamic too

The agent's own reachability changes as it measures. The supplier topology is recomputed every
round against the current intervention profile, so:

- an action blocked in round 1 can be on the executable frontier in round 3, because its premise
  was measured in round 2;
- `steps_to_executable` shrinks as premises are satisfied;
- a capability gap can close when a new capability is registered, and only then.

This is the operational sense in which the system is dynamic rather than static: **what the
agent can do next is a function of what it has already established**, and that function is
recomputed rather than cached. **Implemented** (`maestro/topology.py`).

## 4. Complementarity and structural redundancy

### 4.1 Definitions

- Two evidence items are **complementary** when they constrain *different* open premises.
- They are **structurally redundant** when they constrain the same premise through the same
  original experiment — regardless of how many papers, databases or reviews report it.

Redundancy is not the same as replication. Replication is independent repetition; redundancy is
the same observation arriving by several routes.

### 4.2 Enforcement

| Mechanism | Effect | Status |
|---|---|---|
| Source clusters | Several reports of one experiment count once | implemented |
| Coverage over distinct premises | Bundle value counts premises covered, not items bought | implemented |
| Dependence groups in selection | Actions sharing a cluster do not multiply expected coverage | implemented |
| Modality attribution | Adding a modality is credited only with eligible cases and budget held fixed | design |

The registered bundle tool now reports leave-one-quantity-out coverage contributions for
the selected bundle, without replacement. This is an **implemented planning diagnostic**
under declared powers and dependence groups, not the empirical attribution experiment
above. Optional costs separate access, preprocessing, computation and new measurements
within one explicit unit. Public reuse cannot carry a new-measurement charge. The alignment
tool exposes unknown batches and suppresses directional comparisons across known unequal
batches; it does not fit batch correction or impute missing modalities.

### 4.3 The failure this prevents

Without clustering, a finding cited in three reviews narrows the compatible hypothesis set three
times, and a bundle of three redundant actions looks three times as informative as it is. The
decision that follows is confident for a reason that does not exist.

## 5. Multimodal and multiscale use

### 5.1 Scale table

| Scale | State variables | Intervention examples | Limit that must be stated |
|---|---|---|---|
| Molecular | Sequence, structure, binding, occupancy, activity | Mutation, inhibitor, degrader, rescue allele | Binding does not prove cellular efficacy |
| Intracellular network | Regulatory edges, signalling, pathway flux, feedback | Knockdown, acute inhibition | Inferred edges are hypotheses |
| Single cell | Transcriptome, chromatin, cycle, heterogeneity | Dose, time, genetic, environment | Out-of-domain and endpoint calibration are task-specific |
| Population | State distribution, resistant subpopulations, growth and death | Combination, sequential dosing | Means hide rare states |
| Multicellular | Communication, spatial organization, stromal and immune context | Co-culture, spatial intervention | Less standardized; later scope |
| Organism | Exposure, distribution, systemic response | Schedule, therapeutic window | Outside the first paper |

### 5.2 Rules for crossing scales

1. **Every bridge is declared.** Units, parameter identity, calibration data, uncertainty and
   scope. An unvalidated bridge is exploratory and is paired with a measurement that could test
   it.
2. **Latent coordinates are not parameters.** Feeding a learned embedding into a simulator
   parameter with a similar-sounding name is not a bridge.
3. **Shared-source correlation propagates.** Repeated use of one dataset does not create
   independent confirmation at three scales.
4. **Multi-omics is not multi-scale.** RNA plus ATAC is two modalities at one scale; it does not
   by itself produce a multicellular model.
5. **Imputation stays a prediction.** An imputed modality is never independent confirmation of
   its own input modality.

### 5.3 Cheap, available data first

Preference order for a first-stage study:

1. Already public, condition-level, and inexpensive to process.
2. Deployable from inputs available **before** the candidate is measured: structure, dose, time,
   cell background, a matched control, and where applicable one existing measurement of the
   current action.
3. Stated as three separate costs — access and preprocessing; training and running; inputs per
   new candidate at deployment.

A published processed feature table is neither intrinsically cheap nor intrinsically clean. The
recurring trap: normalization or feature selection fitted across all plates including the test
compounds, which quietly removes the inductive split. Refit on training units, or the split is
not a split. Asset-level detail: [`asrg/02_data_and_costs.md`](asrg/02_data_and_costs.md).

## 6. What would falsify the dynamic framing

If conditioning edges on context and time changes no decision relative to a static graph, at
equal evidence and budget, then the extra structure is cost without benefit and should be
dropped. The comparison is explicit and cheap to run:

- **Arm A** — context-aware and time-aware retrieval and edge use.
- **Arm B** — the same edges with conditions stripped, merged into one graph.
- **Arm C** — valid cross-scale links against permuted ones.

Measure decision regret and wrong-advancement rate, not retrieval overlap. If A does not beat B
on decisions, report that; the conditioning is then a hygiene property, not a contribution.

## 7. Acceptance tests

1. Two contradictory context-specific edges both survive ingestion and are both returned for a
   query spanning their contexts.
2. An edge with no time window cannot satisfy a premise that declares a time match.
3. Three reports of one experiment contribute coverage once.
4. A bundle of complementary actions, each individually useless, is selectable within budget.
5. An action blocked in an early round appears on the executable frontier after its premise is
   measured, without any cached topology being reused.
