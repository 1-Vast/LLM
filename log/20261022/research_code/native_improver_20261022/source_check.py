"""Bounded primary-paper retrieval; never accesses biological assay files."""
import hashlib
import json
from html.parser import HTMLParser
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.title_parts = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        self.parts.append(data)
        if self.in_title:
            self.title_parts.append(data)


def main():
    papers = {
        "seal": "https://arxiv.org/html/2506.10943v2",
        "gradient_history": "https://arxiv.org/html/2610.09604v1",
    }
    receipts = []
    for name, url in papers.items():
        receipt = {"name": name, "url": url, "time_utc": datetime.now(timezone.utc).isoformat()}
        try:
            response = requests.get(url, timeout=45)
            body = response.content
            (OUT / f"{name}.html").write_bytes(body)
            parser = TextParser()
            parser.feed(response.text)
            parsed = " ".join(" ".join(parser.parts).split())
            (OUT / f"{name}.txt").write_text(parsed, encoding="utf-8")
            receipt.update(status=response.status_code, final_url=response.url,
                           content_type=response.headers.get("content-type"), bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest(),
                           title=" ".join(parser.title_parts))
            receipt["success"] = response.status_code == 200 and "arxiv" in response.url
        except Exception as error:
            receipt.update(success=False, error=repr(error))
        receipts.append(receipt)
    (OUT / "PRIMARY_SOURCE_RECEIPTS.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
