"""Separate blockwise numerical reconstruction; no acquisition/selector imports."""
import json
import numpy as np

from .audit import HERE, ROOT, check_freeze, lines, read, sha, vectors, write


def compare_all(names,raw,target,symbols,held=None):
    records=[]
    for column,symbol in enumerate(symbols):
        found=[]
        for start in range(0,len(names),2048):
            errors=np.abs(raw[:,start:start+2048]-target[:,column,None]).max(axis=0)
            found.extend((np.flatnonzero(errors<=1e-5)+start).tolist())
        index=names.index(symbol)
        checks=dict(matches=found,nonzero=int((np.abs(target[:,column])>1e-5).sum()),error=float(np.abs(raw[:,index]-target[:,column]).max()))
        if held is not None:
            checks.update(held_nonzero=int((np.abs(held[1][:,column])>1e-5).sum()),held_error=float(np.abs(held[0][:,index]-held[1][:,column]).max()))
        checks['passed']=found==[index] and names.count(symbol)==1 and checks['nonzero']>=2
        if held is not None:checks['passed'] &= checks['held_nonzero']>=1 and checks['held_error']<=1e-5
        records.append(checks)
    return records


def main():
    check_freeze(HERE/'C44_FREEZE.json')
    check_freeze(HERE/'C45_FREEZE.json')
    p=read(HERE/'PROTOCOL.json')
    old=read(HERE/'PRIOR_SNAPSHOT.json')
    for name,expected in old['sha256'].items():assert sha(ROOT/name)==expected,name
    c44=read(HERE/'C44_UNION.json')
    c45=read(HERE/'C45_NUMERIC.json')
    cert=read(HERE/'CERTIFICATE.json')
    assert cert['c44_record_sha256']==sha(HERE/'C44_UNION.json')
    assert cert['c45_record_sha256']==sha(HERE/'C45_NUMERIC.json')
    files=[]
    for file,record in [('c44.h5ad',c44),('c45.h5ad',c45)]:
        rows=record['rows'] if file=='c44.h5ad' else record['discovery_rows']+record['consistency_rows']
        names,raw,target=vectors(file,rows,extension=file=='c45.h5ad')
        if file=='c44.h5ad':
            reconstructed=compare_all(names,raw,target,p['endpoint']['symbols'])
        else:
            split=len(record['discovery_rows'])
            reconstructed=compare_all(names,raw[:split],target[:split],p['endpoint']['symbols'],held=(raw[split:],target[split:]))
        for expected,actual in zip(record['records'],reconstructed):
            assert expected['matching_source_indices']==actual['matches']
            assert expected['nonzero_cells']==actual['nonzero']
            assert expected['expected_max_error']==actual['error']
            assert expected['passed']==actual['passed']
            if file=='c45.h5ad':
                assert expected['consistency_nonzero_cells']==actual['held_nonzero']
                assert expected['consistency_max_error']==actual['held_error']
        assert all(x['passed'] for x in reconstructed)
        files.append(dict(file=file,passed_coordinates=39,maximum_error=max(x['error'] for x in reconstructed)))
    plan=read(HERE/'C45_SELECTION_VERIFIED.json')
    permitted={tuple(x) for k in ['value_ranges','HVG_ranges'] for x in plan[k]}
    ledger=lines(HERE/'NETWORK.jsonl')
    for row in ledger:
        if row['status']=='HEAD':assert row['bytes']==0;continue
        assert row['status']=='RETAINED' and (row['start'],row['end']) in permitted
        assert row['bytes']==row['end']-row['start']+1
    charged=sum(x['bytes'] for x in ledger)
    assert charged==c45['new_received_body_bytes']==plan['projected_new_body_bytes']==133564
    assert charged<=p['new_received_body_cap_bytes']
    assert not cert['fresh_holdout'] and not cert['P06_execution_released'] and not cert['STATE_checkpoint_axis_certified']
    result=dict(status='PASS_SEPARATE_BLOCKWISE_ARITHMETIC_RECONSTRUCTION',files=files,new_body_bytes=charged,prior_snapshot_files=len(old['sha256']),prior_files_unchanged=True,new_network_requests=0,imports_numeric_producer=False,independent_subagent_run=False,shared_retained_byte_reader=True,fresh_biological_validation=False,P06_execution_released=False,P2_released=False,verifier_sha256=sha(HERE/'verify.py'))
    write(HERE/'VERIFIED.json',result)
    print(json.dumps(result))


if __name__=='__main__':main()
