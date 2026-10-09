from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cleanup/CLEANUP_MANIFEST.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in manifest["planned_deletions"] if row["commit_blob"] is None]
    for row in rows:
        path = ROOT / Path(row["path"])
        if not path.exists():
            continue
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or digest(path) != row["sha256"]:
            raise SystemExit(f"Refusing local-output deletion; file changed: {row['path']}")
    for row in rows:
        path = ROOT / Path(row["path"])
        if not path.exists():
            continue
        if path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        path.unlink()
    print(f"Removed {len(rows)} local outputs, {sum(row['size_bytes'] for row in rows)} bytes")


if __name__ == "__main__":
    main()
