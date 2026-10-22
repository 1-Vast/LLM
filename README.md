# MAESTRO

MAESTRO is a dual-core autonomous research framework for contextual early drug discovery. It studies how research methods transfer across drugs and cellular contexts: when an existing method applies, what evidence can reveal failed transfer, and how measured feedback can improve subsequent research decisions. Current validation is mainly in oncology cell models; general autonomous discovery and clinical efficacy remain unestablished.

The Autonomous Scientific Agent proposes and revises executable research procedures. The Virtual Cell predicts scoped functional responses, candidate differences and model mismatch, then updates supported components from feedback. Their shared task is to learn when previous research experience helps a new decision, when to check its assumptions and when to change the plan. Typed contracts separate predictions from measurements and keep costs and failures visible.

The [research programme](log/archive/HISTORY.md) defines two primary tasks: candidate discovery/repurposing and cellular-context selection with failure analysis. Selectivity needs explicit comparison measurements; mechanism confirmation needs distinguishing evidence. Dose, time and combinations are gated extensions. The programme tests method transfer, within-task feedback, dual-core contributions and selected-candidate reliability separately. The existing thin `maestro.research_loop` is static replay infrastructure; automatic feedback-based replanning and learned procedure transfer remain research goals.

## Install and run

```powershell
Set-Location D:\MAESTRO
& 'D:\anaconda\envs\maestro\python.exe' -m venv .venv
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pip install -r requirements-preparation.lock
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pip install --no-deps --no-build-isolation -e '.[test,preparation]'
& 'D:\MAESTRO\.venv\Scripts\Activate.ps1'
& 'D:\MAESTRO\.venv\Scripts\maestro.exe' --help
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pytest
```

The supported CPU preparation environment is local `.venv`, built from the existing
`maestro` Python 3.11.16. The pinned Windows/Python-3.11 specification is
[requirements-preparation.lock](requirements-preparation.lock). See
[preparation checks and limitations](log/20261020/PREPARATION.md), the
[actual data inventory](data/INVENTORY.md), [cleanup/recovery](log/20261020/PREPARATION.md)
and the [next English execution prompt](log/20261020/NEXT_RESEARCH_PROMPT.md).
The legacy conda environment is retained for historical compatibility and requested tests;
its incomplete arc-state installation is not part of the clean CPU environment.

```powershell
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m tools.research_validation --verify
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

The model predicts within qualified scope; it does not establish functional endpoints, mechanism, causality or experiment value by itself. The Agent selects and audits evidence and actions; it does not turn language-model output into scientific fact. Current conclusions are in [research/REPORT.md](research/REPORT.md), with numerical results in [research/EVIDENCE.md](research/EVIDENCE.md). The [programme stages](log/archive/HISTORY.md#validation-stages-for-research-method-transfer) separate method value, Agent value, transfer and independent confirmation. PRESAGE P0 remains NO-GO; anchor purchasing value remains blocked by independent-endpoint qualification.

### Latest Research Update (2026-10-21)

The latest dual-core validation on the public PTV-1 / ProteinTalks release ended with `STOP_THIS_TASK_CONFIGURATION`: the re-implemented ppODE was below the strongest conventional predictor, feedback did not improve over ordinary updating, and no LLM program edit was accepted. This is a negative result on one exposed published-label task with seven held-out lineages, not a general test of autonomous discovery. See the [integrated research decisions](research/REPORT.md), [numerical evidence](research/EVIDENCE.md), and [full study record](research/dual_core_innovation_validation_20261021/REPORT.md).

Registered studies retain their protocols, results, deviations and replay code. The current evidence, stop decisions and simplification ledger are in [research/REPORT.md](research/REPORT.md). Frozen research records are separate from the maintained runtime and default software tests.
