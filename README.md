# MAESTRO

MAESTRO combines a scientific decision agent with a virtual-cell world model.
The agent chooses admissible evidence and experiments under a resource limit;
the world model predicts supported intervention responses. Qualified observations,
not predictions, determine scientific conclusions.

The world-model foundation is the official pretrained **STATE `final.ckpt`**.
Condition, source, feature-axis and model identity are checked before use.
A transcript forecast does not establish protein activity, apoptosis function,
causal mechanism or the value of an experiment.

## Run

```bash
python -m pip install -e ".[test]"
python -m pytest
maestro --help
python -m tools.datasets.catalog --help
python -m tools.evaluation.cli --help
```

Default tests cover asset-free contracts. Research and frozen regression runs
require their explicit data and commands; see [research](research/README.md).
No optional model or raw-data dependency is required for the default contracts.

## Ownership

| Path | Responsibility |
|---|---|
| `src/agent/` | Planning, execution coordination, providers, context and persistence |
| `src/maestro/` | Evidence admission, scientific decision and repair contracts |
| `src/virtual_cell/` | Prediction identity, applicability, adapters and refusal |
| `tools/` | Reusable acquisition, provenance, analysis and evaluation |
| `research/` | Experimental fitting, policies, protocols and evaluation assets |
| `log/` | Dated experiment records, verification and publication receipts |
| `tests/` | Behavioural contracts and explicitly scoped research checks |

CaseStore owns plans, attempts, results and budget facts. Predictions and derived
summaries retain their source identity. The core does not import research or tools.

## Current evidence

The measured engineering repairs support request binding, source resolution,
feedback, retries and bounded execution. Native-STATE public-data studies show
condition-specific signals, but a general dual-core or LLM decision advantage
has not been established. The latest candidate-comparison acquisition experiment
matches strong KG on final value and cost; its stopping rule does not save profiles.
All five target contexts were previously exposed.

Read [the consolidated research report](research/REPORT.md) for conclusions and
[the evidence register](research/EVIDENCE.md) for exact results, limits and
reproduction. [The experiment log](log/INDEX.md) holds dated records.
[task.md](task.md) defines the operating contract; [Innovation.md](Innovation.md)
states the falsifiable research hypothesis. Reports are maintained in English;
obsolete narrative copies are removed rather than archived.
