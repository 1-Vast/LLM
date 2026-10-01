"""Replay the captured public HTTP request plan into a new directory.

Original discovery requests were executed from PowerShell here-strings. This
command snapshot was saved after acquisition; the original HTTP bodies remain
byte-preserved. This replay file is not a claim of pre-acquisition registration.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("output_directory")
args = parser.parse_args()
plan_directory = pathlib.Path(__file__).resolve().parent
output = pathlib.Path(args.output_directory)
if output.exists():
    raise SystemExit("Refuse to overwrite an existing output directory")
output.mkdir(parents=True)
plan = []
for name in ("receipts_initial.json", "receipts_extended.json"):
    plan.extend(json.loads((plan_directory / name).read_text(encoding="utf-8")))
receipts = []
for original in plan:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    status = None
    headers = {}
    error = None
    try:
        request = urllib.request.Request(
            original["url"], headers={"User-Agent": "MAESTRO-source-audit/1.0"}
        )
        with urllib.request.urlopen(request, timeout=35) as response:
            status = response.status
            headers = dict(response.headers.items())
            body = response.read(8 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = dict(exc.headers.items())
        body = exc.read(8 * 1024 * 1024 + 1)
        error = type(exc).__name__ + ": " + str(exc)
    except Exception as exc:
        body = b""
        error = type(exc).__name__ + ": " + str(exc)
    if len(body) > 8 * 1024 * 1024:
        raise SystemExit("Metadata response exceeded the declared 8 MiB budget")
    target = output / (original["id"] + ".raw")
    target.write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    receipts.append({
        "id": original["id"], "url": original["url"],
        "retrieved_at_utc": started, "status": status,
        "response_sha256": digest, "response_bytes": len(body),
        "path": str(target), "license_scope": original["license_scope"],
        "version": original["version"], "error": error,
        "response_headers": headers,
        "matches_original_response": digest == original["response_sha256"],
        "qualification": "HTTP status alone does not establish valid metadata",
    })
    (output / "receipts.json").write_text(
        json.dumps(receipts, indent=2), encoding="utf-8"
    )
