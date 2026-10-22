"""Build one fixed, outcome-free PRISM profile-completion population."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/prism_profile_opportunity'
PREVIOUS = ROOT / 'log/20261022/update_value_qualification'
SEED = 'prism-profile-20261022-v1'


def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def chemical_keys(record):
    return {('parent', record['nonisomeric_largest_fragment'][0]),
            ('scaffold', record['murcko_scaffolds'][0])}


def build():
    path = PREVIOUS / 'data/PRISM_METADATA_QUALIFICATION.json'
    meta = json.loads(path.read_text(encoding='utf-8'))
    geometry = json.loads((PREVIOUS / 'data/MANIFEST_GEOMETRY.json').read_text(encoding='utf-8'))
    excluded = set(geometry['missing_header_cores'] + geometry['unresolved_structure_cores'])
    records = sorted((r for r in meta['treatment_catalog'] if r['core'] not in excluded), key=lambda r: r['core'])
    plates = sorted({r['compound_plate'] for r in records}, key=lambda p: (digest(SEED + '|' + p), p))
    pools = sorted(meta['hts002_exact_2p5uM']['pool_ids'], key=lambda p: (digest(SEED + '|pool|' + p), p))
    raw = {'test': plates[:7], 'development': plates[7:14], 'source': plates[14:]}
    original = {part: [r for r in records if r['compound_plate'] in part_plates] for part, part_plates in raw.items()}
    test_keys = set().union(*(chemical_keys(r) for r in original['test']))
    heldout_keys = set().union(*(chemical_keys(r) for part in ('test', 'development') for r in original[part]))
    retained = {'test': original['test'],
                'development': [r for r in original['development'] if not chemical_keys(r) & test_keys],
                'source': [r for r in original['source'] if not chemical_keys(r) & heldout_keys]}
    contexts = meta['contexts']
    assert len(records) == 1274 and len(contexts) == 481 and len(plates) == 35 and len(pools) == 20
    assert all(len(r['pool_ids']) == 1 for r in contexts.values())
    membership = {part: {r['core'] for r in rows} for part, rows in retained.items()}
    for a, b in (('source', 'development'), ('source', 'test'), ('development', 'test')):
        assert not membership[a] & membership[b]
        assert not (set().union(*(chemical_keys(r) for r in retained[a]))
                    & set().union(*(chemical_keys(r) for r in retained[b])))
    return {'task': 'one_compound_profile_two_paid_X1_pools_to_unpaid_X2_X3', 'seed': SEED,
            'status': 'METADATA_ONLY_FIXED_DESIGN_NOT_A_MODEL_RESULT',
            'source': 'data/external/prism_19q4/raw/secondary-screen-logfold-change.csv',
            'source_sha256': '59fab6f8126cfc57d84a59e11cb67add1c7850da72cc3df6f4f9d6ef0c1808e7',
            'metadata_sha256': sha(path),
            'geometry_sha256': sha(PREVIOUS / 'data/MANIFEST_GEOMETRY.json'),
            'original_plate_assignment': raw, 'paid_pools': pools[:2], 'audit_pools': sorted(pools[2:]),
            'contexts': contexts, 'records': records,
            'retained_ids': {k: sorted(v) for k, v in membership.items()},
            'purged_ids': {part: sorted({r['core'] for r in original[part]} - membership[part]) for part in raw},
            'original_counts': {part: len(rows) for part, rows in original.items()},
            'retained_counts': {part: len(rows) for part, rows in retained.items()},
            'source_minimum_qualified': 300, 'development_minimum_qualified': 80,
            'coverage_rule': {'each_paid_pool_X1_finite_fraction_at_least': 0.8,
                              'each_unpaid_panel_X2_X3_finite_fraction_at_least': 0.8,
                              'test_compound_retention_fraction_at_least': 0.7,
                              'test_plates_with_at_least_10_qualified_compounds': 6,
                              'all_seven_test_plates_must_have_a_qualified_compound': True},
            'statistical_scope': 'Fixed exposed released catalog; no authenticated independent N, CI or prospective biology.',
            'cost': {'target_feedback': '2 whole X1 pool/compound/well bundles; failed/missing fields still charged',
                     'source_profile': 'all 20 pools per replicate; 60 bundles per complete 3-profile compound',
                     'audit': 'protected X2/X3 numeric fields; not policy feedback or free wet validation'}}


if __name__ == '__main__':
    manifest = build()
    write(LOG / 'MANIFEST_v2.json', manifest)
    print(json.dumps({k: manifest[k] for k in ('status', 'original_counts', 'retained_counts', 'paid_pools')}))
