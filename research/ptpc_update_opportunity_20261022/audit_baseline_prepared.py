"""Independent lxml reconstruction of HCT116 6h preparation, never imports baseline code."""
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import time
import warnings
import zipfile

from lxml import etree
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path('D:/MAESTRO')
OUT = ROOT/'log/20261022/ptpc_update_opportunity'
SOURCE = ROOT/'log/20261022/generative_repair_renewal/source/archive_followup'
TAG = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REPORT = OUT/'source/BASELINE_PREPARED_AUDIT.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    started = time.perf_counter()
    freeze = json.loads((OUT/'BASELINE_PREDICTION_FREEZE.json').read_text())
    for path, expected in freeze['bindings'].items():
        assert sha(ROOT/path) == expected, f'Frozen input changed: {path}'
    prep = json.loads((OUT/'BASELINE_PREPARATION.json').read_text())
    identities = json.loads((SOURCE/'S8_IDENTITY_ROWS.json').read_text())
    groups = json.loads((OUT/'source/HCT116_CONDITION_GROUPS.json').read_text())
    labels = {}
    for group in groups:
        assert group['Cell_line'] == 'HCT116'
        if not group['control'] and group['strict_complete_candidate'] and '6' in group['times']:
            assert set(group['labels']) in ({'0'}, {'1'})
            labels[group['Pert_ID']] = int(next(iter(group['labels'])))
    tasks = sorted(labels)
    assert len(tasks) == 601 and sum(labels.values()) == 34
    assert [t['pert_id'] for t in prep['tasks']] == tasks
    with np.load(OUT/'BASELINE_PREPARED.npz') as data:
        prepared = {key: data[key].copy() for key in ('proteins', 'chemistry', 'labels')}
    assert np.array_equal(prepared['labels'], [labels[t] for t in tasks])
    assert all(t['label'] == labels[t['pert_id']] for t in prep['tasks'])
    source = SOURCE/'archive.body'
    assert sha(source) == 'efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133'
    with zipfile.ZipFile(source) as outer:
        body = outer.read('TableS8_PTPC_info_0703.xlsx')
    member_sha = hashlib.sha256(body).hexdigest()
    assert member_sha == '540ec451edeca2bbbd08e53254cb9c09ba67b6f98727ff9c31e373a192290fdc'
    selected, observed, missing = [], 0, 0
    by_sample = defaultdict(list)
    contexts = defaultdict(set)
    chemistry = {}
    with zipfile.ZipFile(BytesIO(body)) as book:
        strings = etree.fromstring(book.read('xl/sharedStrings.xml')).findall(TAG+'si')
        def text(cell):
            if cell is None:
                return ''
            assert cell.find(TAG+'f') is None
            kind = cell.get('t', 'n')
            assert kind not in ('e', 'b')
            if kind == 's':
                return ''.join(strings[int(cell.find(TAG+'v').text)].itertext())
            if kind == 'inlineStr':
                return ''.join(n.text or '' for n in cell.iter(TAG+'t'))
            node = cell.find(TAG+'v')
            return (node.text or '') if node is not None else ''
        def cells(row):
            return {re.match('[A-Z]+', c.get('r'))[0]: c for c in row if c.tag == TAG+'c'}
        rels = {r.get('Id'): r.get('Target') for r in etree.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        parts = {}
        for node in etree.fromstring(book.read('xl/workbook.xml')).findall('.//'+TAG+'sheet'):
            target = rels[node.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
            parts[node.get('name')] = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        def rows(sheet):
            with book.open(parts[sheet]) as stream:
                for _, row in etree.iterparse(stream, events=('end',), tag=TAG+'row'):
                    yield row
                    row.clear()
                    while row.getprevious() is not None:
                        del row.getparent()[0]
        metadata = []
        for index, row in enumerate(rows('A_metadata')):
            current = cells(row)
            if index == 0:
                names = {text(c): col for col, c in current.items()}
                assert names['Efficacy'] == 'G'
            else:
                # Never resolve any Efficacy cell, even for HCT116: use sealed gate.
                metadata.append({key: text(current.get(col)) for key, col in names.items() if key != 'Efficacy'})
        assert metadata == identities
        for index, row in enumerate(rows('B_drug_info')):
            current = cells(row)
            if index == 0:
                names = {text(c): col for col, c in current.items()}
            else:
                pert = text(current.get(names['Pert_ID']))
                if pert in labels:
                    record = (text(current.get(names['Compound_name'])), text(current.get(names['SMILES'])))
                    assert pert not in chemistry or chemistry[pert] == record
                    chemistry[pert] = record
        matrix_ids = []
        for index, row in enumerate(rows('C_protein_Matrix')):
            current = cells(row)
            if index == 0:
                assert text(current['A']) == 'Sample_ID' and len(current) == 5172
                protein_columns = [col for col in current if col != 'A']
                continue
            assert int(row.get('r')) == index+1
            sample = text(current.get('A'))
            matrix_ids.append(sample)
            meta = metadata[index-1]
            assert sample == meta['Sample_ID']
            if not (meta['Cell_line'] == 'HCT116' and meta['Pert_time_(hrs)'] == '6' and meta['Pert_ID'] in labels):
                continue
            vector = np.full(5171, np.nan)
            for j, col in enumerate(protein_columns):
                raw = text(current.get(col)).strip()
                if raw.casefold() in ('', 'na', 'n/a', 'nan'):
                    missing += 1
                    continue
                number = float(raw)
                assert math.isfinite(number) and number >= 0
                vector[j] = np.log1p(number)
                observed += 1
            key = (meta['Cell_line'], meta['Pert_ID'], meta['Pert_time_(hrs)'], sample)
            by_sample[key].append(vector)
            contexts[sample].add(key[:3])
            selected.append(index+1)
        assert len(matrix_ids) == len(metadata) == 2217
    assert len(selected) == 621 and len(by_sample) == 601
    assert all(len(v) == 1 for v in contexts.values())
    assert observed == prep['observed_abundance_cells'] and missing == prep['missing_abundance_cells']
    assert observed+missing == len(selected)*5171
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        sample_state = {key: np.nanmedian(np.stack(value), axis=0) for key, value in by_sample.items()}
        condition_state = {}
        for pert in tasks:
            matching = sorted(key for key in sample_state if key[1] == pert)
            assert matching
            condition_state[pert] = np.nanmedian(np.stack([sample_state[key] for key in matching]), axis=0)
        rebuilt = np.stack([condition_state[pert] for pert in tasks]).astype(np.float32)
    assert rebuilt.shape == prepared['proteins'].shape == (601, 5171)
    same = (rebuilt == prepared['proteins']) | (np.isnan(rebuilt) & np.isnan(prepared['proteins']))
    mismatched = int((~same).sum())
    assert mismatched == 0, f'Float32 coordinate mismatches: {mismatched}'
    assert np.array_equal(np.isnan(rebuilt), np.isnan(prepared['proteins']))
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    graph = {pert: set() for pert in tasks}
    key_members = defaultdict(list)
    primary = {}
    fingerprints = []
    for pert, detail in zip(tasks, prep['tasks']):
        name, smiles = chemistry.get(pert, ('', ''))
        molecule = Chem.MolFromSmiles(smiles) if smiles.strip() else None
        normalized = re.sub(r'\s+', '', name).casefold()
        fp = np.zeros(2049, dtype=np.float32)
        if molecule is None:
            canonical = None
            fp[-1] = 1
            primary[pert] = 'missing:'+(normalized or pert)
        else:
            canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
            primary[pert] = 'smiles:'+canonical
            fp[:2048] = generator.GetFingerprintAsNumPy(molecule)
        fingerprints.append(fp)
        assert detail['name'] == name and detail['canonical_smiles'] == canonical
        key_members[primary[pert]].append(pert)
        if normalized:
            key_members['name:'+normalized].append(pert)
    for members in key_members.values():
        for pert in members[1:]:
            graph[members[0]].add(pert)
            graph[pert].add(members[0])
    independent_group, components = {}, []
    for pert in tasks:
        if pert in independent_group:
            continue
        pending, component = [pert], set()
        while pending:
            current = pending.pop()
            if current not in component:
                component.add(current)
                pending.extend(graph[current]-component)
        representative = min(primary[p] for p in component)
        independent_group.update({p: representative for p in component})
        components.append(sorted(component))
    assert all(t['chemical_group'] == independent_group[t['pert_id']] for t in prep['tasks'])
    assert np.array_equal(np.stack(fingerprints), prepared['chemistry'])
    def fold(key, salt, modulus):
        return int.from_bytes(hashlib.sha256((salt+'|'+key).encode('utf-8')).digest(), 'big') % modulus
    outer = {p: fold(independent_group[p], 'PTPC_HCT116_DEV_V1', 5) for p in tasks}
    inner = {p: fold(independent_group[p], 'INNER', 3) for p in tasks}
    assert all(len({outer[p] for p in c}) == 1 and len({inner[p] for p in c}) == 1 for c in components)
    for f in range(5):
        assert {independent_group[p] for p in tasks if outer[p] == f}.isdisjoint({independent_group[p] for p in tasks if outer[p] != f})
    report = dict(status='PASS', created_utc=datetime.now(timezone.utc).isoformat(),
        parser='independent lxml; no baseline module imported',
        source_archive_sha256=sha(source), S8_member_sha256=member_sha,
        prediction_freeze_sha256=sha(OUT/'BASELINE_PREDICTION_FREEZE.json'), all_frozen_bindings_match=True,
        exact_metadata_identity_match=True, complete_matrix_id_order_match=True, source_rows=len(metadata),
        selected_rows=len(selected), distinct_sample_ids=len(by_sample), conditions=len(tasks), positives=sum(labels.values()),
        selected_observed_cells=observed, selected_missing_cells=missing,
        transform='log1p each observed value -> technical nanmedian -> sample nanmedian -> float32',
        rebuilt_shape=list(rebuilt.shape), coordinates_compared=int(rebuilt.size), mismatched_coordinates=mismatched,
        missing_mask_equal=True, prepared_missing_coordinates=int(np.isnan(rebuilt).sum()),
        labels_exactly_match_sealed_HCT116_gate=True, chemical_fingerprints_exact_match=True,
        independently_rebuilt_alias_components=len(components), expected_alias_components=prep['unique_chemical_groups'],
        chemical_components_cross_outer_fold=0, chemical_components_cross_inner_fold=0,
        outer_fold_conditions=dict(Counter(outer.values())), inner_fold_conditions=dict(Counter(inner.values())),
        decoded_other_background_Efficacy_cells=0, decoded_any_raw_Efficacy_cells=0,
        decoded_other_background_abundance_cells=0, decoded_24h_abundance_cells=0,
        predictions_read=False, classifier_rerun=False, collected_all_nan_warning_objects=False,
        limitation='Data/transform/assignment audit only; no functional mechanism, performance, transfer or RSI claim. Fold checks concern frozen assignment, not unread prediction artifacts.',
        audit_script_sha256=sha(Path(__file__).resolve()), wall_seconds=time.perf_counter()-started)
    assert len(components) == prep['unique_chemical_groups']
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    assert not REPORT.exists(), 'Refuse audit overwrite'
    try:
        main()
    except Exception as error:
        REPORT.write_text(json.dumps(dict(status='FAIL', created_utc=datetime.now(timezone.utc).isoformat(),
            error_type=type(error).__name__, error=str(error), audit_script_sha256=sha(Path(__file__).resolve())), indent=2), encoding='utf-8')
        raise
