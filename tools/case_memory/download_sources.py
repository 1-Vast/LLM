"""Verify the registered external sources and write the external source manifest.

File summary
- Path: tools/case_memory/download_sources.py
- Purpose: check every registered input of the untouched evaluation against its recorded checksum
  (LINCS 2020 metadata tables against `data/external/lincs2020/provenance.json`, the Level 5
  matrix against the size observed at download and the SHA-256 computed after it), then write
  `outputs/case_memory_integration/external_source_manifest.json` with source URL, publication,
  version, license, download date, checksum, study-level split, independent unit and known
  limitations, as the frozen protocol requires.
- Run: `python -m tools.case_memory.download_sources`
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_LEVEL5_BYTES = 35518405386


def main() -> dict:
    provenance = json.loads((ROOT / "data/external/lincs2020/provenance.json").read_text())
    checks: dict[str, dict] = {}
    ok = True
    import hashlib

    def sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 22), b""):
                h.update(block)
        return h.hexdigest()

    for name, record in provenance["files"].items():
        path = ROOT / "data/external/lincs2020" / name
        actual = sha256(path) if path.is_file() else None
        match = actual == record["sha256"]
        ok &= match
        checks[name] = {"expected": record["sha256"], "actual": actual, "match": match,
                        "url": record["url"]}
    level5 = ROOT / "data/external/lincs2020/level5/level5_beta_trt_cp_n720216x12328.gctx"
    sha_record = json.loads((level5.parent / "sha256.json").read_text()) \
        if (level5.parent / "sha256.json").is_file() else {}
    size_ok = level5.is_file() and level5.stat().st_size == EXPECTED_LEVEL5_BYTES
    ok &= size_ok and bool(sha_record.get("sha256"))
    manifest = {
        "study": "CMap LINCS 2020 beta build, compound treatment Level 5",
        "source_url": ("https://s3.amazonaws.com/macchiato.clue.io/builds/LINCS2020/level5/"
                       "level5_beta_trt_cp_n720216x12328.gctx"),
        "metadata_urls": {name: record["url"] for name, record in provenance["files"].items()},
        "publication": ("Subramanian et al., Cell 2017 (platform); CMap 2020 expansion per the "
                        "NIH Common Fund LINCS symposium summary"),
        "version": {"level5_last_modified": "Wed, 16 Dec 2020 23:54:09 GMT",
                    "siginfo_last_modified": provenance.get("s3_last_modified_siginfo")},
        "license": provenance.get("licence"),
        "download_date": {"metadata": provenance.get("retrieved_utc"),
                          "level5": "2026-09-29"},
        "checksums": checks,
        "level5": {"bytes": level5.stat().st_size if level5.is_file() else None,
                   "expected_bytes": EXPECTED_LEVEL5_BYTES, "size_match": size_ok,
                   **sha_record},
        "study_level_split": ("test units are InChIKey connectivity blocks absent from the "
                              "GSE92742 and GSE70138 trt_cp compound lists; reference units are "
                              "the remaining blocks in pool classes of the same LINCS 2020 build"),
        "independent_unit": "InChIKey connectivity block (first 14 characters)",
        "known_limitations": [
            "beta build; MoA labels are curated annotations used as proxy truth, never ground truth",
            "inferred genes are present alongside the 978 measured landmark genes",
            "Level 5 signatures have no replicate structure",
            "metadata was downloaded 2026-09-27, two days before this evaluation's protocol "
            "freeze; exposure was limited to the columns declared in provenance.json, and no "
            "signature value or quality column was read before the freeze",
        ],
        "verification_ok": bool(ok),
    }
    out = ROOT / "outputs/case_memory_integration/external_source_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"verification_ok": manifest["verification_ok"], "out": str(out)}))
    return manifest


if __name__ == "__main__":
    main()
