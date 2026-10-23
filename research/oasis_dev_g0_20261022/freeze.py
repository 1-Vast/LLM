"""Pin pre-opening inputs and code; refuse replacing the registered freeze."""
from pathlib import Path
import hashlib
import json
import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/oasis_dev_g0"


def main():
    destination = OUT / "PRE_OPEN_FREEZE.json"
    if destination.exists():
        raise RuntimeError("Freeze exists; do not replace")
    files = [OUT / "PROTOCOL.md",
        ROOT / "log/20261021/oasis_evaluation_contract/RESERVATION_v2.json",
        ROOT / "log/20261021/oasis_evaluation_contract/DUPLICATE_READ_CONSISTENCY.json",
        ROOT / "log/20261021/oasis_identity_qualification/IDENTITY_ROWS.json",
        ROOT / "log/20261021/oasis_identity_qualification/PAIRED_IDENTITIES.json",
        ROOT / "log/20261021/oasis_identity_qualification/NEW_SOURCE_MANIFEST.json",
        ROOT / "log/20261021/oasis_source_qualification/SOURCE_MANIFEST.json"]
    source = json.loads(files[-1].read_text())
    files += [ROOT / x["local_path"] for x in source]
    sources = json.loads((ROOT / "log/20261021/oasis_identity_qualification/NEW_SOURCE_MANIFEST.json").read_text())
    files += [ROOT / x["local_path"] for x in sources["files"]]
    files += list(Path(__file__).parent.glob("*.py"))
    mapping = {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted(set(files))}
    record = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "files": mapping,
              "dev_numeric_export_exists": (OUT / "dev_wells.parquet").exists(),
              "numeric_opening_authorised_after_freeze": "Dev and exact DMSO only; no other role export"}
    if record["dev_numeric_export_exists"]:
        raise RuntimeError("Cannot register before-opening freeze after export")
    destination.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(mapping), "utc": record["utc"], "dev_numeric_export_exists": False}))


if __name__ == "__main__":
    main()
