"""New final checks after additional sources; preserve the earlier audit unchanged."""
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
        r=json.loads(path.read_text(encoding='utf-8'))
        body=path.with_name(path.name.replace('.receipt.json','.body'))
        checks.append({'kind':'http_body_integrity','path':str(body),'status':r['status'],'pass':body.exists() and len(body.read_bytes())==r['bytes'] and hashlib.sha256(body.read_bytes()).hexdigest()==r['sha256']})
    dose=json.loads((out/'sources/CIPA_PHYSICAL_DOSE_MAPPING.json').read_text(encoding='utf-8'))
    checks.append({'kind':'dose_mapping','pass':len(dose['rows'])==28 and all(set(x['dose_code_to_uM_string'])=={'1','2','3','4'} for x in dose['rows'])})
    result={'checks':checks,'all_pass':all(x['pass'] for x in checks),'check_count':len(checks),'http_attempts':sum(x['kind']=='http_body_integrity' for x in checks),'assay_scalar_casts':0,'model_fits':0,'api_calls':0,'earlier_audit_sha256':hashlib.sha256((out/'EVIDENCE_AUDIT.json').read_bytes()).hexdigest(),'scope':'Source-only reviewer completion, not global research goal completion'}
    with (out/'EVIDENCE_ADDENDUM_AUDIT.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
