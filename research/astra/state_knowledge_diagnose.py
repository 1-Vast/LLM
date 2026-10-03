"""Development diagnosis and nested shrinkage for PublicTargetGOKernel, not STATE."""
import argparse
from datetime import datetime, timezone
from itertools import combinations
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits

from research.astra.state_knowledge_retrospective import kernel_predict, split_indices
from tools.datasets.state_prospective_input import digest, write_json


def shrinkage(pred, truth, groups):
    counts=pd.Series(groups).value_counts()
    weights=np.array([1/counts[g] for g in groups])[:,None]
    denom=np.sum(weights*pred*pred)
    return float(np.clip(np.sum(weights*pred*truth)/denom,0,1)) if denom>0 else 0.0


def run(previous,out):
    out.mkdir(parents=True,exist_ok=False)
    (out/"execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    records=pd.DataFrame(json.loads((previous/"eligible_metadata.json").read_text()))
    saved=np.load(previous/"predictions_and_observations.npz")
    y=saved["observed"]
    graphs=np.load(previous/"knowledge_kernels.npz")
    idx=records.drug_index.to_numpy()
    dose=(records.dose.to_numpy()[:,None]==records.dose.to_numpy()[None,:]).astype(float)
    kernels={"dose_only":dose,"public_target_GO":dose*(1+graphs['go'][np.ix_(idx,idx)])}
    diagnosis={}
    for name in kernels:
        p=saved[name]
        diagnosis[name]=dict(mean_response_energy=float(np.mean(y*y)),mean_prediction_energy=float(np.mean(p*p)),
                             signal_alignment=float(np.mean(p*y)),
                             mse_identity=float(np.mean(y*y)+np.mean(p*p)-2*np.mean(p*y)),
                             amplitude_ratio=float(np.sqrt(np.mean(p*p)/np.mean(y*y))),
                             retrospective_optimal_shrinkage_descriptive_only=shrinkage(p,y,records.chemical_group))
    repeat=[]
    for key,part in records.groupby(['chemical_group','dose']):
        for i,j in combinations(part.index,2):
            if records.loc[i,'plate']==records.loc[j,'plate']: continue
            denom=np.linalg.norm(y[i])*np.linalg.norm(y[j])
            repeat.append(dict(chemical_group=key[0],dose=key[1],plate_a=records.loc[i,'plate'],plate_b=records.loc[j,'plate'],
                               response_cosine=float(np.dot(y[i],y[j])/denom) if denom else None))
    neighbors=[]
    for fold in range(5):
        train,test=split_indices(records,fold)
        cos=graphs['go'][np.ix_(idx[test],idx[train])]
        support=cos*(records.iloc[test].dose.to_numpy()[:,None]==records.iloc[train].dose.to_numpy()[None,:])
        neighbors.append(dict(fold=fold,train=len(train),test=len(test),no_positive_neighbor=int((support.max(axis=1)<=0).sum()),
                              median_best_neighbor_cosine=float(np.median(support.max(axis=1)))))
    pair_sim=[]
    for _,part in records.groupby(['plate','dose']):
        for i,j in combinations(part.index,2):
            if records.loc[i,'chemical_group']==records.loc[j,'chemical_group']:continue
            denom=np.linalg.norm(y[i])*np.linalg.norm(y[j])
            if denom:pair_sim.append([graphs['go'][idx[i],idx[j]],float(np.dot(y[i],y[j])/denom)])
    arr=np.asarray(pair_sim)
    diagnosis.update(repeat_pairs=len(repeat),median_repeat_response_cosine=float(np.median([r['response_cosine'] for r in repeat if r['response_cosine'] is not None])),
                     same_plate_dose_target_response_similarity_spearman=float(spearmanr(arr[:,0],arr[:,1]).statistic),
                     similarity_pairs=len(arr),neighbor_support=neighbors,
                     endpoint_scope="control-centered RNA; replicate correlations are descriptive assay repeats, not independent cultures",
                     annotation_limit="static unordered targets; no potency, agonism/inhibition direction, occupancy, or per-question state")
    write_json(out/"diagnosis.json",diagnosis);write_json(out/"repeat_pairs.json",repeat)
    freeze=dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),study="PublicTargetGOKernel nested DEVELOPMENT validation",
                source_hashes={p.name:digest(p) for p in [previous/'freeze.json',previous/'predictions_and_observations.npz',previous/'knowledge_kernels.npz']},
                status="all outcomes previously explored; not a new unseen or confirmatory test",
                improvement="one scalar shrinkage toward zero selected only from inner held-out predictions",
                alpha=1.0,outer_folds="historical five whole-plate folds; chemical identities purged",
                inner_folds="leave-one-plate-out within outer training, same chemical purge; metadata support checked before scoring",
                shrinkage="clip weighted inner cross-fit dot(pred,y)/dot(pred,pred) to [0,1]; equal chemical weights",
                equal_budget="both dose and GO get identical inner plate folds plus one outer fit; no added knowledge or retuning",
                primary="chemical-macro MSE",physical_CI="not_reported",seed=42,cost="unknown")
    write_json(out/"freeze.json",freeze)
    predictions={name:np.full_like(y,np.nan) for name in kernels}; scalars=[]; fits=0
    with threadpool_limits(limits=2):
        for outer in range(5):
            train,test=split_indices(records,outer)
            sub=records.iloc[train].reset_index(drop=True).copy()
            pmap={p:i for i,p in enumerate(sorted(set(sub.plate)))}
            sub['fold']=sub.plate.map(pmap)
            for name,kernel in kernels.items():
                inner=np.full((len(train),y.shape[1]),np.nan)
                for fold in range(len(pmap)):
                    a,b=split_indices(sub,fold)
                    if len(a)==0 or len(b)==0:raise ValueError('empty inner fold after chemical purge')
                    inner[b]=kernel_predict(kernel,train[a],train[b],y,1.)
                    fits+=1
                if not np.isfinite(inner).all():raise ValueError('incomplete inner cross fitting')
                factor=shrinkage(inner,y[train],records.iloc[train].chemical_group)
                predictions[name][test]=factor*kernel_predict(kernel,train,test,y,1.)
                fits+=1
                scalars.append(dict(outer_fold=outer,model=name,shrinkage=factor,training_records=len(train),test_records=len(test)))
    scores={}
    for name,p in {**predictions,'no_change':np.zeros_like(y)}.items():
        per=pd.DataFrame({'chemical':records.chemical_group,'mse':np.mean((p-y)**2,axis=1),'mae':np.mean(np.abs(p-y),axis=1)})
        scores[name]={'chemical_macro_MSE':float(per.groupby('chemical').mse.mean().mean()),
                      'chemical_macro_MAE':float(per.groupby('chemical').mae.mean().mean())}
    summary=dict(scope=freeze['status'],models=scores,scalars=scalars,
                 total_model_fits=fits,STATE_calls=0,state_input="absent",utility="not_identified",cost="unknown")
    write_json(out/'summary.json',summary)
    np.savez_compressed(out/'nested_predictions.npz',**predictions)
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.iterdir() if p.is_file()})
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.previous.resolve(),args.out.resolve()),indent=2))
