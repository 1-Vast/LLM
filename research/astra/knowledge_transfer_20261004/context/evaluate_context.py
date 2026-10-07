"""One bounded adaptive follow-up; never overwrite the completed graph study."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from ..acquire import ASSETS, digest
from ..evaluate import ROOT, PARTITION, REGIMES, average_lines, average_pair_matrices, dump
from ..model import history_lines
from .acquire_context import HERE
from .conditional import context_weights, weighted_quantities, score_from
from research.astra.confirmation_campaign_20261004.design import campaign as c
from research.astra.feedback_validation_20261003.jaaks import build_panels
from tools.datasets.combination_screens import open_vault

METHODS = ('pathway','tf','shuffled_pathway','shuffled_tf')
WEIGHTS = (0.,.5,1.)


def freeze():
    path = HERE/'freeze.json'
    if path.exists():
        raise FileExistsError('immutable follow-up freeze already exists')
    prior = json.loads((HERE.parent/'freeze.json').read_text())
    files = {name:digest(ROOT/name) for name in prior['files']}
    for name, expected in prior['files'].items():
        if files[name] != expected:
            raise ValueError(f'stage-1 freeze changed: {name}')
    extra = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    extra += [HERE.parent/'results/development_selection.json',HERE.parent/'results/summary.json']
    for p in extra:
        files[str(p.relative_to(ROOT))] = digest(p)
    dump(path,dict(status='ADAPTIVE EXPLORATORY after stage-1 E results',
                   frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),files=files))
    print('Frozen follow-up before follow-up evaluation.',flush=True)


def context_frames(split):
    frames = {m:pd.read_csv(HERE/f'{m}_125_lines.csv',index_col=0) for m in ('pathway','tf')}
    for m in ('pathway','tf'):
        shuffled = frames[m].copy()
        for ti,tissue in enumerate(c.TISSUES):
            for pi,phase in enumerate(('HD','E')):
                ids = sorted(split[tissue][phase])
                perm = np.random.default_rng([20261004,ti,pi]).permutation(len(ids))
                shuffled.loc[ids] = frames[m].loc[ids].to_numpy()[perm]
        frames['shuffled_'+m] = shuffled
    return frames


def target_records(full,H,sidm,hd,ev,base,frames,choices=None):
    # Only permitted history baseline profiles fit scaler / PCA and bandwidth.
    hist_ids = sorted(H.present_lines)
    predicted = {}
    for method,frame in frames.items():
        weights = context_weights(frame.loc[hist_ids].to_numpy(),frame.loc[sidm].to_numpy(),
                                  pca=method.endswith('tf'))
        weight_by_li = {full.lines.index(s):float(w) for s,w in zip(hist_ids,weights)}
        row_weights = np.array([weight_by_li[int(li)] for li in H.c])
        predicted[method] = row_weights
    recs,tgs = [],{}
    for role in c.ROLES:
        tg = c.make_target(full,H,sidm,role,allowed_history=hd,forbidden=ev)
        original,verify = tg.scores[base]
        arms = ['simple']
        tg.scores['simple'] = (original,verify)
        for method,row_weights in predicted.items():
            q = weighted_quantities(H,role,tg.pid,row_weights)
            score = score_from(q,base)
            for alpha in (WEIGHTS if choices is None else [choices[method]]):
                arm = f'{method}:{alpha:g}'
                tg.scores[arm] = ((1-alpha)*original + alpha*score,verify)
                arms.append(arm)
        truth = c.truth_of(full,tg)
        for arm in arms:
            recs.append(c.run_p2(tg,truth,arm,30))
        tgs[(full.tissue,sidm,role)] = tg
    return recs,tgs


def run():
    out = HERE/'results'
    if (out/'summary.json').exists():
        raise FileExistsError('follow-up E already evaluated')
    ticket = open_vault(HERE/'freeze.json',HERE/'outcome_access.jsonl',
                       purpose='Adaptive exploratory baseline-context follow-up, not untouched evaluation',
                       source=ASSETS/'jaaks.csv',root=ROOT)
    panels,_,candidates = build_panels(ticket,path=ASSETS/'jaaks.csv')
    tissues = c.build_tissues(panels,candidates)
    split = json.loads(PARTITION.read_text())['split']
    old_selection = json.loads((HERE.parent/'results/development_selection.json').read_text())
    old_results = json.loads((HERE.parent/'results/summary.json').read_text())
    frames = context_frames(split)
    summary,selections,all_records = {},{},[]
    for regime,(count,seeds) in REGIMES.items():
        base = old_selection[regime]['choices']['simple']
        dev = []
        for tissue,full in tissues.items():
            hd,ev = split[tissue]['HD'],split[tissue]['E']
            for seed in seeds:
                for sidm in hd:
                    hist = history_lines(hd,sidm,count,seed,full.code)
                    rec,_ = target_records(full,c.restrict(full,hist),sidm,hd,ev,base,frames)
                    for r in rec:
                        r.update(seed=seed,regime=regime,phase='HD',history_lines=hist)
                    dev.extend(rec)
        arms = sorted({r['arm'] for r in dev})
        totals = {arm:sum(average_lines([r for r in dev if r['arm']==arm]).values()) for arm in arms}
        choices = {m:min(WEIGHTS,key=lambda a:(-totals[f'{m}:{a:g}'],a)) for m in METHODS}
        selections[regime] = dict(base=base,choices=choices,development_confirmed=totals)
        dump(out/'development_selection.json',selections)
        print(f'{regime}: {base}; HD chose {choices}',flush=True)
        ev_records,targets = [],{}
        for tissue,full in tissues.items():
            hd,ev = split[tissue]['HD'],split[tissue]['E']
            for seed in seeds:
                for sidm in ev:
                    hist = history_lines(hd,sidm,count,seed,full.code)
                    rec,tgs = target_records(full,c.restrict(full,hist),sidm,hd,ev,base,frames,choices)
                    targets.update(tgs)
                    for r in rec:
                        r.update(seed=seed,regime=regime,phase='E',history_lines=hist)
                    ev_records.extend(rec)
        selected = {m:f'{m}:{choices[m]:g}' for m in METHODS}
        selected['simple'] = 'simple'
        lv = {name:average_lines([r for r in ev_records if r['arm']==arm]) for name,arm in selected.items()}
        keys = c.sort_keys(lv['simple'])
        xs = {name:np.array([v[k] for k in keys]) for name,v in lv.items()}
        if abs(xs['simple'].sum()-old_results[regime]['totals']['simple_selected'])>1e-8:
            raise AssertionError('stage-1 selected simple comparator parity failed')
        ii = c.boot_indices(keys)
        mats = {name:average_pair_matrices([r for r in ev_records if r['arm']==arm],targets,keys,seeds)
                for name,arm in selected.items()}
        s = dict(base=base,choices=choices,seeds=seeds,n_lines=len(keys),
                 status='ADAPTIVE EXPLORATORY; baseline context only, no within-line state/dynamics claim',
                 totals={name:float(x.sum()) for name,x in xs.items()},
                 by_tissue={name:{t:sum(lv[name][k] for k in keys if k[0]==t) for t in tissues} for name in xs},
                 vs_simple={},vs_shuffled={},
                 per_seed_totals={name:{str(seed):sum(average_lines([r for r in ev_records if r['arm']==arm and r['seed']==seed]).values())
                                       for seed in seeds} for name,arm in selected.items()},
                 resource_totals={name:{f:sum(r[f] for r in ev_records if r['arm']==arm)/(2*len(seeds))
                                        for f in ('n_screens','n_verifications','spent','unused')}
                                  for name,arm in selected.items()})
        for name,x in xs.items():
            s['vs_simple'][name] = c.boot_contrast(x,xs['simple'],keys,ii)
            if name in ('pathway','tf'):
                s['vs_simple'][name]['line_pair_sensitivity'] = c.two_way(mats[name],mats['simple'],keys,resamples=5000)
                shuffled = 'shuffled_'+name
                s['vs_shuffled'][name] = c.boot_contrast(x,xs[shuffled],keys,ii)
                s['vs_shuffled'][name]['line_pair_sensitivity'] = c.two_way(mats[name],mats[shuffled],keys,resamples=5000)
        summary[regime] = s
        dump(out/f'{regime}_summary.json',s)
        dump(out/f'{regime}_per_line.json',[{'tissue':k[0],'line':k[1],**{name:lv[name][k] for name in lv}} for k in keys])
        for r in dev+ev_records:
            r.pop('rounds',None)
        all_records.extend(dev+ev_records)
        print(f'{regime}: E totals {s["totals"]}',flush=True)
    with (out/'campaigns.jsonl').open('w') as f:
        for r in all_records:
            f.write(json.dumps(c.jsonable(r),separators=(',',':'))+'\n')
    dump(out/'summary.json',summary)
    print('Completed the fixed follow-up.',flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze',action='store_true')
    args = ap.parse_args()
    freeze() if args.freeze else run()
