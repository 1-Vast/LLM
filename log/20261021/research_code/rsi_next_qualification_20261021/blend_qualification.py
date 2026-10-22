"""Same-configuration attribution on exposed PTV-1; no new confirmation.

Run with python -B research/rsi_next_qualification_20261021/blend_qualification.py.
Only log/20261021/rsi_next_qualification is written. No world models are retrained;
conventional logistic/HGB classifiers are refit from the original training scope.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[key] = "4"
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "research/dual_core_innovation_validation_20261021"
REPAIR = ROOT / "research/dual_core_innovation_validation_20261021_repair1"
OUT = ROOT / "log/20261021/rsi_next_qualification"
WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)
SEED = 20261021
MARGIN = 0.09

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(OLD))
import ptv_data as D
import ptv_direct as X
import ptv_tasks as T


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def snapshot():
    frozen = json.loads((OLD / "FREEZE.json").read_text())["frozen_files"]
    files = [OLD / key for key in frozen]
    files += [p for p in REPAIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    observed = {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}
    bad = [key for key, value in frozen.items() if observed[str((OLD / key).relative_to(ROOT))] != value]
    if bad:
        raise RuntimeError(f"Pre-existing original freeze mismatch: {bad}")
    return observed, len(frozen)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def peak_memory():
    """Authenticate the Windows counter; an OS-call failure is not zero RAM."""
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(k, ctypes.c_size_t) for k in
                    ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.argtypes = []
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(counters.PeakWorkingSetSize)


def predictions(stage, variant, seed):
    directory = OLD / "RUN" / ("sel30" if stage == "sel" and variant == "full" else stage)
    frames, inputs = [], []
    for p in sorted(directory.glob(f"{stage}_*_{variant}_s{seed}.npz")):
        # Object arrays are trusted local research assets, authenticated below.
        with np.load(p, allow_pickle=True) as z:
            prob = z["p_e30"] if "p_e30" in z else z["p"]
            d = pd.DataFrame({"cell": z["cell"], "perts": z["perts"], "y": z["lab"], "single": z["single"], variant: prob})
        d = d.loc[d.single & d.y.notna()].drop(columns="single")
        if d.duplicated(["cell", "perts"]).any():
            raise RuntimeError("Duplicate stock/drug prediction")
        frames.append(d)
        inputs.append({"path": str(p.relative_to(ROOT)), "sha256": sha(p)})
    if not frames:
        raise RuntimeError(f"Missing predictions: {stage}/{variant}/{seed}")
    return pd.concat(frames, ignore_index=True), inputs


def attach_world(d, stage, seed):
    inputs = []
    for variant in ("full", "no_traj"):
        pred, used = predictions(stage, variant, seed)
        d = d.merge(pred, on=["cell", "perts"], how="inner", validate="one_to_one", suffixes=("", "_cached"))
        if not np.array_equal(d.y.to_numpy(), d.y_cached.to_numpy()):
            raise RuntimeError("Cached and source labels disagree")
        d = d.drop(columns="y_cached")
        inputs.extend(used)
    d["lineage"] = d.cell.map(D.lineage_of)
    return d, inputs


def direct_scores(prep, model, ex, stage):
    scope = ex[ex.part.isin(["dev", "sel"])]
    held = ex[ex.part == stage]
    frames = []
    for cell in sorted(held.cell.unique()):
        tr = scope[scope.lineage != D.lineage_of(cell)].dropna(subset="y")
        te = held[held.cell == cell].dropna(subset="y").copy()
        te["lr"] = model.fit_predict(tr, te, "lr")
        te["hgb"] = model.fit_predict(tr, te, "hgb", seed=0)
        pairs = [model.priors(tr, cell, drug) for drug in te.perts]
        gm = float(tr.y.mean())
        te["b1"] = [b if np.isfinite(b) else (a if np.isfinite(a) else gm) for a, b in pairs]
        pool = set(T.contested_pool(tr, te.perts.tolist()))
        te["in_pool"] = te.perts.isin(pool)
        frames.append(te[["cell", "perts", "y", "b1", "lr", "hgb", "in_pool"]])
    return pd.concat(frames, ignore_index=True)


def metrics(frame, score):
    rows = []
    for cell, d in frame.loc[frame.in_pool].groupby("cell", sort=True):
        if len(d) < 6:
            continue
        # Explicit deterministic drug tie-break, identical for every arm.
        d = d.sort_values([score, "perts"], ascending=[False, True], kind="stable")
        rows.append({"cell": cell, "lineage": D.lineage_of(cell), "arm": score,
                     "n_pool": len(d), "hits5": int(d.y.iloc[:5].sum()),
                     "prec5": float(d.y.iloc[:5].mean()),
                     "brier": float(np.mean((d[score] - d.y) ** 2)),
                     "auroc": float(roc_auc_score(d.y, d[score])) if d.y.nunique() > 1 else None,
                     "selected_drugs": "|".join(d.perts.iloc[:5])})
    return pd.DataFrame(rows)


def macro(table, arm):
    return float(table[table.arm == arm].groupby("lineage").prec5.mean().mean())


def choose_weights(selection):
    grid, chosen = [], {}
    for added in ("full", "no_traj", "lr", "hgb"):
        trial = []
        for w in WEIGHTS:
            c = selection.copy()
            c["mix"] = (1 - w) * c.b1 + w * c[added]
            value = macro(metrics(c, "mix"), "mix")
            trial.append((value, w))
            grid.append({"added": added, "weight": w, "selection_prec5": value})
        chosen[added] = min(trial, key=lambda t: (-t[0], t[1]))[1]
    return chosen, grid


def contrast(table, a, b):
    p = table.groupby(["lineage", "arm"]).prec5.mean().unstack()
    delta = (p[a] - p[b]).dropna().to_numpy()
    if not len(delta):
        raise RuntimeError("No paired lineage units")
    rng = np.random.default_rng(SEED)
    boot = rng.choice(delta, size=(10000, len(delta)), replace=True).mean(axis=1)
    return {"a": a, "b": b, "difference_prec5": float(delta.mean()),
            "descriptive_95ci": np.quantile(boot, [0.025, 0.975]).tolist(),
            "n_lineages": len(delta)}


def main():
    t0, cpu0 = time.perf_counter(), time.process_time()
    OUT.mkdir(parents=True, exist_ok=True)
    before, frozen_n = snapshot()
    if (OUT / "INTEGRITY_BEFORE.json").exists():
        previous = json.loads((OUT / "INTEGRITY_BEFORE.json").read_text())
        if previous["files"] != before:
            raise RuntimeError("Refuse to replace a different integrity baseline")
    else:
        save("INTEGRITY_BEFORE.json", {"frozen_original_files": frozen_n, "files": before})
    save("EXECUTION_STATUS.json", {"status": "running", "argv": sys.argv, "exposure": "already_exposed_development"})
    prep = T.Prep()
    model = X.Direct(prep)
    ex = prep.R.experiments(1)
    selection_direct = direct_scores(prep, model, ex, "sel")
    selection, inputs = attach_world(selection_direct, "sel", 0)
    weights, grid = choose_weights(selection)
    pd.DataFrame(grid).to_csv(OUT / "weight_search.csv", index=False)
    selection.to_csv(OUT / "selection_scores.csv", index=False)
    # Chosen before scoring old-final data or reading cached old-final predictions.
    # Release itself loads exposed source labels in RAM; this is not an access seal.
    save("SELECTED_WEIGHTS.json", {"weights": weights, "stage": "selection_only", "slots_per_family": len(WEIGHTS)})
    print("Selection weights fixed", weights, flush=True)
    final_direct = direct_scores(prep, model, ex, "final")
    final_tables, summaries = [], []
    for seed in (0, 1):
        frame, used = attach_world(final_direct, "final", seed)
        inputs.extend(used)
        cols = ["b1", "lr", "hgb", "full", "no_traj"]
        for added, w in weights.items():
            for prefix, weight in (("half_", 0.5), ("selected_", w)):
                name = prefix + added
                frame[name] = (1 - weight) * frame.b1 + weight * frame[added]
                cols.append(name)
        table = pd.concat([metrics(frame, c) for c in cols], ignore_index=True)
        table["seed"] = seed
        final_tables.append(table)
        frame.to_csv(OUT / f"exposed_scores_seed{seed}.csv", index=False)
        alternatives = ["selected_no_traj", "selected_lr", "selected_hgb"]
        best = max(alternatives, key=lambda a: macro(table, a))
        primary = contrast(table, "selected_full", best)
        secondary = [contrast(table, "selected_full", a) for a in ["b1"] + alternatives]
        secondary += [contrast(table, "half_full", a) for a in ["half_no_traj", "half_lr", "half_hgb", "b1"]]
        summaries.append({"seed": seed, "means_prec5": {a: macro(table, a) for a in cols},
                          "primary_vs_strongest_nonworld": primary, "contrasts": secondary,
                          "continue_ptv": primary["difference_prec5"] >= MARGIN and primary["descriptive_95ci"][0] > 0})
        print("Seed", seed, json.dumps(summaries[-1]), flush=True)
    pd.concat(final_tables, ignore_index=True).to_csv(OUT / "decisions.csv", index=False)
    after, _ = snapshot()
    if before != after:
        save("INTEGRITY_FAILURE.json", {"changed": [key for key in before if before[key] != after.get(key)]})
        raise RuntimeError("Historical files changed during qualification")
    save("INTEGRITY_AFTER.json", {"same_as_before": True, "files_verified": len(before), "frozen_original_files": frozen_n})
    save("INPUTS.json", {"prediction_files": inputs, "protocol_sha256": sha(OUT / "PROTOCOL.md"),
                         "script_sha256": sha(Path(__file__)), "source_manifest_sha256": sha(OLD / "SOURCE_MANIFEST.json")})
    save("RESULTS.json", {"decision": "QUALIFY_MATCHED_SUPERVISION_CONTROL" if all(s["continue_ptv"] for s in summaries) else "STOP_FURTHER_PTV_SEARCH",
                          "exposure": "ALREADY_EXPOSED_DEVELOPMENT_ONLY", "margin_prec5": MARGIN,
                          "weights": weights, "seeds": summaries,
                          "limits": ["No independent confirmation", "M1/M2 capacity and supervision confounded", "Cached original training seed initialization imperfect",
                                     "Historical input-only transductive PCA", "No novel-drug transfer test", "No agent/RSI effect tested"]})
    save("RESOURCES.json", {"wall_seconds": time.perf_counter() - t0, "process_cpu_seconds": time.process_time() - cpu0,
                            "peak_working_set_bytes": peak_memory(), "python": sys.version, "platform": platform.platform(),
                            "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__,
                            "bootstrap_seed": SEED, "bootstrap_draws": 10000, "saved_training_seeds": [0, 1],
                            "conventional_classifier_fits": 2 * (selection_direct.cell.nunique() + final_direct.cell.nunique()),
                            "world_model_retrains": 0, "historical_world_training_compute_included": False,
                            "threads": 4, "gpu_seconds": 0, "api_requests": 0, "download_payload_bytes": 0,
                            "command": "& 'D:/anaconda/envs/maestro/python.exe' -B research/rsi_next_qualification_20261021/blend_qualification.py"})
    save("EXECUTION_STATUS.json", {"status": "complete", "argv": sys.argv})


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
