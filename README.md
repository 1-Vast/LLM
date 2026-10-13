# MAESTRO

MAESTRO is a dual-core scientific system: an Agent manages questions, evidence, decisions, budgets and execution; a virtual-cell world model predicts responses within a declared model, source, condition and feature-axis scope. Typed contracts connect the cores. Unsupported predictions must be refused, and predictions remain distinct from observations.

## Install and run

```bash
python -m pip install -e ".[test]"
maestro --help
python -m pytest -q
python -m tools.research_validation --verify
```

The research preflight checks explicitly supplied frozen inputs and outputs. No active study is currently released.

* It authenticates every file a study's `FREEZE.json` lists under its `inputs`, `sha256` or `files` mapping.
* Missing or mismatched assets are reported as `BLOCKED/ASSET_MISSING`.
* Any other freeze schema is refused as `BLOCKED/FREEZE_SCHEMA_UNSUPPORTED`; it is never skipped.

Three levels stay separate:

1. **Software tests** (`pytest`, the CI workflow) show that code and contracts run.
2. **Research verification** is each study's own verifier: replays, provenance and claim audit. The preflight is an engineering check below this level.
3. **The scientific verdict** is the study's predeclared hypothesis outcome.

Passing software tests is not a scientific result.

## Structure

| Path | Responsibility |
|---|---|
| `src/agent/` | Planning, tool execution, scoped memory, restart and audit |
| `src/maestro/` | Evidence, decisions, authorization, risk and repair contracts |
| `src/virtual_cell/` | Model identity, applicability, prediction, uncertainty and refusal |
| `tools/` | Reusable offline tools with stable inputs and outputs |
| `research/` | Central historical evidence, limits and future explicit protocols |
| `tests/` | Core contracts and regression checks; research tests run explicitly |

Minimal command examples:

```bash
python -m tools.datasets.catalog --help
python -m tools.evaluation.cli --help
python -m tools.research_validation --help
```

## Scientific boundary

The model predicts within qualified scope; it does not establish functional endpoints, mechanism, causality or experiment value by itself. The Agent selects and audits evidence and actions; it does not turn language-model output into scientific fact. Current conclusions and the next verification gate are in [research/REPORT.md](research/REPORT.md), with numerical results in [research/EVIDENCE.md](research/EVIDENCE.md). Full checkpoint/data axes, independent repeat qualification and the next P0.6 protocol remain blocked.

Completed and failed study implementations are retired; historical protocols and source identities are referenced in the evidence register. Research asset qualification remains explicit and separate from the default software tests.
