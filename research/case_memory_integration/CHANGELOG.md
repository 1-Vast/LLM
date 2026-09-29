# Changelog: case-memory production integration

> **File summary**
> - **Path**: `research/case_memory_integration/CHANGELOG.md`
> - **Purpose**: every change this task made to the repository, in execution order, with the reason.

## 2026-09-29

### Repository protection
- Created branch `codex/case-memory-production-integration` in place from `main` (`c3d2345`);
  the dirty tree (133 entries, including the uncommitted prior research prototype) is preserved.
- Recorded `outputs/case_memory_integration/repository_baseline.json`.

### Frozen registration
- Wrote and froze `PROTOCOL.md` (`freeze_protocol.json`, sha256
  `3758bf2e40a5f67d962fb645b673c875d178b12011cd6dccbbe164e3e7730231`) before any LINCS 2020
  signature value was read.

### New production modules (all default-safe)
- `src/maestro/case_memory.py`, `directional.py`, `hypothesis_graph.py`, `adaptive_retrieval.py`,
  `hypothesis_forecast.py`, `case_update.py`, `problem_compiler.py`, `case_memory_pipeline.py`;
  `src/agent/case_memory_wiring.py`; `src/virtual_cell/conditional_forecast.py`.

### Backward-compatible extension
- `src/virtual_cell/interface.py`: `PredictionRequest` gained optional `hypotheses`, `history`,
  `observation_context`, `forecast_mode` with conditional validation; `FORECAST_MODES` defined
  here. Old construction, payloads and plain cache keys are unchanged (regression-pinned in
  `tests/test_conditional_forecast_interface.py`).

### Tooling
- `tools/case_memory/`: registered runtime tool (`manifest.json`, `tool.py`) plus CLIs
  `download_sources`, `preprocess`, `build_cases`, `build_hypothesis_graph`, `replay`,
  `quality_audit`, `evaluate`, `visual_verify`.
- `tools/registry.yaml`: registered `case_memory`.

### Test updates (deliberate, shape-contract changes)
- `tests/test_repository_shape.py`: tool set now includes `case_memory`.
- `tests/test_structured_tools.py`: same, with an explicit `MODEL_PREDICTION` branch for it.
- `tests/test_tool_boundaries.py`: catalog set now includes `case_memory`.

### New tests (66)
- `tests/test_case_memory_integration.py` (32): the registered suite of repair item §17.
- `tests/test_conditional_forecast_interface.py` (11): backward-compatibility and conditional
  validation regressions.
- `tests/test_case_memory_orchestrator.py` (15): user-state-conditional forecasts, the gated
  pipeline, the orchestrator path with the flag off and on, the tool contract.
- `research/case_memory_integration/test_external_evaluation.py` (8): split, validator, leak
  probe, missingness, frozen hash, episode schema.

### External evaluation artifacts
- `data/external/lincs2020/level5/level5_beta_trt_cp_n720216x12328.gctx` (35,518,405,386 bytes,
  sha256 `fbb04a94d8aa8a4fa6daf01f7d94dcd938fb9b7937730f81bfba3d8d0f1472a8`; raw data, **not
  committed**) and `sha256.json`.
- `data/processed/case_memory_integration/` (pack, arrays, manifest).
- `outputs/case_memory_integration/`: `external_source_manifest.json`, `results.json`,
  `forecast_items.jsonl`, `quality_audit.json`, `evaluation_summary.json`,
  `episodes/reference_cases.jsonl.gz` (65 episodes), `hypothesis_graphs.json`,
  `figures/` (7 figures), `figures_manifest.json`, `lincs2020_unseen_metadata.csv`.
- `research/case_memory_integration/`: `PROTOCOL.md`, `DESIGN.md`, `AUDIT.md`, `REPORT.md`,
  `CHANGELOG.md`, `freeze_protocol.json`, `external_data.py`, `external_replay.py`,
  `test_external_evaluation.py`.

### Behaviour changes
- None by default. `MAESTRO_CASE_MEMORY_ENABLED` unset means: no forecaster from the environment
  wiring, typed refusals from the pipeline and tool, and the orchestrator's pre-integration
  behaviour, all pinned by tests.
