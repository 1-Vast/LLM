# Agent-first framework implementation

The agent owns the scientific question, competing hypotheses, admissible action catalogue,
evidence budget and stopping decision. A virtual cell supplies conditional predictions.
TypeSafe Jev supplies typed second opinions. Neither supplies an experimental observation.

## Implemented changes

1. **Conditioned knowledge.** `BiologicalRelation` distinguishes experimental, computational
   and hypothetical support, and correlation, regulatory association and causal effect.
   Attention and feature importance cannot be encoded as regulatory or causal assertions.
   A declared causal effect requires a perturbation method and named controls. This is schema
   validation, not independent verification that an experiment established causality.
2. **Context-aware agent retrieval.** The orchestrator supplies the intervention profile's
   context and time to retrieval, and species when a prediction request or template provides it.
   Other conditions are available through `BiologicalConditions`; missing values remain
   unknown. Known mismatches are excluded. Unknown-condition assertions can inform planning
   with explicit caveats but cannot expand the graph for a matched query.
3. **Conflict and provenance.** Opposite signs remain separate assertions. Overlapping
   conditions produce a review candidate; disjoint conditions do not. Candidate records
   retain evidence IDs, source locations and hashes. `trace_evidence` supports both directions
   through declared lineage and respects retraction, case and private-data boundaries.
4. **Complementarity and costs.** The existing exact bundle selector retains source dependence
   groups and now exposes the selected bundle's loss of expected coverage when a quantity is
   removed. It does not rerun a replacement search for this diagnostic. Optional cost components
   sum to the action price in one declared unit; unknown breakdowns are reported as null.
5. **Multimodal quality control.** RNA, protein, occupancy, activity, morphology and chromatin
   accessibility keep distinct quantities. Optional batch IDs expose unknown or unequal
   batches. Known unequal batches cannot generate directional-discordance candidates.
   Sample matching, missingness and source dependence checks remain in force.
6. **Jev receives evidence.** Previously the orchestrator passed the plan, topology and virtual
   cell rows but omitted the available evidence-summary argument. It now passes the same
   bounded, provenance-preserving context used for planning. Its answers remain advisory,
   and untested ranking reproducibility cannot earn selection authority.

These mechanisms map onto concrete biological concerns: condition matching handles
context-specific regulation; signed conflict candidates expose activation/inhibition
ambiguity; time-specific retrieval prevents combining early responses with later feedback;
quantity-level coverage measures complementary measurement capabilities. This change does
not introduce a neural network module named after a biological mechanism or simulate a
dynamic GRN. Establishing feedback requires suitably timed intervention measurements.

## Relation ingestion

Use `EvidenceLedger.add_biological_relation(...)` with registered `source_ids`, or add a
`biology` object to a constraint in the existing versioned knowledge-package format:

```json
{
  "subject": "GENE_A",
  "relation_type": "activation",
  "object": "GENE_B",
  "evidence_type": "hypothesis",
  "claim_level": "regulatory_association",
  "method": "hypothesis",
  "conditions": {
    "species": "human",
    "tissue": null,
    "cell_type": null,
    "context": "declared-cell-context",
    "perturbation": null,
    "time_hours": 24
  },
  "database": null,
  "database_version": null,
  "publication": null,
  "subject_scale": "gene",
  "object_scale": "gene",
  "controls": [],
  "limitations": ["Schema example only; no biological relationship is asserted."]
}
```

Unknown metadata are null, not invented. The surrounding constraint still requires its
statement, limitations and package source IDs. Imported publications remain `retrieved_source`,
including publications reporting experiments. A local prediction can cite a prior assertion
through `lineage_ids`; tracing that prediction returns its source ancestors, and tracing the
assertion returns dependent predictions. Lineage is declared when the prediction is stored;
the system does not infer which biological sources trained an external model.

Run with additional packages:

```powershell
python -m agent "Your fully specified biological question" `
  --actions actions.json --profile intervention_profile.json `
  --knowledge-package research/knowledge/framework_constraints.json `
  --decision-critic auto
```

For a bundle action, optional `data_origin` is `existing_public`, `existing_local` or
`new_experiment`. Optional `cost_breakdown` has four required numeric fields: `access`,
`preprocessing`, `compute`, `new_measurement`. Every component uses the enclosing `cost_unit`;
incompatible units must be converted explicitly before using this single-budget selector.
Free download does not imply zero processing cost. Missing cost information stays unknown.

## Data and mechanism evaluation priorities

| Scientific question | Public data to assess first | Additional information | Main limit |
|---|---|---|---|
| Transcriptional perturbation realization | Staged Tahoe / sci-Plex expression and matched controls | Condition-specific RNA response | Training overlap, batches and RNA-only endpoints |
| Regulator-to-gene hypothesis | Matched RNA + ATAC, reviewed GRN resources | Accessibility constrains candidate regulatory connections | Accessibility and coexpression do not establish causality |
| Protein mechanism | Reviewed PPI/pathway resources and public proteomics | Binding, complex membership and protein state | Physical interaction is not necessarily directed regulation |
| Drug/genetic disagreement | Public perturbation screens and matched functional assays | Separates incomplete perturbation from alternative explanations | Distal fitted viability is insufficient for target mechanism |
| Feedback or state transition | Matched time series and perturbations with orthogonal controls | Timing and conditional activation/inhibition | Snapshot associations cannot establish feedback |

Use source clusters to avoid treating the same experiment reported in multiple databases
as replication. Do not merge unmatched samples by gene symbol alone. Existing virtual-cell
connectors retain explicit quantity, units, conditions, calibration and bridge limitations
when crossing scales; this change adds no unvalidated gene-to-tissue shortcut.

The first empirical comparison should hold cases, candidate menu, visible evidence and
budget fixed: conditioned vs condition-stripped retrieval, source deduplication vs naive
counting, each modality withheld, agent with/without supported virtual-cell predictions,
and Jev enabled/disabled. Report wrong mechanism advancement, correct deferral, decision
regret, measurement cost, preprocessing/compute cost and provider tokens. The new coverage
diagnostic is not a substitute for these outcome-based ablations.

## Literature provenance

On 2026-09-25, Europe PMC returned the following indexed metadata and abstracts:

- Adduri et al., *Predicting cellular responses to perturbation across diverse contexts with
  State*, Cell, first publication 2026-08-31,
  [doi:10.1016/j.cell.2026.07.052](https://doi.org/10.1016/j.cell.2026.07.052).
- Badia-I-Mompel et al., *Gene regulatory network inference in the era of single-cell
  multi-omics*, 2023,
  [doi:10.1038/s41576-023-00618-5](https://doi.org/10.1038/s41576-023-00618-5).

The retained [knowledge package](knowledge/framework_constraints.json) includes the exact
abstracts and their SHA-256 values, publication dates and source identifiers. Full texts were
not verified. The State journal article is newer than the preprint already in the local
knowledge collection; its abstract does not validate the staged checkpoint. This was a
targeted source check, not an exhaustive current-literature review.

## Verification

Environment: `D:/anaconda/envs/maestro/python.exe`. The original suite passed all 1,236 tests
after restoring the local `data -> dataset` junction. Initial missing-file failures resulted
from stale path resolution, not missing experimental evidence. The junction is local and
ignored by Git; no original data were moved or overwritten.

The complete suite passed **1,256 tests** in 53.01 seconds after the changes. The XML and
console records are `outputs/framework_optimization/final.xml` and `final.txt`.
Run all offline regressions with `python -m pytest`. New contract tests cover retrieval
conditions, conflicts, source retraction, epistemic promotion, lineage isolation, atomic
imports, retained abstract hashes, modality contribution and batch/cost boundaries.

Real provider smoke runs and the public-data loop are retained under
`outputs/framework_optimization/`. The live planner and Jev operate on explicitly synthetic
fixture scenarios. The State integration query deliberately uses an unregistered compound
to check abstention propagation. The public PRISM loop stops at `awaiting_result` with no
imported result, and `result_quality_failed` when a fitted curve lacks the required biological
quality; neither eliminates a mechanism hypothesis. These checks establish execution and
boundary behavior, not biological prediction accuracy or improved scientific decisions.

A separate real State checkpoint inference used registered Tahoe condition
`[('Bortezomib', 0.05, 'uM')]` in `NCI-H596`. It completed on the local CUDA runtime and
returned `embedding_delta_l2 = 1.000238462464976` (raw: `5.328971645494894`). The backend
reported approximately 63.23 seconds of inference work. Validation remains `unknown`,
distribution membership is null, and no target mechanism or measured effect follows from
this scalar. Request, artifact lineage and limitations are in
`outputs/framework_optimization/state_real.json`.

The integrated live run made two planner calls (5,296 reported tokens) and received six
usable Jev answers from `jev-1.13.0`, with no Jev refusal. It selected `rna_high` from the
registered fixture menu and preserved both unsupported State query refusals. Provider token
counts here are the text client's meter, not a combined dollar invoice for text and Jev.
Verification also exposed State artifacts ignoring `--state-directory`; the CLI and default
orchestrator backend now keep them under the isolated run, unless an explicit artifact
directory is supplied. Smoke artifacts created at the old location were moved into the run.
