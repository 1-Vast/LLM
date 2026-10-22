"""Record a fresh evidence-led phase without opening biological responses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/next_mechanism/root'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior = ROOT / 'log/20261022/mechanism_gap/root/FINAL_FILE_INVENTORY.json'
    records = json.loads(prior.read_text())['files']
    checks = [{'path': r['path'], 'passed': (ROOT / r['path']).stat().st_size == r['bytes']
               and sha(ROOT / r['path']) == r['sha256']} for r in records]
    assert len(checks) == 152 and all(r['passed'] for r in checks)
    objective = Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md')
    record = {'utc': datetime.now(timezone.utc).isoformat(),
        'previous_turn_classification': 'PROGRESS: sealed independent debate, counterexamples and static primary source facts changed admissible next action',
        'objective_sha256': sha(objective), 'full_goal': 'ACTIVE / NOT_ACHIEVED',
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'git_status': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
        'prior_inventory_sha256': sha(prior), 'previous_file_checks': checks,
        'recovery': 'list_agents returned only root; no old live handle; three fresh explicit user-authorized roles spawned',
        'model_identity': 'Inherited native model, backend identity not independently attested',
        'assay_scalar_reads': 0, 'fits': 0, 'protected_reserves_opened': 0}
    with (OUT / 'START.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(record, handle, indent=2)
    with (OUT / 'START_REPORT_SNAPSHOT.md').open('xb') as handle:
        handle.write((ROOT / 'research/REPORT.md').read_bytes())
    print(json.dumps({'prior_files_pass': len(checks), 'full_goal': record['full_goal']}))


if __name__ == '__main__':
    main()
