"""Write FREEZE.json: EOL-normalised SHA-256 of the P0 protocol and code, plus the imported frozen study files."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AS = HERE.parent / "action_substitution_20261019"
OWN = ["PROTOCOL.md", "p0.py", "audit.py", "AUDIT.json"]
IMPORTED = ["lofo.py", "repro.py", "cas_data.py", "CENSUS.json", "lofo_units_SYNERGY_DELTA_AUC.csv",
            "lofo_units_SYNERGY_OBS_AUC.csv", "REFINE_SYNERGY_DELTA_AUC.json"]


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


if __name__ == "__main__":
    out = HERE / "FREEZE.json"
    if out.exists():
        raise SystemExit("FREEZE.json exists")
    assert not (HERE / "P0_RESULT.json").exists(), "result already exists"
    rec = dict(frozen_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               scope="P0 gate before p0.py ran (smoke on 6 implementations: execution and B5 reproduction only)",
               eol="sha256 over bytes with CRLF normalised to LF",
               files={f: digest(HERE / f) for f in OWN},
               imported={f"../action_substitution_20261019/{f}": digest(AS / f) for f in IMPORTED},
               source_md5="786589e5eb556670cc7d24356487f8fd")
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(rec, indent=1))
