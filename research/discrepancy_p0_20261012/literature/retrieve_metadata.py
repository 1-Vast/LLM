"""Retrieve bounded original methods/metadata only; no assay outcome tables."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sys
from urllib.parse import urlsplit, urlunsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
LOG = ROOT / "RETRIEVAL_RECEIPTS.json"
PIN = "b654a45faf5a80cdb1b514188cc90af8c9565b85"
SPECS = [
    ("cxcl9_active_assay_metadata", f"https://raw.githubusercontent.com/SysBioOncology/ActiveLearning_MechanisticModels_CXCL9/{PIN}/data/cxcl9_assay_active_learning/metadata.md", 20000, "Assay protocol, passage/run identifiers; no outcome values"),
    ("cxcl9_biostudies_metadata", "https://www.ebi.ac.uk/biostudies/api/v1/studies/S-SCDT-10_1038-S44320-026-00221-w", 250000, "Source-data file metadata and potential CXCL9/Cas3 pairing paths; no source-data download"),
    ("prism_primary_readme", "https://ndownloader.figshare.com/files/20237700", 30000, "Original primary-screen endpoint, assay time and replicate hierarchy"),
    ("prism_secondary_readme", "https://ndownloader.figshare.com/files/20238123", 30000, "Original secondary-screen dose design and replicate hierarchy"),
    ("prism_paper_lookup", "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI%3A10.1038%2Fs43018-019-0018-6&format=json", 40000, "Verify original title, DOI, publication date and full-text accession"),
    ("batchie_zenodo_metadata", "https://zenodo.org/api/records/13871987", 100000, "Prospective dataset names, original file sizes, licenses and official download paths only"),
    ("prism_paper_methods", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7328899/", 650000, "Original PRISM methods: endpoint, treatment duration, repeat design and measurement units; no supplementary outcome matrices"),
    ("cxcl9_biostudies_metadata_lowercase", "https://www.ebi.ac.uk/biostudies/api/v1/studies/S-SCDT-10_1038-s44320-026-00221-w", 250000, "Source-data file metadata with normalized DOI case; no source-data download"),
    ("cxcl9_biostudies_official_landing", "https://www.ebi.ac.uk/biostudies/sourcedata/studies/S-SCDT-10_1038-S44320-026-00221-w", 150000, "Paper-linked SourceData study landing page; metadata only, no figure/source-data outcome download"),
    ("cxcl9_fig5_source_archive", "https://pmc.ncbi.nlm.nih.gov/articles/instance/13434641/bin/44320_2026_221_MOESM6_ESM.zip", 5000000, "Authorized exception: save Fig5 source archive sealed; inspect member names and table header/schema only, no outcome values"),
    ("cxcl9_fig5_publisher_archive", "https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs44320-026-00221-w/MediaObjects/44320_2026_221_MOESM6_ESM.zip", 5000000, "Official publisher mirror derived from DOI/attachment basename: save Fig5 source archive sealed; inspect member names and schema only, no outcome values"),
]


def redact_resolved_url(url):
    parts = urlsplit(url)
    signed = any(term in parts.query.lower() for term in ("x-amz-", "signature=", "token=", "credential="))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", "")) if signed else url, signed


def retrieve(spec):
    name, url, cap, scope = spec
    record = {
        "id": name,
        "request_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_url": url,
        "read_scope": scope,
        "maximum_response_bytes": cap,
        "access_kind": "new_network_retrieval",
    }
    body = b""
    try:
        request = Request(url, headers={"User-Agent": "MAESTRO-P0-metadata-audit/1.0"})
        try:
            response = urlopen(request, timeout=40)
        except HTTPError as error:
            response = error
        with response:
            body = response.read(cap + 1)
            resolved, redacted = redact_resolved_url(response.geturl())
            record.update({"http_status": response.status, "resolved_url": resolved, "resolved_signed_query_redacted": redacted, "content_type": response.headers.get("Content-Type"), "declared_content_length": response.headers.get("Content-Length")})
        if len(body) > cap:
            record["status"] = "rejected_over_byte_limit"
            body = body[:cap]
            record["body_is_truncated"] = True
        else:
            record["status"] = "ok" if record["http_status"] == 200 else "http_failure"
            record["body_is_truncated"] = False
        target = RAW / f"{name}.body"
        target.write_bytes(body)
        record.update({"saved_response_path": str(target), "saved_bytes": len(body), "saved_sha256": sha256(body).hexdigest()})
    except Exception as error:
        record.update({"status": "transport_failure", "error_type": type(error).__name__, "error": str(error)})
    record["request_finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    return record


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    selected = [spec for spec in SPECS if not sys.argv[1:] or spec[0] in sys.argv[1:]]
    existing = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(retrieve, selected))
    LOG.write_text(json.dumps(existing + records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in records:
        print(item["id"], item["status"], item.get("http_status"), item.get("saved_bytes"))
