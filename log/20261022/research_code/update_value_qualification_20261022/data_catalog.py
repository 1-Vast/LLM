"""Construct a metadata-only released-profile field contract, not a fit registration."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_value_qualification/data'
prism = json.loads((OUT / 'PRISM_METADATA_QUALIFICATION.json').read_text(encoding='utf-8'))
follow = json.loads((OUT / 'METADATA_FOLLOWUP.json').read_text(encoding='utf-8'))
header = set(follow['matrices']['secondary-screen-logfold-change.csv']['header'][1:])
complete, excluded = [], []
for record in prism['treatment_catalog']:
    absent = sorted(set(record['replicate_columns'].values()) - header)
    if absent:
        excluded.append({'core': record['core'], 'reason': 'RELEASED_PROFILE_HEADER_ABSENT', 'absent': absent})
    else:
        complete.append(record)
resolved = [r for r in complete if r['parent_resolution'] == 'RESOLVED']
for record in complete:
    if record['parent_resolution'] != 'RESOLVED':
        excluded.append({'core': record['core'], 'reason': 'UNRESOLVED_CHEMISTRY_FOR_BLOCKED_SPLIT'})
pool_rows = {}
for row, info in prism['contexts'].items():
    assert len(info['pool_ids']) == 1
    pool_rows.setdefault(info['pool_ids'][0], []).append(row)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


depmap = ROOT / 'data/external/depmap_19q4'
sample_path = depmap / 'sample_info.csv'
with sample_path.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.DictReader(stream)
    sample_schema = reader.fieldnames
    samples = list(reader)
expression_path = depmap / 'CCLE_expression.csv'
with expression_path.open('rb') as stream:
    expression_header = next(csv.reader([stream.readline().decode('utf-8-sig')]))
    expression_ids = []
    for line in stream:
        first = line.split(b',', 1)[0]
        assert b'"' not in first and first.strip()
        expression_ids.append(first.decode('utf-8'))
mutation_path = depmap / 'CCLE_mutations.csv'
with mutation_path.open(encoding='utf-8-sig', newline='') as stream:
    mutation_schema = next(csv.reader(stream))
mutation_id_field = next(k for k in ('DepMap_ID', 'DepMapID', 'depmap_id') if k in mutation_schema)
mutation_ids = set(pd.read_csv(mutation_path, usecols=[mutation_id_field], dtype=str)[mutation_id_field].dropna())
sample_id_field = next(k for k in ('DepMap_ID', 'DepMapID', 'depmap_id') if k in sample_schema)
sample_ids = {s[sample_id_field] for s in samples}
selected_ids = {i['depmap_id'] for i in prism['contexts'].values()}
join = {'eligible_prism_depmap_ids': len(selected_ids),
        'sample_info_join': len(selected_ids & sample_ids),
        'expression_id_join': len(selected_ids & set(expression_ids)),
        'mutation_any_record_join': len(selected_ids & mutation_ids),
        'expression_and_mutation_join': len(selected_ids & set(expression_ids) & mutation_ids),
        'missing_expression_ids': sorted(selected_ids - set(expression_ids)),
        'no_mutation_record_ids': sorted(selected_ids - mutation_ids),
        'mutation_limit': 'No variant record does not authenticate absence of mutations; no variant values converted.'}
depmap_record = {'directory': str(depmap.relative_to(ROOT)), 'files': {
    p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in (sample_path, expression_path, mutation_path)},
    'sample_info_schema': sample_schema, 'sample_info_rows': len(samples),
    'expression_columns': len(expression_header) - 1, 'expression_row_ids': len(expression_ids),
    'expression_header': expression_header, 'expression_ids': expression_ids,
    'mutation_schema': mutation_schema, 'mutation_id_field_only_converted': mutation_id_field,
    'join': join, 'expression_values_or_mutation_variant_values_converted': False}
(OUT / 'DEPMAP_METADATA_JOIN.json').write_text(json.dumps(depmap_record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
result = {'status': 'FIELD_CONTRACT_ONLY_NOT_FIT_REGISTRATION',
          'source': 'data/external/prism_19q4/raw/secondary-screen-logfold-change.csv',
          'source_sha256': follow['matrices']['secondary-screen-logfold-change.csv']['sha256'],
          'response_values_converted': False, 'finite_coverage': 'UNREAD',
          'metadata_complete_triples': len(prism['treatment_catalog']),
          'header_complete_triples': len(complete), 'header_complete_chemistry_resolved': len(resolved),
          'excluded': excluded, 'eligible_contexts': prism['contexts'],
          'pool_rows': {k: sorted(v) for k, v in sorted(pool_rows.items())},
          'pool_slots': {k: len(v) for k, v in sorted(pool_rows.items())},
          'released_field_address': ['row_name', 'column_name'],
          'paid_unit': ['pool_id', 'compound_plate', 'well', 'replicate'],
          'full_profile_pool_units': len(pool_rows),
          'full_profile_nominal_field_slots': len(prism['contexts']),
          'header_complete_all_triplicate_nominal_slots': 3 * len(complete) * len(prism['contexts']),
          'chemistry_resolved_all_triplicate_nominal_slots': 3 * len(resolved) * len(prism['contexts']),
          'released_slot_cost_limit': 'Nominal released fields; finite/QC/wet control/all-attempt costs unqualified',
          'grouping_limit': 'Parents/scaffolds/plates/pools/control/ComBat dependencies; group IDs do not prove independence',
          'task_alternatives_not_to_merge': {
              'cross_chemical_adaptation': 'X1 feedback chemicals -> different chemistry-blocked X2/X3 audit chemicals',
              'compound_profile_completion': 'Target compound X1 paid whole pools -> same compound unpaid pools X2/X3'},
          'catalog': resolved, 'depmap_metadata_join': join}
assert len(complete) == 1279 and len(prism['contexts']) == 481
assert all(len(r['replicate_columns']) == 3 for r in resolved)
(OUT / 'FIELD_CONTRACT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'header_complete': len(complete), 'resolved': len(resolved), 'excluded': excluded,
                  'pool_slots': result['pool_slots'], 'depmap_join': join,
                  'depmap_hashes': depmap_record['files'],
                  'nominal_slot_totals': {k: result[k] for k in ('header_complete_all_triplicate_nominal_slots', 'chemistry_resolved_all_triplicate_nominal_slots')}}))
