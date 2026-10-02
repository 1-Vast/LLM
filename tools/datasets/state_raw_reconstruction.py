"""Strict raw-UMI reconstruction for a separately named official STATE checkpoint.

Empirically verifies the deposited HepG2 raw->processed path, not universal raw
RNA compatibility or provider training provenance. Original Tahoe stays blocked.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import time

import anndata as ad
import numpy as np
import pandas as pd
import torch

from virtual_cell.state_runner import _numpy_scalar_globals
from tools.datasets.state_prospective_input import digest, write_json


def convert_counts(counts, ensembl_ids, contract, *, research_reconstruction=False):
    if not research_reconstruction:
        raise ValueError("external RNA not certified: provider preprocessing provenance remains unknown")
    if list(ensembl_ids)!=contract['raw_ensembl_axis']:
        raise ValueError("raw Ensembl axis/version mismatch; missing or duplicate genes forbidden")
    values=np.asarray(counts,dtype=np.float64)
    if values.ndim!=2 or values.shape[1]!=len(ensembl_ids):
        raise ValueError('raw count matrix shape mismatch')
    if not np.isfinite(values).all() or (values<0).any() or not np.equal(values,np.floor(values)).all():
        raise ValueError('finite nonnegative integer UMI counts required')
    totals=values.sum(axis=1)
    if (totals<=0).any():raise ValueError('empty RNA library')
    # Normalize BEFORE selecting the fixed official model axis.
    return np.log1p(values[:,contract['source_indices']]*10000/totals[:,None]).astype(np.float32)


def run(sources,out,inputs=None):
    out.mkdir(parents=True,exist_ok=False)
    inputs=sources if inputs is None else inputs
    (out/'execution_source.py.txt').write_bytes(Path(__file__).read_bytes())
    genes=json.loads((inputs/'hepg2_raw_symbols.json').read_text())
    ensembl=json.loads((inputs/'hepg2_raw_axis.json').read_text())
    dims=pickle.loads((sources/'evidence/replogle_var_dims.raw').read_bytes())
    model_axis=list(dims['gene_names'])
    official=json.loads((inputs/'replogle_remote_axis.json').read_text())
    if model_axis!=official or len(model_axis)!=dims['input_dim'] or len(set(ensembl))!=len(ensembl):
        raise ValueError('official ordered model axis mismatch')
    unique=ad.utils.make_index_unique(pd.Index(genes)).tolist()
    source_indices=[unique.index(g) for g in model_axis]
    contract=dict(model='arcinstitute/st-x-replogle-full/k562_0.99',revision='48ad5f70215ab4c58caa5a68e77d837601d29d35',
                  raw_ensembl_axis=ensembl,raw_symbols=genes,model_axis=model_axis,source_indices=source_indices,
                  coordinate_map=[dict(model_coordinate=i,model_name=g,raw_ensembl=ensembl[j],raw_symbol=genes[j],raw_position=j) for i,(g,j) in enumerate(zip(model_axis,source_indices))],
                  raw_gene_universe=9624,model_gene_count=6546,normalization='CP10000 over exactly9624 deposited genes before model subset; natural log1p; float32',
                  duplicate_rule='explicit Ensembl-to-coordinate mapping; two distinct HSPA14 IDs remain distinct; no summation',
                  normalization_status='empirical same-record raw->processed reconstruction; exact original training pipeline provenance unknown',
                  certified_external_new_RNA=False,mode='explicit research reconstruction only',
                  weights_sha256=digest(sources/'alternate/replogle_model_weights.raw'))
    write_json(out/'contract.json',contract)
    counts=np.load(inputs/'hepg2_raw32.npy');expected=np.load(inputs/'replogle_first32.npy')
    actual=convert_counts(counts,ensembl,contract,research_reconstruction=True)
    error=float(np.max(np.abs(actual-expected)))
    if not np.allclose(actual,expected,atol=1e-6,rtol=1e-6):
        raise ValueError('reconstructed expression differs from official processed cells')
    np.save(out/'reconstructed32.npy',actual)
    model_dir=out/'model';(model_dir/'checkpoints').mkdir(parents=True)
    for src,dst in [('evidence/replogle_config.raw','config.yaml'),('evidence/replogle_var_dims.raw','var_dims.pkl'),('alternate/replogle_map.raw','pert_onehot_map.pt')]:
        shutil.copyfile(sources/src,model_dir/dst)
    for name in ['batch_onehot_map','cell_type_onehot_map']:
        shutil.copyfile(sources/f'compatibility/{name}.raw',model_dir/f'{name}.pkl')
    with torch.serialization.safe_globals(list(_numpy_scalar_globals())):
        mapping=torch.load(model_dir/'pert_onehot_map.pt',map_location='cpu',weights_only=True)
    actions=['TFAM','MAP2K7'];control='non-targeting'
    if any(x not in mapping for x in [control,*actions]):raise ValueError('unknown action; no control fallback')
    obs=json.loads((inputs/'replogle_first1000_obs.json').read_text())
    selected=[i for i in range(32) if obs['gene'][i]==control]
    if not selected:raise ValueError('no true control among raw reconstruction rows')
    # Select only the first matched context/gem pool; never mix controls across gems.
    chosen=selected[0];context=obs['cell_line'][chosen];batch=obs['gem_group'][chosen]
    if batch not in pickle.loads((model_dir/'batch_onehot_map.pkl').read_bytes()) or context not in pickle.loads((model_dir/'cell_type_onehot_map.pkl').read_bytes()):
        raise ValueError('unknown batch or cell context; no fallback')
    basal=actual[[i for i in selected if obs['cell_line'][i]==context and obs['gem_group'][i]==batch]]
    freeze=dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),model=contract['model'],weights_sha256=contract['weights_sha256'],
                actions=actions,context=context,gem_group=batch,baseline_rows=selected,query_count=16,seed=42,
                fixture='real original non-targeting raw RNA reconstructed to separate official processed axis; no biological prospective state claim',
                atol=1e-6,rtol=1e-6,selector=None)
    write_json(out/'freeze.json',freeze)
    receipts=[]
    for name,baseline in [('raw_reconstructed',basal),('official_processed',expected[[chosen]])]:
        folder=out/name;folder.mkdir()
        labels=[control]*len(baseline)+[a for a in actions for _ in range(16)]
        matrix=np.concatenate([baseline,np.zeros((32,len(model_axis)),np.float32)])
        frame=pd.DataFrame({'gene':labels,'cell_line':context,'gem_group':batch,
                            'role':['baseline_control']*len(baseline)+['prediction_request']*32},index=[f'row{i}' for i in range(len(matrix))])
        query=ad.AnnData(X=matrix,obs=frame,var=pd.DataFrame(index=model_axis));query.write_h5ad(folder/'query.h5ad')
        command=[sys.executable,'-m','tools.datasets.state_replogle_compat','--model-dir',str(model_dir),
                 '--checkpoint',str(sources/'alternate/replogle_model_weights.raw'),'--adata',str(folder/'query.h5ad'),
                 '--output',str(folder/'prediction.h5ad'),'--pert-col','gene','--celltype-col','cell_line','--batch-col','gem_group',
                 '--control-pert',control,'--seed','42','--quiet']
        start=time.perf_counter();done=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        (folder/'stdout.txt').write_text(done.stdout,encoding='utf-8');(folder/'stderr.txt').write_text(done.stderr,encoding='utf-8')
        receipt=dict(command=command,returncode=done.returncode,elapsed_seconds=time.perf_counter()-start,valid=False,valid_experiment=False,cost='unknown')
        if done.returncode==0:
            predicted=ad.read_h5ad(folder/'prediction.h5ad');trace=json.loads((folder/'forward_trace.json').read_text())
            receipt.update(valid=bool(predicted.shape==query.shape and np.isfinite(predicted.X).all() and len(trace['calls'])==3),forward_calls=len(trace['calls']))
            np.save(folder/'request_predictions.npy',predicted.X[len(baseline):])
        write_json(folder/'receipt.json',receipt);receipts.append(receipt)
        print(name,receipt['valid'],flush=True)
    output_difference=None
    if all(r['valid'] for r in receipts):
        a,b=[np.load(out/name/'request_predictions.npy') for name in ['raw_reconstructed','official_processed']]
        output_difference=float(np.max(np.abs(a-b)))
    summary=dict(model=contract['model'],raw_processed_max_abs_difference=error,raw_processed_rows=32,
                 input_axis_complete=True,real_checkpoint_requests=sum(r['valid'] for r in receipts),
                 forward_calls=sum(r.get('forward_calls',0) for r in receipts),prediction_max_abs_difference=output_difference,
                 paired_output_tolerance_pass=bool(output_difference is not None and np.allclose(a,b,atol=1e-6,rtol=1e-6)),
                 technical_reconstruction=('input_and_forward_passed_output_equivalence_not_passed'
                     if output_difference is not None and not np.allclose(a,b,atol=1e-6,rtol=1e-6)
                     else 'passed' if all(r['valid'] for r in receipts) else 'failed_forward'),
                 general_new_RNA_certification='not_complete; protocol provenance and general assay gene universe unresolved',
                 original_Tahoe_route='unchanged; 31 coordinates unresolved',state_gain='not_run',receipts=receipts)
    write_json(out/'summary.json',summary)
    write_json(out/'manifest.json',{p.relative_to(out).as_posix():digest(p) for p in out.rglob('*') if p.is_file()})
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--inputs',type=Path)
    args=parser.parse_args();print(json.dumps(run(args.sources.resolve(),args.out.resolve(),args.inputs.resolve() if args.inputs else None),indent=2))
