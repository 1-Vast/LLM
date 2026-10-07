"""Capacity-preserving STATE counterfactual and noise-corrected endpoint study."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
import psutil
from threadpoolctl import threadpool_limits
from research.astra.state_dual_core_20261007.run_models import linear_kernel, predict, group_loss

HERE=Path(__file__).resolve().parent
OLD=HERE.with_name('state_dual_core_20261007')
GRID=[0.,.25,1.]
ENDPOINT='signed_noise_corrected_mean_squared_native_rna_delta'


def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def write(p,v):
    Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def select(base,addition,train,dev,y):
    trials=[]
    for gamma in GRID:
        p=predict(base+gamma*addition,train,y,.1)
        trials.append((float(np.mean((p[dev]-y[dev])**2)),gamma,p))
    error,gamma,p=min(trials,key=lambda t:(t[0],t[1]))
    return p,{'gamma':gamma,'dev_mse':error,'trials':[{'gamma':g,'dev_mse':e} for e,g,_ in trials]}


def comparison(a,b):
    d=np.asarray(a)-np.asarray(b)
    rng=np.random.default_rng(1907)
    samples=d[rng.integers(len(d),size=(2000,len(d)))].mean(1)
    return {'difference':float(d.mean()),'descriptive_95':np.quantile(samples,[.025,.975]).tolist(),'groups':len(d)}


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    t=time.perf_counter(); proc=psutil.Process(); cpu=proc.cpu_times()
    assert sha(HERE/'PROTOCOL.json')==json.loads((HERE/'PROTOCOL_FREEZE.json').read_text())['sha256']
    frame=pd.read_csv(OLD/'world/conditions.csv')
    rep=np.load(HERE/'world/representations.npz')
    observed=np.load(OLD/'world/sealed_outcomes.npz')
    corrected=np.load(HERE/'observations/bias_corrected_observations.npz')
    table=pd.read_csv(HERE/'observations/bias_corrected_observations.csv')
    prior=np.load(OLD/'model_run1/kernels.npz')
    original=np.load(OLD/'model_run1/predictions.npz')
    assert np.array_equal(frame.condition_id,rep['condition_id']) and np.array_equal(frame.condition_id,corrected['condition_id'])
    train=np.flatnonzero(frame.split=='train'); dev=np.flatnonzero(frame.split=='development'); ev=np.flatnonzero(frame.split=='evaluation')
    base=prior['M1']; basal=linear_kernel(rep['basal_mean'][0],train)
    adds={'matched_nonSTATE':basal,'raw32':linear_kernel(rep['raw_delta'][0],train),
          'raw256':linear_kernel(rep['raw_delta'][1],train),
          'paired32':linear_kernel(rep['counterfactual_delta'][0],train),
          'paired256':linear_kernel(rep['counterfactual_delta'][1],train),
          'permuted256':linear_kernel(rep['counterfactual_delta'][1][prior['permutation']],train)}
    y=observed['observed_delta'].astype(float)
    vector={'M1':predict(base,train,y,.1),'basal_only':predict(prior['basal_only'],train,y,.1),'no_change':np.zeros_like(y)}
    assert np.array_equal(vector['M1'],original['M1'])
    choices={}; losses={}; count_solves=2
    with threadpool_limits(limits=2):
        for name,add in adds.items():
            p,choice=select(base,add,train,dev,y); count_solves+=3
            vector[name]=p; choices[name]=choice
            # Calibration/evaluation poison never enters learned predictions.
            poisoned=y.copy();poisoned[np.flatnonzero(~frame.split.isin(['train','development']))]=1e8
            assert np.array_equal(p,predict(base+choice['gamma']*add,train,poisoned,.1));count_solves+=1
        for name,p in vector.items():losses[name]=group_loss(frame,y,p,ev).to_numpy()
        primary={name:comparison(losses['paired256'],losses[name]) for name in ['matched_nonSTATE','basal_only']}
        vectorsummary={'methods':{name:{'evaluation_group_mse':float(v.mean()),'gamma':choices.get(name,{}).get('gamma')} for name,v in losses.items()},
            'primary':primary,'success':all(c['descriptive_95'][1]<0 for c in primary.values()),
            'zero_gamma_exact_original_M1':True,'selection':choices}
        np.savez_compressed(out/'vector_predictions.npz',**vector,condition_id=frame.condition_id.to_numpy(dtype=str),observed=y)
        write(out/'vector_metrics.json',vectorsummary)
        # Scalar predictions are fitted to the corrected quantities, not relabeled raw RMS.
        role_summaries={}; role_predictions={}; exported=[]
        for role in ['full','technical_validation','screen']:
            subset=table[table.role==role].copy().reset_index(drop=True)
            index={x:i for i,x in enumerate(frame.condition_id)}
            ix=np.array([index[x] for x in subset.condition_id]); n=len(ix)
            tr=np.flatnonzero(subset.split=='train'); dv=np.flatnonzero(subset.split=='development')
            ca=np.flatnonzero(subset.split=='calibration'); te=np.flatnonzero(subset.split=='evaluation')
            target=subset.signed_effect.to_numpy()
            # Source counts known from deposited source metadata, not proposed wet experiments.
            counts=np.stack([1/subset.treated_n.to_numpy(),1/subset.control_n.to_numpy()],axis=1)
            kcount=linear_kernel(counts,tr)
            dose=(subset.dose_uM.to_numpy()[:,None]==subset.dose_uM.to_numpy()[None,:]).astype(float)
            kb=base[np.ix_(ix,ix)]
            preds={'zero':np.zeros(n),'training_mean':np.full(n,target[tr].mean()),
                'count_only':predict((kcount+dose)/2,tr,target,.1),
                'basal_only':predict(prior['basal_only'][np.ix_(ix,ix)],tr,target,.1)};count_solves+=2
            selection={}
            for name,addition in [('matched_nonSTATE',basal),('paired256',adds['paired256'])]:
                if role=='screen':
                    gamma=role_summaries['technical_validation']['selection'][name]['gamma']
                    preds[name]=predict(kb+gamma*addition[np.ix_(ix,ix)],tr,target,.1);count_solves+=1
                    selection[name]={'gamma':gamma,'basis':'same gamma as development-selected validation head'}
                else:
                    preds[name],selection[name]=select(kb,addition[np.ix_(ix,ix)],tr,dv,target);count_solves+=3
            # A common development-selected gamma and reference family across technical roles.
            reference=(role_summaries['technical_validation']['reference_selected_on_development'] if role=='screen' else
                min([k for k in preds if k!='paired256'],key=lambda k:(np.mean((preds[k][dv]-target[dv])**2),k)))
            stats={}
            for name,p in preds.items():
                residual=np.abs(p[ca]-target[ca]);rank=min(len(residual),int(np.ceil((len(residual)+1)*.8)))
                # Full endpoint pools3doses pergroup; simultaneous max residual before quantile.
                if role=='full':
                    residual=pd.DataFrame({'drug':subset.iloc[ca].chemical_group.to_numpy(),'r':residual}).groupby('drug').r.max().to_numpy()
                    rank=min(len(residual),int(np.ceil((len(residual)+1)*.8)))
                q=float(np.sort(residual)[rank-1])
                stats[name]={'development_mse':float(np.mean((p[dv]-target[dv])**2)),
                    'evaluation_mse':float(np.mean((p[te]-target[te])**2)),
                    'evaluation_mae':float(np.mean(np.abs(p[te]-target[te]))),
                    'interval_halfwidth80':q,'interval_coverage':float(np.mean(np.abs(p[te]-target[te])<=q)),
                    'positive_lower_bounds':int(np.sum(p[te]-q>0)),
                    'negative_observed':int(np.sum(target[te]<0)),
                    'gamma':selection.get(name,{}).get('gamma')}
            per_row=pd.DataFrame({'group':subset.iloc[te].chemical_group.to_numpy(),
                'state':(preds['paired256'][te]-target[te])**2,'reference':(preds[reference][te]-target[te])**2}).groupby('group').mean()
            role_summaries[role]={'methods':stats,'reference_selected_on_development':reference,'selection':selection,
                'STATE_minus_reference_mse':comparison(per_row.state.to_numpy(),per_row.reference.to_numpy())}
            for k,p in preds.items():role_predictions[role+'__'+k]=p
            role_predictions[role+'__observed']=target
            role_predictions[role+'__condition_id']=subset.condition_id.to_numpy(dtype=str)
            if role!='full':
                for i,row in subset.iterrows():
                    item=row.to_dict(); item['original_condition_id']=item['condition_id']; item['condition_id']+='-'+role
                    item.update(response_role=role,observed_value=float(target[i]),endpoint=ENDPOINT,
                        reference_prediction=float(preds[reference][i]),state_prediction=float(preds['paired256'][i]),
                        state_representation_active=bool(selection['paired256']['gamma']>0),state_gamma=selection['paired256']['gamma'])
                    # Never put observed sampling variances in policy-visible covariates.
                    exported.append({k:v for k,v in item.items() if k not in ['signed_effect','raw_squared_response','treated_mean_gene_variance','control_mean_gene_variance','treated_noise_term','control_noise_term']})
        np.savez_compressed(out/'scalar_predictions.npz',**role_predictions)
        write(out/'scalar_metrics.json',role_summaries)
        provenance={str(p):sha(p) for p in [HERE/'PROTOCOL.json',HERE/'world/representations.npz',HERE/'observations/ENDPOINT_PROTOCOL.json',out/'vector_predictions.npz',out/'scalar_predictions.npz']}
        identity=hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest()
        result=pd.DataFrame(exported);result['model_provenance_sha256']=identity
        result.to_csv(out/'decision_records.csv',index=False);write(out/'model_provenance.json',provenance)
    c1=proc.cpu_times()
    write(out/'resources.json',{'elapsed_seconds':time.perf_counter()-t,'cpu_seconds':c1.user+c1.system-cpu.user-cpu.system,
        'peak_process_working_set_bytes':proc.memory_info().peak_wset,'linear_solves':count_solves,'API_calls':0,'downloaded_bytes':0,
        'laboratory_credits':0,'actual_billed_API_USD':0,'local_financial_cost_USD':None,'source_sha256':sha(__file__)})
    write(out/'manifest.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps({'world_primary':primary,'world_success':vectorsummary['success'],'corrected_roles':{k:{'reference':v['reference_selected_on_development'],'STATE_minus_reference':v['STATE_minus_reference_mse']} for k,v in role_summaries.items()}}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
