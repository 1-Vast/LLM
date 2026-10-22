"""Project source metadata and narrative without touching assay payloads."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/data_auditor"
source = OUT / "az_primary.body"
tree = ET.fromstring(source.read_bytes())
lines = []
for element in tree.iter():
    if element.tag in {"article-title", "pub-date", "article-id", "title", "p", "ext-link", "supplementary-material"}:
        text = " ".join(" ".join(element.itertext()).split())
        if element.tag in {"article-title", "pub-date", "article-id"} or any(
            term in text.lower() for term in (
                "figshare", "replicat", "celltiter", "72 hour", "72-hour", "7 × 7", "7 ×7", "7x7",
                "755", "109", "37 drugs", "genom", "data avail", "dosage", "dose matrix", "normaliz", "quality control")):
            lines.append({"tag": element.tag, "attributes": element.attrib, "text": text})
(OUT / "PRIMARY_PROJECTION.json").write_text(json.dumps({"source": source.name,
    "exposure": "Primary publication narrative includes reported aggregate biological outcomes; no response array opened",
    "matches": lines}, indent=2), encoding="utf-8")
print(json.dumps(lines, indent=2))

manifests = {}
for name in ("az_well_manifest", "az_matrix_manifest"):
    document = json.loads((OUT / (name + ".body")).read_bytes())
    manifests[name] = {key: document.get(key) for key in (
        "id", "title", "doi", "version", "published_date", "modified_date", "description", "files", "license")}
(OUT / "FILE_MANIFEST_PROJECTION.json").write_text(json.dumps(manifests, indent=2), encoding="utf-8")

prior = ET.fromstring((OUT / "jaaks_primary_lineage.body").read_bytes())
lineage = []
for element in prior.iter("p"):
    text = " ".join(" ".join(element.itertext()).split())
    if "figshare" in text.lower():
        lineage.append(text)
(OUT / "JAAKS_LINEAGE_PROJECTION.json").write_text(json.dumps({
    "source": "jaaks_primary_lineage.body", "primary_data_availability": lineage,
    "exposure": "Previously exposed source; primary full narrative retained, including reported aggregate outcomes"}, indent=2), encoding="utf-8")
