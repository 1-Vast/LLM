"""Single exact-version metadata request; preserve link/manifest differences only."""
from datetime import datetime, timezone
import hashlib
from html import unescape
import json
from pathlib import Path

import requests

from auditor_title_citations import project as project_citations
from auditor_title_registry import project_zenodo

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/antibiotic_schedule_qualification/title_registry_audit"
OUT = BASE / "version_followup"
URL = "https://zenodo.org/api/records/18362221"


def main():
    receipt_path = OUT / "NETWORK.json"
    if receipt_path.exists() or (OUT / "SOURCE_METADATA.json").exists():
        raise RuntimeError("Exact version follow-up exists")
    files = [Path(__file__), Path(__file__).with_name("auditor_title_registry.py"), Path(__file__).with_name("auditor_title_citations.py"), OUT / "PROTOCOL.md", BASE / "LINKED_RECORD_MANIFEST.json",
             ROOT / "log/20261022/antibiotic_schedule_qualification/code_discovery/LIST_README.md"]
    freeze = {"utc": datetime.now(timezone.utc).isoformat(), "requests_before_freeze": 0,
              "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (OUT / "PRE_REQUEST_FREEZE.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    receipt = {"url": URL, "additional_body_cap": 131072, "started_utc": datetime.now(timezone.utc).isoformat()}
    received, parts = 0, []
    try:
        with requests.get(URL, stream=True, timeout=35) as response:
            receipt.update({"status": response.status_code, "final_url": response.url, "headers": dict(response.headers)})
            while received < 131072:
                part = response.raw.read(min(16384, 131072 - received), decode_content=True)
                if not part:
                    break
                received += len(part)
                parts.append(part)
        raw = b"".join(parts)
        (OUT / "SOURCE_METADATA.json").write_bytes(raw)
        receipt.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated": received == 131072})
        if receipt["status"] != 200 or received == 131072:
            raise RuntimeError("HTTP failure or exact-version body cap reached")
        data = json.loads(raw)
        if data.get("id") != 18362221:
            raise ValueError("Returned version identity differs")
        safe = project_zenodo({"hits": {"total": 1, "hits": [data]}})["records"][0]
        safe.update({"created": data.get("created"), "updated": data.get("updated"),
                     "record_revision": data.get("revision"), "metadata_version": data.get("metadata", {}).get("version"),
                     "description_citations": project_citations(data.get("metadata", {}))})
        (OUT / "OLD_VERSION_IDENTITY.json").write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
        new = json.loads((BASE / "LINKED_RECORD_MANIFEST.json").read_text(encoding="utf-8"))
        old_files = {f["key"]: f for f in safe["files"]}
        new_files = {f["key"]: f for f in new["record"]["files"]}
        normalize = lambda text: unescape(text).split()[0].rstrip(".,;)")
        comparison = {"old_record_id": safe["id"], "new_record_id": new["record"]["id"],
            "old_DOI": safe["doi"], "new_DOI": new["record"]["doi"],
            "old_parent": safe["record_links"].get("parent"), "new_parent": new["parent_record"],
            "same_concept_parent": safe["record_links"].get("parent") == new["parent_record"],
            "old_publication_date": safe["publication_date"], "new_publication_date": new["record"]["publication_date"],
            "old_created": safe["created"], "old_updated": safe["updated"],
            "old_files": len(old_files), "new_files": len(new_files),
            "old_total_file_bytes": sum(f["size"] for f in old_files.values()),
            "new_total_file_bytes": new["manifest_total_bytes"],
            "names_only_old": sorted(old_files.keys() - new_files.keys()), "names_only_new": sorted(new_files.keys() - old_files.keys()),
            "common_file_identity_equal": {name: all(old_files[name].get(k) == new_files[name].get(k) for k in ["size", "checksum"]) for name in old_files.keys() & new_files.keys()},
            "old_target_paper_DOI_in_description": safe["description_citations"]["target_paper_DOI_literal_present"],
            "old_normalized_citation_URLs": [normalize(u) for u in safe["description_citations"]["citation_URL_strings"]],
            "payload_files_downloaded": False,
            "schedule_identity_or_complete_observed_menu_certified": False}
        (OUT / "VERSION_COMPARISON.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
        receipt["projection"] = "SUCCESS"
    except Exception as exc:
        receipt.update({"projection": "FAILED_NO_RAW_CONTENT_ECHO", "failure_type": type(exc).__name__})
    receipt["receipt_utc"] = datetime.now(timezone.utc).isoformat()
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ["status", "bytes", "truncated", "projection"] if k in receipt}))


if __name__ == "__main__":
    main()
