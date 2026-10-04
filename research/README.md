> **File summary**
> - **Path**: `research/README.md`
> - **Purpose**: categorized portal to every research block and report; the master index.
> - **Core points**:
>   - Six categories: (a) agent and decision core; (b) virtual cell and world models;
>     (c) evaluation, risk control and validation methodology; (d) data, costs and assets;
>     (e) literature and design sources; (f) engineering records.
>   - Every entry carries a verdict label: verified / negative / inconclusive / design / archive.
>   - Code here is not part of MAESTRO's supported production decision path; the current
>     task and evidence boundaries are maintained in `task.md`; results belong to topical reports.
> - **Interfaces / data**: `CONSOLIDATION_INVENTORY.md` (per-block verdicts and evidence),
>   `topics/` (categorized root-level reports), `../log/INDEX.md`.
> - **Depends on**: `PROMPT_consolidation.md` (Phase C specification).

# Research

This directory contains experimental algorithms, analysis, protocols, and reproduction runners.
Its code is not part of MAESTRO's supported production decision path. This page is an index,
not a status report; verdict labels are the blocks' own registered words, cross-checked in
[`CONSOLIDATION_INVENTORY.md`](CONSOLIDATION_INVENTORY.md).
The new ASTRA entry uses its own current round reports; the dated consolidation inventory
remains a historical record and is not rewritten by this iteration.

Current ownership follows verified responsibilities rather than whole experiment scripts.
The [October 3 follow-up](astra/FEEDBACK_BOUNDARY_FOLLOWUP.md) records the exact migration.

| Lifecycle | Owner and entry point | Scientific status |
|---|---|---|
| Active engineering | `src/`, `tools/`, default `tests/`; exact result attribution and evidence admission | Software contracts only |
| Active research | ASTRA: cheap state × action ordering; intervention realisation and mechanism evidence | Bounded diagnostics/design; qualified biological confirmation still blocked |
| Completed, promoted | `certified_discovery/`: certified dual-core combination discovery (task.md Task 3) | Confirmatory PASS on NCI-ALMANAC for screen labels only; certificate, world model, loop, builders and replay promoted to `src/` and `tools/`; validated-discovery gain not shown (`astra/feedback_validation_20261003/`) |
| Completed, negative | `astra/feedback_validation_20261003/`: does in-context feedback give more independently validated discoveries? | Pre-registered on untouched Jaaks 2022 with plate-disjoint validation: NO_MEANINGFUL_GAIN (−1.1% [−4.0, +1.4]); addendum corrects the certified-discovery claims |
| Completed, exploratory; stopped | `astra/confirmation_campaign_20261004/`: under identical history, deadline and cap, does a confirmation-aware predictor beat strong simple rankings? | Exposed Jaaks data, contract frozen before outcomes. R − C_mean −5.96% [−13.36, +1.67] means WORTHWHILE_EXCLUDED → STOP. Two-orientation history +13.4%. No relative feedback value. Stopping saves 20% of measurements. The untouched Vis 2024 release is kept sealed |
| Completed, exploratory; 2×2 blocked | `astra/reproducible_allocation_20261003/`: can reproducibility-aware predictions improve how a fixed budget is split between screening, verification and stopping? | Exposed Jaaks data only. Equal-budget repair: verify-hits +17.7% over paired, but needs 5 rounds against 1. Repeat provenance corroborated, not authenticated. Development-fitted feedback (λ ≈ 0.3) does not improve candidate ordering. Static reproducibility-aware ranking +6.5%, mostly from richer history. No scheduler or LLM gain. No qualified data, so an executable protocol replaces the frozen 2×2 |
| Historical dependencies | `scientific_optimization/response_training.py`, `population_model.py`; LINCS `case_memory_integration/external_replay.py` | Frozen comparisons and inference dependencies; no active training expansion |
| Paused pending data | ASTRA measured-realisation and two-round biological comparison | Unregistered design; matched measurements, prices and power absent |
| Completed diagnostics | Dated reports/results and earlier negative/inconclusive blocks | Retain original claim boundaries and hashes |
| Reference archive | `research/data/`, results, baseline/snapshot/execution source copies, `experiments/` | Not active implementations or independent observations |

`python -m tools.research_validation` collects ASTRA entries by default. Explicit
historical collection uses `--include-archives`; this does not authenticate old
dependencies or qualify historical datasets. The supplied review copies remain
byte-preserved and excluded from routine collection.

Current maintenance scope is listed separately from each block's historical
scientific verdict. `Completed` below means no new method development is assigned
by this iteration; its tests and reproduction sources remain available and may
still be dependencies of fixed historical studies. No legacy schema is converted
or deleted solely because production has a similarly named concept.

| Directory or explicit research component | Lifecycle | Maintenance boundary |
|---|---|---|
| `astra/` input/decision and realisation diagnostics | active | Only the two questions above; [convergence report](astra/CONVERGENCE.md) defines boundaries and next discriminating work |
| `astra/realisation_plan.py` biological confirmation | paused | Matched actual-action measurements, prices and power missing |
| `scientific_optimization/` candidate fitting | paused; historical inference dependency | Restart only with a qualified independent task and frozen training/evaluation contract; existing model definitions remain available |
| `case_memory_integration/` | historical dependency; study completed | Small registered regression is explicit, shared builder in tools; no new replay variants |
| `scientific_case_memory/` | completed | Legacy schema/retrieval prototype; historical consumers retained; new research uses production schema |
| `belief_planning/`, `external_validation/`, `protocol_v2/` | completed | Frozen historical benchmark dependencies; no new implicit layered pipeline |
| `viability_contrast/`, `sequence_audit/`, `acquisition_followup/` | completed | Negative or limited results retained; no parallel variant expansion |
| `acquisition_link/`, `sparse_value/` | paused | Inconclusive candidate methods; no default activation |
| `dynamic_world_model/`, `biological_depth/`, `incontext_world/`, `dual_core/`, `dual_core_v2/` | completed | Historical model comparisons and promotion restrictions remain binding |
| `identifiability_audit/`, `dual_core_followup/` | completed | Historical attribution and source-boundary studies; source/result archives excluded from current-code views |
| `dual_core_completion/`, `dual_core_live/`, `maestro_vc_v1/` | completed | Engineering/live/replay records; scientific limitations retained |
| `dataset_discovery/`, `premise_forecast/`, `local_verification/` | completed | Prepared-data, source and feasibility checks; no new task admitted by directory status |
| `analysis/`, `asrg/`, `gated_plan/` | paused | Design/probe proposals; need explicit experiment before any scientific claim |
| `knowledge/`, `topics/`, `prompt_review_20260927/` | archived | Reference/design documents; no experiment-state authority |
| `data/`, `experiments/`, results and baseline/snapshot/execution source copies | archived | Byte-preserved evidence or supplied references; explicit historical access |

Historical source and verdicts remain accessible. Default pytest runs the asset-free
core list in `pyproject.toml`; registered replay and full research are explicit scopes.
No missing assets are converted to passing or skipped tests by this maintenance index.
The three permissions are distinct: engineering contracts verified, scientific
gain supported, and default activation allowed. See the field-level schema audit
and responsibility matrix in [the latest follow-up](astra/RESPONSIBILITY_FOLLOWUP.md).

## (a) Agent and decision core

| Path | Verdict | Contents |
|---|---|---|
| [`topics/agent_decision_core/agent_architecture.md`](topics/agent_decision_core/agent_architecture.md) | design | Agent architecture design record. |
| [`topics/agent_decision_core/decision_layer.md`](topics/agent_decision_core/decision_layer.md) | design | Decision-layer design (links the judgment-stability admission test). |
| [`topics/agent_decision_core/typed_decision_model.md`](topics/agent_decision_core/typed_decision_model.md) | design | TypeSafe Jev contract. |
| [`belief_planning/`](belief_planning/README.md) | inconclusive | Conditional outcome model, belief planner, GSE70138 replay. External: INCONCLUSIVE; development: REJECTED in SciPlex3 A. Contract-pinned: `planner.py` never moves. |
| [`acquisition_link/`](acquisition_link/README.md) | inconclusive | Distribution-aware selection study and controls; repair stays opt-in. |
| [`acquisition_followup/`](acquisition_followup/README.md) | negative | Two-step policy follow-up; fixed sequence wins; fallback SHADOW. |
| [`sequence_audit/`](sequence_audit/README.md) | negative | Early-stop diagnosis; frozen fallback rule negligible (+0.0013 utility), not promoted. |
| [`sparse_value/`](sparse_value/README.md) | inconclusive | Sparse-reference value analysis. |
| [`gated_plan/`](gated_plan/README.md) | design | Repository audit and gated research plan; not a registered experiment. |
| [`local_verification/`](local_verification/README.md) | design | Offline and credential-dependent engineering probes. |
| [`dual_core_live/`](dual_core_live/README.md) | inconclusive | Actual DeepSeek/Jev API validation, general contract benchmark, biological pilot and report-only defect review; no assumed biological superiority. |
| [`certified_discovery/`](certified_discovery/README.md) | verified | Certified dual-core discovery: in-context EB world model + agent + design-based audit certificate; pre-registered confirmatory run on NCI-ALMANAC (60 lines) passes both tests (+2.58 hits per line over static retrieval after paying for the audit; FDR 0.043, yield coverage 0.958); context and uncertainty null; LLM planner null on development and untestable on confirmation (every selection invalid at k~128); world-model claims 1.6x optimistic. Later the same day: the gain is a screen-label gain; on an untouched screen with plate-disjoint validation feedback gave no validated gain ([report](astra/feedback_validation_20261003/REPORT.md)). |
| [`astra/`](astra/README.md) | inconclusive | Decision/feedback contracts, EGR1 audit, eight-question review, [GDSC audit](astra/GDSC_INDEPENDENT_REVIEW.md) and [later-layout transport/pilot preparation](astra/GDSC_TRANSPORT_FOLLOWUP.md); no certified causal state or agent gain. |

## (b) Virtual cell and world models

| Path | Verdict | Contents |
|---|---|---|
| [`topics/virtual_cell_world_models/dynamic_networks.md`](topics/virtual_cell_world_models/dynamic_networks.md) | design | Biological structure as conditional and changing. |
| [`topics/virtual_cell_world_models/virtual_cell_wm_audit_20260928.md`](topics/virtual_cell_world_models/virtual_cell_wm_audit_20260928.md) | design | Module-by-module VC world-model audit; assessment of two external proposals; staged plan. |
| [`topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md`](topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md) | design | Dual-core obstruction map: link-by-link evidence for where information dies (forecast side vs decision side vs structural gate) and the ordered research programme R0-R4. |
| [`dynamic_world_model/`](dynamic_world_model/README.md) | negative | No world-model component met its promotion rule; learned transition +0.283 cosine, +0.003 decision. |
| [`biological_depth/`](biological_depth/README.md) | negative | Latent model matched PCA, not promoted. Structure retrieval carried the depth (promoted earlier: `tools/signature_retrieval/`, `virtual_cell.response_rung`). |
| [`incontext_world/`](incontext_world/README.md) | inconclusive | E-WM1/E-WM2 passed their gates; promotion deferred (owner decision; dual_core_v2: "Do not promote"). |
| [`dual_core/`](dual_core/README.md) | negative | Development screen; central negative result on selected-action risk forecasts. Nothing promoted. |
| [`dual_core_v2/`](dual_core_v2/README.md) | verified | Verified repairs (risk control, calibration lineage, transfer errors, world contract) retained as the **research standard**; section 14: nothing earns src promotion. |
| [`viability_contrast/`](viability_contrast/README.md) | negative | v1-v5b: no realistic arm certifies; world-model leverage measured as non-binding on this task-policy pair; next step is reformulation. |
| [`scientific_case_memory/`](scientific_case_memory/README.md) | verified | Case memory library: typed, append-only cases, four-stage adaptive retrieval, hypothesis graph, evidence cards, fold-scoped case building, audits. Parity with the reference world is tested to floating point. |
| [`maestro_vc_v1/`](maestro_vc_v1/README.md) | negative | Closed-loop case-memory replay on 6,601 real episodes: no terminal-decision or calibration benefit (23 of 23 screens `NO_DEVELOPMENT_SIGNAL`); failure and negative cases essential; adaptation helps unseen conditions; hypothesis-conditional beats scalar forecasts. Development evidence; report and audit inside. |
| [`scientific_optimization/`](scientific_optimization/README.md) | inconclusive | Exploratory pilots (README in Chinese); its PASS was superseded by dual_core_v2. |

## (c) Evaluation, risk control and validation methodology

| Path | Verdict | Contents |
|---|---|---|
| [`topics/evaluation_methodology/judgment_stability.md`](topics/evaluation_methodology/judgment_stability.md) | design | Reproducibility as an admission test for a judgment source. |
| [`external_validation/`](external_validation/README.md) | negative | Baseline ladder and firewall; maestro_vc REJECTED under frozen gates; external test blocked. |
| [`protocol_v2/`](protocol_v2/README.md) | negative | Development screen with E-DATA1 / E-CAL1 decision and calibration gates. |
| [`premise_forecast/`](premise_forecast/README.md) | negative | Premise-forecast qualification: NOT_READY (0 of 30 needed target genes). |
| [`experiments/`](experiments/README.md) | archive | Immutable evidence archives and exact historical replay instructions. |
| [`analysis/`](analysis/) | design | Small algebra and synthetic selection checks. |

## (d) Data, costs and assets

| Path | Verdict | Contents |
|---|---|---|
| [`knowledge/`](knowledge/) | design | Data and knowledge notes. |
| [`../data/INVENTORY.md`](../data/INVENTORY.md) | verified | Data-asset inventory: what stays in the tree, what moved to the archive, and the citing rule. |

## (e) Literature and design sources

| Path | Verdict | Contents |
|---|---|---|
| [`topics/literature_design_sources/agent_research_20260925.md`](topics/literature_design_sources/agent_research_20260925.md) | design | Targeted design review (literature + task-state repair record). |
| [`asrg/`](asrg/00_index.md) | design | Action-Supported Repair Geometry audit and proposed protocol; not run or registered. |
| [`prompt_review_20260927/`](prompt_review_20260927/) | design | Prompt-review records (contains Chinese source material; test-exempt). |

## (f) Engineering records

| Path | Verdict | Contents |
|---|---|---|
| [`topics/engineering_records/framework_optimization.md`](topics/engineering_records/framework_optimization.md) | verified | Agent-first framework implementation record, including the first real STATE-checkpoint inference. |
| [`topics/engineering_records/engineering_record.md`](topics/engineering_records/engineering_record.md) | design | Engineering record. |
| [`dual_core_completion/`](dual_core_completion/README.md) | verified | Registered dual-core runtime contracts and offline closure; 21 dataset/version qualifications and source hashes. Final suite: 1,526 passes plus one inherited prose-policy failure; biological terminal benefit remains unestablished. |
| [`dual_core_followup/`](dual_core_followup/README.md) | inconclusive | Primary literature and three no-training experiments: 19,704 paired policy paths, a real case-memory denominator audit and 44,520 frozen value-scope queries. Anchor benefit over fixed remains unestablished; source uncertainty and evidence boundaries retained. |
| [`topics/engineering_records/repository_cleanup_20260927.md`](topics/engineering_records/repository_cleanup_20260927.md) | verified | Repository maintenance disposition of 2026-09-27. |
| [`CONSOLIDATION_INVENTORY.md`](CONSOLIDATION_INVENTORY.md) | verified | Consolidation Phase A: per-block verdicts, freeze status, promotion evidence (zero promotions). |

## Corrections and caveats (retained)

Historical performance figures from the transcriptomic mechanism-class task do not establish
missing-premise repair benefit. The corrected fixed-order/oracle maximum is 99.4%; older dated
records are retained as written with corrections recorded in the later audit. A research plan or
registry specification is not a completed or registered experiment. Negative and inconclusive
blocks stay in place with their READMEs; they are neither deleted nor promoted.

## Reproduction

Run core source contracts from the repository root with `python -m pytest`.
The [convergence report](astra/CONVERGENCE.md) gives registered replay restoration,
Linux verification and full-research commands. Run the protocol-v2
test suite with `python -m pytest research/protocol_v2 -q`. The registered `belief-planning-1`
experiment is reproduced from archive commit `83b9aa9`; see
[`experiments/README.md`](experiments/README.md). Its GSE70138 study was consumed and cannot serve
as unopened external confirmation.
