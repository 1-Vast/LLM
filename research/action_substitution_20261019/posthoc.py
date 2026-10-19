"""POST HOC (not in PROTOCOL_P2): is the same-target sibling a better reference than pooled or functional references?

Reads the saved phase-2 unit tables; cluster bootstrap over held-out implementations. Writes POSTHOC.json (overwrites).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(1)
PAIRS = [("B0", "B1"), ("B0", "B5"), ("B0", "B3"), ("B1", "B5"), ("B2", "B4"), ("M", "B5")]


def main():
    out = {}
    for ep in ("SYNERGY_DELTA_AUC", "SYNERGY_OBS_AUC"):
        u = pd.read_csv(HERE / f"lofo_units_{ep}.csv")
        groups = {x: g for x, g in u.groupby("X")}
        names = list(groups)
        res = {}
        for a, b in PAIRS:
            def diff(g):
                return float(np.mean((g["d_" + a] - g.obs) ** 2) - np.mean((g["d_" + b] - g.obs) ** 2))
            bs = [diff(pd.concat([groups[names[i]] for i in RNG.choice(len(names), len(names))])) for _ in range(2000)]
            res[f"{a}_minus_{b}"] = dict(point=diff(u), ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
        wins = {m: int(sum(np.mean((g["d_" + m] - g.obs) ** 2) <= np.mean((g["d_B0"] - g.obs) ** 2) for g in groups.values()))
                for m in ("B1", "B5", "M")}
        res["implementations_where_method_beats_or_ties_B0"] = dict(of=len(names), **wins)
        out[ep] = res
        print(ep, json.dumps(res, indent=1))
    (HERE / "POSTHOC.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
