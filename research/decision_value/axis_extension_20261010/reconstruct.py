"""Offline parser repair using frozen row layouts, without new HDF5 requests."""
import json
import numpy as np

from .audit import HERE, PRIOR, Cached, check_freeze, matching, read, sha, vectors, write


def layout_vectors(file,rows):
    source=Cached(file,extension=True)
    jobs={j['row']:j for j in read(PRIOR/'INDEX_LAYOUTS.json')[file]}
    names=read(PRIOR/f'inputs/{file}_GENES.json')
    census=read(PRIOR/'CENSUSES.json')[file]
    coordinates=read(PRIOR/'PROTOCOL.json')['endpoint']['coordinates']
    raw,targets=[],[]
    for row in rows:
        job=jobs[row]
        indices=np.frombuffer(b''.join(source.at(a,b+1) for a,b in job['indices']),dtype=census['layouts']['X/indices']['dtype'])
        values=np.frombuffer(b''.join(source.at(a,b+1) for a,b in job['values']),dtype=census['layouts']['X/data']['dtype'])
        assert len(indices)==len(values)==job['nnz']==len(np.unique(indices))
        assert (indices>=0).all() and (indices<len(names)).all()
        assert np.isfinite(values).all() and (values>=0).all()
        x=np.zeros(len(names),dtype=np.float64)
        x[indices]=values
        raw.append(np.log1p(x))
        offset=census['layouts']['obsm/X_hvg']['offset']+row*8000
        target=np.frombuffer(source.at(offset,offset+8000),dtype='<f4')
        assert len(target)==2000 and np.isfinite(target).all() and (target>=0).all()
        targets.append(target[coordinates].astype(np.float64))
    return names,np.asarray(raw),np.asarray(targets)


def main():
    check_freeze(HERE/'OFFLINE_REPAIR_FREEZE.json')
    assert read(HERE/'C45_NUMERIC.json')['error']['reason']=='unretained_range:2145096528:2145097040'
    plan=read(HERE/'C45_SELECTION_VERIFIED.json')
    discovery=plan['existing_discovery_rows']+plan['rows']
    held=plan['existing_consistency_rows']
    names,raw,target=layout_vectors('c45.h5ad',discovery+held)
    split=len(discovery)
    records=matching(names,raw[:split],target[:split],read(HERE/'PROTOCOL.json')['endpoint']['symbols'],consistency=(raw[split:],target[split:]))
    passed=all(x['passed'] for x in records)
    result=dict(status='PASS_FILE_LOCAL_ENDPOINT39_WITH_EXPOSED_CONSISTENCY' if passed else 'BLOCKED_NUMERIC_AMBIGUITY',source_file='c45.h5ad',source_revision=read(HERE/'PROTOCOL.json')['source_revision'],discovery_rows=discovery,consistency_rows=held,records=records,passed_coordinates=sum(x['passed'] for x in records),new_received_body_bytes=read(HERE/'C45_NUMERIC.json')['new_received_body_bytes'],new_network_requests=0,original_execution_error_preserved=True,fresh_holdout=False,P06_execution_released=False,model_axis_certified=False)
    write(HERE/'C45_NUMERIC_RECONSTRUCTED.json',result)
    print(json.dumps(dict(status=result['status'],passed_coordinates=result['passed_coordinates'],max_error=max(x['expected_max_error'] for x in records),new_network_requests=0)))


if __name__=='__main__':main()
