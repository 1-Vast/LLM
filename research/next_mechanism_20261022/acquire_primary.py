"""Bounded metadata search for longitudinal drug-state/function assets."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/next_mechanism/root/literature'
QUERIES = {
    'temporal_state_function': 'FIRST_PDATE:[2025-01-01 TO 2026-10-22] AND ("single cell" OR "single-cell") AND drug AND ("time-resolved" OR longitudinal) AND (viability OR proliferation OR survival)',
    'live_state_therapy': 'FIRST_PDATE:[2025-01-01 TO 2026-10-22] AND ("live-cell" OR "live cell") AND ("drug response" OR "drug resistance") AND (trajectory OR trajectories OR lineage)',
    'interventional_dynamics': 'FIRST_PDATE:[2025-01-01 TO 2026-10-22] AND ("cell dynamics" OR "cellular dynamics") AND ("world model" OR "system identification" OR "perturbation prediction")',
}


def fetch(item):
    name, query = item
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urlencode(
        {'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 30})
    row = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
            body = response.read(2_000_001)
            row.update(status=response.status, final_url=response.url,
                       bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        with (OUT / (name + '.body')).open('xb') as handle:
            handle.write(body)
        assert len(body) <= 2_000_000
        data = json.loads(body)
        rows = [{key: r.get(key) for key in ('id', 'source', 'pmcid', 'doi', 'title',
                 'firstPublicationDate', 'authorString', 'abstractText', 'fullTextUrlList')}
                for r in data['resultList']['result']]
        with (OUT / (name + '.entries.json')).open('x', encoding='utf-8', newline='\n') as handle:
            json.dump({'hitCount': data['hitCount'], 'records': rows}, handle, indent=2)
        row.update(hit_count=data['hitCount'], records=len(rows))
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = {'utc': datetime.now(timezone.utc).isoformat(), 'before_requests': True,
        'scope': 'public primary metadata/abstracts, no numerical assay data',
        'queries': QUERIES, 'max_records_per_query': 30,
        'selection': 'Inspect real observation timing, independent units, paired functional endpoints; no novel algorithm assumed',
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with (OUT / 'PROTOCOL.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(protocol, handle, indent=2)
    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(fetch, QUERIES.items()))
    with (OUT / 'RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipts, handle, indent=2)
    print(json.dumps(receipts))


if __name__ == '__main__':
    main()
