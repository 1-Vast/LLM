"""PRISM metadata-only feasibility census; no response matrix is opened."""
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog('rdApp.*')
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/external/prism_19q4/raw'
OUT = ROOT / 'log/20261022/update_value_qualification/data'
used = {}
def read(name):
    path = RAW / name
    used[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))
def count(rows, key):
    return dict(sorted(Counter(row[key] for row in rows).items()))
rows = read('secondary-screen-replicate-treatment-info.csv')
cells = read('secondary-screen-cell-line-info.csv')
pools = read('secondary-screen-pooling-info.csv')
primary = read('primary-screen-replicate-collapsed-treatment-info.csv')
by_screen = {}
for screen in sorted({row['screen_id'] for row in rows}):
    group = [row for row in rows if row['screen_id'] == screen]
    experimental = [row for row in group if row['perturbation_type'] == 'experimental_treatment']
    by_screen[screen] = {'metadata_rows': len(group), 'types': count(group, 'perturbation_type'),
        'experimental_columns': len(experimental), 'full_broad_ids': len({r['broad_id'] for r in experimental}),
        'broad_cores': len({r['broad_id'][:13] for r in experimental}),
        'detection_plates': len({r['detection_plate'] for r in group}),
        'compound_plates': len({r['compound_plate'] for r in group}),
        'exact_doses_uM': sorted({r['dose'] for r in experimental}, key=Decimal)}
eligible = [r for r in rows if r['screen_id'] == 'HTS002'
            and r['perturbation_type'] == 'experimental_treatment' and Decimal(r['dose']) == Decimal('2.5')]
groups = defaultdict(list)
for row in eligible:
    groups[(row['broad_id'][:13], row['broad_id'], row['compound_plate'], row['well'])].append(row)
triples, excluded, ambiguity = {}, [], []
for key, group in sorted(groups.items()):
    reps = defaultdict(list)
    for row in group:
        match = re.search(r'_(X[123])(?:[_.]|$)', row['detection_plate'])
        reps[match.group(1) if match else 'UNPARSED'].append(row)
    if not {'X1', 'X2', 'X3'} <= reps.keys() or any(len(reps[k]) != 1 for k in ('X1', 'X2', 'X3')):
        excluded.append({'key': list(key), 'replicate_counts': {k: len(v) for k, v in reps.items()}})
        continue
    if key[0] in triples:
        continue  # First metadata-lexical complete treatment per core; no outcome filtering.
    strings = {part.strip() for row in group for part in row['smiles'].split(',') if part.strip() not in ('', 'NA')}
    exact, parent, scaffold = set(), set(), set()
    unparsed = []
    for text in strings:
        mol = Chem.MolFromSmiles(text)
        if mol is None:
            unparsed.append(text)
            continue
        exact.add(Chem.MolToSmiles(mol, isomericSmiles=True))
        fragments = Chem.GetMolFrags(mol, asMols=True)
        main = max(fragments, key=lambda m: (sum(a.GetAtomicNum() == 6 for a in m.GetAtoms()), m.GetNumHeavyAtoms()))
        parent.add(Chem.MolToSmiles(main, isomericSmiles=False))
        scaffold.add(MurckoScaffold.MurckoScaffoldSmiles(mol=main, includeChirality=False))
    resolved = len(parent) == 1 and not unparsed
    record = {'core': key[0], 'full_broad_id': key[1], 'compound_plate': key[2], 'well': key[3],
        'replicate_columns': {k: reps[k][0]['column_name'] for k in ('X1', 'X2', 'X3')},
        'replicate_detection_plates': {k: reps[k][0]['detection_plate'] for k in ('X1', 'X2', 'X3')},
        'names': sorted({r['name'] for r in group}), 'exact_canonical_smiles': sorted(exact),
        'nonisomeric_largest_fragment': sorted(parent), 'murcko_scaffolds': sorted(scaffold),
        'structure_parse_failures': unparsed, 'parent_resolution': 'RESOLVED' if resolved else 'UNRESOLVED',
        'identity_limit': 'Parent grouping is a chemical-dependence blocking variable, not treatment/salt/dose equivalence.'}
    triples[key[0]] = record
    if not resolved:
        ambiguity.append(key[0])
passed = {r['row_name']: r for r in cells if r['passed_str_profiling'].upper() == 'TRUE' and r['depmap_id'] not in ('', 'NA')}
pool_rows = [r for r in pools if r['screen_id'] == 'HTS002' and r['row_name'] in passed]
contexts = sorted({r['row_name'] for r in pool_rows})
context_mapping = {key: {'depmap_id': passed[key]['depmap_id'], 'tissue': passed[key]['primary_tissue'],
    'pool_ids': sorted({r['pool_id'] for r in pool_rows if r['row_name'] == key}),
    'detection_pools': sorted({r['detection_pool'] for r in pool_rows if r['row_name'] == key})} for key in contexts}
parent_groups, scaffold_groups = defaultdict(list), defaultdict(list)
for core, record in triples.items():
    if record['parent_resolution'] == 'RESOLVED':
        parent_groups[record['nonisomeric_largest_fragment'][0]].append(core)
        scaffold_groups[record['murcko_scaffolds'][0]].append(core)
primary_cores = {row['broad_id'][:13] for row in primary}
nominal_columns = 3 * len(triples)
result = {'metadata_hashes': used, 'response_files_opened': False, 'by_screen': by_screen,
    'hts002_exact_2p5uM': {'experimental_metadata_rows': len(eligible), 'candidate_treatments': len(groups),
        'complete_core_triples': len(triples), 'excluded_incomplete_or_duplicate_treatments': excluded,
        'unresolved_structure_cores': ambiguity, 'structurally_resolved_cores': len(triples) - len(ambiguity),
        'distinct_resolved_parents': len(parent_groups), 'distinct_exact_murcko_scaffolds': len(scaffold_groups),
        'largest_scaffold_group': max(map(len, scaffold_groups.values()), default=0),
        'parent_alias_groups': [v for v in parent_groups.values() if len(v) > 1],
        'eligible_context_rows': len(contexts), 'distinct_depmap_ids': len({v['depmap_id'] for v in context_mapping.values()}),
        'tissues': dict(Counter(v['tissue'] for v in context_mapping.values())),
        'pool_ids': sorted({r['pool_id'] for r in pool_rows}),
        'multi_pool_contexts': [k for k, v in context_mapping.items() if len(v['pool_ids']) > 1],
        'primary_core_overlap': sum(core in primary_cores for core in triples),
        'nominal_profile_columns': nominal_columns,
        'nominal_response_field_slots_all_triples': nominal_columns * len(contexts),
        'nominal_slots_per_profile': len(contexts),
        'actual_finite_slots': 'UNREAD; requires a separately authorized numerical conversion stage',
        'replicate_independence': 'NOT_ESTABLISHED: shared released ComBat/control processing; independent cultures not authenticated',
        'exposure': 'Previously exposed internal development; resplitting cannot establish fresh confirmation'},
    'contexts': context_mapping, 'treatment_catalog': list(triples.values()),
    'scaffold_groups': list(scaffold_groups.values()),
    'physical_cost_limit': 'Released profile fields can be priced exactly as catalog slots; original assay/control/all-attempt wet costs not reconstructed.'}
(OUT / 'PRISM_METADATA_QUALIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
summary = dict(result['hts002_exact_2p5uM'])
summary['excluded_incomplete_or_duplicate_treatments'] = len(excluded)
summary['unresolved_structure_cores'] = len(ambiguity)
summary['parent_alias_groups'] = len(summary['parent_alias_groups'])
summary['tissues'] = len(summary['tissues'])
summary['pool_ids'] = len(summary['pool_ids'])
print(json.dumps({'screen_counts': {k: {q: v[q] for q in ('metadata_rows', 'experimental_columns', 'broad_cores')} for k, v in by_screen.items()}, 'summary': summary}, ensure_ascii=False))
