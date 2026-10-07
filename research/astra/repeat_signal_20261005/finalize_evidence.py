"""Verify recovered actions and enrich the separated evidence databases."""
import csv,gzip,hashlib,importlib,inspect,json,math,sqlite3
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from .analyze import HERE,ROOT,ID,COND,sha256,dump
from .build_evidence import identity
from .recover_biology import ARMS

def read_rows(path):
    with (gzip.open if path.suffix=='.gz' else open)(path,'rt',newline='') as f:return list(csv.DictReader(f))

def run():
    passed=[]
    for name in ['test_analysis','test_rna','test_raw','test_biology_recovery']:
        m=importlib.import_module('research.astra.repeat_signal_20261005.'+name)
        for n,f in inspect.getmembers(m,inspect.isfunction):
            if n.startswith('test_'):f();passed.append(name+'.'+n)
    freezes={}
    for p in sorted(HERE.glob('freeze*.json'))+sorted((ROOT/'research/astra/knowledge_transfer_20261004').rglob('freeze*.json')):
        entries=json.loads(p.read_text())['files'];bad=[n for n,h in entries.items() if sha256(ROOT/n)!=h]
        assert not bad;freezes[str(p.relative_to(ROOT))]={'checked':len(entries),'mismatched':bad}
    folder=HERE/'recovered_biology_results';summary=json.loads((folder/'summary.json').read_text())
    groups=defaultdict(list)
    for r in read_rows(folder/'predictions.csv.gz'):groups[(r['Tissue'],r['SIDM'],r['role'])].append(r)
    per={tuple(r[k] for k in ['Tissue','SIDM','role']):r for r in read_rows(folder/'per_role.csv')}
    positive=lambda v:str(v) in ['True','1','1.0'];confirmed={};count=0
    dep={r['SIDM'] for r in read_rows(HERE/'inputs/target_dependency.csv')};fallback=0
    for key,g in groups.items():
        M=math.ceil(.2*len(g));ns=math.floor(.7*M);orders={}
        for arm in ['simple']+ARMS+['prior_control']:
            order=sorted(g,key=lambda r:(-float(r[arm+'_score']),r['pair']));orders[arm]=[r['pair'] for r in order]
            screen=order[:ns];verify=[r for r in screen if positive(r['hit1'])][:M-ns]
            confirmed[(key,arm)]={r['pair'] for r in verify if positive(r['hit2'])}
            actual={'P2_confirmed':len(confirmed[(key,arm)]),'P2_cost':ns+len(verify),'R2_positive':sum(positive(r['hit2']) for r in order[:M])}
            assert actual['P2_cost']<=M
            for metric,value in actual.items():assert value==float(per[key][metric+'_'+arm])
            count+=1
        if key[1] not in dep:
            for arm in ['dependency','dependency_shuffled','target_dependency','target_shuffled']:
                assert orders[arm]==orders['simple'];fallback+=1
    differences={a:sum(confirmed[(key,a)]!=confirmed[(key,'prior_control')] for key in groups) for a in ['hotspot','dependency','target_dependency','rna_binary']}
    assert not any(differences.values())
    for a in ['simple']+ARMS+['prior_control']:
        expected=3.25 if a in ['simple','hotspot_shuffled'] else 23/7
        assert abs(summary['summary']['P2_confirmed_'+a]['mean']-expected)<1e-12
    p=pd.read_csv(HERE/'raw_results/paired_actions.csv.gz',dtype={'ANCHOR_ID':str,'LIBRARY_ID':str});estimates=[]
    for _,g in p.groupby(['Tissue','SIDM','role']):
        c=lambda a,b:float(np.corrcoef(a,b)[0,1])
        estimates.append([c(g.raw_y1,g.raw_y2),(c(g.raw_y1-g.prior_A,g.raw_y2-g.prior_B)+c(g.raw_y1-g.prior_B,g.raw_y2-g.prior_A))/2])
    raw_estimate=np.mean(estimates,axis=0);assert np.allclose(raw_estimate,[.5835883162636465,.3788965702969759],atol=1e-12)
    report={'status':'PASS','test_functions':passed,'freezes':freezes,'reconstructed_policy_runs':count,'missing_dependency_fallback_groups':fallback,'true_arm_confirmed_set_differences_from_static':differences,'previous_point_estimates_reproduced':True,'raw_correlations_reconstructed':raw_estimate.tolist(),'training_lines':111,'target_lines':14,'overlap':0,'scope':'Same executor; scalar policy reconstruction and correlation check, not independent-agent review. Recovery is explicitly after known outcomes.'}
    dump(HERE/'verification_recovery.json',report)
    # Add small feature matrices, never combination response labels, to feature-only DB.
    db=sqlite3.connect(HERE/'feature_catalog.sqlite')
    x=pd.read_csv(HERE/'inputs/target_dependency.csv',index_col=0)
    long=x.rename_axis('SIDM').reset_index().melt(id_vars='SIDM',var_name='gene',value_name='gene_effect')
    long['source_release']='DepMap 24Q4 v1';long['evidence_kind']='long-term CRISPR knockout effect; not pharmacologic inhibition'
    long.to_sql('target_dependency',db,index=False);db.execute('CREATE UNIQUE INDEX dependency_key ON target_dependency(SIDM,gene)')
    db.execute('UPDATE hotspot_mutation SET use_status=?',('subsequently_tested_in_exploratory_biological_arms',))
    db.execute('INSERT INTO policy VALUES(?)',('Hotspot acquisition-time note is historical: hotspot/dependency data subsequently tested in recovered_biology_results. No response labels are added here.',))
    source=json.loads((HERE/'next_sources/dependency_acquisition.json').read_text())
    pd.DataFrame([{k:source[k] for k in ['doi','url','source_sha256','derived_sha256','license']}]).to_sql('dependency_source',db,index=False)
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.commit();db.close()
    db=sqlite3.connect(HERE/'experimental_evidence.sqlite');d=pd.read_csv(folder/'predictions.csv.gz',dtype={k:str for k in ID+COND})
    d['condition_id']=[identity(r,ID+COND) for r in d.to_dict('records')]
    version=sha256(HERE/'freeze_recovery.json')+':'+sha256(folder/'summary.json')+':'+sha256(folder/'predictions.csv.gz')
    z=d[['condition_id']+[a+'_score' for a in ['simple']+ARMS+['prior_control']]].melt(id_vars='condition_id',var_name='model_arm',value_name='ranking_score')
    z['model_arm']='recovery:'+z.model_arm;z['model_version']=version;z['score_semantics']='ranking_only_not_calibrated_probability';z['scope']='all_candidates_including_unselected'
    z.to_sql('candidate_prediction',db,index=False,if_exists='append')
    pd.DataFrame([{'model_version':version,'identity_basis':'frozen_recipe_input_hashes_development_choices_complete_scores','serialized_coefficients':False}]).to_sql('model_recipe',db,index=False)
    p=pd.read_csv(HERE/'raw_results/paired_actions.csv.gz',dtype={k:str for k in ID+COND});p['condition_id']=[identity(r,ID+COND) for r in p.to_dict('records')]
    p[['condition_id','raw_y1','raw_y2','raw_y3','event1','event2','event3']].to_sql('raw_repeat_endpoint',db,index=False)
    count=db.execute('SELECT count(*) FROM candidate_prediction').fetchone()[0]
    orphan=db.execute('SELECT count(*) FROM candidate_prediction p LEFT JOIN assay_condition c USING(condition_id) WHERE c.condition_id IS NULL').fetchone()[0]
    assert orphan==0 and db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.commit();db.close()
    m=json.loads((HERE/'evidence_catalog_manifest.json').read_text());m['counts'].update(candidate_prediction=count,raw_repeat_endpoint=len(p),model_recipe=1)
    m['dependency_layer']=source;m['feature_counts']['dependency_values']=len(long);m['feature_db_sha256']=sha256(HERE/'feature_catalog.sqlite');m['experimental_db_sha256']=sha256(HERE/'experimental_evidence.sqlite');m['orphan_predictions']=0
    m['mutation_layer']['current_use']='Subsequently tested; acquisition-time not_used field is historical.';dump(HERE/'evidence_catalog_manifest.json',m)
    print(json.dumps({'verification':'PASS','tests':len(passed),'policy_runs':report['reconstructed_policy_runs'],'candidate_predictions':count,'dependency_values':len(long)}))

if __name__=='__main__':run()
