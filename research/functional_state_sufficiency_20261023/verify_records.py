"""Check retained local receipts; no requests, biological values or model fitting."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/functional_state_sufficiency'
DATA = ROOT / 'data/external/research_sources/20261023/functional_state_sufficiency'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    checks = []
    for role in ('biology', 'constructive', 'frontier'):
        for path in sorted((OUT / role).glob('*.json')):
            receipt = json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(receipt, dict) or not {'url', 'status', 'sha256', 'bytes'} <= receipt.keys():
                continue
            stem = path.name.removesuffix('.receipt.json').removesuffix('.json')
            body = DATA / role / (stem + '.body')
            ok = (receipt['status'] == 200
                  and body.stat().st_size == receipt['bytes']
                  and digest(body) == receipt['sha256'])
            checks.append({'receipt': str(path.relative_to(OUT)), 'pass': ok})
    api = json.loads((OUT / 'api/RECEIPT.json').read_text(encoding='utf-8-sig'))
    usage = api['provider_usage']
    api_ok = (api['prompt_sha256'] == digest(OUT / 'api/PROMPT.md')
              and usage['prompt_tokens'] + usage['completion_tokens'] == usage['total_tokens']
              and api['generated_code_executed'] is False)
    reports = [OUT / role / name for role in ('biology', 'constructive', 'frontier')
               for name in ('INDEPENDENT.md', 'API_REVIEW.md', 'CROSS.md')]
    result = {'scope': 'Local retained receipts only; not scientific replication or global provenance repair',
              'public_get_receipts': checks, 'api_prompt_and_usage_pass': api_ok,
              'api_total_tokens': usage['total_tokens'],
              'review_files': {str(p.relative_to(OUT)): digest(p) for p in reports},
              'pass': len(checks) == 8 and all(c['pass'] for c in checks) and api_ok}
    (OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['pass']:
        raise SystemExit(1)
