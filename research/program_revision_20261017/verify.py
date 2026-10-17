"""Check the freeze, the access record, and that the reported numbers follow from the cached records.

File summary
- Path: research/program_revision_20261017/verify.py
- Purpose: one command that says whether this study's reported results follow from its frozen code.
- Checks:
  - every FREEZE.json digest (LF-normalised) and the Stage A record digest;
  - SPLITS.json input digests against the raw PRISM/DepMap files when they are present;
  - LIBRARIES.json equals the digest recorded in ACCESS.json (no library edit after exposure);
  - every arm's trajectory file exists and its accepted edits rebuild that arm's final library;
  - RESULTS.json: `evaluate.analyse()` on the cached per-line records equals it exactly, and the
    records' digest is the one RESULTS.json names;
  - the LLM ledger's spend is within the cap.
- Records: per-line records and the LLM ledger are read from `records/` (retained copies of the
  run cache, which tmp/ cleanup may remove), falling back to tmp/program_revision_20261017/.
- Interfaces: ``python -B verify.py``; prints VERIFIED or exits non-zero with the failures.
"""
from __future__ import annotations

import json
import sys

from common import CACHE, DEPMAP, HERE, RAW, ROOT, lf_digest, sha256

ARMS = ["seed_fixed", "stepwise", "maestro_enum", "maestro_llm", "maestro_enum_empty", "maestro_llm_empty",
        "maestro_enum_joint", "maestro_llm_joint"]


def record(name: str):
    """Retained copy in records/ (tmp/ may be pruned), else the run cache."""
    kept = HERE / "records" / name
    return kept if kept.exists() else CACHE / name


def main() -> None:
    fail = []
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for f, digest in freeze["sha256_lf"].items():
        ok = (ROOT / f).exists() and lf_digest(ROOT / f) == digest
        print("PASS" if ok else "FAIL", "freeze", f)
        if not ok:
            fail.append(f)
    if sha256(HERE / "STAGE_A.json") != freeze["stage_a_sha256"]:
        fail.append("STAGE_A.json")
    splits = json.loads((HERE / "SPLITS.json").read_text(encoding="utf-8"))
    for name, digest in splits["inputs_sha256"].items():
        for base in (RAW, DEPMAP):
            p = base / name
            if p.exists():
                ok = sha256(p) == digest
                print("PASS" if ok else "FAIL", "input", name)
                if not ok:
                    fail.append(name)
    libs_path = HERE / "LIBRARIES.json"
    if libs_path.exists():
        libs = json.loads(libs_path.read_text(encoding="utf-8"))
        access = HERE / "ACCESS.json"
        if access.exists():
            rec = json.loads(access.read_text(encoding="utf-8"))
            ok = rec["libraries_sha256"] == sha256(libs_path)
            print("PASS" if ok else "FAIL", "libraries unchanged since first exposure")
            if not ok:
                fail.append("LIBRARIES.json changed after exposure")
        for arm in ARMS:
            t = HERE / "trajectories" / f"{arm}.jsonl"
            if not t.exists():
                fail.append(f"trajectory {arm}")
                continue
            rows = [json.loads(x) for x in t.read_text(encoding="utf-8").splitlines() if x.strip()]
            if arm.startswith("maestro"):
                final = rows[-1]["library_after"] if rows else []
                ok = sorted(final) == sorted(p["key"] for p in libs[arm]["programs"])
                ok &= (rows[-1]["design"] if rows else None) == libs[arm]["design"]
                print("PASS" if ok else "FAIL", "trajectory rebuilds library", arm)
                if not ok:
                    fail.append(f"trajectory/library {arm}")
    res_path = HERE / "RESULTS.json"
    if res_path.exists():
        import evaluate
        stored = json.loads(res_path.read_text(encoding="utf-8"))
        units_path = record("units_future.json")
        if sha256(units_path) != stored["units_sha256"]:
            fail.append("units digest")
        else:
            units = json.loads(units_path.read_text(encoding="utf-8"))
            again = json.loads(json.dumps(evaluate.analyse(units, False)))
            keep = {k: v for k, v in stored.items() if k not in ("seconds", "units_sha256")}
            same = again == keep
            print("PASS" if same else "FAIL", "RESULTS.json recomputed from cached per-line records")
            if not same:
                fail.append("RESULTS.json")
    ledger = record("llm_ledger.jsonl")
    if ledger.exists():
        from llm_proposer import RATE_IN, RATE_OUT, SPEND_CAP
        rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
        usd = sum(r.get("usage", {}).get("prompt_tokens", 0) for r in rows) * RATE_IN / 1e6 + \
            sum(r.get("usage", {}).get("completion_tokens", 0) for r in rows) * RATE_OUT / 1e6
        print("PASS" if usd <= SPEND_CAP else "FAIL", f"LLM spend {usd:.4f} USD <= cap")
        if usd > SPEND_CAP:
            fail.append("LLM spend")
    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("VERIFIED")


if __name__ == "__main__":
    main()
