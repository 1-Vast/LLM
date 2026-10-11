"""Development pilot (exploratory): does the agent add to the virtual cell on development killers?

Population: development drugs killing at least 5% of lines (log fold change < -1). Regime: novel
class (the drug's own class is removed from every pool and from the agent's vocabulary). Arms: the
four agent arms in ``scientist.ARMS`` and the non-LLM predictors in ``predictors``. A prediction that
abstains scores 0 selective r (no selective information).

Usage: python dev_pilot.py [regime] [max_drugs]
Output: development/pilot_<regime>.json and development/pilot_<regime>_rows.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import predictors as PR  # noqa: E402
import scientist as SC  # noqa: E402

sys.path.insert(0, str(PR.BLOCK_M))
import intervals as IV  # noqa: E402

KILL = (-1.0, 0.05)
SEED = 20261011


def killers(world, role):
    return [i for i in np.where(world.role == role)[0] if np.nanmean(world.P[i] < KILL[0]) >= KILL[1]]


def predictions(world, recs, i, regime):
    b = world.baselines(i, regime)
    out = {k: v for k, v in b.items()}
    c = {arm: recs[arm]["claims"] for arm in recs}
    for arm in ("route_lit", "route_nolit", "masked_nolit"):
        if arm in c:
            out[f"R_{arm}"] = world.compile_routes(c[arm]["routes"], i, regime)
    if "adjudicate_lit" in c:
        offered = world.neighbours(i, regime)
        nb = world.compile_neighbours(c["adjudicate_lit"]["keep_neighbours"], i, regime, offered)
        rt = world.compile_routes(c["adjudicate_lit"]["routes"], i, regime)
        parts = [p for p in (nb, rt) if p is not None]
        out["ADJ"] = np.mean(parts, axis=0) if parts else None
        out["ADJ_neighbours_only"] = nb
        out["BM_adj"] = world.compile_biomarkers(c["adjudicate_lit"]["biomarkers"])
        out["ADJ+BM"] = PR.combine([out["ADJ"], out["BM_adj"]], [1.0, 0.5]) if out["ADJ"] is not None else None
    if "route_lit" in c:
        out["BM"] = world.compile_biomarkers(c["route_lit"]["biomarkers"])
        out["L+R_lit"] = PR.combine([b["L"], out.get("R_route_lit")])
        out["R_lit+BM"] = PR.combine([out.get("R_route_lit"), out["BM"]], [1.0, 0.5]) if out.get("R_route_lit") is not None else None
        out["L+BM"] = PR.combine([b["L"], out["BM"]], [1.0, 0.5])
    return out


def score_rows(world, idx, regime, all_recs):
    rows = []
    for i in idx:
        recs = {arm: all_recs[(arm, int(i))] for arm in SC.ARMS if (arm, int(i)) in all_recs}
        preds = predictions(world, recs, i, regime)
        row = {"drug": world.drug[i], "moa": world.moa[i]}
        for k, p in preds.items():
            r = PR.selective_r(p, world.P[i], world.G) if p is not None else np.nan
            row[k] = 0.0 if (p is None or not np.isfinite(r)) and k != "G" else r
        row["ceiling_secondary"] = PR.selective_r(world.S2[i], world.P[i], world.G) if np.isfinite(world.S2[i]).any() else np.nan
        for arm, rec in recs.items():
            cl = rec["claims"]
            row[f"{arm}:n_routes"] = len(cl["routes"])
            row[f"{arm}:n_biomarkers"] = len(cl["biomarkers"])
            row[f"{arm}:killing"] = cl["expected_killing"]
            if arm == "adjudicate_lit":
                row["adjudicate_lit:n_keep"] = len(cl["keep_neighbours"])
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(df):
    res = {"n": int(len(df))}
    cl = df["moa"].to_numpy()
    for col in df.columns:
        if col in ("drug", "moa") or ":" in col:
            continue
        v = df[col].to_numpy(float)
        ok = np.isfinite(v)
        if ok.sum() >= 5:
            est, lo, hi = IV.cluster_bootstrap(v[ok], cl[ok], n_boot=1000, seed=SEED)
            res[col] = [round(est, 4), round(lo, 4), round(hi, 4), int(ok.sum())]
    pairs = [("ADJ", "L"), ("ADJ", "E"), ("ADJ_neighbours_only", "L"), ("L+R_lit", "L"), ("R_route_lit", "T"),
             ("R_route_lit", "C"), ("R_route_lit", "L"), ("R_route_lit", "R_route_nolit"), ("R_route_nolit", "R_masked_nolit"),
             ("BM", "B0"), ("R_lit+BM", "R_route_lit"), ("ADJ+BM", "ADJ"), ("L+BM", "L"), ("L", "T"), ("L", "C"), ("E", "L")]
    res["paired"] = {}
    for a, b in pairs:
        if a in df and b in df:
            x, y = df[a].to_numpy(float), df[b].to_numpy(float)
            ok = np.isfinite(x) & np.isfinite(y)
            if ok.sum() >= 5:
                r = IV.paired_difference(x[ok], y[ok], cl[ok], n_boot=1000, seed=SEED)
                res["paired"][f"{a} - {b}"] = [round(r["mean_difference"], 4), round(r["ci95"][0], 4), round(r["ci95"][1], 4), r["n"]]
    return res


def main(regime: str = "novel_class", max_drugs: int | None = None) -> dict:
    world = PR.load_world("open")
    idx = killers(world, "development")[:max_drugs]
    agent = SC.Agent(world)
    tasks = [(arm, regime, int(i)) for arm in SC.ARMS for i in idx]
    recs = agent.run(tasks)
    all_recs = {(r["arm"], int(np.where(world.drug == r["drug"])[0][0])): r for r in recs}
    df = score_rows(world, idx, regime, all_recs)
    res = summarise(df)
    res["regime"] = regime
    res["llm_status"] = {arm: {s: sum(1 for r in recs if r["arm"] == arm and r["status"] == s) for s in ("ok", "failed")} for arm in SC.ARMS}
    res["ledger_total_usd"] = round(agent.ledger.total_usd, 4)
    out = HERE / "development"
    out.mkdir(exist_ok=True)
    (out / f"pilot_{regime}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    df.to_csv(out / f"pilot_{regime}_rows.csv", index=False)
    return res


if __name__ == "__main__":
    reg = sys.argv[1] if len(sys.argv) > 1 else "novel_class"
    mx = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(main(reg, mx), indent=1))
