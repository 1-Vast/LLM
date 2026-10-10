"""Offline support-pattern diagnosis; does not certify axes or request expression."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

HERE=Path(__file__).resolve().parent
STAGE=HERE.parent


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def lines(path):return [json.loads(line) for line in path.read_text().splitlines()]


def input_files():
    names=['INDEX_LAYOUTS.json','QC_ROWS.json','ROW_MANIFEST.json','RESULTS.json','CENSUSES.json',
           'PROTOCOL.json','NETWORK.jsonl','CACHE_REUSE.jsonl','INDEX_FREEZE.json','PAIR_FREEZE.json']
    paths=[STAGE/name for name in names]
    paths += [STAGE/'inputs'/f'{file}_GENES.json' for file in ['c44.h5ad','c45.h5ad']]
    # Retain references to index bodies only: no CSR values or hidden-vector bodies.
    for row in lines(STAGE/'NETWORK.jsonl')+lines(STAGE/'CACHE_REUSE.jsonl'):
        purpose=row.get('purpose',row.get('original_receipt',{}).get('purpose',''))
        if row['status'] in ['RETAINED','REUSED'] and purpose.startswith('index_screen_'):
            paths.append(STAGE/row['path'])
    return sorted(set(paths))


def freeze():
    if (HERE/'FREEZE.json').exists():raise FileExistsError('Diagnostic freeze exists')
    protocol=dict(schema='offline_index_discrimination_diagnostic_v1',
        primary='Compare support-pattern uniqueness of each expectedgene among all actual62710 sourcegenes in currentdiscovery and fullretainedindexpool',
        repair='Keep existingdiscovery+holdout fixed; greedily add discovery-only rows separating binarysupport competitors, within80discovery/file; noquota filling',
        greedy_score='Sum removed competitors divided by current competitor count for each endpoint; exact Fraction. Tie lower projectedCSRvalue+HVG bytes then SHA256(seed|file|row).',
        seed='p05r-index-identity-discrimination-diagnostic-v1',
        maximum_discovery_cells_per_file=80,maximum_holdout_cells_per_file=48,
        data='Existing retained indices, source-name dictionaries, frozen rows and numerical ambiguity counts only; rawvalues/HVG not read or requested',
        limitations=['Index presence is not a nonzero numerical value','Binary uniqueness is not RNA axis certification',
            'Greedy repair is not globally minimal/optimal','Observed outcomes motivated this diagnostic; not independent evaluation',
            'No new observations, revised frozen certificate or P0.6 release'],
        new_network_calls=0,new_expression_value_reads=0,new_HVG_reads=0,axis_gate_or_efficacy_claim=False)
    (HERE/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2)+'\n')
    paths=input_files()+[Path(__file__),HERE/'PROTOCOL.json']
    (HERE/'FREEZE.json').write_text(json.dumps(dict(schema='offline_diagnostic_input_freeze_v1',
        sha256={p.relative_to(HERE.parent).as_posix():sha(p) for p in paths}),indent=2)+'\n')
    print(json.dumps(dict(status='OFFLINE_DIAGNOSTIC_FROZEN',index_and_metadata_inputs=len(paths))))


class IndexSource:
    def __init__(self,file):
        self.spans=[]
        for row in lines(STAGE/'NETWORK.jsonl')+lines(STAGE/'CACHE_REUSE.jsonl'):
            purpose=row.get('purpose',row.get('original_receipt',{}).get('purpose',''))
            if row['file']==file and row['status'] in ['RETAINED','REUSED'] and purpose.startswith('index_screen_'):
                body=(STAGE/row['path']).read_bytes()
                if len(body)!=row['bytes'] or hashlib.sha256(body).hexdigest()!=row['sha256']:
                    raise ValueError('Index payload hash mismatch')
                self.spans.append((row['start'],body))
        self.spans.sort(key=lambda x:x[0])

    def at(self,first,last):
        parts,cursor=[],first
        for start,body in self.spans:
            if start>cursor:break
            stop=min(last+1,start+len(body))
            if stop>cursor:
                parts.append(body[cursor-start:stop-start]);cursor=stop
            if cursor==last+1:return b''.join(parts)
        raise ValueError('Unretained index-only span')


def union(spans):
    out=[]
    for a,b in sorted((int(a),int(b)) for a,b in spans):
        if out and a<=out[-1][1]+1:out[-1]=(out[-1][0],max(b,out[-1][1]))
        else:out.append((a,b))
    return out


def missing_bytes(spans,cached):
    total=0
    for a,b in union(spans):
        cursor=a
        for left,right in union(cached):
            if right<cursor:continue
            if left>b:break
            if left>cursor:total+=left-cursor
            cursor=max(cursor,right+1)
            if cursor>b:break
        if cursor<=b:total+=b-cursor+1
    return total


def patterns(matrix,rows,expected):
    csc=matrix[rows].tocsc()
    signatures=[csc.indices[csc.indptr[j]:csc.indptr[j+1]].tobytes() for j in range(matrix.shape[1])]
    grouped={}
    for j,pattern in enumerate(signatures):grouped.setdefault(pattern,[]).append(j)
    return [grouped[signatures[index]] for index in expected]


def run():
    if (HERE/'RESULTS.json').exists():raise FileExistsError('Diagnostic result exists')
    for path,digest in read(HERE/'FREEZE.json')['sha256'].items():
        if sha(STAGE/path)!=digest:raise ValueError('Frozen input mismatch: '+path)
    protocol=read(STAGE/'PROTOCOL.json')
    diagnostic=read(HERE/'PROTOCOL.json')
    layouts=read(STAGE/'INDEX_LAYOUTS.json')
    manifests=read(STAGE/'ROW_MANIFEST.json')['groups']
    numerical={r['file']:r for r in read(STAGE/'RESULTS.json')['files']}
    census=read(STAGE/'CENSUSES.json')
    results=[]
    ledger=lines(STAGE/'NETWORK.jsonl')+lines(STAGE/'CACHE_REUSE.jsonl')
    for file,jobs in layouts.items():
        names=read(STAGE/'inputs'/f'{file}_GENES.json')
        expected=[names.index(symbol) for symbol in protocol['endpoint']['symbols']]
        source=IndexSource(file)
        row_indices=[];pointer=[0]
        for job in jobs:
            idx=np.frombuffer(b''.join(source.at(a,b) for a,b in job['indices']),dtype='<i4')
            if len(idx)!=job['nnz'] or len(np.unique(idx))!=len(idx):raise ValueError('Invalid retained index row')
            row_indices.append(idx.copy());pointer.append(pointer[-1]+len(idx))
        all_indices=np.concatenate(row_indices)
        matrix=csr_matrix((np.ones(len(all_indices),dtype=bool),all_indices,np.array(pointer,dtype=np.int64)),shape=(len(jobs),len(names)))
        matrix.sort_indices()
        row_lookup={job['row']:i for i,job in enumerate(jobs)}
        old_discovery={r for g in manifests if g['file']==file for r in g['discovery_rows']}
        old_holdout={r for g in manifests if g['file']==file for r in g['holdout_rows']}
        discovery=[row_lookup[r] for r in sorted(old_discovery)]
        selected=patterns(matrix,discovery,expected)
        full=patterns(matrix,np.arange(len(jobs)),expected)
        # Competitors with equal current support may still differ numerically; this is a conservative proxy.
        competing=[set(x)-{idx} for x,idx in zip(selected,expected)]
        candidates=set(range(len(jobs)))-set(discovery)-{row_lookup[r] for r in old_holdout}
        added=[]
        traces=[]
        while any(competing) and len(discovery)+len(added)<diagnostic['maximum_discovery_cells_per_file']:
            ranked=[]
            relevant=set(expected)|set().union(*competing)
            for index in candidates:
                present=set(row_indices[index])&relevant
                removed=[{gene for gene in rivals if (gene in present)!=(exp in present)} for exp,rivals in zip(expected,competing)]
                score=sum((Fraction(len(gone),len(rivals)) for gone,rivals in zip(removed,competing) if rivals),Fraction(0))
                if not score:continue
                cost=jobs[index]['nnz']*4+8000
                tie=hashlib.sha256(f"{diagnostic['seed']}|{file}|{jobs[index]['row']}".encode()).hexdigest()
                ranked.append((-score,cost,tie,index,removed))
            if not ranked:break
            _,_,_,index,removed=min(ranked,key=lambda x:x[:4])
            candidates.remove(index);added.append(index)
            traces.append(dict(row=jobs[index]['row'],separated_competitors=sum(map(len,removed)),
                separated_endpoint_genes=sum(bool(x) for x in removed),presence_only_not_numerical_truth=True))
            competing=[rivals-gone for rivals,gone in zip(competing,removed)]
        after=patterns(matrix,discovery+added,expected)
        added_rows=[jobs[i]['row'] for i in added]
        cached=[(r['start'],r['end']) for r in ledger if r['file']==file and r['status'] in ['RETAINED','REUSED']]
        offset=census[file]['layouts']['obsm/X_hvg']['offset']
        value_cost=missing_bytes([span for i in added for span in jobs[i]['values']],cached)
        hvg_cost=missing_bytes([(offset+r*8000,offset+(r+1)*8000-1) for r in added_rows],cached)
        detail=[]
        for k,(symbol,index) in enumerate(zip(protocol['endpoint']['symbols'],expected)):
            detail.append(dict(symbol=symbol,source_gene_index=index,
                numeric_registered_discovery_match_count=numerical[file]['endpoint_records'][k]['discovery_matching_source_gene_count'],
                registered_coordinate_passed=numerical[file]['endpoint_records'][k]['passed'],
                binary_current_discovery_match_count=len(selected[k]),binary_full_pool_match_count=len(full[k]),
                binary_diagnostic_augmented_match_count=len(after[k]),
                current_binary_competitor_names=[names[j] for j in selected[k] if j!=index],
                unresolved_full_pool_competitor_names=[names[j] for j in full[k] if j!=index]))
        results.append(dict(file=file,index_pool_cells=len(jobs),source_genes=len(names),
            current_discovery_cells=len(discovery),fixed_holdout_cells=len(old_holdout),
            current_binary_unique_endpoint_genes=sum(len(x)==1 for x in selected),
            full_pool_binary_unique_endpoint_genes=sum(len(x)==1 for x in full),
            diagnostic_augmented_binary_unique_endpoint_genes=sum(len(x)==1 for x in after),
            added_discovery_cells=len(added),added_discovery_rows=added_rows,
            augmented_discovery_cells=len(discovery)+len(added),maximum_discovery_cells=80,
            existing_holdout_preserved=True,additional_CSR_value_bytes_projected_only=value_cost,
            additional_HVG_bytes_projected_only=hvg_cost,allocation_trace=traces,endpoint_records=detail))
    old_total=read(STAGE/'RESULTS.json')['combined_calibration_body_bytes']
    projected=sum(r['additional_CSR_value_bytes_projected_only']+r['additional_HVG_bytes_projected_only'] for r in results)
    out=dict(schema='offline_binary_index_discrimination_results_v1',status='DIAGNOSIS_ONLY_NO_AXIS_CERTIFICATION',files=results,
        existing_combined_calibration_known_bytes=old_total,additional_paired_body_bytes_projected_only=projected,
        hypothetical_combined_total_bytes=old_total+projected,new_network_calls=0,new_CSR_value_reads=0,new_HVG_reads=0,
        original_blocked_certificates_unchanged=True,P06_released=False,axis_certification=False,decision_effectiveness_claim=False)
    (HERE/'RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(status=out['status'],files=[dict(file=r['file'],current_unique=r['current_binary_unique_endpoint_genes'],
        full_pool_unique=r['full_pool_binary_unique_endpoint_genes'],augmented_unique=r['diagnostic_augmented_binary_unique_endpoint_genes'],
        extra_discovery=r['added_discovery_cells']) for r in results],projected_only_extra_bytes=projected)))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true')
    args=parser.parse_args()
    freeze() if args.freeze else run()
