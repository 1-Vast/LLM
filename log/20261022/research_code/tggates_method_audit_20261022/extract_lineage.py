"""Extract primary methods statements without opening experimental outcomes."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "log/20261022/tggates_source_qualification/PAPER.xml"
OUT = ROOT / "log/20261022/tggates_functional_qualification/DOSE_METHOD_EXCERPTS.json"


def main():
    if OUT.exists():
        raise RuntimeError("Excerpts already retained")
    root = ET.parse(SOURCE).getroot()
    paragraphs = []
    for i, p in enumerate(root.findall(".//p")):
        text = " ".join("".join(p.itertext()).split())
        if re.search(r"highest concentration|six lots|systematic trends|global normalization|detailed procedure for the measurement", text, re.I):
            paragraphs.append({"paragraph_index": i, "text": text})
    result = {"source": str(SOURCE.relative_to(ROOT)),
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "doi": "10.1093/nar/gku955", "paragraphs": paragraphs,
              "prescreen_assay": "UNKNOWN", "prescreen_time": "UNKNOWN",
              "prescreen_culture_lot_independence": "UNKNOWN",
              "same_physical_cells_or_parallel_wells": "NOT_AUTHENTICATED",
              "sample_to_lot_mapping": "NOT_OBTAINED",
              "individual_response_values_read": False}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
