"""At most four bounded primary-literature HTTP GETs for the independent review."""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/update_value_qualification/advocate"
LIMIT = 6 * 1024 * 1024


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def fetch(name, url):
    OUT.mkdir(parents=True, exist_ok=True)
    receipts = OUT / "HTTP_RECEIPTS.jsonl"
    previous = receipts.read_text(encoding="utf-8").splitlines() if receipts.exists() else []
    if len(previous) >= 4:
        raise RuntimeError("The four-GET allowance is exhausted")
    body_path = OUT / (name + ".body")
    if body_path.exists():
        raise RuntimeError("Do not overwrite a source attempt")
    record = {"name": name, "url": url, "utc": datetime.now(timezone.utc).isoformat(),
              "request_number": len(previous) + 1, "status": None, "redirects_allowed": False,
              "maximum_body_bytes": LIMIT, "body_complete": False}
    body = bytearray()
    try:
        with requests.get(url, stream=True, timeout=50, allow_redirects=False,
                          headers={"User-Agent": "MAESTRO-primary-literature-qualification/1.0"}) as response:
            record.update(status=response.status_code, final_url=response.url,
                          content_type=response.headers.get("Content-Type"),
                          location=response.headers.get("Location"))
            for chunk in response.iter_content(65536):
                room = LIMIT - len(body)
                body.extend(chunk[:room])
                if len(chunk) > room:
                    record["truncated_at_limit"] = True
                    break
            else:
                record["body_complete"] = True
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    body_path.write_bytes(body)
    record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), body_path=str(body_path.relative_to(ROOT)))
    if "html" in (record.get("content_type") or ""):
        try:
            parser = Text()
            parser.feed(body.decode("utf-8"))
            (OUT / (name + ".txt")).write_text("\n".join(parser.parts), encoding="utf-8")
        except Exception as error:
            record.update(parser_error_type=type(error).__name__, parser_error=str(error))
    with receipts.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, allow_nan=False) + "\n")
    print(json.dumps(record, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("url")
    args = parser.parse_args()
    fetch(args.name, args.url)
