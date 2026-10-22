"""Two explicit primary-narrative requests; no assay payloads or retries."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/novelty_advocate/sources"
REQUESTS = [
    ("01_hyperagents", "https://arxiv.org/html/2603.19461v1"),
    ("02_aide2", "https://arxiv.org/abs/2609.26457"),
]
CAP = 8 * 1024 * 1024


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
    for name, url in REQUESTS:
        body_path = OUT / f"{name}.body"
        receipt_path = OUT / f"{name}.json"
        if receipt_path.exists() or body_path.exists():
            raise RuntimeError("Refusing to repeat a retained request")
        receipt = {
            "url": url, "method": "GET", "timeout_seconds": 30,
            "automatic_retries": 0, "allow_redirects": False,
            "cap_bytes": CAP,
            "utc_started": datetime.now(timezone.utc).isoformat(),
        }
        chunks = []
        started = time.monotonic()
        try:
            with session.get(url, timeout=30, allow_redirects=False, stream=True) as response:
                receipt.update({
                    "status": response.status_code,
                    "headers": {k: response.headers.get(k) for k in
                                ("Content-Type", "Content-Length", "Location", "Last-Modified")},
                })
                size = 0
                for chunk in response.iter_content(65536):
                    if size + len(chunk) > CAP:
                        chunks.append(chunk[:CAP - size])
                        receipt["truncated_at_cap"] = True
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    if time.monotonic() - started >= 30:
                        receipt["stopped_at_elapsed_limit"] = True
                        break
        except requests.RequestException as exc:
            receipt["error"] = type(exc).__name__ + ": " + str(exc)
        body = b"".join(chunks)
        body_path.write_bytes(body)
        receipt.update({
            "utc_finished": datetime.now(timezone.utc).isoformat(),
            "seconds": time.monotonic() - started,
            "retained_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "body_path": str(body_path),
        })
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"request": name, "status": receipt.get("status"),
                          "bytes": len(body), "error": receipt.get("error")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
