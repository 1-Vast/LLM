"""One bounded adaptive supplement; metadata only before the new index freeze."""
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq

try:
    from .storage import HERE,ROOT,CAP,PRIOR_SPENT,STAGE1,Source,physical_spans,merge_adjacent,sha,read_rows,write
except ImportError:
    from storage import HERE,ROOT,CAP,PRIOR_SPENT,STAGE1,Source,physical_spans,merge_adjacent,sha,read_rows,write


def copy_input(source,name):
    target=HERE/'inputs'/name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(source.read_bytes())
    return dict(path=target.relative_to(HERE).as_posix(),sha256=sha(target),bytes=target.stat().st_size,
                original_path=source.relative_to(ROOT).as_posix())


def uncovered_bytes(spans,cached):
    total=0
    for first,last in merge_adjacent(spans):
        cursor=first
        for left,right in merge_adjacent(cached):
            if right<cursor:continue
            if left>last:break
            if left>cursor:total+=min(left,last+1)-cursor
            cursor=max(cursor,right+1)
            if cursor>last:break
        if cursor<=last:total+=last-cursor+1
    return total


def main():
    if (HERE/'INDEX_FREEZE.json').exists():raise FileExistsError('Supplement freeze exists')
    selection_root=HERE.parent/'informative_v2/cost_review/full_cover'
    selection=json.loads((selection_root/'SELECTION.json').read_text())
    amendment=json.loads((HERE.parent/'ADAPTIVE_AMENDMENT.json').read_text())
    stage1_result=json.loads((STAGE1/'INDEX_RESULTS.json').read_text())
    if stage1_result['cumulative_new_body_bytes']!=PRIOR_SPENT or amendment['known_before_design']['first_index_result_sha256']!=sha(STAGE1/'INDEX_RESULTS.json'):
        raise RuntimeError('adaptive_trigger_or_spending_mismatch')
    old_qc=json.loads((STAGE1/'QC_ROWS.json').read_text())
    old_protocol=json.loads((STAGE1/'PROTOCOL.json').read_text())
    for key in ['quota_per_role_condition','worst_case_selected_value_bytes','planned_HVG_bytes',
                'reserved_future_metadata_and_fail_body_bytes','projected_total_response_bytes']:
        old_protocol.pop(key,None)
    old_selection=json.loads((STAGE1/'inputs/SELECTION.json').read_text())
    combined=dict(selection,selected=old_selection['selected']+selection['selected'])
    (HERE/'inputs').mkdir(exist_ok=True)
    combined_path=HERE/'inputs/SELECTION.json'
    if combined_path.exists():
        if json.loads(combined_path.read_text())!=combined:raise RuntimeError('supplementary_selection_changed_after_preparation')
    else:
        write(combined_path,combined)
    records=[dict(path='inputs/SELECTION.json',sha256=sha(combined_path),bytes=combined_path.stat().st_size,
                  original_path=None,derivation='Frozen stage1 selected conditions plus one frozen supplementary selection')]
    for source,name in [(selection_root/'SELECTION.json','SUPPLEMENTARY_SELECTION.json'),
                        (selection_root/'FREEZE.json','INFORMATIVE_V2_FREEZE.json'),
                        (HERE.parent/'ADAPTIVE_AMENDMENT.json','ADAPTIVE_AMENDMENT.json'),
                        (HERE.parent/'BUDGET_AMENDMENT.json','BUDGET_AMENDMENT.json'),
                        (STAGE1/'INDEX_FREEZE.json','PRIOR_INDEX_FREEZE.json'),
                        (STAGE1/'INDEX_RESULTS.json','PRIOR_INDEX_RESULTS.json'),
                        (STAGE1/'QC_ROWS.json','PRIOR_QC_ROWS.json')]:
        records.append(copy_input(source,name))
    for name in ['EXCLUSIONS.json','ENDPOINT.json','CONTROL_PLAN.json','SOURCE_QUALIFICATION.json','SAMPLES.parquet']:
        records.append(copy_input(STAGE1/'inputs'/name,name))
    censuses=json.loads((STAGE1/'CENSUSES.json').read_text())
    exclusions=json.loads((HERE/'inputs/EXCLUSIONS.json').read_text())
    noise=json.loads((HERE/'inputs/CONTROL_PLAN.json').read_text())
    protected_rows={(g['file'],int(r)) for g in noise['selected'] for r in g['rows']}
    sample_table=pq.read_table(HERE/'inputs/SAMPLES.parquet').to_pandas().set_index('sample',verify_integrity=True)
    groups=list(old_qc['groups'])
    layouts=json.loads((STAGE1/'INDEX_LAYOUTS.json').read_text())
    genes_meta,codes_meta,seeds={}, {}, {}
    projected_fresh_index=0
    for file,census in censuses.items():
        for suffix in ['GENES.json','CODES.npz','POINTERS.npy','CENSUS_SEED.json']:
            records.append(copy_input(STAGE1/'inputs'/f'{file}_{suffix}',f'{file}_{suffix}'))
        gene_path=HERE/'inputs'/f'{file}_GENES.json'
        genes_meta[file]=dict(path=gene_path.relative_to(HERE).as_posix(),sha256=sha(gene_path),count=census['source_gene_count'])
        code_path=HERE/'inputs'/f'{file}_CODES.npz'
        codes_meta[file]=dict(path=code_path.relative_to(HERE).as_posix(),sha256=sha(code_path))
        seed_path=HERE/'inputs'/f'{file}_CENSUS_SEED.json'
        seeds[file]=dict(path=seed_path.relative_to(HERE).as_posix(),sha256=sha(seed_path),git_commit='91b0c10')
        census['pointer_path']=f'inputs/{file}_POINTERS.npy'
        ptr=np.load(HERE/census['pointer_path'],allow_pickle=False)
        with np.load(code_path,allow_pickle=False) as arrays:
            values={key:arrays[key].copy() for key in arrays.files}
        cats=census['categories']
        source=Source(file,census['file_bytes'],network=True)
        new_groups=[g for g in selection['selected'] if g['file']==file]
        if len(new_groups)>8:raise RuntimeError('supplement_condition_limit')
        with h5py.File(source,'r') as h5:
            for number,g in enumerate(new_groups):
                if g['label'] in exclusions['excluded_exact_sentinel_labels']:raise RuntimeError('protected_sentinel')
                mask=((values['drugname_drugconc']==cats['drugname_drugconc'].index(g['label']))
                    &(values['plate']==cats['plate'].index(g['plate']))&(values['pass_filter']==cats['pass_filter'].index('full'))
                    &(values['cell_line']==cats['cell_line'].index(g['cell_line_id'])))
                rows=[int(r) for r in np.flatnonzero(mask) if (file,int(r)) not in protected_rows
                    and cats['sample'][int(values['sample'][r])] not in exclusions['excluded_pooled_sample_ids']]
                actual_samples=sorted({cats['sample'][int(values['sample'][r])] for r in rows})
                declared_samples=sorted(g.get('samples',g.get('official_pooled_sample_ids',[])))
                if rows!=g['eligible_rows'] or actual_samples!=declared_samples or len(rows)<50:
                    raise RuntimeError('supplement_source_QC_identity_mismatch')
                for sample in actual_samples:
                    item=sample_table.loc[sample]
                    if item['plate']!=g['plate'] or item['drugname_drugconc']!=g['label']:
                        raise RuntimeError('official_sample_join_mismatch')
                group=dict(file=file,condition_id=f'{file}:supplement:{number}',label=g['label'],plate=g['plate'],
                    samples=actual_samples,cell_line_id=g['cell_line_id'],full_qc_available=len(rows),eligible_rows=rows,
                    holdout_relation='disjoint cell holdout; no culture-level independence asserted',official_sample_join_verified=True,
                    global_exposure_hours=24,timing_scope='global v2 Methods provenance; no per-well timing measurement',
                    adaptive_supplement=True)
                groups.append(group)
                for row in rows:
                    first,last=int(ptr[row]),int(ptr[row+1])
                    layouts[file].append(dict(row=row,condition_id=group['condition_id'],indices=physical_spans(h5['X/indices'],first,last),
                        values=physical_spans(h5['X/data'],first,last),nnz=last-first))
        if len({j['row'] for j in layouts[file]})!=len(layouts[file]):raise RuntimeError('reused_new_row_overlap')
        cached=[(a,b) for a,b,_,_ in source.spans]
        projected_fresh_index+=uncovered_bytes([s for j in layouts[file] for s in j['indices']],cached)
    metadata_bytes=sum(r.get('bytes',0) for r in read_rows(HERE/'NETWORK.jsonl'))
    write(HERE/'BUDGET_RECONCILIATION.json',dict(schema='supplement_pre_index_metadata_reserve_reconciliation_v1',
        frozen_selection_metadata_error_reserve_bytes=selection['metadata_and_error_body_cap'],
        frozen_selection_projected_total_bytes=selection['projected_total_with_reserves'],
        actual_new_metadata_known_body_bytes=metadata_bytes,
        actual_projected_fresh_index_bytes=projected_fresh_index,
        reserved_paired_value_and_HVG_bytes=4_000_000,
        actual_metadata_error_allowance_bytes=CAP-projected_fresh_index-4_000_000,
        projected_combined_total_bytes=PRIOR_SPENT+metadata_bytes+projected_fresh_index+4_000_000,
        binding_combined_body_cap_bytes=28_000_000,
        planning_reserve_was_estimate_not_frozen_scientific_acceptance=True,
        original_selection_unchanged=True,no_supplementary_indices_read=True))
    if projected_fresh_index>11_000_000 or metadata_bytes+projected_fresh_index+4_000_000>CAP:
        raise RuntimeError('supplement_index_and_reserved_paired_cap_exceeded')
    worst_values=sum(sum(sorted((j['nnz']*np.dtype(censuses[file]['layouts']['X/data']['dtype']).itemsize for j in jobs),reverse=True)[:117])
        for file,jobs in layouts.items())
    write(HERE/'SOURCES.json',dict(schema='adaptive_calibration_source_inputs_v1',inputs=records,census_seeds=seeds,
        gene_dictionaries=genes_meta,code_arrays=codes_meta,prior_stage_closure_sha256=sha(STAGE1/'CLOSURE.json')))
    write(HERE/'CENSUSES.json',censuses)
    write(HERE/'QC_ROWS.json',dict(schema='frozen_adaptive_index_QC_pool_v1',groups=groups,exclusions=exclusions,
        protected_rows_overlap=[],protected_samples_overlap=[],protected_labels_overlap=[]))
    write(HERE/'INDEX_LAYOUTS.json',layouts)
    write(HERE/'PROTOCOL.json',dict(old_protocol,schema='one_adaptive_compact_axis_calibration_v2',
        selected_conditions=len(groups),new_conditions=len(selection['selected']),maximum_new_conditions_per_file=8,
        prior_stage_known_body_bytes=PRIOR_SPENT,metadata_preparation_body_bytes=metadata_bytes,
        planned_index_screen_bytes=projected_fresh_index,total_response_body_cap_bytes=CAP,
        combined_calibration_body_cap_bytes=28_000_000,reserved_selected_value_and_HVG_bytes=4_000_000,
        maximum_discovery_cells_per_file=80,maximum_holdout_cells_per_file=48,max_paired_cells=256,
        selected_value_extreme_upper_bound_bytes=worst_values,selected_HVG_extreme_upper_bound_bytes=234*8000,
        paired_cost_check='Exact selected raw-value and complete-HVG spans must fit residual cap before PAIR_FREEZE; no reads on cost failure',
        selection_rule='Holdout rare-gene greedy1 with all-gene remaining>=2 safeguard, then discovery greedy2. Exact inverse-frequency Fraction scores, SHA256 ties; no fill, no per-condition quotas, <=48holdout/80discovery perfile. screen.py freezes exact semantics.',
        projected_index_stage_total_bytes=metadata_bytes+projected_fresh_index,
        adaptive_design=True,maximum_supplements=1,forbid_further_expansion_after_failure=True,
        prior_stage_failure_preserved=True))
    for old,new in [('NETWORK.jsonl','METADATA_NETWORK.jsonl'),('CACHE_REUSE.jsonl','METADATA_CACHE_REUSE.jsonl')]:
        (HERE/new).write_bytes((HERE/old).read_bytes() if (HERE/old).exists() else b'')
    files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['INDEX_FREEZE.json','NETWORK.jsonl','CACHE_REUSE.jsonl']]
    write(HERE/'INDEX_FREEZE.json',dict(schema='single_adaptive_index_screen_freeze_v1',expression_values_and_HVG_read=False,
        sha256={p.relative_to(HERE).as_posix():sha(p) for p in sorted(files)}))
    print(json.dumps(dict(status='SUPPLEMENT_INDEX_FREEZE_READY_FOR_PARENT_REVIEW',fresh_metadata_bytes=metadata_bytes,
        projected_fresh_index_bytes=projected_fresh_index,reserved_paired_bytes=4_000_000,
        combined_pool_cells=sum(len(j) for j in layouts.values()),groups=len(groups))),flush=True)


if __name__=='__main__':main()
