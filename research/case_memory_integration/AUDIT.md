# Audit: repository state, implementation inventory and integrity checks

> **File summary**
> - **Path**: `research/case_memory_integration/AUDIT.md`
> - **Purpose**: the audit record required before integration: the repository baseline, the audit
>   of the pre-existing implementation, the new-code inventory, the integrity checks and their
>   results, and the deviations from the frozen protocol.
> - **Depends on**: `outputs/case_memory_integration/repository_baseline.json`,
>   `outputs/case_memory_integration/quality_audit.json`, `freeze_protocol.json`.

## 1. Repository baseline (measured)

Recorded in `outputs/case_memory_integration/repository_baseline.json` before any edit:

- HEAD `c3d2345` on `main`; remote `git@github.com:1-Vast/LLM.git`; branch
  `codex/case-memory-production-integration` created in place.
- The working tree was dirty: 133 status entries, including the uncommitted research prototype
  this task builds on (`research/scientific_case_memory/`, `research/maestro_vc_v1/`,
  `research/protocol_v2` v2.1 files, `research/viability_contrast/` and others). A worktree from
  HEAD would have excluded that prototype, so the branch was made in place and unrelated
  modifications are preserved and excluded from the final commit.
- Test baseline: 1395 collected, full run green (all passing); the two `git ls-files`-dependent
  markdown tests pass because git is on PATH in this environment.

## 2. Audit of the pre-existing implementation (measured, file-level)

| Area | Finding |
|---|---|
| `research/scientific_case_memory/case_schema.py` | Rich episode schema (scm-1), six measurement states, four case kinds, digests, `OpenProblem` without a truth field. Missing: negative/bridge/real-user-episode kinds, branching plans, retrieved-case records. Frozen by `research/maestro_vc_v1/freeze.json`; extended in production instead of edited. |
| `build_cases.py:200` | Confirmed Problem C: observations carry only the scalar `transcriptome_shift_norm` (`np.linalg.norm(data.shift[row])`); the signed vector exists in `data.shift` and was collapsed. |
| `case_retrieval.py` / `world.py` | Four-stage retrieval with the nine-term score, Kish support, advisory bounded prior; `CaseMemoryWorld` subclasses the research reference world (Problem B: no production virtual-cell integration). |
| `research/maestro_vc_v1/REPORT.md` | Development-grade verdicts: no terminal-decision improvement, no calibration improvement, failure/negative cases essential, hypothesis-conditional beats scalar as a forecast, replay is development evidence only (every tier previously analysed; GSE70138 opened; misled-neighbour stratum 18 units). |
| `src/virtual_cell/interface.py` | `PredictionRequest` had no hypothesis/history/context/mode inputs; `StatePrediction` single-branch. The orchestrator's `outcome_forecaster` seam existed with no production implementation. |
| `src/virtual_cell/cache.py` | Cache identity deliberately strips case/contrast/plan/request ids; a conditional forecast needs the extended identity (provided by `conditional_forecast.conditional_cache_key`). |
| `tests/test_repository_shape.py`, `test_structured_tools.py`, `test_tool_boundaries.py` | Hard-coded tool sets; updated deliberately together with `tools/registry.yaml` for the new `case_memory` tool (this was the full-suite failure of repair item 1). |
| `data/external/lincs2020/provenance.json` | Metadata-only exposure before this task: the census column allowlist; signature values and quality columns declared `never_read`. LINCS 2020 was the pre-registered untouched-source candidate of `research/protocol_v2/protocol.json`. |

## 3. New production code inventory

| File | Purpose |
|---|---|
| `src/maestro/case_memory.py` | scm-2 episode schema, validation, append-only digest-chained store, feature flag |
| `src/maestro/directional.py` | directional features, feature arms, realisation record, cosine |
| `src/maestro/hypothesis_graph.py` | typed hypothesis/evidence graph with hyperedges and promotion boundary |
| `src/maestro/adaptive_retrieval.py` | four-stage adaptation-aware retrieval with explanations |
| `src/maestro/hypothesis_forecast.py` | `OutcomeForecaster` over the store, `UserStateContext`, calibration-labelled detailed receipts |
| `src/maestro/case_update.py` | decision-value ranking, branching plans, append-only ingest with the five outcome states |
| `src/maestro/problem_compiler.py` | user-problem compiler: identifiers, units, controls, replicates, missingness, directional summaries, OOD, hypotheses, actions |
| `src/maestro/case_memory_pipeline.py` | the gated end-to-end production path |
| `src/agent/case_memory_wiring.py` | feature-flagged orchestrator wiring (agent -> maestro direction only) |
| `src/virtual_cell/interface.py` | four optional request fields with conditional validation (backward compatible) |
| `src/virtual_cell/conditional_forecast.py` | `ConditionalStatePrediction` and the conditional cache identity |
| `tools/case_memory/` | registered runtime tool plus the evaluation CLIs (download_sources, preprocess, build_cases, build_hypothesis_graph, replay, quality_audit, evaluate, visual_verify) |
| `research/case_memory_integration/` | frozen protocol, external data pack builder, replay, tests, this audit, design, report, changelog |

## 4. Integrity checks and results (measured)

- `python -m tools.case_memory.quality_audit`: 6 checks, 0 failures
  (`outputs/case_memory_integration/quality_audit.json`): source/pack checksums; split integrity
  against GSE92742+GSE70138 block lists; no zero-filled or non-finite condition vectors; the leak
  probe (detection thresholds and class centroids are reference-membership-only, verified by
  reconstruction); forecast metrics finite; frozen protocol hash unchanged.
- Split: 5 pool classes, 65 reference blocks (244 vectors), 26 unseen test blocks (28 vectors),
  112 forecast items; no test block appears in either development study's `trt_cp` block list.
- Evidence boundary: 91 evaluation hypothesis graphs, 0 promotable edges - nothing in the
  external evaluation is qualified experimental evidence, by construction.
- Episodes: 65 reference episodes written to
  `outputs/case_memory_integration/episodes/reference_cases.jsonl.gz`, all valid under scm-2,
  `data_origin: real`, `label_kind: curated_annotation_proxy`; store digest verifies.

## 5. Deviations from the frozen protocol (recorded, not smoothed)

1. **Pool-rule wording.** The protocol's rule text says "at least 12 reference blocks", but its
   own registered population count (5 classes, 26 unseen, 67 reference) was produced by the
   reference-plus-unseen reading, and the implemented population (65 reference blocks)
   deterministically assigns blocks carrying two MoA annotations to one class. Under the stricter
   reference-only reading, JAK inhibitor (11) and PARP inhibitor (10) would leave the pool. The
   hashed protocol is not rewritten; the implemented rule matches the protocol's registered
   population and is what the tests pin.
2. **Metadata acquisition predates the freeze by two days** (2026-09-27 vs 2026-09-29). Exposure
   was limited to the declared census columns; no signature value or quality column was read
   before the freeze. The Level 5 matrix itself was downloaded after the freeze and parsed only
   by the frozen code.
3. **clue.io retirement.** The source site retired on 2026-01-31; the S3 build objects remain
   accessible and were used directly. The license is "not stated in the files; clue.io terms of
   use apply" - recorded as such, not guessed.
