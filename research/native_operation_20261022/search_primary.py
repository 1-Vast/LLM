"""Four bounded arXiv metadata queries; retain raw response and access receipts."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/native_operation/root/search'
QUERIES = {
    'algorithm_discovery': 'all:"DiscoRL" OR (ti:"discovering" AND ti:"algorithms" AND cat:cs.LG)',
    'learned_optimizers': '(ti:"optimizer" OR ti:"optimization") AND (ti:"learned" OR ti:"self-improving")',
    'intervention_update': '(ti:"world model" OR ti:"causal") AND (all:"intervention" AND all:"adaptation")',
    'program_credit': '(ti:"program" OR ti:"algorithm") AND (all:"counterfactual" AND all:"credit")'
}


def main():
    label = sys.argv[1]
    query = '(' + QUERIES[label] + ') AND submittedDate:[202501010000 TO 202610222359]'
    OUT.mkdir(parents=True, exist_ok=True)
    receipt_path = OUT / (label + '.receipt.json')
    assert not receipt_path.exists()
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'query': query,
               'params': {'search_query': query, 'max_results': 6, 'sortBy': 'submittedDate', 'sortOrder': 'descending'},
               'max_body_bytes': 2000000, 'timeout_seconds': 45}
    entries = []
    try:
        response = requests.get('https://export.arxiv.org/api/query', params=receipt['params'], timeout=45)
        assert len(response.content) <= receipt['max_body_bytes']
        with (OUT / (label + '.body')).open('xb') as handle:
            handle.write(response.content)
        receipt.update(status=response.status_code, final_url=response.url, bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 200:
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            for entry in ET.fromstring(response.content).findall('a:entry', ns):
                entries.append({key: entry.findtext('a:' + key, namespaces=ns)
                                for key in ('id', 'title', 'published', 'updated', 'summary')})
            with (OUT / (label + '.entries.json')).open('x', encoding='utf-8') as handle:
                json.dump(entries, handle, indent=2)
    except Exception as exc:
        receipt.update(error_type=type(exc).__name__)
    with receipt_path.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
    print(json.dumps({'label': label, **receipt, 'entries': [{k: v for k, v in e.items() if k != 'summary'} for e in entries]}))


if __name__ == '__main__':
    main()
