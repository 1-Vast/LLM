"""Bind actual source/review/audit artifacts and verify finalized predecessors."""
import ast,hashlib,io,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import zipfile
from preserve import verify
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/post_rna_mechanism_renewal';C=Path(__file__).resolve().parent

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def read(name):return json.loads((P/name).read_text(encoding='utf-8'))

def main():
    checks={};source_status=Counter();receipts=[]
    for path in sorted(P.glob('*/**/*.http.json')):
        row=json.loads(path.read_text(encoding='utf-8'));body=path.with_name(path.name.removesuffix('.http.json')+'.body')
        label=path.relative_to(P).as_posix();source_status[str(row.get('status',row.get('error_type')))]+=1
        if 'sha256' in row:
            checks['source_body_'+label]=body.is_file() and sha(body)==row['sha256'] and body.stat().st_size==row['bytes']
        else:checks['source_failure_'+label]=row['outcome']=='FAILED_RETAINED' and not body.exists()
        receipts.append(label)
    # The initial malformed DOI routes returned HTTP200 with failed semantic status.
    semantic_errors=[]
    for name in ['labcompass_author_metadata','resolution_author_metadata']:
        row=json.loads((P/'primary'/(name+'.body')).read_text())
        checks['retained_bad_metadata_'+name]=not row['collection'] and row['messages'][0]['status']=='non-numeric value supplied'
        semantic_errors.append(name)
    for name in ['labcompass_corrected_doi_metadata','resolution_corrected_doi_metadata','caf_mechanics_author_metadata']:
        row=json.loads((P/'primary'/(name+'.body')).read_text())
        checks['corrected_metadata_'+name]=row['messages'][0]['status']=='ok' and len(row['collection'])==1
    original=read('INDEPENDENT_RESPONSE_SEAL.json');cross=read('CROSS_INPUT_SEAL.json');usage=Counter();api_rows=[]
    for role in ['constructive','skeptic','application','constructive_cross','skeptic_cross','application_cross']:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text());prompt=(d/'EXACT_REQUEST.txt').read_text(encoding='utf-8')
        checks['api_'+role]=r['status']=='VALID_RESPONSE' and r['finish_reason']=='stop' and bool((d/'RESPONSE.md').read_text(encoding='utf-8').strip()) and not r['generated_code_executed']
        checks['request_'+role]=sha(d/'EXACT_REQUEST.txt')==r['request_raw_sha256'] and hashlib.sha256(prompt.encode()).hexdigest()==r['request_logical_utf8_sha256'] and prompt==(d/'PROMPT.md').read_text(encoding='utf-8')
        if role in original['roles']:
            checks['independent_seal_'+role]=sha(d/'RESPONSE.md')==original['roles'][role]['response_sha256'] and sha(d/'RECEIPT.json')==original['roles'][role]['receipt_sha256']
        else:checks['seal_before_cross_'+role]=original['utc']<r['utc_started']
        usage.update(r['usage']);api_rows.append(dict(role=role,response_sha256=sha(d/'RESPONSE.md'),receipt_sha256=sha(d/'RECEIPT.json')))
    for name,h in cross['inputs'].items():checks['cross_bound_'+name]=sha(P/name)==h
    inputs=read('PROPOSAL_INPUT_SEAL.json')
    checks['proposal_source_packet_bound']=sha(P/'SOURCE_READING.md')==inputs['evidence_sha256']
    audit=read('CHEAP_AUDIT_RESULT.json')
    checks['nine_mathematical_checks_retained']=audit['status']=='PASS' and len(audit['checks'])==9 and all(audit['checks'].values()) and sha(C/'cheap_audit.py')==audit['code_sha256']
    for code in sorted(C.glob('*.py')):
        ast.parse(code.read_text(encoding='utf-8'),filename=str(code));checks['syntax_'+code.name]=True
    z=zipfile.ZipFile(P/'primary/caf_rest_supplementary_bundle.body')
    inspection=read('primary/CAF_SUPPLEMENT_INITIAL_INSPECTION.json')
    checks['supplement_bundle_valid']=set(z.namelist())=={r['name'] for r in inspection['inventory']} and sha(P/'primary/caf_rest_supplementary_bundle.body')==inspection['bundle_sha256']
    docraw=z.read(inspection['document']['member']);tabraw=z.read(inspection['sample_table']['member'])
    checks['supplement_selected_members_bound']=hashlib.sha256(docraw).hexdigest()==inspection['document']['sha256'] and hashlib.sha256(tabraw).hexdigest()==inspection['sample_table']['sha256']
    images=read('primary/caf_figures/PROVENANCE.json')
    with zipfile.ZipFile(io.BytesIO(docraw)) as doc:
        for image in images['entries']:
            raw=doc.read(image['source_member']) if image['source_member'].startswith('word/') else z.read(image['source_member'])
            checks['source_image_'+image['output']]=hashlib.sha256(raw).hexdigest()==image['source_sha256'] and (P/'primary/caf_figures'/image['output']).is_file()
    z.close()
    preservation=verify()
    with (P/'FINAL_PRESERVATION.json').open('x',encoding='utf-8') as f:json.dump(preservation,f,indent=2)
    checks['all_finalized_predecessors_unchanged']=preservation['passed'] and len(preservation['checks'])==5613
    result=dict(utc=datetime.now(timezone.utc).isoformat(),passed=all(checks.values()),checks=checks,source_receipt_count=len(receipts),source_http_or_exception_counts=dict(source_status),retained_http200_content_errors=semantic_errors,api=dict(logical_requests=len(api_rows),transport_attempts='NOT_EXPOSED',usage=dict(usage),responses=api_rows),prior_files_verified=len(preservation['checks']),biological_fits=0,adaptive_assay_queries=0,public_figures_designer_exposed=True,model_target_digitization=False,full_goal='ACTIVE_NOT_ACHIEVED',decision='NO_CANDIDATE_PROMOTED')
    with (P/'FINAL_INTEGRITY.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    assert result['passed'],[k for k,v in checks.items() if not v]
    files=[]
    for base in [P,C]:
        for path in sorted(base.rglob('*')):
            if path.is_file():files.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    with (P/'FINAL_FILE_INVENTORY.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),inventory_excludes_itself=True,files=files),f,indent=2)
    print(json.dumps(dict(passed=result['passed'],checks=len(checks),sources=len(receipts),source_status=dict(source_status),api_requests=len(api_rows),tokens=usage['total_tokens'],prior_files=len(preservation['checks']),phase_files=len(files))))

if __name__=='__main__':main()
