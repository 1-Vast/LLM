"""Write RUN_MANIFEST.json: SHA-256 and size of every file in the study directory and of the cached arrays."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[2] / "data/external/tahoe_zeroshot_20261007"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main():
    study = {str(p.relative_to(HERE)).replace("\\", "/"): {"bytes": p.stat().st_size, "sha256": sha(p)}
             for p in sorted(HERE.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name != "RUN_MANIFEST.json"}
    cache = {}
    for p in sorted(CACHE.rglob("*")):
        if p.is_file() and "blocks" not in p.parts and "superseded" not in "/".join(p.parts):
            entry = {"bytes": p.stat().st_size}
            if p.stat().st_size < 3_000_000_000:
                entry["sha256"] = sha(p)
            else:
                entry["sha256"] = None
                entry["note"] = "large raw-row memmap; its content hash is rows_sha256 in extract/<file>.receipt.json"
            cache[str(p.relative_to(CACHE)).replace("\\", "/")] = entry
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "study_files": study, "cache_root": str(CACHE),
                "cache_files": cache, "excluded": "HTTP block cache (data/external/tahoe_zeroshot_20261007/blocks) and superseded forecast arrays"}
    (HERE / "RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(len(study), "study files;", len(cache), "cache files")


if __name__ == "__main__":
    main()
