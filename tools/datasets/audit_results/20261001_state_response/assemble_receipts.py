"""One-round receipt synthesis; does not mutate frozen experiment outputs."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, parse_qsl

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(name, data):
    (RUN/name).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def main():
    sources, by_service = [], defaultdict(list)
    for file in sorted(RUN.rglob('receipts.json')):
        for row_index, record in enumerate(json.loads(file.read_text())):
            row = dict(record, receipt_file=file.relative_to(RUN).as_posix(), source_row_zero_based=row_index)
            row['service'] = row.get('service', urlsplit(row['url']).netloc)
            row['license'] = row.get('license', 'unknown; model/code/data rights separately')
            row['cost'] = 'unknown'
            if 'elapsed_seconds' not in row and row.get('finished_at_utc'):
                row['elapsed_seconds'] = (datetime.fromisoformat(row['finished_at_utc'])-datetime.fromisoformat(row['started_at_utc'])).total_seconds()
            row['semantic_status'] = ('retrieval_failed' if row.get('error') else 'retrieved; qualification separate')
            if row.get('id') == 'trade_bioc':
                row['semantic_status'] = 'HTTP200_error_body; not usable fulltext'
            if row.get('path'):
                path = file.parent/row['path']
                row['local_source'] = path.relative_to(RUN).as_posix()
                row['stored_bytes_hash_verified'] = path.exists() and sha(path)==row.get('sha256')
                assert row['stored_bytes_hash_verified'], row['local_source']
            sources.append(row)
            by_service[row['service']].append(row)
    write('source_index.json', sources)
    local = []
    for f in sorted(RUN.rglob('receipt.json')):
        row=json.loads(f.read_text())
        if 'command' not in row:
            continue
        local.append(dict(path=f.relative_to(RUN).as_posix(), valid=row.get('valid',False),
                          returncode=row.get('returncode'), elapsed_seconds=row.get('elapsed_seconds'),
                          forwards=row.get('forward_calls',0), cost='unknown', command=row['command']))
    write('api_summary.json', dict(
        generated_at_utc=datetime.now(timezone.utc).isoformat(), logical_public_requests=len(sources),
        scope='one row per acquired request or Range block; redirect transport round trips not instrumented; cached blocks not recounted',
        retrieval_failures=sum(bool(r.get('error')) for r in sources),
        semantic_failures_after_HTTP_success=1,
        stored_payload_bytes=sum(r.get('bytes',0) for r in sources),
        summed_request_elapsed_seconds=sum(r.get('elapsed_seconds',0) for r in sources),
        automatic_retry_attempts=sum(r.get('retry',0) for r in sources),
        followups='Different paths/versions/fulltext providers and independent extraction replay are separate request rows, not hidden retries.',
        partial_downloads='HDF5 sources deliberately partial; each successful block is complete for its explicit range. Whole-file download not claimed.',
        services={name:dict(requests=len(rows),failures=sum(bool(r.get('error')) for r in rows),
                            bytes=sum(r.get('bytes',0) for r in rows),seconds=sum(r.get('elapsed_seconds',0) for r in rows),
                            versions='fixed revisions/accessions and per-response hashes in source_index.json',cost='unknown')
                  for name,rows in by_service.items()},
        external_model_API_calls=0, local_STATE_requests=len(local),
        local_STATE_successful_requests=sum(x['valid'] for x in local),
        local_STATE_failed_requests=sum(not x['valid'] for x in local),
        local_STATE_actual_forwards=sum(x['forwards'] for x in local),
        local_model_receipts=local, model_versions='Tahoe and alternative Replogle weight SHA256 in frozen contracts',
        local_input_output_summary='Tahoe real c39 controls / fixed 3 doses; Replogle original raw and processed matched control / 2 gene actions; output h5ad and numerical arrays retained',
        physical_experiments=0, verified_monetary_cost='unknown'))

    joins=json.loads((RUN/'resistrace_v1/response_joins.json').read_text())
    meta={}
    for accession in {x['post_accession'] for x in joins}:
        path=RUN/f'evidence/{accession}_info.raw'
        frame=pd.read_csv(path,compression='gzip',sep='\t',index_col=0)
        meta[accession]=(dict(zip(frame.index,range(2,len(frame)+2))),sha(path))
    index=[]
    for row in joins:
        accession=row['post_accession'];positions,digest=meta[accession]
        path=RUN/('controls' if int(accession[3:])>=6938175 else 'material')/f'{accession}_counts.raw'
        index.append(dict(**row, post_metadata_source=f'evidence/{accession}_info.raw',
                          post_metadata_sha256=digest,
                          post_source_rows_1based_including_header=[positions[x] for x in row['post_cells']],
                          response_counts_source=path.relative_to(RUN).as_posix(),response_counts_sha256=sha(path),
                          expression_locator='gene row is exact frozen Ensembl ID; sample column is native post_cells ID',
                          derived_formula='mean log1p(raw_UMI*10000/full deposited library total) over exact matched descendants',
                          biological_unit='deposited baseline sister-label group or singleton; not certified independent culture'))
    write('response_source_index.json',index)
    write('retrospective_qualification.json',dict(
        status='qualified_only_for_conditional_retrospective_RNA_prediction',
        baseline_linkage={'evidence':'evidence/carbo2_code.raw:668-684 and final_sources/control2_code.raw:760 onward',
                         'meaning':'pre-only lineage combination grouping; destructive aliquot sisters, no same-cell trajectory'},
        outcome_linkage={'evidence':'evidence/carbo2_code.raw:752-802 and pinned Carbo1 same section; control2:849-897',
                        'meaning':'exact pre/post lineage match; only attaches observed response after building all queries'},
        preprocessing={'evidence':'resistrace_v1/freeze.json and execution_source.py.txt',
                       'meaning':'pre replicate1 feature selection only; all deposited gene library denominator; independently checked integer counts and total'},
        controls='separate same Kuramochi growth context; no certified same-parent counterfactual map',
        split='whole native replicate1 vs replicate2; common transduced pool/vial/parent relationships can remain; no physical independent holdout claim',
        observed_test_units=425, all_test_baseline_queries=6302,
        missing='unknown mixture of biological response, sampling and QC; not death or zero expression',
        availability='pre-treatment collection documented in previous source_review/resistrace_xml.paragraphs.txt:54; processed readability before treatment unknown',
        STATE_compatibility='not qualified for original checkpoint; separately trained RidgeRNA used',
        prospective_action_comparison='not_qualified',net_deployment_value='not_identified',physical_CI='not_reported'))

    previous=RUN.parent/'20261001_state_prospective/knowledge_run_v2'
    annotations=json.loads((previous/'knowledge_rows.json').read_text())
    excluded=json.loads((previous/'excluded_metadata.json').read_text())
    eligible=json.loads((previous/'eligible_metadata.json').read_text())
    write('knowledge_coverage.json',dict(scope='historical eligibility retained; not newly tuned or reselected',
        condition_plate_groups=len(eligible)+len(excluded),eligible=len(eligible),excluded=len(excluded),
        excluded_by_reason=dict(Counter(x['reason'] for x in excluded)),
        drug_annotation_rows=len(annotations),rows_with_provider_targets=sum(bool(x['provider_targets']) for x in annotations),
        rows_with_matched_graph_genes=sum(bool(x['matched_graph_genes']) for x in annotations),
        status='provider target annotations not uniformly independently confirmed; all historical exclusions retained',
        examples=[x for x in annotations if x['drug'] in ['Afatinib','Trametinib','Talc']]))

    pairs=[('raw_reconstruction_v3/execution_source.py.txt','tools/datasets/state_raw_reconstruction.py'),
           ('raw_reconstruction_v3_compat_source.py.txt','tools/datasets/state_replogle_compat.py'),
           ('sensitivity_v1/execution_source.py.txt','tools/datasets/state_sensitivity.py'),
           ('resistrace_v1/execution_source.py.txt','tools/datasets/resistrace_retrospective.py'),
           ('knowledge_diagnosis_v2/execution_source.py.txt','tools/datasets/state_knowledge_diagnose.py')]
    changes=[]
    for before,after in pairs:
        a,b=RUN/before,ROOT/after
        changes.append(dict(executed_snapshot=before,current_source=after,executed_sha256=sha(a),current_sha256=sha(b),
                            diff=''.join(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile=before,tofile=after))))
    write('source_evolution.json',changes)
    failures=[
        ('GitHub issue parsing','null body in public issue response','handle absent body for search inspection; no scientific exclusion','discovery/state_hvg_issues.raw'),
        ('Original checkpoint source','old ST-Tahoe URL failed in previous round','official listing located ST-HVG-Tahoe; appended correction, old receipts retained','followup/tahoe_model.raw'),
        ('Original split acquisition','guessed generalization_zeroshot path returned404','inspect fixed tree and fetch actual generalization.toml; exact training lineage still unknown','evidence/receipts.json; material/actual_tahoe_split_v2.raw'),
        ('cell-load module','not installed in maestro when inspected','inspect public fixed source; do not install full dependency stack','evidence/cell_load_tree.raw'),
        ('Remote matrix layout','initial CSR assumption on dense HDF5 object failed','inspect HDF5 encoding and read dense row ranges','replogle_remote_structure.json; replogle_ranges_v1/receipts.json'),
        ('Raw/processed barcode join','concat cell-line suffix prevented exact raw lookup','verify hepg2 context then remove exact -hepg2 suffix; preserve full raw native ID','replogle_extraction_verified/raw_processed_join.json'),
        ('Duplicate gene symbols','HSPA14-1 absent in raw symbol list','recover explicit unique-name convention and two distinct Ensembl IDs; no sum','raw_reconstruction_v3/contract.json'),
        ('Perturbation map load','weights-only torch rejected numpy scalar global','use existing narrowly scoped _numpy_scalar_globals allowlist','raw_reconstruction_v3/execution_source.py.txt'),
        ('Alternative checkpoint v1','new transformers rejects hidden328/12 divisibility','audit stored head_dim64 and8layer projection shapes','raw_reconstruction_v1/raw_reconstructed/stderr.txt'),
        ('Alternative checkpoint v2','method-only replacement leaves cached validator active','replace exact architecture validator in process-local cache as well; no weights/environment edits','raw_reconstruction_v2/raw_reconstructed/stderr.txt'),
        ('Alternative checkpoint v3 output equivalence','max2.2649765e-6; frozen atol=rtol=1e-6 failed','dtype/order diagnosis performed; still failed, tolerance unchanged','raw_reconstruction_status_erratum.json; raw_dtype_diagnosis.json'),
        ('Knowledge nested validation v1','3 inner folds plus chemical purge leave empty training support','metadata-only support audit; leave-one-plate-out inner folds; old freeze kept','knowledge_diagnosis_v1/freeze.json; knowledge_diagnosis_v2/freeze.json'),
        ('TRADE fulltext','HTTP500 then HTTP200 with error body','alternative BioC route attempted, no valid fulltext claim','paper_methods/receipts.json; final_sources/trade_bioc.raw'),
        ('Replogle README','guessed public README path404','inspect actual repository metadata; not evidence source unavailable','paper_methods/receipts.json'),
        ('Final read-only review','PowerShell literal wildcard and guessed absent local metadata filename','use rg directory/glob and stored plan paths; no research files affected','review only; terminal error not separately timestamped'),
    ]
    write('execution_failures.json',dict(timestamp_policy='exact times only in underlying receipts; no reconstructed timestamps for interactive inspection errors',
        failures=[dict(stage=a,error=b,repair_or_status=c,evidence=d) for a,b,c,d in failures]))
    env={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata.get('Name')}
    write('environment_after.json',env)
    old=json.loads((RUN/'environment.json').read_text())
    normalize=lambda d:{k.lower().replace('_','-'):v for k,v in d.items()}
    assert normalize(old)==normalize(env), 'dependency set changed'

    # Never print query values; report only suspicious parameter keys and local file.
    suspicious=[]
    for row in sources:
        for key in ['url','final_url']:
            if key not in row:continue
            keys=[k for k,_ in parse_qsl(urlsplit(row[key]).query)]
            bad=[k for k in keys if any(x in k.lower() for x in ['signature','credential','token','api_key','apikey','secret'])]
            if bad:suspicious.append(dict(file=row['receipt_file'],keys=bad))
    assert not suspicious, 'sensitive query keys present; inspect sanitized locations only'
    write('source_security_check.json',dict(checked_source_url_fields=True,suspicious_query_keys=suspicious,
                                          raw_auth_headers_stored=False,cost='unknown'))
    print(json.dumps({'source_requests':len(sources),'local_requests':len(local),'successful_local':sum(x['valid'] for x in local),'response_links':len(index),'dependency_changes':False}))


if __name__=='__main__':main()
