"""Ranking quality of the world model's score under different settings (development, open tier).

For each development query of a referenced class, the 212 referenced classes are ranked by the
profile NLL (the relative score orders hypotheses identically) on (a) all available options and
(b) four options drawn at random (seeded per drug). Reports the true class's median rank, top-5
and top-20 rates, overall and for drugs with activity < 0.75 and >= 0.75. Calibration is not
involved: this measures how much ordering information the world model has, which bounds the set
sizes any calibrated rule can reach.
Usage: python dev_scorers.py '<json list of config dicts>'   (writes development/scorers.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import dev_ceiling as DC
import dev_programs as DP
import falsify as F
import study as S

HERE = Path(__file__).resolve().parent


def ranks(data: dict, cfg: S.Config, n_rand: int = 4) -> dict:
    b = S.build(data, cfg)
    fz = S.falsifier(b)
    lib = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    names = [b.models[i].name for i in lib]
    pos = {n: i for i, n in enumerate(names)}
    moa, role = data["moa"], data["role"]
    act = DP.drug_activity(data["x"], role == "reference")
    q = [i for i in np.where(role == "development")[0] if moa[i] in pos]
    out = {"full": [], "rand4": [], "act": []}
    for qi in q:
        avail = S.available(data, qi)
        rng = np.random.default_rng(20261010 + qi)
        sub = sorted(rng.choice(avail, size=min(n_rand, len(avail)), replace=False).tolist())
        for key, opts in (("full", avail), ("rand4", sub)):
            Q, bb, A = fz.stats(b.Z_open[qi], opts, lib)
            nll, _ = F.score_from_stats(Q, bb, A, fz.noise.tau2, len(opts))
            out[key].append(DC.rank_of(nll, pos[moa[qi]], False))
        out["act"].append(float(act[qi]))
    return out


def summary(r: dict) -> dict:
    a = np.array(r["act"])
    res = {}
    for key in ("full", "rand4"):
        x = np.array(r[key])
        for lab, m in (("all", np.ones(len(a), bool)), ("weak", a < 0.75), ("active", a >= 0.75)):
            res[f"{key}/{lab}"] = {"n": int(m.sum()), "median": float(np.median(x[m])), "top5": float(np.mean(x[m] <= 5)),
                                   "top20": float(np.mean(x[m] <= 20)), "p90_rank": float(np.percentile(x[m], 90))}
    return res


def main() -> None:
    configs = json.loads(sys.argv[1])
    data = S.load_tier("open")
    out_path = HERE / "development" / "scorers.json"
    res = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    for c in configs:
        key = json.dumps(c, sort_keys=True)
        r = ranks(data, S.Config(**c))
        res[key] = summary(r)
        out_path.write_text(json.dumps(res, indent=1), encoding="utf-8")
        s = res[key]
        print(f"{key:55s} " + "  ".join(f"{k}: med={v['median']:.0f} t5={v['top5']:.2f} t20={v['top20']:.2f} p90={v['p90_rank']:.0f}"
                                        for k, v in s.items() if k.endswith(("all", "active"))), flush=True)


if __name__ == "__main__":
    main()
