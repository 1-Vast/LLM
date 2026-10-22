"""One registered STACK information gate; no general agent or world-model claim."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
import scipy
import sklearn
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_conditional_information'
OLD = ROOT / 'log/20261022/stack_raw_qualification'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ARMS = ('live_only', 'dead_initial', 'dead_snapshot', 'dead_endpoints', 'dead_history')
ANCHORS = ('persistence', 'log_growth')
ROLES = ('train', 'validate', 'test')
SEED = 20261022
TIMES = np.arange(0, 25, 4, dtype=float)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def utc():
    return datetime.now(timezone.utc).isoformat()


def make_roles(names):
    collision = {'Doxycycline Hyclate', 'E-64'}
    assert collision <= set(names)
    groups = [(name,) for name in sorted(names) if name not in collision]
    groups.append(tuple(sorted(collision)))
    groups.sort(key=lambda g: (hashlib.sha256(
        ('STACK-conditional-roles-v1|' + '\n'.join(g)).encode()).hexdigest(), g))
    n = len(groups)
    result = {}
    for i, group in enumerate(groups):
        role = 'train' if i < int(.6*n) else 'validate' if i < int(.6*n)+int(.2*n) else 'test'
        for name in group:
            result[name] = {'group': '\n'.join(group), 'role': role}
    return result


def make_manifest():
    projection = load(OLD / 'IDENTITY_PROJECTION.json')['files']
    acquired = load(OLD / 'RAW_ACQUISITION_FINAL.json')['files']
    names = [v['metadata_literal'] for a, v in projection[0]['cells'].items()
             if a.startswith('B') and a != 'B1']
    assert len(names) == len(set(names)) == 1833
    roles = make_roles(names)
    assert len({r['group'] for r in roles.values()}) == 1832
    records, sources = [], []
    for screen, (meta, raw) in enumerate(zip(projection[1:], acquired[1:])):
        assert meta['id'] == raw['id'] and sha(raw['body_path']) == meta['source_sha256_before_projection']
        sources.append({'screen': screen, 'filename': raw['filename'], 'path': raw['body_path'],
                        'sha256': sha(raw['body_path']), 'sheet': meta['sheet']['path']})
        dead = ['C','D','E','F','G','H','I'] if screen < 2 else ['C','E','G','I','K','M','O']
        live = ['AC','AD','AE','AF','AG','AH','AI'] if screen < 2 else ['BL','BN','BP','BR','BT','BV','BX']
        target = 'AU' if screen < 2 else 'CV'
        for a, v in meta['cells'].items():
            if not a.startswith('A') or a == 'A1':
                continue
            name = v.get('metadata_literal')
            if name not in roles:
                continue
            row = int(a[1:])
            records.append({'name': name, 'screen': screen, 'row': row, **roles[name],
                            'key': f'{screen}:{row}', 'L': [f'{c}{row}' for c in live],
                            'D': [f'{c}{row}' for c in dead], 'target': f'{target}{row}'})
    assert len(records) == 5499
    assert len({(r['screen'], r['name']) for r in records}) == 5499
    records.sort(key=lambda r: (r['screen'], r['row']))
    return {'sources': sources, 'records': records}


def project_numeric(stream, allowed):
    """Only whitelisted payloads converted; missing addresses explicitly recorded."""
    cells = {}
    for _, element in ET.iterparse(stream, events=['end']):
        if element.tag == NS + 'c':
            address = element.attrib['r']
            if address in allowed:
                assert address not in cells, 'duplicate authorized cell'
                kind = element.attrib.get('t', 'n')
                formula = element.find(NS + 'f') is not None
                raw = element.findtext(NS + 'v')
                status, value = 'valid', None
                if formula:
                    status = 'formula_disallowed'
                elif kind != 'n':
                    status = 'non_numeric_type'
                elif raw is None:
                    status = 'missing_cached_value'
                else:
                    try:
                        value = float(raw)
                    except (TypeError, ValueError):
                        status = 'unparsable'
                    else:
                        if not math.isfinite(value):
                            status, value = 'nonfinite', None
                        elif value < 0:
                            status = 'negative'
                cells[address] = {'status': status, 'value': value, 'formula': formula}
            element.clear()
        elif element.tag == NS + 'row':
            element.clear()
    for address in sorted(allowed - cells.keys()):
        cells[address] = {'status': 'absent', 'value': None, 'formula': False}
    return cells


def authorized(manifest, stage):
    assert stage in ('prefix', 'train_validate_target', 'test_target')
    result = {i: set() for i in range(3)}
    for r in manifest['records']:
        if stage == 'prefix':
            result[r['screen']].update(r['L'] + r['D'])
        elif (stage == 'test_target') == (r['role'] == 'test'):
            result[r['screen']].add(r['target'])
    return result


def read_stage(manifest, stage, prediction_seal=None):
    if stage == 'test_target':
        prefix = load(LOG / 'ACCESS_prefix.json')['cells']
        L,D,_ = observations(manifest,prefix,{})
        eligible = np.isfinite(L).all(axis=1) & np.isfinite(D).all(axis=1)
        verify_predictions(manifest, prediction_seal,
            {r['key']:bool(eligible[i]) for i,r in enumerate(manifest['records']) if r['role']=='test'})
    allowed = authorized(manifest, stage)
    data = {}
    for source in manifest['sources']:
        screen = source['screen']
        assert sha(source['path']) == source['sha256']
        with ZipFile(source['path']) as archive, archive.open(source['sheet']) as stream:
            data[str(screen)] = project_numeric(stream, allowed[screen])
    write(LOG / f'ACCESS_{stage}.json', {'utc': utc(), 'stage': stage,
          'authorized_addresses': {str(k): sorted(v) for k,v in allowed.items()}, 'cells': data})
    return data


def observations(manifest, prefix, targets):
    n = len(manifest['records'])
    L, D, y = np.full((n,7), np.nan), np.full((n,7), np.nan), np.full(n, np.nan)
    for i, r in enumerate(manifest['records']):
        cells = prefix[str(r['screen'])]
        for output, addresses in ((L, r['L']), (D, r['D'])):
            for j, a in enumerate(addresses):
                if cells[a]['status'] == 'valid':
                    output[i,j] = cells[a]['value']
        cell = targets.get(str(r['screen']), {}).get(r['target'])
        if cell and cell['status'] == 'valid':
            y[i] = np.log2(cell['value']+1)
    return L, D, y


def slope(s, indices):
    t = TIMES[indices]
    centered = t-t.mean()
    return s[:,indices] @ centered / (centered @ centered)


def features(L, D, screens):
    s, z = np.log2(L+1), np.log2(D+1)
    common = np.column_stack((s, s[:,:6]-s[:,6,None],
              slope(s, slice(0,4)), slope(s, slice(3,7)), slope(s, slice(0,7)), np.eye(3)[screens]))
    return {'live_only': common, 'dead_initial': np.column_stack((common,z[:,0])),
            'dead_snapshot': np.column_stack((common,z[:,6])),
            'dead_endpoints': np.column_stack((common,z[:,[0,6]])),
            'dead_history': np.column_stack((common,z))}


def weights(screens):
    counts = np.bincount(screens, minlength=3)
    assert (counts > 0).all()
    return len(screens)/(3*counts[screens])


def macro(errors, screens):
    per = [float(np.mean(errors[screens == s])) for s in range(3)]
    return {'macro': float(np.mean(per)), 'screens': per}


def coverage(manifest, L, D, y, roles):
    records = manifest['records']
    live = np.isfinite(L).all(axis=1)
    dual = live & np.isfinite(D).all(axis=1)
    target = np.isfinite(y)
    complete = dual & target
    tables, group_counts = [], {}
    for role in roles:
        groups = {}
        for i,r in enumerate(records):
            if r['role'] == role:
                groups.setdefault(r['group'], []).append(i)
        group_counts[role] = sum(bool(complete[ix].all()) for ix in groups.values())
        for screen in range(3):
            ix = np.array([i for i,r in enumerate(records) if r['role'] == role and r['screen'] == screen])
            n = len(ix)
            tables.append({'role': role, 'screen': screen, 'denominator': n,
                'live_prefix_valid': int(live[ix].sum()), 'dual_prefix_valid': int(dual[ix].sum()),
                'D_additional_prefix_failure': int((live[ix] & ~dual[ix]).sum()),
                'target_valid': int(target[ix].sum()), 'complete': int(complete[ix].sum()),
                'coverage': float(complete[ix].sum()/n)})
    minimum = {'train':200,'validate':100,'test':200}
    passed = all(t['coverage'] >= .95 for t in tables) and all(group_counts[r]>=minimum[r] for r in roles)
    return {'passed': bool(passed), 'tables': tables, 'fully_contributing_groups': group_counts}, dual, complete


def configs():
    result = {}
    for alpha in (.01,.1,1,10,100,1000):
        result[f'ridge_a{alpha:g}'] = ('ridge', {'alpha':alpha})
    for leaves in (7,15):
        for l2 in (0,10):
            result[f'hgb_leaves{leaves}_l2{l2}'] = ('hgb', {'max_leaf_nodes':leaves,'l2_regularization':l2})
    for depth in (8,None):
        for leaf in (2,5):
            result[f'extra_depth{depth}_leaf{leaf}'] = ('extra', {'max_depth':depth,'min_samples_leaf':leaf})
    return dict(sorted(result.items()))


def estimator(config):
    kind, params = config
    if kind == 'ridge':
        return make_pipeline(StandardScaler(), Ridge(**params))
    if kind == 'hgb':
        return HistGradientBoostingRegressor(**params, max_iter=300, learning_rate=.05,
                min_samples_leaf=10, random_state=SEED, early_stopping=False)
    return ExtraTreesRegressor(**params, n_estimators=300, n_jobs=1, random_state=SEED)


def fit(model, config, X, y, w):
    if config[0] == 'ridge':
        model.fit(X, y, ridge__sample_weight=w)
    else:
        model.fit(X, y, sample_weight=w)


def seal_predictions(manifest, records):
    write(LOG / 'TEST_PREDICTIONS.json', {'utc': utc(), 'records': records})
    seal = {'utc': utc(), 'path': str(LOG / 'TEST_PREDICTIONS.json'),
            'sha256': sha(LOG / 'TEST_PREDICTIONS.json')}
    verify_predictions(manifest, seal)
    write(LOG / 'TEST_PREDICTION_SEAL.json', seal)
    return seal


def verify_predictions(manifest, seal, expected_eligible=None):
    assert seal is not None, 'test targets require a saved forecast seal'
    assert sha(seal['path']) == seal['sha256']
    predicted = load(seal['path'])['records']
    expected = {r['key'] for r in manifest['records'] if r['role']=='test'}
    assert len(predicted) == len(expected)
    assert {r['key'] for r in predicted} == expected
    for r in predicted:
        assert set(r['predictions']) == set(ARMS+ANCHORS)
        if expected_eligible is not None:
            assert (r['status'] == 'predicted') == expected_eligible[r['key']]
        if r['status'] == 'predicted':
            assert all(v is not None and math.isfinite(v) for v in r['predictions'].values())
        else:
            assert r['status'] == 'prefix_abstention'
            assert all(v is None for v in r['predictions'].values())


def bootstrap(errors, screens, group_keys, all_groups):
    unique = sorted(set(all_groups))
    index = {g:i for i,g in enumerate(unique)}
    sums = np.zeros((len(unique),3))
    counts = np.zeros_like(sums)
    for i, g in enumerate(group_keys):
        sums[index[g], screens[i]] += errors[i]
        counts[index[g], screens[i]] += 1
    rng = np.random.default_rng(SEED)
    draws = np.empty(10000)
    b, rejected = 0, 0
    while b < 10000:
        ix = rng.integers(0,len(unique),len(unique))
        denominator = counts[ix].sum(axis=0)
        if (denominator == 0).any():
            rejected += 1
            continue
        draws[b] = np.mean(sums[ix].sum(axis=0)/denominator)
        b += 1
    return {'draws':10000, 'seed':SEED, 'groups':len(unique),
            'empty_screen_draws_redrawn':rejected, 'percentile95': np.percentile(draws,[2.5,97.5]).tolist()}


def freeze():
    manifest = make_manifest()
    write(LOG / 'ROLE_MANIFEST.json', manifest)
    files = sorted(Path(__file__).parent.glob('*.py')) + [LOG/'PROTOCOL.md', LOG/'ROLE_MANIFEST.json']
    files += sorted(LOG.glob('*/*.md'))
    files += [LOG/'TESTS_PRE_RESPONSE_FINAL.txt', LOG/'VERIFICATION_PRE_RESPONSE_FINAL.json']
    write(LOG / 'PRE_RESPONSE_FREEZE.json', {'utc': utc(), 'response_access':0,
        'files': [{'path':str(p), 'sha256':sha(p)} for p in files],
        'environment': {'python':sys.version, 'platform':platform.platform(),
            'numpy':np.__version__, 'scipy':scipy.__version__, 'sklearn':sklearn.__version__},
        'configs':configs(), 'arm_dimensions':dict(zip(ARMS,(19,20,20,21,26))),
        'role_groups':dict(Counter({r['group']:r['role'] for r in manifest['records']}.values()))})
    print('FROZEN; assay responses still unopened', flush=True)


def run():
    assert not (LOG/'RUN_START.json').exists(), 'one measured run; do not overwrite'
    frozen = load(LOG/'PRE_RESPONSE_FREEZE.json')
    for item in frozen['files']:
        assert sha(item['path']) == item['sha256'], item['path']
    manifest = load(LOG/'ROLE_MANIFEST.json')
    write(LOG/'RUN_START.json', {'utc':utc(), 'freeze_sha256':sha(LOG/'PRE_RESPONSE_FREEZE.json')})
    started = time.perf_counter()
    fits = 0
    try:
        prefix = read_stage(manifest,'prefix')
        targets = read_stage(manifest,'train_validate_target')
        L,D,y = observations(manifest,prefix,targets)
        records = manifest['records']
        roles = np.array([r['role'] for r in records])
        screens = np.array([r['screen'] for r in records])
        np.savez(LOG/'PRE_FIT_EXPOSURES.npz', L=L,D=D,y=y,roles=roles,screens=screens)
        qualified, dual, complete = coverage(manifest,L,D,y,('train','validate'))
        write(LOG/'TRAIN_VALIDATION_COVERAGE.json',qualified)
        if not qualified['passed']:
            write(LOG/'TERMINAL.json', {'status':'DATA_QUALIFICATION_INSUFFICIENT', 'stage':'train_validation',
                'fits':fits,'test_targets_opened':False,'seconds':time.perf_counter()-started, 'utc':utc()})
            print('TERMINAL DATA_QUALIFICATION_INSUFFICIENT before fits',flush=True)
            return
        X = features(L,D,screens)
        anchor = np.log2(L[:,6]+1)
        delta = y-anchor
        train = (roles=='train') & complete
        val = (roles=='validate') & complete
        refit = train | val
        test = (roles=='test') & dual
        wtrain,wrefit = weights(screens[train]), weights(screens[refit])
        np.savez(LOG/'FEATURE_EXPOSURES.npz', **X, anchor=anchor,train=train,val=val,refit=refit,test=test,
                 wtrain=wtrain,wrefit=wrefit)
        predictions, selections = {}, {}
        with (LOG/'TRIALS.jsonl').open('x',encoding='utf-8') as receipt, threadpool_limits(limits=1):
            for arm in ARMS:
                trials = []
                for name, config in configs().items():
                    before = time.perf_counter()
                    model = estimator(config)
                    fit(model,config,X[arm][train],delta[train],wtrain)
                    fits += 1
                    fit_seconds = time.perf_counter()-before
                    before = time.perf_counter()
                    forecast = model.predict(X[arm][val])+anchor[val]
                    score = macro(np.abs(forecast-y[val]),screens[val])
                    entry = {'arm':arm,'config':name,'kind':'trial','validation':score,
                             'fit_seconds':fit_seconds,'predict_seconds':time.perf_counter()-before,'utc':utc()}
                    receipt.write(json.dumps(entry)+'\n'); receipt.flush()
                    trials.append((score['macro'],name))
                    print(f'{fits}/75 {arm} {name} val={score["macro"]:.6f}',flush=True)
                _, selected = min(trials)
                config = configs()[selected]
                before = time.perf_counter()
                model = estimator(config)
                fit(model,config,X[arm][refit],delta[refit],wrefit)
                fits += 1
                fit_seconds = time.perf_counter()-before
                before = time.perf_counter()
                predictions[arm] = model.predict(X[arm][test])+anchor[test]
                selections[arm] = {'config':selected,'fit_seconds':fit_seconds,
                                  'predict_seconds':time.perf_counter()-before}
                receipt.write(json.dumps({'arm':arm,'kind':'refit',**selections[arm],'utc':utc()})+'\n'); receipt.flush()
        assert fits == 75
        write(LOG/'SELECTED.json',selections)
        predictions['persistence'] = anchor[test]
        predictions['log_growth'] = anchor[test] + 48*slope(np.log2(L[test]+1),slice(0,7))
        eligible_indices = np.flatnonzero(test)
        position = {i:j for j,i in enumerate(eligible_indices)}
        saved = []
        for i,r in enumerate(records):
            if r['role']!='test':
                continue
            saved.append({'key':r['key'],'status':'predicted' if test[i] else 'prefix_abstention',
                'predictions':{arm:float(predictions[arm][position[i]]) if test[i] else None for arm in ARMS+ANCHORS}})
        seal = seal_predictions(manifest,saved)
        test_targets = read_stage(manifest,'test_target',seal)
        for s, cells in test_targets.items():
            targets[s].update(cells)
        L,D,y = observations(manifest,prefix,targets)
        np.savez(LOG/'POST_SEAL_TARGET_EXPOSURES.npz',y=y)
        qualified,dual,complete = coverage(manifest,L,D,y,ROLES)
        write(LOG/'FINAL_COVERAGE.json',qualified)
        if not qualified['passed']:
            write(LOG/'TERMINAL.json', {'status':'DATA_QUALIFICATION_INSUFFICIENT','stage':'test','fits':fits,
                'test_targets_opened':True,'seconds':time.perf_counter()-started,'utc':utc()})
            return
        scored = (roles=='test') & complete
        saved_by_key = {r['key']:r for r in saved}
        scored_records = []
        error = {arm:[] for arm in ARMS+ANCHORS}
        for i in np.flatnonzero(scored):
            r=records[i]
            p=saved_by_key[r['key']]['predictions']
            scored_records.append({**r,'target_log2':float(y[i]),'predictions':p})
            for arm in error:
                error[arm].append(abs(p[arm]-y[i]))
        write(LOG/'SCORED_TEST_RECORDS.json',scored_records)
        error = {arm:np.array(v) for arm,v in error.items()}
        score = {arm:macro(v,screens[scored]) for arm,v in error.items()}
        gains={}
        for baseline in ARMS[:-1]:
            difference=error[baseline]-error['dead_history']
            gain=macro(difference,screens[scored])
            gain['relative']=gain['macro']/score[baseline]['macro'] if score[baseline]['macro'] else None
            gain['passed']=bool(gain['macro']>=.05 and gain['relative'] is not None and gain['relative']>=.1 and min(gain['screens'])>0)
            gain['bootstrap']=bootstrap(difference,screens[scored],[r['group'] for r in scored_records],
                [r['group'] for r in records if r['role']=='test'])
            gains[baseline]=gain
        status='DYNAMIC_HISTORY_PASS' if all(g['passed'] for g in gains.values()) else 'ADDITIONAL_CHANNEL_ONLY' if gains['live_only']['passed'] else 'PRIMARY_USEFUL_GAIN_FAIL'
        write(LOG/'RESULTS.json',{'scores':score,'history_gains':gains,'status':status})
        write(LOG/'TERMINAL.json',{'status':status,'stage':'scored','fits':fits,'test_targets_opened':True,
              'seconds':time.perf_counter()-started,'utc':utc()})
        print('TERMINAL '+status,flush=True)
    except BaseException as exc:
        write(LOG/'IMPLEMENTATION_FAILURE.json',{'utc':utc(),'fits_completed':fits,'error':repr(exc),
            'traceback':traceback.format_exc(),'seconds':time.perf_counter()-started})
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','run'))
    args=parser.parse_args()
    freeze() if args.action=='freeze' else run()
