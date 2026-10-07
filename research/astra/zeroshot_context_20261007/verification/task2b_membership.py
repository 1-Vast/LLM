"""Workstream C, task 2 supplement: group membership and QC flags of the plan rows.

Task 2 shows the stored expression rows equal the pinned remote bytes. This supplement checks
the other link: that every plan row really has the plan's (label, plate) and full-QC flag.
  1. Local, all rows: for the five held-out files, every plan row's label / plate / full flag is
     compared with categories[codes] from the cached obs codes (C/census/<file>.npz) and the
     census categories.
  2. Remote, complete: for c31.h5ad (evaluation line HOP62) the full drugname_drugconc, plate and
     pass_filter code arrays are re-fetched from the pinned revision and compared byte-for-byte
     with the cache and with the census codes_sha256.
  3. Remote, sampled: for the other four held-out files, 6 random plan windows per file; the code
     bytes at those rows are re-fetched and compared with the cache.
Shares the byte budget with task 2 (55 MB including task 2's 19.6 MB). Writes
task2b_membership.json and appends to task2b_requests.jsonl.
"""
import hashlib
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import task2_raw_bytes as t2  # the verifier's own fetch helper (budget-checked)

S, C, V = t2.S, t2.C, t2.V
SEED = 20261007
COLS = ("drugname_drugconc", "plate", "pass_filter")


def main():
    with open(os.path.join(V, "task2_raw_bytes.json"), encoding="utf-8") as fh:
        prior = json.load(fh)["network"]["bytes"]
    t2.state["bytes"] = prior  # carry task 2's usage into the shared budget
    split = t2.load_json(os.path.join(S, "SPLIT.json"))
    heldout = sorted(split["files"].values(), key=lambda s: int(s[1:-5]))
    rng = random.Random(SEED)
    out = {"local_all_rows": {}, "remote_complete": {}, "remote_sampled": {}}
    for f in heldout:
        plan = t2.load_json(os.path.join(C, "extract", "plans", f + ".plan.json"))
        cen = t2.load_json(os.path.join(S, "census", f + ".json"))
        codes = np.load(os.path.join(C, "census", f + ".npz"))
        cat = {k: np.asarray(cen["categories"][k]) for k in COLS}
        sha_ok = {k: hashlib.sha256(np.ascontiguousarray(codes[k]).tobytes()).hexdigest() == cen["codes_sha256"][k]
                  for k in COLS}
        bad_label = bad_plate = bad_full = n = 0
        for g in plan["groups"]:
            r = np.asarray(g["rows"], dtype=np.int64)
            n += len(r)
            bad_label += int((cat["drugname_drugconc"][codes["drugname_drugconc"][r]] != g["label"]).sum())
            bad_plate += int((cat["plate"][codes["plate"][r]] != g["plate"]).sum())
            bad_full += int(((cat["pass_filter"][codes["pass_filter"][r]] == "full") != np.asarray(g["full"], bool)).sum())
        out["local_all_rows"][f] = {"rows": n, "label_mismatch": bad_label, "plate_mismatch": bad_plate,
                                    "full_flag_mismatch": bad_full, "cache_sha256_equals_census": sha_ok,
                                    "pass_filter_categories": cen["categories"]["pass_filter"]}
        lay = cen["code_layouts"]
        if f == "c31.h5ad":
            rc = {}
            for k in COLS:
                L = lay[k]
                data = t2.fetch(f, L["offset"], L["offset"] + L["storage_bytes"] - 1)
                rc[k] = {"bytes": len(data),
                         "sha256_equals_census": hashlib.sha256(data).hexdigest() == cen["codes_sha256"][k],
                         "equals_cache": data == np.ascontiguousarray(codes[k]).tobytes()}
            out["remote_complete"][f] = rc
        else:
            groups = rng.sample(plan["groups"], 6)
            recs = []
            for g in groups:
                rows = g["rows"]
                run = [rows[0]]
                for r in rows[1:]:
                    if r == run[-1] + 1 and len(run) < 64:
                        run.append(r)
                    else:
                        break
                a, b = run[0], run[-1]
                rec = {"group": g["group"], "control": g["control"], "rows": [a, b]}
                for k in COLS:
                    L = lay[k]
                    item = np.dtype(L["dtype"]).itemsize
                    data = t2.fetch(f, L["offset"] + a * item, L["offset"] + (b + 1) * item - 1)
                    rec[k + "_equals_cache"] = data == np.ascontiguousarray(codes[k][a:b + 1]).tobytes()
                recs.append(rec)
            out["remote_sampled"][f] = recs
        print(f, out["local_all_rows"][f], flush=True)
    loc_ok = all(v["label_mismatch"] == 0 and v["plate_mismatch"] == 0 and v["full_flag_mismatch"] == 0
                 and all(v["cache_sha256_equals_census"].values()) for v in out["local_all_rows"].values())
    rc_ok = all(x["sha256_equals_census"] and x["equals_cache"] for v in out["remote_complete"].values() for x in v.values())
    rs_ok = all(all(r[k + "_equals_cache"] for k in COLS) for v in out["remote_sampled"].values() for r in v)
    out["network_cumulative_with_task2"] = {"requests_this_script": len(t2.req_log), "bytes_cumulative": t2.state["bytes"],
                                            "bytes_this_script": t2.state["bytes"] - prior, "budget": t2.BUDGET}
    out["pass"] = bool(loc_ok and rc_ok and rs_ok)
    with open(os.path.join(V, "task2b_membership.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(V, "task2b_requests.jsonl"), "w", encoding="utf-8") as fh:
        for r in t2.req_log:
            fh.write(json.dumps(r) + "\n")
    print(json.dumps({"pass": out["pass"], "remote_complete": out["remote_complete"],
                      "network": out["network_cumulative_with_task2"]}, indent=1))


if __name__ == "__main__":
    main()
