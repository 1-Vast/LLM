"""Bounded literature HTTP receipts and HTML projections; no biological inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/rsi_later_task_literature/skeptic"


def digest(content):
    return hashlib.sha256(content).hexdigest()


def fetch(stem, url):
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (stem + ".body")
    receipt_path = OUT / (stem + ".receipt.json")
    if target.exists() or receipt_path.exists():
        raise RuntimeError("Existing evidence cannot be overwritten")
    receipt = {"url": url, "utc": datetime.now(timezone.utc).isoformat(),
               "request": "GET", "retry": False, "cap_bytes": 16 * 1024 * 1024}
    body = bytearray()
    try:
        with requests.get(url, headers={"User-Agent": "MAESTRO-literature-audit/1.0"},
                          timeout=(15, 45), stream=True) as response:
            receipt.update(status=response.status_code, final_url=response.url,
                           headers=dict(response.headers), redirects=[r.url for r in response.history])
            capped = False
            for block in response.iter_content(65536):
                remain = receipt["cap_bytes"] - len(body)
                if len(block) > remain:
                    body.extend(block[:remain])
                    capped = True
                    break
                body.extend(block)
            receipt["capped"] = capped
    except Exception as error:
        receipt.update(exception_type=type(error).__name__, exception=str(error))
    raw = bytes(body)
    target.write_bytes(raw)
    receipt.update(bytes=len(raw), sha256=digest(raw), body=str(target.relative_to(ROOT)))
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    with (OUT / "HTTP_RECEIPTS.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt) + "\n")
    print(json.dumps({k: receipt.get(k) for k in ("url", "status", "bytes", "sha256", "capped", "exception_type")}))
    content_type = next((v for k, v in receipt.get("headers", {}).items() if k.lower() == "content-type"), "")
    if raw and "html" in content_type.lower():
        project(stem)


def project(stem):
    raw = (OUT / (stem + ".body")).read_bytes()
    class Projection(HTMLParser):
        def __init__(self):
            super().__init__()
            self.active, self.paragraphs, self.links, self.meta = [], [], [], []
            self.suppressed = 0

        def handle_starttag(self, tag, attributes):
            attrs = dict(attributes)
            if tag in {"script", "style", "nav"}:
                self.suppressed += 1
            if tag == "meta":
                self.meta.append(attrs)
            if tag in {"h1", "h2", "h3", "h4", "p", "figcaption", "table", "title", "a"}:
                self.active.append({"tag": tag, "id": attrs.get("id"), "href": attrs.get("href"), "tokens": []})

        def handle_data(self, data):
            if not self.suppressed:
                for record in self.active:
                    record["tokens"].append(data)

        def handle_endtag(self, tag):
            if tag in {"script", "style", "nav"}:
                self.suppressed = max(0, self.suppressed - 1)
            for i in range(len(self.active)-1, -1, -1):
                if self.active[i]["tag"] == tag:
                    record = self.active.pop(i)
                    text = re.sub(r"\s+", " ", " ".join(record.pop("tokens"))).strip()
                    if tag == "a":
                        self.links.append({"label": text, "href": record["href"]})
                    elif text:
                        self.paragraphs.append({"tag": tag, "id": record["id"], "text": text})
                    break
    projection = Projection()
    projection.feed(raw.decode("utf-8", errors="replace"))
    value = {"source_sha256": digest(raw), "metadata": projection.meta,
             "paragraphs": projection.paragraphs, "links": projection.links}
    (OUT / (stem + ".projection.json")).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stem")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--project", action="store_true")
    args = parser.parse_args()
    project(args.stem) if args.project else fetch(args.stem, args.url)
