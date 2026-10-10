"""Re-stage the pinned STATE zero-shot checkpoint files that were absent on 2026-10-10.

Every file must match the SHA-256 recorded in the 2026-10-07 zero-shot SOURCE_MANIFEST; a mismatch
deletes the download and stops. Nothing else under data/external/arc_state is touched.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = ROOT / "research/astra/zeroshot_context_20261007/SOURCE_MANIFEST.json"
REPO, SUBDIR = "arcinstitute/ST-HVG-Tahoe", "zeroshot/state_generalization_zeroshot_X_hvg"
DEST = ROOT / "data/external/arc_state/weights" / SUBDIR


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main():
    checkpoint = json.loads(MANIFEST.read_text(encoding="utf-8"))["checkpoint"]
    revision = checkpoint["revision"]
    wanted = {
        "checkpoints/final.ckpt": checkpoint["local"]["sha256"],
        "pert_onehot_map.pt": checkpoint["pert_onehot_map"]["sha256"],
        "var_dims.pkl": checkpoint["var_dims"]["sha256"],
        "config.yaml": checkpoint["config"]["sha256"],
    }
    receipts = []
    for rel, expected in wanted.items():
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not (target.exists() and sha256(target) == expected):
            url = f"https://huggingface.co/{REPO}/resolve/{revision}/{SUBDIR}/{rel}"
            started = time.perf_counter()
            part = target.with_suffix(target.suffix + ".part")
            for attempt in range(1, 7):
                try:
                    with requests.get(url, stream=True, timeout=300) as response:
                        response.raise_for_status()
                        with part.open("wb") as handle:
                            for chunk in response.iter_content(1 << 22):
                                handle.write(chunk)
                    break
                except requests.RequestException:
                    if attempt == 6:
                        raise
                    time.sleep(5 * attempt)
            actual = sha256(part)
            if actual != expected:
                part.unlink()
                raise SystemExit(f"{rel}: sha256 {actual} differs from pinned {expected}")
            part.replace(target)
            seconds = round(time.perf_counter() - started, 1)
        else:
            seconds = 0.0
        receipts.append({"file": rel, "repo": REPO, "revision": revision, "sha256": expected,
                         "bytes": target.stat().st_size, "seconds": seconds,
                         "verified_utc": datetime.now(timezone.utc).isoformat()})
        print(json.dumps(receipts[-1]), flush=True)
    (HERE / "STATE_STAGING.json").write_text(json.dumps(receipts, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
