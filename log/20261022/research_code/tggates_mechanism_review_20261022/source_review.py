"""Outcome-free primary literature retrieval for the independent mechanism review."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification/skeptic_sources"
OUT.mkdir(parents=True, exist_ok=True)

queries = {
    "early_human": '(("TG-GATEs" OR "primary human hepatocytes") AND ("early" OR "temporal" OR "time course") AND ("predict" OR "prediction" OR "cytotoxicity")) FIRST_PDATE:[2022-01-01 TO 2026-10-22]',
    "prior_early": 'DOI:10.1038/tpj.2013.39',
    "recent_virtual": '("virtual cell" AND ("perturbation" OR "world model")) FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
}

receipts = []
for key, query in queries.items():
    path = OUT / f"{key}.json"
    if path.exists():
        raise FileExistsError(path)
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": query, "format": "json", "resultType": "core", "pageSize": "20", "sort": "FIRST_PDATE_D desc"}
    )
    with urllib.request.urlopen(url, timeout=45) as response:
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise RuntimeError("Literature payload exceeds per-request ceiling")
        status = response.status
    path.write_bytes(payload)
    data = json.loads(payload)
    records = []
    for item in data.get("resultList", {}).get("result", []):
        records.append({field: item.get(field) for field in (
            "id", "source", "pmcid", "doi", "title", "firstPublicationDate", "journalTitle", "abstractText"
        )})
    (OUT / f"{key}_abstracts.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    receipts.append({"query": query, "url": url, "status": status, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "hitCount": data.get("hitCount")})

paper = ET.parse(ROOT / "log/20261022/tggates_source_qualification/PAPER.xml")
sections = {}
for section_id in ("SEC2-1", "SEC2-3", "SEC2-4", "SEC2-7", "SEC2-8"):
    section = paper.find(f".//sec[@id='{section_id}']")
    sections[section_id] = " ".join(section.itertext()) if section is not None else None
(OUT / "TG_METHOD_EXCERPTS.json").write_text(json.dumps(sections, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "NETWORK.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"requests": len(receipts), "bytes": sum(r["bytes"] for r in receipts), "hit_counts": [r["hitCount"] for r in receipts]}))
