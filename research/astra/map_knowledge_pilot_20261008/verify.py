"""Behavioral boundary checks and independent arithmetic reconstruction."""
import json
import numpy as np
from threadpoolctl import threadpool_limits
import run as study


def main():
    checks = []
    protocol=json.loads((study.HERE/'PROTOCOL.json').read_text())
    for path, expected in protocol['inputs'].items():
        assert study.sha(study.ROOT/path)==expected
    checks.append('Original predecessor inputs unchanged')
    arrays=dict(np.load(study.PACKET/'training_arrays.npz'))
    e,perm,matched=study.representations(json.loads((study.PACKET/'PACKET_MANIFEST.json').read_text())['labels'])
    train=list(range(1,45))
    prediction,_,_=study.predict(arrays,train,0,e,matched,'knowledge',1000)
    poisoned={k:v.copy() for k,v in arrays.items()}
    poisoned['train_B'][0]=1e6
    poisoned['train_A'][0]=-1e6
    altered,_,_=study.predict(poisoned,train,0,e,matched,'knowledge',1000)
    np.testing.assert_allclose(prediction,altered,rtol=1e-12,atol=1e-14)
    checks.append('Held-cell A/B outcome poisoning cannot affect its fitted prediction')
    baseline,_,_=study.predict(arrays,train,0,e,matched,'M2',0)
    np.testing.assert_array_equal(prediction[~matched],baseline[~matched])
    checks.append('Unmatched candidates preserve exact STATE fallback')
    np.testing.assert_array_equal(study.ridge_predict(np.zeros((1,2,3)),np.zeros((1,2)),
        np.ones((1,2),bool),np.ones((2,3)),0),np.zeros(2))
    checks.append('Alpha zero truly disables correction')
    public=dict(np.load(study.PACKET/'public_prior.npz'))
    private=dict(np.load(study.PACKET/'evaluator_private.npz'))
    p=public['PANC_1__M2'];a=private['PANC_1__A'];b=private['PANC_1__B']
    original=study.kg_replay(p,public['cov'],public['obsvar'],public['offset'],a,b)
    changed=study.kg_replay(p,public['cov'],public['obsvar'],public['offset'],a,np.arange(146)*1e6)
    assert original['selected']==changed['selected'] and original['history']==changed['history']
    checks.append('Target B poisoning cannot change purchases or final commitment')
    assert len(original['history'])==9 and len({r['purchased_A'] for r in original['history'][:-1]})==8
    assert original['history'][-1]['cumulative_cost']==13 and len(original['selected'])==5
    checks.append('Eight unique A purchases and five committed B choices cost13')
    names=json.loads((study.PACKET/'PACKET_MANIFEST.json').read_text())['labels']
    drugs=[study.ast.literal_eval(x)[0][0].strip().casefold() for x in names]
    for name in set(drugs):
        indices=[i for i,n in enumerate(drugs) if n==name]
        assert all(np.array_equal(perm[indices[0]],perm[i]) for i in indices)
    checks.append('Knowledge permutation preserves same-drug dose grouping')
    reconstructed={}
    for prefix in ['', 'CONTRASTIVE_']:
        results=json.loads((study.HERE/(prefix+'RESULTS.json')).read_text())
        predictions=dict(np.load(study.HERE/(prefix+'PREDICTIONS.npz')))
        summary=json.loads((study.HERE/(prefix+'SUMMARY.json')).read_text())['arms']
        for row in results:
            key=row['context'];pred=predictions[key+'__'+row['arm']];observed=private[key+'__B']
            selection=np.lexsort((np.arange(146),-pred))[:5].tolist()
            assert selection==row['selected']
            assert np.isclose(np.mean((pred-observed)**2),row['mse'],rtol=1e-12)
            assert np.isclose(observed[selection].sum(),row['top5_B'],rtol=1e-12)
            assert np.isclose(observed[row['kg']['selected']].sum(),row['kg']['terminal_B'],rtol=1e-12)
        for arm,declared in summary.items():
            rows=[r for r in results if r['arm']==arm]
            assert len(rows)==5
            assert np.isclose(np.mean([r['kg']['terminal_B'] for r in rows]),declared['mean_KG_B'],rtol=1e-12)
        reconstructed[prefix or 'stage1']=len(results)
    checks.append('All55target arm/context results independently reconstructed')
    study.write('VERIFIED.json',dict(checks=checks,count=len(checks),results_reconstructed=reconstructed,
        verification_source_sha256=study.sha(study.HERE/'verify.py'),
        limits='Behavior/identity/arithmetic verification, not independent biological confirmation.'))
    print(json.dumps({'checks':len(checks),'results':reconstructed}))


if __name__=='__main__':
    with threadpool_limits(limits=1):main()
