"""Pin the post hoc audit before first numerical parsing of historical records."""
from datetime import datetime, timezone
from pathlib import Path

from historical_choice_audit import LOG, ROOT, sha, write


def main():
    if (LOG / "HISTORICAL_AUDIT_STARTED.json").exists():
        raise RuntimeError("Audit has already started")
    names = [
        "log/20261022/update_value_qualification/HISTORICAL_AUDIT_PROTOCOL.md",
        "log/20261022/update_value_qualification/HISTORICAL_AUDIT_SYNTHETIC_01.txt",
        "research/update_value_qualification_20261022/historical_choice_audit.py",
        "research/update_value_qualification_20261022/test_historical_choice_audit.py",
        "research/update_value_qualification_20261022/freeze_historical.py",
        "research/feedback_propagation_20261018/compare.py",
        "research/feedback_propagation_20261018/bench.py",
        "research/feedback_propagation_20261018/loop.py",
        "research/feedback_propagation_20261018/metrics.py",
        "research/feedback_propagation_20261018/THRESHOLDS.json",
        "research/eg_rpt_20261019/NOISE_HEADROOM.json",
    ] + [f"research/feedback_propagation_20261018/records/E_fold{fold}.json" for fold in (2, 3, 4)]
    write(LOG / "HISTORICAL_AUDIT_FREEZE.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "files": {name: sha(ROOT / name) for name in names},
        "scope": "post hoc already-exposed score audit; raw/protected/reserve responses unopened",
    })
    print("Frozen historical audit: " + str(len(names)) + " files")


if __name__ == "__main__":
    main()
