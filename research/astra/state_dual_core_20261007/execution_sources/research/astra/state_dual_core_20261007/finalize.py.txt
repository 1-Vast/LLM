"""Archive actual code and summarize receipts without altering frozen results."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def write(name, value):
    with (HERE/name).open('x', encoding='utf-8') as handle:
        json.dump(value,handle,indent=2,allow_nan=False)
        handle.write('\n')


def main():
    world = read('world/inference_resources.json')
    model = read('model_run1/resources.json')
    agent = read('agent/factorial_run1/factorial_summary.json')
    literature = read('verification/literature_resources.json')
    archive = HERE/'execution_sources'
    archive.mkdir(exist_ok=False)
    sources = list(HERE.rglob('*.py'))
    sources += [ROOT/p for p in ['src/virtual_cell/state_adapter.py','src/virtual_cell/state_runner.py',
        'src/virtual_cell/interface.py','src/virtual_cell/biology.py','src/agent/prediction.py',
        'src/agent/case_store.py','src/agent/llm.py']]
    snapshots = {}
    for p in sources:
        target = archive/p.relative_to(ROOT)
        target = target.with_suffix(target.suffix+'.txt')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(p.read_bytes())
        snapshots[str(p.relative_to(ROOT))] = {'sha256':sha(p),'archive':str(target.relative_to(HERE))}
    write('SOURCE_MANIFEST.json',snapshots)
    write('RESOURCE_SUMMARY.json',{
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'STATE':world,'heads':model,
        'head_linear_solves_including_verification':36,
        'agent':{'actual_API_calls':agent['provider_usage']['calls'], 'usage':agent['provider_usage'],
            'actual_billed_USD':None,'actual_billing_status':'provider invoice not available',
            'API_latency_seconds':sum(json.loads(line).get('api_receipt',{}).get('elapsed_seconds',0) for line in (HERE/'agent/factorial_run1/factorial_actions.jsonl').read_text().splitlines()),
            'episode_wall_seconds':agent['local_elapsed_seconds'],
            'peak_memory_bytes':None,'CPU_seconds':None,'resource_limitation':'not instrumented in agent process; never treated as zero'},
        'all_replay_access_units_including_development_drafts_and_offline_reproduction':read('agent/all_replay_resources.json')['all_replay_access_units'],
        'new_public_HTTP_response_bytes':literature['new_downloaded_response_body_bytes'],
        'new_checkpoint_or_experimental_dataset_download_bytes':0,
        'API_network_bytes':None,'API_network_bytes_status':'not instrumented',
        'new_wet_measurements':0,'laboratory_credits':0,
        'total_local_financial_cost_USD':None,'local_financial_cost_status':'electricity/hardware not invoiced or estimated',
        'whole_session_CPU_or_peak_memory':None,
        'timing_scope':'component timers are not summed as whole-session elapsed; imports and development omitted where noted',
    })
    # Scan only credential values privately, never emit them or their hashes.
    from agent.llm import read_dotenv
    secrets = [v.encode() for k,v in read_dotenv(ROOT/'.env').items() if ('KEY' in k or 'TOKEN' in k or 'SECRET' in k) and len(v)>=12]
    text_extensions = {'.py','.txt','.json','.jsonl','.csv','.md','.yaml'}
    checked = 0
    for p in HERE.rglob('*'):
        if p.is_file() and p.suffix.lower() in text_extensions:
            content = p.read_bytes()
            if any(value in content for value in secrets):
                raise ValueError('credential_detected_in_study_artifact')
            checked += 1
    write('ARTIFACT_CHECKS.json',{'credential_scan_passed':True,'text_artifacts_checked':checked,
        'frozen_H1_intact':sha(HERE/'PROTOCOL.json') == read('PROTOCOL_FREEZE.json')['sha256'],
        'frozen_factorial_intact':sha(HERE/'agent/factorial_run1/FACTORIAL_PROTOCOL.json') == read('agent/factorial_run1/FACTORIAL_FREEZE.json')['protocol_sha256'],
        'production_source_changes_in_this_task':False,'git_commit_or_push':False})
    files = {str(p.relative_to(HERE)):{'bytes':p.stat().st_size,'sha256':sha(p)}
        for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'RUN_MANIFEST.json'}
    write('RUN_MANIFEST.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
        'canonical_results':['model_run1','agent/factorial_run1','world'],
        'independent_verification':'verification_complete.json',
        'scientific_status':'exploratory; H1 negative, no meaningful agent or positive interaction benefit',
        'external_assets_manifest':'world/contract.json','code_snapshots':'SOURCE_MANIFEST.json','files':files})
    print(json.dumps({'files_manifested':len(files),'source_snapshots':len(snapshots),'credential_scan':'PASS'}))


if __name__ == '__main__':
    main()
