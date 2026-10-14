"""Authenticate the external assets a full replay of this study would read, against upstream digests where they exist.

Statuses (never collapsed): VERIFIED (matches a published upstream digest), LOCAL_DIGEST_ONLY (no upstream digest
exists, so the local sha256 only pins the bytes used), MISMATCH, ASSET_MISSING. A replay that needs an asset in any
status but VERIFIED or LOCAL_DIGEST_ONLY must report BLOCKED/ASSET_MISSING, never success.

    python research/mechanism_falsification_20261014/authenticate_assets.py            # small files
    python research/mechanism_falsification_20261014/authenticate_assets.py --large    # also the 21 GB and 5 GB archives
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
P1, P2 = ROOT / "data/external/lincs_l1000_gse92742", ROOT / "data/external/lincs_l1000_phase2"
UPSTREAM = {"GSE92742": (P1 / "GSE92742_SHA512SUMS.txt.gz", P1), "GSE70138": (P2 / "meta/GSE70138_SHA512SUMS.txt.gz", P2 / "meta")}
SMALL = [("GSE92742", P1 / "GSE92742_Broad_LINCS_sig_info.txt.gz"), ("GSE92742", P1 / "GSE92742_Broad_LINCS_pert_info.txt.gz"),
         ("GSE92742", P1 / "GSE92742_Broad_LINCS_cell_info.txt.gz"), ("GSE92742", P1 / "GSE92742_Broad_LINCS_gene_info.txt.gz"),
         ("GSE92742", P1 / "GSE92742_Broad_LINCS_sig_metrics.txt.gz"),
         ("GSE70138", P2 / "meta/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz"), ("GSE70138", P2 / "meta/GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz"),
         ("GSE70138", P2 / "meta/GSE70138_Broad_LINCS_cell_info_2017-04-28.txt.gz")]
LARGE = [("GSE92742", P1 / "GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx.gz"),
         ("GSE70138", P2 / "GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx.gz")]
LOCAL_ONLY = [P1 / "repurposing_drugs_20200324.txt", P1 / "repurposing_samples_20200324.txt",
              ROOT / "data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv",
              ROOT / "data/external/mapkg_20261009/GENE_tahoe_filtered.csv"]


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def upstream_digests(sums: Path) -> dict[str, str]:
    out = {}
    if sums.is_file():
        for line in gzip.open(sums, "rt").read().splitlines():
            parts = line.split()
            if len(parts) == 2:
                out[parts[1].strip()] = parts[0].strip().lower()
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--large", action="store_true")
    args = parser.parse_args()
    reference = {k: upstream_digests(v[0]) for k, v in UPSTREAM.items()}
    rows = []
    for series, path in SMALL + (LARGE if args.large else []):
        record = {"series": series, "path": path.relative_to(ROOT).as_posix(), "algorithm": "sha512"}
        if not path.is_file():
            record["status"] = "ASSET_MISSING"
        else:
            record["bytes"] = path.stat().st_size
            record["sha512"] = digest(path, "sha512")
            expected = reference[series].get(path.name)
            record["upstream_sha512"] = expected
            record["status"] = "VERIFIED" if expected == record["sha512"] else ("MISMATCH" if expected else "NO_UPSTREAM_DIGEST")
        rows.append(record)
        print(record["status"], record["path"], flush=True)
    for path in LOCAL_ONLY:
        record = {"series": "annotation", "path": path.relative_to(ROOT).as_posix(), "algorithm": "sha256"}
        if path.is_file():
            record |= {"bytes": path.stat().st_size, "sha256": digest(path, "sha256"), "status": "LOCAL_DIGEST_ONLY"}
        else:
            record["status"] = "ASSET_MISSING"
        rows.append(record)
        print(record["status"], record["path"], flush=True)
    target = STUDY / ("ASSET_AUTH_LARGE.json" if args.large else "ASSET_AUTH.json")
    target.write_text(json.dumps({"large_included": args.large, "assets": rows}, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if all(r["status"] in ("VERIFIED", "LOCAL_DIGEST_ONLY") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
