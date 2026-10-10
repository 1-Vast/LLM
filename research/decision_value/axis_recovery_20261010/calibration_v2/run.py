"""Execute frozen exact paired vectors; authenticate endpoint coordinates per file."""
import json

import numpy as np

try:
    from .storage import HERE, PRIOR_SPENT, Source, merge_adjacent, sha, read_rows, write
    from .screen import check_freeze
except ImportError:
    from storage import HERE, PRIOR_SPENT, Source, merge_adjacent, sha, read_rows, write
    from screen import check_freeze


def authenticate(file, protocol, census, manifest, layouts):
    groups=[g for g in manifest['groups'] if g['file']==file]
    discovery=sorted({r for g in groups for r in g['discovery_rows']})
    holdout=sorted({r for g in groups for r in g['holdout_rows']})
    if set(discovery)&set(holdout): raise RuntimeError('discovery_holdout_overlap')
    selected=sorted(discovery+holdout)
    jobs={j['row']:j for j in layouts[file]}
    names=json.loads((HERE/'inputs'/f'{file}_GENES.json').read_text())
    source=Source(file,census[file]['file_bytes'],network=True,stage='expression')
    offset=census[file]['layouts']['obsm/X_hvg']['offset']
    width=np.dtype(census[file]['layouts']['obsm/X_hvg']['dtype']).itemsize*2000
    value_spans=merge_adjacent([span for row in selected for span in jobs[row]['values']])
    for a,b in value_spans: source.fetch(a,b,'expression_selected_CSR_values')
    for a,b in merge_adjacent([(offset+r*width,offset+(r+1)*width-1) for r in selected]):
        source.fetch(a,b,'expression_selected_complete_X_hvg')
    raw,stored=[],[]
    for row in selected:
        job=jobs[row]
        idx=np.frombuffer(b''.join(source.fetch(a,b,'selected_CSR_indices_metadata') for a,b in job['indices']),dtype=census[file]['layouts']['X/indices']['dtype'])
        val=np.frombuffer(b''.join(source.fetch(a,b,'expression_selected_CSR_values') for a,b in job['values']),dtype=census[file]['layouts']['X/data']['dtype'])
        if len(idx)!=len(val) or len(np.unique(idx))!=len(idx) or np.any(idx<0) or np.any(idx>=len(names)):
            raise RuntimeError('invalid_selected_CSR_indices')
        if not np.isfinite(val).all() or np.any(val<0): raise RuntimeError('invalid_stored_expression')
        vector=np.zeros(len(names),dtype=np.float64)
        vector[idx]=val
        raw.append(np.log1p(vector))
        hvg=np.frombuffer(source.fetch(offset+row*width,offset+(row+1)*width-1,'expression_selected_complete_X_hvg'),dtype=census[file]['layouts']['obsm/X_hvg']['dtype'])
        if len(hvg)!=2000 or not np.isfinite(hvg).all() or np.any(hvg<0): raise RuntimeError('invalid_stored_hvg')
        stored.append(hvg.astype(np.float64))
    raw,stored=np.array(raw),np.array(stored)
    d=np.array([i for i,row in enumerate(selected) if row in set(discovery)])
    h=np.array([i for i,row in enumerate(selected) if row in set(holdout)])
    records=[]
    tolerance=protocol['absolute_tolerance']
    for coordinate,gene in zip(protocol['endpoint']['coordinates'],protocol['endpoint']['symbols']):
        target=stored[d,coordinate]
        possible=np.arange(len(names))
        for row in np.argsort(-np.abs(target)):
            possible=possible[np.abs(raw[d[row],possible]-target[row])<=tolerance]
            if not len(possible): break
        index=int(possible[0]) if len(possible)==1 else None
        dn=int((np.abs(target)>tolerance).sum())
        hn=int((np.abs(stored[h,coordinate])>tolerance).sum())
        dm=float(np.max(np.abs(raw[d,index]-target))) if index is not None else None
        hm=float(np.max(np.abs(raw[h,index]-stored[h,coordinate]))) if index is not None else None
        passed=(index is not None and names[index]==gene and names.count(gene)==1 and dn>=2 and hn>=1 and hm<=tolerance)
        records.append(dict(coordinate=coordinate,expected_symbol=gene,discovery_matching_source_gene_count=len(possible),
            discovery_unique_source_gene_index=index,discovery_source_symbol=names[index] if index is not None else None,
            source_symbol_duplicate_count=names.count(gene),discovery_nonzero_cells=dn,holdout_nonzero_cells=hn,
            discovery_max_abs_mismatch=dm,holdout_max_abs_mismatch=hm,
            discovery_passed=index is not None and names[index]==gene and dn>=2,
            holdout_passed=index is not None and hn>=1 and hm<=tolerance,passed=bool(passed)))
    return dict(file=file,discovery_rows=discovery,holdout_rows=holdout,source_gene_count=len(names),
        discovery_cells=len(discovery),holdout_cells=len(holdout),endpoint_records=records,
        passed=all(r['passed'] for r in records),identity_scope='39 declared coordinates for this file only',
        same_source_cell_split='disjoint cells with actual sample IDs preserved; not culture-level independent validation',independent_culture_or_checkpoint_axis_certified=False)


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',required=True,help='Use only after parent reviews PAIR_FREEZE')
    parser.parse_args()
    if (HERE/'RESULTS.json').exists(): raise FileExistsError('Paired stage refuses overwrite')
    check_freeze('INDEX_FREEZE.json')
    check_freeze('PAIR_FREEZE.json')
    protocol=json.loads((HERE/'PROTOCOL.json').read_text())
    census=json.loads((HERE/'CENSUSES.json').read_text())
    manifest=json.loads((HERE/'ROW_MANIFEST.json').read_text())
    layouts=json.loads((HERE/'INDEX_LAYOUTS.json').read_text())
    results,error=[],None
    try:
        for file in protocol['source_files']:
            print('Frozen paired coordinate authentication: '+file,flush=True)
            results.append(authenticate(file,protocol,census,manifest,layouts))
    except Exception as exc:
        error=dict(type=type(exc).__name__,reason=str(exc))
    passed=len(results)==2 and all(r['passed'] for r in results) and error is None
    body_bytes=sum(r.get('bytes',0) for r in read_rows(HERE/'NETWORK.jsonl'))
    status='PASS/FILE_LOCAL_ENDPOINT39' if passed else 'BLOCKED/INSUFFICIENT_COORDINATE_INFORMATION'
    write(HERE/'RESULTS.json',dict(schema='finite_informative_axis_results_v1',status=status,files=results,error=error,
        actual_new_body_bytes=body_bytes,total_response_cap_bytes=protocol['total_response_body_cap_bytes'],
        prior_stage_known_body_bytes=PRIOR_SPENT,combined_calibration_body_bytes=PRIOR_SPENT+body_bytes,adaptive_design=True,maximum_supplements=1,
        calibration_treated_expression_requested=True,P06_sentinel_RNA_read=False,old250_noise_rows_read=False,
        full2000_axis_certified=False,STATE_checkpoint_axis_certified=False,decision_effectiveness_test=False))
    write(HERE/'CERTIFICATE.json',dict(schema='two_stage_file_local_endpoint_axis_certificate_v1',status=status,
        endpoint39_verified=passed,per_file_endpoint39_verified={r['file']:r['passed'] for r in results},
        source_repo=protocol['source_repo'],source_revision=protocol['source_revision'],source_files=protocol['source_files'],
        scope='Each c44/c45 file separately; not c40, all2000, checkpoint decoder, independent biological decision validation',
        transform=protocol['transform'],index_freeze_sha256=sha(HERE/'INDEX_FREEZE.json'),
        paired_freeze_sha256=sha(HERE/'PAIR_FREEZE.json'),results_sha256=sha(HERE/'RESULTS.json'),
        endpoint_sha256=sha(HERE/'inputs/ENDPOINT.json'),STATE_checkpoint_axis_certified=False))
    print(json.dumps(dict(status=status,body_bytes=body_bytes,files=[dict(file=r['file'],passed=sum(z['passed'] for z in r['endpoint_records'])) for r in results],error=error)),flush=True)


if __name__=='__main__': main()
