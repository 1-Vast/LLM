"""Open the new evidence-led round without decoding biological outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mechanism_gap/root'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior = ROOT / 'log/20261022/operator_renewal/root/FINAL_FILE_INVENTORY.json'
    records = json.loads(prior.read_text())['files']
    checks = [{'path': r['path'], 'passed': (ROOT / r['path']).stat().st_size == r['bytes']
               and sha(ROOT / r['path']) == r['sha256']} for r in records]
    assert len(checks) == 148 and all(row['passed'] for row in checks)
    objective = Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md')
    value = {'utc': datetime.now(timezone.utc).isoformat(),
        'previous_turn_classification': 'PROGRESS: conditional information result independently sharpened; actual opposing debate and nearest-primary review changed promotion/source decisions',
        'objective': str(objective), 'objective_sha256': sha(objective),
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'git_status': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
        'previous_inventory_sha256': sha(prior), 'previous_file_checks': checks,
        'native_continuations': {'frontier': 'running at confirmed status check',
            'functional': 'running at confirmed status check',
            'recursive': 'FAILED native403insufficientbalance; request e8bd2acb-ece5-42a0-a8d2-dbdcef3a9dd0'},
        'model_attestation': 'Inherited requested identifiers only, no independent backend attestation',
        'deepseek_fallback': 'Separate configured provider context; not a successful native recursive role and not cross-model independent evidence',
        'assay_scalar_reads': 0, 'fits': 0, 'protected_reserves_opened': 0,
        'full_goal': 'ACTIVE / NOT_ACHIEVED'}
    with (OUT / 'START.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2)
    with (OUT / 'START_REPORT_SNAPSHOT.md').open('xb') as handle:
        handle.write((ROOT / 'research/REPORT.md').read_bytes())
    print(json.dumps({'previous_files_preserved': len(checks), 'goal': value['full_goal']}))


if __name__ == '__main__':
    main()
