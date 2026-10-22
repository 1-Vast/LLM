"""Verify exact phase evidence; preserve predecessors without rerunning assays."""
import ast,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from preserve import verify
ROOT=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/caf_mechanics_qualification'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def read(name):return json.loads((P/name).read_text(encoding='utf-8'))

def main():
    checks={};statuses=Counter();receipts=[]
    for path in sorted((P/'sources').glob('*.http.json')):
        row=json.loads(path.read_text());body=path.with_name(path.name.removesuffix('.http.json')+'.body')
        statuses[str(row.get('status',row.get('error_type')))]+=1
        checks['source_'+path.stem]=sha(body)==row['sha256'] and body.stat().st_size==row['bytes'] if 'sha256' in row else row['outcome']=='FAILED_RETAINED' and not body.exists()
        receipts.append(path.relative_to(P).as_posix())
    for name in ['openalex_indexed_pdf','openalex_indexed_grobid']:
        row=read('sources/'+name+'.http.json')
        checks['key_required_not_fulltext_'+name]=row['status']==401 and 'api key' in (P/'sources'/(name+'.body')).read_text().lower()
    manifest=read('sources/SMALL_ASSET_MANIFEST.json');schema=read('sources/WORKBOOK_SCHEMA_AUDIT.json')
    checks['no_assay_casts']=schema['assay_scalar_casts']==0 and schema['normalization_values_not_inspected']
    checks['five_exact_files']=len(manifest['files'])==5 and sum(x['size'] for x in manifest['files'])==62647
    for row in manifest['files']:
        raw=(P/'sources'/(row['name']+'.body')).read_bytes()
        checks['release_'+row['name']]=len(raw)==row['size'] and 'md5:'+hashlib.md5(raw).hexdigest()==row['checksum']
    initial=read('INDEPENDENT_RESPONSE_SEAL.json');cross=read('CROSS_INPUT_SEAL.json');usage=Counter();api=[]
    for role in ['mechanism','skeptic','data','mechanism_cross','skeptic_cross','data_cross']:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text());prompt=(d/'EXACT_REQUEST.txt').read_text(encoding='utf-8')
        checks['api_'+role]=r['status']=='VALID_RESPONSE' and r['finish_reason']=='stop' and bool((d/'RESPONSE.md').read_text(encoding='utf-8').strip()) and not r['generated_code_executed']
        checks['request_'+role]=sha(d/'EXACT_REQUEST.txt')==r['request_raw_sha256'] and hashlib.sha256(prompt.encode()).hexdigest()==r['request_logical_sha256'] and prompt==(d/'PROMPT.md').read_text(encoding='utf-8')
        if role in initial['roles']:
            checks['initial_seal_'+role]=sha(d/'RESPONSE.md')==initial['roles'][role]['response_sha256'] and sha(d/'RECEIPT.json')==initial['roles'][role]['receipt_sha256']
        else:
            checks['prior_to_cross_'+role]=initial['utc']<cross['utc']<r['utc_started']
            checks['cross_prompt_'+role]=sha(d/'PROMPT.md')==cross['prompts'][role]
            checks['exact_peer_exchange_'+role]=all((P/f'api_reviews/{peer}/RESPONSE.md').read_text(encoding='utf-8') in prompt for peer in ['mechanism','skeptic','data'])
        usage.update(r['usage']);api.append(dict(role=role,response_sha256=sha(d/'RESPONSE.md'),receipt_sha256=sha(d/'RECEIPT.json')))
    for name,h in cross['inputs'].items():checks['cross_input_'+name]=sha(P/name)==h
    input_seal=read('API_INPUT_SEAL.json')
    checks['original_packet_bound']=hashlib.sha256((P/'RESEARCH_PACKET.md').read_text(encoding='utf-8').encode()).hexdigest()==input_seal['packet_logical_sha256']
    audit=read('MECHANISM_AUDIT_RESULT.json')
    checks['six_frozen_math_checks']=audit['status']=='PASS' and len(audit['checks'])==6 and all(audit['checks'].values()) and audit['code_sha256']==sha(C/'audit_mechanisms.py')
    checks['five_exact_rewrites']=len(audit['agfr_identities'])==5 and all(x['equal'] for x in audit['agfr_identities'])
    checks['45_bounded_grid_cases']=len(audit['corrected_grid'])==45 and all(x['bounded'] for x in audit['corrected_grid'])
    for name in ['DECISION.md','DEBATE_DISPOSITION.md','CONTINUATION_WORK.md']:checks['decision_record_'+name]=(P/name).is_file()
    for code in sorted(C.glob('*.py')):
        ast.parse(code.read_text(encoding='utf-8'),filename=str(code));checks['syntax_'+code.name]=True
    preservation=verify()
    with (P/'FINAL_PRESERVATION.json').open('x',encoding='utf-8') as f:json.dump(preservation,f,indent=2)
    checks['all_5778_prior_files_unchanged']=preservation['passed'] and len(preservation['checks'])==5778
    result=dict(utc=datetime.now(timezone.utc).isoformat(),passed=all(checks.values()),checks=checks,source_receipt_count=len(receipts),source_http_or_exception_counts=dict(statuses),api=dict(logical_requests=len(api),transport_attempts='NOT_EXPOSED',usage=dict(usage),responses=api,independence_scope='SEPARATE_CONTEXTS_SAME_PROVIDER_NOT_HETEROGENEOUS_REPLICATION'),prior_files_verified=len(preservation['checks']),biological_fits=0,adaptive_assay_queries=0,assay_scalar_casts=0,full_goal='ACTIVE_NOT_ACHIEVED',decision='NO_CANDIDATE_PROMOTED_STOP_CURRENT_CONFIGURATION')
    with (P/'FINAL_INTEGRITY.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    assert result['passed'],[k for k,v in checks.items() if not v]
    files=[dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)) for base in [P,C] for path in sorted(base.rglob('*')) if path.is_file()]
    with (P/'FINAL_FILE_INVENTORY.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),inventory_excludes_itself=True,files=files),f,indent=2)
    print(json.dumps(dict(passed=result['passed'],checks=len(checks),sources=len(receipts),statuses=dict(statuses),api_requests=len(api),tokens=usage['total_tokens'],prior_files=len(preservation['checks']),phase_files=len(files))))

if __name__=='__main__':main()
