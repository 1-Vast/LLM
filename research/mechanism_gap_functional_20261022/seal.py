"""Seal methods/header-only assessment; no scientific data are loaded."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BASE = Path("log/20261022/mechanism_gap/functional")
CODE = Path("research/mechanism_gap_functional_20261022")


if __name__ == "__main__":
    soft = (BASE / "GSE233766.samples.soft").read_text(encoding="utf-8")
    assert soft.count("^SAMPLE = ") == 22
    assert "!sample_table_begin" not in soft.lower()
    assert "GSM7434421" in soft and "GSM7434422" in soft
    names = json.loads((BASE / "FM07_header.zip_names.json").read_bytes())
    assert len(names) == 54
    assert any("989-Cont_S1_L001_R1" in name for name in names)
    assert any("989-Discont_S2_L001_R1" in name for name in names)
    gdna = json.loads((BASE / "processed_gDNA.zip_names.json").read_bytes())
    assert any("gDNA_BarcodeData/FM02/" in name for name in gdna)
    assert not any("FM07" in name for name in gdna)
    primary = json.loads((BASE / "PMC10628994.pmc.receipt.json").read_bytes())
    assert primary["status"] == 200
    files = sorted([p for folder in (BASE, CODE) for p in folder.iterdir()
                    if p.is_file() and p.name != "INDEPENDENT_SEAL.json"])
    seal = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "status": "SOURCE_PARTIALLY_QUALIFIED_REQUESTED_LATER_DECISION_NOT_QUALIFIED",
        "mechanistic_operations_proposed": 0,
        "keyword_queries": 4,
        "successful_new_primary_bodies": 2,
        "current_peer_drafts_read_before_seal": False,
        "raw_numerical_outcomes_decoded": False,
        "protected_holdouts_opened": False,
        "checks": "22 GEO sample headers, no sample outcome table; 54 FM07 ZIP entries; FM02 gDNA present and FM07 absent in inspected directory",
        "files": [{"path": p.as_posix(), "bytes": p.stat().st_size,
                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
    }
    (BASE / "INDEPENDENT_SEAL.json").write_text(
        json.dumps(seal, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in seal.items() if key != "files"}, indent=2))
