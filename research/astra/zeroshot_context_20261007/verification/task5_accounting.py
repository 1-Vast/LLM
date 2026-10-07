"""Workstream C, task 5: network accounting from every ledger (verifier's own code).

Stages: census/ledgers, census/attempt1_stopped/ledgers, extract/ledgers, axis_check/ledgers.
Per stage: ledger files, requests (records), failed requests (error not null), bytes, attempts,
records whose byte count differs from end-start+1, duplicate spans, per-purpose totals, and the
pinned revision. Cross-checks per-file ledger totals against the extraction receipts
(remote_requests / remote_bytes) and the census JSONs. Writes task5_accounting.json.
"""
import collections
import glob
import json
import os

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
V = os.path.join(S, "verification")
REV = "fdf87abece385feea6fa5e9944ab46e173b6af50"
STAGES = {
    "census": os.path.join(S, "census", "ledgers"),
    "census_attempt1_stopped": os.path.join(S, "census", "attempt1_stopped", "ledgers"),
    "extract": os.path.join(S, "extract", "ledgers"),
    "axis_check": os.path.join(S, "axis_check", "ledgers"),
}


def read_ledger(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    res = {"stages": {}, "totals": {}}
    per_file = {}
    for stage, d in STAGES.items():
        files = sorted(glob.glob(os.path.join(d, "*.jsonl")))
        st = {"ledger_files": len(files), "requests": 0, "failed_requests": 0, "bytes": 0, "attempts": 0,
              "retried_requests": 0, "length_mismatch": 0, "duplicate_spans": 0, "other_revision": 0,
              "file_name_mismatch": 0, "purposes": {}, "first_utc": None, "last_utc": None}
        purposes = collections.defaultdict(lambda: {"requests": 0, "bytes": 0})
        for path in files:
            name = os.path.basename(path)[:-len(".jsonl")]
            recs = read_ledger(path)
            spans = collections.Counter()
            pf = per_file.setdefault(stage, {}).setdefault(name, {"requests": 0, "bytes": 0, "failed": 0})
            for r in recs:
                st["requests"] += 1
                pf["requests"] += 1
                st["attempts"] += int(r.get("attempts", 1))
                if int(r.get("attempts", 1)) > 1:
                    st["retried_requests"] += 1
                if r.get("error") is not None:
                    st["failed_requests"] += 1
                    pf["failed"] += 1
                b = int(r.get("bytes") or 0)
                st["bytes"] += b
                pf["bytes"] += b
                if r.get("error") is None and b != r["end"] - r["start"] + 1:
                    st["length_mismatch"] += 1
                if r.get("revision") != REV:
                    st["other_revision"] += 1
                if r.get("file") != name:
                    st["file_name_mismatch"] += 1
                spans[(r["start"], r["end"])] += 1
                p = r.get("purpose", "").split(":")[0]
                purposes[p]["requests"] += 1
                purposes[p]["bytes"] += b
                u = r.get("utc")
                if u:
                    st["first_utc"] = u if st["first_utc"] is None else min(st["first_utc"], u)
                    st["last_utc"] = u if st["last_utc"] is None else max(st["last_utc"], u)
            st["duplicate_spans"] += sum(v - 1 for v in spans.values() if v > 1)
        st["purposes"] = dict(purposes)
        st["GB"] = round(st["bytes"] / 1e9, 4)
        res["stages"][stage] = st
    tot = {k: sum(s[k] for s in res["stages"].values())
           for k in ("ledger_files", "requests", "failed_requests", "bytes", "attempts", "retried_requests",
                     "length_mismatch", "duplicate_spans", "other_revision")}
    tot["GB"] = round(tot["bytes"] / 1e9, 4)
    tot["GiB"] = round(tot["bytes"] / 2 ** 30, 4)
    res["totals"] = tot
    # cross-check with receipts
    xr = {"extract_receipts_checked": 0, "extract_mismatches": [], "census_checked": 0, "census_mismatches": [],
          "files_without_extract_ledger": [], "files_without_census_ledger": []}
    for i in range(50):
        f = f"c{i}.h5ad"
        rp = os.path.join(S, "extract", f + ".receipt.json")
        with open(rp, encoding="utf-8") as fh:
            rec = json.load(fh)
        led = per_file.get("extract", {}).get(f)
        if led is None:
            xr["files_without_extract_ledger"].append({"file": f, "receipt_remote_requests": rec.get("remote_requests"),
                                                       "receipt_remote_bytes": rec.get("remote_bytes"),
                                                       "receipt_local_read": rec.get("local_read")})
        else:
            xr["extract_receipts_checked"] += 1
            if led["requests"] != rec.get("remote_requests") or led["bytes"] != rec.get("remote_bytes"):
                xr["extract_mismatches"].append({"file": f, "ledger": led, "receipt": [rec.get("remote_requests"), rec.get("remote_bytes")]})
        with open(os.path.join(S, "census", f + ".json"), encoding="utf-8") as fh:
            cen = json.load(fh)
        cl = per_file.get("census", {}).get(f)
        if cl is None:
            xr["files_without_census_ledger"].append({"file": f, "census_source": cen.get("source"),
                                                      "census_remote_requests": cen.get("remote_requests"),
                                                      "census_remote_bytes": cen.get("remote_bytes")})
        else:
            xr["census_checked"] += 1
            if cl["requests"] != cen.get("remote_requests") or cl["bytes"] != cen.get("remote_bytes"):
                xr["census_mismatches"].append({"file": f, "ledger": cl, "census_json": [cen.get("remote_requests"), cen.get("remote_bytes")]})
    res["receipt_cross_check"] = xr
    # verifier's own network use (task 2)
    own = {"requests": 0, "bytes": 0, "failed": 0, "logs": [],
           "note": "range GETs only; HEAD requests used to resolve the 302 redirect carry no body"}
    for log in ("task2_requests.jsonl", "task2b_requests.jsonl"):
        rp = os.path.join(V, log)
        if os.path.exists(rp):
            own["logs"].append(log)
            for r in read_ledger(rp):
                own["requests"] += 1
                own["bytes"] += r["bytes"]
                own["failed"] += r["error"] is not None
    own["one_byte_size_probe_not_in_logs"] = 1
    t2 = os.path.join(V, "task2_raw_bytes.json")
    if os.path.exists(t2):
        with open(t2, encoding="utf-8") as fh:
            own["task2_counter_including_size_probe"] = json.load(fh)["network"]
    res["verifier_network_use"] = own
    res["pass"] = bool(tot["length_mismatch"] == 0 and tot["other_revision"] == 0 and not xr["extract_mismatches"]
                       and not xr["census_mismatches"])
    with open(os.path.join(V, "task5_accounting.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
