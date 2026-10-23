"""Plan relocation of data/source artifacts out of log; do not read numeric payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log'
OUT = LOG / '20261023/report_consolidation'
INPUTS = {'.cel', '.xlsx', '.xls', '.h5ad', '.h5', '.hdf5', '.mtx', '.sdf', '.rds', '.rda', '.mat', '.gmt', '.fcs', '.sqlite', '.db'}
DERIVED = {'.npz', '.npy', '.pkl', '.pickle', '.pt', '.pth', '.ckpt', '.parquet', '.feather'}
EXTERNAL = {'.body', '.range', '.bin', '.text', '.xml', '.html', '.htm', '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.py', '.r', '.m', '.rmd', '.ipynb', '.sh'}
KEY = ('manifest', 'audit', 'coverage', 'receipt', 'freeze', 'integrity', 'seal', 'binding', 'index', 'ledger', 'verification', 'summary', 'decision')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def category(path):
    suffix = path.suffix.lower()
    relative = path.relative_to(LOG).as_posix().lower()
    source = any(t in relative for t in ('/source/', '/sources/', '/raw/', '/papers/', '/download', '/external/', '/data/'))
    if suffix in INPUTS:
        return 'raw/research_inputs'
    if suffix in DERIVED:
        return 'processed/research_results'
    if suffix in EXTERNAL:
        return 'external/research_sources'
    if suffix == '.pdf' and '/figures/' not in relative and '/plots/' not in relative:
        return 'external/research_sources'
    if suffix in {'.csv', '.tsv', '.txt', '.json', '.jsonl'}:
        key = any(k in path.name.lower() for k in KEY)
        if suffix in {'.csv', '.tsv'} and (source or path.stat().st_size > 256 * 1024):
            return 'external/research_sources' if source else 'processed/research_results'
        if suffix == '.txt' and (source or 'primary_text' in path.name.lower() or path.stat().st_size > 256 * 1024) and not key:
            return 'external/research_sources'
        if suffix in {'.json', '.jsonl'} and path.stat().st_size > 2 * 1024 * 1024 and not key:
            return 'external/research_sources' if source else 'processed/research_results'
    return None


if __name__ == '__main__':
    manifest = OUT / ('DATA_MIGRATION_SUPPLEMENT_PLAN.json' if len(sys.argv) > 1 else 'DATA_MIGRATION_PLAN.json')
    if manifest.exists():
        raise FileExistsError(manifest)
    items = []
    for path in sorted(LOG.rglob('*')):
        if not path.is_file() or path.is_relative_to(OUT):
            continue
        kind = category(path)
        if not kind:
            continue
        path.resolve().relative_to(LOG.resolve())
        target = ROOT / 'data' / kind / path.relative_to(LOG)
        target.resolve().relative_to((ROOT / 'data').resolve())
        checksum = digest(path)
        if target.exists() and digest(target) != checksum:
            raise ValueError(f'Data destination conflict: {target.relative_to(ROOT)}')
        items.append({'old_path': path.relative_to(ROOT).as_posix(),
                      'data_path': target.relative_to(ROOT).as_posix(),
                      'bytes': path.stat().st_size, 'sha256': checksum, 'kind': kind})
        if len(items) % 1000 == 0:
            print(json.dumps({'classified_and_hashed': len(items)}), flush=True)
    result = {'status': 'PREPARED', 'utc': datetime.now(timezone.utc).isoformat(),
              'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'authorization': 'User clarified log keeps key reports/results; data belongs in its corresponding data location',
              'files': items, 'file_count': len(items), 'bytes': sum(r['bytes'] for r in items)}
    manifest.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
