"""Finite counterexamples and ordinary contextual-Beta reduction; no real data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261022/intervention_program_renewal'


def main():
    path=OUT/'CCIP_ALGEBRA_AUDIT.json'
    if path.exists():
        raise FileExistsError('audit_already_recorded')
    source=OUT/'improver/RESPONSE.md'
    expected='a08eb9dc18c02bb7bec1fca214389e11315f742197f5c7fe5fa9b903a8c24cff'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
    losses={'good':.01,'bad':.25}
    selected=min(losses,key=lambda op:(losses[op],op))
    failure_count={op:1 for op in losses}
    success_count={op:1 for op in losses}
    failure_count[selected]+=1
    banned=[op for op in losses if failure_count[op]/(failure_count[op]+success_count[op])>.5]
    assert selected=='good' and losses[selected]<.05 and selected in banned
    remaining=[op for op in losses if op not in banned]
    literal_next=min(losses[op] for op in remaining)
    assert literal_next>.01
    # A charitable implementation uses actual failure feedback instead of banning argmin.
    certificate={}
    ordinary_failure={}
    ordinary_success={}
    traces=[]
    events=[('r0','o0',True,True),('r0','o1',False,True),('r1','o0',False,True),
            ('r0','o0',False,False),('r1','o1',True,True),('r0','o1',False,True),
            ('r0','o0',False,True),('r1','o0',True,True)]
    gain={'o0':.2,'o1':.3}
    cost={'o0':1.,'o1':2.}
    for i,(region,operator,failed,high_confidence) in enumerate(events):
        for r in ('r0','r1'):
            for op in ('o0','o1'):
                certificate.setdefault((r,op),[1,1])
                ordinary_failure.setdefault((r,op),1)
                ordinary_success.setdefault((r,op),1)
        key=(region,operator)
        if high_confidence:
            certificate[key][0 if failed else 1]+=1
            if failed: ordinary_failure[key]+=1
            else: ordinary_success[key]+=1
        snapshot=[]
        for r in ('r0','r1'):
            scores_a,scores_b={},{}
            for op in ('o0','o1'):
                k=(r,op)
                a,b=certificate[k]
                p=a/(a+b)
                q=ordinary_failure[k]/(ordinary_failure[k]+ordinary_success[k])
                assert p==q
                if p<=.5: scores_a[op]=gain[op]/(cost[op]*(1+p))
                if q<=.5: scores_b[op]=gain[op]/(cost[op]*(1+q))
                snapshot.append({'region':r,'operator':op,'certificate_failure_mean':p,
                    'ordinary_failure_mean':q,'pruned':p>.5})
            assert scores_a==scores_b
            choice_a=sorted(scores_a,key=lambda op:(-scores_a[op],op))
            choice_b=sorted(scores_b,key=lambda op:(-scores_b[op],op))
            assert choice_a==choice_b
        traces.append({'i':i,'event':{'region':region,'operator':operator,'failed':failed,
            'high_confidence':high_confidence},'posterior_state':snapshot,'states_and_order_equal':True})
    # Same named region need not have an invariant operator effect across tasks.
    task1={'o0':.8,'o1':.1}
    task2={'o0':.01,'o1':.4}
    inherited_ban={'o0'}
    accessible=[op for op in task2 if op not in inherited_ban]
    assert min(task2,key=task2.get) not in accessible
    assert min(task2[op] for op in accessible)>.01
    result={'utc':datetime.now(timezone.utc).isoformat(),'source_sha256':expected,
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256':hashlib.sha256((OUT/'CCIP_ALGEBRA_PROTOCOL.md').read_bytes()).hexdigest(),
        'biological_response_access':False,'drug_performance_test':False,
        'literal_counterexample':{'evaluated_losses':losses,'declared_success_cutoff':.05,
            'selected_best':selected,'subsequently_banned':banned,'next_identical_task_best_available_loss':literal_next,
            'unpruned_best_loss':.01},'ordinary_beta_reduction':traces,
        'transfer_counterexample':{'task1_losses':task1,'task2_losses':task2,'inherited_ban':sorted(inherited_ban),
            'reachable_operators':accessible,'reachable_loss':min(task2[op] for op in accessible),
            'unreachable_best_loss':.01,'self_correction_from_exclusively_disabled_operator_reachable':False},
        'verdict':'LITERAL_FAILURE_SIGN_COUNTEREXAMPLE_AND_REPAIRED_BETA_REDUCTION',
        'limits':['Constructive operator examples, not measured biological tasks or an empirical win/loss.',
            'The ordinary baseline receives the identical region/gate/gain/cost/transcript; their computation is not free.',
            'A separate novel region-construction or invariant-transfer operation would need its own explicit test.',
            'No claim that all contextual bandits or all self-modifying research programs are equivalent.']}
    with path.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps({'verdict':result['verdict'],'posterior_events':len(traces),
        'next_task_literal_loss':literal_next,'corrected_reduction_states_equal':True}))


if __name__=='__main__':
    main()
