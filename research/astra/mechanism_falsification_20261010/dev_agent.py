"""Development runs of the LLM arms on a seeded, stratified subset of development drugs.

Usage: python dev_agent.py <name> '<config json>' --n-ref 50 --n-know 30 --budget 3 --modes agent,interface,design
Writes development/<name>.json. The subset is drawn with seed 20261010 from the development drugs of
each stratum (referenced, knowledge_only) after sorting by name; it does not look at any value.
The agent sees only top genes and strength per bought observation, never the drug name.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import numpy as np

import agent_arms as AA
import study as S

HERE = Path(__file__).resolve().parent


def noise_hint(data: dict) -> str:
    """Reference-only distribution of signature strength (L2 norm over 978 genes)."""
    ref = data["role"] == "reference"
    norms = np.linalg.norm(data["x"][ref], axis=2).ravel()
    norms = norms[np.isfinite(norms)]
    q = np.percentile(norms, [25, 50, 75, 90])
    return (f"across reference drugs the strength has quartiles {q[0]:.0f}, {q[1]:.0f}, {q[2]:.0f} "
            f"and 90th percentile {q[3]:.0f}; many drugs barely move these cells")


def subset(data: dict, referenced: set[str], n_ref: int, n_know: int, seed: int = 20261010) -> np.ndarray:
    dev = np.where(data["role"] == "development")[0]
    dev = dev[np.argsort(data["drug"][dev])]
    r = [i for i in dev if data["moa"][i] in referenced]
    k = [i for i in dev if data["moa"][i] not in referenced]
    rng = np.random.default_rng(seed)
    pick = list(rng.choice(r, size=min(n_ref, len(r)), replace=False)) + list(rng.choice(k, size=min(n_know, len(k)), replace=False))
    return np.array(sorted(pick))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("config", nargs="?", default="{}")
    ap.add_argument("--n-ref", type=int, default=50)
    ap.add_argument("--n-know", type=int, default=30)
    ap.add_argument("--budget", type=int, default=3)
    ap.add_argument("--modes", default="agent,interface")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    out = HERE / "development" / f"{a.name}.json"
    t0 = time.time()
    data = S.load_tier("open")
    cfg = S.Config(**json.loads(a.config))
    b = S.build(data, cfg)
    fz = S.falsifier(b)
    referenced = {m.name for m in b.models if m.kind != "knowledge"}
    q = subset(data, referenced, a.n_ref, a.n_know)
    arms = AA.AgentArms(sorted(m.name for m in b.models), data["genes"], data["options"], noise_hint(data))
    rows = []
    lock = threading.Lock()

    def one(job):
        qi, mode = job
        avail = S.available(data, qi)
        zg = {o: data["x"][qi, o] for o in avail}
        rec = arms.episode(str(qi), zg, avail, a.budget, mode, fz=fz, z_proj=b.Z_open[qi])
        row = {"drug": str(data["drug"][qi]), "moa": str(data["moa"][qi]), "mode": mode,
               "stratum": "referenced" if data["moa"][qi] in referenced else "knowledge_only", **rec}
        with lock:
            rows.append(row)
            out.write_text(json.dumps({"name": a.name, "config": asdict(cfg), "rows": rows}, indent=1), encoding="utf-8")

    jobs = [(qi, mode) for qi in q for mode in a.modes.split(",")]
    with ThreadPoolExecutor(a.workers) as pool:
        list(pool.map(one, jobs))
    rows.sort(key=lambda r: (r["drug"], r["mode"]))
    summ = {}
    for mode in a.modes.split(","):
        for key in ("agent_set", "falsifier_set"):  # falsifier_set under an agent-chosen design = agent-design arm
          for stratum in ("all", "referenced", "knowledge_only"):
            rs = [r for r in rows if r["mode"] == mode and (stratum == "all" or r["stratum"] == stratum)]
            if not rs:
                continue
            per = {}
            for k in range(1, a.budget + 1):
                sets = [r["steps"][k - 1].get(key) for r in rs if len(r["steps"]) >= k]
                cov = [r["moa"] in (s or []) for r, s in zip(rs, sets)]
                size = [len(s) if s is not None else len(b.models) for s in sets]
                per[k] = {"n": len(sets), "coverage": float(np.mean(cov)), "mean_set": float(np.mean(size)),
                          "stated_none": int(sum(s is None for s in sets))}
            summ[f"{mode}/{key}/{stratum}"] = per
    res = {"name": a.name, "config": asdict(cfg), "n_queries": int(len(q)), "budget": a.budget,
           "summary": summ, "ledger_total_usd": round(arms.ledger.total_usd, 4), "seconds": round(time.time() - t0, 1),
           "rows": rows}
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in summ.items():
        print(k, {b_: (round(x["coverage"], 3), round(x["mean_set"], 1)) for b_, x in v.items()})
    print("ledger", res["ledger_total_usd"], "seconds", res["seconds"])


if __name__ == "__main__":
    main()
