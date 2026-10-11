"""Development (exploratory): can the agent tell when to trust the virtual cell? All 281 development drugs.

Runs the flash ``adjudicate_lit`` and ``route_lit`` arms (novel-class regime) for development drugs
that lack them, then scores trust rankings of the virtual cell's predictions (``trust.py``).
Utility per drug: selective r of the transcriptional-transfer prediction L.

Output: development/trust_dev.json and development/trust_dev_rows.csv.
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
import trust as TR  # noqa: E402

REGIME = "novel_class"


def build(world, idx, regime, out_dir=SC.OUT):
    rows = []
    for i in idx:
        b = world.baselines(i, regime)
        u = PR.selective_r(b["L"], world.P[i], world.G) if b["L"] is not None else np.nan
        s = TR.scores_for(world, i, regime, TR.load_claims(out_dir, "adjudicate_lit", regime, str(world.drug[i]), SC.slug),
                          TR.load_claims(out_dir, "route_lit", regime, str(world.drug[i]), SC.slug))
        rows.append({"drug": world.drug[i], "moa": world.moa[i], "utility": 0.0 if not np.isfinite(u) else u,
                     "killer": bool(np.nanmean(world.P[i] < -1) >= 0.05), **s})
    return TR.composite(pd.DataFrame(rows))


def summarise(df):
    res = {"n": int(len(df)), "n_killers": int(df["killer"].sum()), "mean_utility": float(df["utility"].mean()),
           "oracle": TR.evaluate(df["utility"], df["utility"]), "trust": {}, "paired_aucc": {}, "paired_top25": {}}
    for c in ("top_sim", "mean5_sim", "moa_agree5", "l1000_norm", "vc", "keep", "kill", "kill_prior", "agent", "vc+agent", "vc+kill_prior"):
        res["trust"][c] = {k: round(v, 4) for k, v in TR.evaluate(TR.rank01(df[c]), df["utility"]).items()}
    cl = df["moa"].to_numpy()
    for a, b in (("vc+agent", "vc"), ("agent", "vc"), ("vc+kill_prior", "vc"), ("keep", "top_sim")):
        res["paired_aucc"][f"{a} - {b}"] = [round(x, 4) for x in TR.bootstrap_diff(df, a, b, cl)]
        res["paired_top25"][f"{a} - {b}"] = [round(x, 4) for x in TR.bootstrap_diff(df, a, b, cl, metric="top25")]
    return res


def main():
    world = PR.load_world("open")
    idx = [int(i) for i in np.where(world.role == "development")[0]]
    agent = SC.Agent(world)
    agent.run([(arm, REGIME, i) for arm in ("adjudicate_lit", "route_lit") for i in idx])
    df = build(world, idx, REGIME)
    res = summarise(df)
    res["ledger_total_usd"] = round(agent.ledger.total_usd, 4)
    (HERE / "development" / "trust_dev.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    df.to_csv(HERE / "development" / "trust_dev_rows.csv", index=False)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
