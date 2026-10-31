"""Post hoc sensitivity raised by the verifier: add BRD-K57796080 (3,5-DHPG-(S)), dropped by the pre-freeze
one-ID-per-InChIKey-block de-duplication, to the 24Q2 query set. Reads exactly one more sealed matrix row.

Usage: python dhpg_sensitivity.py MATRIX_CSV COMPOUND_LIST RUN_DIR DATA_DIR OUT_JSON
Its L1000 signatures are those of its block, shared with query BRD-A20589515, so its predictions are that
query's predictions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/MAESTRO/src")
from virtual_cell.transcriptional_transfer import residualise, selective_r  # noqa: E402

NEW, TWIN = "BRD-K57796080", "BRD-A20589515"
ARMS = ["B0", "B1", "B2", "C1", "L"]


def hit_precision(p, y, g, sign=-1.0, frac=0.10, min_lines=50):
    a, b = residualise(p, g), residualise(y, g)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < min_lines or np.std(a[ok]) < 1e-10:
        return float("nan")
    m = max(1, int(round(frac * ok.sum())))
    ta = set(np.argsort(-(sign * a[ok]), kind="stable")[:m])
    tb = set(np.argsort(-(sign * b[ok]), kind="stable")[:m])
    return len(ta & tb) / m


def main(matrix: Path, listing: Path, run: Path, data: Path, out: Path) -> None:
    cl = pd.read_csv(listing, dtype=str)
    ids = set(cl.loc[(cl.screen == "REP.1M") & cl.IDs.str.contains(NEW, regex=False), "IDs"])
    header = pd.read_csv(matrix, nrows=0).columns.tolist()
    rows = pd.concat(chunk[chunk[header[0]].astype(str).isin(ids)] for chunk in pd.read_csv(matrix, chunksize=500))
    p = np.load(run / "predictions_prism24q2.npz", allow_pickle=True)
    lines = list(p["line"])
    y = rows[lines].astype(float).mean(axis=0).to_numpy()
    active = bool(np.mean(np.where(np.isfinite(y), y <= -1.0, False)) >= 0.05)  # missing counts as not killed
    i = list(p["key"]).index(TWIN)
    g = p["generic"][i]
    r_new = {a: selective_r(p[f"pred_{a}"][i], y, g, min_lines=50) for a in ARMS}
    h_new = {a: hit_precision(p[f"pred_{a}"][i], y, g) for a in ARMS}
    m = pd.read_csv(run / "metrics_prism24q2.csv")
    act = m.active.to_numpy(bool)
    res = {"compound": NEW, "rows_read": int(len(rows)), "ids": sorted(ids), "n_killed_lines": int(np.nansum(y <= -1.0)),
           "n_lines_with_value": int(np.isfinite(y).sum()), "active": active,
           "selective_r": {a: (None if np.isnan(v) else float(v)) for a, v in r_new.items()},
           "hit_precision": {a: (None if np.isnan(v) else float(v)) for a, v in h_new.items()}}
    pop = "actives" if active else "all compounds"
    keep = act if active else np.ones(len(m), bool)
    for name, (a, b) in {"H1": ("C1", "B0"), "H3": ("C1", "B1")}.items():
        xa = np.append(m[f"r_{a}"].to_numpy()[keep], np.nan_to_num(r_new[a]))
        xb = np.append(m[f"r_{b}"].to_numpy()[keep], np.nan_to_num(r_new[b]))
        t = stats.ttest_rel(xa, xb, alternative="greater")
        res[f"{name}_with_compound_{pop.replace(' ', '_')}"] = {"mean_difference": float((xa - xb).mean()),
                                                                 "p_one_sided": float(t.pvalue), "n": int(len(xa))}
    out.write_bytes((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:6]))
