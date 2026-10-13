"""Write or check FREEZE.json: SHA-256 of the protocol, code, S0/S1 results, power and input assets.

File summary
- Path: research/orbit_contrast_20261013/freeze.py
- Purpose: lock everything S2 depends on before S2 runs. Text files are hashed with CRLF normalised
  to LF (the repository stores LF); binary assets are hashed raw. DEVIATIONS.json is listed as not
  hashed, so recording a later deviation never breaks the freeze.
- Schema: `sha256` (checkout-relative path -> digest), supported by tools/research_validation.py.
- Commands: `python freeze.py write` (once, after S1), `python freeze.py check`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = HERE.relative_to(ROOT).as_posix()
TEXT = (".md", ".py", ".json", ".txt", ".csv")
CODE = ("PROTOCOL.md", "LITERATURE.md", "CANDIDATES.md", "INTERFACE.md", "evidence.py", "sources.py", "routes.py",
        "ocea.py", "synthetic.py", "run.py", "freeze.py", "verdict.py", "RESULTS_S0.json", "RESULTS_S1.json", "POWER.json")
ASSETS = ("data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz",
          "data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz",
          "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt",
          "data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv",
          "data/external/mapkg_20261009/GENE_tahoe_filtered.csv",
          "data/external/map_module_replacement_20261009/PROTEIN_FEATURES.npz")
NOT_HASHED = ("DEVIATIONS.json", "FREEZE.json", "RESULTS.json", "README.md", "verify.py")


def digest(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix in TEXT and not path.name.endswith(".gz"):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def targets() -> list[str]:
    return [f"{STUDY}/{n}" for n in CODE] + list(ASSETS)


def write() -> None:
    path = HERE / "FREEZE.json"
    if path.exists():
        raise SystemExit("FREEZE_EXISTS: the freeze is written once")
    freeze = {"locked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "purpose": "Lock protocol, code, S0/S1 results, power and inputs before the single S2 validation run.",
              "not_hashed": [f"{STUDY}/{n}" for n in NOT_HASHED],
              "sha256": {t: digest(ROOT / t) for t in targets()}}
    path.write_text(json.dumps(freeze, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"FREEZE written: {len(freeze['sha256'])} files")


def require_freeze() -> dict:
    path = HERE / "FREEZE.json"
    if not path.is_file():
        raise SystemExit("FREEZE_MISSING: S2 needs FREEZE.json")
    freeze = json.loads(path.read_text(encoding="utf-8"))
    bad = [t for t, d in freeze["sha256"].items() if not (ROOT / t).is_file() or digest(ROOT / t) != d]
    if bad:
        raise SystemExit("FREEZE_MISMATCH: " + ", ".join(bad))
    return freeze


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "write":
        write()
    else:
        f = require_freeze()
        print(f"FREEZE OK: {len(f['sha256'])} files")
