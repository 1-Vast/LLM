"""Fail closed when the exact source ID chemical dictionary is unavailable."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/az_chemical_identity'
projection = json.loads((OUT / 'SOURCE_ID_PROJECTION.json').read_text(encoding='utf-8'))
if (OUT / 'EMS194010-supplement-Table_S2.xlsx').exists():
    raise SystemExit('S2 exists: inspect its exact identity fields before finalizing')

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

dictionary = []
for source_id in projection['source_drug_ids']:
    dictionary.append({'source_drug_id': source_id, 'chemical_name': None,
                       'structure_identifier': None, 'chemical_equivalence_group': None,
                       'salt_formulation_dose_equivalence': 'NOT_ESTABLISHED',
                       'resolution': 'UNRESOLVED',
                       'in_current_design': source_id in projection['design_ids'],
                       'reason': 'Exact primary-source ID-to-chemical dictionary not recovered'})
save('CHEMICAL_DICTIONARY.json', {'status': 'UNRESOLVED', 'records': dictionary})
save('UNRESOLVED.json', {'all_source_ids': projection['source_drug_ids'],
                         'current_design_ids': projection['design_ids'],
                         'unsupported_merges': [], 'guessed_names': []})
qualification = {'status': 'NOT_ESTABLISHED', 'source_id_pair_disjoint': True,
                 'query_pairs': projection['query_pairs'], 'target_pairs': projection['target_pairs'],
                 'cross_pool_source_id_pair_overlap': projection['source_id_pair_overlap'],
                 'cross_pool_chemical_pair_overlap': None,
                 'cross_pool_comparisons_with_unresolved_identity':
                     len(projection['query_pairs']) * len(projection['target_pairs']),
                 'alias_leakage_established': False,
                 'chemical_independence_established': False,
                 'panel_modified': False,
                 'performance_used_for_identity_qualification': False,
                 'inference_limit': 'Source-ID-pair prediction remains the defined task; chemical-pair novelty is unverified.'}
save('PAIR_QUALIFICATION.json', qualification)

http = []
for receipt_path in sorted(OUT.glob('s2_attempt_*.http.json')):
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    body_path = receipt_path.with_name(receipt_path.name.replace('.http.json', '.body'))
    actual = hashlib.sha256(body_path.read_bytes()).hexdigest()
    assert actual == receipt['sha256']
    http.append({'receipt': receipt_path.name, 'status': receipt['status'],
                 'url': receipt['url'], 'utc': receipt['utc'],
                 'retained_body_sha256': actual, 'body_hash_pass': True,
                 'body_complete': receipt.get('body_complete', True)})
assert len(http) == 4
local = json.loads((OUT / 'LOCAL_PRIMARY_PROJECTION.json').read_text(encoding='utf-8'))
local_checks = []
for item in local['local_source_receipts']:
    actual = hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest()
    assert actual == item['sha256']
    local_checks.append({'path': item['path'], 'sha256': actual, 'unchanged': True})
for relative, expected in projection['local_source_sha256'].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert actual == expected
    if relative not in [item['path'] for item in local_checks]:
        local_checks.append({'path': relative, 'sha256': actual, 'unchanged': True})
assert len(dictionary) == 46
assert sum(item['in_current_design'] for item in dictionary) == 11
assert not qualification['cross_pool_source_id_pair_overlap']
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'new_http_attempts': http,
           'all_http_body_hashes_pass': True, 'previous_local_sources_unchanged': local_checks,
           'source_ids': 46, 'current_design_ids': 11, 'resolved_ids': 0,
           'source_csv_opened': False, 'paid_arrays_opened': False,
           'model_outcomes_opened': False, 'reserve_numerical_responses_opened': False,
           'compressed_supplement_archive_prefix_retained': True,
           'non_s2_entries_decoded': False,
           'supplement_numerical_outcome_fields_decoded_or_used': False,
           'published_paper_narrative_read': True,
           'panel_modified': False, 'status': 'NOT_ESTABLISHED'}
save('QUALIFICATION_RECEIPT.json', receipt)
files = sorted(path for directory in (OUT, ROOT / 'research/az_chemical_identity_20261022')
               for path in directory.iterdir() if path.is_file() and path.name != 'INTEGRITY.json')
save('INTEGRITY.json', {'utc': receipt['utc'],
                       'excludes_self': True,
                       'files': [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                 for path in files]})
print(json.dumps({'status': receipt['status'], 'source_ids': 46,
                  'resolved_ids': 0, 'current_design_ids': 11,
                  'http_body_hashes_pass': True, 'previous_sources_unchanged': len(local_checks)}))
