"""Public HTTP receipt capture for the independent later-task literature review."""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/rsi_later_task_literature/advocate"


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def fetch(name, url, category):
    OUT.mkdir(parents=True, exist_ok=True)
    stem, attempt = name, 1
    while (OUT / (name + ".body")).exists():
        attempt += 1
        name = f"{stem}_attempt{attempt}"
    started = datetime.now(timezone.utc).isoformat()
    try:
        response = requests.get(url, timeout=55, headers={"User-Agent": "MAESTRO-literature-review/1.0"})
        body = response.content
        path = OUT / (name + ".body")
        path.write_bytes(body)
        record = {"name": name, "category": category, "url": url, "final_url": response.url,
                  "timestamp_utc": started, "status": response.status_code,
                  "content_type": response.headers.get("Content-Type"), "bytes": len(body),
                  "sha256": hashlib.sha256(body).hexdigest(), "body_path": str(path.relative_to(ROOT))}
        if "text" in response.headers.get("Content-Type", "") or "json" in response.headers.get("Content-Type", ""):
            parser = TextOnly()
            parser.feed(response.text)
            text = "\n".join(parser.parts)
            (OUT / (name + ".txt")).write_text(text, encoding="utf-8")
        print(json.dumps(record))
    except Exception as error:
        record = {"name": name, "category": category, "url": url, "timestamp_utc": started,
                  "status": None, "error_type": type(error).__name__, "error": str(error)}
        print(json.dumps(record))
    with (OUT / "SOURCE_RECEIPTS.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("url")
    parser.add_argument("--category", default="primary", choices=("primary", "discovery"))
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.name):
        raise ValueError("Use a simple local receipt name")
    fetch(args.name, args.url, args.category)
