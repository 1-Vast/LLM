"""One bounded disconfirming prior query; metadata/abstracts only."""
from pathlib import Path
import json
import time
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parent / "root_sources"
receipt = root / "selection_prior_request.json"
assert not receipt.exists(), "No query replay"
query = '(selection AND (induced OR induction) AND (sensitization OR "drug tolerance" OR "drug sensitivity") AND (bound OR bounds OR "fluctuation analysis"))'
url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
    {"query": query, "format": "json", "pageSize": 30, "resultType": "core"})
record = {"query": query, "url": url, "date": "2026-10-29", "scope": "no year filter; biological selection-versus-induction aliases", "timeout_seconds": 25, "automatic_retries": 0}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
start = time.monotonic()
try:
    with urllib.request.build_opener(NoRedirect).open(url, timeout=25) as response:
        body = response.read(2000001)
        record.update(status=response.status, bytes_read=len(body))
        assert len(body) <= 2000000
        (root / "selection_prior_query.json").write_bytes(body)
        data = json.loads(body)
        record.update(total_hits=data.get("hitCount"), returned=len(data.get("resultList", {}).get("result", [])))
        print(json.dumps([{k: row.get(k) for k in ["title", "doi", "pmcid", "firstPublicationDate"]}
                          for row in data.get("resultList", {}).get("result", [])], ensure_ascii=False))
except Exception as error:
    record.update(error_type=type(error).__name__, detail=str(error))
record["elapsed_seconds"] = time.monotonic() - start
receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
