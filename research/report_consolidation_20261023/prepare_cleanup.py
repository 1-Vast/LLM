"""Build a checked exact-file retirement manifest; never delete files here."""
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/report_consolidation'
RESEARCH = (ROOT / 'research').resolve()
CURRENT = {'distribution_health_qualification_20261023', 'functional_state_sufficiency_20261023',
           'report_consolidation_20261023'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    target = OUT / 'APPROVED_DELETIONS.json'
    if target.exists():
        raise FileExistsError(target)
    archive = json.loads((OUT / 'ARCHIVE_MANIFEST.json').read_text(encoding='utf-8'))
    if archive['status'] != 'COMPLETE':
        raise ValueError('Records archive incomplete')
    migration = json.loads((OUT / 'DATA_MIGRATION_RECEIPT.json').read_text(encoding='utf-8-sig'))
    if migration['status'] != 'COMPLETE':
        raise ValueError('Data migration incomplete')
    moved = {r['old_path']: r['data_path'] for r in migration['files']}
    extra = json.loads((OUT / 'DATA_MIGRATION_SUPPLEMENT_RECEIPT.json').read_text(encoding='utf-8-sig'))
    if extra['status'] != 'COMPLETE':
        raise ValueError('Supplemental data migration incomplete')
    moved.update({r['old_path']: r['data_path'] for r in extra['files']})
    for record in archive['records']:
        path = ROOT / moved.get(record['archive'], record['archive'])
        if not path.is_file() or path.stat().st_size != record['bytes']:
            raise ValueError('Archived record missing or changed')
    old_hashes = {r['path']: r['sha256'] for r in archive['code_hashes']}
    registry = json.loads((RESEARCH / 'STUDIES.json').read_text(encoding='utf-8'))['studies']
    protected_names = {r['path'] for r in registry} | CURRENT
    protected = list((ROOT / 'src').rglob('*.py')) + list((ROOT / 'tools').rglob('*.py')) + list((ROOT / 'tests').rglob('*.py'))
    for name in {r['path'] for r in registry}:
        protected.extend((RESEARCH / name).rglob('*.py'))
    source_text = {p: p.read_text(encoding='utf-8-sig').lower() for p in protected}
    tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
    audit = json.loads((OUT / 'CODE_CANDIDATES.json').read_text(encoding='utf-8'))
    directories = [r for r in audit['directories'] if r['disposition'].startswith('CANDIDATE_')]
    followup = json.loads((OUT / 'HOLD_REVIEW.json').read_text(encoding='utf-8'))['entries']
    by_path = {r['path']: r for r in audit['directories']}
    for item in followup:
        if item['runtime_and_registration_check']['source_dependency_scan_exact_hits']:
            raise ValueError('Dependency in hold followup')
        references = [re.sub(r':\d+$', '', p) for p in item['owner_evidence']]
        missing = [p for p in references if not (ROOT / moved.get(p, p)).exists()]
        if missing:
            raise ValueError(f'Missing hold ownership record: {missing}')
        row = by_path[item['research_path']]
        row['final_log_docs'] = item['owner_evidence']
        directories.append(row)
    commands = subprocess.check_output(['powershell', '-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"], text=True)
    processes = json.loads(commands) if commands.strip() else []
    if isinstance(processes, dict):
        processes = [processes]
    approved = []
    external_sources = []
    for directory in directories:
        folder = ROOT / directory['path']
        folder.resolve().relative_to(RESEARCH)
        if folder.name in protected_names or directory['registered'] or directory['source_code_refs']:
            raise ValueError(f'Protected directory candidate: {folder.name}')
        refs = [p.relative_to(ROOT).as_posix() for p, text in source_text.items() if folder.name.lower() in text]
        if refs:
            raise ValueError(f'Protected source references candidate {folder.name}: {refs}')
        live = [p['ProcessId'] for p in processes if folder.name.lower() in (p.get('CommandLine') or '').lower()]
        if live:
            raise ValueError(f'Live process uses {folder.name}: {live}')
        for record in directory['code_files']:
            relative = record['path']
            path = ROOT / relative
            path.resolve().relative_to(folder.resolve())
            path.resolve().relative_to(RESEARCH)
            if path.is_symlink() or relative in tracked or record['tracked']:
                raise ValueError(f'Non-retirable path: {relative}')
            digest = sha(path)
            if old_hashes.get(relative) != digest:
                raise ValueError(f'Source changed after record archive: {relative}')
            if path.suffix.lower() in {'.r', '.m', '.rmd'} or any('published_code' in part for part in path.parts):
                retained = ROOT / 'data/external/retired_research_sources' / path.relative_to(RESEARCH)
                retained.resolve().relative_to((ROOT / 'data').resolve())
                retained.parent.mkdir(parents=True, exist_ok=True)
                if not retained.exists():
                    shutil.copyfile(path, retained)
                if sha(retained) != digest:
                    raise ValueError('External source copy mismatch')
                external_sources.append({'original': relative, 'data_path': retained.relative_to(ROOT).as_posix(),
                                         'sha256': digest, 'bytes': path.stat().st_size})
            approved.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest,
                             'owner': directory['path'], 'log_records': directory['final_log_docs']})
    result = {'status': 'PREPARED', 'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'authorization': 'User requested deletion of irrelevant/redundant exploratory code after durable record preservation',
              'directories': [r['path'] for r in directories], 'files': approved,
              'file_count': len(approved), 'bytes': sum(r['bytes'] for r in approved),
              'protected_source_hashes': {p.relative_to(ROOT).as_posix(): sha(p) for p in protected},
              'archive_manifest_sha256': sha(OUT / 'ARCHIVE_MANIFEST.json'),
              'external_source_copies': external_sources,
              'scope': 'Only listed untracked exploratory files; no log/src/tools/tests/formal/current code deletion'}
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'directories': len(directories),
                      'file_count': len(approved), 'bytes': result['bytes'], 'protected_sources': len(protected)}, indent=2))
