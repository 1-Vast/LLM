# Protocol external-validation-2: run notes (block 3, 2026-09-27)

Chronology (+0800). Times are file modification times, or approximate tool-output times.

| Time | Event |
|---|---|
| 11:33 | Tree as found: `83b9aa9` on `main`, clean. Freeze check: belief-planning-1 54/54 digests match the disk; regenerated external-validation-1 78/79 (`src/maestro/acquisition.py` differs); original external-validation-1 fails on 9 files. |
| 11:35 | Baseline tests at HEAD: production passes; research has 2 failures (`test_freeze_verifies_and_detects_a_change`, `test_replay_reproduces_a_saved_fold`), both on rewritten protocol-v1 artefacts. |
| 11:40 | At HEAD the external-validation SciPlex3 replay (`locked_replay.run_task`, A fold 1) crashes with `TypeError` on truth-less episodes. A rerun of the original L1000 T fold 0 reproduces every original arm's records. |
| 11:55 | `headroom.py` on the registered records (`protocol_v2_headroom_registered.json`). |
| 11:56 | `calibration.py`, leave-one-study-out (`protocol_v2_calibration_registered.json`). Stop gate: allow, on the planner's own bound only. Contamination eps chosen on pooled development data: 0.3. |
| 11:59 | `attribution.py` (`protocol_v2_attribution_registered.json`): virtual cell and feedback REJECT_AS_DEFAULT everywhere. |
| 12:04 | `archive.py --write`: `research/experiments/*/EVIDENCE.json`; 49 untracked originals set read-only. |
| 12:05:59 | `research/protocol_v2/protocol.json` written; it registers the development screen. Its `written_at` field says 12:10 (an estimate, left unchanged to keep the recorded digest). |
| 12:07:35 | Development screen started; run record `development_unregistered` (dirty tree). |
| 12:11 | Screen finished: 20 tasks, 111,852 records, 0 integrity problems, 12 replay mismatches (all on SciPlex3 A compounds with an unplanned condition). |
| 12:15 | `screen.py` (`protocol_v2_dev_screen_analysis.json`). |
| 12:01-12:20 | A concurrent Codex session (slides for the owner's group meeting) created `inspect/` in the repository root and wrote under `outputs/`. Not touched. |
| 12:16-12:18 | After the screen: `contracts.truth_free_episodes` added; unreferenced aliases and `truth_free_episode_list` removed. |
| 12:27 | Rerun of seven screen tasks with the final code: 0 decision mismatches against the screen. |

## Tests

| Suite | Command | Result |
|---|---|---|
| Protocol v2 | `python -m pytest research/protocol_v2 -q -p no:cacheprovider` | 24 passed |
| Research (all, includes protocol v2) | `python -m pytest research -p no:cacheprovider -o addopts="" -q` | 143 passed (228 s) |
| Production, from the repository root | `python -m pytest tests -p no:cacheprovider -o addopts="" -q` | 1,336 passed, 5 failed |
| The 5 failing files' tests, from a working directory without `inspect/` | same test files, `--rootdir D:/MAESTRO` | 48 passed |
| Production, full suite from that working directory | `python -m pytest D:/MAESTRO/tests --rootdir D:/MAESTRO -c D:/MAESTRO/pyproject.toml` | 1,336 passed, 5 failed: `test_directed_repair_and_licensing`, which reads `data/evaluation/cases` relative to the working directory |

The five failures:
- `test_input_basis_identity::test_an_asset_in_the_checkpoints_own_basis_stays_executable`;
- three in `test_production_contract_gaps`;
- `test_state_runner_paths::test_the_in_process_runner_reaches_the_subprocess_verdict`.

All five come from `src/virtual_cell/state_adapter.py::_argument_identity`. It hashes any runner
argument that exists as a path relative to the working directory, and the other session's
`inspect/` directory shadows the runner verb `inspect`. They are not caused by this block's
changes, which touch no file under `src/` or `tests/`. Every production test passes in one of
the two working directories.

## Costs

- Provider calls: none ($0).
- Laboratory: 0 wells, 0 days.
- Compute: about 4 minutes for the screen on 16 workers; about 6 minutes for the analyses.
