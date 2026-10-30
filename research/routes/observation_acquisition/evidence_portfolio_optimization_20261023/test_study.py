"""Synthetic contracts only; never opens research sources or reserve outcomes."""
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def study(tmp_path, monkeypatch):
    source = Path(__file__).with_name('study.py')
    spec = importlib.util.spec_from_file_location('portfolio_contract_fixture', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, value in {'ROOT': tmp_path, 'LOG': tmp_path / 'log',
                        'DATA': tmp_path / 'data', 'ORIGINAL': tmp_path / 'original.csv',
                        'VALIDATION': tmp_path / 'validation.csv'}.items():
        monkeypatch.setattr(module, name, value)
    module.LOG.mkdir()
    module.DATA.mkdir()
    fake_code = tmp_path / 'study.py'
    fake_code.write_text('# Synthetic metadata-freeze target.\n', encoding='utf-8')
    monkeypatch.setattr(module, '__file__', str(fake_code))
    (module.LOG / 'PROTOCOL.md').write_text('Synthetic contract fixture.\n', encoding='utf-8')
    (module.LOG / 'PRE_FREEZE_REVISIONS.md').write_text('Synthetic revision fixture.\n', encoding='utf-8')
    return module


def write_rows(study, final_value='0.2', missing=False, invalid=False):
    original, validation = [], []
    for i in range(13):
        row = {'SIDM': f'SIDM-{i // 5}', 'ANCHOR_ID': 'A', 'ANCHOR_CONC': '1.00',
               'LIBRARY_ID': f'L{i:02}', 'BARCODE': f'ORIGINAL-{i}'}
        original.append({**row, study.VALUE: 'UNREAD-RESPONSE' if invalid else str(100 - i)})
        for role in range(2):
            suffix = 0
            while True:
                barcode = f'VALIDATION-{i}-{role}-{suffix}'
                if study.hashed('portfolio-role-v1:' + barcode) % 2 == role:
                    break
                suffix += 1
            value = str(0.2 + i * 0.03) if role == 0 else final_value
            if missing:
                value = 'nan'
            if invalid:
                value = 'UNREAD-RESPONSE'
            validation.append({**row, 'BARCODE': barcode, study.VALUE: value})
    for path, rows in ((study.ORIGINAL, original), (study.VALIDATION, validation)):
        with path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=study.IDS + [study.VALUE])
            writer.writeheader()
            writer.writerows(rows)


def test_freeze_eligibility_uses_only_metadata(study):
    write_rows(study, invalid=True)
    study.freeze()
    before = json.loads((study.DATA / 'ELIGIBLE.json').read_text())
    assert len(before) == 13
    assert not {r['scout_plate'] for r in before} & {r['final_plate'] for r in before}
    (study.LOG / 'FREEZE.json').unlink()
    write_rows(study, final_value='-999')
    study.freeze()
    assert json.loads((study.DATA / 'ELIGIBLE.json').read_text()) == before


def test_single_anchor_schema_excludes_multianchor_and_invalid_identity(study):
    base = {'SIDM': ' SIDM-0 ', 'ANCHOR_ID': 'NA', 'ANCHOR_CONC': ' 1e0 ',
            'LIBRARY_ID': 'L00', 'BARCODE': 'ORIGINAL-EXCLUDED'}
    assert study.key(base) == 'SIDM-0|NA|1.0|L00'
    for bad in ('0.125|0.003', '0.5|0.03', '', 'nan', 'inf', 'bad'):
        assert study.key({**base, 'ANCHOR_CONC': bad}) is None
    for field in ('SIDM', 'ANCHOR_ID', 'LIBRARY_ID'):
        assert study.key({**base, field: ''}) is None
        assert study.key({**base, field: 'A|B'}) is None
    write_rows(study, invalid=True)
    for path in (study.ORIGINAL, study.VALIDATION):
        with path.open('a', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=study.IDS + [study.VALUE])
            writer.writerow({**base, 'ANCHOR_CONC': '0.5|0.03',
                             'BARCODE': path.stem + '-MULTI', study.VALUE: 'UNREAD-RESPONSE'})
    study.freeze()
    freeze = json.loads((study.LOG / 'FREEZE.json').read_text())
    assert freeze['K'] == 13
    assert freeze['metadata_excluded_rows'] == {'original': 1, 'validation': 1}


def test_future_final_values_do_not_change_choices_or_charges(study, monkeypatch):
    write_rows(study)
    study.freeze()
    # This test mutates synthetic futures after a synthetic freeze, so bypass only
    # its source-hash gate. Real study execution retains the production gate.
    (study.LOG / 'FREEZE.json').write_text('{"files": {}}', encoding='utf-8')
    original_values = study.values
    final_calls = []
    final_plates = {r['final_plate'] for r in json.loads((study.DATA / 'ELIGIBLE.json').read_text())}

    def checked_values(path, allowed):
        if path == study.VALIDATION and {b for _, b in allowed} & final_plates:
            choice_file = study.DATA / 'CHOICES.json'
            receipt = json.loads((study.LOG / 'CHOICES_FREEZE.json').read_text())
            assert receipt['sha256'] == study.digest(choice_file)
            assert receipt['final_outcomes_used_for_choices'] is False
            final_calls.append(set(allowed))
        return original_values(path, allowed)

    monkeypatch.setattr(study, 'values', checked_values)
    study.run()
    choices = (study.DATA / 'CHOICES.json').read_bytes()
    result = json.loads((study.LOG / 'RESULTS.json').read_text())
    assert len(final_calls) == 1
    write_rows(study, final_value='-999')
    study.run()
    changed = json.loads((study.LOG / 'RESULTS.json').read_text())
    assert (study.DATA / 'CHOICES.json').read_bytes() == choices
    assert final_calls[0] == final_calls[1]
    for arm, summary in result['summary'].items():
        assert summary['planned_reads'] == 7
        assert summary['scout_reads'] + summary['final_reads'] == 7
        assert changed['summary'][arm]['planned_reads'] == 7
        assert changed['summary'][arm]['0.1']['repeat_positive'] == 0
    paid = json.loads(choices)
    assert len(paid['scouts_by_arm']['direct']) == 4
    assert len(paid['finals']['direct']) == 3
    # Revised repeatability task has no discarded design's set-inclusion cap.
    assert not set(paid['finals']['feedback']) <= set(paid['finals']['direct'])


def test_missing_purchased_observations_are_charged_and_not_replaced(study):
    write_rows(study, missing=True)
    study.freeze()
    study.run()
    result = json.loads((study.LOG / 'RESULTS.json').read_text())
    assert result['missing_scout_reads'] == 5
    for summary in result['summary'].values():
        assert summary['planned_reads'] == 7
        assert summary['missing_final_reads'] == summary['final_reads']
        assert summary['missing_paired_scout_reads'] == summary['final_reads']
        assert summary['0.1']['repeat_positive'] == 0
        assert summary['0.1']['per_1000_planned_wells'] == 0
    with np.load(study.DATA / 'OBSERVED.npz') as arrays:
        assert np.isnan(arrays['scout']).all()
        assert np.isnan(arrays['final']).all()
