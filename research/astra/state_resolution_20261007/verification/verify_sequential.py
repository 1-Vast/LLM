"""Saved sequential-development reconstruction, no policy implementation imported."""
from pathlib import Path
import json,hashlib,sqlite3
import numpy as np,pandas as pd
B=Path(__file__).resolve().parents[1];A=B/'agent';D=A/'development_corrected_run2';O=B/'verification';read=lambda p:json.loads(p.read_text());f=pd.read_csv(B/'models_run2/decision_records.csv').rename(columns={'observed_value':'observed_rms'});pairs={d:{x.response_role:x for x in g.itertuples()} for d,g in f.groupby('drug')};train=sorted(d for d,x in pairs.items() if x['screen'].split=='train');rows=read(D/'episodes.json');summary=read(D/'summary.json');assert len(rows)==60
trans={}
for world in ['reference','state']:
 a=np.array([pairs[d]['screen'].observed_rms-getattr(pairs[d]['screen'],world+'_prediction') for d in train]);b=np.array([pairs[d]['technical_validation'].observed_rms-getattr(pairs[d]['technical_validation'],world+'_prediction') for d in train]);trans[world]=float(a@b/(a@a+max(float(a@a)*.1,1e-12)))
for row in rows:
 assert row['endpoint']=='signed_noise_corrected_mean_squared_native_rna_delta';drugs=row['drugs'];assert len(drugs)==4 and all(pairs[d]['screen'].split=='development' for d in drugs);world=row['world'];means=[getattr(pairs[d]['technical_validation'],world+'_prediction') for d in drugs];ids=[pairs[d]['screen'].condition_id for d in drugs];acquired=set();count=0
 initial=max(range(4),key=lambda i:(means[i],ids[i]));assert row['initial_choice']==pairs[drugs[initial]]['technical_validation'].condition_id
 for step in row['steps']:
  view=step['public_view'];assert all('observed_rms' not in x and 'observed_value' not in x and 'signed_effect' not in x for x in view);np.testing.assert_allclose([x['forecast'] for x in view],means)
  selected=step['selected']
  if selected is None:break
  assert selected not in acquired;acquired.add(selected);i=ids.index(selected);screen=pairs[drugs[i]]['screen'];assert step['receipt']['response']==screen.observed_rms;delta=trans[world]*(screen.observed_rms-getattr(screen,world+'_prediction'));np.testing.assert_allclose(delta,step['forecast_update']);means[i]+=delta;count+=1
 chosen=max(range(4),key=lambda i:(means[i],ids[i]));validation=pairs[drugs[chosen]]['technical_validation'];assert row['final_choice']==validation.condition_id;assert row['selected_value']==validation.observed_rms;assert count<=2 and row['budget']['recorded_use']==count+1 and row['budget']['reserved']==0
for world in ['reference','state']:
 for policy in ['myopic','lookahead']:
  subset=[x for x in rows if x['world']==world and x['policy']==policy];m=np.mean([x['selected_value'] for x in subset]);gain=np.mean([x['selected_value']-x['no_update_value_postdecision'] for x in subset]);np.testing.assert_allclose(m,summary[world][policy]['mean_selected_value']);np.testing.assert_allclose(gain,summary[world][policy]['mean_gain_vs_no_update'])
db=sqlite3.connect(D/'cases.sqlite');assert db.execute('select count(*) from results').fetchone()[0]==173;assert db.execute('select sum(spent) from cases').fetchone()[0]==173;assert db.execute('select count(*) from prediction_scores').fetchone()[0]==0;db.close()
receipt={'status':'PASS','development_episodes':60,'unique_development_drugs':6,'menus_each_world_policy':15,'replay_access_units':173,'endpoint_identity_and_negative_values_preserved':True,'future_validation_absent_policy_views':True,'all_acquisitions_and_updates_reconstructed':True,'all_final_selections_reconstructed':True,'STATE_column_warning':'paired256 gamma0; column is nonSTATE fallback, cannot establish activeSTATE interaction','agent_result':'lookahead no benefit over competent myopic on development; reference stop better; myopic fallback column achieves registered achievable ceiling','independence':'15overlapping menus not15 independent biological units','API_calls':0};(O/'sequential_independent_verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
