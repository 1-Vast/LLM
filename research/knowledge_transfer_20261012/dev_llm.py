"""Development step 6: prototype the LLM arms on a few phase-1 campaigns at W = N (deepseek-flash).

Usage: python dev_llm.py [n_campaigns]  (fold 0; responses cached in cache/llm_dev_cache.jsonl)
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import campaign as C
import llm_arms as LA
from dev_campaign import setup
from dev_common import CACHE

COMPARE = ("vc_only", "sparse_hub", "activity_greedy", "maestro")


def main(n_campaigns: int = 2, fold: int = 0):
    t0 = time.time()
    campaign, n_sub, _ = setup(fold)
    agent = LA.Agent(CACHE / "llm_dev_cache.jsonl", CACHE / "llm_dev_spend.json", ceiling_usd=3.0)
    camps = [campaign(s) for s in range(min(n_campaigns, n_sub))]
    jobs = [(c, meta, arm) for c, meta in camps for arm in LA.LLM_ARMS]

    def run(job):
        c, meta, arm = job
        W = len(c.library)
        r = LA.run_llm_arm(c, arm, W, meta, agent)
        r.update({"campaign": c.cid, "budget": 1.0})
        print(f"  {c.cid} {arm} utility {r['utility']:.3f} errors {r['errors']} fallback {r['fallback_cells']} {time.time()-t0:.0f}s", flush=True)
        return r

    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(run, jobs))
    for c, meta in camps:
        for arm in COMPARE:
            r = C.run_arm(c, arm, len(c.library))
            r.update({"campaign": c.cid, "budget": 1.0})
            rows.append(r)
    (CACHE / "dev_llm.json").write_text(json.dumps(rows, indent=0, default=str), encoding="utf-8")
    import pandas as pd
    df = pd.DataFrame(rows)
    print(df.pivot_table(index="arm", columns="campaign", values=["utility", "utility_vcfill", "utility_naivefill"]).round(3).to_string())
    print("spend", round(agent.ledger.session_total_usd, 4), "calls", len(agent.ledger.entries))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
