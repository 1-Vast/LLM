"""One-source BioSample identity projection; phenotypes remain inside this worker."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/serial_antibiotic_alternatives"
OUT = BASE / "biosample_identity_followup"
IDENTITY_ATTRIBUTES = {"strain", "isolate", "sample name"}
DATE_ATTRIBUTES = {"collection date"}


def normalize_name(value):
    return " ".join(value.replace("_", " ").replace("-", " ").casefold().split())


def safe_identity(value):
    """Names with phenotype content are withheld, never numerically interpreted."""
    value = value.strip()
    normalized = normalize_name(value)
    forbidden = r"\b(?:mic|fitness|mutation|variant|variation|phenotype|resistance|resistant|resensiti[sz]\w*|sensitivity|sensitive|susceptib\w*|growth|absorbance|auc|od\d*)\b"
    units_or_response = r"(?:[<>=:%]|(?:µ|μ|u)g\s*/|\b(?:m|n|u|μ|µ)M\b)"
    if re.search(forbidden, normalized, flags=re.I) or re.search(units_or_response, value):
        return {"value": None, "withheld": True, "reason": "POSSIBLE_PHENOTYPE_OR_RESPONSE_CONTENT"}
    return {"value": value, "withheld": False, "reason": None}


def project(raw):
    root = ET.fromstring(raw)
    samples = []
    elements = list(root.iter("BioSample"))
    if root.tag == "BioSample":
        elements = [root]
    for element in elements:
        ids = []
        for identifier in element.findall("./Ids/Id"):
            label = normalize_name(identifier.get("db_label", ""))
            if label == "sample name":
                ids.append({"source": "Ids/Id", "db_label": identifier.get("db_label"),
                            "namespace": identifier.get("namespace"), **safe_identity(identifier.text or "")})
        description = element.find("Description")
        title = safe_identity(description.findtext("Title", "") if description is not None else "")
        organism = description.find("Organism") if description is not None else None
        taxonomy = None if organism is None else {
            "taxonomy_id": organism.get("taxonomy_id"), "taxonomy_name": organism.get("taxonomy_name"),
            "organism_name": organism.findtext("OrganismName")}
        owner = element.find("./Owner/Name")
        owner_metadata = None if owner is None else {"name": owner.text, "abbreviation": owner.get("abbreviation")}
        attribute_names, identity_values, dates = [], [], []
        for attribute in element.findall("./Attributes/Attribute"):
            name = attribute.get("attribute_name", "")
            harmonized = attribute.get("harmonized_name", "")
            attribute_names.append({"attribute_name": name, "harmonized_name": harmonized, "display_name": attribute.get("display_name")})
            normalized_names = {normalize_name(name), normalize_name(harmonized)}
            if normalized_names & IDENTITY_ATTRIBUTES:
                identity_values.append({"attribute_name": name, "harmonized_name": harmonized,
                                        **safe_identity(attribute.text or "")})
            elif normalized_names & DATE_ATTRIBUTES:
                dates.append({"attribute_name": name, "value": attribute.text or ""})
        sample = {"entrez_id": element.get("id"), "accession": element.get("accession"),
                  "submission_date": element.get("submission_date"), "publication_date": element.get("publication_date"),
                  "last_update": element.get("last_update"), "title": title, "sample_name_ids": ids,
                  "taxonomy": taxonomy, "owner": owner_metadata, "collection_dates": dates,
                  "attribute_names": attribute_names, "strain_isolate_sample_identity": identity_values}
        samples.append(sample)
    if not samples:
        raise ValueError("No BioSample elements in exact request response")
    return {"samples": samples, "source_response_values_exported": False,
            "projection_is_OS_security_boundary": False}


def main():
    source = OUT / "sealed_source/BIOSAMPLE.xml"
    receipt_path = OUT / "NETWORK.json"
    if source.exists() or receipt_path.exists() or (OUT / "IDENTITY_METADATA.json").exists():
        raise RuntimeError("BioSample identity source already recorded; no restart")
    relation_path = BASE / "manifest_followup/amendment2_sources/RELATION_SUMMARY.json"
    relation = json.loads(relation_path.read_text(encoding="utf-8"))
    ids = relation["unique_linked_BioSample_Entrez_ids"]
    if len(ids) != 21 or len(set(ids)) != 21 or not all(isinstance(i, str) and i.isdigit() for i in ids):
        raise ValueError("Authenticated sample ID contract failed")
    paths = [Path(__file__), Path(__file__).with_name("auditor_biosample_test.py"), OUT / "PROTOCOL.md",
             OUT / "SYNTHETIC_TESTS.txt", relation_path, BASE / "supplement_followup/REPORT.md"]
    freeze = {"utc": datetime.now(timezone.utc).isoformat(), "requests_before_freeze": 0,
              "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT / "PRE_REQUEST_FREEZE.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urlencode({"db": "biosample", "id": ",".join(ids), "retmode": "xml"})
    receipt = {"url": url, "requested_Entrez_ids": ids, "body_cap": 500000,
               "started_utc": datetime.now(timezone.utc).isoformat()}
    received, parts = 0, []
    try:
        with requests.get(url, stream=True, timeout=40) as response:
            receipt.update({"status": response.status_code, "headers": dict(response.headers), "final_url": response.url})
            while received < 500000:
                part = response.raw.read(min(16384, 500000 - received), decode_content=True)
                if not part:
                    break
                received += len(part)
                parts.append(part)
        raw = b"".join(parts)
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        receipt.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated_at_cap": received == 500000})
        if receipt["status"] != 200 or received == 500000:
            raise RuntimeError("BioSample HTTP failure or body cap")
        safe = project(raw)
        (OUT / "IDENTITY_METADATA.json").write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
        receipt.update({"projection": "SUCCESS", "returned_samples": len(safe["samples"])})
    except Exception as exc:
        receipt.update({"projection": "FAILED_NO_RAW_CONTENT_ECHO", "failure_type": type(exc).__name__})
    receipt["receipt_utc"] = datetime.now(timezone.utc).isoformat()
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ["status", "bytes", "truncated_at_cap", "projection", "returned_samples"] if k in receipt}))


if __name__ == "__main__":
    main()
