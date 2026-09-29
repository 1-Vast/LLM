# MAESTRO

MAESTRO is an evidence-driven biological decision agent. Predictions support planning;
measured, qualified evidence controls scientific conclusions.

## Layout

| Path | Responsibility |
|---|---|
| `src/maestro/` | Core evidence, decision and repair contracts |
| `src/agent/` | Agent execution, providers, context and persistence |
| `src/virtual_cell/` | Prediction contracts, model adapters and refusal rules |
| `tools/evaluation/` | Case construction, replay, costing and scoring |
| `tools/datasets/` | Dataset discovery, acquisition, provenance, construction and QA |
| `tools/{data,evidence,prediction,case_memory}/` | Registered analyses and case workflows |
| `research/` | Experimental algorithms and their frozen protocols |
| `log/` | Dated results, limits and repository changes |
| `tests/` | Core and tool contract tests |
| `data/`, `outputs/`, `tmp/`, `reference/` | Local datasets, generated artifacts and reference material |

The core does not import tools or research. Research protocols and hashes remain historical
records; a positive development result does not automatically qualify a production model.
The current consolidation and verification record is
[log/20260929/README.md](log/20260929/README.md).

## Run

```bash
python -m pip install -e ".[test]"
python -m pytest
maestro --help
python -m tools.datasets.catalog --help
python -m tools.evaluation.cli --help
```

Dataset requirements and commands are in [tools/datasets/README.md](tools/datasets/README.md).
Registered tool groups are in [tools/README.md](tools/README.md).
Research status is indexed in [research/README.md](research/README.md).
