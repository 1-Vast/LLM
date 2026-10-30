# Software tests

Run the default software suite from the repository root with `python -m pytest`.
The asset-dependent files registered in `pyproject.toml` remain explicit opt-in
suites; moving a test does not change its evidence scope.

| Directory | Responsibility |
|---|---|
| `acquisition/` | Evidence acquisition policies |
| `agent/` | Agent orchestration, runtime, case lifecycle and restart contracts |
| `case_memory/` | Case-memory integration, forecasts and scientific boundaries |
| `evaluation/` | Evaluation protocols, isolation, integrity and dataset contracts |
| `maestro/` | Evidence, decision, authorization, reliability and utility contracts |
| `repository/` | Repository layout, language, packaging and dependency boundaries |
| `research/` | Software contracts for retained research implementations and validation |
| `tools/` | Reusable tools, source lookup, inventory and retained-record access |
| `virtual_cell/` | Virtual-cell predictions, adapters, transfer and applicability |
| `fixtures/` | Shared helpers; preserved independently of test collection |

Software tests do not establish a scientific result. Study-specific experiments
and scientific records remain under `research/` and `log/` respectively.
