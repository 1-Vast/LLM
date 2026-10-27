# MAESTRO

MAESTRO is a dual-core autonomous research framework for contextual early drug discovery. It studies how research methods transfer across drugs and cellular contexts: when an existing method applies, what evidence can reveal failed transfer, and how measured feedback can improve subsequent research decisions. Current validation is mainly in oncology cell models; general autonomous discovery and clinical efficacy remain unestablished.

The Autonomous Scientific Agent proposes and revises executable research procedures. The Virtual Cell predicts scoped functional responses, candidate differences and model mismatch, then updates supported components from feedback. Their shared task is to learn when previous research experience helps a new decision, when to check its assumptions and when to change the plan. Typed contracts separate predictions from measurements and keep costs and failures visible.

The [research programme](log/RESEARCH_REPORT.md#current-paid-repeatability-result) defines two primary tasks: candidate discovery/repurposing and cellular-context selection with failure analysis. Selectivity needs explicit comparison measurements; mechanism confirmation needs distinguishing evidence. Dose, time and combinations are gated extensions. The programme tests method transfer, within-task feedback, dual-core contributions and selected-candidate reliability separately. The existing thin `maestro.research_loop` is static replay infrastructure; automatic feedback-based replanning and learned procedure transfer remain research goals.

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
[actual data inventory](data/INVENTORY.md) and [research records](log/README.md).
The existing conda environment remains an installed environment outside this source refactor;
its incomplete arc-state installation is not part of the clean CPU environment.

```powershell
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m tools.research_validation --verify
```

The research preflight checks explicitly supplied frozen inputs and outputs. No active study is currently released.

* It authenticates every file a study's `FREEZE.json` lists under its `inputs`, `sha256` or `files` mapping.
* Missing or mismatched assets are reported as `BLOCKED/ASSET_MISSING`.
* Any other freeze schema is refused as `BLOCKED/FREEZE_SCHEMA_UNSUPPORTED`; it is never skipped.

The compact experiment register, failure reasons and next directions are in [`log/`](log/README.md). Durable protocols, reports, decisions and provenance records belong in `log/`; experimental implementations and tests remain in `research/`. Historical source IDs are read through the [storage policy and record reader](log/STORAGE_POLICY.md); old execution paths are retired.

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
| `research/` | Experimental implementations, research tests and study registry |
| `log/` | Current scientific synthesis, durable study records and evidence navigation |
| `data/` | Raw inputs, external sources, derived data and model artifacts |
| `data/processed/research_packages/` | Three verified packages of retired implementations, numeric artifacts and workbench assets |
| `tests/` | Core contracts and regression checks; research tests run explicitly |
| `tmp/` | Retained GPU environment, nested DGM checkout, test state and explicitly protected payloads; historical workbench assets are packaged |

Minimal command examples:

```bash
python -m tools.datasets.catalog --help
python -m tools.evaluation.cli --help
python -m tools.research_validation --help
```

## Scientific boundary

The model predicts within qualified scope; it does not establish functional endpoints, mechanism, causality or experiment value by itself. The Agent selects and audits evidence and actions; it does not turn language-model output into scientific fact. Current conclusions are in [current research status](log/RESEARCH_REPORT.md#current-paid-repeatability-result), with numerical results in [research/EVIDENCE.md](research/EVIDENCE.md). The [programme boundaries](log/RESEARCH_REPORT.md#current-paid-repeatability-result) separate method value, Agent value, transfer and independent confirmation. PRESAGE P0 remains NO-GO; anchor purchasing value remains blocked by independent-endpoint qualification.

### Current research and literature

Start with the [current research synthesis](log/RESEARCH_REPORT.md#current-paid-repeatability-result) for findings, stopped configurations and evidence gaps. The [literature chapter](log/RESEARCH_REPORT.md#literature-and-source-access) distinguishes two incomplete research surveys from a search-tool validation; the [study index](log/STUDY_INDEX.tsv) traces individual decisions. Storage maintenance does not establish new scientific results.

### Historical dual-core validation (2026-10-21)

The dual-core validation on the public PTV-1 / ProteinTalks release ended with `STOP_THIS_TASK_CONFIGURATION`: the re-implemented ppODE was below the strongest conventional predictor, feedback did not improve over ordinary updating, and no LLM program edit was accepted. This is a negative result on one exposed published-label task with seven held-out lineages, not a general test of autonomous discovery. See the [integrated research decisions](log/RESEARCH_REPORT.md#functional-feedback-and-acquisition), [numerical evidence](research/EVIDENCE.md), and exact source ID `log/research_records/dual_core_innovation_validation_20261021/REPORT.md` ([reader](log/README.md)).

Registered studies retain their protocols, results, deviations and replay code. The current evidence, stop decisions and simplification ledger are in [current research status](log/RESEARCH_REPORT.md#current-paid-repeatability-result). Frozen research records are separate from the maintained runtime and default software tests.

## Changelog

### 2026-10-27 - Agent and virtual-cell research sources

- Integrate the R196v2/R197v2 inconclusive audits, R199/Q0 qualification stops, and the ON3 authorization/peek boundary in the maintained research report.
- Preserve the recent research source lineage, negative results, amendments and independent reviews through exact source IDs; retain Chinese originals in the source layer and English maintained navigation.
- Publish ten research directions and four conditional mechanism candidates. None is promoted to runtime or certified as a new algorithm, biological mechanism, transfer result, decision benefit or RSI.
- Keep datasets, environments, protected outcomes, third-party full papers and author-code checkouts local. The source manifest enables knowledge recovery; complete experiment replay requires separately supplied assets.

### 2026-10-25 - Evidence and navigation review

- Correct 14 main-chapter targets after reviewing all 39 registered studies.
- Distinguish the KG analytical value from its repaired Monte Carlo estimate; retain the G1 strict margin and population, legacy replay limits and explicit evidence grades.
- Bind six selected fact contracts to published sources and exact report excerpts, with independent review. Default checks require no local dataset or large package. This does not establish exhaustive semantic coverage or a scientific method advantage.
- Asset-free clean-checkout software suite: 1,095 passed, 4 skipped. Knowledge continuity is verified separately from data-dependent calculation checking and experimental reproduction.
- Isolate the synthetic worked-example test output in a temporary directory; it previously rewrote a tracked research JSON file, changing line endings on Windows.

### 2026-10-25 - Maintenance verification

- Parse signature arrays and calibration from the same bytes used for their hashes.
- Keep protected inventory entries unverified without reading payloads; stream binary hashes.
- Distinguish inexpensive Level 5 metadata/receipt checks from an explicit full-content rehash.
- Add an optional exact-source record reader with single-load lookup and isolated regression fixtures. Local stores and research packages are not bundled.
- This release preserves historical research through fixed source identities and publishes no new scientific result.
- Publish the complete key-information refactor: one maintained research report, the study index, current code and pinned historical source identities. Small unique text corrections accompany the manifest; data, models and large research packages stay local. Historical loose files are retired from the current tree while their pinned Git versions remain available.
