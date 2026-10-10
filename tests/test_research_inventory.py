"""Inventory preserves ambiguous duplicates and records actual local dependency pins."""
import hashlib
import json

from tools.research_inventory import build_inventory


def test_inventory_reports_pins_duplicates_and_imports_without_executing(tmp_path):
    study = tmp_path / 'research/study'
    study.mkdir(parents=True)
    producer = study / 'run.py'
    producer.write_text('from .helper import compute\nraise RuntimeError("must not execute")\n', encoding='utf-8')
    body = 'def compute(x):\n    value = x + 1\n    return value\n'
    (study / 'helper.py').write_text(body, encoding='utf-8')
    (study / 'historical_copy.py').write_text(body, encoding='utf-8')
    expected = hashlib.sha256(producer.read_bytes()).hexdigest()
    (study / 'FREEZE.json').write_text(json.dumps({'sha256': {
        'research/study/run.py': expected,
        './helper.py': hashlib.sha256(body.encode()).hexdigest(),
    }}))
    before = {p.name: p.read_bytes() for p in study.iterdir()}
    result = build_inventory(tmp_path)
    record = next(r for r in result['files'] if r['path'].endswith('/run.py'))
    assert record['referenced_by'] == ['research/study/FREEZE.json']
    assert record['local_import_dependencies'] == ['research/study/helper.py']
    helper = next(r for r in result['files'] if r['path'].endswith('/helper.py'))
    assert helper['referenced_by'] == ['research/study/FREEZE.json']
    assert result['byte_identical_groups'][0]['automatically_removable'] is False
    assert {p.name: p.read_bytes() for p in study.iterdir()} == before


def test_inventory_excludes_its_self_reference_and_keeps_unparsed_evidence(tmp_path):
    study = tmp_path / 'research'
    study.mkdir()
    (study / 'RESEARCH_INVENTORY.json').write_text('{}')
    (study / 'broken.py').write_text('def (')
    cache = study / '__pycache__'
    cache.mkdir()
    (cache / 'generated.py').write_text('raise RuntimeError')
    result = build_inventory(tmp_path)
    assert result['totals']['files'] == 1
    assert result['files'][0]['parse_status'] == 'SyntaxError'
    assert (study / 'broken.py').exists()
