"""Comparison/evaluation of immutable predictions only; contains no fitting code."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
P=Path(__file__).resolve().parent; B=P.parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
ind=load(P/'independent_predictions.json'); roles=load(P/'roles_reconstructed.json'); co=load(B/'predictions_role_isolated.json'); result=load(B/'results.json'); audit=load(B/'input_role_audit.json')
methods=['scalar_ridge','full_ridge','full_rbf','partner_mean','source_copy']
raw=[s.split() for s in (B.parent/'2026-10-28-agent-a-matched-signal-function/sources/q1_pertbio_data.txt').read_text().splitlines() if s.strip()]
rows=[]; groups=[]; selections=[]; role_checks=[]; constant_checks=[]
def check(category,key,x,y):
 a=np.asarray(x); b=np.asarray(y)
 diff=float(np.max(np.abs(a-b))) if a.size else 0.
 ok=bool(np.allclose(a,b,atol=1e-10,rtol=1e-10))
 rows.append({'category':category,'key':key,'independent':x,'coordinator':y,'max_abs_difference':diff,'within_numerical_tolerance':ok})
for g,rg,cg,cr,ar in zip(ind['groups'],roles['groups'],co['tasks'],result['groups'],audit['tasks']):
 number=g['group']; contexts=rg['contexts']; truth=np.array([float(raw[c['BC_row']-1][86]) for c in contexts])
 label_match=all(all(c[f'{role}_row']==cc[role] and c[f'{role}_label']==cc[f'{role}_label'] for role in ['C','AC','BC']) and c['partner']==cc['partner'] for c,cc in zip(contexts,cg['records']))
 source=set(rg['allowed_Y_rows']); target=set(rg['withheld_Y_rows']); xr={c[k] for c in contexts for k in ['C_row','AC_row','BC_row']}
 role_checks.append({'group':number,'record_count':len(contexts),'rows_and_labels_exact':label_match,'within_group_source_target_disjoint':not bool(source&target),'whitelist_matches':source==set(ar['source_function_rows']) and target==set(ar['withheld_function_rows_for_this_task']) and xr==set(ar['protein_rows']) and ar['protein_columns_1based']==list(range(1,83)),'checkpoint_matches':rg['checkpoint']==cg['checkpoint'] and rg['checkpoint_column_0based']+1==cg['checkpoint_column_1based']})
 scores={}
 for m in methods:
  for j,(a,b) in enumerate(zip(g['predictions'][m],cg['predictions'][m])):check('prediction',f'{number}/{m}/{j}',a,b)
  residual=np.array(g['predictions'][m])-truth
  scores[m]={'mse':float(np.mean(residual**2)),'mae':float(np.mean(np.abs(residual)))}
  for metric in ['mse','mae']:check('group_loss',f'{number}/{m}/{metric}',scores[m][metric],cr['losses'][m][metric])
  for j,v in enumerate(residual.tolist()):check('residual',f'{number}/{m}/{j}',v,cr['details'][j]['residuals'][m])
  if m not in g['source_loo']:continue
  for j,e in enumerate(g['source_loo'][m]):
   check('source_loo_mse',f'{number}/{m}/{j}',e['mse'],cg['fits'][m]['source_loo_mse'][j])
   cfg=e['config']; cc=cg['fits'][m]['grid_in_order'][j]
   assert (cfg==cc if m!='full_rbf' else [cfg['ell'],cfg['lambda']]==cc)
  selection=g['selected'][m]; cc=cg['fits'][m]
  config=selection['config']; other=cc['selected_parameter']
  selections.append({'group':number,'model':m,'independent_index':selection['grid_index'],'coordinator_index':cc['selected_index'],'index_exact':selection['grid_index']==cc['selected_index'],'config_exact':config==other if m!='full_rbf' else [config['ell'],config['lambda']]==other})
  diag=g['final_constants'][m]; cd=cc['final_transform']
  constant_checks.append({'group':number,'model':m,'columns_exact':diag['constant_columns_0based']==cd['constant_columns_zero_based_in_model'],'target_offsets_exact':diag['target_shifted_constant_cells']==cd['target_nonconstant_offsets_on_constant_columns']})
 s=scores['scalar_ridge']['mse']; a=min(scores[m]['mse'] for m in ['partner_mean','source_copy']); f=min(scores[m]['mse'] for m in ['full_ridge','full_rbf'])
 decision='scalar_strict_best' if all(s<scores[m]['mse'] for m in methods[1:]) else 'dominated_by_simple_and_full' if s>=a and s>=f else 'mixed_or_tied'
 groups.append({'group':number,'truth':truth.tolist(),'scores':scores,'decision':decision,'source_d_constant':g['source_d_constant'],'target_Y_constant':bool(np.all(truth==truth[0])),'decision_exact':decision==cr['panel_status']})
 for j,v in enumerate(truth.tolist()):check('target_coordinate',f'{number}/{j}',v,cr['details'][j]['actual_target_coordinate'])
summary={}
for name,ids,coname in [('macro',[0,1,2,3],'equal_group_macro'),('exact_name_groups_1_3',[0,2],'exact_name_group_macro')]:
 summary[name]={m:{metric:float(np.mean([groups[j]['scores'][m][metric] for j in ids])) for metric in ['mse','mae']} for m in methods}
 for m in methods:
  for metric in ['mse','mae']:check('macro_loss',f'{name}/{m}/{metric}',summary[name][m][metric],result[coname][m][metric])
decisions=[g['decision'] for g in groups]
if all(d=='scalar_strict_best' for d in decisions) and not any(g['source_d_constant'] or g['target_Y_constant'] for g in groups):overall='retain_configuration_for_independent_test'
elif all(d=='dominated_by_simple_and_full' for d in decisions):overall='stop_this_configuration_on_this_panel'
else:overall='mixed_or_inconclusive'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
indsha=sha(P/'independent_predictions.json'); cosha=sha(B/'predictions_role_isolated.json')
assert indsha==load(P/'prediction_save_receipt.json')['prediction_sha256']
assert cosha==result['predictions_sha256_saved_before_evaluation']
assert ind['script_sha256']==sha(P/'independent_recompute.py')==load(P/'independent_code_freeze.json')['script_sha256']
assert co['script_sha256']==sha(B/'run_checkpoint_prediction.py')
for path,h in ind['input_sha256'].items():assert sha(Path(path))==h
ok=all(r['within_numerical_tolerance'] for r in rows) and all(r['index_exact'] and r['config_exact'] for r in selections) and all(all(v for k,v in r.items() if k not in ['group','record_count']) for r in role_checks) and all(r['columns_exact'] and r['target_offsets_exact'] for r in constant_checks) and all(g['decision_exact'] for g in groups) and overall==result['disposition']
receipt=load(P/'execution_receipt.json'); save=lambda name,obj:(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
save('independent_results_postprocessed.json',{'groups':groups,**summary,'decision':overall,'provenance':'Postprocessing immutable independent predictions after original telemetry failure; zero refits. Target coordinates reparsed after prediction freeze. Original process not rerun.','original_process_returncode':receipt['returncode'],'original_process_peak_working_set_bytes':None,'requested_model':'gpt-6.1-sol/high','effective_model':'unknown'})
save('numerical_comparison.json',{'numerical_reproduction_pass':ok,'overall_verification_pass':False,'resource_gate':'not_verified_original_process_failed_at_memory_telemetry','comparison_tolerance':{'absolute':1e-10,'relative':1e-10,'meaning':'Numerical reproduction only; not biological or practical effect threshold'},'max_abs_difference':max(r['max_abs_difference'] for r in rows),'by_category':{c:{'count':sum(r['category']==c for r in rows),'max_abs_difference':max(r['max_abs_difference'] for r in rows if r['category']==c)} for c in sorted(set(r['category'] for r in rows))},'selected_parameters':selections,'roles':role_checks,'constant_column_diagnostics':constant_checks,'all_values':rows,'independent_prediction_sha256':indsha,'coordinator_prediction_sha256':cosha,'prediction_byte_hashes_equal':indsha==cosha,'hash_note':'Independent schema and metadata differ; matching byte hashes are neither expected nor claimed.','frozen_input_sha_checks':True,'script_sha_checks':True,'decision':overall,'decision_matches':overall==result['disposition'],'postprocessing_completed_utc':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'numerical_reproduction_pass':ok,'max_abs_difference':max(r['max_abs_difference'] for r in rows),'group_decisions':decisions,'decision':overall,'macro':summary['macro'],'compared_values':len(rows),'resource_gate':'not_verified'}))
