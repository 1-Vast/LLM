"""Print only source structure or file metadata, never dose outcomes."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(r"D:\MAESTRO")
paper = BASE / "research/routes/agent_virtual_cell_joint_learning/2026-10-27-direction-mechanism-expansion/primary/PMC13168506.xml"
root = ET.parse(paper).getroot()
for section in root.findall(".//sec"):
    title = section.find("title")
    title_text = "".join(title.itertext()) if title is not None else ""
    print("SECTION", section.get("id"), title_text)

listing = BASE / "data/external/conditional_interventions_20261030/dose/simplicity_osf_files.json"
data = json.loads(listing.read_text(encoding="utf-8"))
print("OSF LINKS", data.get("links"))
for item in data.get("data", []):
    attrs = item["attributes"]
    print(json.dumps({"id": item["id"], "name": attrs.get("name"), "kind": attrs.get("kind"),
                      "size": attrs.get("size"), "hashes": attrs.get("extra", {}).get("hashes"),
                      "relationships": item.get("relationships"), "links": item.get("links")}, ensure_ascii=False))
