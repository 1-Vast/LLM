"""Workstream C, task 2: raw-byte integrity by independent HTTPS range re-fetch.

Selects ledger records at random (fixed seed) from S/extract/ledgers: for each of the five
held-out files 3 treated-group records and 1 control-group record; for four randomly chosen
training files 2 treated-group records and 1 control-group record. Every span is re-fetched
from the pinned Hugging Face resolve URL (302 followed, Range header), its SHA-256 compared
with the ledger, and:
  * held-out records: the bytes compared with the rows stored in rows.npy (plan -> slot map;
    first_row = (start - X_hvg offset from census) / 8000);
  * training treated-group records that cover a whole group: n, mean and var (ddof=1) over the
    plan's full-QC rows recomputed from the bytes and compared with treated_summaries.npz;
  * training control-group records: bytes compared with rows.npy.
Extra: c39.h5ad was read from a local copy (no ledger); one control window is fetched from the
pinned remote and compared with rows.npy and with the local copy.
Hard byte budget 55 MB. Signed CDN URLs are never written. Writes task2_raw_bytes.json and
task2_requests.jsonl.
"""
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone

import numpy as np
import requests

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
C = r"D:\MAESTRO\data\external\tahoe_zeroshot_20261007"
V = os.path.join(S, "verification")
REPO = "arcinstitute/State-Tahoe-Filtered"
REV = "fdf87abece385feea6fa5e9944ab46e173b6af50"
BUDGET = 55 * 1000 * 1000
SEED = 7102026
ROW = 8000
LOCAL_C39 = r"D:\MAESTRO\data\external\arc_state\tahoe_metadata_source\c39.h5ad"

session = requests.Session()
session.headers["User-Agent"] = "MAESTRO-verifier-workstream-C/1"
state = {"bytes": 0, "requests": 0}
req_log = []


def resolve(name):
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REV}/{name}"
    r = session.head(url, allow_redirects=False, timeout=60)
    if r.status_code not in (301, 302, 303, 307, 308):
        raise RuntimeError("resolve status %d" % r.status_code)
    return r.headers["location"]


_loc = {}


def fetch(name, start, end):
    n = end - start + 1
    if state["bytes"] + n > BUDGET:
        raise RuntimeError("byte budget would be exceeded")
    err, data = None, None
    for attempt in range(4):
        try:
            if name not in _loc or attempt > 0:
                _loc[name] = resolve(name)
            r = session.get(_loc[name], headers={"Range": f"bytes={start}-{end}"}, timeout=180)
            if r.status_code != 206:
                raise RuntimeError("status %d" % r.status_code)
            span = r.headers.get("Content-Range", "").split()[-1].split("/")[0]
            if span != f"{start}-{end}":
                raise RuntimeError("span mismatch " + span)
            data = r.content
            if len(data) != n:
                raise RuntimeError("short read")
            err = None
            break
        except Exception as exc:
            err = type(exc).__name__ + ":" + str(exc).split("?")[0][:100]
            time.sleep(2 * (attempt + 1))
    state["requests"] += 1
    state["bytes"] += len(data) if data is not None else 0
    req_log.append({"file": name, "start": start, "end": end, "bytes": len(data) if data else 0,
                    "error": err, "utc": datetime.now(timezone.utc).isoformat(),
                    "sha256": hashlib.sha256(data).hexdigest() if data else None})
    if data is None:
        raise RuntimeError("fetch failed: " + str(err))
    return data


def load_json(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def ledger(f):
    recs = []
    with open(os.path.join(S, "extract", "ledgers", f + ".jsonl"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def row_map(plan):
    m = {}
    for g in plan["groups"]:
        for i, r in enumerate(g["rows"]):
            m[r] = (g["group"], i)
    return m


def main():
    split = load_json(os.path.join(S, "SPLIT.json"))
    heldout = sorted(split["files"].values(), key=lambda s: int(s[1:-5]))
    rng = random.Random(SEED)
    with_ledger = [f"c{i}.h5ad" for i in range(50)
                   if os.path.exists(os.path.join(S, "extract", "ledgers", f"c{i}.h5ad.jsonl"))]
    train_pool = [f for f in with_ledger if f not in heldout]
    train_pick = sorted(rng.sample(train_pool, 4), key=lambda s: int(s[1:-5]))
    results = []
    summary_checks = []
    for f in heldout + train_pick:
        role = "heldout" if f in heldout else "train"
        plan = load_json(os.path.join(C, "extract", "plans", f + ".plan.json"))
        census = load_json(os.path.join(S, "census", f + ".json"))
        offset = census["layouts"]["obsm/X_hvg"]["offset"]
        assert offset == plan["x_hvg_offset"]
        gmap = {g["group"]: g for g in plan["groups"]}
        recs = [r for r in ledger(f) if r["error"] is None]
        ctl = [r for r in recs if gmap[int(r["purpose"].split("group")[1])]["control"]]
        trt = [r for r in recs if not gmap[int(r["purpose"].split("group")[1])]["control"]]
        k_t = 3 if role == "heldout" else 2
        pick = rng.sample(trt, k_t) + rng.sample(ctl, 1)
        z = np.load(os.path.join(C, "extract", f, "slots.npz"))
        slots = {int(g): int(s) for g, s in zip(z["group"], z["start"])}
        rows = np.load(os.path.join(C, "extract", f, "rows.npy"), mmap_mode="r")
        assert rows.dtype == np.dtype("<f4")
        rmap = row_map(plan)
        summ = np.load(os.path.join(C, "extract", f, "treated_summaries.npz")) if role == "train" else None
        for rec in pick:
            data = fetch(f, rec["start"], rec["end"])
            sha = hashlib.sha256(data).hexdigest()
            gid = int(rec["purpose"].split("group")[1])
            g = gmap[gid]
            first = (rec["start"] - offset) / ROW
            nrow = rec["bytes"] / ROW
            out = {"file": f, "role": role, "group": gid, "control": g["control"], "start": rec["start"],
                   "end": rec["end"], "bytes": rec["bytes"], "ledger_sha256": rec["sha256"], "fetched_sha256": sha,
                   "sha256_match": sha == rec["sha256"], "length_match": len(data) == rec["end"] - rec["start"] + 1,
                   "first_row": first, "n_rows": nrow}
            assert first.is_integer() and nrow.is_integer()
            first, nrow = int(first), int(nrow)
            file_rows = list(range(first, first + nrow))
            located = [rmap.get(r) for r in file_rows]
            out["rows_all_in_plan_group"] = all(x is not None and x[0] == gid for x in located)
            stored = None
            if out["rows_all_in_plan_group"] and (role == "heldout" or g["control"]):
                idx = [slots[gid] + x[1] for x in located]
                stored = np.asarray(rows[idx])
                out["rows_npy_bytes_equal"] = stored.tobytes() == data
            arr = np.frombuffer(data, dtype="<f4").reshape(nrow, 2000)
            if role == "train" and not g["control"] and out["rows_all_in_plan_group"]:
                covers = sorted(x[1] for x in located) == list(range(len(g["rows"])))
                out["covers_whole_group"] = covers
                if covers:
                    full = np.asarray(g["full"], bool)[[x[1] for x in located]]
                    X = arr[full].astype(np.float64)
                    i = int(np.flatnonzero(summ["group"] == gid)[0])
                    mu, var = X.mean(0), X.var(0, ddof=1)
                    sc = {"file": f, "group": gid, "n_recomputed": int(full.sum()), "n_summary": int(summ["n"][i]),
                          "max_abs_mean_diff": float(np.abs(mu - summ["mean"][i]).max()),
                          "max_abs_var_diff": float(np.abs(var - summ["var"][i]).max()),
                          "max_rel_var_diff": float((np.abs(var - summ["var"][i]) / np.maximum(np.abs(var), 1e-12)).max())}
                    sc["match"] = sc["n_recomputed"] == sc["n_summary"] and sc["max_abs_mean_diff"] < 1e-5 \
                        and sc["max_rel_var_diff"] < 1e-4
                    summary_checks.append(sc)
            results.append(out)
            print(f, gid, "ctl" if g["control"] else "trt", out["sha256_match"], out.get("rows_npy_bytes_equal"),
                  state["bytes"], flush=True)
    # extra: c39 local copy vs pinned remote
    extra = {}
    f = "c39.h5ad"
    plan = load_json(os.path.join(C, "extract", "plans", f + ".plan.json"))
    offset = plan["x_hvg_offset"]
    census = load_json(os.path.join(S, "census", f + ".json"))
    g = [x for x in plan["groups"] if x["control"]][rng.randrange(14)]
    rws = g["rows"]
    run = [rws[0]]
    for r in rws[1:]:
        if r == run[-1] + 1:
            run.append(r)
        else:
            break
    start, end = offset + run[0] * ROW, offset + (run[-1] + 1) * ROW - 1
    data = fetch(f, start, end)
    z = np.load(os.path.join(C, "extract", f, "slots.npz"))
    slots = {int(a): int(b) for a, b in zip(z["group"], z["start"])}
    rows = np.load(os.path.join(C, "extract", f, "rows.npy"), mmap_mode="r")
    stored = np.asarray(rows[slots[g["group"]]:slots[g["group"]] + len(run)]).tobytes()
    with open(LOCAL_C39, "rb") as fh:
        fh.seek(start)
        local = fh.read(end - start + 1)
    size_probe = session.get(_loc[f], headers={"Range": "bytes=0-0"}, timeout=60)
    remote_size = int(size_probe.headers["Content-Range"].split("/")[-1])
    state["bytes"] += len(size_probe.content)
    state["requests"] += 1
    extra = {"file": f, "group": g["group"], "plate": g["plate"], "rows": [run[0], run[-1]], "bytes": len(data),
             "remote_equals_rows_npy": data == stored, "remote_equals_local_copy": data == local,
             "local_copy_size": os.path.getsize(LOCAL_C39), "remote_size": remote_size,
             "census_file_bytes": census["file_bytes"], "sizes_equal": os.path.getsize(LOCAL_C39) == remote_size}
    files_covered = sorted({r["file"] for r in results}, key=lambda s: int(s[1:-5]))
    ho = [r for r in results if r["role"] == "heldout"]
    out = {
        "seed": SEED, "records_checked": len(results), "files_covered": files_covered,
        "heldout_files_covered": sorted({r["file"] for r in ho}),
        "sha256_matches": sum(r["sha256_match"] for r in results),
        "heldout_records_compared_with_rows_npy": sum("rows_npy_bytes_equal" in r for r in ho),
        "heldout_rows_npy_equal": sum(bool(r.get("rows_npy_bytes_equal")) for r in ho),
        "training_control_records_compared_with_rows_npy": sum("rows_npy_bytes_equal" in r for r in results if r["role"] == "train"),
        "training_control_rows_npy_equal": sum(bool(r.get("rows_npy_bytes_equal")) for r in results if r["role"] == "train"),
        "treated_summary_checks": summary_checks,
        "c39_local_copy_check": extra,
        "network": {"requests": state["requests"], "bytes": state["bytes"], "budget_bytes": BUDGET},
        "records": results,
    }
    out["pass"] = bool(out["sha256_matches"] == len(results) and len(results) >= 30 and len(files_covered) >= 6
                       and len(out["heldout_files_covered"]) == 5 and out["heldout_records_compared_with_rows_npy"] >= 10
                       and out["heldout_rows_npy_equal"] == out["heldout_records_compared_with_rows_npy"]
                       and all(r["rows_all_in_plan_group"] for r in results)
                       and all(sc["match"] for sc in summary_checks)
                       and out["training_control_rows_npy_equal"] == out["training_control_records_compared_with_rows_npy"])
    with open(os.path.join(V, "task2_raw_bytes.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(V, "task2_requests.jsonl"), "w", encoding="utf-8") as fh:
        for r in req_log:
            fh.write(json.dumps(r) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "records"}, indent=1))


if __name__ == "__main__":
    main()
