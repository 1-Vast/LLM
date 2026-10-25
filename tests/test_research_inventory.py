"""Inventory preserves ambiguous duplicates and records actual local dependency pins."""
import hashlib
import json
from pathlib import Path

import pytest

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


def test_protected_payloads_are_never_opened(tmp_path, monkeypatch):
    from pathlib import Path
    study = tmp_path / 'research/study'
    study.mkdir(parents=True)
    protected = [study / name for name in ('sealed_outcomes.csv', 'blind_scores.npz', '.env', '.ENV.local', 'api_key.json', 'id_rsa')]
    for path in protected:
        path.write_bytes(b'synthetic protected placeholder')
    (study / 'safe.py').write_text('VALUE = 1')
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path in protected:
            raise AssertionError('Protected payload opened')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', guarded_open)
    result = build_inventory(tmp_path)
    records = {r['path']: r for r in result['files']}
    for path in protected:
        record = records[path.relative_to(tmp_path).as_posix()]
        assert record['content_status'] == 'UNVERIFIED_PROTECTED'
        assert 'sha256' not in record
    assert result['totals']['protected_files'] == 6
    assert result['duplicate_AST_candidates'] == []


def test_declared_protection_is_case_insensitive(tmp_path, monkeypatch):
    from pathlib import Path
    study = tmp_path / 'research/study'
    study.mkdir(parents=True)
    protected = study / 'Reserved.csv'
    protected.write_bytes(b'predeclared outcomes')
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path == protected:
            raise AssertionError('Declared protection ignored')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', guarded_open)
    result = build_inventory(tmp_path, protected_sources=['research/study/reserved.csv'])
    assert result['files'][0]['content_status'] == 'UNVERIFIED_PROTECTED'


def test_binary_duplicate_scan_streams_without_materializing_file(tmp_path, monkeypatch):
    from pathlib import Path
    study = tmp_path / 'research/study'
    study.mkdir(parents=True)
    body = b'fixed binary evidence' * 10000
    paths = [study / name for name in ('a.npz', 'b.npz')]
    for path in paths:
        path.write_bytes(body)
    original_read = Path.read_bytes

    def guarded_read(path):
        if path in paths:
            raise AssertionError('Large binary materialized')
        return original_read(path)

    monkeypatch.setattr(Path, 'read_bytes', guarded_read)
    result = build_inventory(tmp_path)
    assert result['byte_identical_groups'][0]['sha256'] == hashlib.sha256(body).hexdigest()


def test_inventory_refuses_a_linked_research_scope(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'ordinary.py').write_text('VALUE = 1')
    try:
        (tmp_path / 'research').symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Directory symlinks require local Windows privileges')
    with pytest.raises(ValueError, match='Linked research'):
        build_inventory(tmp_path)


def test_reparse_scope_is_rejected_before_payload_access(tmp_path, monkeypatch):
    import stat
    from types import SimpleNamespace
    research = tmp_path / 'research'
    research.mkdir()
    payload = research / 'ordinary.py'
    payload.write_text('VALUE = 1')
    original_lstat = Path.lstat
    original_open = Path.open

    def reparse_info(path):
        if path == research:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original_lstat(path)

    def guarded_open(path, *args, **kwargs):
        if path == payload:
            raise AssertionError('Linked scope payload opened')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'lstat', reparse_info)
    monkeypatch.setattr(Path, 'open', guarded_open)
    with pytest.raises(ValueError, match='Linked research'):
        build_inventory(tmp_path)


@pytest.mark.parametrize('name', ['.GIT', '.VENV'])
def test_managed_directory_exclusion_is_case_insensitive(tmp_path, monkeypatch, name):
    folder = tmp_path / 'research/study' / name
    folder.mkdir(parents=True)
    payload = folder / 'config'
    payload.write_bytes(b'synthetic managed state')
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path == payload:
            raise AssertionError('Managed state opened')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', guarded_open)
    assert build_inventory(tmp_path)['files'] == []
