"""Generate the content manifest for dated experiment logs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "log"


def build_manifest() -> dict:
    days = []
    for directory in sorted(
        path for path in LOG.iterdir()
        if path.is_dir() and path.name.isdigit() and (path / "README.md").is_file()
    ):
        files = []
        for path in sorted(item for item in directory.rglob("*") if item.is_file()):
            content = path.read_bytes()
            files.append({
                "path": path.relative_to(LOG).as_posix(),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            })
        days.append({"date": directory.name, "files": files})
    return {"schema_version": 1, "days": days}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest_path = LOG / "MANIFEST.json"
    expected = json.dumps(build_manifest(), indent=2) + "\n"
    if args.check:
        if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != expected:
            print("log/MANIFEST.json is stale; run python -m tools.log_manifest")
            return 1
        print("log/MANIFEST.json is current")
        return 0
    manifest_path.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
