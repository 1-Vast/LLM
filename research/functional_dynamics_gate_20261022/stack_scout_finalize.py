"""Seal the bounded scout receipts and source-only count semantics."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/functional_dynamics_gate/functional_auditor'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    requests = []
    for path in sorted(OUT.glob('REQUEST_*.json')):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        body = Path(receipt['body_path'])
        requests.append({'receipt': str(path), 'status': receipt['status'], 'body_bytes': receipt['body_bytes'],
                         'body_hash_matches': sha(body) == receipt['sha256'],
                         'length_matches': body.stat().st_size == receipt['body_bytes'],
                         'redirects_followed': receipt['redirects_followed'],
                         'automatic_retries': receipt['automatic_retries'],
                         'timeout_seconds': receipt['timeout_seconds'], 'disposition': receipt['disposition']})
    if len(requests) != 6 or not all(row['body_hash_matches'] and row['length_matches'] for row in requests):
        raise ValueError('scout_receipt_integrity_failure')
    primary = OUT / 'RESPONSE_05_05_primary_efetch.body'
    root = ET.fromstring(primary.read_bytes())
    sections = []
    for section in root.iter('sec'):
        title = section.findtext('title') or ''
        if title in ['Lethal fraction scoring', 'Lag exponential death (LED) model fitting'] or 'curve fitting' in title.lower():
            sections.append({'title': title, 'text': ' '.join(''.join(section.itertext()).split())})
    output = {
        'utc': datetime.now(timezone.utc).isoformat(), 'status': 'SIX_GET_SCOUT_COMPLETE_NO_MORE_NETWORK',
        'requests': requests, 'GET_count': len(requests), 'total_body_bytes': sum(row['body_bytes'] for row in requests),
        'source_response_array_access': False, 'primary_aggregate_outcome_exposure': True,
        'exact_raw_file_manifest_authenticated': False, 'source_semantics_primary_sha256': sha(primary),
        'source_semantics_sections': sections,
        'draft_sha256_before_cross_finalization': sha(OUT / 'DRAFT.md'),
        'cross_question_sha256': sha(OUT / 'CROSS_QUESTIONS_TO_ADVOCATE.md'),
        'cross_reply_sha256': sha(OUT / 'REPLY_TO_ADVOCATE.md'),
        'decision': 'Primary-supported STACK lead; exact raw object still unqualified. Continue only a separately scoped source, not further GETs by this scout.'}
    with (OUT / 'SCOUT_CHECKS.json').open('x', encoding='utf-8') as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
    print(json.dumps({key: output[key] for key in ['status', 'GET_count', 'total_body_bytes',
                                                  'source_response_array_access', 'exact_raw_file_manifest_authenticated']}))


if __name__ == '__main__':
    main()
