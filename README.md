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

Default tests cover asset-free production contracts. The three current research
test groups are explicit: `python -m tools.research_validation`. Frozen studies
require their listed packet and, where noted, external assets.

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

Engineering closure is verified. The original STATE study reports a task-specific
RNA prediction signal, while independent decision benefit, LLM advantage,
functional phenotype and mechanism causality remain unestablished. All five
current target contexts were previously exposed.

Read [the research report](research/REPORT.md) for claim boundaries and next
steps, [the evidence register](research/EVIDENCE.md) for canonical results and
reproduction paths, and [the experiment log](log/INDEX.md) for dated receipts.
