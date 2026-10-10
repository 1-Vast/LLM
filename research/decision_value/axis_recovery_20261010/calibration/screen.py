"""Frozen index-only information screen, deterministic allocation and paired freeze."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np

try:
    from .storage import HERE, Source, merge_adjacent, sha, read_rows, write
except ImportError:
    from storage import HERE, Source, merge_adjacent, sha, read_rows, write


def check_freeze(name):
    frozen = json.loads((HERE/name).read_text())
    for path, digest in frozen['sha256'].items():
        if sha(HERE/path) != digest: raise RuntimeError('frozen_input_changed: '+path)


def allocate(file, groups, jobs, presence, protocol):
    """A bounded heuristic; an allocation failure is not proof of infeasibility."""
    total = presence.sum(axis=0).astype(int)
    summary = dict(index_occurrences_per_gene=total.tolist(), method='rare-cover heuristic; not globally optimal',
                   necessary_support_count_below_three=np.flatnonzero(total<3).tolist())
    if np.any(total<3):
        return None, dict(summary, status='BLOCKED/NECESSARY_INDEX_SUPPORT_BELOW_THREE')
    available = set(range(len(jobs)))
    counts = {role:np.zeros(presence.shape[1], dtype=int) for role in ('discovery','holdout')}
    selected = {role:[] for role in counts}
    quotas = {(role,g['condition_id']):0 for role in counts for g in groups}
    remaining = total.copy()

    def tie(index, role):
        job = jobs[index]
        group = next(g for g in groups if g['condition_id']==job['condition_id'])
        key = f"{protocol['hash_seed']}|{file}|{role}|{group['label']}|{','.join(group['samples'])}|{job['row']}"
        return hashlib.sha256(key.encode()).hexdigest()

    def take(index, role):
        available.remove(index)
        remaining[:] -= presence[index]
        counts[role][:] += presence[index]
        quotas[(role,jobs[index]['condition_id'])] += 1
        selected[role].append(index)

    # Reserve a separate holdout hit while leaving two possible discovery hits.
    for role,target in [('holdout',1),('discovery',2)]:
        while np.any(counts[role]<target):
            ranked = []
            for index in available:
                if quotas[(role,jobs[index]['condition_id'])] >= 16: continue
                if role=='holdout' and np.any(remaining-presence[index]<2): continue
                needed = np.flatnonzero(presence[index] & (counts[role]<target))
                score = sum((Fraction(1,int(total[g])) for g in needed), Fraction(0))
                if score: ranked.append((-score,tie(index,role),index))
            if not ranked:
                return None, dict(summary, status='BLOCKED/INDEX_ALLOCATION_HEURISTIC_FAILURE',
                    discovery_coverage=counts['discovery'].tolist(), holdout_coverage=counts['holdout'].tolist(),
                    note='This frozen heuristic failed; no claim that every feasible allocation is excluded.')
            take(min(ranked)[2],role)
    # Fill after coverage reservation so arbitrary hash cells cannot consume rare hits.
    for role in ('discovery','holdout'):
        for group in groups:
            choices = sorted((i for i in available if jobs[i]['condition_id']==group['condition_id']),key=lambda i:tie(i,role))
            need = 16-quotas[(role,group['condition_id'])]
            if len(choices)<need: raise RuntimeError('insufficient_disjoint_quota_cells')
            for index in choices[:need]: take(index,role)
    out = []
    for group in groups:
        item = dict(group)
        item['discovery_rows'] = sorted(jobs[i]['row'] for i in selected['discovery'] if jobs[i]['condition_id']==group['condition_id'])
        item['holdout_rows'] = sorted(jobs[i]['row'] for i in selected['holdout'] if jobs[i]['condition_id']==group['condition_id'])
        out.append(item)
    return out, dict(summary,status='INDEX_ALLOCATION_READY',discovery_index_coverage=counts['discovery'].tolist(),
        holdout_index_coverage=counts['holdout'].tolist(), index_presence_does_not_certify_nonzero_expression=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',required=True,help='Run only after parent reviews INDEX_FREEZE')
    parser.parse_args()
    if (HERE/'INDEX_RESULTS.json').exists(): raise FileExistsError('Index stage refuses overwrite')
    check_freeze('INDEX_FREEZE.json')
    protocol=json.loads((HERE/'PROTOCOL.json').read_text())
    census=json.loads((HERE/'CENSUSES.json').read_text())
    layouts=json.loads((HERE/'INDEX_LAYOUTS.json').read_text())
    groups=json.loads((HERE/'QC_ROWS.json').read_text())['groups']
    manifests,results=[],[]
    for file in protocol['source_files']:
        jobs=layouts[file]
        source=Source(file,census[file]['file_bytes'],network=True,stage='index_screen')
        names=json.loads((HERE/'inputs'/f'{file}_GENES.json').read_text())
        indices=[names.index(g) for g in protocol['endpoint']['symbols']]
        spans=merge_adjacent([span for job in jobs for span in job['indices']])
        print('Index-only calibration screen: '+file,flush=True)
        for a,b in spans: source.fetch(a,b,'index_screen_CSR_indices')
        presence=np.zeros((len(jobs),len(indices)),dtype=bool)
        for i,job in enumerate(jobs):
            body=b''.join(source.fetch(a,b,'index_screen_CSR_indices') for a,b in job['indices'])
            array=np.frombuffer(body,dtype=census[file]['layouts']['X/indices']['dtype'])
            if len(array)!=job['nnz'] or len(np.unique(array))!=len(array) or np.any(array<0) or np.any(array>=len(names)):
                raise RuntimeError('invalid_or_duplicate_selected_CSR_indices')
            presence[i]=np.isin(indices,array)
        np.savez_compressed(HERE/f'{file}_PRESENCE.npz',rows=np.array([j['row'] for j in jobs]),presence=presence,
            source_gene_indices=np.array(indices))
        chosen,result=allocate(file,[g for g in groups if g['file']==file],jobs,presence,protocol)
        results.append(dict(file=file,**result))
        if chosen is not None: manifests.extend(chosen)
    ready=all(r['status']=='INDEX_ALLOCATION_READY' for r in results)
    write(HERE/'INDEX_RESULTS.json',dict(schema='finite_CSR_index_screen_results_v1',status='READY_FOR_PAIRED_FREEZE' if ready else 'BLOCKED/INDEX_INFORMATION',
        files=results,screened_calibration_cells=sum(len(jobs) for jobs in layouts.values()),
        cumulative_new_body_bytes=sum(r.get('bytes',0) for r in read_rows(HERE/'NETWORK.jsonl')),
        raw_values_read=False,X_hvg_read=False,P06_sentinel_RNA_read=False))
    if ready:
        write(HERE/'ROW_MANIFEST.json',dict(schema='frozen_paired_calibration_rows_v1',groups=manifests,
            selected_cells=sum(len(g['discovery_rows'])+len(g['holdout_rows']) for g in manifests),
            selection_is_index_presence_guided=True,not_independent_biological_decision_validation=True))
        for old,new in [('NETWORK.jsonl','INDEX_NETWORK.jsonl'),('CACHE_REUSE.jsonl','INDEX_CACHE_REUSE.jsonl')]:
            (HERE/new).write_bytes((HERE/old).read_bytes() if (HERE/old).exists() else b'')
        files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['NETWORK.jsonl','CACHE_REUSE.jsonl','PAIR_FREEZE.json']]
        write(HERE/'PAIR_FREEZE.json',dict(schema='paired_expression_calibration_freeze_v1',raw_values_and_HVG_read=False,
            index_screen_freeze_sha256=sha(HERE/'INDEX_FREEZE.json'),sha256={p.relative_to(HERE).as_posix():sha(p) for p in sorted(files)}))
    print(json.dumps(dict(status='PAIR_FREEZE_READY_FOR_PARENT_REVIEW' if ready else 'BLOCKED/INDEX_INFORMATION',
        files=[dict(file=r['file'],status=r['status']) for r in results])),flush=True)


if __name__=='__main__': main()
