"""Independent audit of already exposed gate artifacts; no raw access or fitting."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/stack_conditional_information'
OUT = BASE / 'data_auditor'
ARMS = ('live_only', 'dead_initial', 'dead_snapshot', 'dead_endpoints', 'dead_history')
ALL = ARMS + ('persistence', 'log_growth')
ROLES = ('train', 'validate', 'test')


def load(name):
    return json.loads((BASE / name).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def macro(values, screens):
    per = np.array([values[screens == s].mean() for s in range(3)])
    return per, float(per.mean())


def main():
    freeze = load('PRE_RESPONSE_FREEZE.json')
    assert all(sha(item['path']) == item['sha256'] for item in freeze['files'])
    manifest = load('ROLE_MANIFEST.json')
    records = manifest['records']
    old_meta=json.loads((ROOT/'log/20261022/stack_raw_qualification/IDENTITY_PROJECTION.json').read_text(encoding='utf-8'))['files'][1:]
    for source,meta in zip(manifest['sources'],old_meta):
        assert source['filename']==meta['filename'] and source['sheet']==meta['sheet']['path']
        assert source['sha256']==meta['source_sha256_before_projection']
    for r in records:
        assert old_meta[r['screen']]['cells']['A'+str(r['row'])]['metadata_literal']==r['name']
    assert len(records) == len({r['key'] for r in records}) == 5499
    names = {r['name'] for r in records}
    collision = {'Doxycycline Hyclate', 'E-64'}
    groups = [(n,) for n in sorted(names - collision)] + [tuple(sorted(collision))]
    groups.sort(key=lambda g: (hashlib.sha256(('STACK-conditional-roles-v1|'+'\n'.join(g)).encode()).hexdigest(), g))
    expected_roles = {}
    for i, group in enumerate(groups):
        role = 'train' if i < 1099 else 'validate' if i < 1465 else 'test'
        for name in group:
            expected_roles[name] = (role, '\n'.join(group))
    assert len(names) == 1833 and len(groups) == 1832
    for r in records:
        assert (r['role'], r['group']) == expected_roles[r['name']]
        assert not 601 <= r['row'] <= 687
        live = ['AC','AD','AE','AF','AG','AH','AI'] if r['screen'] < 2 else ['BL','BN','BP','BR','BT','BV','BX']
        dead = ['C','D','E','F','G','H','I'] if r['screen'] < 2 else ['C','E','G','I','K','M','O']
        assert r['L'] == [c+str(r['row']) for c in live]
        assert r['D'] == [c+str(r['row']) for c in dead]
        assert r['target'] == ('AU' if r['screen'] < 2 else 'CV')+str(r['row'])
    assert all(len({r['screen'] for r in records if r['name'] == n}) == 3 for n in names)
    group_roles = dict(Counter(dict((r['group'],r['role']) for r in records).values()))
    assert group_roles == freeze['role_groups'] == {'train':1099,'validate':366,'test':367}

    ledgers = {stage:load('ACCESS_'+stage+'.json') for stage in ('prefix','train_validate_target','test_target')}
    invalid, access_counts = [], {}
    cell_owner = {}
    for r in records:
        for a in r['L']+r['D']+[r['target']]:
            cell_owner[r['screen'],a] = r
    for stage, ledger in ledgers.items():
        allowed = {str(s):set() for s in range(3)}
        for r in records:
            if stage == 'prefix':
                allowed[str(r['screen'])].update(r['L']+r['D'])
            elif (r['role'] == 'test') == (stage == 'test_target'):
                allowed[str(r['screen'])].add(r['target'])
        for s in allowed:
            assert set(ledger['authorized_addresses'][s]) == set(ledger['cells'][s]) == allowed[s]
            for address, cell in ledger['cells'][s].items():
                if cell['status'] != 'valid':
                    r = cell_owner[int(s),address]
                    invalid.append({'stage':stage,'screen':int(s),'address':address,
                        'key':r['key'],'name':r['name'],'role':r['role'],**cell})
        access_counts[stage] = sum(map(len,allowed.values()))
    assert access_counts == {'prefix':76986,'train_validate_target':4398,'test_target':1101}
    assert len(invalid) == 26

    L,D,y = np.full((5499,7),np.nan),np.full((5499,7),np.nan),np.full(5499,np.nan)
    y_before = y.copy()
    for i,r in enumerate(records):
        s = str(r['screen'])
        for array, channel in ((L,'L'),(D,'D')):
            for j,address in enumerate(r[channel]):
                cell = ledgers['prefix']['cells'][s][address]
                if cell['status'] == 'valid':
                    assert cell['value'] >= 0 and np.isfinite(cell['value']) and not cell['formula']
                    array[i,j] = cell['value']
        stage = 'test_target' if r['role'] == 'test' else 'train_validate_target'
        cell = ledgers[stage]['cells'][s][r['target']]
        if cell['status'] == 'valid':
            y[i] = np.log2(cell['value']+1)
            if r['role'] != 'test': y_before[i] = y[i]
    roles = np.array([r['role'] for r in records])
    screens = np.array([r['screen'] for r in records])
    live_ok = np.isfinite(L).all(axis=1)
    dual = live_ok & np.isfinite(D).all(axis=1)
    complete = dual & np.isfinite(y)
    coverage = load('FINAL_COVERAGE.json')
    assert coverage['passed']
    for table in coverage['tables']:
        ix = (roles == table['role']) & (screens == table['screen'])
        assert table['denominator'] == int(ix.sum())
        for key, mask in [('live_prefix_valid',live_ok),('dual_prefix_valid',dual),
                          ('D_additional_prefix_failure',live_ok & ~dual),
                          ('target_valid',np.isfinite(y)),('complete',complete)]:
            assert table[key] == int((ix & mask).sum())
        assert np.isclose(table['coverage'],complete[ix].mean()) and table['coverage'] >= .95
    full_groups = {}
    for role in ROLES:
        role_groups = {r['group'] for r in records if r['role'] == role}
        full_groups[role] = sum(complete[[i for i,r in enumerate(records) if r['group'] == g]].all() for g in role_groups)
    assert {k:int(v) for k,v in full_groups.items()} == coverage['fully_contributing_groups']
    assert all(full_groups[r]>=minimum for r,minimum in [('train',200),('validate',100),('test',200)])

    before = np.load(BASE/'PRE_FIT_EXPOSURES.npz',allow_pickle=False)
    after = np.load(BASE/'POST_SEAL_TARGET_EXPOSURES.npz',allow_pickle=False)
    feature = np.load(BASE/'FEATURE_EXPOSURES.npz',allow_pickle=False)
    for key, expected in [('L',L),('D',D),('y',y_before)]:
        np.testing.assert_allclose(before[key],expected,equal_nan=True)
    assert np.isnan(before['y'][roles == 'test']).all()
    np.testing.assert_allclose(after['y'],y,equal_nan=True)
    masks = {'train':(roles=='train') & complete,'val':(roles=='validate') & complete,
             'refit':(roles!='test') & complete,'test':(roles=='test') & dual}
    for key,mask in masks.items(): np.testing.assert_array_equal(feature[key],mask)
    weight_summary = {}
    for key,mask in [('wtrain',masks['train']),('wrefit',masks['refit'])]:
        expected = mask.sum()/(3*np.bincount(screens[mask],minlength=3)[screens[mask]])
        np.testing.assert_allclose(feature[key],expected)
        weight_summary[key] = {'rows':int(mask.sum()),'sum':float(feature[key].sum()),
            'mean':float(feature[key].mean()),'screen_totals':[float(feature[key][screens[mask]==s].sum()) for s in range(3)]}
    s,z = np.log2(L+1),np.log2(D+1)
    slopes = []
    for ix in (slice(0,4),slice(3,7),slice(0,7)):
        t=np.arange(0,25,4,dtype=float)[ix]; t=t-t.mean()
        slopes.append((s[:,ix]*t).sum(axis=1)/(t*t).sum())
    common=np.column_stack((s,s[:,:6]-s[:,6,None],*slopes,np.eye(3)[screens]))
    expected_features={'live_only':common,'dead_initial':np.column_stack((common,z[:,0])),
        'dead_snapshot':np.column_stack((common,z[:,6])),'dead_endpoints':np.column_stack((common,z[:,[0,6]])),
        'dead_history':np.column_stack((common,z))}
    for arm,X in expected_features.items():
        np.testing.assert_allclose(feature[arm],X,atol=1e-14,equal_nan=True)
        assert X.shape[1] == freeze['arm_dimensions'][arm]
    np.testing.assert_allclose(feature['anchor'],s[:,6],equal_nan=True)

    predicted = load('TEST_PREDICTIONS.json')
    seal = load('TEST_PREDICTION_SEAL.json')
    assert sha(seal['path']) == seal['sha256']
    pred = {r['key']:r for r in predicted['records']}
    test_records = [r for r in records if r['role']=='test']
    assert len(pred) == len(predicted['records']) == len(test_records) == 1101
    assert set(pred) == {r['key'] for r in test_records}
    for i,r in enumerate(records):
        if r['role'] != 'test': continue
        p=pred[r['key']]
        assert set(p['predictions']) == set(ALL)
        assert p['status'] == ('predicted' if dual[i] else 'prefix_abstention')
        assert all(v is None for v in p['predictions'].values()) if not dual[i] else all(np.isfinite(list(p['predictions'].values())))
    times={'freeze':freeze['utc'],'run_start':load('RUN_START.json')['utc'],
        'prefix_ledger':ledgers['prefix']['utc'],'train_validate_ledger':ledgers['train_validate_target']['utc'],
        'prediction_file':predicted['utc'],'prediction_seal':seal['utc'],
        'test_target_ledger':ledgers['test_target']['utc'],'terminal':load('TERMINAL.json')['utc']}
    assert list(times.values()) == sorted(times.values())
    trials=[json.loads(line) for line in (BASE/'TRIALS.jsonl').read_text(encoding='utf-8').splitlines()]
    selected=load('SELECTED.json')
    assert len(trials) == 75 and Counter(t['kind'] for t in trials) == {'trial':70,'refit':5}
    for arm in ARMS:
        grid=[t for t in trials if t['arm']==arm and t['kind']=='trial']
        refit=[t for t in trials if t['arm']==arm and t['kind']=='refit']
        assert len(grid)==14 and {t['config'] for t in grid} == set(freeze['configs']) and len(refit)==1
        winner=min((t['validation']['macro'],t['config']) for t in grid)[1]
        assert selected[arm]['config'] == refit[0]['config'] == winner
    assert max(t['utc'] for t in trials) <= predicted['utc']

    scored=load('SCORED_TEST_RECORDS.json')
    score_keys={r['key'] for r in scored}
    expected_keys={r['key'] for i,r in enumerate(records) if r['role']=='test' and complete[i]}
    assert len(score_keys)==len(scored)==1098 and score_keys==expected_keys
    target_by_key={r['key']:y[i] for i,r in enumerate(records)}
    for r in scored:
        assert r['predictions'] == pred[r['key']]['predictions']
        assert np.isclose(r['target_log2'],target_by_key[r['key']])
    result=load('RESULTS.json')
    ss=np.array([r['screen'] for r in scored])
    errors={a:np.array([abs(r['predictions'][a]-r['target_log2']) for r in scored]) for a in ALL}
    metrics={}
    for arm,err in errors.items():
        per,mean=macro(err,ss)
        np.testing.assert_allclose(per,result['scores'][arm]['screens'])
        assert np.isclose(mean,result['scores'][arm]['macro'])
        metrics[arm]={'macro':mean,'screens':per.tolist()}
    test_groups=sorted({r['group'] for r in test_records})
    assert len(test_groups)==367
    gi={g:i for i,g in enumerate(test_groups)}
    counts=np.zeros((367,3)); sums={a:np.zeros_like(counts) for a in ARMS[:-1]}
    for i,r in enumerate(scored):
        counts[gi[r['group']],r['screen']]+=1
        for a in sums: sums[a][gi[r['group']],r['screen']]+=errors[a][i]-errors['dead_history'][i]
    gains={}
    for a in ARMS[:-1]:
        per,gain=macro(errors[a]-errors['dead_history'],ss)
        relative=gain/metrics[a]['macro']
        passed=bool(gain>=.05 and relative>=.1 and (per>0).all())
        old=result['history_gains'][a]
        assert np.isclose(gain,old['macro']) and np.isclose(relative,old['relative']) and passed==old['passed']
        rng=np.random.default_rng(20261022); draws=[]; rejected=0
        while len(draws)<10000:
            chosen=rng.integers(0,367,367); denominator=counts[chosen].sum(axis=0)
            if (denominator==0).any(): rejected+=1; continue
            draws.append(float((sums[a][chosen].sum(axis=0)/denominator).mean()))
        interval=np.percentile(draws,[2.5,97.5]).tolist()
        assert old['bootstrap']['groups']==367 and old['bootstrap']['draws']==10000
        assert old['bootstrap']['empty_screen_draws_redrawn']==rejected
        np.testing.assert_allclose(interval,old['bootstrap']['percentile95'])
        gains[a]={'macro':gain,'relative':relative,'screens':per.tolist(),'passed':passed,'bootstrap95':interval}
    terminal=load('TERMINAL.json')
    assert terminal['fits']==75 and terminal['status']==result['status']=='PRIMARY_USEFUL_GAIN_FAIL'
    assert not gains['live_only']['passed']
    test_mask=roles=='test'
    assert int((test_mask & ~dual).sum())==2
    assert int((test_mask & dual & ~np.isfinite(y)).sum())==1
    output={'utc':datetime.now(timezone.utc).isoformat(),'verdict':'AUDIT_PASS_PRIMARY_USEFUL_GAIN_FAIL_CONFIRMED',
        'audit_code_sha256':sha(__file__),'raw_access':False,'new_fields_opened':False,'fits':0,
        'freeze_files_all_unchanged':True,'group_roles':group_roles,'access_counts':access_counts,
        'timestamps':times,'trial_rows':len(trials),'fit_count':75,'selected_configs':selected,
        'test_keys':1101,'prefix_abstentions':2,'valid_prefix_invalid_target':1,'common_scored_keys':1098,
        'all_bootstrap_test_clusters':367,'coverage':coverage,'weight_checks':weight_summary,
        'invalid_selected_cells_count':len(invalid),'invalid_selected_cells':invalid,
        'metrics_recomputed':metrics,'gains_recomputed':gains,
        'input_hashes':{name:sha(BASE/name) for name in ['PRE_RESPONSE_FREEZE.json','ROLE_MANIFEST.json',
            'ACCESS_prefix.json','ACCESS_train_validate_target.json','ACCESS_test_target.json',
            'PRE_FIT_EXPOSURES.npz','FEATURE_EXPOSURES.npz','POST_SEAL_TARGET_EXPOSURES.npz',
            'TRIALS.jsonl','SELECTED.json','TEST_PREDICTIONS.json','TEST_PREDICTION_SEAL.json',
            'FINAL_COVERAGE.json','SCORED_TEST_RECORDS.json','RESULTS.json','TERMINAL.json']},
        'limits':['Audit uses preserved selected-cell outputs, not an independent raw reread.',
                  'Ledger completion timestamps plus audited code support ordering; not cryptographic isolation.',
                  'Bootstrap conditions on fitted models and fixed screens, not biological repeats.']}
    with (OUT/'POST_RESULT_AUDIT.json').open('x',encoding='utf-8') as handle:
        json.dump(output,handle,ensure_ascii=False,indent=2,allow_nan=False); handle.write('\n')
    print(json.dumps({k:output[k] for k in ('verdict','fit_count','test_keys','common_scored_keys',
        'prefix_abstentions','valid_prefix_invalid_target','invalid_selected_cells_count','all_bootstrap_test_clusters')},ensure_ascii=False))


if __name__=='__main__':
    main()
