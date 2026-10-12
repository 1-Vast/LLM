"""Freeze and verification for block Q: hashes of every file the confirmation depends on.

Text files are hashed with line endings normalised to LF, so a Windows checkout cannot break the
freeze. ``DEVIATIONS.json`` is deliberately not frozen: it is written after the freeze.
Usage: python verify_freeze.py --write (once, before the confirmation)  |  python verify_freeze.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FREEZE = HERE / "FREEZE.json"
TEXT = {".py", ".md", ".json", ".txt", ".csv", ".yaml", ".toml"}

CODE = ["rkt.py", "engine.py", "pool.py", "campaign.py", "metrics.py", "llm_arms.py", "confirm.py", "knowledge.py",
        "dev_common.py", "dev_routes2.py", "dev_mono2.py", "extract_phase1.py", "extract_phase2.py",
        "extract_knowledge2.py", "verify_freeze.py", "verify.py", "PROTOCOL.md", "PROTOCOL.json", "DISCLOSURE.md"]
DATA = ["cache/dev2_routes.npz", "cache/phase1_knowledge.npz", "cache/phase2_knowledge.json", "cache/pooler_all.pkl",
        "extract_phase1.json", "extract_phase2.json"]
EXTERNAL = ["data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz",
            "data/external/lincs_l1000_phase2/derived/blockq_phase2_reference.npz",
            "data/external/lincs_l1000_phase2/derived/blockq_phase2_query_SEALED.npz",
            "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt",
            "data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv",
            "data/external/mapkg_20261009/GENE_tahoe_filtered.csv",
            "src/agent/llm.py", "tools/evaluation/scoring.py", "tools/evaluation/costs.py"]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    if path.suffix.lower() in TEXT:
        h.update(path.read_bytes().replace(b"\r\n", b"\n"))
    else:
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 24), b""):
                h.update(block)
    return h.hexdigest()


def frozen_paths() -> dict[str, Path]:
    out = {f: HERE / f for f in CODE + DATA}
    out.update({f: ROOT / f for f in EXTERNAL})
    return out


def write() -> None:
    if FREEZE.exists():
        raise RuntimeError("FREEZE_EXISTS: a freeze is written once")
    files = {name: digest(p) for name, p in frozen_paths().items()}
    rec = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": files,
           "not_frozen": ["DEVIATIONS.json", "results/"], "hash_rule": "sha256; text files with CRLF normalised to LF"}
    FREEZE.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(f"FREEZE.json written: {len(files)} files")


def check() -> dict:
    if not FREEZE.exists():
        raise RuntimeError("NOT_FROZEN")
    rec = json.loads(FREEZE.read_text(encoding="utf-8"))
    bad = [name for name, p in frozen_paths().items() if name not in rec["files"] or digest(p) != rec["files"][name]]
    if bad:
        raise RuntimeError("FREEZE_MISMATCH: " + ", ".join(bad))
    return rec


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
    else:
        print(json.dumps({"ok": True, "frozen_utc": check()["frozen_utc"]}))
