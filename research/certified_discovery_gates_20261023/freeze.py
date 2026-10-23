"""Write FREEZE.json before any response value is converted. Refuses to overwrite an existing freeze.

`files` are enforced by common.require_freeze (any later change needs a DEVIATIONS.md entry naming the file);
`references` are recorded only. DEVIATIONS.md is never hashed here."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy  # noqa: E402
import pandas  # noqa: E402
import scipy  # noqa: E402

from common import (AZ_DESIGN, AZ_ZIP, CERTIFICATION, DATA, HERE, JAAKS_ORIGINAL, JAAKS_RAW, JAAKS_VALIDATION, OUT,  # noqa: E402
                    ROOT, sha, sha_lf, write_json)

EVIDENCE = ["PROTOCOL.md", "START.md", "CENSUS.json", "SYNTHETIC_TESTS.txt"]
REFERENCES = [ROOT / "log/20261023/forward_perspective/PERSPECTIVE.md"]


def entry(path):
    path = Path(path)
    return {"sha256": sha(path), "sha256_lf": sha_lf(path) if path.stat().st_size < 50_000_000 else None,
            "bytes": path.stat().st_size}


def main():
    target = OUT / "FREEZE.json"
    if target.exists():
        raise SystemExit("FREEZE.json already exists; record changes in DEVIATIONS.md instead")
    responses = [str(p) for base in (OUT, DATA) for p in base.glob("DATA_*.npz")]
    if responses:
        raise SystemExit(f"response files already exist, so this would not be a pre-response freeze: {responses}")
    enforced = [OUT / name for name in EVIDENCE] + sorted(HERE.glob("*.py")) + [CERTIFICATION, AZ_DESIGN]
    inputs = [AZ_ZIP, JAAKS_ORIGINAL, JAAKS_VALIDATION, JAAKS_RAW]
    record = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "statement": ("Written before prepare.py, the first step of this study that converts a response value. "
                      "CENSUS.json read identity and layout fields only."),
        "python": sys.version.split()[0], "platform": platform.platform(),
        "numpy": numpy.__version__, "scipy": scipy.__version__, "pandas": pandas.__version__,
        "files": {str(p.relative_to(ROOT)).replace("\\", "/"): entry(p) for p in enforced + inputs},
        "references": {str(p.relative_to(ROOT)).replace("\\", "/"): entry(p) for p in REFERENCES if p.exists()},
    }
    write_json(target, record)
    print(json.dumps({"files": len(record["files"]), "frozen_at_utc": record["frozen_at_utc"]}))


if __name__ == "__main__":
    main()
