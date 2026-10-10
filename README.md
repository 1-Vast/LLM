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

Default tests cover asset-free production contracts. Research test groups are explicitly scoped: `python -m tools.research_validation`. Frozen studies
require their listed packet and outputs. Run `python -m tools.research_validation --verify`
for a hash and asset preflight; missing files are reported as `BLOCKED/ASSET_MISSING`.
Passing contract tests does not mean a research experiment was rerun.

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

The 2026-10-10 phenotype-anchored study tested STATE on a functional endpoint measured in the
same spheroids as its RNA: Tahoe relative-survival selectivity on five held-out lines. Basal-
similarity transfer beat STATE (delta r -0.23) and generic ranking (top-10 +0.56 log2, 5/5). A
registered world-model value gate refused STATE from reference data alone, and held-out lines
confirmed the refusal. The gate, same-unit bridge rule and basal transfer are promoted with scope.

Software checks and replay receipts establish engineering behaviour, not independent
scientific benefit. STATE remains the pretrained world-model foundation; decision
benefit, LLM advantage and functional or causal claims remain unestablished.

The separate P0.5R-Extension qualifies the specified **39 endpoint coordinates** in
c44 and c45 against all 62,710 source genes. It reuses exposed c44 data and acquires
133,564 new c45 expression bytes. This is file-local data identity evidence, not a
fresh biological holdout. The full 2,000-gene and STATE checkpoint output axes
remain uncertified. P0.6 needs a new execution freeze; P2 and production promotion
remain closed. Historical failures are preserved.

Read [the research index](research/INDEX.md) for navigation,
[the report](research/REPORT.md) for current conclusions and next gates,
[the evidence register](research/EVIDENCE.md) for numerical results and replay
paths, and [the experiment log](log/INDEX.md) for dated receipts.
[Blocked assets](BLOCKED_ASSETS.md) distinguishes locally retained evidence from
what a clean checkout can reproduce.
