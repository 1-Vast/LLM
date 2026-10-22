"""Inspect only paper methods and identity-archive headers, never viability data."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_source_qualification"


def main():
    result = {}
    paper = OUT / "PAPER.xml"
    if paper.exists():
        tree = ET.parse(paper)
        root = tree.getroot()
        selected = []
        for paragraph in root.findall(".//p"):
            text = " ".join("".join(paragraph.itertext()).split())
            if re.search(r"\blots?\b|cryopreserved|human hepatocyte|viability|high concentration", text, re.I):
                selected.append(text)
        result["paper_metadata_methods_paragraphs"] = selected
        result["supplementary"] = [ET.tostring(x, encoding="unicode") for x in root.findall(".//supplementary-material")]
        result["paper_doi"] = [x.text for x in root.findall(".//article-id") if x.attrib.get("pub-id-type") == "doi"]
    archives = {}
    for name in ("CEL_ATTRIBUTES.zip", "CELL_SAMPLE.zip"):
        path = OUT / name
        if path.exists():
            with zipfile.ZipFile(path) as archive:
                files = []
                for item in archive.infolist():
                    with archive.open(item) as handle:
                        first = handle.readline().decode("utf-8-sig").strip()
                    files.append({"name": item.filename, "uncompressed_bytes": item.file_size, "header": first})
                archives[name] = files
    result["archive_headers"] = archives
    (OUT / "METADATA_INSPECTION.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
