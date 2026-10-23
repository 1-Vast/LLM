"""Decode only authenticated treated S3 counts; never open S4 or other sheets."""
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from diagnose_counts import NS, cell_value, sheet_members, strings

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/next_mechanism/source/cdk_review'
OUT = ROOT / 'log/20261022/cdk_middle_feedback'


def main():
    started = time.perf_counter()
    body = SOURCE / 'table_s3.body'
    digest = hashlib.sha256(body.read_bytes()).hexdigest()
    assert digest == '36903d770ff3bd3bc5fd62c6ee19d8106871c9735e8591c0e722da05cf146608'
    bindings = json.loads((SOURCE / 'SAMPLE_HEADER_CONTRACT.json').read_text())['bindings']
    chosen = [b for b in bindings if b['treatment_label'] != 'Veh']
    assert len(chosen) == 36
    samples, dictionaries = [], []
    omissions = {}
    with zipfile.ZipFile(body) as archive:
        shared = strings(archive)
        members = sheet_members(archive)
        for sheet in dict.fromkeys(b['sheet'] for b in chosen):
            specs = [b for b in chosen if b['sheet'] == sheet]
            columns = [b['count_column'].rstrip('0123456789') for b in specs]
            fraction_columns = [b['fraction_column'].rstrip('0123456789') for b in specs]
            permitted = {'A', *columns}
            values = [dict() for _ in specs]
            missing = [0 for _ in specs]
            seen = set()
            with archive.open(members[sheet]) as stream:
                for _, element in ET.iterparse(stream, events=('end',)):
                    if element.tag != NS + 'row':
                        continue
                    cells = {cell.attrib.get('r', '').rstrip('0123456789'): cell for cell in element}
                    row = {cell.attrib['r'].rstrip('0123456789'): cell_value(cell, shared)
                           for cell in element if cell.attrib.get('r', '').rstrip('0123456789') in permitted}
                    if int(element.attrib['r']) == 1:
                        for b, col in zip(specs, columns):
                            assert row[col] == b['sample_label'] + '_Count'
                    else:
                        barcode = row['A']
                        assert isinstance(barcode, str) and barcode not in seen
                        seen.add(barcode)
                        for j, (store, col) in enumerate(zip(values, columns)):
                            if col not in row or row[col] is None:
                                fraction = cells.get(fraction_columns[j])
                                if fraction is not None:
                                    assert not any((n.text or '').strip() for n in fraction.iter()
                                                   if n.tag in (NS + 'v', NS + 't')), 'Asymmetric missing Count/Fraction'
                                missing[j] += 1
                                continue  # Explicit author-style sparse zero convention, logged below.
                            count = float(row[col])
                            assert np.isfinite(count) and count >= 0 and count == int(count)
                            if count:
                                store[barcode] = count
                    element.clear()
            for spec, store, absent in zip(specs, values, missing):
                samples.append(spec)
                dictionaries.append(store)
                omissions[spec['sheet'] + '::' + spec['sample_label']] = absent
    # All cohort Early assays are declared observable. Middle and End cannot enroll features.
    universe = sorted(set().union(*(set(d) for b, d in zip(samples, dictionaries) if b['stage_label'] == 'Early')))
    positions = {barcode: i for i, barcode in enumerate(universe)}
    tasks = sorted(set((b['selection_family'], b['genotype_label'], b['evolutionary_replicate']) for b in samples))
    array = np.zeros((12, 3, len(universe) + 1), dtype=np.float64)
    depth = np.zeros((12, 3), dtype=np.float64)
    for b, counts in zip(samples, dictionaries):
        key = (b['selection_family'], b['genotype_label'], b['evolutionary_replicate'])
        i = tasks.index(key)
        stage = {'Early': 0, 'Middle': 1, 'Late_Resistant': 2}[b['stage_label']]
        for barcode, count in counts.items():
            array[i, stage, positions.get(barcode, len(universe))] += count
        depth[i, stage] = array[i, stage].sum()
        assert depth[i, stage] > 0
        array[i, stage] /= depth[i, stage]
    assert len(tasks) == 12 and np.allclose(array.sum(axis=2), 1)
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'prepared.npz'
    assert not target.exists(), 'Do not silently overwrite decoded data'
    np.savez_compressed(target, compositions=array, depth=depth)
    metadata = {'source_sha256': digest, 'tasks': tasks, 'shape': list(array.shape),
                'universe': 'union of positive Early counts across declared observable cohort; one other bucket',
                'other_mass': array[:, :, -1].tolist(), 'depth': depth.tolist(),
                'omitted_count_cells': omissions,
                'missingness_convention': 'author-style sparse zero convention; not proof of structural biological absence or exact S3 exporter semantics',
                'wall_seconds': time.perf_counter() - started,
                'prepared_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (OUT / 'PREPARATION.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps({k: metadata[k] for k in ('shape', 'wall_seconds', 'prepared_sha256')}))


if __name__ == '__main__':
    main()
