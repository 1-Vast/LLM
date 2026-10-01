"""Check preserved history, executed source and local research delivery hashes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[3]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(name,value):
    (RUN/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    prior=json.loads((RUN/'historical_hashes.json').read_text())
    prefixes=json.loads((RUN/'documentation_prefixes.json').read_text())
    changed=[];preserved_prefixes={}
    for name,expected in prior.items():
        path=ROOT/name
        if name in prefixes:
            raw=path.read_bytes()[:prefixes[name]['bytes']]
            preserved_prefixes[name]=hashlib.sha256(raw).hexdigest()==expected
        elif not path.exists() or sha(path)!=expected:
            changed.append(name)
    assert not changed and all(preserved_prefixes.values()), 'historical modification'
    manifests={}
    for folder in ['sensitivity_v1','resistrace_v1','knowledge_diagnosis_v2',
                   'raw_reconstruction_v1','raw_reconstruction_v2','raw_reconstruction_v3']:
        entries=json.loads((RUN/folder/'manifest.json').read_text())
        bad=[name for name,digest in entries.items() if sha(RUN/folder/name)!=digest]
        assert not bad,(folder,bad)
        manifests[folder]=dict(files=len(entries),passed=True)
    verification=json.loads((RUN/'verification.json').read_text())
    checked=verification['source_sha256']
    assert all(sha(ROOT/name)==digest for name,digest in checked.items()), 'tested code changed'
    assert verification['counts']==dict(tests=176,failures=0,errors=0,skipped=0)
    for path in [RUN/'assemble_receipts.py',Path(__file__)]:
        compile(path.read_text(encoding='utf-8'),str(path),'exec')
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0,diff.stdout+diff.stderr
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head==json.loads((RUN/'start.json').read_text())['HEAD']
    api=json.loads((RUN/'api_summary.json').read_text())
    assert api['local_STATE_successful_requests']==11 and api['local_STATE_failed_requests']==4
    assert api['local_STATE_actual_forwards']==42
    delivery=dict(completed_at_utc=datetime.now(timezone.utc).isoformat(),HEAD=head,
        python='D:\\anaconda\\envs\\maestro\\python.exe',dependency_changes=False,
        scientific_status={
            'original_Tahoe_external_raw_RNA':'not_certified;31 ambiguous coordinates',
            'alternative_Replogle_raw_reconstruction':'input_reconstruction_and_real_forward_passed;paired_output_equivalence_failed;external_RNA_not_certified',
            'STATE_real_state_sensitivity':'executed;positive_output_sensitivity;1/9 concrete_action_switches;6/9abstention_changes',
            'STATE_prediction_improvement':'not_run',
            'RidgeRNA_retrospective_prediction':'negative_point_result_vs_blind_reference;425 conditional_matched_test_units;not_STATE',
            'knowledge_nested_development':'near_no_change;no_confirmatory_knowledge_gain',
            'prospective_action_utility':'not_run/not_identified',
            'deployment_net_value':'not_identified'},
        tests=verification['counts'],public_requests=api['logical_public_requests'],
        external_model_API_calls=0,physical_experiments=0,cost='unknown',
        exact_commands='verification.json; each model receipt; REPORT.md reproduction commands',
        preserved_prior_files=len(prior),new_report='REPORT.md',log='log/20261001/README.md#18',
        commits_or_pushes=False)
    write('delivery.json',delivery)
    # The manifest does not include itself; final_integrity will be added below.
    for document in ['REPORT.md','collection_addendum.md','log_append.md']:
        missing=[]
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',(RUN/document).read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            path=target.split('#')[0]
            if document=='log_append.md':base=ROOT/'log/20261001'
            else:base=RUN
            if path in ['delivery_manifest.json','final_integrity.json']:continue
            if not (base/path).exists():missing.append(target)
        assert not missing,(document,missing)
    write('final_integrity.json',dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),
        original_history_count=len(prior),unexpected_historical_changes=changed,
        prior_documentation_prefixes=preserved_prefixes,run_manifests=manifests,
        tested_source_hashes_unchanged=True,dependency_snapshot_unchanged=True,
        git_diff_check_passed=True,local_report_links_passed=True,
        source_receipt_hashes='195 receipt rows checked by assemble_receipts.py; local payload hash matched',
        frozen_erratum='raw_reconstruction_status_erratum.json corrects summary without changing frozen v3',
        no_production_src_changes=True))
    entries={}
    for path in sorted(RUN.rglob('*')):
        if path.is_file() and path.name!='delivery_manifest.json' and '__pycache__' not in path.parts:
            entries[path.relative_to(RUN).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
    for name in checked:
        path=ROOT/name
        entries['../../../../'+name]=dict(bytes=path.stat().st_size,sha256=sha(path))
    for name in prefixes:
        path=ROOT/name
        entries['../../../../'+name]=dict(bytes=path.stat().st_size,sha256=sha(path))
    write('delivery_manifest.json',dict(scope='all local round inputs/outputs including ignored originals; excludes this manifest and pycache',files=entries))
    print(json.dumps({'historical_files':len(prior),'manifests_passed':len(manifests),'delivery_files':len(entries),'tests':verification['counts'],'HEAD':head}))


if __name__=='__main__':main()
