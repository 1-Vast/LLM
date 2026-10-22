"""Read declared published experimental-design prose, never table arrays."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/dynamic_source_followup/ncbi_scout"
target = OUT / "SWITCH_DESIGN_LITERATURE.json"
if target.exists():
    raise FileExistsError("Refusing projection overwrite")
article = ET.parse(OUT / "PRIMARY.xml").getroot()
def text(node):
    return " ".join(node.itertext()).strip() if node is not None else ""
sections = []
for sec in article.iter("sec"):
    title = text(sec.find("title"))
    if "Success of switching to a second antibiotic" in title:
        sections.append({"title": title,
                         "paragraphs": [text(p) for p in sec.findall("p") if p.find(".//table") is None]})
captions = [{"id": fig.get("id"), "label": text(fig.find("label")),
             "caption": text(fig.find("caption"))}
            for fig in article.iter("fig") if "switch" in text(fig.find("caption")).casefold()]
tables = [{"id": table.get("id"), "label": text(table.find("label")),
           "caption": text(table.find("caption"))}
          for table in article.iter("table-wrap")]
result = {"scope": "PUBLISHED_DESIGN_AND_NARRATIVE_EXPOSED_NOT_PROJECT_RESULTS",
          "sections": sections, "switch_figure_captions": captions,
          "table_labels_only": tables, "response_table_arrays_projected": False}
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
