"""Current-host OA metadata and real BioProject-to-BioSample relation only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import requests

from auditor_manifest import project_oa

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/serial_antibiotic_alternatives/manifest_followup"
OUT = BASE / "amendment2_sources"


def project_search(raw):
    data = json.loads(raw)
    result = data.get("esearchresult", {})
    return {k: result.get(k) for k in ["count", "retmax", "retstart", "idlist", "querytranslation", "errorlist", "warninglist"]}


def project_link(raw):
    data = json.loads(raw)
    entries = []
    for linkset in data.get("linksets", []):
        entries.append({"dbfrom": linkset.get("dbfrom"), "input_project_ids": linkset.get("ids"),
                        "linksetdbs": [{"dbto": d.get("dbto"), "linkname": d.get("linkname"),
                                        "ids": d.get("links", []), "linked_record_count": len(d.get("links", []))}
                                       for d in linkset.get("linksetdbs", [])],
                        "error": linkset.get("error")})
    return {"linksets": entries, "top_level_error": data.get("error"),
            "counts_are_distinct_strains_lineages_backgrounds_or_tasks": False}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ledger_path = OUT / "NETWORK.json"
    if ledger_path.exists():
        raise RuntimeError("Amendment2 ledger exists; no restart")
    paths = [Path(__file__), Path(__file__).with_name("auditor_manifest.py"), BASE / "AMENDMENT2.md", BASE / "REPORT.md", BASE / "STATUS.json", BASE / "NETWORK.json"]
    freeze = {"utc": datetime.now(timezone.utc).isoformat(), "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT / "PRE_REQUEST_FREEZE.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    ledger, received = [], 0

    def fetch(name, url, parser):
        nonlocal received
        source = OUT / f"{name}_SOURCE.body"
        target = OUT / f"{name}_METADATA.json"
        if source.exists() or target.exists() or len(ledger) >= 3:
            raise RuntimeError("Amendment2 overwrite/request cap")
        receipt = {"name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat()}
        metadata = None
        try:
            parts = []
            with requests.get(url, stream=True, timeout=35) as response:
                receipt.update({"status": response.status_code, "final_url": response.url, "headers": dict(response.headers)})
                while received < 500000:
                    part = response.raw.read(min(16384, 500000 - received), decode_content=True)
                    if not part:
                        break
                    received += len(part)
                    parts.append(part)
            raw = b"".join(parts)
            source.write_bytes(raw)
            receipt.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated_at_shared_cap": received == 500000})
            if receipt["status"] != 200 or received == 500000:
                raise RuntimeError("HTTP failure or body cap")
            metadata = parser(raw)
            target.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            receipt["projection"] = "SUCCESS"
        except Exception as exc:
            receipt.update({"projection": "FAILED_NO_RAW_CONTENT_ECHO", "failure_type": type(exc).__name__})
        receipt["receipt_utc"] = datetime.now(timezone.utc).isoformat()
        ledger.append(receipt)
        ledger_path.write_text(json.dumps({"additional_consumed_HTTP_body_bytes": received, "requests": ledger}, indent=2), encoding="utf-8")
        print(json.dumps({k: receipt[k] for k in ["name", "status", "bytes", "projection"] if k in receipt}))
        return metadata

    fetch("CURRENT_PMC_OA", "https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC12164588", project_oa)
    if received >= 500000:
        return
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode({"db": "bioproject", "term": "PRJNA1254677", "retmax": 5, "retmode": "json"})
    project = fetch("BIOPROJECT_SEARCH", search_url, project_search)
    identifiers = project.get("idlist", []) if project else []
    if received < 500000 and identifiers and len(identifiers) <= 5 and all(isinstance(i, str) and i.isdigit() for i in identifiers):
        link_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?" + urlencode({"dbfrom": "bioproject", "db": "biosample", "id": ",".join(identifiers), "retmode": "json"})
        fetch("BIOPROJECT_BIOSAMPLE_LINK", link_url, project_link)


if __name__ == "__main__":
    main()
