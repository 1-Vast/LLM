"""Record a native constructive search and preserve the immediately prior phase."""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/native_operation/root'
OBJECTIVE = Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = ROOT / 'log/20261022/mse_source_gate/FINAL_FILE_INVENTORY.json'
    inventory = json.loads(manifest.read_text(encoding='utf-8'))
    checks = [{'path': row['path'], 'passed': sha(ROOT / row['path']) == row['sha256']
               and (ROOT / row['path']).stat().st_size == row['bytes']} for row in inventory['files']]
    assert len(checks) == 92 and all(row['passed'] for row in checks)
    write('PREDECESSOR_SNAPSHOT.json', {'passed': True, 'checks': checks,
          'manifest_sha256': sha(manifest), 'manifest_path': manifest.relative_to(ROOT).as_posix()})
    write('START.json', {'utc': datetime.now(timezone.utc).isoformat(),
          'previous_turn': 'PROGRESS: frozen numerical STOP and independent reconstruction changed next action',
          'objective_path': str(OBJECTIVE), 'objective_sha256': sha(OBJECTIVE),
          'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
          'native_requested_models': {'native_operation_proposer': 'gpt-6-astra/high',
                                     'native_improver_proposer': 'gpt-6.1-sol/high',
                                     'native_biological_bottleneck': 'gpt-6-astra/high'},
          'model_attestation': 'Tool accepted advertised requested identifiers; backend identity not independently attested',
          'deepseek_calls_planned': 0, 'assay_value_decodes_authorized': 0, 'biological_fits_authorized': 0,
          'goal': 'ACTIVE / NOT_ACHIEVED'})
    print(json.dumps({'passed': True, 'prior_entries': len(checks), 'goal': 'ACTIVE / NOT_ACHIEVED'}))


if __name__ == '__main__':
    main()
