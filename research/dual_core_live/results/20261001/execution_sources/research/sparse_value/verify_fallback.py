"""Replay exactly the 32 recorded fallback-first early stops without rewriting the frozen run."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "sequence_audit"))
import lincs_evaluate as LE

P, C, E, LP = LE.P, LE.C, LE.E, LE.LP
SOURCE = LE.OUT / "episodes" / "episodes.jsonl"
OUT = ROOT / "outputs" / "sparse_value" / "fallback"


def main():
    source_bytes = SOURCE.read_bytes()
    historical = [json.loads(line) for line in source_bytes.splitlines()]
    affected = [row for row in historical if row["tier"] == "LT" and row["policy"] == "two_step_fallback"
                and row["stop"] == "no_supported_positive_utility_continuation:implementation_defect"]
    assert len(affected) == 32, f"Expected 32 frozen LT cases, found {len(affected)}"
    data, tier = LP.load(), LP.tiers()["LT"]
    setting = LP.setting(tier)
    detected, spec = data.conditions.detected.to_numpy(bool), C.load_protocol()
    proofs = []
    for fold in sorted({row["fold"] for row in affected}):
        ctx = LE.context(data, tier, fold, detected, spec)
        for old in (row for row in affected if row["fold"] == fold):
            args = (ctx, old["compound"], old["truth"], old["h1"], old["h2"], setting)
            legacy = P.run_matched("two_step_fallback", P.arms("l1000", frozen_replay=True)["two_step_fallback"],
                                   *args, qc_rule=old["qc_rule"])
            assert legacy == {key: old[key] for key in legacy}, "Frozen legacy episode did not reproduce"
            repaired = P.run_matched("two_step_fallback", P.arms("l1000")["two_step_fallback"],
                                     *args, qc_rule=old["qc_rule"])
            assert not P.audit_record(repaired, setting)
            assert legacy["steps"] == repaired["steps"][:1], "The repair changed the first measurement"
            assert repaired["measurements"] == 2
            assert repaired["steps"][1]["note"]["replanned_from"] == legacy["steps"][0]["action"]
            proofs.append({"fold": fold, "compound": old["compound"], "h1": old["h1"], "h2": old["h2"],
                           "before": legacy, "after": repaired})
        print(f"LT fold {fold}: {sum(row['fold'] == fold for row in proofs)} defects replayed", flush=True)
    summary = {
        "scope": "32 previously observed LT implementation defects; regression proof, not independent efficacy evidence",
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "legacy_exact_matches": len(proofs), "repaired_continuations": len(proofs),
        "before": dict(Counter(row["before"]["final"] for row in proofs)),
        "after": dict(Counter(row["after"]["final"] for row in proofs)),
        "extra_measurements": sum(row["after"]["measurements"] - row["before"]["measurements"] for row in proofs),
        "extra_assay_days": sum(row["after"]["days"] - row["before"]["days"] for row in proofs),
        "utility_change": sum(row["after"]["utility"] - row["before"]["utility"] for row in proofs),
        "code_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in (Path(__file__), Path(P.__file__))},
    }
    assert SOURCE.read_bytes() == source_bytes, "Historical records were modified"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "episodes.json").write_text(json.dumps(proofs, indent=2), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
