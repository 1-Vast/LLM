"""Build condition-aware experimental evidence, separate from feature-only inputs."""
import hashlib,json,sqlite3,shutil
from pathlib import Path
import pandas as pd
from .analyze import HERE,ROOT,ID,COND,sha256,dump


def identity(row,keys):
    return hashlib.sha256(json.dumps({k:str(row[k]) for k in keys},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run():
    inputs=HERE/'inputs';inputs.mkdir(exist_ok=True)
    old=ROOT/'research/astra/knowledge_transfer_20261004'
    snapshots={
        'pathway_125_lines.csv':old/'context/pathway_125_lines.csv',
        'context_sources.json':old/'context/pinned_sources.json',
    }
    for name,src in snapshots.items():
        if src.exists():shutil.copyfile(src,inputs/name)
    prior_db=old/'biological_knowledge.sqlite'
    src=sqlite3.connect(f'file:{prior_db}?mode=ro',uri=True) if prior_db.exists() else None
    features=sqlite3.connect(HERE/'feature_catalog.sqlite')
    for name in ['drug','drug_target_annotation','context_release']:
        frame=pd.read_sql_query(f'SELECT * FROM {name}',src) if src else pd.read_csv(inputs/f'{name}.csv')
        if name=='context_release':frame=frame[frame.kind.eq('pathway')]
        frame.to_csv(inputs/f'{name}.csv',index=False)
        frame.to_sql(name,features,index=False)
    ctx=pd.read_csv(inputs/'pathway_125_lines.csv',index_col=0)
    context=ctx.rename_axis('SIDM').reset_index().melt(id_vars='SIDM',var_name='pathway',value_name='activity')
    context['evidence_kind']='upstream_computational_activity_from_basal_RNA'
    context.to_sql('cell_context',features,index=False)
    features.execute('CREATE UNIQUE INDEX context_key ON cell_context(SIDM,pathway)')
    features.execute('CREATE TABLE policy(note TEXT)')
    features.executemany('INSERT INTO policy VALUES(?)',[(x,) for x in [
        'No combination response or confirmation outcome is stored in this feature database.',
        'Drug targets are provider annotations, not validated binding or causal effect claims.',
        'RNA pathway scores describe untreated basal state; do not imply perturbation response.',
        'Feature rows do not create additional independent cell lines.'
    ]])
    features.commit();features.close()
    if src:src.close()
    p=HERE/'experimental_evidence.sqlite';db=sqlite3.connect(p)
    events=pd.read_csv(HERE/'results/events.csv.gz',dtype={k:str for k in ID+COND},low_memory=False)
    ckeys=ID+COND
    events['condition_id']=[identity(r,ckeys) for r in events.to_dict('records')]
    conditions=events[ckeys+['condition_id','role','pair','in_menu','n_anchor']].drop_duplicates('condition_id')
    conditions['assay']='CellTiter-Glo 2.0 per published protocol'
    conditions['treatment_duration_hours_protocol']=72
    conditions['full_library_grid_status']='seven-point design from paper; not independently rechecked well-by-well here'
    conditions['units']='concentration uM; seeding density cells/well; delta_Emax fraction'
    conditions.to_sql('assay_condition',db,index=False)
    db.execute('CREATE UNIQUE INDEX condition_key ON assay_condition(condition_id)')
    events['measurement_id']=[identity(r,['condition_id','event']) for r in events.to_dict('records')]
    events['source_id']='jaaks_original_events'
    events['exposure_status']='previously_exposed_exploratory_benchmark_only'
    cols=['measurement_id','condition_id','event','seeded','CELL_ID','design_plates','no_day1','y','hit','strict_hit','valid','source_id','exposure_status']
    events[cols].to_sql('measurement',db,index=False)
    db.execute('CREATE UNIQUE INDEX measurement_key ON measurement(measurement_id)')
    lookup={(r['condition_id'],r['event']):r['measurement_id'] for r in events.to_dict('records')}
    pairs=pd.read_csv(HERE/'results/paired_actions.csv.gz',dtype={k:str for k in ID+COND})
    pair_rows=[]
    for r in pairs.to_dict('records'):
        c=identity(r,ckeys);row={'condition_id':c,'SIDM':r['SIDM'],'pair':r['pair'],'role':r['role']}
        for i in [1,2,3]:row[f'R{i}_measurement']=lookup.get((c,r[f'event{i}']))
        assert row['R1_measurement'] and row['R2_measurement'] and row['R1_measurement']!=row['R2_measurement']
        pair_rows.append(row)
    pd.DataFrame(pair_rows).to_sql('benchmark_pair',db,index=False)
    pred=pd.read_csv(HERE/'rna_results/predictions.csv.gz',dtype={k:str for k in ID+COND})
    pred['condition_id']=[identity(r,ckeys) for r in pred.to_dict('records')]
    pred=pred[['condition_id','simple_score','rna_score','shuffled_score']].melt(id_vars='condition_id',var_name='model_arm',value_name='ranking_score')
    version=sha256(HERE/'freeze_rna.json')+':'+sha256(HERE/'rna_results/summary.json')
    pred['model_version']=version;pred['score_semantics']='relative_ranking_only_not_calibrated_probability'
    pred['scope']='all_candidates_including_unselected';pred.to_sql('candidate_prediction',db,index=False)
    db.execute('CREATE UNIQUE INDEX prediction_key ON candidate_prediction(condition_id,model_arm,model_version)')
    sources=[{'source_id':'jaaks_original_events','url':'https://doi.org/10.6084/m9.figshare.16843597.v1','source_sha256':'1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278','derived_table_sha256':sha256(HERE/'results/events.csv.gz'),'license':'CC BY 4.0','note':'Event aggregation; cached raw-plate hierarchy; not new independent experiments'},
             {'source_id':'plate_hierarchy','url':'https://api.figshare.com/v2/articles/19141916','source_sha256':sha256(ROOT/'research/astra/reproducible_allocation_20261003/repeats/receipts/plate_hierarchy.csv'),'derived_table_sha256':None,'license':'See original public release','note':'Repository cached mapping; CORROBORATED_NOT_AUTHENTICATED'}]
    pd.DataFrame(sources).to_sql('source',db,index=False)
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    orphan=db.execute('SELECT count(*) FROM measurement m LEFT JOIN assay_condition c USING(condition_id) WHERE c.condition_id IS NULL').fetchone()[0]
    assert orphan==0
    count={n:db.execute('SELECT COUNT(*) FROM '+n).fetchone()[0] for n in ['assay_condition','measurement','benchmark_pair','candidate_prediction']}
    db.commit();db.close()
    dump(HERE/'evidence_catalog_manifest.json',{'counts':count,'feature_counts':{'drugs':len(pd.read_csv(inputs/'drug.csv')),'target_annotations':len(pd.read_csv(inputs/'drug_target_annotation.csv')),'cell_pathway_scores':len(context),'cells':len(ctx)},'feature_db_sha256':sha256(HERE/'feature_catalog.sqlite'),'experimental_db_sha256':sha256(p),'orphan_measurements':orphan,'scope_note':'37k event rows include menu-external and compound-anchor conditions. Independent evaluation units remain 14 cell lines. No outcome is in feature_catalog.sqlite.'})
    print(json.dumps(count))

if __name__=='__main__':run()
