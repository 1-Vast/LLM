"""Offline primary narrative and search projections; no dataset access."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path("D:/MAESTRO/log/20261022/dead_stock_information_gate/skeptic")
source = ET.fromstring((BASE / "PHASE_SPECIFIC_PRIMARY.body").read_bytes())
rows = []
for section in source.findall(".//body//sec"):
    title = section.find("title")
    title_text = " ".join("".join(title.itertext()).split()) if title is not None else ""
    paragraphs = [" ".join("".join(p.itertext()).split()) for p in section.findall("p")]
    if paragraphs:
        rows.append({"title": title_text, "paragraphs": paragraphs})
(BASE / "PHASE_SPECIFIC_NARRATIVE.json").write_text(
    json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
print("PRIMARY_SECTIONS")
print("\n".join(f"{i}: {row['title']}" for i, row in enumerate(rows)))

search = json.loads((BASE / "LIVE_DEAD_FORECAST_SEARCH.body").read_bytes())
results = [{k: row.get(k) for k in ["id", "source", "pmcid", "doi", "title",
           "firstPublicationDate", "abstractText"]} for row in search["resultList"]["result"]]
projection = {"hitCount": search["hitCount"], "results": results}
(BASE / "LIVE_DEAD_FORECAST_SEARCH_PROJECTION.json").write_text(
    json.dumps(projection, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(projection, indent=2, ensure_ascii=False))

ros = ET.fromstring((BASE / "ROS_GROWTH_PRIMARY.body").read_bytes())
ros_rows = []
for section in ros.findall(".//body//sec"):
    title = section.find("title")
    title_text = " ".join("".join(title.itertext()).split()) if title is not None else ""
    paragraphs = [" ".join("".join(p.itertext()).split()) for p in section.findall("p")]
    if paragraphs:
        ros_rows.append({"title": title_text, "paragraphs": paragraphs})
(BASE / "ROS_GROWTH_NARRATIVE.json").write_text(
    json.dumps(ros_rows, indent=2, ensure_ascii=False), encoding="utf-8")
print("ROS_SECTIONS")
print("\n".join(f"{i}: {row['title']}" for i, row in enumerate(ros_rows)))
