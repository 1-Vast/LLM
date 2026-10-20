"""Internal development replay on the previously RELEASED backgrounds of the O'Neil export (H0, D1, D2, D3 only; 18 of 39 cells).

Restricted export: the A (anchor) and T (target) backgrounds of the predecessor study are sliced away at load time and never decoded; the writer
records only their names' hash. This is exposed development data (the predecessors already analysed these cells): it is a software/behaviour check
under the real observation structure, NOT independent evidence and NOT a test of H4. One world => no stream-level inference.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "self_improving_virtual_cell_20261020"))

from svc_evolution import split_cells  # noqa: E402
from svc_world import Static, World  # noqa: E402

SRC = ROOT / "tmp" / "self_improving_virtual_cell_20261020" / "env_export.npz"
DST = ROOT / "tmp" / "innovation_validation_20261020" / "env_export_released_only.npz"


def write_restricted():
    z = np.load(SRC, allow_pickle=False)
    cells = z["cells"].tolist()
    parts = split_cells(cells, "real")
    allowed = parts["H0"] + parts["D1"] + parts["D2"] + parts["D3"]
    ix = [cells.index(c) for c in allowed]
    withheld = sorted(parts["A"] + parts["T"])
    arrs = {k: z[k][:, ix] for k in ("A", "Aref", "amin", "amax")}
    DST.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DST, cells=np.array(allowed), pair_i=z["pair_i"], pair_j=z["pair_j"], drug_module=z["drug_module"], drugs=z["drugs"], **arrs,
                        splits=np.array(json.dumps({k: parts[k] for k in ("H0", "D1", "D2", "D3")})),
                        withheld_names_sha256=np.array(hashlib.sha256("|".join(withheld).encode()).hexdigest()))
    return {"allowed_cells": len(allowed), "withheld_cells": len(withheld), "withheld_names_sha256": hashlib.sha256("|".join(withheld).encode()).hexdigest()}


def load_restricted():
    z = np.load(DST, allow_pickle=False)
    drugs = tuple(z["drugs"].tolist())
    static = Static(drugs, z["pair_i"], z["pair_j"], z["drug_module"], tuple(f"{drugs[i]}+{drugs[j]}" for i, j in zip(z["pair_i"], z["pair_j"])))
    cells = tuple(z["cells"].tolist())
    w = World(static, cells, z["Aref"], z["amin"], z["amax"], z["A"], label="oneil_released_only")
    sp = json.loads(str(z["splits"]))
    sched = {"H0": sp["H0"], "batches": [sp["D1"], sp["D2"], sp["D3"]], "A_old": [], "A_new": []}
    return {"world": w, "schedule": sched, "meta": {"kind": "real_dev", "n_cells": len(cells)}}


if __name__ == "__main__" and len(sys.argv) == 1:
    print(json.dumps(write_restricted()))
    s = load_restricted()
    st = s["world"].static
    print(st.n, len(st.classes), np.isnan(s["world"].history(s["world"].cells).R).sum())


def run_replay(out_dir: Path):
    """Development replay (one world, 9 task backgrounds D1-D3 after an H0 release of 9). Descriptive only."""
    import gzip

    import iv_run

    s = load_restricted()
    iv_run.run_stream("real", 0, False, out_dir, {}, stream=s, sid_override="real_dev")
    with gzip.open(out_dir / "streams" / "real_dev.json.gz", "rt", encoding="utf-8") as f:
        d = json.load(f)
    acc = {}
    for r in d["rows"]:
        if r["role"] == "task":
            acc.setdefault((r["contract"], r["arm"]), []).append((r["gen"], r["cell"], r["utility"], r["oracle"]))
    table = {}
    for (c, a), v in sorted(acc.items()):
        table.setdefault(c, {})[a] = {"mean_utility_all_9_tasks": float(np.mean([x[2] for x in v])), "mean_utility_batches_2_3": float(np.mean([x[2] for x in v if x[0] >= 2])),
                                      "per_task": {x[1]: round(x[2], 4) for x in v}}
    oracle = float(np.mean([x[3] for x in acc[("E", "prior")]]))
    paired = {}
    for comp in ("prior", "direct", "lat_aopt", "gbm_ucb", "broadcap_bald", "rst_kg", "fix_kg"):
        if ("E", comp) in acc:
            diffs = [a[2] - b[2] for a, b in zip(acc[("E", "inh_kg")], acc[("E", comp)])]
            paired[comp] = {"mean_gain_inh_kg_minus_comp": float(np.mean(diffs)), "tasks_positive": int(sum(x > 0 for x in diffs)), "n_tasks": len(diffs)}
    out = {"label": "DEVELOPMENT_REPLAY_EXPOSED", "cells_used": 18, "withheld_backgrounds_touched": False, "streams": 1, "inference": "none (one world; tasks are not independent)",
           "oracle_E_mean": oracle, "utilities": table, "paired_E_inh_kg_vs": paired,
           "generation_records": {a: [{"gen": g["gen"], "deployed_after": g["deployed_after"], "n_candidates": g["n_candidates"], "statuses": [c.get("status") for c in g["candidates"] if c.get("fit")]} for g in d["generation_records"][a]] for a in ("inh_kg", "rst_kg")},
           "resources": d["resources"], "note": "Same cells the predecessors analysed. Not independent evidence; not a test of measured drug-discovery utility."}
    return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "replay":
    out = run_replay(Path(sys.argv[2]))
    Path(sys.argv[3]).write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print("wrote", sys.argv[3])
