"""Independently compare every pre-task study byte with the registered snapshot."""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    baseline = root / "research/astra/agent_closed_loop_20261007/PRIOR_PRESERVATION.json"
    receipt = json.loads(baseline.read_text(encoding="utf-8"))
    missing, changed = [], []
    for relative, expected in receipt["files"].items():
        path = root / relative
        if not path.is_file():
            missing.append(relative)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            changed.append(relative)
    result = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "checked_files": len(receipt["files"]),
        "missing": missing, "changed": changed,
        "verdict": "PASS" if not missing and not changed else "FAIL",
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result))
    if result["verdict"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
