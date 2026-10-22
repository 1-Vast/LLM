"""Freeze protocol, implementation, synthetic results, and bytes before projection."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"


def main():
    target = OUT / "PRE_OPEN_FREEZE.json"
    if target.exists():
        raise RuntimeError("Freeze already exists")
    paths = sorted((ROOT / "research/tggates_functional_qualification_20261022").glob("*.py"))
    paths += [OUT / "PROTOCOL.md", OUT / "NETWORK.json", OUT / "SYNTHETIC_TESTS.txt",
              OUT / "sealed_source/open_tggates_cell_viability.zip"]
    paths += [ROOT / "log/20261022/tggates_source_qualification" / name for name in
              ["HUMAN_CELL_IDENTITIES.json", "HUMAN_CEL_IDENTITIES.json", "TEMPORAL_IDENTITY.json", "README_e.html"]]
    for path in paths:
        if not path.is_file():
            raise RuntimeError("Required frozen file missing")
    result = {"frozen_utc": datetime.now(timezone.utc).isoformat(),
              "official_response_rows_inspected_before_freeze": False,
              "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PRE_OPEN_FROZEN", "files": len(paths)}))


if __name__ == "__main__":
    main()
