"""Check this phase's frozen evidence and retain a final byte manifest."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/functional_update_operation'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(seal):
    entries = json.loads(seal.read_text(encoding='utf-8'))['files']
    if isinstance(entries, dict):
        entries = [dict(path=p, sha256=h) for p, h in entries.items()]
    for entry in entries:
        path = Path(entry['path'])
        if not path.is_absolute():
            path = ROOT / path
        assert digest(path) == entry['sha256'], str(path)
    return len(entries)


if __name__ == '__main__':
    target = OUT / 'VERIFICATION.json'
    if target.exists():
        count = check(target)
        print(json.dumps(dict(files=count, drift=0, mode='recheck')))
    else:
        seals = [ROOT / 'log/20261023/depmap_state_increment/VERIFICATION.json',
                 OUT / 'CRITERION_FREEZE.json', OUT / 'constructive/CAPACITY_FREEZE.json']
        seals += sorted(OUT.rglob('*[Ss][Ee][Aa][Ll].json'))
        checked = {p.relative_to(ROOT).as_posix(): check(p) for p in seals}
        audit = json.loads((OUT / 'critic/CRITERION_INDEPENDENT_CHECK.json').read_text())
        assert all(audit['result_agreement'].values())
        assert all(row['pass'] for row in audit['freeze_bindings'])
        receipt = json.loads((OUT / 'api/RECEIPT.json').read_text())
        assert receipt['finish_reason'] == 'stop'
        assert receipt['provider_usage']['total_tokens'] == 4868
        for role in ['constructive', 'critic']:
            assert (OUT / role / 'CROSS.md').exists()
        files = {p.relative_to(ROOT).as_posix(): digest(p)
                 for base in [OUT, Path(__file__).resolve().parent]
                 for p in sorted(base.rglob('*')) if p.is_file() and p != target}
        target.write_text(json.dumps(dict(files=files, checked_seals=checked,
            decision='NO_NEW_CORE_GO', goal='ACTIVE / NOT_ACHIEVED',
            scope='local byte and arithmetic verification; no biological validation'), indent=2),
            encoding='utf-8')
        assert check(target) == len(files)
        print(json.dumps(dict(files=len(files), drift=0, mode='initial-seal')))
