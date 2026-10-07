"""Post-hoc dependence check of the already HD-selected sparse-history comparator.

No new predictor, selection or outcome read: response values come solely from saved
campaign receipts. Raw input is restricted to assay design columns to restore pair IDs.
"""
import json
from collections import defaultdict
import numpy as np
import pandas as pd
from .acquire import HERE,ASSETS
from research.astra.confirmation_campaign_20261004.design import campaign as c


def main():
    root=HERE.parents[2]
    builder=json.loads((HERE/'results/builder_report.json').read_text())
    assert builder['qc_rmse_excluded']==builder['missing_excluded']==0
    candidates=json.loads((root/'research/astra/feedback_validation_20261003/results/jaaks_primary/candidates.json').read_text())
    split=json.loads((root/'research/astra/confirmation_campaign_20261004/protocol/partition.json').read_text())['split']
    design=pd.read_csv(ASSETS/'jaaks.csv',usecols=['Tissue','SIDM','ANCHOR_ID','LIBRARY_ID'],dtype=str).drop_duplicates()
    menu={};pair_index={};line_index={};mats={arm:{} for arm in ('S_both','C_mean')}
    for tissue,info in candidates.items():
        d=design[design.Tissue==tissue].copy();S=set(info['S']);V=set(info['V'])
        forward=d.ANCHOR_ID.isin(S)&d.LIBRARY_ID.isin(V)
        backward=d.ANCHOR_ID.isin(V)&d.LIBRARY_ID.isin(S)
        d=d[forward|backward].copy()
        is_s=d.ANCHOR_ID.isin(S)
        d['s']=np.where(is_s,d.ANCHOR_ID,d.LIBRARY_ID)
        d['v']=np.where(is_s,d.LIBRARY_ID,d.ANCHOR_ID)
        d['role']=is_s
        count=d.groupby(['SIDM','s','v']).role.nunique()
        good=count[count==2].index
        for sidm in split[tissue]['E']:
            menu[(tissue,sidm)]=sorted((s,v) for line,s,v in good if line==sidm)
        pairs=sorted({tuple(p) for p in info['pairs_s_v']})
        pair_index[tissue]={p:i for i,p in enumerate(pairs)}
        line_index[tissue]={s:i for i,s in enumerate(sorted(split[tissue]['E']))}
        for arm in mats:mats[arm][tissue]=np.zeros((len(line_index[tissue]),len(pairs)))
    for line in (HERE/'results/campaigns.jsonl').open():
        r=json.loads(line)
        if r['phase']!='E' or r['regime']!='n4' or r['arm'] not in mats:continue
        key=(r['tissue'],r['line']);pairs=menu[key]
        assert len(pairs)==r['n_menu']
        for i in set(r['verification_hits'])&set(r['screen_hits']):
            mats[r['arm']][r['tissue']][line_index[r['tissue']][r['line']],pair_index[r['tissue']][pairs[i]]]+=1/6
    prior=json.loads((HERE/'results/summary.json').read_text())['n4']
    for arm in mats:
        expected=prior['totals']['simple_selected' if arm=='S_both' else 'C_mean']
        assert abs(sum(x.sum() for x in mats[arm].values())-expected)<1e-8
    result=dict(status='Post-hoc comparison of an HD-selected simple baseline; no model revision',
                line_contrast=prior['vs_C_mean']['simple_selected'],
                line_pair_sensitivity=c.two_way(mats['S_both'],mats['C_mean'],c.sort_keys(menu),resamples=5000),
                per_seed_simple=prior['per_seed_totals']['simple_selected'],
                per_seed_C_mean=prior['per_seed_totals']['C_mean'])
    (HERE/'simple_data_efficiency.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
