"""Read or explicitly restore exact source records retained during report consolidation."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = Path('data/processed/research_records')


def load_index(root: Path = ROOT, *, published: bool = False) -> dict:
    local = root / STORE / 'INDEX.json'
    target = local if local.is_file() and not published else root / 'log/SOURCE_MANIFEST.json'
    return json.loads(target.read_text(encoding='utf-8'))


def resolve(path: str, index: dict) -> str:
    name = path.replace('\\', '/').removeprefix('./')
    files, live_files = index['files'], index.get('live_files', {})
    seen = set()
    while name not in files and name not in live_files and name in index.get('aliases', {}):
        if name in seen:
            raise ValueError(f'Circular historical path: {path}')
        seen.add(name)
        name = index['aliases'][name]
    if name not in files and name not in live_files:
        raise FileNotFoundError(path)
    return name


def read_bytes(path: str, root: Path = ROOT) -> bytes:
    return _read_bytes(path, root, load_index(root))


def _read_bytes(path: str, root: Path, index: dict) -> bytes:
    name = resolve(path, index)
    item = index['files'].get(name) or index['live_files'][name]
    if 'git_blob' in item:
        commit, git_path = index['source_commit'], item['git_path']
        if not re.fullmatch('[0-9a-f]{40}', commit) or not re.fullmatch('[0-9a-f]{40}', item['git_blob']):
            raise ValueError('Invalid Git source identity')
        if git_path.startswith(('/', '\\')) or '..' in git_path.split('/'):
            raise ValueError(f'Unsafe Git source path: {path}')
        result = subprocess.run(['git', 'show', f'{commit}:{git_path}'], cwd=root, capture_output=True)
        if result.returncode:
            raise FileNotFoundError(f'Git source unavailable: {path}; fetch its fixed version with git fetch origin {commit}')
        data = result.stdout
        oid = hashlib.sha1(f'blob {len(data)}\0'.encode('ascii') + data).hexdigest()
        if oid != item['git_blob']:
            raise ValueError(f'Git source identity mismatch: {path}')
    elif 'record_path' in item:
        target = (root / item['record_path']).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError(f'Unsafe source supplement path: {path}')
        with target.open('rb') as stream:
            stream.seek(item['offset'])
            record = json.loads(stream.read(item['length']))
        data = record['text'].encode('utf-8') if record['encoding'] == 'utf-8' else base64.b64decode(record['base64'], validate=True)
    elif 'archive_path' in item:
        target = (root / item['archive_path']).resolve()
        member = item['member']
        if not target.is_relative_to(root.resolve()) or member.startswith('/') or '..' in member.split('/'):
            raise ValueError(f'Unsafe retained package path: {path}')
        with zipfile.ZipFile(target) as archive:
            data = archive.read(member)
    elif 'live_path' in item:
        target = (root / item['live_path']).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError(f'Unsafe retained source path: {path}')
        data = target.read_bytes()
    else:
        with (root / STORE / 'RECORDS.jsonl').open('rb') as stream:
            stream.seek(item['offset'])
            record = json.loads(stream.read(item['length']))
        data = record['text'].encode('utf-8') if record['encoding'] == 'utf-8' else base64.b64decode(record['base64'], validate=True)
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise ValueError(f'Retained source failed content verification: {path}')
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--show', metavar='ORIGINAL_PATH', help='Print one UTF-8 source record without recreating files.')
    actions.add_argument('--list', metavar='PREFIX', help='List retained paths under a historical prefix.')
    actions.add_argument('--restore', metavar='PREFIX', help='Restore bytes of the selected representation under a prefix.')
    parser.add_argument('--destination', type=Path, help='Required for restoration; no existing differing file is overwritten.')
    parser.add_argument('--published', action='store_true', help='Use published Git identities and small supplements, including when a local store exists.')
    args = parser.parse_args()
    index = load_index(published=True) if args.published else load_index()
    if args.show is not None:
        print(_read_bytes(args.show, ROOT, index).decode('utf-8'), end='')
        return
    prefix = (args.list if args.list is not None else args.restore).replace('\\', '/').rstrip('/')
    names = sorted(name for name in set(index['files']) | set(index.get('live_files', {})) | set(index.get('aliases', {})) if name == prefix or name.startswith(prefix + '/'))
    if not names:
        parser.error('No retained source matches the prefix.')
    if args.list is not None:
        for name in names:
            print(name)
        return
    if args.destination is None:
        parser.error('--restore requires an explicit --destination.')
    destination = args.destination.resolve()
    for name in names:
        target = (destination / name).resolve()
        if not target.is_relative_to(destination):
            raise ValueError(f'Unsafe retained path: {name}')
        data = _read_bytes(name, ROOT, index)
        if target.exists():
            if target.read_bytes() != data:
                raise FileExistsError(f'Refusing to overwrite different content: {target}')
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        resolved = resolve(name, index)
        item = index['files'].get(resolved) or index['live_files'][resolved]
        if 'atime_ns' in item and 'mtime_ns' in item:
            os.utime(target, ns=(item['atime_ns'], item['mtime_ns']))
        if 'mode' in item:
            os.chmod(target, item['mode'])
    print(f'Restored {len(names)} verified source representations into {destination}')


if __name__ == '__main__':
    main()
