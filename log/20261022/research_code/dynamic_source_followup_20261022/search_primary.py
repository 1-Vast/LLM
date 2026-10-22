"""One retained Europe PMC search per explicitly registered query."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
QUERIES = {
    "antibiotic_evolution": ('TITLE_ABS:antibiotic AND TITLE_ABS:"experimental evolution" '
                             'AND (TITLE_ABS:sequential OR TITLE_ABS:switching OR TITLE_ABS:longitudinal) '
                             'AND FIRST_PDATE:[2023-01-01 TO 2026-10-22]', 30),
    "virtual_cell_2026": ('(TITLE_ABS:"virtual cell" OR TITLE_ABS:"cellular world model") '
                          'AND FIRST_PDATE:[2026-01-01 TO 2026-10-22]', 20),
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


parser = argparse.ArgumentParser()
parser.add_argument("query", choices=QUERIES)
args = parser.parse_args()
out = ROOT / "log/20261022/dynamic_source_followup" / args.query
out.mkdir(parents=True, exist_ok=False)
query, size = QUERIES[args.query]
url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode(
    {"query": query, "format": "json", "resultType": "core", "pageSize": size, "sort": "FIRST_PDATE_D"})
record = {"query": query, "url": url, "started_utc": datetime.now(timezone.utc).isoformat(),
          "requests": 1, "retries": 0, "redirects_followed": 0,
          "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
body = b""
try:
    try:
        response = build_opener(NoRedirect()).open(Request(url, headers={
            "User-Agent": "MAESTRO-primary-literature/1.0"}), timeout=60)
    except HTTPError as error:
        response = error
    with response:
        record["status"] = response.code
        body = response.read(3_000_001)
    if record["status"] != 200 or len(body) > 3_000_000:
        raise RuntimeError("HTTP status or body cap failed")
    data = json.loads(body)
    results = [{k: r.get(k) for k in ("id", "source", "pmid", "pmcid", "doi", "title",
                 "authorString", "firstPublicationDate", "abstractText", "isOpenAccess")}
               for r in data.get("resultList", {}).get("result", [])]
    (out / "PROJECTED.json").write_text(json.dumps({"hitCount": data.get("hitCount"),
        "scope": "PUBLISHED_ABSTRACTS_DESIGN_EXPOSED", "results": results}, indent=2), encoding="utf-8")
    record["projected_results"] = len(results)
    record["hit_count"] = data.get("hitCount")
except Exception as error:
    record["error_type"] = type(error).__name__
finally:
    (out / "SOURCE.body").write_bytes(body)
    record.update({"received_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest(),
                   "ended_utc": datetime.now(timezone.utc).isoformat()})
    (out / "NETWORK.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({k: record.get(k) for k in ("status", "received_bytes", "hit_count", "projected_results", "error_type")}))
raise SystemExit(1 if record.get("error_type") else 0)
