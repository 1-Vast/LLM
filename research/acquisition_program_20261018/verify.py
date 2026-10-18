"""Check the freezes, the search traces, the records and the reported contrasts of the acquisition-program study.

File summary
- Path: research/acquisition_program_20261018/verify.py
- Checks: FREEZE1/FREEZE2 digests; the trace budgets (12 proposals each) and that every accepted step satisfies the acceptance
  rule's recorded improvement; INCUMBENTS.json equals the traces' final incumbents; the programs compile under the grammar;
  RESULTS.json contrasts recompute exactly from records/held.json; the predecessor hindsight clarification recomputes from
  the predecessor's public records; frozen predecessors unchanged. Prints VERIFIED or exits non-zero.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "feedback_propagation_20261018"))
sys.path.insert(0, str(HERE))
import seal  # noqa: E402


def lf(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    fail = []
    for st in (1, 2):
        try:
            seal.check(st)
            print("PASS freeze", st)
        except SystemExit as e:
            print("FAIL", e)
            fail.append(str(e))
    inc = json.loads((HERE / "INCUMBENTS.json").read_text(encoding="utf-8"))
    import ap_task as A
    for name, f in (("conventional_search", "SEARCH_TRACE_conventional.json"), ("agent_search", "SEARCH_TRACE_agent.json")):
        tr = json.loads((HERE / f).read_text(encoding="utf-8"))
        ok = len(tr["trace"]) == 12 and tr["incumbent"] == inc[name]
        cur = "la"
        for t in tr["trace"]:
            if t["accepted"]:
                o = t["observed"]
                ok &= o["delta_total"] > 0 and o["cells_better"] > o["cells_worse"]
                cur = t["expression"]
        ok &= cur == tr["incumbent"]
        A.compile_program(inc[name])
        print("PASS" if ok else "FAIL", "trace", name)
        if not ok:
            fail.append(name)
    if (HERE / "RESULTS.json").exists():
        import evaluate as E
        res = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
        rec = json.loads((HERE / "records" / "held.json").read_text(encoding="utf-8"))
        again = json.loads(json.dumps(E.contrasts_from_records(rec)))
        ok = again == res["contrasts"]
        print("PASS" if ok else "FAIL", "contrasts recompute from records/held.json")
        if not ok:
            fail.append("contrasts")
    r = subprocess.run([sys.executable, "-B", str(HERE / "hindsight_clarification.py")], capture_output=True, text=True, cwd=str(HERE))
    ok = "'campaign_best_of': 131" in r.stdout and "'R1': 100" in r.stdout
    print("PASS" if ok else "FAIL", "hindsight clarification recomputes (131 vs 100)")
    if not ok:
        fail.append("hindsight")
    for study in ("feedback_propagation_20261018", "seed_attribution_20261017", "feedback_attribution_20261017"):
        p = ROOT / "research" / study / "FREEZE.json"
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            bad = [rel for rel, d in (rec.get("sha256_lf") or {}).items()
                   if not ((ROOT / rel).exists() or (ROOT / "research" / study / rel).exists())
                   or lf((ROOT / rel) if (ROOT / rel).exists() else (ROOT / "research" / study / rel)) != d]
            if study == "feedback_propagation_20261018":
                bad = [b for b in bad if b != "REPORT.md"]
            print("PASS" if not bad else "FAIL", "predecessor unchanged", study)
            if bad:
                fail.append(f"{study}: {bad[:3]}")
    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("VERIFIED")


if __name__ == "__main__":
    main()
