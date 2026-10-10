# Release Check

This document and `RELEASE_STATS.json` describe the historical compression
release. They are not measurements of the present dirty worktree. Current
local consolidation measurements are in `CURRENT_REPOSITORY_STATS.json` and
[research/REFACTOR_REPORT.md](research/REFACTOR_REPORT.md); no new release,
commit or push is implied.

## Revision and Size

- Baseline: `540bc85801fa78a3a58780b37b81b4197449d107`.
- Compressed checkpoint: `e450d2787ebfa82491db42c646e887f91d0a8f61`.
- Repair implementation commit: `b3e060db83c405291e231988fb0de585e1f46586` on `repair/release-compress-20261009`.
- Final release commit: the repository `HEAD` containing this release check and `RELEASE_STATS.json`.
- GitHub `main` was not changed. No push or history rewrite was performed.
- Baseline tree: 5,493 tracked files, 1,100,955,280 blob bytes. Compressed checkpoint: 261 files, 23,384,797 blob bytes. Repair implementation: 271 files, 5,375,126 blob bytes. `RELEASE_STATS.json` records these measurements.

## Removed and Restored

- Removed historical research copies and result trees, old dated logs, duplicate reports, generated output copies, obsolete dataset audit programs/data, and stale test registrations. Detailed per-path hashes, reasons, states and recovery locations are in `../LLM-precompress-manifest.json.gz`.
- Restored `tools/datasets/catalog.py`, `lincs_pack.py`, `combination_screens.py`, `sources.json` and `candidates.json` from baseline history. `__init__.py` and `condition_sources.py` remain present. `discovery_replay` remains available.
- Restored default tests for case memory, structured tools, state adapters, tool receipts, evaluation integrity and typed decision contracts. Historical evaluation isolation/protocol tests need ignored case/cost assets; combination-screen parity requires the excluded `research/certified_discovery` source. These are registered in `archive`, not default tests.
- Production `src/` code was not modified. Dataset and replay utilities were restored from baseline; no model or algorithm was expanded.

## Verification

- `python -m pip install -e ".[test]"`: PASS.
- `python -m pytest`: PASS, 653 passed.
- `python -m tools.research_validation`: PASS, 21 current research contract tests passed. These are tests, not a rerun of the scientific studies.
- `python -m tools.log_manifest --check`: PASS; paths, sizes and SHA-256 values match retained log files.
- `python -m compileall -q src tools research/astra research/decision_value`: PASS.
- `PYTHONPATH=src python -m tools.datasets.catalog --help`: PASS.
- `PYTHONPATH=src python -m tools.evaluation.cli --help`: PASS.
- Imports for `tools.case_memory.build_cases`, `audit`, `validate`, `tools.analysis.tool` and `tools.evaluation.discovery_replay`: PASS.
- `git diff --check`: PASS.
- `python -m tools.research_validation --verify`: BLOCKED/ASSET_MISSING for `data/virtual_cell/tahoe_c39_x_hvg_feature_names.json`. The preflight did not invoke full study verifiers.

The active freeze and verifier hashes were checked over raw bytes. Feedback `FREEZE.json` is preserved as CRLF with SHA-256 `2d7cfb509b2b9eed8386fffa4dd3df48ccef042907f8ebe8d636711bd83dfcab`; decision-value `FREEZE.json` is CRLF with SHA-256 `543c5aaf95dd5df08dff9ca06a73ec4ec453b240c5ac548db4c05ac407c3edb8`. Accessible nested hashes match. No `FREEZE.json` or `PROTOCOL.json` scientific values were changed.

## Remaining Blocks

- The Tahoe feature-name JSON is absent from baseline Git history and cannot be restored from the repository.
- Generated readout, feedback and decision-value `RESULTS.json` files are ignored outputs and are not shipped. Local copies are not evidence that a clean checkout can replay them.
- MAP released checkpoints, compatible source/dependencies and the viability risk-calibration prepared pack are external/local assets; see `BLOCKED_ASSETS.md`.
- Full numerical study verifiers were not run. Recorded development outcomes remain bounded by the limitations in `research/REPORT.md` and `research/EVIDENCE.md`.

## Recovery

- Tag `archive/pre-compress-540bc85` points to the pre-compression baseline.
- `../LLM-precompress.bundle` contains complete Git history and passed `git bundle verify`.
- Detailed cleanup manifest: `../LLM-precompress-manifest.json.gz`.
