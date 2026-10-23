# MAESTRO-FAR: Development Study, Reproduction, and Audit

**Current verdict: `FAR_NOT_SUPPORTED`.** The current kernel/kNN + L1000 transfer implementation did not show that FAR slice selection outperforms exploit-first. This does not falsify the broader Agent + Virtual Cell research direction.

Read the [reproduction and methods audit](audit_20261019/REPORT.md) first, then the [original study results](REPORT.md) and [frozen decision](DECISION.json). Claims in the original report about strict three-stage isolation, exactly equal drug-count costs, and future-task headroom must be interpreted in light of the audit.

## Files

| Category | Files | Status and use |
|---|---|---|
| Frozen core | `far_core.py`, `far_data.py`, `MODEL.json`, `VALUE_MODEL.pkl`, `FREEZE_PROTOCOL.md` | Pinned by `FREEZE.json`; not changed during cleanup |
| Completed study | `records_*.npz`, `ATLAS_*.json`, `CONTRASTS_*.json`, `DECISION.json`, `V2_SEARCH.json` | Original results retained; the vault reuses already exposed data |
| Read-only verification | `verify.py`, `far_decide.decide()` | Checks the freeze, recomputes the original gate and one primary contrast from saved records; writes no results and trains no model |
| Deep reproduction | `audit_20261019/audit.py` | Independently recomputes 118 contrasts, rebuilds 54 select/test policy combinations, and checks data and stage dependencies; writes only in the audit directory |
| Historical runners | `far_run.py`, `far_v2_search.py`, `far_vault.py`, `far_analyse.py`, `qualify_edges.py` | Retained as reproduction sources; commands that generate existing stages/models refuse to overwrite them. Analysis and metadata commands still write their JSON outputs, so use the read-only entry point for routine checks. |
| Earlier drafts | `AUDIT.md`, `PROTOCOL.md`, `EDGES.json` | Phase 0 audit and draft. “Not yet run” describes the earlier state; the executed study is defined by `FREEZE_PROTOCOL.md`. |
| Study history | `DEVIATIONS.json`, `discarded_run0/` | Retains deviations and the discarded unequal-cost run; identical atlas/model copies were deduplicated |
| Cleanup regression | `test_maintenance.py`, `CLEANUP.json` | Records cleanup checks for non-frozen scripts, read-only behavior, and overwrite guards |

## Routine Checks

From `D:/MAESTRO` in PowerShell:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -B research/maestro_far_20261019/verify.py
& 'D:\anaconda\envs\maestro\python.exe' -B -m pytest research/maestro_far_20261019/test_maintenance.py -p no:cacheprovider
```

For a full strategy reproduction, use the original dependency environment. The current `maestro` environment uses scikit-learn 1.9.0, which cannot directly load the pickle created with scikit-learn 1.6.1:

```powershell
& 'D:\anaconda\python.exe' -B -c 'import os,runpy; h=os.add_dll_directory("D:/anaconda/Library/bin"); runpy.run_path("research/maestro_far_20261019/audit_20261019/audit.py",run_name="__main__")' --original-env
```

The deep reproduction updates the corresponding audit result JSON. Results from the single-threaded, original default-thread, and `maestro` environments are retained as compatibility and sensitivity evidence. Historical `predecessor_sha256` values identify the file version used in that run; later cleanup of non-frozen drivers is recorded in `CLEANUP.json`, so those historical hashes must not be treated as hashes of the current code.

## Next Steps

Before revisiting whether MoA or target knowledge predicts assay value, define isolated references, complete MoA and structural identity groups, exact costs, and evaluator access boundaries, then freeze a new protocol. The current test and vault data are exposed; repartitioning them would still provide development evidence. Agent, 2x2, and transfer phases did not pass their prerequisites and were not run.
