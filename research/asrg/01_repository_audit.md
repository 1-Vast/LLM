# ASRG repository gap audit

Read-only audit of `1-Vast/LLM` at commit `b41bab1`, branch `claude/sharp-bardeen-q4yt0t`,
identical to `origin/main`, clean working tree, no `AGENTS.md` or `CLAUDE.md` present.
No repository file was changed for this assignment.

Evidence labels: **SV** source-verified (read in this checkout), **LR** locally reproduced
(executed here 2026-09-25), **DO** document-only (asserted in a repo document, no artifact
here), **NA** not available in this checkout or blocked by network policy, **PR** proposed
(this report's design, not implemented).

## 1. What exists in this checkout

| Item | Status | Note |
|---|---|---|
| `src/{agent,maestro,virtual_cell,evaluation}` | SV | Four packages, layered import graph pinned by a test |
| `tests/` 70 modules | LR | `test_asrg.py` + `test_e0_dir.py` = 7 passed |
| `data/`, `log/`, `evaluations/`, `reference/`, `research/` | NA | Absent. `dataset/` holds only `README.md` (on 2026-09-26 `dataset/` was merged into `data/`; the tracked placeholder is now `data/README.md`) |
| SciPlex3 `.h5ad`, State checkpoint, prediction artifacts | NA | Referenced by code and by `ASSET_INVENTORY.json` (DO) |
| `state` Python package | NA | `import state` → ModuleNotFoundError; State cannot run here |

Consequence: every number in `ASRG_RESEARCH_UPDATE.md` (276 tasks, mean gain 0.5744,
CI [0.1193, 1.1382], 37.68% worse) is **DO** in this checkout. It cannot be recomputed here.

## 2. Virtual-cell request path

`PredictionRequest` → `assess_query` → `predict`, wrapped by `safe_predict`
(`src/virtual_cell/interface.py`, SV).

- `safe_predict` assesses once, then predicts once, and fails closed: invalid request,
  capability mismatch, wrong `request_id`, wrong `model_version`, contract violation, or a
  requested readout the backend did not declare all become a typed abstention. Backend
  exceptions and `SystemExit` become abstentions; `KeyboardInterrupt` is not swallowed. **SV**
- `StatePrediction.contract_errors` forbids an "applicable" prediction with no state change,
  and forbids an abstention that still carries estimates or intervals. **SV**
- `Interval` separates `DESCRIPTIVE` from `CALIBRATED`; only a calibrated band with a level
  and a named basis claims coverage. **SV**

**Can any backend accept an arbitrary latent vector?** No. `Intervention` carries
`identifier`, `mode`, `intended_targets`, `dose`, `dose_unit`, `time_hours` — no vector
field. No registered backend exposes a latent input. **SV**

## 3. State adapter and runner

`StateCapabilityAdapter` (`src/virtual_cell/state_adapter.py`, SV):

- Capabilities declare `supported_modes=("drug",)`, `requires_matched_control=True`,
  `supports_dose=False`, `supports_time=False`.
- `_static_issues` refuses: model-version mismatch; missing checkpoint, config or isolated
  Python; unregistered `dataset_id`; asset size or SHA-256 mismatch; feature-identity and
  input-basis problems; a context not registered for the dataset; an unmatched or
  unregistered control dataset; the control label used as the perturbation; **any** stated
  dose or `time_hours` ("must be represented by the exact registered perturbation label,
  not unvalidated continuous State inputs"); an unknown perturbation label.

`state_runner.subset` (SV) builds the query file from rows of the declared context whose
label is the control **or** the requested perturbation, and returns
`{"valid": false, "errors": ["no rows for the declared context contain the perturbation"]}`
when the condition has no rows. `validate` computes the condition shift as
mean(perturbation rows) − mean(control rows) in the embedding.

Upstream, Arc's `state tx infer` samples control cells as the basal input for treated cells
rather than reading treated cells' own embeddings (verified by fetching the upstream
`_infer.py`, external source). That does not rescue the point above: MAESTRO's own subset
step needs the condition's rows to exist in the registered asset before inference starts.

**Therefore:** the registered backend cannot score a candidate that has not already been
measured in the registered dataset, and cannot interpolate dose or time. A cheap,
matched-domain predictor is required for ASRG; this is a design constraint, not a defect.
A successful NCI-H596 call (DO, `ASSET_INVENTORY.json`) says nothing about A549, K562 or MCF7.

## 4. Coordinate identity and lineage

`write_shift_artifact` (`src/virtual_cell/artifacts.py`, SV) stores raw and calibrated
vectors side by side, names coordinates where a verified identity exists and marks the rest
unresolved, and records digests. `_feature_identity_problem` and `_input_basis_problem`
compare declared coordinate names, not just vector length. `load_feature_names` returns a
feature-identity SHA-256.

`PredictionPair` (`src/evaluation/e0_dir_core.py`, SV) carries `response_basis_id`,
`control_pool_id`, `projection_sha256` and enforces the residual identity at construction.
`E0Observation` carries `response_basis_id`, `source_id`, `independent_unit_id`, and
`score_observation` refuses an observation whose episode or basis does not match.

Reusable as-is for ASRG. Equal vector length is already treated as insufficient.

## 5. Hidden evaluation, selection, repair, cost

| Surface | Status | Behaviour |
|---|---|---|
| `evaluation/cases.py` | SV | `PublicCase` vs `RevealedEvidence`; `ReplayView` exposes only queried reveals; `RevealRefusal` carries a machine-readable code; `FinalTestRecord` is never reachable by a policy |
| `evaluation/runner.py` | SV | Per-run, per-policy, per-case isolated state directory; a provider failure is recorded as one lost case, not a lost run |
| `maestro/selection.py`, `acquisition.py` | SV | Exact budgeted coverage selection; expected-coverage selection with declared `detection_power`; blocked actions stay visible |
| `maestro/repair.py`, `contrast.py` | SV | Bounded repair ledger; `keep` / directed replacement / explicit deferral; adoption only after deterministic re-check |
| `maestro/topology.py` | SV | Executable frontier, steps-to-executable, **capability gaps** (premises nothing registered supplies), supply cycles — the discrete analogue of the proposed reachability certificate |
| `virtual_cell/applicability.py` | SV | `SupportLevel`, joint support slices, `receipt_level`; observed support is never promoted to validation |
| `evaluation/lab_cost.py` | SV | Wells and turnaround days; shared control charged once; an undeclared action refuses the whole sequence by name |
| `evaluation/provider_spend.py` | SV | API spend reserved and charged separately from laboratory cost |

**Does the original orchestration predict all actions before selecting a branch?** Yes when a
`VirtualCellQueryTemplate` declares `action_interventions`: one request per registered action,
answered at most once per distinct query per round, then used for ranking and for the repair
briefing (`src/agent/orchestrator.py`, SV; added earlier in this session).

**Can the model service see hidden treated rows?** Not through the replay path: reveals enter
only via `ReplayView` after a query. The ASRG pilot's own separation is weaker and says so —
`asrg.py` writes `public_plan.json` first and `evaluator_private.npz` beside it, with the
comment that file separation "is not an OS permission boundary" (SV).

## 6. E0-DIR prerequisites

| Prerequisite | Status |
|---|---|
| Independently valid `ideal_hat` source | **NA**. `ASSET_INVENTORY.json` records `frozen chemCPA checkpoint: not_registered` and `ideal_latent_adapter: missing_for_original_DIR_only` (DO) |
| Two paths sharing an exact response basis | Partially. `PredictionPair` enforces it structurally (SV), but the only running experiment supplies both paths from the same pipeline |
| A goal that is not derived from the candidate's own outcome | **Not met** in `dual_residual_experiment.py`: `g = np.mean(actual, axis=0)`, the mean of the model's own predictions, and `ideal = chemistry_context_neural` — a second predictor, not an ideal intervention (SV) |
| Private final observations for a fresh run | **NA** (DO) |
| CLI | `maestro-e0-dir` always writes `status: "not_run"` with a reason (SV) |

`visible_view(arm="corrupted")` already implements the falsification control for the
non-identifiability result: it adds η to `r_goal` and subtracts it from `r_realization`,
leaving the sum unchanged (SV).

## 7. Minimal integration surface (PR)

Smallest path that reuses valid contracts and leaves the default CLI and the original task
untouched:

1. **New module, no edits to existing ones.** `src/evaluation/asrg_geometry.py` for the
   anchor, shrinkage, certificate and selector; `src/evaluation/asrg_replay.py` for the
   frozen-plan runner. Both import from `virtual_cell.interface`, `virtual_cell.applicability`,
   `virtual_cell.artifacts`, `evaluation.lab_cost` and `evaluation.cases`.
2. **Reuse unchanged:** `safe_predict` fail-closed semantics; artifact digests and coordinate
   identity; `SupportRegistry` for `A_valid`; the public/private case split and refusal codes;
   lab-cost and provider-spend accounting; `paired_interval`-style cluster bootstrap.
3. **Do not reuse as truth:** `maestro.repair` branch semantics (ASRG operations are
   trust-region subsets, not identified causes); `MonotoneRealization` as a functional state;
   State condition labels as latent coordinates.
4. **Record on every predicted or derived vector:** model version and weights digest, feature
   schema and gene order, preprocessing, control-pool identifier, context, action registration,
   uncertainty type (descriptive vs calibrated), and prediction-versus-measurement provenance.
5. **New CLI entry only:** `maestro-asrg` with `prepare` / `evaluate` phases mirroring the
   existing frozen-plan pattern; `python -m agent` and `maestro-evaluate` behaviour unchanged.

Schemas are deliberately left unspecified until the pilot data is rebuilt (gate G1), because
the coordinate set depends on what the rebuild actually produces.
