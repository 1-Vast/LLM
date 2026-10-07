"""Independent decision reconstruction without replay implementation imports."""
from pathlib import Path
import json,hashlib,time,sqlite3
import pandas as pd,numpy as np
B=Path(__file__).resolve().parents[1];A=B/'agent';D=A/'factorial_run1';O=B/'verification';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest();t=time.perf_counter()
protocol=read(D/'FACTORIAL_PROTOCOL.json');assert sha(D/'FACTORIAL_PROTOCOL.json')==read(D/'FACTORIAL_FREEZE.json')['protocol_sha256'];assert sha(A/'technical_screen_bound_records.csv')==protocol['records_sha256']
for name,h in protocol['code_sha256'].items():assert sha(A/name)==h,name
f=pd.read_csv(A/'technical_screen_bound_records.csv');base=pd.read_csv(B/'model_run1/decision_records.csv').set_index('condition_id');offsets=read(A/'technical_screen_bound_records.calibration.json');freeze=read(B/'world/technical_screen_freeze.json');metadata={x['condition_id']:x for x in freeze['rows']}
for path,h in offsets['model_provenance'].items():assert sha(B/path)==h
assert f.model_provenance_sha256.eq(digest(offsets['model_provenance'])).all()
for role in ['screen','technical_validation']:
 ix=f.response_role.eq(role);train=ix&f.split.eq('train');subset=f.loc[ix];b=base.loc[subset.original_condition_id]
 for world,basecol in [('reference','world_reference'),('state','world_state')]:
  trainrows=f.loc[train];off=float((trainrows.observed_rms.to_numpy()-base.loc[trainrows.original_condition_id,basecol].to_numpy()).mean());np.testing.assert_allclose(off,offsets['training_only_endpoint_offsets'][role+':'+world]);np.testing.assert_allclose(f.loc[ix,world+'_prediction'],b[basecol].to_numpy()+off)
 for row in subset.itertuples():assert row.subset_sha256==digest(metadata[row.original_condition_id]['screen_cell_ids' if role=='screen' else 'validation_cell_ids'])
assert f.groupby('chemical_group').split.nunique().eq(1).all();lookup=f.set_index('condition_id');pairs={drug:{row.response_role:row for row in g.itertuples()} for drug,g in f.groupby('drug')};train=sorted(d for d,rows in pairs.items() if rows['screen'].split=='train');evaldrugs=[d for pair in protocol['pairs'] for d in pair];assert len(set(evaldrugs))==12 and all(pairs[d]['screen'].split=='evaluation' for d in evaldrugs)
transfer={}
for world in ['reference','state']:
 low=np.array([pairs[d]['screen'].observed_rms-getattr(pairs[d]['screen'],world+'_prediction') for d in train]);high=np.array([pairs[d]['technical_validation'].observed_rms-getattr(pairs[d]['technical_validation'],world+'_prediction') for d in train]);beta=float(low@high/(low@low+max(float(low@low)*.1,1e-12)));transfer[world]=(beta,low*beta)
logs=[json.loads(x) for x in (D/'factorial_actions.jsonl').read_text().splitlines()];summary=read(D/'factorial_summary.json');assert len(logs)==24;tokens={};api_status={};scored=[]
for row in logs:
 arm=row['arm'];drugs=protocol['pairs'][row['episode']];world=protocol['arms'][arm][0];assert row['drugs']==drugs
 initial=[getattr(pairs[d]['technical_validation'],world+'_prediction') for d in drugs];updates=initial.copy();screenids=[pairs[d]['screen'].condition_id for d in drugs];validids=[pairs[d]['technical_validation'].condition_id for d in drugs];beta,samples=transfer[world]
 before=max(range(2),key=lambda i:(initial[i],screenids[i]));assert validids[before]==row['initial_choice'];actions=row['actions'];assert len(actions)<=2 and actions[-1]['kind']=='confirm';assert len(actions)==row['budget']['recorded_use']<=2
 if len(actions)==2:
  action=actions[0];assert action['kind']=='acquire' and action['condition_id'] in screenids;i=screenids.index(action['condition_id']);lo=pairs[drugs[i]]['screen'];assert action['response']==lo.observed_rms;updates[i]+=beta*(lo.observed_rms-getattr(lo,world+'_prediction'))
 selected=max(range(2),key=lambda i:(updates[i],screenids[i]));assert validids[selected]==row['final_choice'];observed=pairs[drugs[selected]]['technical_validation'].observed_rms;assert abs(observed-row['observed_selected_rms'])<1e-14;assert actions[-1]['condition_id']==validids[selected];np.testing.assert_allclose([v['forecast'] for v in row['policy_view_after_acquisition']],updates)
 assert row['deadline_compliant']==(row['elapsed_seconds']<=120);np.testing.assert_allclose(row['decision_utility'],observed if row['deadline_compliant'] else 0)
 if arm in 'AB':
  name=protocol['deterministic_policy_by_world'][world]
  if name=='sensitivity':expected=max(range(2),key=lambda i:(initial[i],screenids[i]))
  else:
   gains=[float(np.maximum(initial[1-i],initial[i]+samples).mean())-max(initial) for i in range(2)];expected=max(range(2),key=lambda i:(gains[i],screenids[i])) if max(gains)>0 else None
  assert (actions[0]['condition_id'] if len(actions)==2 else None)==(screenids[expected] if expected is not None else None)
 else:
  receipt=row['api_receipt'];view=receipt['request']['candidates'];assert all('observed_rms' not in v and 'response' not in v for v in view);np.testing.assert_allclose([v['forecast'] for v in view],initial);assert row['same_information_equal'] and row['same_information_final_choice']==row['final_choice'];api_status[receipt['status']]=api_status.get(receipt['status'],0)+1
  for key,value in receipt['usage'].items():
   if isinstance(value,(int,float)):tokens[key]=tokens.get(key,0)+value
  if receipt['status']=='accepted':assert receipt['answer']['acquire_condition_id']==(actions[0]['condition_id'] if len(actions)==2 else None)
 scored.append((row['episode'],arm,row['decision_utility']))
values=np.array([[next(v for i,a,v in scored if i==episode and a==arm) for arm in 'ABCD'] for episode in range(6)]);diff=values[:,3]-values[:,2]-values[:,1]+values[:,0];rng=np.random.default_rng(719);ci=np.quantile(diff[rng.integers(6,size=(10000,6))].mean(1),[.025,.975]);np.testing.assert_allclose(diff.mean(),summary['interaction']['estimate']);np.testing.assert_allclose(ci,summary['interaction']['bootstrap_95_interval'])
for i,arm in enumerate('ABCD'):np.testing.assert_allclose(values[:,i].mean(),summary['arms'][arm]['mean_selected_rms'])
for key in ['prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens']:assert tokens[key]==summary['provider_usage'][key]
# Persisted facts: source identities, unique imports, final predictions, no fabricated reliability update.
dbs={}
for area in ['runs','shared_information']:
 db=sqlite3.connect(D/area/'cases.sqlite');db.row_factory=sqlite3.Row;cases=list(db.execute('SELECT * FROM cases'));results=list(db.execute('SELECT * FROM results'));pred=list(db.execute('SELECT * FROM prediction_records'));scores=list(db.execute('SELECT * FROM prediction_scores'))
 assert not scores
 assert sum(x['spent'] for x in cases)==len(results)
 assert len({x['result_id'] for x in results})==len(results)
 for result in results:
  assert result['evidence_kind']=='retrieved_source';cond=json.loads(result['conditions_json']);source=lookup.loc[cond['condition_id']];assert cond['subset_sha256']==source.subset_sha256 and cond['response_role']==source.response_role;assert result['context_identifier']==source.cell and result['time_hours']==source.time_hours;np.testing.assert_allclose(float(json.loads(result['metrics_json'])['native_rna_delta_rms']),source.observed_rms)
 for prediction in pred:
  payload=json.loads(prediction['payload_json']);assert payload['request']['request_id']==prediction['request_id'];assert payload['prediction']['request_id']==prediction['request_id']
 dbs[area]={'cases':len(cases),'results':len(results),'predictions':len(pred),'reliability_scores':len(scores),'spent':sum(x['spent'] for x in cases)};db.close()
receipt={'status':'PASS','episodes':6,'arms':24,'main_replay_access_units':dbs['runs']['spent'],'auxiliary_replay_access_units':dbs['shared_information']['spent'],'api_calls':12,'api_statuses':api_status,'provider_tokens':tokens,'actual_billed_usd':None,'per_arm_mean':dict(zip('ABCD',values.mean(0).tolist())),'optimized_pipeline_interaction':{'estimate':float(diff.mean()),'bootstrap95':ci.tolist()},'database_checks':dbs,'training_only_screen_offsets_rebuilt':True,'same_information_all12_choices_equal':True,'future_validation_outcomes_absent_from_policy_views':True,'condition_subset_and_model_identity_checked':True,'independent_physical_confirmations':0,'limitations':['Main A/B use different development-selected deterministic policies; contrast is optimized-pipeline interaction, not pure fixed-policy world interaction','All evaluation groups are downstream-held-out within one previously exposed cell/source; unknown checkpoint pretraining overlap','Technical screen and validation share control denominator, not biological replicates','Fixed-policy supplement registered during API execution, after evaluation began; must be labeled supplementary exploratory not original preregistration'],'wall_seconds':time.perf_counter()-t};(O/'decision_independent_verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

# Supplementary fixed-policy contrasts, registered mid-run and kept secondary.
fixed=read(D/'fixed_policy_actions.json');fs=read(D/'fixed_policy_summary.json');assert len(fixed)==24
fixed_results={}
for policy in ['sensitivity','empirical_value']:
 matrix=[]
 for world in ['reference','state']:
  rows=[x for x in fixed if x['case_id'].startswith('fixed-'+policy+'-'+world+'-')];rows.sort(key=lambda x:int(x['case_id'].rsplit('-',1)[1]));assert len(rows)==6
  for row in rows:
   np.testing.assert_allclose(row['observed_selected_rms'],lookup.loc[row['final_choice'],'observed_rms']);assert row['budget']['recorded_use']==len(row['actions'])<=2
  matrix.append(np.array([x['observed_selected_rms'] for x in rows]));np.testing.assert_allclose(matrix[-1].mean(),fs[policy]['mean_rms'][world])
 d=matrix[1]-matrix[0];interaction=values[:,3]-values[:,2]-d;np.testing.assert_allclose(d.mean(),fs[policy]['world_effect_fixed_policy']);np.testing.assert_allclose(interaction.mean(),fs[policy]['interaction_fixed_policy']);fixed_results[policy]={'world_effect':float(d.mean()),'interaction':float(interaction.mean())}
db=sqlite3.connect(D/'fixed_policy_runs/cases.sqlite');assert db.execute('select sum(spent) from cases').fetchone()[0]==48;assert db.execute('select count(*) from results').fetchone()[0]==48;assert db.execute('select count(*) from prediction_scores').fetchone()[0]==0;db.close()
(O/'supplement_independent_verification.json').write_text(json.dumps({'status':'PASS','fixed_policy_contrasts':fixed_results,'fixed_replay_access_units':48,'API_calls':0,'main_and_auxiliary_and_fixed_total_access_units':120,'best_fixed_reference_matches_LLM_reference':bool(np.all(matrix[0]==values[:,2])),'registration_status':'during API execution; supplementary exploratory, not original untouched preregistration'},indent=2)+'\n')
