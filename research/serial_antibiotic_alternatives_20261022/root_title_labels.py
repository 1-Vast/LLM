"""Offline author-title annotation review; no measurement or genome export."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives/biosample_identity_followup"
source = OUT / "sealed_source/BIOSAMPLE.xml"
target = OUT / "TITLE_LABELS.json"
if target.exists():
    raise FileExistsError(target)
receipt = json.loads((OUT / "NETWORK.json").read_bytes())
if hashlib.sha256(source.read_bytes()).hexdigest() != receipt["sha256"]:
    raise ValueError("Source changed")
rows = []
for sample in ET.fromstring(source.read_bytes()).iter("BioSample"):
    title = sample.findtext("./Description/Title", "")
    quantitative = re.search(r"\b(?:MIC|IC\d+|EC\d+|fitness|mutations?|variants?|growth|absorbance|AUC)\b|[<>=:%]|(?:µ|μ|u|m)g\s*/", title, re.I)
    names = [item.text for item in sample.findall("./Ids/Id") if item.get("db_label") == "Sample name"]
    rows.append({"accession": sample.get("accession"), "sample_alias": names,
                 "author_title": None if quantitative else title,
                 "title_withheld_for_measurement_terms": bool(quantitative)})
result = {"samples": rows, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "scope": "AUTHOR_CATEGORICAL_SOURCE_LABELS_ONLY; DESIGN_EXPOSED",
          "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
