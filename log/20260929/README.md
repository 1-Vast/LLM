> **File summary**
> - **Path**: `log/20260929/README.md`
> - **Purpose**: Day record for programme item R0 — open the lawful-influence channel from the
>   virtual-cell world model to agent decisions: scored, revocable, and without changing any model,
>   any default ranking, or any historical record.
> - **Core points**: Phase-0 pair audit found zero predicted-vs-realised pairs on disk, so the
>   calibration asset could not be fitted; the owner chose the data-free route, and the engineering
>   repair landed without new data. The channel is open in code and closed in production until pairs
>   are generated.
> - **Interfaces / data**: `src/virtual_cell/calibration.py`, `src/virtual_cell/state_adapter.py`,
>   `src/maestro/contrast.py`, `src/maestro/repair.py`, `src/agent/orchestrator.py`,
>   `data/virtual_cell/registry.json`.
> - **Depends on**: `PROMPT_R0_calibration_channel.md`,
>   `research/topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md`,
>   `research/topics/virtual_cell_world_models/virtual_cell_wm_audit_20260928.md`.

# R0 — Open the lawful-influence channel (2026-09-29)

Date: 2026-09-29. Executor: WorkBuddy agent session. Specification:
`PROMPT_R0_calibration_channel.md` (designed 2026-09-29). Spend: $0, 0 wells, 0 downloads,
0 STATE inferences.

## 1. Record control

No experiment run was active or unrecorded at start. Test environment is
`D:\anaconda\envs\maestro\python.exe` (3.11.16); every command below was run with it. Owner
decision recorded in section 9: the data-free route.

## 2. Research questions and hypotheses

Three defects were to be repaired, each a stated obstruction in
`research/topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md` section 4 (R0):

- **H1 (gate cannot open).** `_calibrated_model_support` requires a coverage-claiming interval for
  the action's readout, and the STATE adapter emits `intervals={}`. Falsified by a test in which a
  STATE prediction with a bound calibration carries a `CALIBRATED` band and the action certifies.
- **H2 (ledger cannot fire).** `PredictionReliabilityLedger` grades only `interval_hit` on
  coverage-claiming bands, so with no calibrated intervals it is always empty; and `_score_prediction`
  is reached only from `run_case_loop`, never from the single-shot path. Falsified by a test in which
  a single-shot `import_measurement` produces exactly one `prediction_reliability_scored` event.
- **H3 (gate ignores the ledger).** Falsified by a test in which three consecutive calibrated misses
  flip the same action from certifying to non-certifying while the band itself is unchanged.

## 3. Materials, data and computational environment

- Code under repair: `src/virtual_cell/calibration.py`, `src/virtual_cell/state_adapter.py`,
  `src/maestro/contrast.py`, `src/maestro/repair.py`, `src/agent/orchestrator.py`.
- Registry read, not written: `data/virtual_cell/registry.json` (one scale calibration, one receipt
  `c39-x-hvg-shift-crossfit-20260913`).
- Real asset present and not read: `data/external/arc_state/tahoe_metadata_source/c39.h5ad`
  (653,318,588 bytes).
- Environment verified for the deferred option only: `state` importable under the test interpreter,
  with `anndata` 0.12.19, `numpy` 2.4.6, `scanpy` 1.11.5.
- Measured cost of one STATE inference, taken from the one real artifact that exists:
  `wall_seconds = 63.233`.

## 4. Experimental design and controls

Four test modules, each pinning one repaired boundary, written against the behaviour the defect
predicts and run before the repair was considered done:

| Module | Pins |
|---|---|
| `tests/test_virtual_cell_interval_calibration.py` | conformal quantile index, reproducible fit and support counts, binding refusals over endpoint / context / model version / input schema / control protocol / partition digest |
| `tests/test_state_adapter_intervals.py` | `CALIBRATED` when a receipt validates, `DESCRIPTIVE` when it does not, empty when no calibration is bound or the partition disagrees |
| `tests/test_discrimination_gate_revocation.py` | certification before revocation, loss of certification after three consecutive misses, and certification restored when the ledger argument is withdrawn |
| `tests/test_single_shot_reconciliation.py` | one scored event per single-shot import, duplicate-ignored on re-import, neither for a QC-failed or context-mismatched result, and reconciliation of an authorized reveal |

Controls kept deliberately: `None` for the ledger argument preserves the behaviour every caller had
before it existed (proved by the same test that proves the guard); a provisional record with fewer
graded pairs than the ledger needs withholds revocation rather than inventing one.

## 5. Experiment register and results

**Measured (commands run in this session):**

- `python -m pytest tests/test_repository_shape.py -q` — 2 failures, both the documented
  environmental ones (`test_project_markdown_has_no_chinese_prose`,
  `test_tracked_markdown_is_never_empty`); the two log-structure assertions were made to pass by
  writing this record and updating `log/INDEX.md`.
- `python -m research.viability_contrast.freeze --verify` for v1, v2, v3, v4, v5, v5b —
  `all_match: true` in all six.
- `python -m pytest tests/ -q -p no:warnings` — 1381 passed, 2 failed, the 2 being the documented
  environmental shape-test failures. Baseline before the repair was 1367 passed, 2 failed; the
  difference is 14 new tests, all passing.
- `python -c "import src.agent, src.evaluation, src.maestro, src.virtual_cell"` — clean.
- CJK scan of every new and edited file under the shape test's own stripping rules — zero
  violations.

**One regression found and fixed during verification:** threading the ledger into
`RepairController.run` made `src/maestro/repair.py` call `check_contrast` with four arguments, and
the two stub agents in `tests/test_repair_ledger.py` declared only three. Their signatures were
widened with `reliability=None`, mirroring the real method; no assertion in that file changed. This
is recorded rather than left silent because it is the only existing test file this repair touched.

**Not established:** that any of this improves a decision. The four-arm ablation is R1 and gates on
this repair's acceptance; no ablation was run.

## 6. Deviations, failures and corrections

**The deviation is the whole shape of this record.** Phase 0 was specified as a read-only pair audit
with an explicit stop rule, and the audit found nothing to calibrate on.

### 6.1 Audit method

Target: predicted-vs-realised pairs for `embedding_delta_l2` on endpoint `x_hvg_perturbation_shift`,
context `NCI-H596`, model `state_generalization_zeroshot_X_hvg`. Searches: filename globs
(`*crossfit*`, `*partition*`, `*shift*`); content greps (`NCI-H596`, `embedding_delta_l2`,
`development_partition`, `fit_scale`, `863`, `d64e6387`, `ebb40bf3`); binary-array enumeration
(`*.npz`, `*.npy`).

### 6.2 What the registry promises

- `scale_calibrations[0]`: `fitted_on` = "863 development conditions (fold 3 held out), all vehicle
  wells, reference seed-42 run"; `independent_units` 303; `development_partition_sha256`
  `ebb40bf31f8ed4aa192e6ae7875617a8e9aad234b365873944c737276c67dfa6`.
- `receipts[0]`: `c39-x-hvg-shift-crossfit-20260913`, "5-fold drug-level cross-fitting over 379 drugs
  with disjoint vehicle wells", `artifact_sha256`
  `d64e6387bf4e7ac50788fa6bdbd6cc4e97055bb6a49f15533f88e65e74c1974d`, `holdout_verified: false`,
  `passed: true`, with a caveat stating the comparator is uninformative.

### 6.3 What exists on disk: zero pairs

1. `log/20260913/` **does not exist**. `log/` held only `20260915`, `20260925`, `20260926`,
   `20260927`, `20260928` and `INDEX.md`. Every 2026-09-13 provenance path cited in the registry
   (for example `log/20260913/real_path/provenance/feature_identity_verification.json`) is dangling.
2. No file matches `*crossfit*` anywhere in the repository.
3. `development_partition_sha256` `ebb40bf3...` occurs in exactly three places: `registry.json`, the
   provenance of the single artifact in item 5, and the R0 prompt itself. **No partition definition
   file exists** — nothing names the 863 conditions or identifies fold 3.
4. No c39 partition file exists. The only two `partition.json` files are pytest fixtures under
   `outputs/followup_full_tests/` and `outputs/sparse_value/tests_runtime/`.
5. Exactly **one** real STATE shift artifact exists:
   `outputs/framework_optimization/state/framework-state-real-1.shift.json`, one condition,
   `wall_seconds` 63.233, no realised counterpart. The other ten `*.shift.json` files are pytest
   fixtures.
6. No condition-level predicted-vs-realised array store exists under `data/`. The three arrays in
   `data/external/arc_state/` belong to a different pipeline: `operator_calibration/singles.npz`
   (8994 x 2000 cells), `combo_input.npz` (12278 x 2000 cells), `hvg_alignment_sample.npz`
   (512 x 62710 / 512 x 2000).
7. `PredictionCache` (`src/virtual_cell/cache.py:39-49`) is in-memory only, so no prediction was
   ever persisted through it.
8. Fold coverage: none. **Fold 3 was never read by anything since the scale fit**, because nothing on
   disk carries it.

### 6.4 Consequence, and the correction made

A held-out coverage split is impossible from existing artifacts, so no calibration asset and no
coverage receipt were written. This is the specified stop condition (constraint 0.8), and the
registry was left byte-identical. What shipped instead is the code path, fully tested, with no
calibration bound in any production configuration.

### 6.5 One design correction made during implementation

`IntervalCalibration.binding_mismatches` checks `development_partition_sha256`, but a query carries
no partition of its own. The adapter therefore offers the partition this endpoint's calibration
lineage names — the scale calibration's `development_partition_sha256`. Two consequences, both
recorded rather than hidden: an interval fitted on another split refuses, and an interval cannot be
served at all when no scale calibration names a partition.

## 7. Interpretation and claim boundaries

- **Measured:** the three defects are repaired in code and pinned by 14 new tests; the full suite
  shows no regression; all six freezes still match.
- **Proposed:** nothing. No decision gain is claimed, and none was measured.
- **Not established:** whether anything improves decisions through the opened channel. That is R1.
- The channel is **open in code and closed in production.** No `IntervalCalibration` is bound in any
  workspace configuration, so a STATE prediction still emits `intervals={}`, the ledger still grades
  nothing, and `_calibrated_model_support` still returns `False` for a STATE readout. The repair
  makes the channel usable; it does not yet carry anything.
- A calibrated interval is a planning-only coverage statement. It is not a measurement and does not
  make the prediction it surrounds one. No wet-lab, target-engagement or clinical claim is made.

## 8. Reproduction and artifact ledger

- Files changed: `src/virtual_cell/calibration.py` (added `conformal_quantile`, `ResidualPair`,
  `IntervalCalibration`, `fit_interval`), `src/virtual_cell/__init__.py` (exports),
  `src/virtual_cell/state_adapter.py` (config field `interval_calibration`, `_intervals`, provenance
  entry), `src/maestro/contrast.py` (`reliability` through `check_contrast` ->
  `_outcome_separation` -> `_calibrated_model_support`), `src/maestro/repair.py` (`reliability`
  through `RepairController.run`), `src/agent/orchestrator.py` (ledger at four `check_contrast` and
  two repair call sites; reconciliation registry, `_reconcile`, and the removal of the now-redundant
  `_score_prediction` call inside `run_case_loop`).
- Files added: four test modules above; this record.
- Files widened, no assertion changed: `tests/test_repair_ledger.py`, two stub-agent signatures.
- Files not touched: `data/virtual_cell/registry.json` (byte-identical), every `freeze*.json`, every
  file under `research/`.
- Idempotence on the single-shot path is the existing `record_pair` dedup
  (`src/maestro/reliability.py:102-121`); no second mechanism was added.

## 9. Open items and next experiments

1. **The blocker.** Generate the missing pairs. The realised side needs no inference (mean `X_hvg`
   over a condition's measured cells minus the control mean, from `c39.h5ad`); the predicted side
   needs one `state tx infer` per condition at 63.2 s. Priced: 863 conditions ~= 15.2 h;
   120 ~= 2.1 h; 60 ~= 1.1 h; 30 ~= 32 min.
2. **Declare the partition first.** The 863-condition partition and its fold assignment have no
   definition file. Any regeneration must write one, with a digest, before fitting.
3. **Power must be disclosed, not discovered.** A 0.90 quantile fitted on 48 residuals is the
   fifth-largest residual; coverage measured on 12 held-out conditions has a 95% Clopper-Pearson
   interval of [0.735, 1.000] if all 12 are covered and [0.615, 0.998] if 11 of 12 are, either
   way too wide to falsify nominal 0.90 at that n. Either pay for a larger split or register the
   receipt as under-powered. (The earlier draft of this item quoted "roughly [0.62, 1.00]"
   without the hit count; the two intervals above are the correct 12/12 and 11/12 cases.)
4. **Then** refit `IntervalCalibration`, write `data/virtual_cell/state_interval_calibration.json`,
   register the coverage receipt with `holdout_verified` set truthfully, and bind the calibration in
   the workspace configuration. Only then does the channel open in production.
5. R1 (directional readouts, four-arm ablation) remains gated on this acceptance.

## 10. Curation provenance

No file was moved, renamed or deleted from `research/` or `data/`. The two pre-existing
`research/dual_core_v2/` freeze mismatches recorded in `log/20260928/CONSOLIDATION.md` section 6
were left unresolved, as specified. `log/INDEX.md` was updated in the same pass. No opportunistic
refactoring was performed: the only removal is the `_score_prediction` call that the new
reconciliation path orphans (`src/agent/orchestrator.py`, inside `run_case_loop`).

## 11. Caller inventory for the ledger guard

The ledger is now passed at every `check_contrast` call site that has one available:

| Site | Ledger |
|---|---|
| `src/agent/orchestrator.py` (`_check_and_repair`) | `self._reliability` |
| `src/agent/orchestrator.py` (LLM-repair recheck) | `self._reliability` |
| `src/agent/orchestrator.py` (`_review_plan`) | `self._reliability` |
| `src/maestro/repair.py` (both rechecks) | threaded from the orchestrator caller |

A repair-path caller constructed without an orchestrator still passes `None` and keeps the behaviour
it had; this is the one caller class left without a ledger, and it is the deliberate default rather
than an oversight.

## 12. Same-day follow-up audit and cleanup (second session)

A later session the same day audited the R0 statistical and provenance boundaries and ran a
repository cleanup. No new biological or decision evidence was generated; $0, 0 wells, 0 STATE
inferences. Production calibration remains disabled: the registry carries no `interval_calibrations`
entry and no coverage receipt.

**Correctness repairs (each pinned by new tests):**

1. `conformal_quantile` clamped the order statistic to the largest residual when
   `ceil((n + 1) * level) > n` (n <= 8 at nominal 0.90) and still claimed nominal coverage. It now
   refuses by name; `fit_interval` checks support per readout and refuses the whole fit; nonfinite
   and invalid inputs are refused. Tests: `test_virtual_cell_interval_calibration.py` (3 new),
   replacing one that encoded the clamping.
2. Coverage receipts were bound to intervals only by readout and model name (context, level,
   calibration identity and coverage-specificity unchecked). `ValidationReceipt` gained
   `calibration_sha256`, `nominal_level` and `holdout_basis`, plus `qualifies_coverage`, which fails
   closed; `IntervalCalibration.content_sha256` is the stable digest receipts bind to; the STATE
   adapter and the SciPlex rung serve CALIBRATED only through it. Tests: 7 new negative tests in
   `test_state_adapter_intervals.py`.
3. The registry loader now reads an optional `interval_calibrations` section (production has none),
   so a future calibration binds through configuration exactly as declared (1 test).
4. The reliability ledger's consecutive-miss rule counted one pooled sequence, so another context's
   hit could break a failing context's run and hide a local failure. It now counts per context
   within the scope and fires on the worst local run; pooled miss-rate hiding is documented, the
   pooled scope string is explicit (`@all-contexts`), and the rules are documented as operational
   safeguards, not certification (1 new test). Ledger persistence: still in-memory only; restart
   loses scored history and unresolved pairs — documented at the orchestrator, no subsystem built.
5. The SciPlex rung's coverage receipts now state their holdout basis precisely (185 skeleton
   groups; what was verified out-of-fold; the post-hoc informativeness width gate and external
   pretraining exposure named as not covered), and item 3 of section 9 now quotes the correct
   12/12 and 11/12 Clopper-Pearson intervals with the hit count.

**Cleanup:** `inspect/unzip/` (90 files, verified a strict subset of `inspect/source.pptx`'s zip
entries) deleted as reproducible; `inspect/source.pptx` retained. `tmp/` lost 12 uncited one-off
diagnostics (`vc_*`, dual-deck styling scripts and renders); files cited by scientific records
(`genetic_refit_posthoc.py`, `smoke5.py`, `smoke5b.py`, `prism_census_probe*`) and the user-facing
0927 deck drafts were retained. `src/` import inventory found no dead modules. Test count moved
from 1383 to 1395 (12 new, 1 replaced; recount verified by collection after the run); full suite
green. Freeze status: viability_contrast v1-v5b
all_match; dual_core_v2's two pre-existing mismatches (`test_dual_core_v2.py`,
`analysis.py`) remain exactly as recorded in `log/20260928/CONSOLIDATION.md` section 6.

A second re-audit the same evening re-ran the corrected import inventory and reference greps. The
11 modules it flagged (`agent`, `evaluation.*` submodules, `maestro.{engagement, licence,
pharmacology, policy, tool_analysis}`, `virtual_cell.{population_flow, realization}`) all have
live consumers in tests/ or research/; `evaluation.exclusion_{discontinuity, licensing}` are
pinned by their own test files and by
`research/topics/engineering_records/repository_cleanup_20260927.md`, so `src/` still contains no
dead modules. The remaining `tmp/` bulk (15 items: the 0927 deck build/render workflow, whose
scripts write to the owner's Desktop, plus the synergy report/roadmap renders) is uncited by any
scientific record but is owner work product outside this audit's deletion authorization; it stays
pending an explicit owner decision.

## 13. Block 3: MAESTRO-VC v1, an evidence-grounded case memory (separate session)

Owner: the user's own session (not WorkBuddy, not Codex). This block is scoped to its own work; blocks 1
and 2 above (R0 and the follow-up audit) are another actor's and are not claimed here. The full report is
`research/maestro_vc_v1/REPORT.md` and the audit and baseline are `research/maestro_vc_v1/AUDIT.md`.
Spend: $0 provider cost, 0 wells; about 240 public metadata queries (Figshare, PubChem, ChEMBL), no data
file downloaded. Nothing under `src/` was changed.

**Brief.** Build and evaluate a closed-loop decision-support system in which a structured case memory
(canonical, contrastive, failure and adaptation cases), adaptive retrieval, a hypothesis graph and a
hypothesis-conditional virtual-cell forecast feed action selection by terminal-decision value, with
append-only updating after real results.

**Code and architecture.** New packages `research/scientific_case_memory/` (schema, append-only store, index,
four-stage retrieval, adaptation model, hypothesis graph, evidence cards, protocol library, case builder,
audits, evaluation) and `research/maestro_vc_v1/` (sources, validation, tables, views, second case family,
replay and arms, analysis, stress and update tests, decision-support system, figures). `CaseMemoryWorld`
equals the reference world when its extensions are off (maximum probability difference 0) and the
case-memory belief arm reproduces the existing arm's decisions (0 mismatches over 61 episodes).

**Measured results.**

- Replay of 6,601 real episodes (20 development tasks, 334 units, 14 arms), 0 integrity problems: every
  arm returns `NO_DEVELOPMENT_SIGNAL`; only tier B has headroom (0.072); `cm_full_prior` against fixed in B is
  -0.011 [-0.034, +0.014].
- Forecasts over 49,304 held-out items: all memory worlds NLL 0.432 to 0.433, no detectable difference from
  the current world; chosen-action wrong-elimination under-forecast 2.35 to 2.46 times for every planner
  (fixed order 0.91). Removing failure and negative cases raises NLL by 5.02 [4.76, 5.28].
- Unseen-condition stress test: adapted minus pooled NLL -0.082 [-0.110, -0.054]; priced cost against error
  Spearman 0.50. Closed-loop update: -0.0034 nats [-0.0067, -0.0003].
- Data: eleven validation checks pass, including the SciPlex3 stray-header offset; public checks agree on
  Figshare licences and the local SciPlex3 MD5, on 106 of 118 PubChem connectivity blocks, and on 12 of 13
  ChEMBL targets (manual reading).
- Tests: 1,395 production and 66 research tests passed before any change; the two new packages add their own.

**Deviations and corrections.** The protocol's first timestamp was wrong (corrected before use); the
adaptation signature treated a missing batch as `None` (fixed after the freeze, cannot affect forecasts, recorded
in `freeze_postrun_edits.json`); the protocol text counts six inspected tasks where its list has five; a figure
redraw was silently skipped once because of a hidden syntax error and was caught by timestamp. The state table
first counted planned conditions for cell lines outside the prepared release as missing; it is now scoped to the
release.

**Claim boundary.** Development evidence only: every task was analysed before and GSE70138 was opened. The task
is a transcriptomic mechanism-class proxy, class labels are annotations, and the misled-neighbour stratum has
18 units. The evidence supports keeping failure and negative cases in any memory, choosing by
hypothesis-conditional and never scalar forecasts, and treating forecast risk as a floor; it does not support
a benefit of the memory for terminal decisions.

## 14. Core, tool and dataset consolidation

This later session implements the owner's requested module boundaries and repository upload.
The detailed consolidation report belongs in this day record. The root README is now a short
navigation and execution guide.

### Module boundaries

| Location | Current responsibility |
|---|---|
| `src/maestro/` | Evidence, biological decision and repair contracts |
| `src/agent/` | Agent execution, provider transport, context and persistence |
| `src/virtual_cell/` | Prediction contracts, adapters, applicability and refusal |
| `tools/evaluation/` | Case construction, policies, costs, replay and scoring |
| `tools/datasets/` | Candidate search, provenance, acquisition, response construction and QA |
| `tools/{data,evidence,prediction,case_memory}/` | Nine registered capabilities and case workflows |

Evaluation's 12 Python files moved out of `src`; the small model-benchmark scorer was merged
into `tools.evaluation.scoring`. The core now contains 43 Python files in three packages;
tools contains 30 Python files in six functional directories. The previous 146-file baseline
is now 73 files. The extra dataset and evaluation directories are deliberate ownership groups.

Public package-root APIs now have 11 names: four core records/controller names, two agent
controllers, three prediction-contract names and two evaluation types. Callers import other
symbols from their owning modules. There are no compatibility shims or dynamic export hooks.
Only `maestro` remains an installed console command; evaluation and dataset commands run as
explicit tool modules. Schemas, capability IDs and byte-bound manifest checks remain intact.

### Research synchronization

The operational LINCS pack constructor was copied from the frozen research implementation
into `tools.datasets.lincs_pack`, and active case tools now import it there. The source registry
and candidate metadata have operational snapshots under `tools/datasets`. Frozen research
originals and historical protocol hashes remain available. Changes to import paths do not
retroactively renew a research freeze.

No newly examined research predictor or planner meets the recorded promotion rule. The
dual-core, in-context, population and case-memory development results do not establish a
terminal-decision or deployment-calibration benefit. Those algorithms remain research-only.
This synchronization promotes reusable data-processing code, not an unsupported scientific claim.

### Dataset workflow

`tools.datasets.catalog` lists reviewed candidates by task role, audits local source hashes,
and searches Figshare or Zenodo metadata. Searches record query, URL, retrieval time and
response hash. A live Figshare search for `sciPlex` succeeded with two metadata records; its
snapshot is local `data/manifests/dataset_search_20260929.json`. Discovery alone does not qualify
either result for the model. No new expression matrix was downloaded.

The acquisition command streams one explicitly selected HTTPS asset, enforces a declared
byte budget, verifies SHA-256, writes provenance and refuses to replace an unverified existing
file. Default budget: 32 MiB. Hash mismatch, excess size, outside-data destinations and an
existing partial download have regression coverage.

The sciPlex-v2 constructor, shared mapping logic, QA and public/hidden model benchmark builder
moved into the dataset group. The existing package was rebuilt after the move to refresh its
implementation hashes. The 569 quarantined cells, 32/32 and 206/206 sample-sheet matches,
60 usable sciPlex4 treatment contrasts and unavailable rescue result remain unchanged. The
benchmark still covers 6,601 episodes and 49,304 measured action records. These exposed records
support implementation checks and development comparisons, not independent external validation.

### Other directories and upload

`data` (~104 GiB), `outputs` (~2 GiB), `tmp`, `.workbuddy` and reference inputs remain local.
Already tracked small provenance/pack records and historical experiment results are retained.
The single `inspect/source.pptx` input moved to `reference/inputs/source.pptx`, preserving the
user's asset; the empty `inspect` directory and pytest cache were removed. Uncited presentation
drafts in `tmp` are preserved as user work product. Ignore rules exclude local session memory,
reference inputs, secrets, build products and bulk datasets.

### Verification

Commands: `python -B -m pytest tests -q -p no:cacheprovider -o addopts=''`, dataset QA, package
build and the opt-in research tests. The final results are recorded below before upload.
SciPlex-v2 QA passes 15/15; the source/data migration has 44 focused contract tests passing.
The dataset commands are documented in `tools/datasets/README.md`.

Final verification for this consolidation:

- Core and tool suite: 1,452 passed in 69.54 seconds.
- Focused migration, source, benchmark and sciPlex contracts: 44 passed.
- Rebuilt sciPlex-v2 package: QA 15/15, with refreshed implementation hashes.
- Wheel build and editable installation succeeded; the installed command surface is `maestro` only.
- Research suite initially returned 271 passed and one historical replay comparison failure.
  A complete field comparison found 182 differences, exclusively ridge `score_gap`
  diagnostics, with maximum absolute difference `2.9976021664879227e-15`.
  The replay test now allows `1e-14` absolute tolerance only for that diagnostic;
  actions, outcomes and every other field remain exact. All three focused replay tests
  passed, including rejection of meaningful score and outcome changes. The entire
  research suite was not rerun after this test-only correction. Frozen records and
  model policies were not changed.
- Repository whitespace checks passed. Bulk data, local references and session artifacts
  are excluded from the upload; source, tools, tests and research/log records are included.

The upload target is the owner's `1-Vast/LLM` repository, `main`, using a normal
fast-forward push. This record describes module organization and verified behavior;
it does not establish independent model performance on new experiments.
