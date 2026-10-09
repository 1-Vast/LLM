from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cleanup/CLEANUP_MANIFEST.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = manifest["planned_deletions"]
    for row in rows:
        path = ROOT / Path(row["path"])
        if not path.is_file():
            raise SystemExit(f"Refusing deletion; planned file changed: {row['path']}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != row["sha256"]:
            raise SystemExit(f"Refusing deletion; planned file changed: {row['path']}")
    for start in range(0, len(rows), 100):
        batch = [row["path"] for row in rows[start:start + 100] if row["commit_blob"]]
        if not batch:
            continue
        subprocess.run(["git", "rm", "-f", "--", *batch], cwd=ROOT, check=True)
    for row in rows:
        if row["commit_blob"]:
            continue
        (ROOT / Path(row["path"])).unlink()
    print(f"Removed {len(rows)} files, {sum(row['size_bytes'] for row in rows)} bytes")


if __name__ == "__main__":
    main()
