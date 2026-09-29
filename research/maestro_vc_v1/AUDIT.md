# MAESTRO-VC v1: audit of the current implementation and the baseline before any change

**File summary**
- **Path:** `research/maestro_vc_v1/AUDIT.md`
- **Purpose:** the audit the design required before modification: what each named component is and
  does today, where a virtual-cell output can and cannot reach a decision, and the measured baseline
  the case-memory work was compared with.
- **Core points:**
  - `EvidenceState` is a set of compatible hypotheses, not a posterior; `OutcomeForecast` is a
    per-hypothesis reading distribution that already carries a named refusal and is always a model
    prediction; `PredictionRequest` has no hypothesis or history field, so the production request
    cannot express a forecast that is conditional on them.
  - The production `StatePrediction` is one scalar per readout. The hypothesis-conditional forecast
    the design asks for exists only in research code (`research/belief_planning/world.py`,
    `research/incontext_world/`, `research/dual_core/`).
  - Baseline: 1,395 production tests and 66 research tests passed before any change; the current
    reference world forecasts held-out readings with NLL 0.432, and its forecasts of a wrong
    elimination run about 2.1 to 2.4 times low on the actions a planner chooses.
- **Interfaces / data:** `outputs/maestro_vc_v1/baseline/` (test transcripts), the source files named below.
- **Depends on:** `research/gated_plan/AUDIT.md`, `research/dual_core_v2/README.md`,
  `research/topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md`.

Date of the audit: 2026-09-29, tree at `c3d2345` plus uncommitted work of other sessions. Nothing under
`src/` was changed by this work.

## 1. Instructions and concurrent activity

There is no `AGENTS.md`, `CLAUDE.md` or project instruction file beside `README.md`; the standing
requirements are in the working-standards notes and enforced by `tests/test_repository_shape.py`
(English-only markdown and Python, one dated record per working day under `log/`, no test module
importing another).

Other actors were active in the tree during this work: a WorkBuddy session was implementing item R0
(calibrated intervals, ledger guard, single-shot reconciliation) in `src/virtual_cell/`,
`src/maestro/` and `src/agent/`, and Codex sessions were drafting prompts. Everything new was written
under `research/scientific_case_memory/`, `research/maestro_vc_v1/`, `data/processed/maestro_vc_v1/`,
`data/manifests/`, `data/external/public_checks_20260929/` and `outputs/`, and nothing of theirs was
edited.

## 2. Component audit

| Component | Where | What it is | What it means for a case memory |
|---|---|---|---|
| `EvidenceState` | `src/maestro/outcome.py` | Frozen set of `candidates`, `eliminated`, append-only `UpdateRecord`s and source clusters. `apply` removes a hypothesis only when the interpretation is a real, QC-passed, mechanism-scope reading; a failed measurement updates feasibility only; a non-measurement is retained without effect. `resolved` means one candidate, `exhausted` none. | Hypothesis probabilities cannot live here. They are kept as a planning belief outside it and never remove a hypothesis. |
| `OutcomeForecast`, `OutcomeBranch` | `src/maestro/acquisition.py` | Per action, per hypothesis, a label-to-probability map with integer support; `refusal` names why no forecast exists; `evidence_kind` is `MODEL_PREDICTION` and a forecast that claims measurement status is refused. | The right container for a hypothesis-conditional forecast. It has no field for applicability, out-of-distribution status, an interval or calibration status, so the system layer adds them beside it. |
| `OutcomeForecaster` | same | A protocol: `forecast(contrast, actions, evidence)` returns a forecast per action. | Reused unchanged: the case-memory world is a subclass of the research reference world and feeds the same planner. |
| `PredictionRequest` | `src/virtual_cell/interface.py` | Request id, case id, contrast id, plan version, an `Intervention` (mode, targets, dose, time, functional profile), a `SystemContext`, readouts, model version. Validation refuses malformed identity, dose without unit, and profile/context mismatch. | No hypothesis field and no history field. A forecast conditional on either cannot be requested through it. Not changed here; adding optional fields belongs to a decision on whether a served rung can honour them. |
| `StatePrediction` | same | `applicable`, a `state_change` mapping readout to one float, a scalar `uncertainty`, limitations, optional `Interval`s (descriptive or calibrated), `confidence`, `in_distribution`, `abstain_reason`, named uncertainty components. | One scalar per readout: direction and magnitude are not separated and no hypothesis enters. This is the object the production selector can use, and it can only break a tie. |
| `CompositeWorldModel` | `src/virtual_cell/world_model.py` | One interface over a ladder of swappable rungs; eligibility decided per rung against the actual request; a contract-violating prediction becomes an abstention; simulation is billed as compute, never as experiment budget. | Sound plumbing. It has no rung that answers a hypothesis-conditional question. |
| `population_flow` | `src/virtual_cell/population_flow.py` | Experimental conditional population transport (CellFlow- and State-inspired), unpaired cells, no decision calibration by its own statement. | Not wired to any decision. `research/dual_core_v2` found it adds no mechanism signal beyond pseudobulk. |
| `state_adapter` | `src/virtual_cell/state_adapter.py` | Guarded adapter for the pinned State checkpoint: refuses any query whose endpoint, context, controls, input schema, asset or model version does not match a registered asset; runnable is not validated. | One registered STATE context; about 63 s per condition. It is the only served single-cell model. |
| `realization` | `src/virtual_cell/realization.py` | Realised dose as a monotone coordinate with an explicit identifiability statement; its ablations are declared, not run. | Names the nominal-versus-realised dose problem; the release tables here record nominal dose only and say so (`dose_realized` is empty). |
| `PredictionReliabilityLedger` | `src/maestro/reliability.py` | Grades predictions against later real values, per readout; only calibrated interval hits count; three consecutive misses revoke. Its own text says these are operational safeguards, not statistical certification. | Was empty in production (no calibrated intervals existed); the same-day R0 work opened the channel in code. A case memory needs its own calibration history, kept in each case. |
| Action selection | `src/maestro/selection.py`, `acquisition.py`, `contrast.py` | Budgeted minimum-cost set cover; a declared prediction priority may only break a tie between otherwise equivalent plans; a research discrimination selector and `DecisionValue` exist in `acquisition.py`. | Reused: the case-memory arms use the research belief planner and the registered rules; the production selector stays the `coverage` and `scalar_vc` comparison arms. |
| World-model briefing | `src/agent/world_model_briefing.py` | Renders predictions for the agent's reasoning, labelled planning-only; an abstention is "no supported answer", never a null effect. | The answer's model-prediction section follows the same boundary. |
| Splits and leakage | `research/protocol_v2/contracts.py`, `runner.py`, `design.py`, `tasks_v21.py` | Folds by independent unit (skeleton or component), a whitelist `PublicContext`, `public_view_problems`, a fail-closed `score` that refuses a missing or out-of-contrast truth, a menu fixed by the study design. | Adopted as the replay's boundary. The case-memory snapshot for fold *f* is built only from compounds outside fold *f*, and a test proves that changing every held-out label leaves its digest unchanged. |

## 3. Where a virtual-cell output reaches a decision today

Measured in this work's replay (6,601 episodes, tiers below), against the same episodes:

| Channel | Changes the first action | Changes the terminal decision |
|---|---|---|
| Scalar magnitude priority (`scalar_vc`) against the coverage selector | 100% (A), 99% (B), 46% (LT), 0% (T) | 20.5%, 44.5%, 0.9%, 0% |
| Hypothesis-conditional in-context virtual cell (`vc_incontext`) against the belief planner | 0% in every tier (no purchased prompt exists at step 0) | 2.9% (A), 1.6% (B), 0% (LT), 0.2% (T) |
| Case-memory reading terms (`cm_full`) against the belief planner | 5.0% (A), 0.6% (B), 0%, 0% | 0.4% (A), 0%, 0%, 0% |
| Retrieved hypothesis prior (`cm_full_prior`) against the belief planner | 11.3%, 8.0%, 9.1%, 7.0% | 3.4%, 1.0%, 4.0%, 1.8% |

The scalar channel changes almost every choice and is harmful (section 4 of the report); the
hypothesis-conditional channel is nearly inert; the two failures are opposite in kind. Independently,
the calibrated-interval channel was closed in production because no predicted-versus-realised pair
existed on disk (the same-day R0 record).

## 4. Baseline before modification

| Measure | Value | Source |
|---|---|---|
| Production tests | 1,395 passed, exit 0, 2026-09-29 11:10 to 11:12, `-x` (no failure to stop on) | `outputs/maestro_vc_v1/baseline/tests_full.txt` |
| Research tests, five packages (`protocol_v2`, `belief_planning`, `incontext_world`, `dynamic_world_model`, `premise_forecast`) | 66 passed, exit 0 | `outputs/maestro_vc_v1/baseline/tests_research.txt` |
| Data | SciPlex3: 188 compounds in 185 skeleton units, 3 cell lines, 24 and 72 h (72 h only in A549), four doses 10 to 10,000 nM, two replicate groups, 2,473 genes. L1000 (GSE92742 subset): 478 compounds in 335 component units, 4 cell lines, 6 and 24 h, one dose (10 uM), 978 landmark genes | `data/processed/maestro_vc_v1/`, `outputs/maestro_vc_v1/preprocess/validation_report.json` |
| Independent units per tier in the replay | A 34, B 105, LT 205, T 128 (334 in all) | `outputs/maestro_vc_v1/analysis/results.json` |
| Current reference-world forecast, all held-out (compound, condition, contrast) items | NLL 0.432; hypothesis discrimination 0.60 nats; observed to forecast wrong-elimination ratio 1.07; ECE 0.003 | same |
| Current planner, chosen actions | wrong-elimination observed to forecast 2.36 [1.50, 3.38] (the fixed order: 0.91 [0.42, 1.54]) | same |
| Decisions, correct rate (fixed / belief planner / oracle) | A 0.636 / 0.582 / 0.674; B 0.620 / 0.603 / 0.692; LT 0.058 / 0.066 / 0.100; T 0.244 / 0.235 / 0.247 | same |

The baseline is development evidence: every one of these tasks has been analysed before (protocol
v2 and later blocks), and GSE70138 was opened by an earlier session, so no untouched study exists
locally.
