# Identifiability and dual-core impact audit

Round 1 is recorded in `log/20260930/README.md`; its artifacts remain under
`outputs/identifiability_audit_20260930/`. The missing log/test were recovered from
Git stash object `11f7e57`. The original stash was retained.

Round 2's authoritative entry point is `round2.py`, with `verify`, `run`, and
`analyse` stages. The inherited `intervention.py` draft was **not executed**:
it substitutes ReferenceWorld for unavailable WorldV2 and some policy wrappers
construct their own forecast. Its unrelated `sparse_two_step` is not risk-select.
Round 2 uses the existing belief planner, discrimination selector and genuine
`wrong_risk_cap` policy with one injected query-to-forecast function.

Use `D:/anaconda/envs/maestro/python.exe` from the repository root. All outputs are
write-once. Reproduction should target a new output directory. First run the
Round-1 lineage scripts and `unified_score` with `--out` below that directory,
using subdirectories `round1_replay/sciplex3_B`, `round1_replay/l1000_LT`, and
`round1_replay/unified_score`; then run:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2 verify --out OUTPUT_DIRECTORY
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2 run --out OUTPUT_DIRECTORY
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2 analyse --out OUTPUT_DIRECTORY
```

The verified run is `outputs/identifiability_round2_20260930/`. The dated record
contains all executed commands, source corrections, eight predeclared cells,
39,408 episode-cell results, four-arm review, partial-identification rules,
exposure history and explicit not-run analyses.

Companion entry points: `state_round2.py` repeats inference seeds on inherited
registered queries; `round2_cached_world.py` reviews historical WorldV2 reading
forecasts without generating a new forecast; `round2_physical_controls.py` keeps
physical dependency graphs separate; `round2_risk.py` computes descriptive
same-coverage risk; `round2_validate.py` independently checks every terminal/cost
path and original artifact hashes; `round2_report.py` creates the dated section.
The computation modules expose `run(output_path)` for a fresh output root;
STATE's CLI also accepts the root as its first argument. Reporting exposes
`render(output_path)` and `generate(output_path)` and never silently overwrites
a dated section. Generate the report after computing the risk supplement.

`round2_delivery.py` checks the final report against its renderer, preserves a
final code/document snapshot, and writes `delivery_ledger.json`. That ledger
includes the post-validation physical/risk supplements, final report and dated
log hashes; `artifact_ledger.json` remains the earlier validation-stage ledger.
Run the delivery stage last: `python -m research.identifiability_audit.round2_delivery`.

WorldV2 swap is not runnable without serialized fitted transitions or a complete
forecast bank. Its historical reading-quality review is not a substitute for
that intervention. STATE and case-memory are separate targets/populations.
Known QC failures are observed attempts; unresolved source comparisons use
the declared utility range [-2,+1]. No production module is edited.
