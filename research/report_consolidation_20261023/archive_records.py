"""Preserve research records/data in durable log storage before code retirement."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'research'
DEST = ROOT / 'log/research_records'
OUT = ROOT / 'log/20261023/report_consolidation'
CODE = {'.py', '.pyc', '.pyo', '.r', '.m', '.rmd', '.ipynb', '.sh', '.ps1', '.bat', '.cmd'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == '__main__':
    manifest = OUT / 'ARCHIVE_MANIFEST.json'
    if manifest.exists():
        raise FileExistsError(manifest)
    records, code_hashes = [], []
    files = sorted(p for p in SOURCE.rglob('*') if p.is_file())
    result = {'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'RUNNING',
              'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'scope': 'Research records/data copied; code represented by hashes, not copied into log',
              'records': records, 'code_hashes': code_hashes}
    try:
        for index, source in enumerate(files):
            source.resolve().relative_to(SOURCE.resolve())
            relative = source.relative_to(SOURCE)
            if source.suffix.lower() in CODE or '__pycache__' in relative.parts:
                code_hashes.append({'path': source.relative_to(ROOT).as_posix(),
                                    'bytes': source.stat().st_size, 'sha256': sha(source)})
                continue
            if source.name.startswith('.env'):
                raise ValueError('Unexpected secret-like file in research records')
            target = DEST / relative
            target.resolve().relative_to(DEST.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = sha(source)
            if target.exists():
                if sha(target) != digest:
                    raise ValueError(f'Archive destination conflict: {relative}')
            else:
                shutil.copyfile(source, target)
            if sha(target) != digest:
                raise ValueError(f'Archive hash mismatch: {relative}')
            records.append({'source': source.relative_to(ROOT).as_posix(),
                            'archive': target.relative_to(ROOT).as_posix(),
                            'bytes': source.stat().st_size, 'sha256': digest})
            if len(records) % 100 == 0:
                print(json.dumps({'records_copied_and_verified': len(records)}, ensure_ascii=True), flush=True)
        result.update(status='COMPLETE', records_count=len(records),
                      records_bytes=sum(r['bytes'] for r in records))
    except Exception as error:
        result.update(status='FAILED_RETAINED', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        result['ended_utc'] = datetime.now(timezone.utc).isoformat()
        manifest.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('records', 'code_hashes')}, indent=2))
