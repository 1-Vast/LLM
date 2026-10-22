"""Separate scorer: verify sealed forecasts, then cast only already-exposed devHigh means."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
OLD=ROOT/'log/20261022/tggates_feedback_headroom'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def evaluate(predictions,target,labels,masks):
    scores={};losses={}
    for family,pred in predictions.items():
        value=np.asarray(pred);assert value.shape==target.shape and np.isfinite(value).all()
        err=np.abs(value-target)
        scores[family]=dict(dna_mae=float(err[:,0].mean()),ldh_mae=float(err[:,1].mean()))
        losses[family]=[dict(label=label,dna_absolute_error=float(e[0]),ldh_absolute_error=float(e[1])) for label,e in zip(labels,err)]
    ordinary=[name for name in predictions if name!='rho_0' and not name.startswith('route_') and not name.startswith('null_')]
    best=min(ordinary,key=lambda name:(scores[name]['dna_mae'],name))
    candidate=scores['rho_0']['dna_mae'];baseline=scores[best]['dna_mae']
    absolute=baseline-candidate;relative=absolute/baseline if baseline>0 else 0.
    utility=absolute>.02 and relative>=.1
    state_increment=candidate<scores['route_01']['dna_mae']
    function_increment=candidate<scores['route_10']['dna_mae']
    observed_increment=candidate<scores['no_rna']['dna_mae']
    proceed=utility and state_increment and function_increment and observed_increment
    return dict(status='DEVELOPMENT_ONLY_NOT_CONFIRMATORY',scores=scores,losses=losses,
        strongest_nonisomorphic_ordinary=best,absolute_dna_gain=absolute,relative_dna_gain=relative,
        useful_gain_gate=utility,state_route_increment=state_increment,function_route_increment=function_increment,
        observed_rna_increment=observed_increment,
        decision='GO_ONLY_TO_NEW_QUALIFICATION_NOT_RSI_PROOF' if proceed else 'STOP_THIS_CONFIGURATION_EXPANSION',
        agent_benefit='NOT_TESTED',inheritance_benefit='NOT_TESTED',rsi_c4='NOT_TESTED',later_opened=False)


def main():
    assert not (P/'RNA_PILOT_RESULT.json').exists()
    seal=json.loads((P/'PREDICTION_SEAL.json').read_text())
    assert seal['status']=='SEALED_BEFORE_SEPARATE_DEVELOPMENT_SCORING'
    for relative,digest in dict(seal['files'],**seal['code']).items():assert sha(ROOT/relative)==digest,relative
    new=json.loads((P/'DEVELOPMENT_RNA_PREDICTIONS.json').read_text());labels=new['labels']
    rows=json.loads((OLD/'CONDITION_MEANS.json').read_text(encoding='utf-8'),parse_float=str)
    selected={r['compound_label']:r for r in rows if r['role']=='development'}
    assert set(labels)==set(selected) and len(labels)==7
    target=np.asarray([[float(v) for v in selected[label]['doses']['High']['mean']] for label in labels])
    predictions=dict(new['predictions'])
    old=json.loads((OLD/'DEVELOPMENT_PREDICTIONS.json').read_text(),parse_float=str)
    for family,records in old.items():
        lookup={r['compound_label']:r for r in records}
        assert set(lookup)==set(labels)
        # Old target fields are skipped. These predictions were already frozen in the earlier phase.
        predictions['prior_'+family]=[[float(v) for v in lookup[label]['prediction']] for label in labels]
    predictions.update({'route_'+k:v for k,v in new['route_masks'].items()})
    predictions.update({'null_'+k:v for k,v in new['nulls'].items()})
    result=evaluate(predictions,target,labels,new['route_masks'])
    result.update(prediction_seal_sha256=sha(P/'PREDICTION_SEAL.json'),
        development_high_function_casts=14,later_function_casts=0,development_high_rna_opened=False,
        warning='Historical development exposure and source selection remain; intervals would be descriptive only.')
    with (P/'RNA_PILOT_RESULT.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in {'scores','losses'}},indent=2))

if __name__=='__main__':main()
