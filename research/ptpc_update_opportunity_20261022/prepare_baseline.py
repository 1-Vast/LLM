"""HCT116 six-hour states only; reserved background outcomes never resolved."""
from collections import defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import time
import warnings
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_update_opportunity'
SOURCE = ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup'
TAG = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def value(cell, shared):
    if cell is None:
        return ''
    assert cell.find(TAG + 'f') is None, 'No formula-derived observations'
    assert cell.attrib.get('t') not in ('e', 'b'), 'Error/boolean observation'
    node = cell.find(TAG + 'v')
    if cell.attrib.get('t') == 's':
        return ''.join(t.text or '' for t in shared[int(node.text)].iter(TAG + 't'))
    if cell.attrib.get('t') == 'inlineStr':
        return ''.join(t.text or '' for t in cell.iter(TAG + 't'))
    return node.text if node is not None else ''


def column(address):
    letters = re.match('[A-Z]+', address)[0]
    number = 0
    for letter in letters:
        number = number * 26 + ord(letter) - 64
    return number - 1


def main():
    started = time.perf_counter()
    assert not (OUT / 'BASELINE_PREPARED.npz').exists()
    identities = json.loads((SOURCE / 'S8_IDENTITY_ROWS.json').read_text())
    groups = json.loads((OUT / 'source/HCT116_CONDITION_GROUPS.json').read_text())
    eligible = {g['Pert_ID']: int(next(iter(g['labels']))) for g in groups
                if not g['control'] and g['strict_complete_candidate'] and '6' in g['times']}
    assert len(eligible) == 601
    source = SOURCE / 'archive.body'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == 'efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133'
    with zipfile.ZipFile(source) as outer:
        body = outer.read('TableS8_PTPC_info_0703.xlsx')
    assert hashlib.sha256(body).hexdigest() == '540ec451edeca2bbbd08e53254cb9c09ba67b6f98727ff9c31e373a192290fdc'
    rows_by_id = defaultdict(list)
    ids_by_condition = defaultdict(set)
    chemistry = {}
    missing_cells = observed_cells = 0
    with zipfile.ZipFile(BytesIO(body)) as book:
        shared = ET.fromstring(book.read('xl/sharedStrings.xml')).findall(TAG + 'si') if 'xl/sharedStrings.xml' in book.namelist() else []
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        parts = {}
        for sheet in ET.fromstring(book.read('xl/workbook.xml')).find(TAG + 'sheets'):
            part = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            parts[sheet.attrib['name']] = part.lstrip('/') if part.startswith('/') else 'xl/' + part
        drug_rows = ET.fromstring(book.read(parts['B_drug_info'])).findall('.//' + TAG + 'row')
        for row in drug_rows[1:]:
            cells = {column(c.attrib['r']): c for c in row}
            pert = value(cells.get(0), shared)
            if pert not in eligible:
                continue
            record = {'name': value(cells.get(2), shared), 'smiles': value(cells.get(4), shared)}
            assert pert not in chemistry or chemistry[pert] == record
            chemistry[pert] = record
        with book.open(parts['C_protein_Matrix']) as stream:
            position = -1
            for _, row in ET.iterparse(stream, events=('end',)):
                if row.tag != TAG + 'row':
                    continue
                if row.attrib['r'] == '1':
                    headers = [value(c, shared) for c in row]
                    assert headers[0] == 'Sample_ID' and len(headers) == 5172
                    row.clear()
                    continue
                position += 1
                assert int(row.attrib['r']) == position + 2
                meta = identities[position]
                if meta['Cell_line'] != 'HCT116' or meta['Pert_time_(hrs)'] != '6' or meta['Pert_ID'] not in eligible:
                    row.clear()
                    continue
                vector = np.full(5171, np.nan)
                sample = None
                for cell in row:
                    index = column(cell.attrib['r'])
                    text = value(cell, shared)
                    if index == 0:
                        sample = text
                    elif text.strip().casefold() not in ('', 'na', 'n/a', 'nan'):
                        number = float(text)
                        assert np.isfinite(number) and number >= 0, 'Unqualified intensity scale'
                        vector[index - 1] = np.log1p(number)
                assert sample == meta['Sample_ID']
                observed_cells += int(np.isfinite(vector).sum())
                missing_cells += int(np.isnan(vector).sum())
                rows_by_id[sample].append(vector)
                ids_by_condition[meta['Pert_ID']].add(sample)
                row.clear()
            assert position + 1 == len(identities)
    tasks = sorted(eligible)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', RuntimeWarning)
        per_sample = {key: np.nanmedian(np.stack(values), axis=0) for key, values in rows_by_id.items()}
        proteins = np.stack([np.nanmedian(np.stack([per_sample[s] for s in sorted(ids_by_condition[pert])]), axis=0) for pert in tasks])
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fingerprints, chemical_groups, details = [], [], []
    for pert in tasks:
        record = chemistry.get(pert, {'name': '', 'smiles': ''})
        molecule = Chem.MolFromSmiles(record['smiles']) if record['smiles'].strip() else None
        fp = np.zeros(2049, dtype=np.float32)
        if molecule is not None:
            canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
            fp[:2048] = generator.GetFingerprintAsNumPy(molecule)
            group = 'smiles:' + canonical
        else:
            canonical = None
            fp[-1] = 1
            normalized = re.sub(r'\s+', '', record['name']).casefold()
            group = 'missing:' + (normalized or pert)
        fingerprints.append(fp)
        chemical_groups.append(group)
        details.append({'pert_id': pert, 'name': record['name'], 'canonical_smiles': canonical,
                        'chemical_group': group, 'label': eligible[pert], 'six_hour_sample_ids': sorted(ids_by_condition[pert])})
    # Equal declared names conservatively connect valid and missing-SMILES aliases too.
    parent = list(range(len(tasks)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    aliases = {}
    for i, detail in enumerate(details):
        name = re.sub(r'\s+', '', detail['name']).casefold()
        for key in [detail['chemical_group']] + (['name:' + name] if name else []):
            if key in aliases:
                parent[find(i)] = find(aliases[key])
            aliases[key] = i
    component_keys = defaultdict(list)
    for i, group in enumerate(chemical_groups):
        component_keys[find(i)].append(group)
    chemical_groups = [min(component_keys[find(i)]) for i in range(len(tasks))]
    for detail, group in zip(details, chemical_groups):
        detail['chemical_group'] = group
    target = OUT / 'BASELINE_PREPARED.npz'
    np.savez_compressed(target, proteins=proteins.astype(np.float32), chemistry=np.stack(fingerprints),
                        labels=np.array([eligible[t] for t in tasks], dtype=int))
    metadata = {'scope': 'HCT116 development, six-hour drug states only; no other backgrounds or24h abundance decoded',
                'tasks': details, 'protein_shape': list(proteins.shape), 'positive_conditions': int(sum(eligible.values())),
                'unique_chemical_groups': len(set(chemical_groups)),
                'missing_or_invalid_smiles': sum(d['canonical_smiles'] is None for d in details),
                'observed_abundance_cells': observed_cells, 'missing_abundance_cells': missing_cells,
                'median_warning_count': len(caught), 'wall_seconds': time.perf_counter() - started,
                'prepared_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (OUT / 'BASELINE_PREPARATION.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in metadata.items() if k != 'tasks'}))


if __name__ == '__main__':
    main()
