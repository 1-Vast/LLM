"""Finalize immutable pilot evidence after root review; no training or new targets."""
import ast,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
import psutil
from preserve import verify
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(name):return json.loads((P/name).read_text(encoding='utf-8'))
def write(name,value):
    with (P/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)

def main():
    checks=[]
    def check(name,passed):checks.append(dict(name=name,passed=bool(passed)))
    prior=verify();write('FINAL_PRESERVATION.json',prior)
    check('1426_earlier_finalized_files_unchanged',prior['passed'] and len(prior['checks'])==1426)
    for name,digest in read('NUMERICAL_EXECUTION_FREEZE.json')['artifacts_sha256'].items():check('execution_freeze:'+name,sha(ROOT/name)==digest)
    tests=read('FINAL_NUMERICAL_TEST_RECEIPT.json')
    check('original_32_synthetic_tests_passed_not_reexecuted',tests['all_passed'] and tests['test_count']==32 and tests['returncode']==0)
    for name,digest in tests['code_sha256'].items():check('tested_code:'+name,sha(ROOT/name)==digest)
    seal=read('PREDICTION_SEAL.json')
    for name,digest in dict(seal['files'],**seal['code']).items():check('sealed:'+name,sha(ROOT/name)==digest)
    reference=read('REFERENCE_ASSEMBLY_AUDIT.json');result=read('RNA_PILOT_RESULT.json');audit=read('ROOT_RESULT_AUDIT.json')
    check('independent_decimal_assembly',reference['status']=='PASS' and reference['state_scalar_comparisons']==3007125 and reference['function_mean_sd_comparisons']==316)
    check('real_budget_4336_1552',read('NUMERICAL_RECEIPT.json')['operations']['coefficient_fits']==4336 and read('NUMERICAL_RECEIPT.json')['pipeline_evaluations']==1552)
    check('root_audit_binds_actual_outputs',all(sha(P/n)==d for n,d in audit['files_sha256'].items()))
    check('candidate_identity_and_original_stop',audit['candidate']=='rho_0' and result['decision']=='STOP_THIS_CONFIGURATION_EXPANSION' and not result['useful_gain_gate'])
    check('no_later_or_development_high_rna',not result['later_opened'] and result['later_function_casts']==0 and not result['development_high_rna_opened'])
    check('development_high_function_only_scored_after_seal',result['development_high_function_casts']==14 and reference['development_high_function_casts']==0 and result['prediction_seal_sha256']==sha(P/'PREDICTION_SEAL.json'))
    check('all172_and_pilot_terminal_success',read('ARRIVAL_PROCESSING_TERMINAL.json')['status']=='ALL_172_COMPLETE' and read('AUTONOMOUS_PILOT_TERMINAL.json')['status']=='PILOT_COMPLETE_REQUIRES_RESULT_REVIEW')
    check('actual_post_result_exchange_complete',read('POST_RESULT_REVIEW_TERMINAL.json')['status']=='REVIEWS_AND_ACTUAL_CROSS_REPLIES_COMPLETE_ROOT_DECISION_PENDING')
    for name,digest in read('NEXT_MECHANISM_REVIEW_EVIDENCE.json')['files_sha256'].items():
        path=P/'RESEARCH_REPORT_AS_REVIEWED.md' if name=='research/REPORT.md' else ROOT/name
        check('direction_review_original_context:'+name,sha(path)==digest)
    api=[]
    for path in sorted((P/'api_reviews').glob('*/RECEIPT.json')):
        r=json.loads(path.read_text());response=path.with_name('RESPONSE.md')
        api.append(dict(role=path.parent.name,status=r['status'],finish_reason=r.get('finish_reason'),
                        nonempty=response.exists() and bool(response.read_text(encoding='utf-8').strip()),usage=r.get('usage',{})))
    check('all20_actual_api_call_receipts',len(api)==20)
    for role in ['post_result_support','post_result_skeptic','post_result_support_cross','post_result_skeptic_cross',
                 'post_result_identity_support','post_result_identity_skeptic']:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text())
        check('completed_result_review:'+role,r['status']=='RESPONSE_RETAINED' and r['finish_reason']=='stop' and bool((d/'RESPONSE.md').read_text().strip()))
        check('logical_request:'+role,hashlib.sha256((d/'EXACT_REQUEST.txt').read_text(encoding='utf-8').encode()).hexdigest()==r['request_sha256'])
    for path in C.rglob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'))
    active=[]
    for proc in psutil.process_iter(['pid','name','cmdline']):
        try:
            if (proc.info['name'] or '').lower()=='python.exe' and any(s in ' '.join(proc.info['cmdline'] or []) for s in ['rna_archive_acquire.py','process_arrivals.py','run_when_ready.py','reference_assembly.py','run_pilot.py','post_result_reviews.py']):active.append(proc.info)
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue
    check('no_pilot_or_review_job_left_running',not active)
    diff=subprocess.run(['git','diff','--check','--',str(C.relative_to(ROOT)),str(P.relative_to(ROOT)),'research/REPORT.md','log/README.md'],cwd=ROOT,capture_output=True,text=True)
    check('scoped_diff_check',diff.returncode==0)
    final=dict(utc=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in checks),checks=checks,
               earlier_files=1426,full_goal='ACTIVE_NOT_ACHIEVED',phase_decision=result['decision'],api=api,
               api_calls=len(api),api_tokens=sum(r['usage'].get('total_tokens',0) for r in api),
               empty_or_incomplete_reviews=[r['role'] for r in api if not r['nonempty'] or r['finish_reason']!='stop'],
               root_decision_sha256=sha(P/'RESULT_REVIEW_DECISION.md'),active_jobs=active,
               review_context_snapshot={'research/REPORT.md':'log/20261022/tggates_rna_feedback_pilot/RESEARCH_REPORT_AS_REVIEWED.md'},
               diff_stdout=diff.stdout,diff_stderr=diff.stderr)
    write('FINAL_INTEGRITY.json',final)
    if not final['passed']:raise RuntimeError('Integrity failure retained; inspect failed checks before finalization')
    paths=sorted(p for directory in [P,C] for p in directory.rglob('*') if p.is_file() and p.name!='FINAL_FILE_INVENTORY.json')
    write('FINAL_FILE_INVENTORY.json',dict(utc=datetime.now(timezone.utc).isoformat(),files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in paths]))
    print(json.dumps(dict(passed=True,checks=len(checks),earlier_files=1426,phase_files=len(paths),api_calls=len(api),api_tokens=final['api_tokens'],decision=result['decision'],full_goal=final['full_goal'])))

if __name__=='__main__':main()
