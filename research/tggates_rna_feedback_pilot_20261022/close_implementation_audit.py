"""Retain root disposition and one exact-code final synthetic verification run."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,value):
    with p.open('x') as f:json.dump(value,f,indent=2)


def main():
    files=[C/n for n in ['linear_models.py','pilot_core.py','prepare_numeric_inputs.py','run_pilot.py','score_pilot.py']]
    originally=json.loads((P/'api_reviews/implementation_skeptic/INPUT_HASHES.json').read_text())
    assert all(sha(p)==originally[p.relative_to(ROOT).as_posix()] for p in files)
    start=time.monotonic()
    result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(C),'-p','test_*.py','-v'],
                          cwd=ROOT,capture_output=True,text=True)
    output=result.stdout+'\n'+result.stderr
    with (P/'FINAL_NUMERICAL_TEST_OUTPUT.log').open('x',encoding='utf-8') as f:f.write(output)
    count=re.search(r'Ran (\d+) tests?',output)
    passed=result.returncode==0 and count is not None and int(count[1])==32 and '\nOK\n' in output
    tests=dict(returncode=result.returncode,all_passed=passed,test_count=int(count[1]) if count else None,
        elapsed_seconds=time.monotonic()-start,synthetic_only=True,
        code_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in files+sorted(C.glob('test_*.py'))})
    write(P/'FINAL_NUMERICAL_TEST_RECEIPT.json',tests)
    assert passed,'Final numerical verification failed; inspect retained output'
    audit=dict(status='CLEARED_FOR_FIXED_NUMERICAL_EXECUTION',not_a_novel_core_clearance=True,
        cleared_code_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in files},
        actual_code_review='api_reviews/implementation_skeptic/RESPONSE.md',
        review_limits='First actual-code audit length-truncated; many non-bugs/self-retractions. '
                      'Follow-up concise resolution retained. No reviewer statement treated as empirical proof.',
        dispositions=[
            dict(claim='rho0 weighting and g derivative incorrect',decision='REJECT_OR_REVIEWER_WITHDRAWAL',
                 evidence='Primal/dual, derivative-versus-explicit-g and SVD sign tests pass; train/query transform is identical.'),
            dict(claim='Final selected families only contain rho0; count4332',decision='REJECT',
                 evidence='Full24/7 synthetic execution of the SAME code reaches4336 coefficient fits and1552 pipelines; '
                          'selected contains all3rho families plus5others. Final main fits31, not27 or followup28.'),
            dict(claim='Must remove fixed_half_mixture from strongest comparator',decision='REJECT_THRESHOLD_RELAXATION',
                 evidence='Predetermined distinct50/50 predictor, no dev labels choose weights; conservative gate retained. '
                          'Reviewer followup agrees no required statistical exclusion; name ordinary should include fixed alternative programs.'),
            dict(claim='No target leakage found in inspected ownership/projection/refit',decision='ACCEPT_WITH_TEST_LIMIT',
                 evidence='HeldoutHigh source+inner sentinels, noRNA measurement ablation, full pipeline with all devHigh NaN. '
                          'This does not establish biological validity or remove historical exposure.')],
        unresolved_scientific_limits=['Predictive advantage unknown until real experiment',
            'Ordinary constrained linear prediction; no distinct algorithm established',
            'N24/dev7 and already-exposed development; no donor or confirmatory generalization',
            'No agent, inheritance, joint benefit or common-start RSI tested'],
        execution_preconditions=['All172whitelist arrays complete','Matched controls and fixed54675coordinates',
            'Input hashes prepared and separate NUMERICAL_EXECUTION_FREEZE','Later opening prohibited'])
    write(P/'IMPLEMENTATION_AUDIT_DISPOSITION.json',audit)
    print(json.dumps(dict(status=audit['status'],synthetic_tests=tests['test_count'],actual_smoke_fits=4336)))

if __name__=='__main__':main()
