"""Reconstruct the proposed c45 support-discrimination panel offline."""
import json

import numpy as np
import pyarrow.parquet as pq
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix

from .audit import HERE, PRIOR, ROOT, Cached, binary_groups, read, sha, support_matches, write

PROPOSED = [135646,31154,31156,101840,122387,122427,92422,92442,92478,92543,120161]


def union(spans):
    merged=[]
    for a,b in sorted((int(a),int(b)) for a,b in spans):
        if merged and a<=merged[-1][1]+1:
            merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:
            merged.append((a,b))
    return merged


def uncovered(spans,cached):
    total=0
    for first,last in union(spans):
        cursor=first
        for left,right in union(cached):
            if right<cursor:continue
            if left>last:break
            total+=max(0,min(left,last+1)-cursor)
            cursor=max(cursor,right+1)
            if cursor>last:break
        total+=max(0,last-cursor+1)
    return total


def main():
    file='c45.h5ad'
    jobs=read(PRIOR/'INDEX_LAYOUTS.json')[file]
    groups=[g for g in read(PRIOR/'ROW_MANIFEST.json')['groups'] if g['file']==file]
    discovery=sorted(r for g in groups for r in g['discovery_rows'])
    heldout=sorted(r for g in groups for r in g['holdout_rows'])
    assert len(PROPOSED)==len(set(PROPOSED))==11
    assert not set(PROPOSED)&set(discovery+heldout)
    census=read(PRIOR/'CENSUSES.json')[file]
    protocol=read(PRIOR/'PROTOCOL.json')
    names=read(PRIOR/f'inputs/{file}_GENES.json')
    ids=[names.index(g) for g in protocol['endpoint']['symbols']]
    job_by_row={j['row']:j for j in jobs}
    exclusion=read(PRIOR/'inputs/EXCLUSIONS.json')
    controls=read(PRIOR/'inputs/CONTROL_PLAN.json')
    protected={r for g in controls['selected'] if g['file']==file for r in g['rows']}
    codes=np.load(PRIOR/f'inputs/{file}_CODES.npz',allow_pickle=False)
    samples={x['sample']:x for x in pq.read_table(PRIOR/'inputs/SAMPLES.parquet').to_pylist()}
    identities=[]
    categories=census['categories']
    for row in PROPOSED:
        job=job_by_row[row]
        group=next(g for g in groups if g['condition_id']==job['condition_id'])
        assert row in group['eligible_rows'] and row not in protected
        assert group['label'] not in exclusion['excluded_exact_sentinel_labels']
        assert categories['pass_filter'][int(codes['pass_filter'][row])]=='full'
        sample=categories['sample'][int(codes['sample'][row])]
        assert sample in group['samples'] and sample not in exclusion['excluded_pooled_sample_ids']
        assert samples[sample]['plate']==group['plate'] and samples[sample]['drugname_drugconc']==group['label']
        for key,want in [('drugname_drugconc',group['label']),('plate',group['plate']),('cell_line',group['cell_line_id'])]:
            assert categories[key][int(codes[key][row])]==want
        identities.append(dict(row=row,sample=sample,label=group['label'],plate=group['plate'],full_QC=True,condition_id=group['condition_id']))
    all_rows=[j['row'] for j in jobs]
    matrix=binary_groups(file,all_rows)
    loc={row:i for i,row in enumerate(all_rows)}
    old_indices=[loc[r] for r in discovery]
    aliases=support_matches(matrix[old_indices],ids)
    expanded=support_matches(matrix[[loc[r] for r in discovery+PROPOSED]],ids)
    assert all(x==[e] for x,e in zip(expanded,ids))
    candidates=[i for i,r in enumerate(all_rows) if r not in set(discovery+heldout)]
    pairs=[(e,c) for e,match in zip(ids,aliases) for c in match if c!=e]
    relevant=sorted({v for pair in pairs for v in pair})
    local={g:i for i,g in enumerate(relevant)}
    restricted=matrix[candidates][:,relevant].toarray()
    covering=csr_matrix(np.asarray([restricted[:,local[e]]!=restricted[:,local[c]] for e,c in pairs],dtype=np.float64))
    constraints=LinearConstraint(covering,np.ones(len(pairs)),np.full(len(pairs),np.inf))
    solved=milp(np.ones(len(candidates)),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=constraints,options={'time_limit':45,'mip_rel_gap':0.0})
    receipts=[dict(objective='minimum_added_cells',status=int(solved.status),message=solved.message,objective_value=float(solved.fun) if solved.fun is not None else None,dual_bound=float(solved.mip_dual_bound) if solved.x is not None else None,gap=float(solved.mip_gap) if solved.x is not None else None)]
    minimum_proven=solved.status==0 and round(solved.fun)==11
    costs=np.asarray([jobs[i]['nnz']*4+8000 for i in candidates],dtype=np.float64)
    fixed=LinearConstraint(csr_matrix(np.ones((1,len(candidates)))),[11],[11])
    cost_result=milp(costs,integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=[constraints,fixed],options={'time_limit':45,'mip_rel_gap':0.0})
    receipts.append(dict(objective='minimum_gross_payload_at11cells',status=int(cost_result.status),message=cost_result.message,objective_value=float(cost_result.fun) if cost_result.fun is not None else None,gap=float(cost_result.mip_gap) if cost_result.x is not None else None))
    source=Cached(file)
    cached=[(a,a+len(b)-1) for a,b in source.spans]
    value_spans=[s for r in PROPOSED for s in job_by_row[r]['values']]
    offset=census['layouts']['obsm/X_hvg']['offset']
    hvg_spans=[(offset+r*8000,offset+(r+1)*8000-1) for r in PROPOSED]
    value_bytes=uncovered(value_spans,cached)
    hvg_bytes=uncovered(hvg_spans,cached)
    assert value_bytes==45564 and hvg_bytes==88000
    exact_cost_optimal=cost_result.status==0 and round(cost_result.fun)==value_bytes+hvg_bytes
    output=dict(status='PASS_OFFLINE_PROPOSED_PANEL',source_file=file,source_revision=protocol['source_revision'],rows=PROPOSED,identities=identities,existing_discovery_rows=discovery,existing_consistency_rows=heldout,proposed_binary_unique_genes=sum(x==[e] for x,e in zip(expanded,ids)),candidate_genes=62710,alias_constraints=len(pairs),eligible_candidate_rows=len(candidates),new_CSR_value_bytes=value_bytes,new_complete_HVG_bytes=hvg_bytes,projected_new_body_bytes=value_bytes+hvg_bytes,minimum_count11_proven=minimum_proven,minimum_gross_payload_at11_proven=exact_cost_optimal,MILP=receipts,value_ranges=union(value_spans),HVG_ranges=union(hvg_spans),new_network_requests=0,new_values_read=False,binary_uniqueness_is_not_numeric_certification=True,old_consistency_cells_previously_exposed=True)
    write(HERE/'C45_SELECTION_VERIFIED.json',output)
    print(json.dumps({k:v for k,v in output.items() if k not in ['value_ranges','HVG_ranges','identities','existing_discovery_rows','existing_consistency_rows']}))


if __name__=='__main__':main()
