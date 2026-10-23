"""Review publication scope and preserved migrations before staging; never opens model/data arrays."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/main_publication'
SAFE_LOG = {'.md', '.json', '.jsonl', '.txt', '.sha256', '.log'}
SOURCE_DIRS = {'source', 'sources', 'root_sources', 'render', 'remote_schema', 'remote_image_metadata'}
RECEIPTS = {'REQUESTS.jsonl', 'RECEIPTS.json', 'SOURCE_RECEIPTS.json'}
SECRET = re.compile(r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----|\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', action='store_true')
    args = parser.parse_args()
    tracked = [p for p in git('diff', '--name-only', '-z', 'HEAD').split('\0') if p]
    untracked = [p for p in git('ls-files', '--others', '--exclude-standard', '-z').split('\0') if p]
    included, excluded = [], []
    for name in untracked:
        p = Path(name)
        parts = set(p.parts)
        is_source = bool(parts & SOURCE_DIRS) and p.name not in RECEIPTS
        allowed = (name.startswith('research/') and p.suffix.lower() in {'.py', '.ps1', '.md'}
                   or name.startswith('log/') and p.suffix.lower() in SAFE_LOG and not is_source
                   or name == 'src/README.md')
        if name.endswith('/github_report_payload.json'):
            allowed = False
        (included if allowed else excluded).append(name)
    docs = ['data/raw/README.md', 'data/external/README.md', 'data/processed/README.md']
    included += [p for p in docs if (ROOT / p).is_file() and p not in included]
    candidates = sorted(set(tracked + included))
    issues = []
    for name in candidates:
        p = ROOT / name
        if not p.is_file():
            continue
        if p.stat().st_size > 10_000_000:
            issues.append({'path': name, 'reason': 'oversize'})
        try:
            text = p.read_text(encoding='utf-8')
        except UnicodeError:
            issues.append({'path': name, 'reason': 'unexpected binary'})
            continue
        if SECRET.search(text):
            issues.append({'path': name, 'reason': 'secret-shaped text requires review'})
    mappings = {}
    for name in ('DATA_MIGRATION_RECEIPT.json', 'DATA_MIGRATION_SUPPLEMENT_RECEIPT.json', 'TEXT_SOURCE_MIGRATION_RECEIPT.json'):
        record = json.loads((ROOT / 'log/20261023/report_consolidation' / name).read_text(encoding='utf-8'))
        mappings.update({r['old_path']: r for r in record['files']})
    deletions = [p for p in tracked if not (ROOT / p).exists()]
    preservation = []
    for name in deletions:
        m = mappings.get(name)
        ok = bool(m and (ROOT / m['data_path']).is_file() and sha(ROOT / m['data_path']) == m['sha256'])
        preservation.append({'old_path': name, 'data_path': m['data_path'] if m else None, 'preserved_hash_match': ok})
        if not ok:
            issues.append({'path': name, 'reason': 'deleted path has no verified preserved migration'})
    report = {'base_commit': git('rev-parse', 'HEAD').strip(), 'tracked_changes': len(tracked),
              'new_included': included, 'excluded_local_artifacts': excluded, 'candidate_paths': candidates,
              'tracked_deletion_preservation': preservation, 'issues': issues,
              'scope': 'Reports, key result/operation records, experimental code and documentation; source/data/model artifacts remain local'}
    (OUT / 'PLAN.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'tracked_changes': len(tracked), 'included_new': len(included), 'excluded_local': len(excluded),
                      'verified_migrated_deletions': sum(x['preserved_hash_match'] for x in preservation), 'issues': issues}, indent=2))
    if issues:
        raise SystemExit(1)
    if args.stage:
        # Explicit path list: never sweep large ignored data or unrelated artifacts into the index.
        known = set(git('ls-files', '-z').split('\0'))
        paths = sorted(p for p in set(candidates + ['log/20261023/main_publication/PLAN.json'])
                       if (ROOT / p).exists() or p in known)
        result = subprocess.run(['git', 'add', '-f', '--pathspec-from-file=-', '--pathspec-file-nul'],
                                input='\0'.join(paths).encode('utf-8') + b'\0', cwd=ROOT, capture_output=True)
        if result.returncode:
            print(result.stderr.decode('utf-8'))
            raise SystemExit(result.returncode)
        existing = [p for p in paths if (ROOT / p).is_file()]
        subprocess.run(['git', 'add', '--renormalize', '--pathspec-from-file=-', '--pathspec-file-nul'],
                       input='\0'.join(existing).encode('utf-8') + b'\0', cwd=ROOT, check=True, capture_output=True)
        print('Staged reviewed paths only')


if __name__ == '__main__':
    main()
