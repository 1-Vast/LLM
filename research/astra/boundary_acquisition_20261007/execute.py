"""Reference-only fitting and cheap charged scalar evidence acquisition replay."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREVIOUS=ROOT/"research/astra/decision_opportunity_20261007"
sys.path.insert(0,str(HERE))
import method
spec=importlib.util.spec_from_file_location('boundary_paid_study',PREVIOUS/'run.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)


def protocol():
    p=json.loads((HERE/'PROTOCOL.json').read_text())
    frozen=json.loads((HERE/'FREEZE.json').read_text())
    if study.digest(HERE/'PROTOCOL.json')!=frozen['protocol_sha256']:
        raise ValueError('Frozen boundary protocol modified')
    for name,sha in p['source_dependencies'].items():
        if study.digest(ROOT/name)!=sha:raise ValueError('Frozen source modified:'+name)
    for name,sha in p['upstream_dependencies'].items():
        if study.digest(ROOT/name)!=sha:raise ValueError('Frozen upstream modified:'+name)
    return p


def parameters(a,keep):
    return study.fit_common_belief(a['train_A'][keep],a['train_B'][keep],
                                 (a['availability_A']&a['availability_B'])[keep])[:3]


def permute_states(state,available,keys):
    shuffled=[];qualified=[];details=[]
    for row,ok in zip(state,available):
        value,detail=study.state_permutation(row[:,None],keys)
        mask,_=study.state_permutation(ok[:,None],keys)
        shuffled.append(value[:,0]);qualified.append(mask[:,0]);details.append(detail)
    return np.array(shuffled),np.array(qualified),details


def save_models(path,models):
    arrays={}
    meta={}
    for name,model in models.items():
        for key in ('centre','scale','coef'):arrays[name+'__'+key]=model[key]
        meta[name]={key:model[key] for key in ('intercept','predicted_centre','floor','design')}
    np.savez_compressed(path/'fitted_models.npz',**arrays)
    study.write(path/'FIT_PARAMETERS.json',meta)


def build(out):
    p=protocol();out=Path(out).resolve()
    if out.exists():raise ValueError('Use a fresh packet directory')
    out.mkdir(parents=True);started=time.perf_counter()
    labels,wells=p['menu']['labels'],p['menu']['wells']
    keys=sorted({(l,plate) for l in labels for plate in wells[l]})
    idx={k:i for i,k in enumerate(keys)}
    ia=np.array([idx[(l,wells[l][0])] for l in labels]);ib=np.array([idx[(l,wells[l][1])] for l in labels])
    weights=np.zeros(2000);coords=[r['coordinate'] for r in p['endpoint']['mapped']]
    weights[coords]=1/len(coords)
    panel=study.wm.Panel(keys);w0=panel.w_precision();m0=panel.apply(w0)
    # Present source identity cannot be inferred from numerical zero.
    stateok=np.zeros((len(panel.files),len(keys)),bool)
    for li,file in enumerate(panel.files):
        s=study.wm.load_state(file)
        skeys=set(zip(s['label'].tolist(),s['plate'].tolist()))
        stateok[li]=[key in skeys for key in keys]
    train=panel.delta.astype(float)@weights
    dose=np.array([study.wm.parse_label(l)[1] for l in labels])
    plates=sorted(set(wells[l][1] for l in labels))
    design=np.array([[float(wells[l][1]==plate) for plate in plates] for l in labels])
    state_scalar=panel.state.astype(float)@weights
    state_B=state_scalar[:,ib]
    shuffled_full,shuffledok_full,permutation=permute_states(state_scalar,stateok,keys)
    shuffled,shuffledok=shuffled_full[:,ib],shuffledok_full[:,ib]
    a=dict(train_A=train[:,ia],train_B=train[:,ib],availability_A=panel.avail[:,ia],
        availability_B=panel.avail[:,ib],precision_B=np.where(panel.avail[:,ib],1/np.maximum(panel.noise0[:,ib],1e-12),0.),
        basal=panel.basal,state_B=state_B,state_B_permuted=shuffled,state_available_B=stateok[:,ib],
        state_available_B_permuted=shuffledok,dose=dose,plate_design=design)
    np.savez_compressed(out/'training_arrays.npz',**a)
    models={};diagnostics={}
    included=np.ones(len(panel.files),bool)
    for name,perm,design_only in [('residual',False,False),('design',False,True),('permuted',True,False)]:
        x,errors,groups=method.dataset(a,included,perm)
        models[name]=method.fit(x,errors,design_only)
        diagnostics[name]=dict(training_rows=len(errors),missing_reference_rows=int(a['train_B'].size-len(errors)),
            active_coefficients=int(np.sum(np.abs(models[name]['coef'])>1e-12)),
            ratio_min=float(method.variance_ratio(models[name],x).min()),
            ratio_max=float(method.variance_ratio(models[name],x).max()))
    oofpred,ooftrue,oofconstant=method.nested_diagnostic(a)
    np.savez_compressed(out/'nested_reference_diagnostic.npz',predicted=oofpred,true=ooftrue,constant=oofconstant)
    diagnostics['nested_residual']=dict(rows=len(ooftrue),logerror_pearson=float(np.corrcoef(oofpred,ooftrue)[0,1]),
        learned_logerror_rmse=float(np.sqrt(np.mean((oofpred-ooftrue)**2))),
        constant_logerror_rmse=float(np.sqrt(np.mean((oofconstant-ooftrue)**2))),
        meaning='Nested entirecontext exclusion; STATE checkpoint was nevertheless trained on these contexts')
    cov,var,offset=parameters(a,included)
    threshold_scores=[]
    for held in range(len(panel.files)):
        keep=included.copy();keep[held]=False
        _,_,_,prior=method.reference_row(a,held)
        c,v,_=parameters(a,keep)
        method.validate_inputs(prior,c,v)
        scores,_=method.boundary_scores(prior,c,v,range(len(labels)))
        threshold_scores.append(max(scores.values()))
    tau=.1*float(np.median(threshold_scores))
    save_models(out,models)
    study.write(out/'TRAINING_DIAGNOSTIC.json',dict(diagnostics=diagnostics,
        threshold_m0_loo_scores=threshold_scores,tau=tau,training_permutation=permutation,
        STATE_reference_in_sample=True,calibrated_risk=False))
    public=dict(cov=cov,obsvar=var,offset=offset,tau=np.array(tau));private={};sourceaudit=[]
    for context,file in p['contexts'].items():
        t=study.wm.target(context,panel);tidx={k:i for i,k in enumerate(t['keys'])}
        if any(key not in tidx for key in keys):raise ValueError('Fullmenu source absent:'+context)
        kk=np.array([tidx[key] for key in keys])
        if not np.all(t['eligible'][kk]):raise ValueError('Fullmenu qualification failed:'+context)
        state=t['devS'][kk]
        shuffled_target,detail=study.state_permutation(state,keys)
        token=context.replace('/','_').replace('-','_')
        variance=np.nanvar(np.where(a['availability_B'],a['train_B'],np.nan),axis=0,ddof=1)
        distance=method.nearest_basal_distance(t['basal'],a['basal'])
        available=a['availability_B'].mean(0);state_coverage=a['state_available_B'].mean(0)
        x=method.features(.5*state[ib]@weights,distance,dose,design,available,state_coverage,variance)
        xp=method.features(.5*shuffled_target[ib]@weights,distance,dose,design,available,state_coverage,variance)
        public[token+'__M0']=m0[ib]@weights
        public[token+'__M2']=(m0+.5*state)[ib]@weights
        public[token+'__M2_permuted']=(m0+.5*shuffled_target)[ib]@weights
        public[token+'__features']=x;public[token+'__features_permuted']=xp
        for name,model in models.items():
            ratio=method.variance_ratio(model,xp if name=='permuted' else x)
            public[token+'__ratio_'+name]=ratio
        obs=study.wm.load_obs(file)
        oi={k:i for i,k in enumerate(zip(obs['label'].tolist(),obs['plate'].tolist()))}
        private[token+'__A']=t['delta'][kk[ia]]@weights
        private[token+'__B']=t['delta'][kk[ib]]@weights
        for role in ('A','B'):
            private[token+'__counts_'+role]=np.array([obs['n'][oi[(l,wells[l][role=='B'])]] for l in labels])
        sourceaudit.append(dict(context=context,full146source_qualified=True,basal_distance=distance,
            state_permutation=detail,
            scaled_covariance_min_eigenvalues={name:float(np.linalg.eigvalsh(method.scale_covariance(cov,
                public[token+'__ratio_'+name])).min()) for name in models},
            features_finite=bool(np.all(np.isfinite(x))),priors_finite=bool(np.all(np.isfinite(public[token+'__M2'])))))
    np.savez_compressed(out/'public_prior.npz',**public)
    np.savez_compressed(out/'evaluator_private.npz',**private)
    names=['public_prior.npz','evaluator_private.npz','training_arrays.npz','fitted_models.npz',
           'FIT_PARAMETERS.json','TRAINING_DIAGNOSTIC.json','nested_reference_diagnostic.npz']
    study.write(out/'PACKET_MANIFEST.json',dict(schema='boundary_scalar_packet_v1',
        protocol_sha256=study.digest(HERE/'PROTOCOL.json'),contexts=p['contexts'],labels=labels,wells=wells,arms=p['arms'],
        hashes={name:study.digest(out/name) for name in names},sizes={name:(out/name).stat().st_size for name in names},
        source_audit=sourceaudit,elapsed_seconds=time.perf_counter()-started,
        private_split='Evaluator-only unpurchased outcomes are never provided to policy; filesystemcontract, not OSsandbox',
        replay_requirement='OnlyscalarNPZ/SciPy/productionCaseStore; no largePanel/GPU/network/checkpoint load',
        raw_upstream_bytes=sum((ROOT/name).stat().st_size for name in p['upstream_dependencies'])))
    print(json.dumps(dict(packet_bytes=sum((out/name).stat().st_size for name in names),tau=tau,
                          diagnostic=diagnostics['nested_residual'])),flush=True)


class Evaluator(study.PaidObservations):
    def __init__(self,packet,out,case_id,context):
        meta=json.loads((packet/'PACKET_MANIFEST.json').read_text())
        token=context.replace('/','_').replace('-','_')
        with np.load(packet/'evaluator_private.npz',allow_pickle=False) as private:
            yA,yB=private[token+'__A'],private[token+'__B']
            counts={r:private[token+'__counts_'+r] for r in ('A','B')}
        super().__init__(out,case_id,context,meta['labels'],meta['wells'],yA,yB,counts,budget=13.,max_screens=8)


def episode(prior,cov,var,offset,evaluator,arm,tau,normals):
    started=time.perf_counter()
    method.validate_inputs(prior,cov,var)
    if offset.shape!=prior.shape or not np.all(np.isfinite(offset)):
        raise ValueError('Invalid observation offset')
    belief=study.Belief(prior.copy(),cov.copy(),var.copy())
    initial=study.flags(belief,5)
    order=[int(i) for i in np.lexsort((np.arange(len(prior)),-prior))]
    available=set(range(len(prior)));screens=[];prefix_flags=[initial]
    stopreason='fixed_screen_count' if arm['acquisition']=='fixed' else 'max_A_profiles'
    for step in range(arm['max_A']):
        pair=None;score=None
        if arm['acquisition']=='fixed':choice=next(i for i in order if i in available)
        elif arm['acquisition']=='KG':
            scores=study.kg_values(belief,5,sorted(available),normals)
            choice=max(scores,key=lambda i:(scores[i],-i));score=scores[choice]
            if score<=0:stopreason='nonpositive_KG_surrogate';break
        else:
            scores,details=method.boundary_scores(belief.mean,belief.cov,belief.obs_var,sorted(available))
            choice=max(scores,key=lambda i:(scores[i],-i));score=scores[choice];pair=details[choice]
            if arm['stopping'] and score<=tau:
                stopreason='boundary_surrogate_below_training_tau'
                study.append(evaluator.out/'policy.jsonl',dict(case_id=evaluator.case_id,step=step,event='stop',
                    next_candidate=choice,boundary_score=score,tau=tau,active_comparison=pair))
                break
        predictedA=float(belief.mean[choice]+offset[choice])
        observed=evaluator.screen(choice)
        innovation=observed-predictedA
        study.append(evaluator.out/'policy.jsonl',dict(case_id=evaluator.case_id,step=step,event='paid_screen',
            candidate=choice,boundary_or_KG_score=score,tau=tau,active_comparison=pair,
            purchased_A=observed,predicted_A=predictedA,innovation=innovation,
            current_flags=study.flags(belief,5),B_unavailable_to_policy=True))
        study.gaussian_update(belief,choice,observed,offset)
        screens.append(choice);available.remove(choice);prefix_flags.append(study.flags(belief,5))
    final=study.flags(belief,5);values=evaluator.confirm(final)
    snapshot=evaluator.store.snapshot(evaluator.case_id)
    return dict(case_id=evaluator.case_id,context=evaluator.context,arm=arm['name'],model=arm['model'],
        acquisition=arm['acquisition'],uncertainty=arm['uncertainty'],initial_flags=initial,final_flags=final,
        screened=screens,prefix_flags=prefix_flags,swapped_in=sorted(set(final)-set(initial)),
        swapped_out=sorted(set(initial)-set(final)),final_B_values=values,utility=float(sum(values)),
        actual_credits=snapshot.spent,common_cap=13,unused_cap=13-snapshot.spent,stopreason=stopreason,
        elapsed_seconds=time.perf_counter()-started)


def replay(packet,out):
    # Small replay validates sourcecode/protocol, never reads external upstream bytes.
    p=json.loads((HERE/'PROTOCOL.json').read_text());frozen=json.loads((HERE/'FREEZE.json').read_text())
    if study.digest(HERE/'PROTOCOL.json')!=frozen['protocol_sha256']:raise ValueError('Protocolchanged')
    for name,sha in p['source_dependencies'].items():
        if study.digest(ROOT/name)!=sha:raise ValueError('Sourcechanged:'+name)
    packet,out=Path(packet).resolve(),Path(out).resolve()
    if out.exists():raise ValueError('Use fresh output')
    out.mkdir(parents=True);started=time.perf_counter()
    meta=json.loads((packet/'PACKET_MANIFEST.json').read_text())
    if meta['protocol_sha256']!=study.digest(HERE/'PROTOCOL.json'):raise ValueError('Wrongpacket')
    for name,sha in meta['hashes'].items():
        if study.digest(packet/name)!=sha:raise ValueError('Packetmodified:'+name)
    rows=[];normals=np.random.default_rng(42).standard_normal(64)
    with np.load(packet/'public_prior.npz',allow_pickle=False) as public:
        for context in p['contexts']:
            token=context.replace('/','_').replace('-','_')
            for arm in p['arms']:
                covariance=public['cov']
                if arm['uncertainty']!='common':
                    name='permuted' if arm['model']=='M2_permuted' else ('design' if arm['uncertainty']=='design_missingness' else 'residual')
                    covariance=method.scale_covariance(covariance,public[token+'__ratio_'+name])
                evaluator=Evaluator(packet,out,token+'.'+arm['name'],context)
                draws=np.random.default_rng(42).standard_normal(arm.get('normal_draws',64))
                row=episode(public[token+'__'+arm['model']],covariance,public['obsvar'],public['offset'],
                            evaluator,arm,float(public['tau']),draws)
                rows.append(row);study.append(out/'EPISODES.jsonl',row)
            print(json.dumps(dict(context=context,episodes=len(p['arms']))),flush=True)
    # Outcome-rich audit follows committed B decisions; no further policy acts.
    audit=[];frontier=[]
    with np.load(packet/'evaluator_private.npz',allow_pickle=False) as private:
        for row in rows:
            token=row['context'].replace('/','_').replace('-','_');yB=private[token+'__B']
            audit.append(dict(case_id=row['case_id'],initial_utility=float(yB[row['initial_flags']].sum()),
                swapped_in_B=float(yB[row['swapped_in']].sum()),swapped_out_B=float(yB[row['swapped_out']].sum()),
                swaps_in=[dict(index=i,label=meta['labels'][i],B=float(yB[i])) for i in row['swapped_in']],
                swaps_out=[dict(index=i,label=meta['labels'][i],B=float(yB[i])) for i in row['swapped_out']]))
            for k,flags in enumerate(row['prefix_flags']):
                frontier.append(dict(context=row['context'],arm=row['arm'],A=k,credits=k+5,
                    utility=float(yB[flags].sum()),flags=json.dumps(flags),posthoc=True))
    study.write(out/'REPLACEMENT_AUDIT.json',audit)
    with (out/'PREFIX_FRONTIER.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(frontier[0]));writer.writeheader();writer.writerows(frontier)
    groups=[]
    for arm in p['arms']:
        selected=[r for r in rows if r['arm']==arm['name']]
        groups.append(dict(arm=arm['name'],mean_utility=float(np.mean([r['utility'] for r in selected])),
            total_credits=sum(r['actual_credits'] for r in selected),
            per_context={r['context']:dict(utility=r['utility'],credits=r['actual_credits'],stopreason=r['stopreason']) for r in selected}))
    study.write(out/'SUMMARY.json',dict(status=p['status'],episodes=len(rows),groups=groups,
        profiles=sum(r['actual_credits'] for r in rows),common_cap_total=len(rows)*13,
        api_calls=0,fresh_STATE_inference=0,new_downloaded_bytes=0,new_wet_experiments=0,
        elapsed_seconds=time.perf_counter()-started,protocol_sha256=study.digest(HERE/'PROTOCOL.json'),
        packet_manifest_sha256=study.digest(packet/'PACKET_MANIFEST.json'),
        primary='Percontext descriptive cost-utility; no newindependentbiologicalefficacy or calibratedrisk'))
    print(json.dumps(dict(groups=[{k:r[k] for k in ('arm','mean_utility','total_credits')} for r in groups],
                          profiles=sum(r['actual_credits'] for r in rows))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['build','replay'])
    parser.add_argument('--packet',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    (build(args.out) if args.command=='build' else replay(args.packet,args.out))
