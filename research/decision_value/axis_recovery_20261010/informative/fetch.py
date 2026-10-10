"""Bounded public-source fetches; retain successful and failed response bodies."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

import requests


ROOT = Path(__file__).resolve().parent
CAP = 25_000_000
LEDGER = ROOT / "NETWORK.jsonl"


def records():
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines()]


def public_url(url):
    parts = urlsplit(url)
    if any("signature" in key.lower() or "credential" in key.lower()
           for key in parse_qs(parts.query)):
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "SIGNED_QUERY_REDACTED", ""))
    return url


def fetch(name, url, *, limit=1_000_000, headers=None):
    """Receive at most limit body bytes, logging every redirect/error separately."""
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "sources").mkdir(exist_ok=True)
    history = records()
    spent = sum(item.get("received_body_bytes", 0) for item in history)
    remaining = min(limit, CAP - spent)
    if remaining <= 0:
        raise RuntimeError("Named-summary body budget exhausted")
    request_headers = {"User-Agent": "MAESTRO-axis-discovery/1.0", "Accept-Encoding": "identity"}
    request_headers.update(headers or {})
    for hop in range(6):
        number = len(records())
        path = ROOT / "sources" / f"{number:03d}_{name}.body"
        item = {"name": name, "url": public_url(url), "utc": datetime.now(timezone.utc).isoformat(),
                "hop": hop, "received_body_bytes": 0, "limit": remaining}
        body = bytearray()
        try:
            with requests.get(url, headers=request_headers, stream=True,
                              allow_redirects=False, timeout=(15, 60)) as response:
                response_headers = dict(response.headers)
                redirect_url = response.headers.get("Location")
                if redirect_url:
                    response_headers["Location"] = public_url(redirect_url)
                item.update(http_status=response.status_code, headers=response_headers)
                length = response.headers.get("Content-Length")
                if length and int(length) > remaining:
                    item["status"] = "REFUSED_OVERSIZE"
                else:
                    while len(body) < remaining:
                        chunk = response.raw.read(min(65_536, remaining - len(body)))
                        if not chunk:
                            item["status"] = "RECEIVED" if response.ok else "HTTP_ERROR"
                            break
                        body.extend(chunk)
                    else:
                        item["status"] = "RECEIVED" if length and int(length) == len(body) else "PARTIAL_LIMIT_REACHED"
        except Exception as exc:
            item.update(status="NETWORK_ERROR", error=f"{type(exc).__name__}: {exc}",
                        transport_bytes_before_application_delivery="unmeasured")
        path.write_bytes(body)
        item.update(received_body_bytes=len(body), path=path.relative_to(ROOT).as_posix(),
                    sha256=hashlib.sha256(body).hexdigest())
        with LEDGER.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")
        remaining -= len(body)
        if item.get("http_status") in (301, 302, 303, 307, 308):
            url = urljoin(url, redirect_url)
            if remaining <= 0:
                raise RuntimeError("Response-body cap reached during redirect")
            continue
        print(name, item["status"], len(body), item.get("http_status"), flush=True)
        return item, bytes(body)
    raise RuntimeError("Too many redirects")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("url")
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument("--range")
    args = parser.parse_args()
    fetch(args.name, args.url, limit=args.limit,
          headers={"Range": args.range} if args.range else None)
