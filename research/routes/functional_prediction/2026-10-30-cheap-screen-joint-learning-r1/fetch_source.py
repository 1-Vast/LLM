"""Fetch one declared public source, retaining partial bodies and a receipt."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

label, url = sys.argv[1:3]
assert label.replace("_", "").isalnum()
folder = Path(__file__).parent / "sources"
folder.mkdir(exist_ok=True)
body = folder / (label + ".body")
assert not body.exists(), "No automatic source replay."
headers = folder / (label + ".headers")
start = time.monotonic()
command = ["curl.exe", "--silent", "--show-error", "--max-time", "25",
           "--connect-timeout", "10", "--max-filesize", "30000000",
           "--dump-header", str(headers), "--output", str(body),
           "--write-out", "%{http_code}", url]
try:
    result = subprocess.run(command, capture_output=True, timeout=30)
    code, status, error = result.returncode, result.stdout.decode().strip(), result.stderr.decode(errors="replace")
except subprocess.TimeoutExpired:
    code, status, error = None, None, "External 30 second guard expired."
raw = body.read_bytes() if body.exists() else b""
record = {"label": label, "url": url, "client_date": "2026-10-30",
          "returncode": code, "status": status, "error": error,
          "seconds": round(time.monotonic() - start, 3), "saved_bytes": len(raw),
          "sha256": hashlib.sha256(raw).hexdigest(), "partial": code != 0,
          "redirects_followed": 0, "automatic_retries": 0,
          "unknown_unsaved_traffic": True}
(folder / (label + ".json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
