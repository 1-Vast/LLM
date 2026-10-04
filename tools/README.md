# Tools

Tools are grouped by responsibility. Each capability keeps its own ID, schema, applicability
boundary and source hashes. The router discovers `*/manifest.json` and `*/*.manifest.json`;
each manifest selects a public function in the group's `tool.py`. The exact manifest and source
bytes are verified again before invocation. Receipts retain their declared evidence type.

| Directory | Registered Capability IDs |
|---|---|
| `data/` | `data_profile`, `column_summary`, `table_filter` |
| `evidence/` | `evidence_bundle_optimize`, `multimodal_alignment`, `typed_decision_review` |
| `prediction/` | `signature_retrieval`, `virtual_cell_query` |
| `case_memory/` | `case_memory`; case construction, audit and replay commands |
| `datasets/` | Discovery, hash-pinned acquisition, data construction and QA (no runtime manifest) |
| `evaluation/` | Case replay, costs and scoring (no runtime manifest) |

The larger case-memory workflow is grouped under `case_memory/`: its builders and validation
commands share the reference-vector index and byte-hash helpers instead of rescanning the same
arrays or duplicating checksum loops.
The two validation modes use one entry point: `python -m tools.case_memory.validate forecasts` and
`python -m tools.case_memory.validate calibration`.
Source and pack preparation is installed tooling; the scientific replay is checkout-local:

```bash
python -m tools.case_memory.workflow sources
python -m tools.case_memory.workflow pack
python -m tools.case_memory.workflow graphs
python -m research.case_memory_integration.external_replay replay
python -m research.case_memory_integration.external_replay evaluate
python -m tools.case_memory.audit quality
python -m tools.case_memory.audit figures
```

These replace the former `download_sources`, `build_hypothesis_graph`, `preprocess`,
`replay` and `evaluate` modules. Run
`python -m tools.case_memory.workflow --help` for the available steps.
The pack step accepts `--workspace PATH`; `load_pack(workspace=PATH)` can also read
an explicit data workspace outside the checkout. Source verification and graph
construction retain their fixed checkout scope. Replay/evaluation no longer import
research from installed tooling.

## Model Benchmark

```bash
python -m tools.datasets.benchmark
```

This replaces `tools.model_experiment.build_benchmark`. It reads the existing protocol-v2.1
tables and writes `data/processed/model_experiment_v1/`: `public_episodes.jsonl.gz`,
`hidden_outcomes.jsonl.gz` and a hashed `manifest.json`. There are 6,601 episodes and 49,304
measured action records across SciPlex3 A/B and L1000 LT/T. Fold 0 is evaluation; folds 1-4
are development. The source-unit field is retained for clustered reporting.

Public episodes contain legal menus and budgets, with no truth, outcome, readout, lifecycle or
score fields. `tools.evaluation.scoring.score_sequence` validates the submitted sequence before
joining hidden outcomes by `episode_id`. These previously exposed records support replay and
leakage checks and development comparisons, not independent validation or deployment calibration.

The sciPlex-v2 builder and QA are in `datasets`; superseded v1 scripts and duplicate
archives are removed. Historical findings remain in the dataset-discovery reports.

## Certified Combination Discovery

```bash
python -m tools.datasets.combination_screens oneil --out data/processed/certified_discovery/oneil_tools_v1.npz
python -m tools.datasets.combination_screens almanac-design
python -m tools.evaluation.discovery_replay --library data/processed/certified_discovery/oneil_tools_v1.npz --out NEW_OUTPUT
```

`datasets.combination_screens` builds O'Neil 2016 and NCI-ALMANAC 2017 libraries. Each
candidate is an unordered drug pair x cell line. The label is the Bliss excess averaged over
the dose grid, and a hit is a label above 10. Context comes from single agents only.
ALMANAC outcomes are readable only through `open_vault` against an intact freeze record.
`evaluation.discovery_replay` runs every arm at equal budget, one campaign per target line,
and branches each campaign into exploit and certify variants. It uses
`virtual_cell.combination_world`, `maestro.certification` and the loop in `agent.discovery`.
Both modules were promoted from `research/certified_discovery`, which keeps the frozen
originals and the confirmatory evidence. `tests/test_combination_screens.py` (research
scope) checks parity against them.

Run evaluation through `python -m tools.evaluation.cli` and
`python -m tools.evaluation.construction build|screen`. Only `maestro` is an installed command.
The checkout-local research test
runner is `python -m tools.research_validation` from the repository root; it checks ASTRA
entries and does not imply that a research claim is validated. Other historical
suites use explicit pytest paths; `--include-archives` scans the historical tree.
Results, baseline/snapshot source copies, `research/experiments` and supplied
`research/data` copies are excluded by default. Use `--include-archives` only for an
explicit historical collection; an active regression may still load an archived
source deliberately to reproduce a known defect.

Synthetic biological, virtual-cell, and provider-client fixtures are test-only and live in
`tests/fixtures/`.

## STATE research commands

Specific diagnostic menus, feature kernels, held-out comparisons and historical
lineage replays are checkout-local research, not installed dataset capabilities:

```bash
python -m research.astra.state_sensitivity --help
python -m research.astra.state_knowledge_retrospective --help
python -m research.astra.state_knowledge_diagnose --help
python -m research.astra.state_identifiability --help
python -m research.astra.resistrace_retrospective --help
python -m research.astra.state_evidence_followup --help
python -m research.astra.state_prospective_certify --help
python -m research.astra.state_prospective_review --help
python -m research.astra.state_raw_reconstruction --help
```

`tools.datasets.state_identifiability` retains the pure source/sample/time/action
checks; `state_prospective_input`, raw-count conversion and metadata readers stay
in tools. Moving an experiment does not authenticate its dataset or improve its
scientific result. Earlier frozen commands use their pinned Git versions.
The case-memory audit and fixed source/graph commands still need their declared
checkout assets and protocols; installation does not bundle biological data.
