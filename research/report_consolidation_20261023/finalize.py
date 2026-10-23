"""Verify storage/retirement and write durable report/data location indexes."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/report_consolidation'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    archive = read('ARCHIVE_MANIFEST.json')
    migrations = [read('DATA_MIGRATION_RECEIPT.json'), read('DATA_MIGRATION_SUPPLEMENT_RECEIPT.json'), read('TEXT_SOURCE_MIGRATION_RECEIPT.json')]
    deletion = read('DELETION_RECEIPT.json')
    residual = read('RESIDUAL_CLEANUP_RECEIPT.json')
    approved = read('APPROVED_DELETIONS.json')
    if any(r['status'] != 'COMPLETE' for r in migrations + [archive, deletion, residual]):
        raise ValueError('Incomplete operation')
    moved = {r['old_path']: r['data_path'] for receipt in migrations for r in receipt['files']}
    moved.update({r['old_log_path']: r['data_path'] for r in residual['files'] if r['old_log_path']})
    locations = []
    missing_records, changed_records = [], []
    for item in archive['records']:
        current = moved.get(item['archive'], item['archive'])
        path = ROOT / current
        if not path.is_file() or path.stat().st_size != item['bytes']:
            missing_records.append(current)
        elif current.startswith('log/') and sha(path) != item['sha256']:
            changed_records.append(current)
        locations.append({'original_research_path': item['source'], 'current_path': current,
                          'bytes': item['bytes'], 'sha256': item['sha256']})
    (OUT / 'ARCHIVE_LOCATIONS.json').write_text(json.dumps({'records': locations}, indent=2), encoding='utf-8')
    deleted_paths = [r['path'] for r in deletion['files']] + [r['old_path'] for r in residual['files']]
    still_present = [p for p in deleted_paths if (ROOT / p).exists()]
    changed_protected = [p for p, expected in approved['protected_source_hashes'].items()
                         if not (ROOT / p).is_file() or sha(ROOT / p) != expected]
    data_problems = []
    for receipt in migrations:
        for row in receipt['files']:
            target = ROOT / row['data_path']
            if not target.is_file() or target.stat().st_size != row['bytes'] or (ROOT / row['old_path']).exists():
                data_problems.append(row['old_path'])
    # A concurrently created source was not part of the deletion baseline. Keep it
    # and update only its relocated, hash-identical input path.
    concurrent = ROOT / 'research/certified_discovery_gates_20261023/census.py'
    concurrent_note = None
    if concurrent.exists():
        text = concurrent.read_text(encoding='utf-8')
        before = sha(concurrent)
        changed_paths = []
        for old, new in moved.items():
            needle = 'ROOT / "' + old + '"'
            if needle in text:
                text = text.replace(needle, 'ROOT / "' + new + '"')
                changed_paths.append({'old_path': old, 'data_path': new})
        if changed_paths:
            if sha(concurrent) != before:
                raise ValueError('Concurrent source changed during path update')
            concurrent.write_text(text, encoding='utf-8')
        concurrent_note = {'path': concurrent.relative_to(ROOT).as_posix(), 'retained': True,
                           'reason': 'Created after cleanup baseline, not reviewed for retirement',
                           'before_sha256': before, 'after_sha256': sha(concurrent),
                           'input_path_updates': changed_paths}
    entrypoints = [ROOT / p for p in ('research/REPORT.md', 'research/EVIDENCE.md', 'log/README.md',
                  'log/20261023/PROGRESS_SUMMARY.md', 'log/STORAGE_POLICY.md',
                  'log/research_records/README.md')]
    entrypoints += [OUT / name for name in ('RESEARCH_SUMMARY.md', 'LUNA_EARLY_SUMMARY.md',
                                          'LUNA_RECENT_SUMMARY.md', 'STUDY_INDEX.md')]
    broken = []
    for page in entrypoints:
        for target in re.findall(r'\]\(([^\n)]+)\)', page.read_text(encoding='utf-8-sig')):
            target = target.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-z]+://', target):
                continue
            if not (page.parent / target).resolve().exists():
                broken.append({'page': page.relative_to(ROOT).as_posix(), 'target': target})
    bytes_moved = sum(r['bytes'] for receipt in migrations for r in receipt['files'])
    files_moved = sum(len(r['files']) for r in migrations)
    before_sizes = {r['source']: r['bytes'] for r in archive['records']}
    navigation_before = before_sizes['research/REPORT.md'] + before_sizes['research/EVIDENCE.md'] + (OUT / 'original_entrypoints/log__README.md').stat().st_size
    navigation_after = sum((ROOT / p).stat().st_size for p in ('research/REPORT.md', 'research/EVIDENCE.md', 'log/README.md'))
    result = {'scope': 'Storage, code-retirement and navigation verification; no model/biological validation',
              'archived_research_records': len(locations), 'archived_research_bytes': archive['records_bytes'],
              'relocated_data_files': files_moved, 'relocated_data_bytes': bytes_moved,
              'retired_research_files': len(deleted_paths), 'retired_main_code_files': deletion['deleted_files'],
              'retired_residual_files': residual['file_count'],
              'protected_source_files': len(approved['protected_source_hashes']),
              'missing_archived_records': missing_records, 'changed_archived_key_records': changed_records,
              'remaining_deleted_paths': still_present, 'changed_protected_source': changed_protected,
              'data_migration_problems': data_problems, 'broken_entrypoint_links': broken,
              'concurrent_source': concurrent_note,
              'entrypoint_bytes_before': navigation_before, 'entrypoint_bytes_after': navigation_after,
              'pass': not any((missing_records, changed_records, still_present, changed_protected, data_problems, broken))}
    (OUT / 'FINAL_VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    data_text = f'''# Data locations after report consolidation

{files_moved} files ({bytes_moved:,} bytes) were relocated out of `log/`. Content hashes were checked before and after each relocation. This is storage verification, not analysis of outcomes.

- Raw inputs: `data/raw/research_inputs/`.
- External datasets, documents and downloaded sources: `data/external/research_sources/`.
- Detailed derived data, model artifacts and numeric outputs: `data/processed/research_results/`.
- Retained third-party source copies from retired experiment folders: `data/external/retired_research_sources/`.

Exact original/current paths and hashes: [main migration receipt](DATA_MIGRATION_RECEIPT.json), [supplement](DATA_MIGRATION_SUPPLEMENT_RECEIPT.json), and [retained research record locations](ARCHIVE_LOCATIONS.json). Historical frozen manifests keep their original content; use these maps to resolve paths after organization. Key reports and result summaries stay in `log/`; experimental code stays in `research/`. No code was promoted to `src/` or `tools/`.
'''
    (OUT / 'DATA_LOCATIONS.md').write_text(data_text, encoding='utf-8')
    inventory = ROOT / 'data/INVENTORY.md'
    heading = '## Research record relocation (2026-10-23)'
    old_text = inventory.read_text(encoding='utf-8-sig')
    if heading in old_text:
        updated = re.sub(r'(?m)^\d+ files / [\d,]+ bytes were relocated from log storage',
                         f'{files_moved} files / {bytes_moved:,} bytes were relocated from log storage', old_text)
        if updated != old_text:
            inventory.write_text(updated, encoding='utf-8')
    else:
        inventory.write_text(old_text + f'\n\n{heading}\n\n{files_moved} files / {bytes_moved:,} bytes were relocated from log storage into raw, external-source and processed-data research subtrees. The base inventory above remains dated as stated. No outcome values were decoded for this maintenance. Exact paths, hashes and operation receipts are in [DATA_LOCATIONS.md](../log/20261023/report_consolidation/DATA_LOCATIONS.md). This is a relocation record, not a new independent dataset or scientific result.\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'concurrent_source'}, indent=2))
    if not result['pass']:
        raise SystemExit(1)
