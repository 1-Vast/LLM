"""Verify audit 1 at separate levels. There is no single pass/fail line.

  1 software integrity       artefacts present, audit tests, v1 verify and v1 tests
  2 recalculation            stored requalification, counts and manifest digests recomputed from the stored records
  3 full reproduction        mutation checks and the audit build rerun, outputs compared byte for byte
  4 independent biological confirmation  not performed and not performable from this evidence

extract_supplements.py needs the downloaded supplementary files and is not rerun here.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "implementation_identifiability_v1"
sys.path.insert(0, str(HERE))
GENERATED = ["records_v2.jsonl", "SOURCE_COMPLETION_AUDIT.json", "JB211_PREMISE_STATUS.json", "CCT57_TERMINAL_STATUS.json", "MISSING_EVIDENCE_UPDATE.json",
             "AUDIT_MANIFEST.json", "GATE_DECISIONS_AUDIT1.json", "MUTATION_RESULTS.json"]
STATIC = ["PROTOCOL.md", "AMENDMENT.md", "supplement_extracts.json", "audit_logic.py", "audit_data.py", "mutation.py", "build_audit.py", "extract_supplements.py"]


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def run(args, cwd):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


def level1():
    ok = True
    for a in GENERATED + STATIC:
        present = (HERE / a).is_file()
        ok &= present
        print(f"  {'ok ' if present else 'BAD'} artefact {a}")
    p = run([sys.executable, "-m", "pytest", str(HERE / "tests"), "-q", "-p", "no:cacheprovider"], HERE)
    print("  audit tests: " + (p.stdout.strip().splitlines() or ["no output"])[-1])
    ok &= p.returncode == 0
    p = run([sys.executable, str(V1 / "verify.py")], V1)
    print("  v1 verify: " + ("pass" if p.returncode == 0 else "FAIL"))
    ok &= p.returncode == 0
    p = run([sys.executable, "-m", "pytest", str(V1 / "tests" / "test_g0_g1.py"), "-q", "-p", "no:cacheprovider"], V1)
    print("  v1 tests: " + (p.stdout.strip().splitlines() or ["no output"])[-1])
    ok &= p.returncode == 0
    return ok


def level2():
    ok = True
    man = json.loads((HERE / "AUDIT_MANIFEST.json").read_text(encoding="utf-8"))
    for rel, h in man["v1_artefact_sha256"].items():
        same = digest(V1 / rel) == h
        ok &= same
        print(f"  {'ok ' if same else 'BAD'} v1 artefact unchanged: {rel}")
    for rel, h in man["file_sha256"].items():
        same = digest(HERE / rel) == h
        ok &= same
        print(f"  {'ok ' if same else 'BAD'} manifest digest: {rel}")
    import audit_logic as al
    import records as rec
    v1 = {r["id"]: r for r in rec.RECORDS}
    bad = []
    for line in (HERE / "records_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["supersedes"] is not None and r["supersedes_digest"] != al.canonical_digest(v1[r["supersedes"]]):
            bad.append(r["id"])
    ok &= not bad
    print(f"  {'ok ' if not bad else 'BAD'} every superseded v1 record digest matches ({bad})")
    g = json.loads((HERE / "GATE_DECISIONS_AUDIT1.json").read_text(encoding="utf-8"))
    levels = [r["level"] for r in g["G0"]["requalification"]]
    counts = {f"level_{k}_units": levels.count(k) for k in (1, 2, 3, 4)}
    same = counts == g["G0"]["counts"] and not any(r["can_exceed_v1_level"] for r in g["G0"]["requalification"])
    ok &= same
    print(f"  {'ok ' if same else 'BAD'} unit-level counts {counts}, no audit rule raises a level")
    expect = "QUALIFIED_FOR_RESEARCH_PENDING_POWER" if counts["level_3_units"] else ("QUALIFIED_FOR_LOGIC_TEST" if counts["level_2_units"] else "ASSET_BLOCKED")
    same = g["G0"]["g0_decision"] == expect
    ok &= same
    print(f"  {'ok ' if same else 'BAD'} G0 decision {g['G0']['g0_decision']} follows from counts")
    for k in ("G2", "G3", "G4", "G5"):
        ok &= g[k] == "NOT_EXECUTED"
    for flag, want in (("post_hoc_audit", True), ("not_preregistered", True), ("independent_confirmation", False), ("sources_exposed", True)):
        ok &= man[flag] is want
    print("  ok  G2-G5 not executed; audit flags as required" if ok else "  BAD flags")
    return ok


def level3():
    ok = True
    before = {a: (HERE / a).read_bytes() for a in GENERATED}
    for script in ("mutation.py", "build_audit.py"):
        p = run([sys.executable, str(HERE / script)], HERE)
        ok &= p.returncode == 0
        print(f"  {'ok ' if p.returncode == 0 else 'BAD'} ran {script}")
    for a in GENERATED:
        same = (HERE / a).read_bytes() == before[a]
        ok &= same
        print(f"  {'ok ' if same else 'BAD'} rebuilt byte-identical: {a}")
    return ok


def main():
    results = []
    for n, f in ((1, level1), (2, level2), (3, level3)):
        print(f"level {n}: {f.__doc__ or f.__name__}")
        results.append(f())
        print(f"level {n}: {'PASS' if results[-1] else 'FAIL'}")
    print("level 4: independent biological confirmation: NOT PERFORMED (not performable from this evidence)")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
