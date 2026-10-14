"""Offline verification of the mechanism-falsification study: defect reproduction, strict contracts, census, benchmark, assets.

File summary
- Path: research/mechanism_falsification_20261014/verify.py
- Purpose: replay, without any network, paid call, sealed outcome or expression matrix, every mechanical fact that
  the documents in this folder cite. Prose judgements (severity, novelty class, the verdict) are not machine-checked.
- Core points:
  - Defects: `reproduce_defects.py` still shows D1-D3c on the historical modules (they were deliberately not changed).
  - Strict contracts: `benchmark.py` fixtures replayed in memory must give the status stored in BENCHMARK_RESULTS.json,
    and the strict policy must pass all 21 tasks while the legacy review fails the recorded 15.
  - Census: CENSUS.json must carry the A0 decision INSUFFICIENT_MECHANISM_TRUTH with zero measured references and
    must record that no expression matrix and no PRISM 24Q2 response was opened.
  - Triage: the structural power limit in CONFORMAL_TRIAGE.json must recompute from its own counts.
  - Assets: ASSET_AUTH*.json statuses are only VERIFIED or LOCAL_DIGEST_ONLY; a replay that needs any other status is
    BLOCKED/ASSET_MISSING, never success.
  - Frozen history: the files of every frozen study are unchanged in the git working tree (skipped when git is absent).
- Command: `python research/mechanism_falsification_20261014/verify.py` from the repository root.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

ALLOWED_CHANGES = {"pyproject.toml", "research/REPORT.md", "research/STUDIES.json", "research/EVIDENCE.md"}


def load(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def check_defects(fail: list) -> None:
    out = subprocess.run([sys.executable, "-I", str(HERE / "reproduce_defects.py")], capture_output=True, text=True, cwd=ROOT)
    if out.returncode:
        fail.append(f"reproduce_defects.py exited {out.returncode}")
        return
    d = json.loads(out.stdout)
    if d["D1_unauthenticated_no_go"]["status"] != "NO_GO" or d["D1_unauthenticated_no_go"]["evidence_supplied"] != 0:
        fail.append("D1 no longer reproduces on the historical review")
    if d["D2_premature_go"]["status"] != "GO" or not d["D2_premature_go"]["untested_required"]:
        fail.append("D2 no longer reproduces on the historical review")
    if d["D3_unauthenticated_digest_admitted"]["source_exists"] or not d["D3_unauthenticated_digest_admitted"]["admit"][0]:
        fail.append("D3 no longer reproduces")
    if d["D3b_independent_flag_not_consulted"]["status"] != "GO" or d["D3c_derived_without_lineage"]["status"] != "GO":
        fail.append("D3b or D3c no longer reproduces")


def check_benchmark(fail: list) -> None:
    import benchmark as b

    stored = {r["id"]: r for r in load("BENCHMARK_RESULTS.json")["tasks"]}
    fixtures = b.fixtures()
    strict_ok = 0
    for fx in fixtures:
        s, l = b.run_strict(fx), b.run_legacy(fx)
        row = stored.get(fx["id"])
        if row is None or row["strict"]["status"] != s["status"] or row["legacy"]["status"] != l["status"]:
            fail.append(f"benchmark task {fx['id']} no longer matches the stored result")
        strict_ok += b.matches(s, fx["expected"]) and (fx["id"] != "D-04" or s.get("certificate_invalidated") is True)
    executable = b.executable_tasks()
    strict_ok += sum(t["strict_passes"] for t in executable)
    total = len(fixtures) + len(executable)
    summary = load("BENCHMARK_RESULTS.json")["summary"]
    if (strict_ok, total) != (summary["strict_passes"], summary["tasks"]) or strict_ok != total:
        fail.append(f"strict policy passes {strict_ok} of {total}; stored {summary['strict_passes']} of {summary['tasks']}")
    if len(summary["legacy_fails"]) != 15:
        fail.append("stored legacy failures changed")
    if "specification conformance" not in summary["caveat"]:
        fail.append("benchmark caveat dropped")


def check_census(fail: list) -> None:
    c = load("CENSUS.json")
    if c["a0_decision"] != "INSUFFICIENT_MECHANISM_TRUTH":
        fail.append("A0 decision changed")
    if c["expression_matrices_opened"] or c["prism_24q2_responses_opened"] or c["downloads"]:
        fail.append("census claims an access the protocol forbids")
    t = c["independent_mechanism_truth"]["categories"]
    if t["measured_positive_reference"] or t["measured_negative_reference"]:
        fail.append("census records measured references that do not exist locally")
    if c["power"]["available_now"] != 0:
        fail.append("power section changed")


def check_triage(fail: list) -> None:
    s = load("CONFORMAL_TRIAGE.json")["structural_power_limit"]
    need = s["test_units_m"] / 0.1
    if abs(s["calibration_units_needed_to_reject_one_at_q0.1"] - need) > 1:
        fail.append("structural power limit does not recompute from m / (q k)")
    if abs(s["smallest_possible_p"] - 1 / (s["calibration_units_n_R3"] + 1)) > 1e-12:
        fail.append("smallest possible p-value does not equal 1/(n+1)")
    if abs(s["BH_threshold_for_first_rejection_q0.1"] - 0.1 / s["test_units_m"]) > 1e-12:
        fail.append("BH threshold for the first rejection does not equal q/m")


def check_assets(fail: list) -> None:
    for name in ("ASSET_AUTH.json", "ASSET_AUTH_LARGE.json"):
        for row in load(name)["assets"]:
            if row["status"] not in {"VERIFIED", "LOCAL_DIGEST_ONLY"}:
                fail.append(f"{name}: {row['path']} is {row['status']}")


def check_frozen_history(fail: list) -> None:
    try:
        changed = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True, cwd=ROOT, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        print("git unavailable: frozen-history check skipped")
        return
    for path in changed:
        if path not in ALLOWED_CHANGES:
            fail.append(f"tracked file changed: {path}")


def main() -> int:
    fail: list[str] = []
    for check in (check_defects, check_benchmark, check_census, check_triage, check_assets, check_frozen_history):
        check(fail)
        print(f"{check.__name__}: {'FAIL' if any(check.__name__[6:] in f for f in fail) else 'done'}")
    for f in fail:
        print("FAIL", f)
    print("PASS" if not fail else f"{len(fail)} failure(s)")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
