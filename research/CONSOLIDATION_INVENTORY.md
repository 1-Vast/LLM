> **Historical source/tool audit, 2026-09-29:** section 5 records the earlier consolidation.
> The current core/tool boundaries and results are in `log/20260929/README.md` section 14.
> Sections 1-4 below are a historical research-promotion inventory from 2026-09-28;
> their statements about unchanged `src/` and older tool paths describe that earlier pass.

> **File summary**
> - **Path**: `research/CONSOLIDATION_INVENTORY.md`
> - **Purpose**: Phase A output of the consolidation task (`PROMPT_consolidation.md`): every
>   research block and root-level report, its self-declared verdict, freeze status, candidate
>   modules, and promotion destination, each tied to evidence.
> - **Core points**:
>   - No module earns promotion in this pass: every plausible candidate is explicitly marked
>     "do not promote" or "research standard only" by its own block's registered record.
>   - Two pre-existing freeze digest mismatches in `research/dual_core_v2/` are listed, not
>     resolved; they predate this consolidation.
>   - `task.md` section 11 predates the 2026-09-27/28 blocks; the lag is listed, not edited here.
> - **Interfaces / data**: input to `PROMPT_consolidation.md` Phase B and Phase C;
>   `research/README.md` (rewritten in Phase C); `log/20260928/CONSOLIDATION.md`.
> - **Depends on**: `PROMPT_consolidation.md`, `task.md` sections 11-12, `log/INDEX.md`,
>   each block's README and freeze records.

# Consolidation inventory (Phase A), 2026-09-28

Method: each block's README was read; verdicts are the blocks' own registered words, not this
inventory's judgement. Promotion qualification follows `PROMPT_consolidation.md` section 0.4
(measured under a frozen protocol, reproduced, positive on the registered gate) and section 1.4
(candidate rule of thumb, verified per block).

## 1. Block table

| block | verdict (self-declared) | frozen | candidate modules | destination | evidence |
|---|---|---|---|---|---|
| `acquisition_link/` | INCONCLUSIVE (selector stays opt-in) | no | none | stay | README section 1, 7: "Classification by the frozen rule: INCONCLUSIVE" |
| `acquisition_followup/` | negative (fixed sequence wins; SHADOW fallback negligible) | no | none | stay | README; `task.md` section 11 (sequence_audit paragraph) |
| `analysis/` | design/checks (small algebra and synthetic selection checks) | no | none | stay | `research/README.md` index row |
| `asrg/` | design, protocol unregistered and unrun | no | none | stay | `research/asrg/00_index.md`; `research/README.md` row |
| `belief_planning/` | INCONCLUSIVE external (GSE70138); REJECTED development; contract-pinned | `freeze.json` | none (planner.py must never move, contract) | stay | `task.md` section 11; `PROMPT_consolidation.md` section 0.1 |
| `biological_depth/` | negative for the latent model (JEPA ~= PCA, not promoted); retrieval library already promoted | no | none new (retrieval already in `tools/signature_retrieval/`) | stay | README; `task.md` section 11 (biological depth paragraph) |
| `dual_core/` | development screen; "Nothing is promoted" | no (digests live in its protocols) | none | stay | README; `research/README.md` row |
| `dual_core_v2/` | positive repairs as **research standard**; section 14: "Nothing above earns promotion" | `freeze.json`, `freeze_population.json` (see section 3 discrepancies) | risk_control.py, nested.py, transfer_honest.py, world3.py — all marked "Retain as the research standard" | **stay** (owner-registered recommendation) | README sections 0, 7, 14 |
| `dynamic_world_model/` | negative (no world-model component met its promotion rule) | no | none | stay | README "Result in one paragraph"; `task.md` section 11 |
| `experiments/` | archive (immutable evidence archives) | n/a | none | stay | README; `research/README.md` row |
| `external_validation/` | REJECTED under frozen gates; external test blocked | `freeze.json` | none | stay | `task.md` section 11; README |
| `gated_plan/` | design (audit and gated plan; not a registered experiment) | no | none | stay | README; `research/README.md` row |
| `incontext_world/` | E-WM1/E-WM2 PASS (positive gates) but promotion deferred to owner; dual_core_v2 section 12: "Do not promote" | no | ridge_st — explicitly not promoted by later registered record | **stay** | README sections 4-6; `research/dual_core_v2/README.md` section 12 |
| `knowledge/` | data/design notes (no experiment) | no | none | stay | directory contents |
| `local_verification/` | engineering probes (offline loop, prompt-state ablation) | no | none | stay | README; `research/README.md` row |
| `premise_forecast/` | NOT_READY (0 of 30 needed target genes with in-context premise measurement) | no | none | stay | README; `research/README.md` row |
| `prompt_review_20260927/` | review record (contains Chinese source material, test-exempt) | no | none | stay | directory; `tests/test_repository_shape.py` fallback note |
| `protocol_v2/` | development screen; E-DATA1 / E-CAL1 gates recorded | no | none | stay | README; `research/README.md` row |
| `scientific_optimization/` | exploratory pilots (README in Chinese, pre-existing exemption) | no | none | stay | `research/README.md` row |
| `sequence_audit/` | negative / SHADOW (fallback +0.0013 utility, not promoted) | `freeze.json` | none | stay | `task.md` section 11; README |
| `sparse_value/` | negative-leaning analysis | `freeze.json` | none | stay | `research/README.md` row; `task.md` section 11 (value arms) |
| `viability_contrast/` | negative / not-established (v1-v5b; world-model leverage measured as non-binding on this task-policy pair) | `freeze{,2,3,4,5,5b}.json` | none | stay | README sections 3.1-3.7; `log/20260928/VIABILITY_CONTRAST_V5B.md` |

## 2. Root-level report files (Phase C classification input)

| file | purpose (File summary block) | Phase C category |
|---|---|---|
| `agent_architecture.md` | agent architecture design | (a) agent and decision core |
| `decision_layer.md` | decision layer design (cross-references judgment_stability) | (a) agent and decision core |
| `typed_decision_model.md` | TypeSafe Jev contract | (a) agent and decision core |
| `dynamic_networks.md` | biological structure as conditional and changing | (b) virtual cell and world models |
| `virtual_cell_wm_audit_20260928.md` | VC world-model audit and assessment of two external proposals | (b) virtual cell and world models |
| `judgment_stability.md` | reproducibility as an admission test | (c) evaluation, risk control and validation methodology |
| `agent_research_20260925.md` | targeted design review (literature + task-state repair record) | (e) literature and design sources |
| `framework_optimization.md` | agent-first framework implementation session record (incl. first real STATE inference) | (f) engineering records |
| `engineering_record.md` | engineering record | (f) engineering records |
| `repository_cleanup_20260927.md` | repository maintenance disposition | (f) engineering records |

Inbound links that must be updated on the move: `task.md` (section 12, five links),
`Innovation.md` (two links), `research/decision_layer.md` (one cross-link),
`log/20260927/README.md` and `log/20260927/0927/premise_forecast_run_notes.md`
(repository_cleanup link). `outputs/` archives and `PROMPT_consolidation.md` are historical
records and are not edited.

## 3. Discrepancies (listed, not resolved — per task section 0.2/0.4)

1. **Pre-existing freeze mismatch, `dual_core_v2/freeze.json`** (written 2026-09-28 10:18:21):
   `research/dual_core_v2/test_dual_core_v2.py` no longer matches its frozen digest
   (`--verify` reports it under `changed`). Predates this consolidation; no file under
   `research/` is edited by the consolidation.
2. **Pre-existing freeze mismatch, `dual_core_v2/freeze_population.json`** (written 10:29:21):
   `research/dual_core_v2/analysis.py` no longer matches its frozen digest (manual digest
   check). Same disposition.
3. **`task.md` section 11 predates the 2026-09-27/28 blocks**: `dual_core/`, `dual_core_v2/`,
   `incontext_world/`, `premise_forecast/`, `viability_contrast/` have no section 11 entry.
   Their registered records are their own READMEs and `log/20260927/`, `log/20260928/`.
   Listed here; updating `task.md` section 11 is outside this consolidation's scope except
   where a promotion changes the verified list (none did).
4. **Block self-verdict vs index lag**: `research/README.md` (pre-Phase-C) lacks rows for
   `dual_core_v2/`, `viability_contrast/`, `prompt_review_20260927/`, `knowledge/`. Resolved
   by the Phase C rewrite.

## 4. Phase B outcome

Zero promotions. Reason, per candidate:

- **dual_core_v2 repaired risk-control pieces** (`risk_control.py`, `nested.py`,
  `transfer_honest.py`, `world3.py`): the block's own registered section 14 states
  "Production defaults and src/: Unchanged — Nothing above earns promotion", and section 0
  assigns each repaired piece "Retain as the research standard". Promoting against the
  block's registered recommendation would violate evidence discipline (task section 0.4).
- **incontext_world `ridge_st`**: positive on E-WM1/E-WM2 gates, but the block defers
  promotion to an owner decision requiring new contract tests, and the later registered
  record (`dual_core_v2` section 12) says "Do not promote". Not promoted.
- Everything else: negative, inconclusive, design-only, archive, or already promoted.

Consequence: `src/`, `tools/` and `tests/test_repository_shape.py` are unchanged by this
consolidation; no new tool folder is created; no contract test needs a same-commit update.

## 5. Current source and tool audit (2026-09-29)

This section records the later production-module consolidation. Every Python file in the four
`src/` packages and every former `tools/` directory was classified by current imports, public
exports, command entry points, manifests, and test coverage. The historical promotion decisions
above did not authorize a research model for production use.

| Package | Current files | Module responsibilities |
|---|---:|---|
| `src/agent/` | 11 | `orchestrator` executes turns; `planner`, `context`, `decision_critic`, `knowledge` prepare and review decisions; `llm`, `memory`, `tool_runtime` own providers, case persistence and manifest tools; `cli`, `__main__`, `__init__` expose the supported entry points. |
| `src/maestro/` | 19 | `models`, `decision`, `licence`, `repair`, `outcome`, `contrast`, `acquisition`, `composition`, `judgment`, `handoff`, `pharmacology` own evidence and decision contracts; `case_memory`, `case_update`, `hypothesis_forecast`, `adaptive_retrieval`, `problem_compiler`, `tool_analysis`, `model_replay` own the current case and prediction interfaces; `__init__` exports them. |
| `src/virtual_cell/` | 14 | `interface`, `applicability`, `artifacts`, `calibration` define prediction and refusal contracts; `state_adapter`, `state_runner`, `world_model`, `learned_response`, `ladder`, `signature_retrieval`, `biology`, `panel` implement current adapters/readouts; `__main__`, `__init__` expose the panel command and API. |
| `src/evaluation/` | 12 | `cases`, `capabilities`, `planning`, `policies`, `costs`, `runner`, `scoring`, `construction`, `engagement_sources`, `engagement_cases`, `cli`, `__init__` own the installed replay and source-backed case workflow. |
| `tools/` | 15 | Four capability/workflow directories plus root `__init__` and the checkout-local `research_validation` launcher. |

Tools now has four business directories, down from eleven. `data/` has one `tool.py` and
three named manifests; `evidence/` has one `tool.py` and three named manifests;
`prediction/` has one `tool.py` and two named manifests. `case_memory/` retains the one
registered case-memory manifest and its builders, audit, validation, workflow and benchmark
commands. Nine capability IDs retain distinct schemas and source fingerprints; the router
checks the selected named manifest again at invocation. Test-only biological and provider
fixtures are under `tests/fixtures/`, not a discoverable tool directory.

Python file counts: `agent` 22 to 11; `maestro` 30 to 19; `virtual_cell` 26 to 14;
`evaluation` 43 to 12; `tools` 25 to 15. Total 146 to 71. Merged modules were removed
directly; there are no one-line compatibility shims. Retired code includes disconnected
adaptive/admissible/contingent evaluation solvers, old model-validation and PRISM demonstration
runners, synthetic linear/Hill/one-hot world-model arms, and superseded sciPlex-v1 builder/QA
copies. Tests only for those retired APIs were removed. Current evidence, refusal, leakage,
replay and tool-boundary tests remain.

Supported command surfaces are `python -m agent`, `python -m virtual_cell panel`,
`python -m evaluation.cli`, installed `maestro-build-cases` and `maestro-screen-cases`,
`python -m evaluation.construction <build|screen>`, `python -m evaluation.scoring <adjudicate|table>`,
`python -m evaluation.engagement_cases`, and the grouped `tools.case_memory` commands
documented in `tools/README.md`. Former per-capability tool folders and old case-memory
audit/preprocess/replay/evaluate/download_sources/build_hypothesis_graph module paths are retired.

| Package | Retired module files merged into current owners |
|---|---|
| `agent` | `audit`, `cases`, `reflection`, `storage` into `memory`; `biology` into `knowledge`; `configuration`, `template_client`, `vision` into `llm`; `world_model_briefing` into `context`; `case_memory_wiring` into `planner`; `typesafe` into `decision_critic`. |
| `maestro` | `selection`, `topology` into `composition`; `reliability`, `stability` into `judgment`; `provenance`, `tool_contracts`, `policy` into `handoff`; `engagement` into `pharmacology`; `case_memory_pipeline` into `case_update`; `hypothesis_graph` into `problem_compiler`; `directional` into `adaptive_retrieval`. |
| `virtual_cell` | `receipts` into `applicability`; `identity_markers` into `artifacts`; `conditional_forecast`, `cache` into `interface`; `transcript_baselines` into `ladder`; `backends` into `world_model`; `response_rung` into `signature_retrieval`; `population_flow` into `learned_response`; `pathway_readout` into `biology`. |
| `evaluation` | Baseline, prediction-control, proposal and VOI policies into `policies`; lab/provider costs and tracking into `costs`; adjudication and score-table code into `scoring`; repair replay into `runner`; evidence-base, builder and screening code into `construction`; feasibility into `planning`; workbook reader into `engagement_sources`; engagement package into `engagement_cases`. |
| `tools` | Per-capability entry files into `data`, `evidence`, `prediction`; quality and figure checks into `case_memory.audit`; source/graph/pack/replay/evaluate commands into `case_memory.workflow`; forecast/calibration commands into `case_memory.validate`; benchmark into `case_memory.benchmark`. |

Verification: 1,444 production tests collected and passed; sciPlex-v2 QA 15/15 passed.
The benchmark builder produced 6,601 episodes and 49,304 action records in an isolated
directory. Decompressed public and hidden JSONL bytes match the existing data package
exactly. The gzip files differ across compression runtimes, while two rebuilds in this
runtime have identical compressed and manifest hashes. No independent biological performance
or execution-speed claim follows from this cleanup.
