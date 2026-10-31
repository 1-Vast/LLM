"""Admit supplement methods prose and identity-only table schema."""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

DATA = Path(r"D:\MAESTRO\data\external\conditional_interventions_20261030\dose")
EPISODE = Path(__file__).resolve().parent
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
source = DATA / "redirect1_simplicity_supplement_JCSCT9708.zip"
with ZipFile(source) as outer:
    for member in outer.infolist():
        if "/" in member.filename or "\\" in member.filename:
            raise ValueError("Unexpected nested supplement member")
        (DATA / member.filename).write_bytes(outer.read(member))

with ZipFile(DATA / "Simplicity_Supplemental_Materials.docx") as document:
    root = ET.fromstring(document.read("word/document.xml"))
paragraphs = ["".join(t.text or "" for t in p.findall(".//w:t", NS)) for p in root.findall(".//w:body/w:p", NS)]
out = []
for index, paragraph in enumerate(paragraphs, 1):
    if index > 77:
        break
    if paragraph:
        out.append(f"P{index}: {paragraph}")
content = "\n".join(out)
(EPISODE / "simplicity_supplement_methods.txt").write_text(content, encoding="utf-8")
print(content)

X = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
for path in DATA.glob("Simplicity_Table_*Name_Harmonizer.xlsx"):
    with ZipFile(path) as workbook:
        strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            strings = ["".join(t.text or "" for t in s.findall(".//m:t", X)) for s in ET.fromstring(workbook.read("xl/sharedStrings.xml")).findall("m:si", X)]
        for sheet in sorted(name for name in workbook.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")):
            rows = ET.fromstring(workbook.read(sheet)).findall(".//m:row", X)
            headers = []
            for cell in rows[0].findall("m:c", X):
                val = cell.find("m:v", X)
                text = val.text if val is not None else "".join(t.text or "" for t in cell.findall(".//m:t", X))
                headers.append(strings[int(text)] if cell.get("t") == "s" and text else text)
            print("IDENTITY TABLE", path.name, sheet, "HEADERS", headers)
