"""Verify the G0/G1 package at four separate levels. There is no single pass/fail line.

  1 software integrity      tests, artefact presence, access-control behaviour
  2 statistical recalculation  there are no statistics in G0/G1; stored eligibility and gate fields are recomputed
  3 full computational reproduction  rebuild G0 and rerun G1, compare bytes
  4 independent biological confirmation  not performed and not performable from this evidence

Optional: --online re-downloads the two Europe PMC XML files and compares their digests.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ARTEFACTS = [
    "evidence/manifest.jsonl", "evidence/records.jsonl", "evidence/units.jsonl", "evidence/actions.jsonl", "evidence/eligibility.json",
    "evidence/access_ledger.jsonl", "evidence/replay_access_ledger.jsonl", "evidence/dependence_graph.json", "evidence/mismatch_register.json",
    "evidence/missing_evidence_register.json", "evidence/candidate_split_manifest.json",
    "results/gate_decisions.json", "results/metrics.json", "results/cost_ledger.jsonl",
]


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def level1():
    ok = True
    for a in ARTEFACTS:
        present = (HERE / a).is_file()
        ok &= present
        print(f"  {'ok ' if present else 'BAD'} artefact {a}")
    p = subprocess.run([sys.executable, "-m", "pytest", str(HERE / "tests"), "-q", "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=HERE)
    print("  " + (p.stdout.strip().splitlines() or ["no output"])[-1])
    ok &= p.returncode == 0
    gd = json.loads((HERE / "results" / "gate_decisions.json").read_text(encoding="utf-8"))
    for g in ("G2", "G3", "G4"):
        ok &= gd[g] == "NOT_EXECUTED"
    ok &= gd["G5"].startswith("NOT_EXECUTED")
    return ok


def level2():
    import idlib
    import records as rec
    ok = True
    elig = json.loads((HERE / "evidence" / "eligibility.json").read_text(encoding="utf-8"))
    classes = [idlib.classify_unit(u, rec.RECORDS) for u in rec.UNITS]
    same = json.loads(json.dumps(classes)) == elig["unit_classification"]
    ok &= same
    print(f"  {'ok ' if same else 'BAD'} unit classification recomputed from records")
    levels = [c["level"] for c in classes]
    expect = "QUALIFIED_FOR_RESEARCH_PENDING_POWER" if max(levels) >= 3 else ("QUALIFIED_FOR_LOGIC_TEST" if max(levels) >= 2 else "ASSET_BLOCKED")
    gd = json.loads((HERE / "results" / "gate_decisions.json").read_text(encoding="utf-8"))
    same = gd["G0"]["decision"] == expect
    ok &= same
    print(f"  {'ok ' if same else 'BAD'} G0 decision {gd['G0']['decision']} follows from unit levels {levels}")
    mt = json.loads((HERE / "results" / "metrics.json").read_text(encoding="utf-8"))
    consistent = (gd["G1"]["biological"] == "BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED") == (not gd["G1"]["section_9_4_criterion_met"])
    ok &= consistent
    print(f"  {'ok ' if consistent else 'BAD'} G1 biological label consistent with the section 9.4 criterion flag")
    wells = sum(json.loads(l)["wells"] for l in (HERE / "results" / "cost_ledger.jsonl").read_text(encoding="utf-8").splitlines() if '"simulated_acquisition"' in l)
    same = wells == mt["simulated_wells_spent"]
    ok &= same
    print(f"  {'ok ' if same else 'BAD'} simulated wells {wells} match metrics, actual ledger kept separate")
    return ok


def level3():
    before = {a: digest(HERE / a) for a in ARTEFACTS}
    import build_g0
    build_g0.main()
    r = subprocess.run([sys.executable, str(HERE / "run_g1.py")], capture_output=True, text=True, cwd=HERE)
    ok = r.returncode == 0
    after = {a: digest(HERE / a) for a in ARTEFACTS}
    for a in ARTEFACTS:
        same = before[a] == after[a]
        ok &= same
        print(f"  {'ok ' if same else 'BAD'} reproduced {a}")
    return ok


def online():
    import urllib.request
    import records as rec
    ok = True
    for sid, s in rec.SOURCES.items():
        data = urllib.request.urlopen(s["retrieved_from"], timeout=90).read()
        same = hashlib.sha256(data).hexdigest() == s["xml_sha256"]
        ok &= same
        print(f"  {'ok ' if same else 'DIFFERS (source text may have been revised)'} {sid} xml digest")
    return ok


def main():
    res = {}
    for name, fn in (("1 software integrity", level1), ("2 statistical recalculation (stored fields only; no statistics exist)", level2),
                     ("3 full computational reproduction", level3)):
        print(f"[level {name}]")
        res[name] = fn()
    if "--online" in sys.argv:
        print("[optional: source digests]")
        res["source digests"] = online()
    print("[level 4 independent biological confirmation]\n  NOT PERFORMED: all evidence is known-case and designer-exposed")
    for k, v in res.items():
        print(f"{'PASS' if v else 'FAIL'}  level {k}")
    sys.exit(0 if all(res.values()) else 1)


if __name__ == "__main__":
    main()
