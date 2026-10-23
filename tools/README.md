# Tools

## Research promotion and storage

Keep maintained command-line and operational utilities here. Experimental implementations and research tests belong in [research](../research/README.md) until validation relevant to their intended use supports promotion. Record the evidence, limitations and promotion decision in [log](../log/README.md); structure or storage checks alone do not establish scientific validity.

Keep datasets, source bodies and model artifacts in [data](../data/README.md). Follow the [storage policy](../log/STORAGE_POLICY.md). The October 23 consolidation promoted no experimental implementation.

## Campaign resources and terminal utility

`python -m tools.evaluation.decision_report` reports paired terminal utility and
utility-unit measurement/turnaround prices. Supply `--resource-budget budget.json`
to also enforce the same hard total resource cap for both arms. For example:

```json
{"total": 18, "measurement_cost": 1, "turnaround_cost": 2, "unit": "read-equivalent scenario"}
```

This permits 16 measurements in one round or 14 in two rounds. The source contract
`maestro.campaign_budget.CampaignBudget.require_feasible` also checks cumulative
proposed expenditure before execution. Campaign records accept `other_resource_cost`
and `other_utility_cost` for API, compute and overhead, declared separately in their
respective units; omitted values retain the legacy zero. Prices are declarations,
not authenticated invoices. Without a resource-budget argument, the legacy report
does not establish equivalence of total resource allowances. The tested prototype
and scientific limitations are in
[the historical evidence register](../research/EVIDENCE.md).

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
and remaining limits are in [research/EVIDENCE.md](../research/EVIDENCE.md).

`tools.analysis.platform_identity.identity_test(reference, query)` checks a cross-platform feature
axis before a world model is fed another platform's cells. Every shared line must be most
similar to itself, above a permuted-axis null; otherwise it refuses with `AXIS_IDENTITY_FAILED`
or `TOO_FEW_SHARED_LINES`.

`tools.evaluation.increment.paired_increment(prior, extra, outcome)` returns the paired gain
`r(prior + extra) - r(prior)` on common units with a unit bootstrap, ready for
`maestro.world_model_value.IncrementEstimate`.

Both come from `research/astra/kinetic_horizon_20261010`. There, identity passed 18 of 18 lines
while responses did not transport, so a passing identity check is not transport evidence.

`python -m tools.research_inventory --workspace . --out EXTERNAL_TEMP_PATH/inventory.json`
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
python -m tools.case_memory.audit quality --protocol-freeze PATH
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
The library builder and replay entry points are retained. Historical comparisons against the retired research implementation are removed.
The explicit synthetic ALMANAC vault test retains identity/sealing behavior;
asset-free combination-world contracts remain in the default suite.

Run evaluation through `python -m tools.evaluation.cli` and
`python -m tools.evaluation.construction build|screen`. Only `maestro` is an installed command.
The checkout-local research test
runner is `python -m tools.research_validation` from the repository root; it runs only the
explicitly selected registered research suites and does not imply that a research claim is validated.
Historical suites and their required data are not part of default collection.

Synthetic biological, virtual-cell, and provider-client fixtures are test-only and live in
`tests/fixtures/`.

## Bridged Context Transfer

```bash
python -m tools.datasets.design_census TABLE.tsv --preset beataml --feature-header EXPR.tsv --out census.json
python -m tools.evaluation.bridge_replay domain.npz --budget 16 --k-bridge 4 --out replay.json
```

`datasets.design_census` counts contexts, dependence groups, items and measured pairs of a
long-format screen. It reads only the declared design columns, so a census taken before a freeze
cannot see outcomes. `evaluation.bridge_replay` is an equal-query retrospective replay on any
context x item matrix (NPZ keys `Y`, `X`, `contexts`, `groups`, `items`). In every outer fold it
selects rank and procedure on source contexts only (`agent.procedure_selection`). It then grades
these arms on held-out contexts: no bridge, exploit-first bridge, lookahead bridge, the selected
procedure, and the item prior. It uses `virtual_cell.bridged_transfer` and `agent.bridge_design`.
Both tools come from `research/context_transfer_20261017`; a replay on exposed data is a planning
aid, not a confirmation. The lookahead arm uses the corrected rule; the study's confirmation used
`lookahead_v1`, whose baseline defect is described in `agent.bridge_design`.

## Research Validation

The maintained research test suites are explicitly opt-in:

```bash
python -m tools.research_validation --help
python -m tools.research_validation --verify --study STUDY_PATH --result RESULT_PATH
```

No active study is currently released. Select registered asset-dependent tests explicitly.
The verification command checks supplied frozen inputs and generated outputs without executing study code. Missing assets produce `BLOCKED/ASSET_MISSING`. Historical
dataset audit commands and older ASTRA drivers are recoverable from Git history, not current
release entry points. Case-memory builders and audits likewise require their declared local
assets and do not replace missing values with zeros.
