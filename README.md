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
The current dual-core workflow and verification record is
[log/20261003/README.md](log/20261003/README.md).
The certified dual-core discovery block is in
[research/certified_discovery/README.md](research/certified_discovery/README.md). Combination
discovery is a task where prediction binds decisions. The world model learns in context, and
claims about untested candidates are certified by a random audit. Its confirmatory run on
NCI-ALMANAC passed both pre-registered tests, and its components are promoted into `src/` and
`tools/`. A later audit and an untouched validation test found that this gain does not produce
more independently validated discoveries:
[research/astra/feedback_validation_20261003/REPORT.md](research/astra/feedback_validation_20261003/REPORT.md).
How to split a fixed budget between screening, independent verification and stopping, with
repaired accounting and a blocked confirmatory protocol, is in
[research/astra/reproducible_allocation_20261003/REPORT.md](research/astra/reproducible_allocation_20261003/REPORT.md).
The supported architecture, reproduction entry point and dataset qualification are in
[research/dual_core_completion/README.md](research/dual_core_completion/README.md).
The literature-guided frozen-data experiments, negative policy result and source limits are in
[research/dual_core_followup/README.md](research/dual_core_followup/README.md).
The live DeepSeek/Jev validation, report-only defect auditor and general contract evaluation are in
[research/dual_core_live/README.md](research/dual_core_live/README.md).
The next real predecision-state data audit and acquisition plan are indexed in
[tools/datasets/STATE_IDENTIFIABILITY.md](tools/datasets/STATE_IDENTIFIABILITY.md).
The subsequent public-source search, raw relation construction and collection specification are in
[the October 1 continuation](log/20261001/README.md#15-public-source-search-and-relation-construction-after-3923541).
The supplied evidence report and its independent replay, control-well erratum,
and design-specific contracts are indexed in
[the evidence addendum](log/20261001/README.md#16-independent-review-of-the-supplied-state-evidence-report).
The real STATE input certification, public-knowledge retrospective prediction experiment,
and executable collection templates are in
[the prospective-input and knowledge report](tools/datasets/audit_results/20261001_state_prospective/REPORT.md).

## Run

```bash
python -m pip install -e ".[test]"
python -m pytest
maestro --help
python -m tools.datasets.catalog --help
python -m tools.evaluation.cli --help
```

Default pytest runs the explicit asset-free core contracts. Small frozen replay
and full research require explicit paths and their declared assets; commands and
cross-environment limits are in [the convergence report](research/astra/CONVERGENCE.md).

Dataset requirements and commands are in [tools/datasets/README.md](tools/datasets/README.md).
Registered tool groups are in [tools/README.md](tools/README.md).
Research status is indexed in [research/README.md](research/README.md).

Raw RNA reconstruction, real STATE sensitivity and conditional retrospective state prediction are in
[the STATE response research report](tools/datasets/audit_results/20261001_state_response/REPORT.md).

The review-guided ASTRA decision/feedback prototype, paired STATE correction and residual
diagnostics are in [research/astra/README.md](research/astra/README.md) and
[the October 2 record](log/20261002/README.md).
The subsequent native zero attribution and bounded policy diagnostics are in
[the ASTRA EGR1 audit](research/astra/ZERO_AUDIT.md).
The cheap-input decision and mechanism research questions, native observed-action
coverage and next experimental gates are in
[the ASTRA eight-question review](research/astra/EIGHT_QUESTIONS.md).
Independent source reproduction and finite sensitivity analysis of the supplied
GDSC policy reports are in [the GDSC review](research/astra/GDSC_INDEPENDENT_REVIEW.md).
Later-layout measured transport, CTRP menu qualification and randomized pilot preparation
are in [the GDSC follow-up](research/astra/GDSC_TRANSPORT_FOLLOWUP.md).
