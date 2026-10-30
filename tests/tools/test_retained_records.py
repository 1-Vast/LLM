"""Exact-byte and path safety checks for consolidated research source records."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import zipfile

import pytest

from tools import retained_records as records


def make_store(tmp_path, data):
    folder = tmp_path / records.STORE
    folder.mkdir(parents=True)
    encoded = json.dumps({'path': 'log/study/REPORT.md', 'encoding': 'base64', 'base64': base64.b64encode(data).decode('ascii')}).encode()
    (folder / 'RECORDS.jsonl').write_bytes(encoded)
    item = {'offset': 0, 'length': len(encoded), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    index = {'files': {'log/study/REPORT.md': item}, 'aliases': {'log/old/REPORT.md': 'log/study/REPORT.md'}}
    (folder / 'INDEX.json').write_text(json.dumps(index), encoding='utf-8')
    return folder, index


def test_exact_bytes_and_historical_alias(tmp_path):
    payload = b'Historical correction\r\n\x00\xff'
    make_store(tmp_path, payload)
    assert records.read_bytes('log/study/REPORT.md', tmp_path) == payload
    assert records.read_bytes('log\\old\\REPORT.md', tmp_path) == payload
    with pytest.raises(FileNotFoundError):
        records.read_bytes('log/missing.md', tmp_path)


def test_corrupted_content_is_rejected(tmp_path):
    folder, index = make_store(tmp_path, b'unchanged')
    index['files']['log/study/REPORT.md']['sha256'] = '0' * 64
    (folder / 'INDEX.json').write_text(json.dumps(index), encoding='utf-8')
    with pytest.raises(ValueError, match='content verification'):
        records.read_bytes('log/study/REPORT.md', tmp_path)


def test_alias_cycle_is_rejected():
    with pytest.raises(ValueError, match='Circular'):
        records.resolve('a', {'files': {}, 'aliases': {'a': 'b', 'b': 'a'}})


def test_relocated_live_file_preserves_alias_and_integrity(tmp_path):
    folder, index = make_store(tmp_path, b'protocol')
    data = b'original run predictions\x00\xff'
    target = tmp_path / 'data/processed/run_outputs/run/predictions.bin'
    target.parent.mkdir(parents=True)
    target.write_bytes(data)
    relative = target.relative_to(tmp_path).as_posix()
    index['live_files'] = {relative: {'live_path': relative, 'bytes': len(data),
                                    'sha256': hashlib.sha256(data).hexdigest()}}
    index['aliases']['outputs/run/predictions.bin'] = relative
    (folder / 'INDEX.json').write_text(json.dumps(index), encoding='utf-8')
    assert records.read_bytes('outputs/run/predictions.bin', tmp_path) == data
    target.write_bytes(b'changed')
    with pytest.raises(ValueError, match='content verification'):
        records.read_bytes('outputs/run/predictions.bin', tmp_path)
    index['live_files'][relative]['live_path'] = '../outside.bin'
    (folder / 'INDEX.json').write_text(json.dumps(index), encoding='utf-8')
    with pytest.raises(ValueError, match='Unsafe'):
        records.read_bytes('outputs/run/predictions.bin', tmp_path)


def test_research_package_member_is_read_and_verified(tmp_path):
    folder, index = make_store(tmp_path, b'protocol')
    package = tmp_path / 'data/processed/research_packages/history.zip'
    package.parent.mkdir(parents=True)
    payload = b'fixed run predictions\x00\xff'
    member = 'research/study/predictions.bin'
    with zipfile.ZipFile(package, 'w') as archive:
        archive.writestr(member, payload)
    index['live_files'] = {member: {'archive_path': package.relative_to(tmp_path).as_posix(),
                                  'member': member, 'bytes': len(payload),
                                  'sha256': hashlib.sha256(payload).hexdigest()}}
    (folder / 'INDEX.json').write_text(json.dumps(index), encoding='utf-8')
    assert records.read_bytes(member, tmp_path) == payload
    index['live_files'][member]['sha256'] = '0' * 64
    (folder / 'INDEX.json').write_text(json.dumps(index), encoding='utf-8')
    with pytest.raises(ValueError, match='content verification'):
        records.read_bytes(member, tmp_path)


def test_restore_never_overwrites_a_file_created_after_the_existence_check(tmp_path, monkeypatch):
    _, index = make_store(tmp_path, b'original source')
    destination = tmp_path / 'restored'
    target = destination / 'log/study/REPORT.md'
    original_mkdir = Path.mkdir

    def mkdir_with_concurrent_file(path, *args, **kwargs):
        original_mkdir(path, *args, **kwargs)
        if path == target.parent:
            target.write_bytes(b'new independent content')

    monkeypatch.setattr(records, 'ROOT', tmp_path)
    monkeypatch.setattr(records, 'load_index', lambda: index)
    monkeypatch.setattr(Path, 'mkdir', mkdir_with_concurrent_file)
    monkeypatch.setattr(sys, 'argv', ['retained_records', '--restore', 'log/study/REPORT.md',
                                    '--destination', str(destination)])
    with pytest.raises(FileExistsError):
        records.main()
    assert target.read_bytes() == b'new independent content'


def test_cli_show_loads_the_index_once(tmp_path, monkeypatch, capsys):
    _, index = make_store(tmp_path, b'exact source')
    calls = []

    def counted_load(*args):
        calls.append(args)
        return index

    monkeypatch.setattr(records, 'ROOT', tmp_path)
    monkeypatch.setattr(records, 'load_index', counted_load)
    monkeypatch.setattr(records, 'read_bytes', lambda name: records._read_bytes(name, tmp_path, counted_load(tmp_path)))
    monkeypatch.setattr(sys, 'argv', ['retained_records', '--show', 'log/study/REPORT.md'])
    records.main()
    assert capsys.readouterr().out == 'exact source'
    assert len(calls) == 1


def test_published_manifest_recovers_pinned_git_bytes_and_rejects_wrong_identity(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path).decode().strip()

    git('init', '-q')
    source = tmp_path / 'source.md'
    source.write_bytes(b'Historical conclusion\n')
    git('-c', 'core.autocrlf=false', 'add', 'source.md')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'source')
    commit, oid = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD:source.md')
    payload = b'Historical conclusion\n'
    item = {'git_path': 'source.md', 'git_blob': oid, 'bytes': len(payload),
            'sha256': hashlib.sha256(payload).hexdigest(), 'representation': 'git_blob'}
    index = {'source_commit': commit, 'files': {'source-id': item}}
    (tmp_path / 'log').mkdir()
    (tmp_path / 'log/SOURCE_MANIFEST.json').write_text(json.dumps(index), encoding='utf-8')
    source.write_bytes(b'Later working-tree change\n')
    assert records.read_bytes('source-id', tmp_path) == payload
    monkeypatch.setattr(records, 'ROOT', tmp_path)
    monkeypatch.setattr(records, 'load_index', lambda **kwargs: index)
    destination = tmp_path / 'restore'
    monkeypatch.setattr(sys, 'argv', ['retained_records', '--published', '--restore', 'source-id',
                                    '--destination', str(destination)])
    records.main()
    assert (destination / 'source-id').read_bytes() == payload
    item['git_blob'] = '0' * 40
    with pytest.raises(ValueError, match='Git source identity mismatch'):
        records._read_bytes('source-id', tmp_path, index)
    item['git_blob'] = oid
    index['source_commit'] = '0' * 40
    with pytest.raises(FileNotFoundError, match='git fetch origin'):
        records._read_bytes('source-id', tmp_path, index)


def test_published_supplement_is_exact_and_cannot_escape_checkout(tmp_path):
    payload = b'New correction\r\n'
    record = json.dumps({'encoding': 'base64', 'base64': base64.b64encode(payload).decode()}).encode()
    folder = tmp_path / 'log/source_supplement'
    folder.mkdir(parents=True)
    (folder / 'RECORDS.jsonl').write_bytes(record)
    item = {'record_path': 'log/source_supplement/RECORDS.jsonl', 'offset': 0,
            'length': len(record), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
    index = {'files': {'correction': item}}
    assert records._read_bytes('correction', tmp_path, index) == payload
    item['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='content verification'):
        records._read_bytes('correction', tmp_path, index)
    item['record_path'] = '../outside.jsonl'
    with pytest.raises(ValueError, match='Unsafe source supplement'):
        records._read_bytes('correction', tmp_path, index)


def test_explicit_published_manifest_does_not_reuse_private_local_index(tmp_path):
    make_store(tmp_path, b'local bytes')
    (tmp_path / 'log').mkdir()
    published = {'files': {}, 'scope': 'Published key sources only'}
    (tmp_path / 'log/SOURCE_MANIFEST.json').write_text(json.dumps(published), encoding='utf-8')
    assert records.load_index(tmp_path)['files']
    assert records.load_index(tmp_path, published=True) == published
