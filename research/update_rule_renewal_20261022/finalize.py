"""Bind the local research phase and verify predecessor preservation explicitly."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_rule_renewal'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (OUT / 'FINAL_BINDINGS.json').exists()
    required = ['DECISION.md', 'CONTINUATION.md', 'ROOT_ESG_PROTOCOL.md', 'EXACT_ESG.json',
                'frontier/INDEPENDENT.md', 'frontier/CROSS.md',
                'biology/INDEPENDENT.md', 'biology/API_REVIEW.md', 'biology/CROSS_API.md', 'biology/NATIVE_CROSS.md',
                'skeptic/INDEPENDENT.md', 'skeptic/API_REVIEW.md', 'skeptic/CROSS_ESG.md', 'skeptic/CROSS_FRONTIER.md']
    assert all((OUT / name).is_file() for name in required)
    exact = json.loads((OUT / 'EXACT_ESG.json').read_text())
    assert exact['null_calibration']['ordered']['gate_acceptance'] == '169/720'
    assert exact['null_calibration']['unique_unordered']['gate_acceptance'] == '49/720'
    assert json.loads((OUT / 'api/RECEIPT.json').read_text())['finish_reason'] == 'length'
    assert json.loads((OUT / 'api_completion/RECEIPT.json').read_text())['finish_reason'] == 'stop'
    predecessor = ROOT / 'log/20261022/revision_value_operation/FINAL_BINDINGS.json'
    previous = json.loads(predecessor.read_text())['bindings']
    mismatches = [name for name, digest in previous.items() if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
    assert not mismatches, mismatches
    receipts = []
    for path in OUT.rglob('*receipt.json'):
        receipt = json.loads(path.read_text())
        if 'url' in receipt:
            receipts.append({'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'status': receipt.get('status')})
    folders = [OUT, ROOT / 'research/update_rule_renewal_20261022',
               ROOT / 'research/update_rule_renewal_frontier_20261022']
    excluded = {'FINAL_BINDINGS.json', 'VERIFICATION.json'}
    bindings = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for folder in folders
                for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
    (OUT / 'FINAL_BINDINGS.json').write_text(json.dumps({
        'scope': 'Local phase only, not novelty/performance or global provenance', 'bindings': bindings}, indent=2), encoding='utf-8')
    assert all(sha(ROOT / name) == digest for name, digest in bindings.items())
    verification = {'status': 'PASS_LOCAL', 'current_files': len(bindings),
                    'predecessor_files_checked': len(previous), 'predecessor_mismatches': mismatches,
                    'http_receipts': receipts,
                    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    'src_tools_diff': subprocess.check_output(['git', 'diff', '--stat', '--', 'src', 'tools'], cwd=ROOT, text=True),
                    'full_goal': 'ACTIVE_NOT_ACHIEVED', 'historical_global_provenance': 'NOT_REPAIRED'}
    (OUT / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()
