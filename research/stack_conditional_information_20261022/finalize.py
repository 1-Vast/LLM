"""Post-run accounting, independent score arithmetic and final file inventory."""
from collections import Counter
import ast
import json
from pathlib import Path
import sys

import numpy as np

import gate as g


def resources():
    terminal=g.load(g.LOG/'TERMINAL.json')
    accesses={}
    for path in sorted(g.LOG.glob('ACCESS_*.json')):
        access=g.load(path)
        cells=[c for screen in access['cells'].values() for c in screen.values()]
        accesses[access['stage']]={'selected_cell_records':len(cells),
            'statuses':dict(Counter(c['status'] for c in cells)),
            'selected_formula_cells':sum(c['formula'] for c in cells)}
    trialpath=g.LOG/'TRIALS.jsonl'
    trials=[json.loads(line) for line in trialpath.read_text().splitlines()] if trialpath.exists() else []
    byarm={arm:{'trial_fits':sum(t['arm']==arm and t['kind']=='trial' for t in trials),
        'refit_fits':sum(t['arm']==arm and t['kind']=='refit' for t in trials),
        'fit_seconds':sum(t['fit_seconds'] for t in trials if t['arm']==arm),
        'predict_seconds':sum(t['predict_seconds'] for t in trials if t['arm']==arm)} for arm in g.ARMS}
    g.write(g.LOG/'RESOURCES_AND_EXPOSURE.json',{'utc':g.utc(),'runtime':'maestro',
        'measured_gate_invocations':1,'model_fits':terminal['fits'],'by_arm':byarm,
        'gate_seconds':terminal['seconds'],'accesses':accesses,'new_network_requests':0,
        'new_dataset_downloads':0,'DeepSeek_provider_calls':0,'wetlab_experiments':0,
        'external_contact':0,'note':'Synthetic software fits are separate from measured assay fits. Source bytes/XML physically available; this is an enforced pipeline authorization, not cryptographic secrecy.'})
    if (g.LOG/'RESULTS.json').exists():
        records=g.load(g.LOG/'SCORED_TEST_RECORDS.json')
        result=g.load(g.LOG/'RESULTS.json')
        screens=np.array([r['screen'] for r in records])
        target=np.array([r['target_log2'] for r in records])
        calculated={}
        for arm in g.ARMS+g.ANCHORS:
            forecast=np.array([r['predictions'][arm] for r in records])
            values=[float(np.abs(forecast[screens==s]-target[screens==s]).mean()) for s in range(3)]
            np.testing.assert_allclose(values,result['scores'][arm]['screens'],rtol=0,atol=1e-14)
            np.testing.assert_allclose(np.mean(values),result['scores'][arm]['macro'],rtol=0,atol=1e-14)
            calculated[arm]=values
        decisions=[]
        for baseline in g.ARMS[:-1]:
            gain=np.array(calculated[baseline])-np.array(calculated['dead_history'])
            absolute=float(gain.mean())
            relative=absolute/np.mean(calculated[baseline])
            passed=absolute>=.05 and relative>=.1 and bool((gain>0).all())
            assert passed==result['history_gains'][baseline]['passed']
            decisions.append(passed)
        expected='DYNAMIC_HISTORY_PASS' if all(decisions) else 'ADDITIONAL_CHANNEL_ONLY' if decisions[0] else 'PRIMARY_USEFUL_GAIN_FAIL'
        assert expected==result['status']==terminal['status']
        g.write(g.LOG/'INDEPENDENT_SCORE_ARITHMETIC.json',{'utc':g.utc(),'passed':True,
            'scored_rows':len(records),'screen_counts':dict(Counter(map(str,screens))),
            'seven_forecast_metrics_recomputed':True,'four_gate_decisions_recomputed':True,'status':expected})
    print(json.dumps({'terminal':terminal,'accesses':accesses,'by_arm':byarm},ensure_ascii=False))


def inventory():
    frozen=g.load(g.LOG/'PRE_RESPONSE_FREEZE.json')['files']
    assert all(g.sha(item['path'])==item['sha256'] for item in frozen)
    preserved=0
    for phase in ('functional_dynamics_gate','dead_stock_information_gate','stack_raw_qualification'):
        for item in g.load(g.ROOT/f'log/20261022/{phase}/FINAL_FILE_INVENTORY.json')['files']:
            path=g.ROOT/item['path']
            assert path.stat().st_size==item['bytes'] and g.sha(path)==item['sha256']
            preserved+=1
    codefiles=sorted(Path(__file__).parent.glob('*.py'))
    for path in codefiles:
        ast.parse(path.read_text(encoding='utf-8'))
    g.write(g.LOG/'FINAL_INTEGRITY.json',{'utc':g.utc(),'passed':True,
        'prior_inventoried_files_unchanged':preserved,'current_frozen_files_unchanged':len(frozen),
        'all_phase_python_files_parse':len(codefiles),'measured_runs':1,
        'terminal':g.load(g.LOG/'TERMINAL.json')['status']})
    paths=sorted([p for folder in (g.LOG,Path(__file__).parent) for p in folder.rglob('*')
        if p.is_file() and p.name!='FINAL_FILE_INVENTORY.json'])
    g.write(g.LOG/'FINAL_FILE_INVENTORY.json',{'utc':g.utc(),'files':[
        {'path':p.relative_to(g.ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':g.sha(p)} for p in paths],
        'excludes':'This inventory itself and mutable navigation research/REPORT.md and log/README.md.'})
    print(f'{len(paths)} phase files inventoried')


if __name__=='__main__':
    assert sys.argv[1] in ('resources','inventory')
    resources() if sys.argv[1]=='resources' else inventory()
