# MAESTRO

MAESTRO is a dual-core scientific system: an Agent manages questions, evidence, decisions, budgets and execution; a virtual-cell world model predicts responses within a declared model, source, condition and feature-axis scope. Typed contracts connect the cores. Unsupported predictions must be refused, and predictions remain distinct from observations.

## Install and run

```bash
python -m pip install -e ".[test]"
maestro --help
python -m pytest -q
python -m tools.research_validation --verify
```

The research verifier checks frozen inputs and outputs. Missing or mismatched assets are reported as `BLOCKED/ASSET_MISSING`; passing software tests is not a scientific result.

## Structure

| Path | Responsibility |
|---|---|
| `src/agent/` | Planning, tool execution, scoped memory, restart and audit |
| `src/maestro/` | Evidence, decisions, authorization, risk and repair contracts |
| `src/virtual_cell/` | Model identity, applicability, prediction, uncertainty and refusal |
| `tools/` | Reusable offline tools with stable inputs and outputs |
| `research/` | Experimental code, protocols, frozen inputs, results and limits |
| `tests/` | Core contracts and regression checks; research tests run explicitly |

Minimal command examples:

```bash
python -m tools.datasets.catalog --help
python -m tools.evaluation.cli --help
python -m tools.research_validation --collect-only
```

## Scientific boundary

The model predicts within qualified scope; it does not establish functional endpoints, mechanism, causality or experiment value by itself. The Agent selects and audits evidence and actions; it does not turn language-model output into scientific fact. Current conclusions and the next verification gate are in [research/REPORT.md](research/REPORT.md), with numerical results in [research/EVIDENCE.md](research/EVIDENCE.md) and study navigation in [research/INDEX.md](research/INDEX.md). Missing assets are listed in [BLOCKED_ASSETS.md](BLOCKED_ASSETS.md).
