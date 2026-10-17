# MAESTRO

MAESTRO is a dual-core autonomous research framework for contextual early drug discovery. It studies how research methods transfer across drugs and cellular contexts: when an existing method applies, what evidence can reveal failed transfer, and how measured feedback can improve subsequent research decisions. Current validation is mainly in oncology cell models; general autonomous discovery and clinical efficacy remain unestablished.

The Autonomous Scientific Agent proposes and revises executable research procedures. The Virtual Cell predicts scoped functional responses, candidate differences and model mismatch, then updates supported components from feedback. Their shared task is to learn when previous research experience helps a new decision, when to check its assumptions and when to change the plan. Typed contracts separate predictions from measurements and keep costs and failures visible.

The [research programme](log/RESEARCH_PROGRAM.md) defines two primary tasks: candidate discovery/repurposing and cellular-context selection with failure analysis. Selectivity needs explicit comparison measurements; mechanism confirmation needs distinguishing evidence. Dose, time and combinations are gated extensions. The programme tests method transfer, within-task feedback, dual-core contributions and selected-candidate reliability separately. The existing thin `maestro.research_loop` is static replay infrastructure; automatic feedback-based replanning and learned procedure transfer remain research goals.

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

The compact experiment register, failure reasons and next directions are in [`log/`](log/). Authoritative frozen records remain in `research/`.

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

The model predicts within qualified scope; it does not establish functional endpoints, mechanism, causality or experiment value by itself. The Agent selects and audits evidence and actions; it does not turn language-model output into scientific fact. Current conclusions are in [research/REPORT.md](research/REPORT.md), with numerical results in [research/EVIDENCE.md](research/EVIDENCE.md). The [programme stages](log/RESEARCH_PROGRAM.md#validation-stages-for-research-method-transfer) separate method value, Agent value, transfer and independent confirmation. PRESAGE P0 remains NO-GO; anchor purchasing value remains blocked by independent-endpoint qualification.

Registered studies retain their protocols, results, deviations and replay code. The current evidence, stop decisions and simplification ledger are in [research/REPORT.md](research/REPORT.md). Frozen research records are separate from the maintained runtime and default software tests.
