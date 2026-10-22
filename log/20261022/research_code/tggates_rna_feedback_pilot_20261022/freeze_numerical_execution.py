"""Authorize only the fully prepared, independently audited fixed numerical run."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from pilot_core import configurations
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    meta=json.loads((P/'numeric_inputs/METADATA.json').read_text())
    assert meta['development_high_function_casts']==0 and meta['later_function_casts']==0
    assert len(meta['source'])==24 and len(meta['development'])==7
    assert sha(P/'numeric_inputs/DATA.npz')==meta['data_sha256']
    audit=json.loads((P/'IMPLEMENTATION_AUDIT_DISPOSITION.json').read_text())
    assert audit['status']=='CLEARED_FOR_FIXED_NUMERICAL_EXECUTION'
    for relative,digest in audit['cleared_code_sha256'].items():assert sha(ROOT/relative)==digest
    tests=json.loads((P/'FINAL_NUMERICAL_TEST_RECEIPT.json').read_text())
    assert tests['returncode']==0 and tests['all_passed'] is True
    for relative,digest in tests['code_sha256'].items():assert sha(ROOT/relative)==digest
    files=[C/name for name in ['linear_models.py','pilot_core.py','prepare_numeric_inputs.py','run_pilot.py','score_pilot.py']]
    files += [P/name for name in ['NUMERICAL_PROTOCOL.md','PREPROCESS_FREEZE_V2.json',
        'numeric_inputs/DATA.npz','numeric_inputs/METADATA.json','IMPLEMENTATION_AUDIT_DISPOSITION.json',
        'FINAL_NUMERICAL_TEST_RECEIPT.json']]
    record=dict(numerical_execution_authorized=True,utc=datetime.now(timezone.utc).isoformat(),
        configurations=sorted(configurations(),key=lambda c:json.dumps(c,sort_keys=True,separators=(',',':'))),
        artifacts_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in files},
        estimator_fit_ceiling=4336,source_pipeline_evaluations=1536,total_pipeline_evaluations=1552,
        distinct_nuisance_training_sets=301,base_packs=602,
        source_groups=24,development_groups=7,later_opening_authorized=False)
    with (P/'NUMERICAL_EXECUTION_FREEZE.json').open('x') as f:json.dump(record,f,indent=2)
    print(json.dumps(dict(status='FROZEN',configurations=len(record['configurations']),fits=4336)))

if __name__=='__main__':main()
