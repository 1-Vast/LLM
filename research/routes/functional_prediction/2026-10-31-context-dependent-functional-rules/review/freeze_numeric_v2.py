"""Freeze executable choices and input identities without reading responses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

EP = Path(__file__).resolve().parent.parent
ROOT = EP.parents[3]
output = EP/'numeric_freeze_v2.json'
assert not output.exists()
files = [EP/name for name in ['protocol_v2.md','experiment_v2.py','launcher_v2.py','check_arithmetic_v2.py',
                             'candidate_freeze_v1.json','development/common_coordinate_candidate_v1.md']]
files += [ROOT/'data/external/conditional_interventions_20261030/egi/15_GI_expt2_counts.txt.gz',
          EP.parent/'2026-10-31-regulatory-functional-dynamics/egi_admission/guide_identity.tsv']
result = {'created_utc':datetime.now(timezone.utc).isoformat(),'python_executable':sys.executable,
          'python_version':platform.python_version(),'scope':'One staged I054.v1 matrix, unexecuted; no target response access',
          'files':{str(path):{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in files}}
assert result['files'][str(files[-2])]['sha256']=='f9f5c85fc81e366709fd5d42f1c3c85388f00ab19624e14ebede53f72e09080b'
assert result['files'][str(files[-1])]['sha256']=='9adbe2671aa6d422f394016677b4f944c9347eacfb8bc6acb07a2b0ba184ea78'
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'freeze':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'python':sys.executable}))
