"""Record the new constructive search without opening biological outcomes."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/operator_renewal/root'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = ROOT / 'log/20261022/native_operation/root/FINAL_FILE_INVENTORY.json'
    inventory = json.loads(manifest.read_text(encoding='utf-8'))
    checks = [{'path': r['path'], 'passed': (ROOT / r['path']).stat().st_size == r['bytes']
               and sha(ROOT / r['path']) == r['sha256']} for r in inventory['files']]
    assert len(checks) == 124 and all(r['passed'] for r in checks)
    postfinal = manifest.parent / 'POSTFINAL_VERIFICATION.json'
    post = json.loads(postfinal.read_text(encoding='utf-8-sig'))
    assert post['exit_code'] == 0 and post['sealed_inventory_sha256'] == sha(manifest)
    value = {'utc': datetime.now(timezone.utc).isoformat(),
        'previous_goal_turn': 'PROGRESS: exact reductions, actual reciprocal review and source qualification changed the next action',
        'objective': str(Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md')),
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'git_status': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'executable': sys.executable, 'python': sys.version, 'platform': platform.platform(),
        'predecessor_inventory_sha256': sha(manifest), 'predecessor_checks': checks,
        'predecessor_postfinal_sha256': sha(postfinal),
        'new_native_models_requested': {'frontier_operator_renewal': 'gpt-6-astra/high',
            'functional_operator_renewal': 'gpt-6.1-sol/high', 'recursive_operator_renewal': 'gpt-6-astra/high'},
        'model_attestation': 'Requested identifiers accepted by collaboration interface; backend not independently attested',
        'protected_reserve_scalar_accesses': 0, 'assay_scalar_decodes_authorized': 0,
        'goal': 'ACTIVE / NOT_ACHIEVED'}
    value['objective_sha256'] = sha(Path(value['objective']))
    with (OUT / 'START.json').open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)
    with (OUT / 'START_REPORT_SNAPSHOT.md').open('xb') as handle:
        handle.write((ROOT / 'research/REPORT.md').read_bytes())
    print(json.dumps({'passed': True, 'prior_phase_entries': len(checks), 'goal': value['goal']}))


if __name__ == '__main__':
    main()
