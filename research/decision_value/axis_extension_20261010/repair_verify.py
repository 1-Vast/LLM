"""Verify repaired values by independent logical HDF5 slices and block matching."""
import json
import h5py
import numpy as np

from .audit import HERE, PRIOR, ROOT, Cached, check_freeze, extract, lines, read, sha, vectors, write
from .verify import compare_all


def logical_vectors(file,rows):
    source=Cached(file,extension=True)
    pointer=np.load(PRIOR/f'inputs/{file}_POINTERS.npy',allow_pickle=False)
    names=read(PRIOR/f'inputs/{file}_GENES.json')
    census=read(PRIOR/'CENSUSES.json')[file]
    coordinates=read(PRIOR/'PROTOCOL.json')['endpoint']['coordinates']
    raw,targets=[],[]
    with h5py.File(source,'r') as h5:
        for row in rows:
            lo,hi=int(pointer[row]),int(pointer[row+1])
            ids=extract(source,h5['X/indices'],lo,hi)
            data=extract(source,h5['X/data'],lo,hi)
            assert len(ids)==len(data)==hi-lo==len(np.unique(ids))
            assert np.isfinite(data).all() and (data>=0).all()
            x=np.zeros(len(names),dtype=np.float64)
            x[ids]=data
            raw.append(np.log1p(x))
            offset=census['layouts']['obsm/X_hvg']['offset']+row*8000
            targets.append(np.frombuffer(source.at(offset,offset+8000),dtype='<f4')[coordinates].astype(np.float64))
    return names,np.asarray(raw),np.asarray(targets)


def main():
    for name in ['C44_FREEZE.json','C45_FREEZE.json','OFFLINE_REPAIR_FREEZE.json']:check_freeze(HERE/name)
    for name,expected in read(HERE/'PRIOR_SNAPSHOT.json')['sha256'].items():assert sha(ROOT/name)==expected,name
    c44,c45=read(HERE/'C44_UNION.json'),read(HERE/'C45_NUMERIC_RECONSTRUCTED.json')
    symbols=read(HERE/'PROTOCOL.json')['endpoint']['symbols']
    files=[]
    for file,record in [('c44.h5ad',c44),('c45.h5ad',c45)]:
        rows=record['rows'] if file=='c44.h5ad' else record['discovery_rows']+record['consistency_rows']
        if file=='c44.h5ad':
            names,raw,target=vectors(file,rows)
            tests=compare_all(names,raw,target,symbols)
        else:
            names,raw,target=logical_vectors(file,rows)
            split=len(record['discovery_rows'])
            tests=compare_all(names,raw[:split],target[:split],symbols,(raw[split:],target[split:]))
        assert len(tests)==39
        for a,b in zip(record['records'],tests):
            assert a['matching_source_indices']==b['matches']
            assert a['nonzero_cells']==b['nonzero'] and a['expected_max_error']==b['error']
            assert a['passed']==b['passed'] and b['passed']
            if file=='c45.h5ad':
                assert a['consistency_nonzero_cells']==b['held_nonzero'] and a['consistency_max_error']==b['held_error']
        files.append(dict(file=file,passed=39,maximum_error=max(t['error'] for t in tests)))
    plan=read(HERE/'C45_SELECTION_VERIFIED.json')
    permitted={tuple(s) for k in ['value_ranges','HVG_ranges'] for s in plan[k]}
    ledger=lines(HERE/'NETWORK.jsonl')
    observed=[]
    for r in ledger:
        if r['status']=='HEAD':assert r['bytes']==0;continue
        assert r['status']=='RETAINED' and r['http_status']==206 and r['source_revision']==read(HERE/'PROTOCOL.json')['source_revision']
        assert (r['start'],r['end']) in permitted
        assert r['bytes']==r['end']-r['start']+1
        observed.append((r['start'],r['end']))
    assert set(observed)==permitted and len(observed)==len(permitted)
    charged=sum(r['bytes'] for r in ledger)
    assert charged==133564==c45['new_received_body_bytes']
    assert charged<=read(HERE/'PROTOCOL.json')['new_received_body_cap_bytes']
    receipt=dict(status='PASS_SEPARATE_LOGICAL_SLICE_BLOCKWISE_RECONSTRUCTION',files=files,new_body_bytes=charged,new_network_requests=0,prior_files_unchanged=True,producer_matching_imports=False,producer_layout_reader_imports=False,independent_subagent_run=False,shared_hash_checked_range_reader=True,fresh_holdout=False,independent_biological_validation=False,verifier_sha256=sha(HERE/'repair_verify.py'))
    write(HERE/'VERIFIED.json',receipt)
    write(HERE/'QUALIFIED_CERTIFICATE.json',dict(status='PASS_FILE_LOCAL_DATA_ENDPOINT39_QUALIFICATION',source_repo='arcinstitute/State-Tahoe-Filtered',source_revision=read(HERE/'PROTOCOL.json')['source_revision'],files=files,transform='log1p(stored normalized X) once',absolute_tolerance=1e-5,scope='Specified39columns perfile at pinnedrevision; historical/adaptive data-axis evidence, no untouched biological validation',c44_result_sha256=sha(HERE/'C44_UNION.json'),c45_result_sha256=sha(HERE/'C45_NUMERIC_RECONSTRUCTED.json'),verification_sha256=sha(HERE/'VERIFIED.json'),execution_freeze_sha256=sha(HERE/'C45_FREEZE.json'),offline_repair_freeze_sha256=sha(HERE/'OFFLINE_REPAIR_FREEZE.json'),prior_P05R_failed_certificate_unchanged=True,initial_extension_parser_failure_preserved=True,full2000_axis_certified=False,STATE_checkpoint_axis_certified=False,fresh_holdout=False,old250_noise_plan_released=False,P06_execution_released=False,P06_data_axis_prerequisite_satisfied=True,P2_released=False,production_promotion=False))
    print(json.dumps(receipt))


if __name__=='__main__':main()
