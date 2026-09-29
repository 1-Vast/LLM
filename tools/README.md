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
The external evaluation workflow also uses one entry point:

```bash
python -m tools.case_memory.workflow sources
python -m tools.case_memory.workflow pack
python -m tools.case_memory.workflow graphs
python -m tools.case_memory.workflow replay
python -m tools.case_memory.workflow evaluate
python -m tools.case_memory.audit quality
python -m tools.case_memory.audit figures
```

These replace the former `download_sources`, `build_hypothesis_graph`, `preprocess`,
`replay` and `evaluate` modules. Run
`python -m tools.case_memory.workflow --help` for the available steps.

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

Run evaluation through `python -m tools.evaluation.cli` and
`python -m tools.evaluation.construction build|screen`. Only `maestro` is an installed command.
The checkout-local research test
runner is `python -m tools.research_validation` from the repository root; it checks code under
`research/` and does not imply that a research claim is validated.

Synthetic biological, virtual-cell, and provider-client fixtures are test-only and live in
`tests/fixtures/`.
