# Minimal implementation plan

For MINIMAL_IMPLEMENTATION only when the owner selects it. **Nothing in this file has been implemented.** Items are
ordered by what blocks the selected experiments (E-DATA1, E-AG1 stage 0, E-CAL1).

- **Production default:** every P0 item is research-only. P1 items that touch `src/` keep old behaviour unless a flag
  is set.
- **Rollback:** every item is a new function or an optional argument. Reverting the file restores `e5ad68f`, and no
  registered record depends on it.

## P0: blocks E-DATA1 and any further use of the v2 runner

| ID | Issue (audit row) | Files and interfaces | Migration and compatibility | Test (must fail before, pass after) | Effort |
|---|---|---|---|---|---|
| P0-1 | The legal menu moves with an outcome; lifecycle and readout are merged (D8, D9, D10) | New `research/protocol_v2/design.py`: `sciplex_design_table()` from raw release groups (metadata columns only), `l1000_design_table()` from `inst_info`. Both are written once with a digest. `contracts.py`: `Lifecycle` enum; `design_availability(design, keys, compounds)`; `lifecycle_state(design_row, measured_row, qc)`. `runner.run_episode`: menu = planned conditions; buying a planned but excluded condition returns `MEASURED_QC_FAILED`, charged. | `availability` (row exists) and `MeasurementState` stay for registered v2 records. New records carry `lifecycle` plus `readout`. A derived `v2_state()` maps back losslessly. This is a protocol version bump, because 12 SciPlex3 decisions change. | (a) Dropping a held-out compound's measured rows leaves its menu digest unchanged. (b) The round trip over every registered v2 record reproduces its state. (c) Buying `A549 72 h 10 uM Panobinostat` returns `MEASURED_QC_FAILED` at cost. | 0.5 day |
| P0-2 | L1000 development pools read held-out detection outcomes (D7) | `contracts.py`: `fold_pools(labels, detected, fold_of, *, min_identities=6, min_detected=2)`, which applies the `lincs_prepare` rule to training compounds of each fold. Used by the E-DATA1 tier builder. | Historical tiers untouched and reported alongside. | Flipping held-out detection flags leaves every fold's pool unchanged. | 0.25 day |
| P0-3 | Point estimates are episode-weighted, and the weighting is unregistered (D3, V2) | `records.py` / `headroom.py`: `unit_mean` beside the episode mean; the CI resamples units for both. | Additive fields. | Unit mean equals episode mean when episodes per unit are constant; they differ on L1000 LT. | 0.1 day |

## P1: needed before E-CAL1 conclusions, E-AG1 stage 1 or E-JOINT1

| ID | Issue | Files and interfaces | Default behaviour | Test | Effort |
|---|---|---|---|---|---|
| P1-1 | An unregistered source counts as independent (E3) | `src/maestro/provenance.py`: `SourceClusterIndex.is_registered(source_id)`. `src/maestro/outcome.py` `EvidenceState`: new field `dependence_unknown: frozenset[str]`; an unregistered source goes there, not into `independent_source_clusters`, when `strict_dependence=True`. | Off by default; the owner decides. | The probe `evidence` returns 1 cluster plus 1 unknown. | 0.25 day |
| P1-2 | A lysate grant can satisfy an engagement premise with no site (E5) | Lint in `evaluation/cases.py` next to `PublicCase.untyped_premises()`: `unsited_engagement_premises()`. The case builder refuses to write a case that has one. | Existing packages are re-linted; engagement_v1 declares its context and should pass. | Constructing an unsited occupancy premise is reported. | 0.1 day |
| P1-3 | Calibration covers one arm, per step only; the stop gate accepts uninformative bounds (C1) | `research/protocol_v2/calibration.py`: `items(frame, arm=…)`, `episode_items(frame)`, and an informativeness clause in `stop_gate` (mean bound at most 3 times observed). | Research only. | Synthetic frames exercise each clause. | 0.25 day |
| P1-4 | Forecasts cannot reach repair selection (JOINT prerequisite; wiring row 12) | Evaluation-only arm in `evaluation/proposal_arms.py`: `ForecastRankedRepairPolicy`, which ranks admissible registry offers by `planning.plan_measurement` value from an `OutcomeForecaster`. No change to the orchestrator. | Not in production. | Build it **only when E-JOINT1 has a qualified task.** | 0.5 day |
| P1-5 | `OutcomeForecast` lacks version and domain fields (W1) | `src/maestro/acquisition.py`: `training_version: str \| None = None`, `calibration_version: str \| None = None`, `domain: Mapping[str, object] = {}`. | Backward compatible. | Payload round trip; existing forecasters unchanged. | 0.1 day |
| P1-6 | Research scoring is closed-world (E10) | `research/protocol_v2/contracts.py`: `score(trace, truth, *, open_set=False)`. With `open_set`, truth outside the pair makes `exhausted`, `deferred` or `undetermined` a correct rejection (utility 0, counted separately) and a singleton wrong (-2). | Default is the current fail-closed behaviour. | Unit test for each case. | 0.1 day |

## Backlog: governance improvements that block no selected experiment

| ID | Item (audit row) | Why it waits |
|---|---|---|
| B1 | Licence and append-only exposure fields in data sidecars (D1) | Exposure is reconstructable from logs for now; needed before EXT-1. |
| B2 | Record the identity match route per compound (D2) | Scoring labels do not depend on name joins in the current tasks. |
| B3 | Evaluator-process reveal for sealed cohorts (D6) | No sealed cohort exists locally; needed before EXT-1. |
| B4 | Column tags (metadata or outcome) in prepare manifests (D4) | The whitelist covers the v2 path; tags make it data-driven. |
| B5 | Absence-branch power rule in the validator (E7) | Changes a frozen validator; only in a new validator version. |
| B6 | Per-rule false-elimination risk field (E8) | Filled by E-CAL1 results. |
| B7 | Fixed-order fallback when every forecast is refused (P1) | `plan_measurement` is not wired into production. |
| B8 | Loss-sensitivity grid (wrong loss 1, 2, 4) (P2) | Part of any future planner registration. |
| B9 | Declare L1000 MODZ plate-population normalisation as transductive (D7) | Documentation only. |

## Skipped ideas and why

| Idea | Reason |
|---|---|
| A new evidence store, graph database or second registry | The typed records in `models.py` and `outcome.py` already hold kinds, scope, lineage and source clusters. The gaps are field-level (E3, E5), not architectural. |
| Wiring `plan_measurement` or the virtual cell into the production default | WM-G2 and WM-G3 fail, and AG-G2 is inconclusive. It would add an unvalidated path to production. |
| Training a larger or latent world model (JEPA, three heads, r(t) network) | WM-G1 fails for the current model. No realisation data exist (E-WM1b NOT_READY). Not authorised. |
| Conformal or risk-control guarantees across studies | Two development studies; exchangeability across studies is not credible. Allowed only as exploratory in E-CAL1. |
| Downloading LINCS 2020, CPJUMP1 or Tahoe-100M | Needs the owner's approval. A metadata-only census comes first; only JUMP/CPJUMP1 addresses the primary use case with measured pairing. |
| An LLM repair-proposal arm | LLM-specific value is not claimed. It would cost money, and deterministic-controller gains must not be attributed to it. |
| Promoting the `safe` arm | It departs from fixed in at most 0.24% of decisions: safe, but it gains nothing. |
| A knowledge-base-assisted track | No demonstrated hypothesis-generation gap. MoA entries would be an answer key for the proxy task. |
| Combination screening, toxicity, a third agent role | Outside the initial scope of the brief. |

## Resources

- **Engineering:** P0 about 1 day; P1-1, P1-2, P1-3, P1-5 and P1-6 about 1 day; P1-4 about 0.5 day, if unblocked.
- **Compute:** E-DATA1 at most 2 CPU hours. E-CAL1 takes minutes. E-AG1 stage 0 takes minutes.
- **Downloads:** none for P0, E-DATA1, E-CAL1 or AG stage 0. The CPJUMP1 and LINCS 2020 metadata census needs
  approval.
- **Spend:** $0. Laboratory: 0 wells, 0 days.
