"""Four bounded metadata queries using installed lit-survey HTTP client; no full text."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, 'D:/CodexData/.codex/skills/lit-survey/scripts')
from _common import http_get

out = Path(__file__).parent / 'sources' / 'P1_structural'
out.mkdir(parents=True, exist_ok=True)
queries = [
    ('P1-q1_schedule', 'TITLE_ABS:(("sequential" OR "order-dependent") AND ("drug combination" OR "drug combinations") AND ("priming" OR "memory" OR "schedule"))'),
    ('P1-q2_measurement', 'TITLE_ABS:(("drug sensitivity" OR "drug response") AND ("assay" OR "measurement") AND ("calibration" OR "growth rate" OR "reproducibility"))'),
    ('P1-q3_hysteresis', 'TITLE_ABS:(("drug" OR "pharmacodynamic") AND ("hysteresis" OR "persistent state") AND ("washout" OR "cancer"))'),
    ('P1-q4_bridges', 'TITLE_ABS:(("drug screening" OR "drug response") AND ("cross-platform" OR "cross-study") AND ("reference" OR "calibration" OR "harmonization"))'),
]
for tag, query in queries:
    params = {'query': query, 'format': 'json', 'pageSize': 20, 'resultType': 'core', 'sort': 'CITED desc'}
    record = {'tag': tag, 'query': query, 'params': params, 'source': 'Europe PMC', 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'metadata and abstracts only; no date limit; 20 highest cited results'}
    try:
        response = http_get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params, source='EuropePMC', raw=True)
        raw = response if isinstance(response, bytes) else response.encode('utf-8')
        (out / (tag + '_raw.json')).write_bytes(raw)
        record.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        parsed = json.loads(raw)
        record['hitCount'] = parsed.get('hitCount')
        results = parsed.get('resultList', {}).get('result', [])
        print(json.dumps({'tag': tag, 'hitCount':record['hitCount'], 'results':[{'title': r.get('title'), 'doi':r.get('doi'), 'pmcid':r.get('pmcid'), 'year':r.get('pubYear')} for r in results]}, ensure_ascii=False))
    except Exception as exc:
        record['error'] = str(exc)
        print(json.dumps({'tag':tag, 'error':str(exc)},ensure_ascii=False))
    (out / (tag + '_receipt.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
