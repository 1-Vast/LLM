"""Seal pre-run independent metadata review; never read response or finite-mask artifacts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/prism_profile_opportunity'
OUT = LOG / 'data'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(OUT / 'INDEPENDENT.md') == '301a3a20ba7497f045f4c6c0fb51fb82e3dc5867503e792a6027ca5c25c6031f'
assert sha(OUT / 'INDEPENDENT_SPLIT.json') == 'aedf9670e8b9e7f9771c9916a6fd7247e17af24107ca23a415f36f7ffc9b44e0'
assert sha(ROOT / 'log/20261022/update_value_qualification/data/FIELD_CONTRACT.json') == 'ff6d9d5417349c7553f597a42128c7350e146b4e99245fc6376218514967fe1b'
comparison = json.loads((OUT / 'MANIFEST_COMPARISON.json').read_text(encoding='utf-8'))
assert comparison['checks'] == 50 and all(c['pass'] for c in comparison['detail'])
tests = json.loads((LOG / 'TEST_EXECUTION.json').read_text(encoding='utf-8'))
assert tests['exit_code'] == 0 and 'Ran 9 tests' in tests['stderr'] and 'OK' in tests['stderr']
files = [OUT / name for name in ('INDEPENDENT.md', 'INDEPENDENT_SPLIT.json', 'MANIFEST_COMPARISON.json', 'CROSS.md', 'WORK_AND_FAILURES.md')]
files += [LOG / name for name in ('PROTOCOL.md', 'MANIFEST.json', 'MANIFEST_v2.json', 'TEST_EXECUTION.json', 'advocate/INDEPENDENT.md', 'skeptic/INDEPENDENT_PROTOCOL_REVIEW.md')]
files += sorted((ROOT / 'research/prism_profile_opportunity_20261022').glob('data*.py'))
files += [ROOT / 'research/prism_profile_opportunity_20261022' / name for name in ('prepare.py', 'coverage.py', 'test_coverage.py')]
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
    'status': 'PRE_RUN_METADATA_REVIEW_COMPLETE', 'decision': 'GO_ONE_FROZEN_MASK_ONLY_GATE_NOT_FIT',
    'independent_saved_before_root_manifest_and_peer_drafts_read': True,
    'actual_bilateral_cross': ['mechanism_advocate', 'scientific_skeptic', 'root'],
    'independent_metadata_comparison_checks': comparison['checks'],
    'root_synthetic_test_receipt': '9 PASS; reviewed receipt, not independently rerun by data auditor',
    'response_matrices_or_finite_masks_read_by_data_auditor': 0,
    'new_GETs': 0, 'new_fits': 0, 'provider_calls': 0,
    'hashes': {str(p.relative_to(ROOT)): sha(p) for p in files},
    'subsequent_results_policy': 'Do not mutate frozen pre-run review; use a new POST_RESULT_REVIEW file.'}
out = OUT / 'CROSS_RECEIPT.json'
assert not out.exists()
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': receipt['status'], 'hash_bindings': len(receipt['hashes']), 'metadata_checks': receipt['independent_metadata_comparison_checks']}))
