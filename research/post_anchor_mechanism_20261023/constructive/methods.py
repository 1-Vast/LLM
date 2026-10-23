"""Project source method/design prose; exclude result sections and tables."""
from pathlib import Path
import xml.etree.ElementTree as ET

base = Path("log/20261023/post_anchor_mechanism/constructive")
root = ET.fromstring((base / "hierarchical_primary.body").read_bytes())
texts = []
for sec in root.findall(".//sec"):
    title = sec.find("title")
    t = " ".join(title.itertext()).strip() if title is not None else ""
    if t.lower() in {"methods", "data availability", "code availability"}:
        # Each selected top-level section contains the relevant nested methods.
        for node in sec.iter():
            if node.tag in {"title", "p"}:
                text = " ".join(node.itertext()).strip()
                if text:
                    texts.append(text)
target = base / "hierarchical_methods.txt"
assert not target.exists()
target.write_text("\n\n".join(texts), encoding="utf-8")
print("Projected method/design prose; no results/tables printed")
