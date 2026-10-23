"""Independently verify archive and XML metadata without response text extraction."""
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "log/20261023/hcc_task_qualification"
OUT = BASE / "method/VERIFICATION.json"
if OUT.exists():
    raise SystemExit("Refusing overwrite")
tree = ET.parse(BASE / "epmc_fulltext.xml")
raw_xml = (BASE / "epmc_fulltext.xml").read_text(encoding="utf-8")
expected_md5 = {}
for fragment in re.findall(r"<supplementary-material\b.*?</supplementary-material>", raw_xml, re.S):
    href = re.search(r'xlink:href="([^"]+)"', fragment)
    digest = re.search(r"<\?suppdata-md5 ([0-9a-f]{32})\?>", fragment)
    if href and digest:
        expected_md5[href.group(1)] = digest.group(1)
supplements = []
for node in tree.iter():
    if node.tag.rsplit("}", 1)[-1] == "supplementary-material":
        for child in node.iter():
            attrs = child.attrib
            href = attrs.get("{http://www.w3.org/1999/xlink}href", "")
            if href:
                supplements.append({"tag": child.tag, "attrs": attrs})
with zipfile.ZipFile(BASE / "epmc_supplements.zip") as archive:
    members = [{"name": i.filename, "bytes": i.file_size} for i in archive.infolist()]
    checks = []
    for name in ["mmc1.pdf", "mmc2.docx", "mmc3.pdf", "mmc4.pdf"]:
        content = archive.read(name)
        digest = hashlib.md5(content).hexdigest()
        if digest != expected_md5.get(name):
            raise SystemExit(f"MD5 unverified for {name}")
        checks.append({"name": name, "md5": digest, "matches_primary_xml": True})
with zipfile.ZipFile(BASE / "mmc2_authenticated.docx") as docx:
    doc = ET.fromstring(docx.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    headers = []
    for table in doc.findall(".//w:tbl", ns):
        row = table.find("w:tr", ns)
        headers.append(["".join(cell.itertext()).strip() for cell in row.findall("w:tc", ns)])
    embedded = [name for name in docx.namelist() if name.startswith("word/embeddings/")]
pdf_attachments = {name: list(PdfReader(BASE / name).attachments) for name in ["mmc1.pdf", "mmc3.pdf", "mmc4.pdf"]}
result = {
    "primary_title": tree.findtext("./front/article-meta/title-group/article-title"),
    "archive_members": members,
    "spreadsheet_members": [m for m in members if m["name"].lower().endswith((".xls", ".xlsx", ".csv", ".tsv", ".ods"))],
    "supplement_md5_checks": checks,
    "docx_first_rows": headers,
    "docx_embedded": embedded,
    "pdf_embedded_attachments": pdf_attachments,
    "scope": "Names, attributes, table first rows, attachment lists only; no PDF outcome text extraction",
}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
