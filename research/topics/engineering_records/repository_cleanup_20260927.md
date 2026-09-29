# Repository Cleanup Disposition (2026-09-27)

This is the disposition record for the repository consolidation. The root README is the current
capability summary; this file records the code decisions and their caller evidence.

## Baseline

- Git was at `c3d2345` (`main`, tracking `origin/main`). The tracked tree was clean. Existing
  untracked `inspect/`, `reference_0927/`, and `research/prompt_review_20260927/` were preserved.
- `pyproject.toml` exposed `maestro`, `maestro-evaluate`, `maestro-screen-cases`,
  `maestro-build-cases`, `maestro-e0-dir`, and `maestro-test-research`.
- `tools/registry.yaml` and the eight `tools/*/manifest.json` files named the eight discoverable
  data tools; discovery uses the manifest glob, not Python imports.
- The static source graph was `maestro` → `virtual_cell` → `agent` → `evaluation`, with deferred
  `maestro` references to virtual-cell types. Searches for `importlib`, `__import__`, `runpy`, and
  `sys.path` found dynamic loading in virtual-cell runner code and research harnesses, but no
  dynamic caller of the removed evaluation API router or repair certificate.
- Supported commands and reproduction paths checked included the `pyproject.toml` scripts,
  `maestro-evaluate --policy repair` in `research/gated_plan/VALIDATION.md`, the case builder and
  replay commands in the root README, manifest discovery in `agent/tool_runtime.py`, and the
  registered research commands in `research/belief_planning/README.md` and
  `research/experiments/README.md`.
- Before changes, `python -m pytest -q` collected the project tests and failed five runner tests
  because the preserved root `inspect/` directory was resolved as a relative executable path.
  The standalone `pytest` command used an incompatible interpreter; `python -m pytest` is the
  valid invocation here.

## Disposition Table

Engineering evidence below is test or CLI contract coverage. None of the evaluation modules is
evidence of biological benefit. Research rows retain proxy-task and engagement replay code only
where the named replay or test depends on it.

In the `Current path` column, a bare filename means `src/evaluation/<filename>`.

| Current path | Callers or entry point | Purpose | Engineering evidence | Scientific evidence | Reproduction dependency | Decision and destination/reason |
|---|---|---|---|---|---|---|
| `src/evaluation/__init__.py` | `maestro-evaluate`; API imports in tests | Public replay API | evaluation protocol, isolation, and real replay tests | no biological claim | CLI and test API | keep; mixed replay package boundary |
| `adaptive_reference.py` | admissible/contingent/exclusion analyses; tests | Exact finite decision reference | adaptive-reference and policy tests | synthetic declared outcomes only | comparator and exact optimum tests | keep; tests and analyzers import it |
| `adjudication.py` | `python -m evaluation.adjudication` API; tests | Blind packet and mechanical verdict | replay protocol tests | six-case adjudication is task-local | adjudication records and CLI | keep; replay support |
| `admissible.py` | contingent/licensing analyzers; tests | Admissible-policy solver and certificate | admissible and licensing tests | declared replay models, not biology | six-case analysis | keep; intertwined with replay comparators |
| `asrg.py` | `test_asrg.py` | Exploratory action-supported geometry pilot | algebra and input validation tests | exploratory old SciPlex holdout; no confirmation | pilot code follows historical model-validation outputs | move to `research/asrg/pilot.py` |
| `baselines.py` | evaluation CLI and runner | Replay policies and submission parsing | replay, isolation, and protocol tests | policy arms are comparisons, not validated methods | installed replay and dated comparisons | keep; required by installed evaluation CLI |
| `build_cli.py` | `maestro-build-cases` | Build public/private case package | case-builder and integrity tests | no claim | documented case generation path | keep; installed operational CLI |
| `capabilities.py` | evaluation CLI, proposal arms, package tests | Capability registry and repair compilation | engagement package and replay tests | six-case package only | `--capabilities` replay path | keep; installed replay dependency |
| `case_builder.py` | build CLI, engagement package, tests | Construct leakage-bounded cases | case-builder/integrity tests | proxy or replay cases, not biology | documented real-case builder | keep; operational case adapter |
| `cases.py` | runner, CLI, scoring, tests | Public/private replay contract | evaluation integrity/isolation tests | no standalone claim | all evaluation replay | keep; stable evaluation contract |
| `cli.py` | `maestro-evaluate` | Run replay policies and write reports | evaluation protocol and CLI tests | arm results remain task-bound | historical engagement and policy replays | keep; installed CLI and documented invocation |
| `composition.py` | real composition analyzer; tests | Compose declared gate/readout options | gated composition tests | synthetic and declared case models | composition analysis tests | keep; shared comparator helper |
| `contingent_suite.py` | licensing analyses and tests; module CLI | Constructed families and policy comparisons | contingent/admissible tests | synthetic only | retained synthetic analysis | keep; explicit test/research caller |
| `contingent.py` | contingent suite, real replay analyzers, tests | Contingent repair and attribution rules | contingent repair tests | declared outcomes only | replay comparison dependencies | keep; comparator implementation |
| `dual_residual_api_router.py` | none found | One-call model router smoke | no tests or manifest | no recorded result | no registered or documented run | delete; no supported caller or reproduction record |
| `dual_residual_experiment.py` | historical E0-DIR analysis reference | Offline residual experiment | retained code, no production test | exploratory, not independent evidence | reads dated model-validation outputs | move to `research/asrg/dual_residual_experiment.py` |
| `e0_dir_controller.py` | `test_e0_dir.py` | Experimental branch router | unit contract tests | no qualified task | prototype tests only | move to `research/asrg/e0_dir_controller.py` |
| `e0_dir_core.py` | controller and `test_e0_dir.py` | Experimental typed records and residual checks | unit contract tests | no validated intervention or task | prototype tests only | move to `research/asrg/e0_dir_core.py` |
| `e0_dir.py` | `maestro-e0-dir` only | Writes a fixed `not_run` status payload | no substantive operation | no experiment run; prerequisites absent | no result or registration | delete; remove placeholder installed command |
| `engagement_cases.py` | engagement package and tests | Screen engagement-repair candidates | engagement package tests | six-case, condition-mismatch limitations recorded | engagement package build | keep; package dependency |
| `engagement_package.py` | `python -m evaluation.engagement_cases`; tests | Build six-case engagement replay assets | engagement package and integrity tests | six-case replay only; no biological superiority | package and manifest construction | keep; named replay entry point |
| `engagement_sources.py` | package/case code and tests | Load and qualify source records | engagement source tests | source-specific limitations remain | six-case package | keep; source adapter |
| `evidence_base.py` | case builder and tests | Verify and load source releases | evidence-base/integrity tests | no claim | case-builder inputs | keep; operational data adapter |
| `exclusion_discontinuity.py` | exclusion analysis and tests | Analyze admissibility discontinuity | exclusion tests | synthetic/declared policy analysis | repair comparison | keep; explicit analyzer caller |
| `exclusion_licensing.py` | tests and licensing analysis | Analyze licensed decisions under exclusion | exclusion/licensing tests | six-case declared replay only | replay comparator tests | keep; analyzed behavior is not production |
| `feasibility.py` | planning and scoring; tests | Enumerate legal public actions and costs | evidence-planning/integrity tests | no claim | case replay semantics | keep; evaluation contract |
| `lab_cost.py` | CLI, score table, runner; tests | Price wells and turnaround | lab-cost/evaluation tests | no claim | replay cost records | keep; CLI operational contract |
| `licensing_gap.py` | exclusion and repair tests; module CLI | Compare menu and repair licensing | tests and explicit script interface | six-case package analysis | replay analysis | keep; tests and analyzer depend on it |
| `llm_proposal_arm.py` | `test_llm_proposal_arm.py`; module CLI | Provider-backed proposal comparator | proposal arm tests | no scientific superiority claim | explicit optional paid comparator | keep; named opt-in comparator |
| `llm_rows.py` | evaluation CLI and tests | Explicit-hypothesis provider arm | evaluation protocol tests | comparator only | optional provider row | keep; CLI supports named arm |
| `model_validation.py` | virtual-cell research code and tests; module CLI | Prepare and validate response models | learned-response and identity tests | transcriptomic prediction task; no decision benefit implied | dated model-validation artifacts and research prep | keep; actively referenced preparation path |
| `planning.py` | evaluation tests and case feasibility | Enumerate public evidence bundles | evidence-planning and contract tests | declared utility, no biology | replay feasibility contract | keep; distinct from moved belief planner |
| `prediction_controls.py` | evaluation CLI and protocol tests | Shuffle/remove prediction controls | protocol tests | attribution control only | section-37 and protocol arms | keep; CLI dependency |
| `prediction_value.py` | evaluation CLI and tests | Retrospective prediction-value arm | prediction-value tests | proxy-task comparator only | score-table rows | keep; installed CLI dependency |
| `proposal_arms.py` | evaluation CLI and engagement tests | Registry repair and same-information controls | engagement and evaluation tests | six-case replay shows no extra repair value | `maestro-evaluate --policy repair` | keep; required documented replay path |
| `provider_spend.py` | evaluation CLI/arms; tests | Track API spend | provider spend and CLI tests | no claim | paid replay accounting | keep; installed CLI contract |
| `public_loop.py` | integrated contract test; module runner | End-to-end public-data workflow | integrated research contract test | no mechanism update without measured evidence | registered two-stop smoke | keep; integration reproduction path |
| `real_admissible.py` | admissible tests; module CLI | Analyze the frozen real package | admissible tests | declared case outcomes only | 58-case analysis | keep; retained negative analysis |
| `real_composition.py` | composition tests; module CLI | Analyze the frozen real package under composed plans | real composition tests | declared package result, not biological validation | frozen package comparison | keep; negative/limited replay evidence |
| `real_contingent.py` | real admissible/contingent analyses; module CLI | Build real-package decision problem | tests and analyzers | declared outcomes only | replay comparison | keep; shared analysis dependency |
| `repair_certificate.py` | none found outside itself | Price registry repair against exact menu optimum | no importing tests | no registered or cited result | no documented invocation | delete; orphaned analysis with no supported reproduction path |
| `repair_replay.py` | runner, proposal arms, tests | Execute registry proposal round | replay and engagement tests | six-case replay only | installed repair policy replay | keep; CLI dependency |
| `runner.py` | evaluation CLI and tests | Isolated per-case policy runner | evaluation isolation/protocol tests | no claim | every replay command | keep; stable replay contract |
| `score_table.py` | evaluation CLI; module CLI; tests | Produce section-37 rows and exit verdict | evaluation protocol tests | reports comparator outcomes, not validation | installed replay output | keep; CLI dependency |
| `scoring.py` | runner, tests | Score decisions against declared outcomes | integrity and replay tests | no biological claim | replay output contract | keep; stable score contract |
| `screening.py` | screening CLI and tests | Validate candidate eligibility | candidate screening tests | eligibility only | candidate registry | keep; installed CLI dependency |
| `screening_cli.py` | `maestro-screen-cases` | Print candidate screening records | candidate screening tests | no claim | candidate registry checks | keep; installed operational CLI |
| `tracking.py` | evaluation CLI | Track provider calls | CLI/provider tests | no claim | paid arm replay | keep; installed CLI dependency |
| `voi_arm.py` | evaluation CLI and tests | Simple model VOI comparator | section-37 tests | proxy task comparator only | optional section-37 rows | keep; installed CLI dependency |
| `xlsx.py` | package/source adapters and tests | Read/write source workbooks | engagement package tests | no claim | package input materialization | keep; operational data adapter |

## Moves and Deletions

| From | To or deletion | Evidence |
|---|---|---|
| `src/maestro/planning.py` | `research/belief_planning/planner.py` | It had callers only in research arms and tests; no production runtime import. Its registered historical replay is reproducible from immutable archive commit `83b9aa9`; the moved code remains the opt-in research planner. Frozen `freeze.json` and evidence records were left untouched. |
| `src/evaluation/asrg.py` | `research/asrg/pilot.py` | Pilot reads a historical SciPlex holdout and tests exploratory action geometry; its protocol is proposed and not registered. Test now imports the research path. |
| `src/evaluation/e0_dir_core.py`, `e0_dir_controller.py` | `research/asrg/` | Prototype contracts had only test callers and a proposed research plan; tests remain under `tests/`. |
| `src/evaluation/dual_residual_experiment.py` | `research/asrg/dual_residual_experiment.py` | Historical experimental runner retained outside supported runtime. |
| `src/evaluation/e0_dir.py`, `dual_residual_api_router.py` | deleted; `maestro-e0-dir` entry point removed | The installed E0 command only emitted `not_run`; API router had no caller, manifest, documentation command, result, or registered experiment. |
| `src/evaluation/repair_certificate.py` | deleted | No static or dynamic caller, no test, no manifest, no documented run, and no registered result dependency. The surrounding real replay and negative result modules remain. |
| `src/maestro/research_tests.py` | `tools/research_validation.py` | Its only caller was the installed opt-in `maestro-test-research` script; it is a pytest launcher, not runtime domain logic. |
| `tools/shared/state_fixture.py`, `biological_fixture.py` | `tests/fixtures/state.py`, `biological.py` | Imports were test-only; moved to the test fixture boundary and import sites updated. |

## Remaining Mixed Responsibility

`src/evaluation/` still combines installed case building, replay, scoring, operational adapters, and
experimental policy arms. The policy arms are directly selected by the installed `maestro-evaluate`
CLI (including the documented six-case `--policy repair` replay), and their public/private case and
scoring contracts are interdependent and covered by the evaluation tests. Moving those arms alone
would make the installed CLI depend on research code; moving the package would violate the
module-by-module boundary and change the supported CLI's import surface. This cleanup therefore
keeps those coupled evaluation responsibilities together and moves the independent ASRG/E0-DIR
experiments and belief planner to `research/`.

## Initial Cleanup Verification Record

- Baseline before reorganization: `python -m pytest -q` failed five runner tests because the
  pre-existing, untracked root `inspect/` directory was resolved as an inspection executable.
- After reorganization: `python -m pip install -e ".[test]"` succeeded. All five installed
  commands (`maestro`, `maestro-evaluate`, `maestro-screen-cases`, `maestro-build-cases`, and
  `maestro-test-research`) returned successfully with `--help` when invoked from Python's
  Scripts directory. That directory is not on this shell's `PATH`.
- `python -m pytest -q tests`: five failures, the same root `inspect/` collision as baseline;
  the failures were in `test_input_basis_identity.py`, `test_production_contract_gaps.py` (three
  cases), and `test_state_runner_paths.py`. The migrated code and the changed repository-shape,
  research-import-boundary, fixture, research-test-launcher, and experimental-code tests passed.
- `python -m pytest -q tests -k "not test_an_asset_in_the_checkpoints_own_basis_stays_executable and not test_entry_point_binds_the_declared_context_to_the_selected_rows and not test_a_compatible_query_stays_executable_and_its_validation_stays_unknown and not test_a_registered_receipt_without_a_verified_holdout_is_not_reported_as_validated and not test_the_in_process_runner_reaches_the_subprocess_verdict"`: passed; the rest of the configured project tests completed successfully.
- `python -m pytest -q research/protocol_v2`: passed.
- Parsed all eight `tools/*/manifest.json` files successfully. The source import-boundary assertion
  in `tests/test_repository_shape.py` passed as part of the project test run.
- `python -m pytest -q tests/test_repository_shape.py`: passed (10 tests).
  `python -m tools.research_validation --help` reached the opt-in pytest launcher successfully.
- `git diff --check`: passed after the changes.

## Follow-Up Disposition (2026-09-27)

The follow-up fixes the inspection cache's command/path ambiguity in `src/virtual_cell/state_adapter.py`
and adds a regression test with an unrelated `inspect/` directory in the current working directory.
The research test runner is checkout-local, validates that it is launched from this checkout, and
is no longer an installed project script. `tools/shared/StubClient` had test-only callers, so it
moved to `tests/fixtures/stub_client.py`; `tools/shared/` no longer has tracked package files.
The installed case-building, screening, and replay command implementations remain in
`src/evaluation/` and are documented there.

## Evaluation Boundary Decision

`cases.py` owns the public case, revealed-evidence, and private evaluator-data contracts.
`runner.py` gives each arm the same `ReplayView`, controls reveal through the shared environment,
and sends every terminal submission through `scoring.py`. Those are the stable replay contracts;
the evaluator-only private rules stay behind the same scoring boundary for every arm.

The arm implementations are experimental comparators: `proposal_arms.py`, the policy classes in
`baselines.py`, `prediction_controls.py`, `prediction_value.py`, `voi_arm.py`, `llm_rows.py`, and
`llm_proposal_arm.py`. The installed `cli.py` currently imports and constructs these classes
directly, and its `--policy` choices, dispatch, output rows, and reproduction commands name them.
`baselines.py` also defines the `ReplayPolicy` and `DecisionSubmission` interfaces consumed by the
stable runner. Moving only the arm modules would break the installed dispatcher; moving the CLI
arms into `research/` would make the command depend on research code and would change registered
reproduction paths. They therefore remain in `src/evaluation/` for this round, without any claim
of scientific validation.

Bounded migration plan before a future split:

1. Extract the `ReplayPolicy`/submission interface, case reveal API, and common scorer behind a
   stable replay contract; test that all arms receive identical public views and scoring inputs.
2. Add a research-owned replay dispatcher for experimental arms, preserving the exact frozen
   command and output schema at the historical archive commit.
3. Reduce the installed CLI to supported operational commands and stable baseline paths only;
   verify public/private isolation, equal scoring, package installation, and archive reproduction
   before moving any arm implementation.

## Follow-Up Verification Record

- The six focused inspection cases (five prior failures plus the new `inspect/` regression) passed.
- `python -m pytest -q tests`: passed with no exclusions. This includes the repository-shape,
  launcher-scope, fixture-location, and import-boundary checks.
- `python -m pytest -q research/protocol_v2`: passed.
- `python -m tools.research_validation` from the checkout root ran the full research test scope:
  142 passed and one archived L1000 saved-fold reproduction failed at
  `research/external_validation/test_external_validation.py:481` because regenerated records
  differ from the saved fold. No frozen record was changed. From `C:\Windows\Temp`, invoking
  `python D:\MAESTRO\tools\research_validation.py` returned the documented checkout-local error.
- `python -m pip install -e ".[test]"` succeeded. The four remaining installed commands returned
  successfully with `--help`; `maestro-test-research` is no longer installed. All eight tool
  manifests parsed successfully.
- The saved experiment records were unchanged (`git diff HEAD -- log research/experiments` was
  empty). `git diff HEAD --check` passed.
