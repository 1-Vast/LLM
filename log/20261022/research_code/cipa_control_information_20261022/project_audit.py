"""Snapshot updated objective and current resources without printing credentials."""
from pathlib import Path
import subprocess
import sys
import os
import json
import hashlib
import platform
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cipa_control_information'
OBJECTIVE = Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md')

def command(args, timeout=60):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {'args': args, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'args': args, 'error': str(error)}

objective = OBJECTIVE.read_bytes()
with (OUT / 'ACTIVE_OBJECTIVE.md').open('xb') as handle:
    handle.write(objective)
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'objective_path': str(OBJECTIVE), 'objective_sha256': hashlib.sha256(objective).hexdigest(),
    'python': sys.executable, 'python_version': sys.version, 'platform': platform.platform(),
    'git_head': command(['git', 'rev-parse', 'HEAD']),
    'git_status': command(['git', 'status', '--short']),
    'git_diff_check': command(['git', 'diff', '--check']),
    'applicable_agents_files': command(['rg', '--files', '--hidden', '-g', 'AGENTS.md', '-g', '!.git']),
    'tracked_core_files': command(['git', 'ls-files', 'src', 'tools', 'tests', 'research/REPORT.md', 'research/EVIDENCE.md']),
    'gpu': command(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader']),
    'packages': command([sys.executable, '-B', '-c',
        "import importlib.metadata as m,json; print(json.dumps({n:m.version(n) for n in ['numpy','scipy','scikit-learn','requests','torch']}))"]),
    'credential_environment_names_present': sorted(k for k in os.environ if any(s in k.upper() for s in ('DEEPSEEK', 'API_KEY'))),
    'native_agents': [
        {'task': 'conditional_design_skeptic', 'requested_model': 'gpt-6-astra', 'effort': 'high', 'spawn_accepted': True},
        {'task': 'conditional_implementation', 'requested_model': 'gpt-6.1-sol', 'effort': 'high', 'spawn_accepted': True},
        {'task': 'frontier_mechanism_renewal', 'requested_model': 'gpt-6-astra', 'effort': 'high', 'spawn_accepted': True}],
    'model_identity_limit': 'Native tool accepted these model names; no independent backend identity attestation is claimed.',
    'new_deepseek_calls_so_far': 0,
    'prior_turn_classification': 'PROGRESS: actual975headfits, independentDecimal audit, actual3position debate and finalized STOP/retainedmixture decision',
    'full_goal': 'ACTIVE / NOT_ACHIEVED',
}
with (OUT / 'PROJECT_ENVIRONMENT_AUDIT.json').open('x', encoding='utf-8') as handle:
    json.dump(result, handle, indent=2)
print(json.dumps({k: result[k] for k in ('objective_sha256','python','git_head','gpu','packages','full_goal')}, indent=2))
