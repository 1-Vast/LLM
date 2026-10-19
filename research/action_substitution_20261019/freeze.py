"""Write FREEZE.json: EOL-normalised SHA-256 of the phase-2 protocol and code, plus the source data checksum."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import cas_data as D

HERE = Path(__file__).resolve().parent
FILES = ["PLAN_P1.md", "PROTOCOL_P2.md", "lofo.py", "repro.py", "cas_data.py", "census.py", "CENSUS.json", "REPRO.json", "DECOMP.json"]


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


if __name__ == "__main__":
    out = HERE / "FREEZE.json"
    if out.exists():
        raise SystemExit("FREEZE.json exists")
    rec = dict(frozen_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), scope="phase 2 (lofo.py) before any held-out prediction was computed",
               eol="sha256 over bytes with CRLF normalised to LF", files={f: digest(HERE / f) for f in FILES},
               data={D.ORIGINAL.name: dict(md5=D.MD5_ORIGINAL), D.VALIDATION.name: dict(sha256=D.sha256(D.VALIDATION))},
               smoke="lofo.py --smoke ran two folds (Camptothecin 0 cells, Docetaxel 2251/66 cells), counts and finiteness only")
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(rec, indent=1))
