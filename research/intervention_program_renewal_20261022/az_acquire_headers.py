"""Acquire one pinned public archive; inspect member names and CSV headers only."""
import csv
import hashlib
import io
import json
from pathlib import Path
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/az_design"
PROTOCOL = OUT.parent / "AZ_DESIGN_PROTOCOL.md"
EXPECTED_SIZE = 241088863
EXPECTED_MD5 = "ff3dab95ad59a1c956e3b11c397dcbd8"


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    started = OUT / "STARTED.json"
    if started.exists():
        raise RuntimeError("One acquisition invocation only; existing STARTED record")
    binding = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "code_sha256": digest(Path(__file__)),
        "protocol_sha256": digest(PROTOCOL),
        "expected_bytes": EXPECTED_SIZE,
        "expected_md5": EXPECTED_MD5,
        "target_numeric_use": False,
        "source_response_bytes_acquired": True,
    }
    started.write_text(json.dumps(binding, indent=2), encoding="utf-8")
    url = "https://ndownloader.figshare.com/files/45451363"
    archive = OUT / "matrix_well_stats_GDSC_007_010_plus_Spiper1.zip"
    completed = False
    session = requests.Session()
    for index in range(4):
        receipt = {"index": index, "url": url,
                   "utc": datetime.now(timezone.utc).isoformat(),
                   "automatic_retry": False, "automatic_redirect": False}
        count = 0
        then = time.monotonic()
        try:
            with session.get(url, timeout=30, stream=True, allow_redirects=False) as response:
                receipt.update(status=response.status_code, headers=dict(response.headers))
                redirect = response.status_code in (301, 302, 303, 307, 308)
                body = OUT / f"get_{index:02d}.body" if redirect or response.status_code != 200 else archive
                cap = 8 * 1024 * 1024 if body != archive else EXPECTED_SIZE
                with body.open("wb") as sink:
                    for block in response.iter_content(1024 * 1024):
                        if count + len(block) > cap:
                            raise RuntimeError("Response exceeds registered byte cap")
                        sink.write(block)
                        count += len(block)
                receipt.update(body=body.name, bytes=count, sha256=digest(body))
                if redirect:
                    url = urljoin(url, response.headers["Location"])
                elif response.status_code == 200:
                    completed = True
                else:
                    raise RuntimeError(f"HTTP {response.status_code}")
        except Exception as error:
            receipt.update(error=type(error).__name__ + ": " + str(error), partial_bytes=count)
            raise
        finally:
            receipt["elapsed_seconds"] = time.monotonic() - then
            (OUT / f"GET_{index:02d}.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            print(json.dumps({k: receipt[k] for k in ("index", "status", "bytes", "error") if k in receipt}), flush=True)
        if completed:
            break
    if not completed:
        raise RuntimeError("Explicit GET allocation exhausted")
    if archive.stat().st_size != EXPECTED_SIZE or digest(archive, "md5") != EXPECTED_MD5:
        raise RuntimeError("Pinned archive size/MD5 mismatch")
    members = []
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            member = {"name": entry.filename, "bytes": entry.file_size,
                      "compressed_bytes": entry.compress_size, "crc32": entry.CRC}
            if entry.filename.lower().endswith((".csv", ".tsv")):
                with z.open(entry) as stream:
                    line = stream.readline(65537)
                if len(line) > 65536 or not line.endswith(b"\n"):
                    raise RuntimeError("Header bound/line format failed")
                delimiter = "\t" if entry.filename.lower().endswith(".tsv") else ","
                member["header"] = next(csv.reader(io.StringIO(line.decode("utf-8-sig")), delimiter=delimiter))
            members.append(member)
    result = dict(binding, archive_sha256=digest(archive), archive_md5=digest(archive, "md5"), members=members)
    (OUT / "HEADERS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"qualified_bytes": archive.stat().st_size, "members": len(members), "target_numeric_use": False}), flush=True)


if __name__ == "__main__":
    main()
