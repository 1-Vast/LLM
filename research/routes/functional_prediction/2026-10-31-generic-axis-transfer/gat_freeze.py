"""Write FREEZE.json for the GAT study (run once, before the 24Q2 outcome matrix is downloaded).

Usage: python gat_freeze.py
Binds the protocol, development log, run code, built inputs and source files by SHA-256. Text files also get a
digest with CRLF normalised to LF, so a checkout under eol=lf still verifies.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import subprocess
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/MAESTRO")
DATA = ROOT / "data/processed/generic_axis_transfer_20261031"
EXT = ROOT / "data/external"
TEXT = {".md", ".py", ".txt", ".tsv", ".csv", ".json", ".log", ".out"}
LARGE = 4 * 1024 ** 3


def digest(path: Path) -> dict:
    if path.stat().st_size > LARGE:
        st = path.stat()
        return {"bytes": st.st_size, "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.UTC).isoformat(),
                "sha256": None, "note": "too large to hash at freeze; the extracted arrays below are hashed"}
    raw = path.read_bytes()
    out = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if path.suffix in TEXT:
        out["sha256_lf"] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return out


def bind(paths: list[Path], base: Path) -> dict:
    return {p.relative_to(base).as_posix(): digest(p) for p in paths}


def main() -> None:
    study = [HERE / n for n in ("PROTOCOL.md", "DEV_LOG.md", "gat_core.py", "gat_data.py", "gat_run.py", "gat_freeze.py")]
    dev = sorted(p for p in (HERE / "dev").rglob("*") if p.is_file())
    data = sorted(p for p in DATA.iterdir() if p.is_file())
    l1000 = EXT / "lincs_l1000_gse92742"
    sources = [
        EXT / "prism_19q4/derived/block_n_prism_open.npz",
        EXT / "prism_19q4/derived/block_n_prism_sealed.npz",
        EXT / "prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv",
        EXT / "prism_19q4/raw/secondary-screen-replicate-collapsed-treatment-info.csv",
        l1000 / "derived/block_m_landmark_open.npz",
        l1000 / "derived/block_m_landmark_sealed.npz",
        l1000 / "GSE92742_Broad_LINCS_pert_info.txt.gz",
        l1000 / "GSE92742_Broad_LINCS_sig_info.txt.gz",
        l1000 / "GSE92742_Broad_LINCS_sig_metrics.txt.gz",
        l1000 / "GSE92742_Broad_LINCS_gene_info.txt.gz",
        l1000 / "GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx",
        EXT / "nci60_cellminer_20261031/raw/DTP_NCI60_ZSCORE.zip",
        EXT / "nci60_cellminer_20261031/raw/DTP_NCI60_RAW.zip",
        EXT / "nci60_cellminer_20261031/raw/extracted/output/DTP_NCI60_ZSCORE.xlsx",
        EXT / "nci60_cellminer_20261031/raw/extracted_raw/output/DTP_NCI60_RAW.xlsx",
        *sorted((EXT / "prism_24q2_20261031/meta").iterdir()),
        ROOT / "log/research_records/knowledge_reality_20261013/sealed_compounds.csv",
        ROOT / "src/virtual_cell/transcriptional_transfer.py",
    ]
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    record = {
        "study": "generic_axis_transfer_20261031",
        "frozen_at_utc": datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat(),
        "repository_head": head,
        "study_files": bind(study, HERE),
        "development_files": bind(dev, HERE),
        "built_inputs": bind(data, ROOT),
        "sources": bind(sources, ROOT),
        "sealed_outcome_expected": {
            "file": "data/external/prism_24q2_20261031/matrix/Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv",
            "source": "https://ndownloader.figshare.com/files/46630984 (figshare article 25917643)",
            "md5": "042b15d3ebcc138a80a571b9286451ae",
            "downloaded_before_freeze": False,
        },
        "software": {"python": platform.python_version(),
                     **{p: metadata.version(p) for p in ("numpy", "pandas", "scipy", "rdkit", "openpyxl")}},
    }
    (HERE / "FREEZE.json").write_bytes((json.dumps(record, indent=1) + "\n").encode("utf-8"))
    print(record["frozen_at_utc"], len(record["study_files"]), len(record["development_files"]),
          len(record["built_inputs"]), len(record["sources"]))


if __name__ == "__main__":
    main()
