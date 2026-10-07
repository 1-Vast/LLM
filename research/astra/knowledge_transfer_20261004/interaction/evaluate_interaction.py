"""Final, single-pass exploratory state-action interaction evaluation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import numpy as np

from ..acquire import ASSETS,digest
from ..evaluate import ROOT,PARTITION,REGIMES,average_lines,average_pair_matrices,dump,make_kernels
from ..model import history_lines
from ..context.evaluate_context import context_frames
from ..context.conditional import score_from
from .learned import pair_features,state_features,residual_prediction
from research.astra.confirmation_campaign_20261004.design import campaign as c
from research.astra.feedback_validation_20261003.jaaks import build_panels
from tools.datasets.combination_screens import open_vault

HERE = Path(__file__).resolve().parent
METHODS = ('id_context','network_context','network_shuffled_context')
WEIGHTS = (0.,.5,1.)


def freeze():
    fp = HERE/'freeze.json'
    if fp.exists():
        raise FileExistsError('final follow-up freeze is immutable')
    prior = json.loads((HERE.parent/'context/freeze.json').read_text())
    for name,h in prior['files'].items():
        if digest(ROOT/name)!=h:raise ValueError('prior freeze mismatch: '+name)
    files = dict(prior['files'])
    extra = list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE.parent/'context/results/summary.json']
    for p in extra:files[str(p.relative_to(ROOT))]=digest(p)
    dump(fp,dict(status='FINAL ADAPTIVE EXPLORATORY trial after both earlier E outputs',
                 frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),files=files))
    print('Frozen final state-action trial.',flush=True)


def target_records(full,H,sidm,hd,ev,base,frames,pair_phi,choices=None):
    hist = sorted(H.present_lines)
    histpos = {full.lines.index(s):i for i,s in enumerate(hist)}
    row_index = np.array([histpos[int(li)] for li in H.c])
    target_pid = full.pid[full.c==full.lines.index(sidm)]
    n_pairs = next(iter(pair_phi.values())).shape[0]
    q = c.history_quantities(H,'SV',np.arange(n_pairs))
    prior = np.column_stack([q['p_s'],q['p_v'],q['S'],q['L_v']])
    a = H.arrays['SV']
    y = np.column_stack([a['h_s'],a['h_v'],a['y_s'],a['y_v']]).astype(float)
    residual = y-prior[H.pid]
    predicted = {}
    for method in METHODS:
        prefix = 'shuffled_' if 'shuffled' in method else ''
        ph,tf = frames[prefix+'pathway'],frames[prefix+'tf']
        z,zt = state_features(ph.loc[hist].to_numpy(),ph.loc[sidm].to_numpy(),
                             tf.loc[hist].to_numpy(),tf.loc[sidm].to_numpy())
        phi = pair_phi['drug_id' if method=='id_context' else 'network']
        delta = residual_prediction(phi,H.pid,z[row_index],residual,H.c,target_pid,zt)
        pred = prior[target_pid]+delta
        pred[:,:2] = np.clip(pred[:,:2],0,1)
        predicted[method]=pred
    recs,tgs = [],{}
    for role in c.ROLES:
        tg = c.make_target(full,H,sidm,role,allowed_history=hd,forbidden=ev)
        original,verify = tg.scores[base]
        tg.scores['simple']=(original,verify)
        arms=['simple']
        for method,pred in predicted.items():
            ps,pv,ys,yv = pred.T if role=='SV' else pred[:,[1,0,3,2]].T
            pq = {'p_s':ps,'p_v':pv,'S_both':(ys+yv)/2,'S':ys,'L_v':yv}
            score = score_from(pq,base)
            for alpha in WEIGHTS if choices is None else [choices[method]]:
                arm=f'{method}:{alpha:g}'
                tg.scores[arm]=((1-alpha)*original+alpha*score,verify)
                arms.append(arm)
        truth=c.truth_of(full,tg)
        recs.extend(c.run_p2(tg,truth,arm,30) for arm in arms)
        tgs[(full.tissue,sidm,role)]=tg
    return recs,tgs


def run():
    out=HERE/'results'
    if (out/'summary.json').exists():raise FileExistsError('final trial already evaluated')
    ticket=open_vault(HERE/'freeze.json',HERE/'outcome_access.jsonl',
                     purpose='Final adaptive exploratory state-action model; no confirmatory claim',
                     source=ASSETS/'jaaks.csv',root=ROOT)
    panels,_,candidates=build_panels(ticket,path=ASSETS/'jaaks.csv')
    tissues=c.build_tissues(panels,candidates)
    split=json.loads(PARTITION.read_text())['split']
    old=json.loads((HERE.parent/'results/summary.json').read_text())
    frames=context_frames(split)
    drugs=np.load(HERE.parent/'knowledge/drug_kernels.npz',allow_pickle=False)
    pair_phi={t:{m:pair_features(k) for m,k in make_kernels(T,drugs).items() if m in ('network','drug_id')}
              for t,T in tissues.items()}
    summaries,selections,all_records={},{},[]
    for regime,(count,seeds) in REGIMES.items():
        base=old[regime]['choices']['simple']
        dev=[]
        for tissue,full in tissues.items():
            hd,ev=split[tissue]['HD'],split[tissue]['E']
            for seed in seeds:
                for sidm in hd:
                    hist=history_lines(hd,sidm,count,seed,full.code)
                    rec,_=target_records(full,c.restrict(full,hist),sidm,hd,ev,base,frames,pair_phi[tissue])
                    for r in rec:r.update(seed=seed,regime=regime,phase='HD',history_lines=hist)
                    dev.extend(rec)
        totals={arm:sum(average_lines([r for r in dev if r['arm']==arm]).values()) for arm in {r['arm'] for r in dev}}
        choices={m:min(WEIGHTS,key=lambda a:(-totals[f'{m}:{a:g}'],a)) for m in METHODS}
        selections[regime]=dict(base=base,choices=choices,development_confirmed=totals)
        dump(out/'development_selection.json',selections)
        print(f'{regime}: HD chose {choices}',flush=True)
        evaluation,targets=[],{}
        for tissue,full in tissues.items():
            hd,ev=split[tissue]['HD'],split[tissue]['E']
            for seed in seeds:
                for sidm in ev:
                    hist=history_lines(hd,sidm,count,seed,full.code)
                    rec,tgs=target_records(full,c.restrict(full,hist),sidm,hd,ev,base,frames,pair_phi[tissue],choices)
                    targets.update(tgs)
                    for r in rec:r.update(seed=seed,regime=regime,phase='E',history_lines=hist)
                    evaluation.extend(rec)
        selected={m:f'{m}:{choices[m]:g}' for m in METHODS};selected['simple']='simple'
        lv={name:average_lines([r for r in evaluation if r['arm']==arm]) for name,arm in selected.items()}
        keys=c.sort_keys(lv['simple']); ii=c.boot_indices(keys)
        xs={name:np.array([vals[k] for k in keys]) for name,vals in lv.items()}
        if abs(xs['simple'].sum()-old[regime]['totals']['simple_selected'])>1e-8:
            raise AssertionError('selected simple parity failure')
        mats={name:average_pair_matrices([r for r in evaluation if r['arm']==arm],targets,keys,seeds)
              for name,arm in selected.items()}
        s=dict(base=base,choices=choices,n_lines=len(keys),seeds=seeds,
               status='FINAL ADAPTIVE EXPLORATORY; static context interaction, no causal/dynamic-state claim',
               totals={name:float(x.sum()) for name,x in xs.items()},
               vs_simple={name:c.boot_contrast(x,xs['simple'],keys,ii) for name,x in xs.items()},
               by_tissue={name:{t:sum(lv[name][k] for k in keys if k[0]==t) for t in tissues} for name in xs},
               network_contrasts={},
               resource_totals={name:{f:sum(r[f] for r in evaluation if r['arm']==arm)/(2*len(seeds))
                                     for f in ('n_screens','n_verifications','spent','unused')}
                                for name,arm in selected.items()})
        for comp in ('simple','id_context','network_shuffled_context'):
            v=c.boot_contrast(xs['network_context'],xs[comp],keys,ii)
            v['line_pair_sensitivity']=c.two_way(mats['network_context'],mats[comp],keys,resamples=5000)
            s['network_contrasts'][comp]=v
        summaries[regime]=s
        dump(out/f'{regime}_summary.json',s)
        dump(out/f'{regime}_per_line.json',[{'tissue':k[0],'line':k[1],**{name:lv[name][k] for name in lv}} for k in keys])
        for r in dev+evaluation:r.pop('rounds',None)
        all_records.extend(dev+evaluation)
        print(f'{regime}: E totals {s["totals"]}',flush=True)
    with (out/'campaigns.jsonl').open('w') as f:
        for r in all_records:f.write(json.dumps(c.jsonable(r),separators=(',',':'))+'\n')
    dump(out/'summary.json',summaries)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args()
    freeze() if a.freeze else run()
