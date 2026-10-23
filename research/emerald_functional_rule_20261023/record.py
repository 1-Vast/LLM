"""Record environment and descriptive result differences, without new fitting."""
import collections
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
import numpy as np
import pyarrow
from run import ROOT, OUT

r = json.loads((OUT / 'RESULT.json').read_text())
m = r['metrics']
trials = json.loads((OUT / 'TRIALS.json').read_text())
old = json.loads((ROOT / 'log/20261023/dose_update_qualification/VERIFICATION.json').read_text())
drift = [name for name, h in old['files'].items()
         if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != h]
receipt = dict(utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
    executable=sys.executable, platform=platform.platform(), numpy=np.__version__, pyarrow=pyarrow.__version__,
    git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    seed='No stochastic fitting; deterministic identity hash and folds; synthetic test seed 5023',
    blas_threads_requested=2, gpu=False, fitting_model_api_calls=0,
    prior_seal_files=len(old['files']), prior_seal_drift=drift,
    relative_mse_worsening=m['single_plus_anchor']['mse']/m['single_only']['mse']-1,
    relative_regret_reduction=1-m['single_plus_anchor']['regret']/m['single_only']['regret'],
    single_vs_mean_relative_mse_reduction=1-m['single_only']['mse']/m['source_mean']['mse'],
    selected_counts={arm: dict(collections.Counter(str(t['selected']) for t in trials if t['arm']==arm))
                     for arm in ['single_only', 'single_plus_anchor']})
(OUT / 'ENVIRONMENT_AND_COST.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
