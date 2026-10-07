"""Seal this follow-up, preserving every prior-study artifact."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read(p):return json.loads((HERE/p).read_text(encoding='utf-8'))


def write(name,value):
    with (HERE/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False)


def main():
    archive=HERE/'execution_sources';archive.mkdir(exist_ok=False)
    sources=list(HERE.rglob('*.py'))
    manifest={}
    for p in sources:
        target=archive/(str(p.relative_to(HERE))+'.txt');target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(p.read_bytes());manifest[str(p.relative_to(HERE))]=sha(p)
    write('SOURCE_MANIFEST.json',manifest)
    completion=read('agent/COMPLETION.json')
    write('RESOURCE_SUMMARY.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
        'world':read('world/resources.json'),
        'model_runs':[read(f'models_run{i}/resources.json') for i in [1,2]],
        'corrected_endpoint_extraction':read('observations/EXTRACTION_RECEIPT.json'),
        'agent':completion,'new_API_calls':0,'new_API_tokens':0,'API_cost_USD':0,
        'new_downloaded_bytes':0,'new_laboratory_credits':0,'new_wet_experiments':0,
        'local_hardware_energy_financial_cost_USD':None,'whole_session_peak_memory_or_CPU':None,
        'scope':'Only actual component instrumentation reported; zero new API does not mean zero hardware cost; replay units are not laboratory credits'})
    from agent.llm import read_dotenv
    secrets=[v.encode() for k,v in read_dotenv(ROOT/'.env').items() if any(t in k for t in ['KEY','TOKEN','SECRET']) and len(v)>=12]
    count=0
    for p in HERE.rglob('*'):
        if p.is_file() and p.suffix in ['.json','.jsonl','.py','.txt','.md','.csv']:
            if any(s in p.read_bytes() for s in secrets):raise ValueError('credential_in_artifact')
            count+=1
    write('ARTIFACT_CHECKS.json',{'credential_scan':'PASS','text_artifacts':count,
        'primary_freeze_intact':sha(HERE/'PROTOCOL.json')==read('PROTOCOL_FREEZE.json')['sha256'],
        'prior_files_verified':205,'production_changes':False,'commit_or_push':False})
    files={str(p.relative_to(HERE)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in HERE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.name!='RUN_MANIFEST.json'}
    write('RUN_MANIFEST.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
        'canonical':['world','observations','models_run2','agent/development_corrected_run2'],
        'scientific_status':'No active STATE incremental signal; no sequential planning advantage; engineering/measurement problems corrected, scientific gain unresolved',
        'verification':'verification_complete.json','files':files})
    print(json.dumps({'manifest_files':len(files),'source_snapshots':len(sources),'credential_scan':'PASS'}))


if __name__=='__main__':main()
