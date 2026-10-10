"""Development runs for block M (open tier only: reference fits, development drugs scored).

Usage: python dev_run.py <name> [json config overrides] [--budget B] [--policies a,b] [--limit N]
Writes development/<name>.json with the config, summaries overall and by stratum, and per-episode
rows. Strata are fixed before scoring: whether the query's class has reference drugs
("referenced") or exists only as an agent hypothesis ("knowledge_only").
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

import episodes as EP
import study as S

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("config", nargs="?", default="{}")
    ap.add_argument("--budget", type=int, default=4)
    ap.add_argument("--policies", default="fixed,random,magnitude,falsify")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--hyp", default="all", choices=["all", "library"])  # library = closed world: referenced classes only
    a = ap.parse_args()
    out = HERE / "development" / f"{a.name}.json"
    out.parent.mkdir(exist_ok=True)
    t0 = time.time()
    data = S.load_tier("open")
    cfg = S.Config(**json.loads(a.config))
    b = S.build(data, cfg)
    q = np.where(data["role"] == "development")[0]
    if a.limit:
        q = q[: a.limit]
    referenced = {m.name for m in b.models if m.kind != "knowledge"}
    lib = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    hf = (lambda qi, true: lib) if a.hyp == "library" else None
    rows = EP.run_queries(b, data, q, a.policies.split(","), a.budget, hyp_filter=hf)
    strata = {"all": rows,
              "referenced": [r for r in rows if r["moa"] in referenced],
              "knowledge_only": [r for r in rows if r["moa"] not in referenced]}
    res = {"name": a.name, "config": asdict(cfg), "hyp": a.hyp, "budget": a.budget, "n_queries": int(len(q)),
           "n_hypotheses": len(b.models), "slopes": b.slopes,
           "buckets": {k: int((np.array([m.bucket for m in b.models]) == k).sum()) for k in ("K", "1", "2-3", "4+")},
           "option_order": [data["options"][o] for o in b.option_order],
           "summary": {k: EP.summarise(v, a.budget) for k, v in strata.items() if v},
           "n_strata": {k: len(v) // max(1, len(a.policies.split(","))) for k, v in strata.items()},
           "seconds": round(time.time() - t0, 1), "rows": rows}
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in res["summary"].items():
        for pol, per in v.items():
            last = per[a.budget]
            print(f"{k:15s} {pol:10s} B={a.budget} cov={last['coverage']:.3f} set={last['mean_set']:.1f} "
                  f"(B1 cov={per[1]['coverage']:.3f} set={per[1]['mean_set']:.1f}) cred_cov={last['cred_coverage']:.3f} cred_set={last['cred_mean_set']:.1f}")
    print("seconds", res["seconds"])


if __name__ == "__main__":
    main()
