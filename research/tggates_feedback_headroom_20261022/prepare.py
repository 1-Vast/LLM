"""Prepare a value-blind TG-GATEs proxy-block split and exact sample manifest."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/tggates_feedback_headroom'
PROXY = ROOT / 'log/20261022/api_evidence_innovation/chemical_proxy/RESULT.json'
MENU = ROOT / 'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json'
IDENTITIES = ROOT / 'log/20261022/tggates_functional_qualification/JOINED_IDENTITY_FLAGS.json'
RAW = ROOT / 'log/20261022/tggates_functional_qualification/sealed_source/open_tggates_cell_viability.zip'
IDENTITY_FIELDS = ['EXP_ID', 'GROUP_ID', 'INDIVIDUAL_ID', 'COMPOUND_NAME', 'SPECIES',
                   'SEX_TYPE', 'SACRIFICE_PERIOD', 'DOSE', 'DOSE_UNIT', 'DOSE_LEVEL']
KEY_FIELDS = IDENTITY_FIELDS[:3]
LEVELS = ['Low', 'Middle', 'High']
PREFIX = 'tggates-feedback-headroom-v1|'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, payload):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def sample_key(row):
    return tuple(row[field] for field in KEY_FIELDS)


def block_split(groups):
    assert len(groups) == 39
    blocks = []
    for labels in groups:
        labels = sorted(labels)
        block_id = hashlib.sha256((PREFIX + '\n'.join(labels)).encode('utf-8')).hexdigest()
        blocks.append({'block_id': block_id, 'labels': labels})
    blocks.sort(key=lambda row: row['block_id'])
    assert len({row['block_id'] for row in blocks}) == 39
    for number, block in enumerate(blocks):
        block['role'] = 'source' if number < 24 else 'development' if number < 31 else 'later'
        block['rank'] = number
    return blocks


def identity(row):
    return {field: row[field] for field in IDENTITY_FIELDS}


def build_manifest(proxy, menu, identities):
    accepted = menu['results']['both']['accepted_identity_only']
    assert len(accepted) == 47
    resolved = [row for row in proxy['rows'] if row['resolution'] == 'NAME_RESOLVED_PROXY_ONLY']
    assert len(resolved) == 45
    blocks = block_split(proxy['parent_scaffold_components'])
    flat_labels = [label for block in blocks for label in block['labels']]
    assert len(flat_labels) == len(set(flat_labels)) == 45
    assert set(flat_labels) == {row['compound_label'] for row in resolved}
    by_label = {row['compound_label']: row for row in accepted}
    by_block = {label: block for block in blocks for label in block['labels']}
    assert len({sample_key(row) for row in identities}) == len(identities)
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    compounds = []
    for row in sorted(resolved, key=lambda value: value['compound_label']):
        label = row['compound_label']
        declared = by_label[label]
        assert declared['experiment'] == row['experiment']
        block = by_block[label]
        mol = Chem.MolFromSmiles(row['neutral_parent'])
        assert mol is not None
        fingerprint = generator.GetFingerprint(mol)
        dense = np.zeros(2048, dtype=np.int8)
        DataStructs.ConvertToNumpyArray(fingerprint, dense)
        doses = {}
        for dose_key in declared['dose_keys']:
            exp, name, amount, unit, level = dose_key
            assert name == label and exp == row['experiment'] and level in LEVELS
            samples = [entry for entry in identities
                       if entry['EXP_ID'] == exp and entry['COMPOUND_NAME'] == name
                       and entry['SACRIFICE_PERIOD'] == '24 hr' and entry['DOSE_LEVEL'] == level
                       and entry['DOSE_UNIT'] == unit and Decimal(entry['DOSE']) == Decimal(amount)]
            assert len(samples) >= 2
            assert all(entry['functional_identity_match'] and entry['DNA_nonmissing_unconflicted']
                       and entry['LDH_nonmissing_unconflicted'] for entry in samples)
            doses[level] = {'value': str(Decimal(amount)), 'unit': unit,
                            'samples': sorted((identity(entry) for entry in samples), key=sample_key)}
        assert set(doses) == set(LEVELS)
        amounts = [Decimal(doses[level]['value']) for level in LEVELS]
        assert 0 < amounts[0] < amounts[1] < amounts[2]
        assert len({doses[level]['unit'] for level in LEVELS}) == 1
        controls = [identity(entry) for entry in identities
                    if entry['EXP_ID'] == row['experiment'] and entry['COMPOUND_NAME'] == label
                    and entry['SACRIFICE_PERIOD'] == '24 hr' and entry['DOSE_LEVEL'] == 'Control']
        assert controls
        compounds.append({'compound_label': label, 'experiment': row['experiment'],
                          'block_id': block['block_id'], 'role': block['role'],
                          'neutral_parent_proxy': row['neutral_parent'],
                          'fingerprint_on_bits': np.flatnonzero(dense).tolist(),
                          'doses': doses, 'controls_metadata_only': sorted(controls, key=sample_key)})
    costs = {}
    for role in ['source', 'development', 'later']:
        selected = [row for row in compounds if row['role'] == role]
        samples = [sample_key(sample) for row in selected for dose in row['doses'].values()
                   for sample in dose['samples']]
        controls = {sample_key(sample) for row in selected for sample in row['controls_metadata_only']}
        costs[role] = {'proxy_blocks': sum(block['role'] == role for block in blocks),
                       'compound_labels': len(selected), 'treatment_condition_bundles': 3 * len(selected),
                       'treatment_sample_records': len(samples), 'treatment_assay_values': 2 * len(samples),
                       'unique_control_records_metadata_only': len(controls),
                       'new_wet_experiments': 0, 'new_cel_downloads': 0}
    all_keys = [sample_key(sample) for row in compounds for dose in row['doses'].values()
                for sample in dose['samples']]
    assert len(all_keys) == len(set(all_keys))
    return {'schema_version': 1, 'status': 'METADATA_ONLY_PREPARED', 'split_prefix': PREFIX,
            'split_serialization': "prefix + '\\n'.join(sorted labels), SHA256 hex ascending",
            'blocks': blocks, 'compounds': compounds, 'costs': costs,
            'excluded_unresolved': [row for row in proxy['rows'] if row['resolution'] != 'NAME_RESOLVED_PROXY_ONLY'],
            'unit_categories': sorted({dose['unit'] for row in compounds for dose in row['doses'].values()}),
            'fingerprint': {'algorithm': 'Morgan', 'radius': 2, 'bits': 2048,
                            'input': 'frozen neutral_parent name-derived proxy', 'rdkit': rdBase.rdkitVersion},
            'target': '24h published DNA relative-survival percentage / 100; no control renormalization',
            'controls_numeric_permission': False, 'later_numeric_permission': False,
            'scope': 'Released catalog exploratory proxy-blocked prediction; no source-material, donor or causal certification.'}


def main():
    LOG.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(json.loads(PROXY.read_text(encoding='utf-8')),
                              json.loads(MENU.read_text(encoding='utf-8')),
                              json.loads(IDENTITIES.read_text(encoding='utf-8')))
    paths = [PROXY, MENU, IDENTITIES, RAW, Path(__file__)]
    manifest['inputs_sha256'] = {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}
    manifest['raw_zip_relative'] = RAW.relative_to(ROOT).as_posix()
    manifest['raw_zip_access'] = 'Byte hash only; CSV member not opened or decoded during preparation.'
    write(LOG / 'MANIFEST.json', manifest)
    print(json.dumps({'status': manifest['status'], 'costs': manifest['costs'],
                      'raw_csv_opened': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
