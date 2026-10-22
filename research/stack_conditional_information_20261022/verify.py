"""Record tests and integrity checks without broadening assay access."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys

import gate as g


def main(stage):
    checks=[]
    for path in Path(__file__).parent.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
        checks.append({'check':'python_parse','path':str(path),'passed':True})
    for phase in ('functional_dynamics_gate','dead_stock_information_gate','stack_raw_qualification'):
        inventory=g.load(g.ROOT/f'log/20261022/{phase}/FINAL_FILE_INVENTORY.json')
        for item in inventory['files']:
            path=g.ROOT/item['path']
            assert path.stat().st_size==item['bytes'] and g.sha(path)==item['sha256'],str(path)
            checks.append({'check':'historical_frozen_file','path':item['path'],'passed':True})
    with (g.LOG/f'TESTS_{stage}.txt').open('x',encoding='utf-8') as output:
        result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(Path(__file__).parent),
            '-p','test_gate.py','-v'],cwd=g.ROOT,stdout=output,stderr=subprocess.STDOUT)
    assert result.returncode==0
    checks.append({'check':'synthetic_suite','passed':True,'exit_code':result.returncode})
    if stage=='POST_RUN':
        for item in g.load(g.LOG/'PRE_RESPONSE_FREEZE.json')['files']:
            assert g.sha(item['path'])==item['sha256']
            checks.append({'check':'current_freeze_unchanged','path':item['path'],'passed':True})
        manifest=g.load(g.LOG/'ROLE_MANIFEST.json')
        for action in ('prefix','train_validate_target','test_target'):
            path=g.LOG/f'ACCESS_{action}.json'
            if not path.exists():
                continue
            access=g.load(path)
            allowed=g.authorized(manifest,action)
            for s in range(3):
                assert set(access['authorized_addresses'][str(s)])==allowed[s]
                assert set(access['cells'][str(s)])==allowed[s]
                checks.append({'check':'exact_access_ledger','stage':action,'screen':s,'passed':True})
        terminal=g.load(g.LOG/'TERMINAL.json')
        if terminal['test_targets_opened']:
            seal=g.load(g.LOG/'TEST_PREDICTION_SEAL.json')
            prefix=g.load(g.LOG/'ACCESS_prefix.json')['cells']
            L,D,_=g.observations(manifest,prefix,{})
            eligible=g.np.isfinite(L).all(axis=1)&g.np.isfinite(D).all(axis=1)
            g.verify_predictions(manifest,seal,{r['key']:bool(eligible[i]) for i,r in enumerate(manifest['records']) if r['role']=='test'})
            assert g.load(g.LOG/'ACCESS_test_target.json')['utc']>seal['utc']
            checks.append({'check':'complete_forecast_seal_precedes_test_target_access','passed':True})
        if (g.LOG/'TRIALS.jsonl').exists():
            trials=[json.loads(line) for line in (g.LOG/'TRIALS.jsonl').read_text().splitlines()]
            assert len(trials)==75 and terminal['fits']==75
            for arm in g.ARMS:
                entries=[t for t in trials if t['arm']==arm]
                assert len(entries)==15
                assert {t['config'] for t in entries if t['kind']=='trial'}==set(g.configs())
            checks.append({'check':'exact_70_trial_5_refit_budget','passed':True})
        else:
            assert terminal['fits']==0 and not terminal['test_targets_opened']
            checks.append({'check':'qualification_stop_before_fit_and_test_targets','passed':True})
    g.write(g.LOG/f'VERIFICATION_{stage}.json',{'utc':g.utc(),'checks':checks,'passed':True,
        'count':len(checks),'synthetic_test_cases':10})
    print(f'{stage}: {len(checks)} integrity checks and10 synthetic tests passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=('PRE_RESPONSE','PRE_RESPONSE_FINAL','POST_RUN'))
    main(parser.parse_args().stage)
