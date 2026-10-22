"""Bounded primary-method retrieval; all artifacts are retained under log/."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = Path("D:/MAESTRO/log/20261022/functional_dynamics_gate/skeptic")
CAP = 3 * 1024 * 1024


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("url")
    args = parser.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    if not args.name.replace("_", "").isalnum():
        raise ValueError("Use an alphanumeric/underscore artifact name")
    if len(list(BASE.glob("*_RECEIPT.json"))) >= 6:
        raise RuntimeError("Six-request ceiling reached")
    receipt_path = BASE / f"{args.name}_RECEIPT.json"
    body_path = BASE / f"{args.name}.body"
    if receipt_path.exists() or body_path.exists():
        raise RuntimeError("Refuse overwrite or retry")
    receipt = {"url": args.url, "started_utc": utc(), "timeout_seconds": 25,
               "redirects_allowed": False, "retries": 0, "body_cap": CAP}
    started = time.monotonic()
    body = bytearray()
    try:
        with requests.Session() as session:
            session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
            with session.get(args.url, timeout=25, allow_redirects=False, stream=True,
                             headers={"User-Agent": "MAESTRO-primary-method-qualification/1.0"}) as response:
                receipt.update(status=response.status_code, headers=dict(response.headers))
                for chunk in response.iter_content(16384):
                    if time.monotonic() - started > 25:
                        raise TimeoutError("Total retrieval deadline exceeded")
                    if len(body) + len(chunk) > CAP:
                        body.extend(chunk[:CAP - len(body)])
                        raise ValueError("Response cap reached; body is truncated")
                    body.extend(chunk)
                receipt["complete_body"] = True
    except Exception as exc:
        receipt.update(error=f"{type(exc).__name__}: {exc}", complete_body=False)
    body_path.write_bytes(body)
    receipt.update(finished_utc=utc(), elapsed_seconds=time.monotonic() - started,
                   retained_bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                   body_path=str(body_path))
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: receipt.get(k) for k in ["url", "status", "retained_bytes",
          "sha256", "complete_body", "error"]}))


if __name__ == "__main__":
    main()
