# Scientific case memory: typed decision trajectories, adaptive retrieval and hypothesis graphs

**File summary**
- **Path:** `research/scientific_case_memory/README.md`
- **Purpose:** the dataset-independent library behind MAESTRO-VC v1: how a validated scientific decision
  trajectory is stored, versioned, retrieved and used to forecast, and how a memory is audited.
- **Core points:**
  - A case is a typed record (canonical, contrastive, failure or adaptation) whose measurements carry one of
    six statuses; a missing or failed condition is never a value. Cases are immutable and append-only.
  - Retrieval has four stages (hard compatibility, mechanism, state, adaptation-aware rerank) and returns the
    reasons for every case; the forecast weight multiplies structural similarity by every other term of the
    nine-term case score.
  - `CaseMemoryWorld` equals the repository's reference world when its extensions are off (tested to
    floating point), so any difference an extension makes is the extension's.
  - The retrieved hypothesis prior is advisory and never enters `EvidenceState`.
- **Interfaces / data:** case snapshots under `outputs/scientific_case_memory/`; results in
  `../maestro_vc_v1/REPORT.md`.
- **Depends on:** `../belief_planning/world.py`, `src/maestro/acquisition.py` (forecast containers).

| Module | Contents |
|---|---|
| `case_schema.py` | `Case`, `OpenProblem`, `MeasurementStatus`, `ReadingKind`, `EvidenceClass`, digests, `validate_case`. |
| `case_store.py` | Append-only digest-chained store, supersede, verify, deterministic snapshots. |
| `case_index.py`, `case_retrieval.py` | Reading-code tables, stage-1 hard filter, `PrecedentScorer`, `CaseRetriever`. |
| `adaptation_model.py` | Difference signatures, `AdaptationTable`, relative cost, transition matrices. |
| `world.py` | `CaseMemoryWorld`, `MemoryConfig`, the configured worlds and ablations. |
| `hypothesis_graph.py`, `evidence_cards.py`, `protocol_library.py` | Layered graph, evidence classes with refused promotion, costed protocol templates. |
| `build_cases.py`, `build_episode_replay.py`, `case_quality_audit.py` | Fold-scoped case building and typing; replay integrity and the leak probe; the ten-check audit. |
| `evaluate_case_retrieval.py`, `evaluate_decision_policy.py` | Forecast-level and decision-level metrics with unit-cluster intervals. |
| `test_case_memory.py` | Tests, including negative controls that plant a leak and require the audit to name it. |
