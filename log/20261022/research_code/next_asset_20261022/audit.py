"""Verify retained HTTP bodies and Python syntax without rerunning requests."""
from pathlib import Path
import ast
import hashlib
import json

if __name__=='__main__':
    code=Path(__file__).resolve().parent
    out=code.parents[1]/'log/20261022/next_asset'
    checks=[]
    for path in sorted(code.glob('*.py')):
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
        checks.append({'kind':'python_syntax','path':str(path),'pass':True})
    for path in sorted((out/'sources').glob('*.receipt.json')):
        receipt=json.loads(path.read_text(encoding='utf-8'))
        body=path.with_name(path.name.replace('.receipt.json','.body'))
        checks.append({'kind':'http_body_integrity','path':str(body),'pass':body.exists() and len(body.read_bytes())==receipt['bytes'] and hashlib.sha256(body.read_bytes()).hexdigest()==receipt['sha256'],'status':receipt['status']})
    result={'checks':checks,'all_pass':all(x['pass'] for x in checks),'check_count':len(checks),'http_attempts':sum(x['kind']=='http_body_integrity' for x in checks),'assay_scalar_casts':0,'model_fits':0,'api_calls':0}
    (out/'EVIDENCE_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
