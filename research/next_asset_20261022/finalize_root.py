"""Bind source qualification and the separate executed conventional C4 screen."""
import ast,hashlib,importlib.util,json,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'log/20261022/next_asset'
BASES=[ROOT/f'{kind}/{name}' for kind,names in [('research',['next_asset_20261022','cardiac_mechanism_review_20261022','strategy_rethink_20261022']),('log/20261022',['next_asset','cardiac_mechanism_review','strategy_rethink'])] for name in names]

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    spec=importlib.util.spec_from_file_location('caf_preserve',ROOT/'research/caf_mechanics_qualification_20261022/preserve.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    prior=module.verify();manifest=ROOT/'log/20261022/caf_mechanics_qualification/FINAL_FILE_INVENTORY.json'
    prior['manifest_sha256'][manifest.relative_to(ROOT).as_posix()]=sha(manifest)
    for row in json.loads(manifest.read_text())['files']:
        path=ROOT/row['path'];prior['checks'].append(dict(path=row['path'],passed=path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256']))
    prior['passed']=prior['passed'] and all(x['passed'] for x in prior['checks'])
    checks={'5902_predecessors_unchanged':prior['passed'] and len(prior['checks'])==5902};counts=Counter()
    for base in BASES:
        for path in sorted(base.rglob('*.py')):
            ast.parse(path.read_text(encoding='utf-8'));checks['syntax_'+path.relative_to(ROOT).as_posix()]=True
        if 'log' not in base.parts:continue
        for path in sorted(base.rglob('*.receipt.json')):
            row=json.loads(path.read_text());body=path.with_name(path.name.removesuffix('.receipt.json')+'.body')
            checks['http_'+path.relative_to(ROOT).as_posix()]=body.is_file() and sha(body)==row['sha256'] and body.stat().st_size==row['bytes']
            counts[str(row['status'])]+=1
    q=ROOT/'log/20261022/strategy_rethink'
    freeze=json.loads((q/'FREEZE.json').read_text())
    for row in freeze['files']:checks['freeze_'+row['path']]=sha(ROOT/row['path'])==row['sha256']
    checks['rkt_input_unchanged']=sha(ROOT/'research/knowledge_transfer_20261012/cache/dev_routes.npz')==freeze['route_input_sha256']
    seal=json.loads((q/'DEPLOYMENT_SEAL.json').read_text())
    checks['deployment_and_source_seal']=sha(q/'DEPLOYMENTS.json')==seal['deployments_sha256'] and sha(q/'SOURCE_LEARNING.json')==seal['source_learning_sha256'] and not seal['terminal_feedback_exposed'] and seal['earlier_full_truth_array_decoded']
    result=json.loads((q/'RESULT.json').read_text());audit=json.loads((q/'INDEPENDENT_RESULT_CHECK.json').read_text())
    checks['conventional_screen_stopped']=result['decision']=='STOP_CURRENT_ARENA_GRAMMAR' and result['new_minus_old']<0 and result['oracle_minus_S0']>0
    checks['independent_decimal_and_trajectories']=audit['status']=='PASS' and audit['decimal_episode_scores']==104 and audit['validated_trajectories']==168 and audit['proposal_counts']==672
    s0=json.loads((q/'S0_FEEDBACK_REPLAY.json').read_text())
    checks['postrun_S0_feedback_replay']=s0['status']=='PASS' and s0['classification']=='POSTRUN_RECOMPUTATION' and s0['matching_deployments']==168 and s0['additional_solver_fits']==8 and not s0['old_outputs_changed'] and not s0['terminal_selected_or_scored'] and s0['audit_code_sha256']==sha(ROOT/'research/strategy_rethink_20261022/audit_s0_feedback.py')
    mapping=json.loads((P/'sources/CIPA_PHYSICAL_DOSE_MAPPING.json').read_text())
    checks['28_drug_112_dose_metadata']=len(mapping['rows'])==28 and all(set(x['dose_code_to_uM_string'])=={'1','2','3','4'} for x in mapping['rows'])
    supplement=json.loads((P/'sources/CIPA_SUPPLEMENT_AUDIT.json').read_text())
    checks['supplement_pdf_bound']=sha(P/'sources/cipa_supplement_tables.pdf')==supplement['selected_sha256']
    with zipfile.ZipFile(P/'sources/cipa_supplement_europepmc.body') as z:
        checks['actual_author_pdf_in_official_zip']=sum(hashlib.sha256(z.read(n)).hexdigest()==supplement['selected_sha256'] for n in z.namelist() if n.endswith('.pdf'))==1
    checks['root_decision_present']=(P/'DECISION.md').is_file() and (q/'RESULT_DECISION.md').is_file()
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    for name,value in [('FINAL_PRESERVATION.json',prior),('FINAL_INTEGRITY.json',dict(utc=datetime.now(timezone.utc).isoformat(),passed=True,checks=checks,source_receipt_status_counts=dict(counts),predecessors_verified=5902,source_and_review_scope='CIPA_QUALIFIED_NO_CORE_PROMOTED',rkt_screen='ORDINARY_C4_ANALOGUE_STOP_CURRENT_GRAMMAR',full_goal='ACTIVE_NOT_ACHIEVED'))]:
        with (P/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
    files=[dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)) for base in BASES for path in sorted(base.rglob('*')) if path.is_file()]
    with (P/'FINAL_FILE_INVENTORY.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),inventory_excludes_itself=True,scope=[b.relative_to(ROOT).as_posix() for b in BASES],files=files),f,indent=2)
    print(json.dumps(dict(passed=True,checks=len(checks),http_counts=dict(counts),prior_files=5902,phase_files=len(files))))

if __name__=='__main__':main()
