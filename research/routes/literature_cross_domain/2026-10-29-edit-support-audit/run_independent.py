"""Frozen independent identity/chemical-graph reconstruction; no response access."""
import csv
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

CPU_START, WALL_START = time.process_time(), time.monotonic()
import psutil
import pyarrow.parquet as pq
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT_LIMIT = 30 * 1024 * 1024
METALS = {3, 4, 11, 12, 13}
for lower, upper in [(19, 31), (37, 50), (55, 84), (87, 116)]:
    METALS.update(range(lower, upper + 1))
RDLogger.DisableLog('rdApp.warning')
RDLogger.DisableLog('rdApp.error')


def guard():
    proc = psutil.Process()
    while True:
        if (time.process_time() - CPU_START > 120 or
                time.monotonic() - WALL_START > 180 or
                proc.memory_info().rss > 1024 ** 3):
            os.write(2, b'independent resource cap exceeded\n')
            os._exit(86)
        time.sleep(0.05)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def name_key(value):
    return str(value).strip().casefold()


def molecule(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, 'parse'
    if len(Chem.GetMolFrags(mol)) != 1:
        return None, 'disconnected'
    if not any(a.GetAtomicNum() == 6 for a in mol.GetAtoms()):
        return None, 'no_carbon'
    if sum(a.GetFormalCharge() for a in mol.GetAtoms()) != 0:
        return None, 'net_charge'
    if any(a.GetAtomicNum() in METALS for a in mol.GetAtoms()):
        return None, 'metal'
    if mol.GetNumHeavyAtoms() < 6:
        return None, 'too_small'
    return mol, None


def fragment_smiles(fragment):
    for atom in fragment.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetIsotope(0)
            atom.SetAtomMapNum(1)
    params = Chem.RemoveHsParameters()
    params.removeIsotopes = False
    params.removeDummyNeighbors = False
    fragment = Chem.RemoveHs(fragment, params)
    return Chem.MolToSmiles(fragment, canonical=True, isomericSmiles=True)


def decompositions(mol):
    explicit = Chem.AddHs(mol)
    result = set()
    for bond in explicit.GetBonds():
        if bond.IsInRing() or bond.GetBondType() != Chem.BondType.SINGLE:
            continue
        cut = Chem.FragmentOnBonds(explicit, [bond.GetIdx()], addDummies=True)
        atom_sets = Chem.GetMolFrags(cut, asMols=False)
        fragments = Chem.GetMolFrags(cut, asMols=True, sanitizeFrags=True)
        if len(fragments) != 2:
            raise RuntimeError('single acyclic cut did not give two fragments')
        for core_index, var_index in [(0, 1), (1, 0)]:
            core, variable = fragments[core_index], fragments[var_index]
            nc = sum(a.GetAtomicNum() > 1 for a in core.GetAtoms())
            nv = sum(a.GetAtomicNum() > 1 for a in variable.GetAtoms())
            if nc < 6 or nv > 8 or nc < 2 * nv:
                continue
            if nv == 0:
                non_dummy = [a for a in variable.GetAtoms() if a.GetAtomicNum()]
                if len(non_dummy) != 1 or non_dummy[0].GetAtomicNum() != 1:
                    continue
            begin, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            attachment = explicit.GetAtomWithIdx(
                begin if begin in atom_sets[core_index] else end)
            descriptor = (attachment.GetSymbol(), attachment.GetIsAromatic(),
                          attachment.IsInRing(), str(bond.GetBondType()))
            result.add((fragment_smiles(core), fragment_smiles(variable), descriptor))
    return result


def construct_edges(molecules):
    groups = defaultdict(lambda: defaultdict(set))
    for parent, mol in sorted(molecules.items()):
        for core, variable, descriptor in decompositions(mol):
            groups[(core, descriptor)][variable].add(parent)
    edges = set()
    for (core, descriptor), variables in groups.items():
        for v1, v2 in itertools.combinations(sorted(variables), 2):
            for p1, p2 in itertools.product(variables[v1], variables[v2]):
                if p1 != p2:
                    edges.add((v1, v2, descriptor, core, p1, p2))
    return sorted(edges)


def synthetic_sanity():
    smiles = ['c1ccccc1', 'Cc1ccccc1', 'Fc1ccccc1', 'Cc1ccc(F)cc1']
    mols = {}
    for smiles_value in smiles:
        mol, reason = molecule(smiles_value)
        assert reason is None
        mols[Chem.MolToSmiles(mol, isomericSmiles=True)] = mol
    edges = construct_edges(mols)
    a, b, c, d = [Chem.MolToSmiles(Chem.MolFromSmiles(s), isomericSmiles=True)
                   for s in smiles]
    first = {e[:3] for e in edges if set(e[4:]) == {a, b}}
    second = {e[:3] for e in edges if set(e[4:]) == {c, d}}
    assert first & second, 'synthetic H to methyl edit not shared'
    assert not construct_edges({a: mols[a]}), 'self edit admitted'
    assert molecule('[Na+].O=C([O-])c1ccccc1')[1] == 'disconnected'
    assert molecule('C[NH2+]Cc1ccccc1')[1] == 'net_charge'
    return {'benzene_toluene_fluoro_shared_edit': True,
            'self_edit_rejected': True, 'salt_rejected': True,
            'net_charge_rejected': True,
            'shared_keys': sorted(first & second)}


def rows(handle, allowed):
    # Full records are temporarily tokenized; only the whitelisted cells are accessed.
    reader = csv.reader(handle)
    header = next(reader)
    positions = {field: header.index(field) for field in allowed}
    for values in reader:
        yield {field: values[index].strip() for field, index in positions.items()}


def decimal_value(raw):
    try:
        result = Decimal(raw)
    except InvalidOperation:
        return None
    return result if result.is_finite() and result > 0 else None


def q_string(value):
    text = format(value, 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def murcko(core):
    mol = Chem.MolFromSmiles(core)
    return Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol),
                           canonical=True, isomericSmiles=True)


def main():
    sanity = synthetic_sanity()
    if '--sanity' in sys.argv:
        print(json.dumps(sanity, sort_keys=True))
        return
    archive = ROOT / 'tmp/extq1/gsdc_well_stats.zip'
    matrix = ROOT / 'tmp/extq1/gdsc-007_matrix_results.csv'
    source = HERE / 'sources/root_metadata/tahoe_drug_metadata.body'
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in [archive, matrix, source]}
    assert hashes[str(archive.relative_to(ROOT))] == 'e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259'
    assert hashes[str(source.relative_to(ROOT))] == '7a04c7a6611e74c92253163b994ff0a47191928ee7511f1c2ca508cee0e79f28'
    counts = Counter({key: 0 for key in [
        'edges_with_any_cell_q', 'edges_with_two_cell_rectangle',
        'identity_edges', 'identity_edges_with_any_cell_q',
        'identity_edges_with_two_cell_rectangle',
        'identity_edge_project_cell_q_opportunities', 'identity_edge_project_q_rectangles',
        'identity_edge_two_cell_rectangles', 'cross_parent_edge_pairs',
        'cross_parent_identity_edge_pairs', 'cross_parent_identity_pair_project_q_groups',
        'cross_parent_identity_two_cell_rectangles', 'cross_parent_pairs_different_murcko']})
    id_names, name_ids = defaultdict(set), defaultdict(set)

    def identity(drug_id, drug_name):
        if drug_id and drug_name:
            key = name_key(drug_name)
            id_names[drug_id].add(key)
            name_ids[key].add(drug_id)

    with matrix.open(encoding='utf-8-sig', newline='') as handle:
        for row in rows(handle, ['lib1_ID', 'lib1_name', 'lib2_ID', 'lib2_name']):
            counts['matrix_rows'] += 1
            for side in [1, 2]:
                identity(row[f'lib{side}_ID'], row[f'lib{side}_name'])
    selected = {}
    allowed = ['PROJECT_ID', 'MASTER_CELL_ID']
    for side in [1, 2]:
        allowed += [f'lib{side}_drug_id', f'lib{side}_drug', f'lib{side}_conc']
    with zipfile.ZipFile(archive) as package:
        members = sorted(n for n in package.namelist()
                         if 'GDSC007' in n.upper().replace('-', '') and n.lower().endswith('.csv'))
        if not members:
            raise RuntimeError('no protocol GDSC007 CSV member')
        for member in members:
            with package.open(member) as binary:
                with io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as handle:
                    for row in rows(handle, allowed):
                        counts['well_rows'] += 1
                        for side in [1, 2]:
                            drug_id = row[f'lib{side}_drug_id']
                            if not row['PROJECT_ID'] or not row['MASTER_CELL_ID'] or not drug_id:
                                counts['missing_identity_sides'] += 1
                                continue
                            key = (row['PROJECT_ID'], row['MASTER_CELL_ID'], drug_id)
                            ref = row[f'lib{side}_drug']
                            old = selected.get(key)
                            if old is None or ref < old[0]:
                                selected[key] = (ref, set())
                            q = decimal_value(row[f'lib{side}_conc'])
                            if q is None:
                                counts['nonpositive_nonfinite_invalid_dose_sides'] += 1
                                continue
                            old = selected[key]
                            if ref == old[0]:
                                old[1].add(q)
    conflict_ids = {drug_id for drug_id, names in id_names.items()
                    if len(names) != 1 or any(len(name_ids[n]) != 1 for n in names)}
    source_names = defaultdict(set)
    source_molecules = {}
    source_rejections = Counter()
    metadata = pq.read_table(source, columns=['drug', 'canonical_smiles', 'pubchem_cid'])
    for row in metadata.to_pylist():
        counts['source_records'] += 1
        if row['drug'] is None or row['canonical_smiles'] is None:
            source_rejections['missing_name_or_structure'] += 1
            continue
        mol, reason = molecule(str(row['canonical_smiles']))
        canonical = (Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
                     if mol is not None else 'REJECTED:' + str(row['canonical_smiles']))
        name = name_key(row['drug'])
        cid = str(row['pubchem_cid'])
        source_names[name].add((canonical, cid))
        if reason:
            source_rejections[reason] += 1
        else:
            source_molecules[canonical] = mol
    id_structure = {}
    id_exclusions = Counter()
    for drug_id, names in sorted(id_names.items()):
        if drug_id in conflict_ids:
            id_exclusions['id_name_conflict'] += 1
            continue
        name = next(iter(names))
        candidates = source_names.get(name, set())
        if not candidates:
            id_exclusions['exact_name_unmapped'] += 1
        elif len(candidates) != 1:
            id_exclusions['source_name_structure_cid_ambiguous'] += 1
        else:
            canonical, cid = next(iter(candidates))
            if canonical not in source_molecules:
                id_exclusions['structure_rejected'] += 1
            else:
                id_structure[drug_id] = canonical
    used_molecules = {s: source_molecules[s] for s in set(id_structure.values())}
    support = defaultdict(lambda: defaultdict(set))
    for (project, cell, drug_id), (ref, qs) in selected.items():
        if drug_id in id_structure:
            counts['mapped_selected_project_cell_drug'] += 1
            for q in qs:
                support[drug_id][(project, q)].add(cell)
    structure_ids = defaultdict(list)
    for drug_id, canonical in sorted(id_structure.items()):
        structure_ids[canonical].append(drug_id)
    edges = construct_edges(used_molecules)
    edge_records, edge_groups = [], defaultdict(list)
    for index, edge in enumerate(edges):
        v1, v2, descriptor, core, p1, p2 = edge
        instances = []
        for d1, d2 in itertools.product(structure_ids[p1], structure_ids[p2]):
            counts['identity_edges'] += 1
            opportunities, rectangles = [], {}
            for project_q in sorted(support[d1].keys() & support[d2].keys()):
                cells = sorted(support[d1][project_q] & support[d2][project_q])
                if cells:
                    project, q = project_q
                    opportunities.append({'project': project, 'q_uM': q_string(q), 'cells': cells})
                    counts['identity_edge_project_cell_q_opportunities'] += len(cells)
                    if len(cells) >= 2:
                        rectangles[project_q] = set(cells)
                        counts['identity_edge_project_q_rectangles'] += 1
                        counts['identity_edge_two_cell_rectangles'] += math.comb(len(cells), 2)
            counts['identity_edges_with_any_cell_q'] += int(bool(opportunities))
            counts['identity_edges_with_two_cell_rectangle'] += int(bool(rectangles))
            instance_index = len(instances)
            instances.append({'drug_id_from': d1, 'drug_id_to': d2,
                              'opportunities': opportunities})
            edge_groups[(v1, v2, descriptor)].append((index, instance_index, rectangles))
        if any(instance['opportunities'] for instance in instances):
            counts['edges_with_any_cell_q'] += 1
        if any(len(o['cells']) >= 2 for instance in instances for o in instance['opportunities']):
            counts['edges_with_two_cell_rectangle'] += 1
        record = {'edge_index': index, 'variable_from': v1, 'variable_to': v2,
                  'attachment': descriptor, 'core': core, 'molecule_from': p1,
                  'molecule_to': p2, 'core_murcko': murcko(core),
                  'identity_instances': instances}
        edge_records.append(record)
    examples = []
    canonical_pairs, different_murcko_pairs, canonical_pair_groups = set(), set(), set()
    for edit_key, candidates in sorted(edge_groups.items()):
        for (i, ii, ri), (j, ij, rj) in itertools.combinations(candidates, 2):
            a, b = edge_records[i], edge_records[j]
            parents = [a['molecule_from'], a['molecule_to'], b['molecule_from'], b['molecule_to']]
            if len(set(parents)) != 4 or a['core'] == b['core']:
                continue
            eligible = []
            for project_q in sorted(ri.keys() & rj.keys()):
                cells = sorted(ri[project_q] & rj[project_q])
                if len(cells) >= 2:
                    project, q = project_q
                    eligible.append({'project': project, 'q_uM': q_string(q), 'cells': cells})
                    counts['cross_parent_identity_pair_project_q_groups'] += 1
                    counts['cross_parent_identity_two_cell_rectangles'] += math.comb(len(cells), 2)
                    canonical_pair_groups.add((i, j, project, q))
            if eligible:
                counts['cross_parent_identity_edge_pairs'] += 1
                canonical_pairs.add((i, j))
                different = a['core_murcko'] != b['core_murcko']
                if different:
                    different_murcko_pairs.add((i, j))
                if len(examples) < 20:
                    examples.append({'edit_key': edit_key, 'edge_indices': [i, j],
                                     'identity_instance_indices': [ii, ij],
                                     'different_core_murcko': different, 'support': eligible})
    counts.update({'unique_drug_ids': len(id_names), 'id_name_conflict_ids': len(conflict_ids),
                   'mapped_drug_ids': len(id_structure), 'mapped_unique_molecules': len(used_molecules),
                   'duplicate_structure_extra_ids': len(id_structure) - len(used_molecules),
                   'selected_project_cell_drug': len(selected), 'structural_edges': len(edges),
                   'edit_keys': len(edge_groups),
                   'cross_parent_edge_pairs': len(canonical_pairs),
                   'cross_parent_edge_pair_project_q_groups': len(canonical_pair_groups),
                   'cross_parent_pairs_different_murcko': len(different_murcko_pairs)})
    observed_ids = {key[2] for key in selected}
    counts['well_drug_ids'] = len(observed_ids)
    counts['well_drug_ids_absent_from_matrix'] = len(observed_ids - set(id_names))
    counts['well_drug_ids_mapped'] = len(observed_ids & set(id_structure))
    summary = {'schema': 'independent-support-v1', 'input_sha256': hashes, 'members': members,
               'rdkit_version': Chem.rdBase.rdkitVersion, 'sanity': sanity, 'counts': dict(counts),
               'id_exclusions': dict(id_exclusions), 'source_rejections': dict(source_rejections),
               'identity_map': [{'drug_id': d, 'name': next(iter(id_names[d])), 'canonical_smiles': s}
                                for d, s in sorted(id_structure.items())],
               'excluded_ids': [{'drug_id': d, 'names': sorted(id_names[d])}
                                for d in sorted(set(id_names) - set(id_structure))],
               'well_drug_ids_absent_from_matrix': sorted(observed_ids - set(id_names)),
               'status': ('structural_opportunity_present' if counts['cross_parent_edge_pairs']
                          else 'no_cross_parent_opportunity_in_mapped_subset'),
               'measurement_qualification': 'full_measurement_qualification_unknown',
               'csv_access': 'full rows temporarily tokenized; metadata projection only',
               'cpu_seconds': time.process_time() - CPU_START,
               'wall_seconds': time.monotonic() - WALL_START,
               'rss_bytes': psutil.Process().memory_info().rss}
    outputs = {
        'independent_summary.json': json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        'independent_edges.jsonl': ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n'
                                           for r in edge_records),
        'independent_examples.json': json.dumps(examples, ensure_ascii=False, indent=2, sort_keys=True) + '\n'}
    if sum(len(s.encode('utf-8')) for s in outputs.values()) > OUTPUT_LIMIT:
        raise RuntimeError('independent output cap exceeded')
    for filename, content in outputs.items():
        (HERE / filename).write_text(content, encoding='utf-8', newline='\n')
    print(json.dumps({'files': sorted(outputs), 'counts': dict(counts)}, sort_keys=True))


if __name__ == '__main__':
    threading.Thread(target=guard, daemon=True).start()
    main()
