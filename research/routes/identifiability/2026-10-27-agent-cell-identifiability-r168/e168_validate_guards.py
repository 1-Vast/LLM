"""E168: validate the per-group guards against the real R167 data.

Reads E167_RESULTS.json (no refitting) and checks that the guards reproduce the conclusion R167 reached
after correcting its own gate: one group dropped for appearing in a single split, at least one degenerate
interval flagged, and zero interval-supported reversals.

Pre-registered in PROTOCOL_E156.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\MAESTRO")
sys.path.insert(0, str(ROOT / "research" / "tools"))
from effect_audit import summarise, min_reps_filter, ci_degenerate  # noqa: E402

E167 = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r167" / "E167_RESULTS.json"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r168"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = json.loads(E167.read_text(encoding="utf-8"))
    groups = {r["level"]: r for r in d["per_level"]}

    rep = summarise(groups, diff_key="pathway_minus_target", ci_key="pmt_ci95", min_reps=5)

    print("per-group guards against the real R167 data\n")
    print("  groups total          %d" % rep["n_groups_total"])
    print("  kept (>=5 splits)     %d" % len(rep["kept"]))
    print("  dropped (<5 splits)   %d  -> %s" % (len(rep["dropped"]), rep["dropped"]))
    print("  degenerate intervals  %d  -> %s" % (len(rep["degenerate_intervals"]), rep["degenerate_intervals"]))
    print("  usable                %d" % len(rep["usable"]))
    print("  INTERVAL reversals    %d  -> %s" % (len(rep["interval_reversals"]), rep["interval_reversals"]))
    print("  sign-only negatives   %d  -> %s" % (len(rep["sign_only_negatives"]), rep["sign_only_negatives"]))
    print()
    print("  what a sign-counting gate would have said : reversal in %d groups" % len(rep["sign_only_negatives"]))
    print("  what the intervals support                : reversal in %d groups" % len(rep["interval_reversals"]))

    h400 = (len(rep["dropped"]) == 1
            and rep["dropped"] == ["JNK and p38 signaling"]
            and len(rep["degenerate_intervals"]) >= 1
            and len(rep["interval_reversals"]) == 0)
    print("\nH400 guards reproduce the corrected conclusion:", h400)

    res = {"kind": "validate_per_group_guards_against_R167",
           "inputs": {"e167": sha256(E167)},
           "settings": {"min_reps": 5, "ci_tol": 1e-9},
           "result": rep,
           "comparison": {"sign_counting_gate_would_find": len(rep["sign_only_negatives"]),
                          "intervals_support": len(rep["interval_reversals"]),
                          "overstatement_factor": (len(rep["sign_only_negatives"])
                                                    / max(1, len(rep["interval_reversals"])))},
           "decisions": {"H400_guards_reproduce_the_corrected_conclusion": bool(h400),
                         "H401_inconsistent": not h400},
           "decisions_verdict": (
               "the_guards_drop_the_single_split_group_flag_the_degenerate_interval_and_report_no_reversal"
               if h400 else "the_guards_do_not_reproduce_the_corrected_conclusion"),
           "limits": ["Validated on the 21 groups of E167 only; correctness on other data shapes is untested.",
                     "The min_reps of five is chosen, not optimised.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r168/PROTOCOL_E156.md",
                "research/2026-10-27-agent-cell-identifiability-r168/e168_validate_guards.py",
                "research/tools/effect_audit.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E168_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("written E168_RESULTS.json")


if __name__ == "__main__":
    main()
