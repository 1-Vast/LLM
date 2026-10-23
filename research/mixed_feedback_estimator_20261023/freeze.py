"""Bind reviewed code, exact source membership and raw inputs before state access."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from datetime import datetime, timezone
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/mixed_feedback_estimator'


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


if __name__ == '__main__':
    assert not (OUT / 'FREEZE.json').exists()
    assert not (OUT / 'EXTRACTION_STARTED.json').exists()
    names = [
        'log/20261023/mixed_feedback_estimator/STATE_PROTOCOL.md',
        'log/20261023/mixed_feedback_estimator/support/SOURCE_PAIR_METADATA.csv',
        'log/20261023/mixed_feedback_estimator/constructive/PREFIT_REVIEW.md',
        'log/20261023/mixed_feedback_estimator/prior/PREFIT_REVIEW.md',
        'log/20261023/reciprocity_resolution/IDENTITY.json',
        'log/20261022/norman_functional_contract/PAIR_SPLITS.csv',
        'log/20261022/norman_functional_contract/data/GSE133344_raw_cell_identities.csv.gz',
        'log/20261022/norman_functional_contract/data/GSE133344_raw_barcodes.tsv.gz',
        'log/20261022/norman_functional_contract/data/GSE133344_raw_genes.tsv.gz',
        'log/20261022/norman_functional_contract/data/GSE133344_raw_matrix.mtx.gz',
        'research/mixed_feedback_estimator_20261023/extract.py',
        'research/mixed_feedback_estimator_20261023/predict.py',
        'research/mixed_feedback_estimator_20261023/test_predict.py',
        'research/mixed_feedback_estimator_20261023/freeze.py',
    ]
    report = {'utc': datetime.now(timezone.utc).isoformat(),
              'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'python': platform.python_version(), 'numpy': np.__version__, 'fit_threads': 1,
              'files': {name: digest(ROOT / name) for name in names},
              'scope': 'Frozen single execution; source-state falsifier, not independent confirmation or final goal completion'}
    (OUT / 'FREEZE.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}))
