"""Fetch only primary paper texts and precise bibliographic metadata; no assay data."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification/skeptic_sources"
targets = {
    "EARLY_TG_FULL.xml": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4034126/fullTextXML",
    "BENCHMARK_FULL.xml": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13557097/fullTextXML",
    "precise_tg.json": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": '(TITLE_ABS:"TG-GATEs" AND FIRST_PDATE:[2024-01-01 TO 2026-10-22])', "format": "json", "resultType": "core", "pageSize": "30", "sort": "FIRST_PDATE_D desc"}),
    "PROTEINTALKS.json": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": 'DOI:10.1038/s41586-026-11001-9', "format": "json", "resultType": "core"}),
}
receipts = []
for name, url in targets.items():
    path = OUT / name
    if path.exists():
        raise FileExistsError(path)
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            payload = response.read(2_000_001)
            status = response.status
        if len(payload) > 2_000_000:
            raise RuntimeError("Literature payload too large")
        path.write_bytes(payload)
        receipts.append({"name": name, "url": url, "status": status, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
        if name.endswith(".xml"):
            tree = ET.fromstring(payload)
            texts = [" ".join(p.itertext()) for p in tree.findall(".//p")]
            (OUT / (name + ".txt")).write_text("\n\n".join(texts), encoding="utf-8")
        else:
            data = json.loads(payload)
            records = [{field: item.get(field) for field in ("id", "pmcid", "doi", "title", "firstPublicationDate", "abstractText", "fullTextUrlList")} for item in data.get("resultList", {}).get("result", [])]
            (OUT / (name + "_abstracts.json")).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        receipts.append({"name": name, "url": url, "error": str(exc)})
(OUT / "PRIMARY_NETWORK.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(receipts))
