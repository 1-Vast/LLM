"""Sister-lineage RNA forecasting, conditional on deposited matched follow-up.

Auxiliary RidgeRNA, not STATE. Inputs/queries are built from all deposited baseline
cells using pre-only sister IDs; future matching is used only to attach outcomes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from tools.datasets.state_prospective_input import digest, write_json

SAMPLES = {(1,"carboplatin"): (6938163,6938164), (2,"carboplatin"): (6938165,6938166),
           (1,"growth_control"): (6938175,6938176), (2,"growth_control"): (6938177,6938178)}


def baseline_groups(metadata):
    # Never use drugSens or prer_r_group here: both carry future information.
    return pd.Series([f"sister:{int(s)}" if pd.notna(s) else f"cell:{cell}"
                      for cell,s in zip(metadata.index,metadata.sisters)], index=metadata.index)


def load_counts(path, metadata, genes=None):
    """Exact Ensembl IDs; log1p(CP10k) over all deposited genes, no missing imputation."""
    totals = np.zeros(len(metadata), dtype=np.float64)
    selected, stats = {}, {}
    requested = set(genes) if genes is not None else None
    for chunk in pd.read_csv(path, compression="gzip", sep="\t", index_col=0, chunksize=256):
        if set(chunk.columns) != set(metadata.index) or not chunk.index.is_unique:
            raise ValueError("RNA/sample identity mismatch")
        values = chunk.loc[:,metadata.index].to_numpy(dtype=np.float64)
        if not np.isfinite(values).all() or (values<0).any() or not np.equal(values,np.floor(values)).all():
            raise ValueError("noninteger or invalid UMI count")
        totals += values.sum(axis=0)
        norm = np.log1p(values * (10000 / metadata.nCount_RNA.to_numpy())[None,:])
        for name,row in zip(chunk.index.astype(str),norm):
            if name in stats:
                raise ValueError("duplicate Ensembl ID")
            stats[name] = float(row.var())
            if requested is not None and name in requested:
                selected[name] = row.astype(np.float32)
    if not np.array_equal(totals,metadata.nCount_RNA.to_numpy()):
        raise ValueError("UMI library totals disagree with deposited nCount_RNA")
    if genes is None:
        return stats
    if requested-set(selected):
        raise ValueError("missing frozen genes; cannot impute nondetection")
    return np.stack([selected[g] for g in genes],axis=1)


def attach_responses(pre_meta, post_meta, groups, post_values):
    response = {}
    for key in sorted(set(groups)):
        ids = pre_meta.loc[groups==key,"prer_r_group"].dropna().unique()
        if len(ids)>1:
            raise ValueError("baseline sister group has conflicting future linkage")
        if len(ids)==1:
            mask = post_meta.prer_r_group==ids[0]
            if mask.any():
                response[key] = (post_values[mask].mean(axis=0),
                                 post_meta.index[mask].tolist(),float(ids[0]))
    return response


def predict_pair(train_x, train_y, query_x, reference, blind=False):
    x = np.repeat(reference[None,:],len(train_x),axis=0) if blind else train_x
    q = np.repeat(reference[None,:],len(query_x),axis=0) if blind else query_x
    center, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale<1e-6] = 1
    model = Ridge(alpha=10.0, solver="svd")
    model.fit((x-center)/scale,train_y)
    return model.predict((q-center)/scale)


def metrics(pred, truth):
    x,y=pred.reshape(-1),truth.reshape(-1)
    slope=float(np.dot(x-x.mean(),y-y.mean())/np.sum((x-x.mean())**2)) if np.std(x) else None
    return dict(MSE=float(np.mean((pred-truth)**2)),MAE=float(np.mean(np.abs(pred-truth))),
                pooled_calibration_slope=slope,pooled_calibration_intercept=float(y.mean()-slope*x.mean()) if slope is not None else None)


def run(sources,out):
    out.mkdir(parents=True,exist_ok=False)
    (out/"execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    meta={n:pd.read_csv(sources/f"evidence/GSM{n}_info.raw",compression="gzip",sep="\t",index_col=0)
          for pair in SAMPLES.values() for n in pair}
    paths={n:sources/("controls" if n>=6938175 else "material")/f"GSM{n}_counts.raw" for n in meta}
    # Select a fixed endpoint/feature axis using development BASELINE RNA only.
    variance=[load_counts(paths[SAMPLES[1,a][0]],meta[SAMPLES[1,a][0]]) for a in ["carboplatin","growth_control"]]
    common=set(variance[0])&set(variance[1])
    genes=sorted(common,key=lambda g:(-(variance[0][g]+variance[1][g]),g))[:256]
    plan=dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),model="RidgeRNA auxiliary, not STATE",
              context="KURAMOCHI",training_replicate=1,test_replicate=2,
              genes=genes,feature_selection="top 256 average variances of development pre-treatment RNA; no post expression",
              preprocessing="unchanged Ensembl IDs; log1p(UMI*10000/deposited total); duplicates/missing/noninteger/total mismatch reject",
              alpha=10.0,hyperparameter_trials=1,seed=20261001,
              reference="all baseline sister-group means from replicate 1 in the same action context; frozen before test response read",
              state_permutation="within action and replicate over ALL baseline groups, before response matching",
              primary="equal action then equal baseline sister-group MSE over observed exact-match follow-up RNA",
              coverage="all deposited baseline groups are prediction requests; only groups with exact observed follow-up can be scored",
              outcome="mean post-treatment log1p RNA of deposited exact-match descendants; not death/survival or causal drug effect",
              controls="separate untreated-growth arm, same cell line; not certified same-parent counterfactual",
              exclusions="baseline-independent raw QC done by provider; missing follow-up retained, never imputed as death",
              exposure="metadata inspected; post expression not read by this program before freeze; retrospective exploratory study, not confirmatory",
              independent_cultures="unknown; replicate labels blocked, no physical CI",cost="unknown",
              sources={str(p):digest(p) for p in [*paths.values(),*[sources/f'evidence/GSM{n}_info.raw' for n in meta]]})
    write_json(out/"freeze.json",plan)
    x,questions,groups={},[],{}
    for (rep,action),(pre,post) in SAMPLES.items():
        g=baseline_groups(meta[pre]); groups[rep,action]=g
        values=load_counts(paths[pre],meta[pre],genes)
        frame=pd.DataFrame(values,index=meta[pre].index).groupby(g,sort=True).mean()
        x[rep,action]=frame
        for key in frame.index:
            questions.append(dict(question_id=f"{rep}:{action}:{key}",replicate=rep,action=action,baseline_group=key,
                                  pre_accession=f"GSM{pre}",pre_cells=meta[pre].index[g==key].tolist(),
                                  pre_source_rows=[int(i)+2 for i in np.flatnonzero(g==key)],role="prediction_request"))
    write_json(out/"baseline_questions.json",questions)
    permutations={}
    for key,frame in x.items():
        permutations[f"{key[0]}:{key[1]}"]=np.random.default_rng(20261001).permutation(len(frame)).tolist()
    write_json(out/"permutations_before_response.json",permutations)
    # Only now read post-treatment expression and attach it to the prebuilt queries.
    matched,joins={},[]
    for (rep,action),(pre,post) in SAMPLES.items():
        values=load_counts(paths[post],meta[post],genes)
        matched[rep,action]=attach_responses(meta[pre],meta[post],groups[rep,action],values)
        for key,(y,cells,gid) in matched[rep,action].items():
            joins.append(dict(question_id=f"{rep}:{action}:{key}",post_accession=f"GSM{post}",
                              post_cells=cells,source_prer_r_group=gid,
                              evidence="pinned Preprocess_Carbo_1.Rmd lines 752-802: exact lineage-label combination matching; not a same-cell trajectory"))
    write_json(out/"response_joins.json",joins)
    results,coverage,predictions={},[],{}
    with threadpool_limits(limits=2):
        for action in ["carboplatin","growth_control"]:
            train_keys=sorted(matched[1,action]); test_keys=sorted(matched[2,action])
            if min(len(train_keys),len(test_keys))<10:
                raise ValueError("insufficient exact-match lineage support")
            train_x=x[1,action].loc[train_keys].to_numpy(); train_y=np.stack([matched[1,action][k][0] for k in train_keys])
            all_q=x[2,action].to_numpy(); selected=x[2,action].index.get_indexer(test_keys)
            truth=np.stack([matched[2,action][k][0] for k in test_keys])
            reference=x[1,action].mean(axis=0).to_numpy()
            np.save(out/f"blind_reference_{action}.npy",reference)
            visible=predict_pair(train_x,train_y,all_q,reference)
            blind=predict_pair(train_x,train_y,all_q,reference,blind=True)
            perm=permutations[f"2:{action}"]
            preds={"state_visible":visible,"state_blind_same_family":blind,
                   "state_permuted":visible[perm],"no_change":all_q,
                   "context_mean_response":np.repeat(train_y.mean(axis=0)[None,:],len(all_q),axis=0)}
            # Hash-group development validation; no parameter is chosen from it.
            val=np.array([int(hashlib.sha256(k.encode()).hexdigest()[:8],16)%5==0 for k in train_keys])
            devpred=predict_pair(train_x[~val],train_y[~val],train_x[val],reference)
            results[action]={"development_validation":metrics(devpred,train_y[val]),
                             "test":{name:metrics(p[selected],truth) for name,p in preds.items()}}
            for name,p in preds.items(): predictions[f"{action}_{name}"]=p
            predictions[f"{action}_observed_matched"]=truth
            predictions[f"{action}_scored_query_indices"]=selected
            for rep in [1,2]:
                coverage.append(dict(action=action,replicate=rep,baseline_groups=len(x[rep,action]),
                                     matched_groups=len(matched[rep,action]),
                                     matched_fraction=len(matched[rep,action])/len(x[rep,action])))
    summary=dict(scope=plan["outcome"],model=plan["model"],metrics=results,coverage=coverage,
                 test_action_macro_MSE={name:float(np.mean([results[a]['test'][name]['MSE'] for a in results])) for name in preds},
                 predictive_population="conditional on exact-match deposited descendants; missing follow-up may depend on state and sampling",
                 physical_CI="not_reported",STATE_calls=0,prospective_state_availability="unknown/not_established",
                 action_gain="not_run",utility="not_identified",cost="unknown")
    write_json(out/"summary.json",summary)
    np.savez_compressed(out/"predictions_and_observations.npz",**predictions)
    write_json(out/"manifest.json",{p.name:digest(p) for p in out.iterdir() if p.is_file()})
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.sources.resolve(),args.out.resolve()),indent=2))
