"""Verify this reviewer's immutable source captures and report inventory."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/data'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = OUT / 'INTEGRITY_AND_INVENTORY.json'
    assert not target.exists()
    assert digest(OUT / 'INDEPENDENT.md') == '54d54f7199866c186df2a951c6818ed331702fb2774d1565bc12d35962121f96'
    receipts = sorted(OUT.glob('*.http.json'))
    assert len(receipts) == 4
    requests = []
    for path in receipts:
        receipt = json.loads(path.read_text(encoding='utf-8'))
        body = path.with_name(path.name.replace('.http.json', '.body'))
        assert digest(body) == receipt['sha256']
        assert body.stat().st_size == receipt['bytes']
        assert receipt['status'] == 200 and 'error' not in receipt
        assert not receipt['automatic_retries'] and not receipt['automatic_redirects']
        requests.append({'receipt': path.name, 'body_bytes': body.stat().st_size,
                         'body_sha256': digest(body), 'status': receipt['status']})
    mix = json.loads((OUT / 'MIX_HISTORY_AND_SCHEMA.json').read_text(encoding='utf-8'))
    assert not any(mix[key] for key in ('expression_values_read', 'functional_values_read',
                                      'treated_cell_abundance_computed'))
    for record in mix['historical_records'].values():
        assert digest(ROOT / record['saved']) == record['sha256']
    tggates = json.loads((OUT / 'TGGATES_THREE_DOSE_IDENTITY.json').read_text(encoding='utf-8'))
    assert tggates['results']['LDH']['three_declared_positive_dose_compounds'] == 51
    assert tggates['results']['both']['three_declared_positive_dose_compounds'] == 47
    records = {'data_tggates_menu.py': tggates,
               'data_watermelon_audit.py': json.loads((OUT / 'WATERMELON_DESIGN_AUDIT.json').read_text(encoding='utf-8')),
               'data_watermelon_keys.py': json.loads((OUT / 'WATERMELON_KEY_AUDIT.json').read_text(encoding='utf-8'))}
    for filename, record in records.items():
        assert digest(Path(__file__).with_name(filename)) == record['script_sha256']
    inventory = [{'path': str(path.relative_to(ROOT)).replace('\\', '/'),
                  'bytes': path.stat().st_size, 'sha256': digest(path)}
                 for path in sorted(OUT.iterdir()) if path.is_file()]
    code = [{'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': digest(path)}
            for path in sorted(Path(__file__).parent.glob('data_*.py'))]
    result = {'status': 'PASS_REVIEWER_SOURCE_AND_RECORD_INTEGRITY',
              'reviewer_gets': requests, 'reviewer_new_http_requests': len(requests),
              'reviewer_http_body_bytes': sum(item['body_bytes'] for item in requests),
              'new_model_fits': 0, 'new_provider_calls': 0,
              'protected_or_reserve_access': False, 'expression_or_numeric_response_values_opened': False,
              'inventory_excludes_this_self_referential_receipt': True,
              'files': inventory, 'research_code': code,
              'limits': 'Identity/schema/integrity checks only, no biological performance or new-core qualification'}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'reviewer_new_http_requests',
                     'reviewer_http_body_bytes', 'new_model_fits', 'new_provider_calls')}, indent=2))
    print(json.dumps({'receipt_sha256': digest(target),
                      'cross_sha256': digest(OUT / 'CROSS.md')}, indent=2))


if __name__ == '__main__':
    main()
