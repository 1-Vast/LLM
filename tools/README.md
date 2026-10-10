# Tools

## Offline observation and maintenance checks

`python -m tools.analysis.observation_audit axis input.npz` compares each target
coordinate with the complete declared candidate gene pool. The NPZ contains
`names`, already transformed and row-aligned `raw`, `targets`, and `symbols`;
optional `consistency_raw`/`consistency_targets` remain exposed consistency.
`python -m tools.analysis.observation_audit variance input.npz` consumes `values`
and explicit `weights`, retains gene covariance and uses actual cell count.
Neither command authenticates source identity, the STATE output axis or
independent biological replication. Their frozen sources are the P0.5R
extension matching and observation-reliability projection routines; validation
and remaining limits are in [research/INDEX.md](../research/INDEX.md).

`python -m tools.research_inventory --workspace . --out research/RESEARCH_INVENTORY.json`
rebuilds the static path/hash/import inventory. Identical bytes and ASTs are
cleanup candidates only; this command never deletes files or runs studies.

Tools are grouped by responsibility. Each capability keeps its own ID, schema, applicability
boundary and source hashes. The router discovers `*/manifest.json` and `*/*.manifest.json`;
each manifest selects a public function in its declared Python entrypoint. The exact manifest and source
bytes are verified again before invocation. Receipts retain their declared evidence type.

| Directory | Registered Capability IDs |
|---|---|
| `analysis/` | `data_profile`, `column_summary`, `table_filter`, `evidence_bundle_optimize`, `multimodal_alignment`, `typed_decision_review`, `condition_sources` |
| `prediction/` | `signature_retrieval`, `virtual_cell_query` |
| `case_memory/` | `case_memory`; case construction, audit and replay commands |
| `datasets/` | Discovery, hash-pinned acquisition, condition-source lookup implementation, data construction and QA |
| `evaluation/` | Case replay, costs and scoring (no runtime manifest) |

The larger case-memory workflow is grouped under `case_memory/`: its builders and validation
commands share the reference-vector index and byte-hash helpers instead of rescanning the same
arrays or duplicating checksum loops.
The two validation modes use one entry point: `python -m tools.case_memory.validate forecasts` and
`python -m tools.case_memory.validate calibration`.
Source and pack preparation is installed tooling. Pack construction and audits require their
registered LINCS inputs; a missing pack is an asset blocker, not an empty dataset.

```bash
python -m tools.case_memory.workflow sources
python -m tools.case_memory.workflow pack
python -m tools.case_memory.workflow graphs
python -m tools.case_memory.audit quality
python -m tools.case_memory.audit figures
```

These replace the former `download_sources`, `build_hypothesis_graph`, `preprocess`,
`replay` and `evaluate` modules. Run
`python -m tools.case_memory.workflow --help` for the available steps.
The pack step accepts `--workspace PATH`; `load_pack(workspace=PATH)` can also read
an explicit data workspace outside the checkout. Source verification and graph
construction retain their fixed checkout scope. The historical external replay package
is not part of this release.

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
The library builder and replay entry points are retained. Their historical parity suite is
archived because its `research/certified_discovery` source package is not in this release;
asset-free combination-world contracts remain in the default suite.

Run evaluation through `python -m tools.evaluation.cli` and
`python -m tools.evaluation.construction build|screen`. Only `maestro` is an installed command.
The checkout-local research test
runner is `python -m tools.research_validation` from the repository root; it runs only the
three current study contract suites and does not imply that a research claim is validated.
Historical suites and their required data are not part of default collection.

Synthetic biological, virtual-cell, and provider-client fixtures are test-only and live in
`tests/fixtures/`.

## Research Validation

The maintained research test suites are explicitly opt-in:

```bash
python -m tools.research_validation
python -m tools.research_validation --verify
```

The first command runs contract tests. The second checks frozen inputs and generated outputs
before invoking study verifiers. Missing assets produce `BLOCKED/ASSET_MISSING`. Historical
dataset audit commands and older ASTRA drivers are recoverable from Git history, not current
release entry points. Case-memory builders and audits likewise require their declared local
assets and do not replace missing values with zeros.
