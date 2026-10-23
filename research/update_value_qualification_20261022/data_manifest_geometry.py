"""Metadata-only parent/scaffold/source-plate dependence geometry."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_value_qualification/data'
paths = [OUT / 'PRISM_METADATA_QUALIFICATION.json', OUT / 'METADATA_FOLLOWUP.json']
prism, follow = [json.loads(p.read_text(encoding='utf-8')) for p in paths]
header = set(follow['matrices']['secondary-screen-logfold-change.csv']['header'][1:])
missing = {r['core'] for r in prism['treatment_catalog'] if set(r['replicate_columns'].values()) - header}
unresolved = {r['core'] for r in prism['treatment_catalog'] if r['parent_resolution'] != 'RESOLVED'}
records = [r for r in prism['treatment_catalog'] if r['core'] not in missing | unresolved]


def components(include_plate, include_empty):
    parent = list(range(len(records)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    seen = {}
    for i, r in enumerate(records):
        keys = [('parent', r['nonisomeric_largest_fragment'][0])]
        scaffold = r['murcko_scaffolds'][0]
        if scaffold or include_empty:
            keys.append(('scaffold', scaffold))
        if include_plate:
            keys.append(('compound_plate', r['compound_plate']))
        for key in keys:
            if key in seen:
                union(i, seen[key])
            else:
                seen[key] = i
    groups = defaultdict(list)
    for i, r in enumerate(records):
        groups[find(i)].append(r['core'])
    values = sorted((sorted(v) for v in groups.values()), key=lambda v: (-len(v), v))
    return {'component_sizes': [len(v) for v in values], 'components': values}


plates = sorted({r['compound_plate'] for r in records})
plate_reports = []
for plate in plates:
    held = [r for r in records if r['compound_plate'] == plate]
    rest = [r for r in records if r['compound_plate'] != plate]
    held_keys = {(kind, r[field][0]) for r in held for kind, field in
                 [('parent', 'nonisomeric_largest_fragment'), ('scaffold', 'murcko_scaffolds')]}
    rest_keys = {(kind, r[field][0]) for r in rest for kind, field in
                 [('parent', 'nonisomeric_largest_fragment'), ('scaffold', 'murcko_scaffolds')]}

    def safe(r, other):
        return (('parent', r['nonisomeric_largest_fragment'][0]) not in other
                and ('scaffold', r['murcko_scaffolds'][0]) not in other)

    plate_reports.append({'compound_plate': plate, 'heldout_initial': len(held), 'source_initial': len(rest),
        'heldout_retained_if_all_other_plates_frozen_source': sum(safe(r, rest_keys) for r in held),
        'source_retained_if_whole_plate_frozen_heldout': sum(safe(r, held_keys) for r in rest),
        'purge_rule': 'Exclude any exact-parent OR exact-Murcko overlap; empty Murcko included. No response filtering.'})
graphs = {
    'parent_OR_exact_murcko_including_empty': components(False, True),
    'parent_OR_exact_murcko_including_empty_OR_compound_plate': components(True, True),
    'descriptive_sensitivity_parent_OR_nonempty_murcko_OR_plate': components(True, False)}
result = {'response_values_converted': False,
    'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    'metadata_triples': len(prism['treatment_catalog']), 'missing_header_cores': sorted(missing),
    'unresolved_structure_cores': sorted(unresolved), 'excluded_intersection': sorted(missing & unresolved),
    'eligible_after_union_exclusion': len(records), 'compound_plates': len(plates),
    'empty_murcko_cores': [r['core'] for r in records if r['murcko_scaffolds'][0] == ''],
    'empty_murcko_policy': 'Included as exact scaffold block in main graph; omitted only in clearly labeled descriptive sensitivity, never proof of independence',
    'graphs': graphs, 'per_plate_holdout_purge': plate_reports,
    'interpretation': 'Dependence-blocking geometry, not authenticated statistical independence. Controls/pool/ComBat/cell contexts may connect additional units; do not choose test plates or thresholds from this feasibility report.'}
assert len(records) == len(prism['treatment_catalog']) - len(missing | unresolved)
assert all(sum(g['component_sizes']) == len(records) for g in graphs.values())
(OUT / 'MANIFEST_GEOMETRY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'missing_header_cores': sorted(missing), 'unresolved': len(unresolved),
                  'intersection': sorted(missing & unresolved), 'eligible': len(records), 'plates': len(plates),
                  'empty_murcko': len(result['empty_murcko_cores']),
                  'graphs': {k: {'count': len(v['component_sizes']), 'largest_sizes': v['component_sizes'][:15]} for k, v in graphs.items()},
                  'plate_holdout_target_retained_range': [min(v['heldout_retained_if_all_other_plates_frozen_source'] for v in plate_reports), max(v['heldout_retained_if_all_other_plates_frozen_source'] for v in plate_reports)],
                  'plate_holdout_source_retained_range': [min(v['source_retained_if_whole_plate_frozen_heldout'] for v in plate_reports), max(v['source_retained_if_whole_plate_frozen_heldout'] for v in plate_reports)]}))
