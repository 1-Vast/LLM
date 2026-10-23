"""Independent Decimal/analytic reconstruction; does not import or run root code."""
from decimal import Decimal as D, getcontext
import json, hashlib
from pathlib import Path
getcontext().prec=70
p=Path('log/20261023/inherited_update_renewal')
f=json.loads((p/'API_CHECK_FREEZE.json').read_text(encoding='utf-8'))
hashes={k:hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in f['files'].items()}
assert all(hashes.values())
r=json.loads((p/'API_CHECK.json').read_text(encoding='utf-8'))
e=D('0.000001'); c=D('0.001')
records=[]
def check(label,node,want):
 a,b=(node['exact'].split('/')+['1'])[:2] if '/' in node['exact'] else (node['exact'],'1')
 got=D(a)/D(b); err=abs(got-want); assert err<D('1e-60')
 records.append({'field':label,'independent':str(want),'absolute_difference':str(err)})
t=r['same_history_toy']
for field in ['proposed','ordinary_rank_one_gaussian']:
 for j,w in enumerate([D(1),D(2)]):check('same_history_toy.'+field+str(j),t[field][j],w)
for j in range(2):check('same_history_toy.uninformed_ls'+str(j),t['uninformed_ls'][j],D(3)/2)
for field in ['proposed_query_error','ordinary_same_history_query_error']:check(field,t[field],D(0))
t=r['coordinate_check']; ident=1/(1+e); physical=c*c/(c*c+e)
for field,w in [('epsilon',e),('physical_scale',c),('identity_query_after_same_feedback',D(1)),('changed_query_after_same_feedback',ident/physical),('difference',ident/physical-1)]:check(field,t[field],w)
for j,w in enumerate([ident,ident]):check('identity_direction'+str(j),t['identity_direction'][j],w)
for j,w in enumerate([physical,ident]):check('changed_physical_direction'+str(j),t['changed_physical_direction'][j],w)
t=r['finite_control_check']; drug=-D(1)/4+D(1)/2; s=drug/(1+e); alpha=drug/s
for field,w in [('history_control_increment',-D(1)/4+(D(1)/2)**2),('history_drug_increment',drug),('direction_second_coordinate',s),('alpha',alpha),('initial_control_jacobian_dot_direction',D(0)),('finite_control_increment',(alpha*s)**2),('final_drug_prediction',alpha*s)]:check(field,t[field],w)
(p/'frontier/RESULT_AUDIT.json').write_text(json.dumps({'status':'PASS','independent_method':'70-digit Decimal analytic reconstruction, root code not imported/run','freeze_hashes':hashes,'checked_values':len(records),'records':records},indent=2),encoding='utf-8')
print(len(records),len(hashes))
