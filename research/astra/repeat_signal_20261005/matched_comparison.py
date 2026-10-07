"""Post hoc matched-population orientation vs repetition diagnostic."""
import json
import numpy as np
import pandas as pd
from .analyze import HERE,ROOT,SEED,plain,dump,sha256,wcorr,line_boot


def calculate(g,w=None):
    w=np.ones(len(g)) if w is None else w
    def corr(a,b):return wcorr(a,b,w)
    out={}
    for scale in ['raw','shared','split']:
        def r(x,rx,y,ry):
            xx=g[f'y{rx}_{x}'].to_numpy();yy=g[f'y{ry}_{y}'].to_numpy()
            if scale=='raw':return corr(xx,yy)
            if scale=='shared':return corr(xx-g[f'prior_full_{x}'],yy-g[f'prior_full_{y}'])
            return np.mean([corr(xx-g[f'prior_A_{x}'],yy-g[f'prior_B_{y}']),corr(xx-g[f'prior_B_{x}'],yy-g[f'prior_A_{y}'])])
        same=np.mean([r('SV','1','SV','2'),r('VS','1','VS','2')])
        cross=np.mean([r('SV','1','VS','1'),r('SV','2','VS','2')])
        out[f'{scale}_same']=same;out[f'{scale}_cross']=cross
        out[f'{scale}_same_minus_cross']=same-cross
        out[f'{scale}_cross_averaged']=r('SV','avg','VS','avg')
    return out


def run():
    f=json.loads((HERE/'freeze_matched.json').read_text())
    assert all(sha256(ROOT/p)==d for p,d in f['files'].items())
    d=pd.read_csv(HERE/'results/paired_actions.csv.gz',dtype={'ANCHOR_ID':str,'LIBRARY_ID':str})
    keep=['Tissue','SIDM','pair','y1','y2','prior_full','prior_A','prior_B']
    p=d[d.role.eq('SV')][keep].merge(d[d.role.eq('VS')][keep],on=['Tissue','SIDM','pair'],suffixes=('_SV','_VS'),validate='one_to_one')
    for r in ['SV','VS']:p[f'yavg_{r}']=(p[f'y1_{r}']+p[f'y2_{r}'])/2
    rows=[]
    for (t,s),g in p.groupby(['Tissue','SIDM']):rows.append({'Tissue':t,'SIDM':s,'n':len(g),**calculate(g)})
    line=pd.DataFrame(rows);summary=line_boot(line)
    rng=np.random.default_rng(SEED+2);keys=sorted(p.pair.unique());ki={k:i for i,k in enumerate(keys)}
    groups={s:g for s,g in p.groupby('SIDM')};strata=[list(g.SIDM) for _,g in line.groupby('Tissue')]
    boot=[]
    for _ in range(1000):
        sample=sum([rng.choice(z,len(z)).tolist() for z in strata],[])
        pw=np.bincount(rng.integers(len(keys),size=len(keys)),minlength=len(keys))
        values={s:calculate(groups[s],pw[groups[s].pair.map(ki)]) for s in set(sample)}
        boot.append({k:np.nanmean([values[s][k] for s in sample]) for k in next(iter(values.values()))})
    for k in boot[0]:summary[k]['line_pair_ci95']=np.quantile([v[k] for v in boot],[.025,.975]).tolist()
    result={'label':'Post hoc matched-population diagnostic; not causal separation or noise ceiling','unordered_pair_x_line':len(p),'lines':len(line),'summary':summary,'by_tissue':{t:line_boot(g.reset_index(drop=True)) for t,g in line.groupby('Tissue')}}
    line.to_csv(HERE/'results/matched_orientation_per_line.csv',index=False)
    dump(HERE/'results/matched_orientation.json',plain(result))
    print(json.dumps(plain(result['summary'])))

if __name__=='__main__':run()
