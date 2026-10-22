"""Read authenticated XML; extract design, availability, and closest-prior text."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "log/20261022/next_asset/sources"
OUT = ROOT / "log/20261022/cardiac_mechanism_review"
NAMES = ["cardiac_organelle", "cardiac_multidonor_ai", "cipa_multisite_primary"]
PATTERN = re.compile(r"availab|github|supplement|request|arrhythm|quiescen|statistical model|censor|qnet|205|GSE289264|simulat|ion channel", re.I)


def main():
    result = {}
    for name in NAMES:
        path = SOURCES / f"{name}_fulltext.body"
        raw = path.read_bytes()
        root = ET.fromstring(raw)
        paragraphs = []
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] in {"p", "ref"}:
                text = " ".join("".join(node.itertext()).split())
                if PATTERN.search(text):
                    paragraphs.append(text)
        result[name] = {
            "source": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "title": [" ".join(n.itertext()) for n in root.iter("article-title")][:1],
            "doi": [n.text for n in root.iter("article-id") if n.get("pub-id-type") == "doi"],
            "paragraphs": paragraphs,
        }
    target = OUT / "SOURCE_REVIEW_EXTRACTION.json"
    with target.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    for name, record in result.items():
        print(name, record["title"], record["doi"], len(record["paragraphs"]))
        for p in record["paragraphs"]:
            if re.search("availab|github|request|205|GSE289264|statistical model|qnet", p, re.I):
                print(p[:4500])


if __name__ == "__main__":
    main()
