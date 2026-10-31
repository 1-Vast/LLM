"""Create identity projections and local provenance receipts only."""
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

EPISODE = Path(__file__).resolve().parent
DATA = Path(r"D:\MAESTRO\data\external\conditional_interventions_20261030\dose")
PROCESSED = Path(r"D:\MAESTRO\data\processed\conditional_interventions_20261030\dose")
PROCESSED.mkdir(parents=True, exist_ok=True)
X = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
schema = []
for path in sorted(DATA.glob("Simplicity_Table_*Name_Harmonizer.xlsx")):
    with ZipFile(path) as workbook:
        strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            strings = ["".join(t.text or "" for t in s.findall(".//m:t", X)) for s in ET.fromstring(workbook.read("xl/sharedStrings.xml")).findall("m:si", X)]
        for sheet in sorted(name for name in workbook.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")):
            projected = []
            for row in ET.fromstring(workbook.read(sheet)).findall(".//m:row", X):
                fields = []
                for cell in row.findall("m:c", X):
                    value = cell.find("m:v", X)
                    text = value.text if value is not None else "".join(t.text or "" for t in cell.findall(".//m:t", X))
                    fields.append(strings[int(text)] if cell.get("t") == "s" and text else text)
                projected.append(fields)
            destination = PROCESSED / (path.stem + ".tsv")
            with destination.open("w", encoding="utf-8", newline="") as stream:
                csv.writer(stream, delimiter="\t").writerows(projected)
            schema.append({"source": str(path), "sheet": sheet, "headers": projected[0], "projection": str(destination), "rows_excluding_header": len(projected)-1})
            for row in projected[1:]:
                if len(row) >= 3 and row[2]:
                    print("Identity note", row)

receipts = [json.loads(line) for line in (EPISODE / "http_receipts.jsonl").read_text(encoding="utf-8").splitlines()]
summary = {"requests_including_redirects": len(receipts),
           "completed_body_bytes": sum(row.get("completed_body_bytes", 0) for row in receipts),
           "redirects": sum(300 <= row.get("status", 0) < 400 for row in receipts),
           "errors": sum(bool(row.get("error")) or row.get("status", 0) >= 400 for row in receipts),
           "unknown_partial_traffic": any(row.get("unknown_partial_traffic") or row.get("unknown_unread_body_bytes") for row in receipts),
           "minimum_interrequest_gap_seconds": min(b["started_unix"] - a["finished_unix"] for a, b in zip(receipts, receipts[1:])),
           "identity_schema": schema}
(EPISODE / "access_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))

with (EPISODE / "public_files.sha256.tsv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, delimiter="\t")
    writer.writerow(["path", "bytes", "sha256"])
    for path in sorted(DATA.iterdir()):
        if path.is_file():
            writer.writerow([str(path), path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()])
