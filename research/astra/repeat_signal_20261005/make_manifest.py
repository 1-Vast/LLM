"""Hash final deliverables and package the small reproducible study inputs."""
import datetime,hashlib,importlib.metadata,json,platform,subprocess,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORKSPACE=ROOT.parent
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()
def included(path):
    return path.is_file() and not any(k in path.relative_to(HERE).parts for k in ['assets','__pycache__']) and path.name!='RUN_MANIFEST.json'

def run():
    assert not subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).strip()
    inputs={}
    for name,path in [('jaaks_fitted',ROOT/'research/astra/knowledge_transfer_20261004/assets/jaaks.csv'),('jaaks_raw',HERE/'assets/original_raw.zip'),('depmap_crispr',HERE/'assets/depmap_crispr.csv')]:
        if path.exists():inputs[name]={'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':digest(path),'included_in_archive':False}
    expected={'jaaks_fitted':'1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278','jaaks_raw':'51550262aed5440d3c5f54997cc940f429ff5dcb55e6970179d3500ba7c5f61e','depmap_crispr':'3d8f3ec6dbf2db7ff834b79b508622ec0b226f3518003fe96ecf5a4fcf167e3b'}
    assert all(v['sha256']==expected[k] for k,v in inputs.items())
    files={str(p.relative_to(ROOT)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(HERE.rglob('*')) if included(p)}
    manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'status':'completed_exploratory_no_biological_action_gain','tracked_repository_files_modified':False,'git_commit_or_push':False,'python':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','matplotlib']},'large_source_inputs':inputs,'files':files,'verification':'verification_recovery.json','notebook_validation':'notebook_validation.json','exposure':'All Jaaks outcomes exposed; static comparator post hoc; recovery reruns known outcomes. No Vis outcomes opened.','execution_scope':'Original repeat/raw/RNA computations survived. Biological arms and static control actually retrained/re-evaluated after snapshot loss, matching earlier recorded confirmation results. No production/LLM arm.','cost_scope':'Public downloads and CPU computation; no paid model inference. P2 resource units are measurements, not real plate/time costs.','limitations':['14 target cell lines','one fixed shuffle seed per destructive arm','same existing drug pairs, not novel-pair generalization','bootstrap conditional on fixed history/development/menus','no independent-agent verification','no entire-repository test rerun','no production-loadable model artifact']}
    (HERE/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=WORKSPACE/'MAESTRO_repeat_signal_20261005.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(HERE.rglob('*')):
            if included(p) or p==HERE/'RUN_MANIFEST.json':z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,item in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==item['sha256']
    print(json.dumps({'manifest_files':len(files),'archive_bytes':archive.stat().st_size,'archive_sha256':digest(archive),'all_packaged_hashes_match':True}))

if __name__=='__main__':run()
