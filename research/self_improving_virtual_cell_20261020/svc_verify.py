"""Read-only verifier. It fits nothing, calls no API and opens no outcome file (sealed arrays are only stat'ed).

Levels
  1 frozen-file integrity       code/protocol/export hashes against FREEZE.json; prior package and consumed inputs unchanged
  2 stored-output recalculation contrast tables, labels and arm means recomputed from stored per-cell results
  3 boundary and accounting     budgets, unique nominations, split disjointness, library transitions, API limits, compute limit
Independent biological confirmation is not performed and not performable from this evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))


def sha_lf(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main() -> int:
    problems, notes = [], []
    check = lambda ok, msg: problems.append(msg) if not ok else None  # noqa: E731
    present = lambda n: (HERE / n).exists()  # noqa: E731
    import svc_summarize as SM

    # ---- level 1
    if present("FREEZE.json"):
        fr = load("FREEZE.json")
        for f, h in fr["code_sha256"].items():
            check(sha_lf(HERE / f) == h, f"frozen file changed after freeze: {f}")
        check(sha_lf(HERE / "PROTOCOL.md") == fr["protocol_sha256"], "PROTOCOL.md changed after freeze")
        check(sha_lf(HERE / "DEV_HEADROOM.json") == fr["dev_headroom_sha256"], "DEV_HEADROOM.json changed after freeze")
        export = ROOT / "tmp" / "self_improving_virtual_cell_20261020" / "env_export.npz"
        if export.exists():
            check(hashlib.sha256(export.read_bytes()).hexdigest() == fr["env_export_sha256"], "environment export changed after freeze")
    if present("INTEGRITY_BEFORE.json") and present("INTEGRITY_AFTER.json"):
        b, a = load("INTEGRITY_BEFORE.json"), load("INTEGRITY_AFTER.json")
        check(b == a, "prior package or consumed inputs differ between the before and after receipts")
        notes.append("prior package + consumed inputs: before == after" if b == a else "prior package differs")
    elif present("INTEGRITY_BEFORE.json"):
        notes.append("INTEGRITY_AFTER.json not yet produced")

    # ---- level 2 / 3 on stored results
    for fname, key in (("SYNTHETIC_RESULTS.json", "synthetic"), ("REAL_RESULTS.json", "real")):
        if not present(fname):
            continue
        data = load(fname)
        results = data["results"]
        check(data["compute_seconds"] <= 120 * 60 + 5 or key == "synthetic", f"{key}: compute limit exceeded")
        for r in results:
            cells = r["cells"]
            allc = [c for k in ("H0", "D1", "D2", "D3", "A", "T") for c in cells[k]]
            check(len(allc) == len(set(allc)), f"{key}: cell splits overlap in {r['world']}")
            check(set(r["test"]) >= {"refit", "evo_full", "evo_repr", "evo_proc", "evo_noinherit"}, f"{key}: missing arms in {r['world']}")
            n_test = len(cells["T"])
            for arm, rows in r["test_detail"].items():
                check(len(rows) == n_test, f"{key}: {arm} does not cover all test cells")
                for d in rows:
                    check(d["spent"] <= r["budget"], f"{key}: {arm} exceeded the query budget")
                    check(len(set(d["nominated"])) == len(d["nominated"]) == 5, f"{key}: {arm} duplicate or short nomination")
                    check(d["utility"] <= d["oracle"] + 1e-9, f"{key}: utility above oracle")
                    check(d["n_nominated_queried"] <= d["spent"], f"{key}: more queried nominations than spent units")
                    if r["contract"] == "T":
                        check(d["n_nominated_queried"] == 0, f"{key}: transfer contract nominated a probed pair")
            check("direct" not in r["test"] or r["contract"] == "E", f"{key}: direct confirmation under the transfer contract")
            for arm, recs in r["generation_records"].items():
                check(len(recs) <= 3, f"{key}: more than three generations ({arm})")
                for g in recs:
                    check(g["n_candidates"] <= 12, f"{key}: more than 12 candidates in a generation ({arm})")
            for arm, lib in r["library"].items():
                ids = {e["id"] for e in lib}
                for e in lib:
                    check(e["parent"] is None or e["parent"] in ids, f"{key}: dangling parent {e['id']}")
                    check(e["status"] in ("demonstrated", "provisional", "retired"), f"{key}: bad status {e['status']}")
                    if e["status"] != "provisional" and e["parent"] is not None:
                        check("validation" in e["evidence"], f"{key}: {e['id']} left provisional without a validation record")
                if arm == "evo_noinherit":
                    check(all(e["parent"] in (None, lib[0]["id"]) for e in lib), f"{key}: no-inheritance arm inherited a learned program")
        # recompute summaries from per-cell results
        groups = SM.group(results)
        if present("SUMMARY.json"):
            summ = load("SUMMARY.json").get(key, {}).get("conditions", {})
            for (grp, contract, B), rs in groups.items():
                k = f"{grp}|{contract}|B{B}"
                if k not in summ:
                    problems.append(f"{key}: {k} missing from SUMMARY.json")
                    continue
                again = SM.contrasts(rs)
                for name, v in again.items():
                    check(abs(v["mean"] - summ[k]["contrasts"][name]["mean"]) < 1e-9 and v["wins"] == summ[k]["contrasts"][name]["wins"], f"{key}: {k} {name} not reproduced")
                check(abs(SM.arm_means(rs)["refit"] - summ[k]["arm_means"]["refit"]) < 1e-9, f"{key}: {k} arm mean not reproduced")
        notes.append(f"{key}: {len(results)} condition runs checked")
    if present("SUMMARY.json") and present("DEV_HEADROOM.json"):
        summ, head = load("SUMMARY.json"), load("DEV_HEADROOM.json")
        for k, v in summ.get("labels", {}).items():
            opp = v["headroom"] >= 0.005
            expect = SM.label(v["contrast"], v["delta_use"], v["control"]) if opp else "NO_DECISION_OPPORTUNITY"
            check(expect == v["label"], f"label for {k} not reproduced")
            check(abs(v["delta_use"] - 0.25 * v["headroom"]) < 1e-12, f"delta_use for {k} is not 25% of the stored H0 headroom")
        check(abs(head["delta_use"] - 0.25 * head["primary"]["headroom"]) < 1e-12, "primary delta_use is not 25% of headroom")
    if present("API_RESULTS.json"):
        api = load("API_RESULTS.json")
        led = api["api_ledger"]
        check(led["http_attempts"] <= 6 and led["cumulative_tokens"] <= 30000, "API limits exceeded")
        text = json.dumps(api)
        check("Bearer" not in text and "api_key" not in text.lower() and "sk-" not in text, "credential-like text in API results")
        notes.append("API: attempts %d, tokens %d, outcomes %s" % (led["http_attempts"], led["cumulative_tokens"], [r["outcome"] for r in led["receipts"]]))
    if present("SERIALIZATION_RECEIPT.json"):
        rc = load("SERIALIZATION_RECEIPT.json")["receipts"]
        for k, v in rc.items():
            check(v["equal"], f"saved program {k} did not reproduce predictions after reload")
            f = next((p for p in (HERE / "PROGRAMS").glob("fitted_*.json") if p.name.split("_", 1)[1].startswith(k.replace(":", "_"))), None)
            check(f is not None and hashlib.sha256(f.read_bytes()).hexdigest() == v["file_sha256"], f"serialised program file for {k} missing or changed")
    for p in problems:
        print("FAIL", p)
    for n in notes:
        print("NOTE", n)
    print("VERIFY OK (levels 1-3; no refit, no API call, no outcome opened)" if not problems else f"VERIFY FAILED ({len(problems)})")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
