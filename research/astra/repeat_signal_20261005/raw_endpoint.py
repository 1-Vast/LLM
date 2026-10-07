"""Plate-local, no-fit raw endpoint sensitivity on the fixed repeat menu."""
import json,re,zipfile
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from .analyze import (HERE,ROOT,SOURCE,HIERARCHY,ID,COND,EVENT,SEED,jaaks,canonical,prepare_design,
                      history_priors,wcorr,line_boot,dump,plain,sha256,open_vault)

RAW=HERE/'assets/original_raw.zip'
COLS=['BARCODE','POSITION','TAG','DRUG_ID','CONC','INTENSITY']


def plate_endpoint(f):
    # Control means use unique physical wells, never repeated annotation rows.
    b=f[f.TAG.eq('B')].drop_duplicates('POSITION').INTENSITY.mean()
    nc=f[f.TAG.eq('NC-1')].drop_duplicates('POSITION').INTENSITY.mean()
    allnc=f[f.TAG.isin(['NC-0','NC-1'])].drop_duplicates('POSITION').INTENSITY.mean()
    if not np.isfinite([b,nc,allnc]).all() or min(nc-b,allnc-b)<=0:return None,'invalid_controls'
    kinds={n:f[f.TAG.str.fullmatch(p)].copy() for n,p in {
        'anchor':r'A\d+-S','library':r'L\d+-D\d+-S','ac':r'A\d+-C','lc':r'L\d+-D\d+-C'}.items()}
    for z in kinds.values():
        if not z.empty:z['CONC']=z.CONC.map(canonical)
    a=kinds['anchor'].groupby(['DRUG_ID','CONC']).INTENSITY.mean().rename('anchor_I').reset_index().rename(columns={'DRUG_ID':'ANCHOR_ID','CONC':'ANCHOR_CONC'})
    l=kinds['library'].groupby(['DRUG_ID','CONC']).INTENSITY.mean().rename('library_I').reset_index().rename(columns={'DRUG_ID':'LIBRARY_ID','CONC':'LIBRARY_CONC'})
    # All dose positions are joined here, then the fitted design restricts to the exact highest dose.
    ac=kinds['ac'][['POSITION','DRUG_ID','CONC','INTENSITY']].rename(columns={'DRUG_ID':'ANCHOR_ID','CONC':'ANCHOR_CONC','INTENSITY':'combo_I'})
    lc=kinds['lc'][['POSITION','DRUG_ID','CONC','INTENSITY']].rename(columns={'DRUG_ID':'LIBRARY_ID','CONC':'LIBRARY_CONC','INTENSITY':'library_combo_I'})
    # Multiple compound annotations at a position may represent compound anchors.
    # Exclude that position rather than silently treating a mixture as one drug.
    ac=ac[~ac.POSITION.duplicated(keep=False)];lc=lc[~lc.POSITION.duplicated(keep=False)]
    z=ac.merge(lc,on='POSITION',validate='one_to_one')
    if not np.allclose(z.combo_I,z.library_combo_I,equal_nan=True):raise ValueError('Different intensity attached to same physical well')
    z=z.merge(a,on=['ANCHOR_ID','ANCHOR_CONC'],validate='many_to_one').merge(l,on=['LIBRARY_ID','LIBRARY_CONC'],validate='many_to_one')
    for name,control in [('raw_y',nc),('mixed_control_y',allnc)]:
        scale=control-b
        z[name]=(z.anchor_I-b)*(z.library_I-b)/(scale*scale)-(z.combo_I-b)/scale
    z['BARCODE']=f.BARCODE.iloc[0]
    return z[['BARCODE','ANCHOR_ID','ANCHOR_CONC','LIBRARY_ID','LIBRARY_CONC','raw_y','mixed_control_y']],None


def statistics(d,x='raw_y1',y='raw_y2',weights=None):
    w=np.ones(len(d)) if weights is None else weights
    a=d[x].to_numpy();b=d[y].to_numpy()
    return {'pearson':wcorr(a,b,w),'spearman':wcorr(rankdata(a),rankdata(b),w),
        'residual_shared':wcorr(a-d.prior_full,b-d.prior_full,w),
        'residual_split':np.mean([wcorr(a-d.prior_A,b-d.prior_B,w),wcorr(a-d.prior_B,b-d.prior_A,w)])}


def run():
    out=HERE/'raw_results';out.mkdir(exist_ok=False)
    ticket=open_vault(HERE/'freeze_raw.json',HERE/'outcome_access.jsonl',purpose='POST HOC raw plate-local Bliss endpoint, no curve fitting/shared parameters, fixed repeat selection',source=RAW,root=ROOT)
    assert ticket['data_sha256']=='51550262aed5440d3c5f54997cc940f429ff5dcb55e6970179d3500ba7c5f61e'
    design=prepare_design(jaaks._read(SOURCE,jaaks.DESIGN_COLUMNS),pd.read_csv(HIERARCHY,dtype=str))
    keys=['BARCODE','ANCHOR_ID','ANCHOR_CONC','LIBRARY_ID','LIBRARY_CONC']
    wanted={b:g[keys] for b,g in design[design.in_menu].groupby('BARCODE')}
    parts=[];seen=set();skips={};audit={'raw_rows':0,'plates_seen':0,'wanted_plates':len(wanted)}
    def process(frame):
        for barcode,g in frame.groupby('BARCODE',sort=False):
            if barcode in seen:raise ValueError('Input is not plate-contiguous; must revise streaming implementation')
            seen.add(barcode);audit['plates_seen']+=1
            if barcode not in wanted:continue
            z,reason=plate_endpoint(g)
            if reason:skips[barcode]=reason;continue
            z=wanted[barcode].merge(z,on=keys,how='inner',validate='one_to_one')
            parts.append(z)
    carry=pd.DataFrame()
    with zipfile.ZipFile(RAW) as archive,archive.open(archive.namelist()[0]) as handle:
        for chunk in pd.read_csv(handle,usecols=COLS,dtype={'BARCODE':str,'POSITION':str,'TAG':str,'DRUG_ID':str,'CONC':str},chunksize=300000):
            audit['raw_rows']+=len(chunk)
            frame=pd.concat([carry,chunk],ignore_index=True);last=frame.BARCODE.iloc[-1]
            process(frame[frame.BARCODE.ne(last)]);carry=frame[frame.BARCODE.eq(last)].copy()
        if len(carry):process(carry)
    metadata=list(dict.fromkeys(keys+['Tissue','SIDM','event']+COND+['n_anchor','in_menu']))
    curves=pd.concat(parts,ignore_index=True).merge(design[metadata],on=keys,validate='one_to_one')
    finite=np.isfinite(curves[['raw_y','mixed_control_y']]).all(axis=1)
    audit['nonfinite_curves']=int((~finite).sum());curves=curves[finite]
    per=curves.groupby(EVENT+['ANCHOR_CONC'],as_index=False).agg(raw_y=('raw_y','mean'),mixed_control_y=('mixed_control_y','mean'))
    vals=per.groupby(EVENT,as_index=False).agg(raw_y=('raw_y','max'),mixed_control_y=('mixed_control_y','max'),concs=('ANCHOR_CONC','nunique'))
    meta=design.groupby(EVENT,as_index=False).agg(**{k:(k,'first') for k in COND+['n_anchor','in_menu']})
    events=meta.merge(vals,on=EVENT,how='left',validate='one_to_one');events['valid']=events.concs.eq(events.n_anchor)
    base=pd.read_csv(HERE/'results/paired_actions.csv.gz',dtype={k:str for k in ID+COND})
    repeats=set(base.SIDM);p=base.copy()
    for i in [1,2,3]:
        e=events[ID+['event','raw_y','mixed_control_y','valid']].rename(columns={k:f'{k}{i}' for k in ['event','raw_y','mixed_control_y','valid']})
        p=p.merge(e,on=ID+[f'event{i}'],how='left',validate='many_to_one')
    keep=p.valid1.eq(True)&p.valid2.eq(True)&np.isfinite(p[['raw_y1','raw_y2']]).all(axis=1)
    audit['original_paired_actions']=len(p);p=p[keep].copy();audit['usable_paired_actions']=len(p)
    summaries={};line_rows=[]
    for scale in ['raw_y','mixed_control_y']:
        e=events.copy();e['y']=e[scale]
        # Replace every earlier fitted-endpoint prior with a raw-endpoint prior.
        p,history=history_priors(e,p,repeats)
        perrole=[]
        for (t,s,r),g in p.groupby(['Tissue','SIDM','role']):perrole.append({'Tissue':t,'SIDM':s,'role':r,'scale':scale,'n':len(g),**statistics(g,f'{scale}1',f'{scale}2')})
        roles=pd.DataFrame(perrole);lines=roles.groupby(['Tissue','SIDM']).mean(numeric_only=True).reset_index()
        summaries[scale]={'summary':line_boot(lines),'history':history};line_rows.extend(perrole)
        if scale=='raw_y':
            primary=p.copy();rng=np.random.default_rng(SEED+3);pk=sorted(p.pair.unique());pi={k:i for i,k in enumerate(pk)}
            strata=[list(g.SIDM) for _,g in lines.groupby('Tissue')];groups={s:g for s,g in p.groupby('SIDM')};boot=[]
            for _ in range(1000):
                sample=sum([rng.choice(a,len(a)).tolist() for a in strata],[]);pw=np.bincount(rng.integers(len(pk),size=len(pk)),minlength=len(pk))
                val={}
                for s in set(sample):
                    a=[statistics(g,weights=pw[g.pair.map(pi)]) for _,g in groups[s].groupby('role')]
                    val[s]={k:np.mean([r[k] for r in a]) for k in ['pearson','residual_split']}
                boot.append({k:np.mean([val[s][k] for s in sample]) for k in ['pearson','residual_split']})
            for k in boot[0]:summaries[scale]['summary'][k]['line_pair_ci95']=np.quantile([b[k] for b in boot],[.025,.975]).tolist()
    result={'label':'Post hoc direct highest-dose Bliss endpoint, not author Synergy or independently thawed biology','audit':audit,'skipped_plates':skips,'results':summaries,'ticket':ticket}
    dump(out/'summary.json',plain(result));primary.to_csv(out/'paired_actions.csv.gz',index=False,compression={'method':'gzip','mtime':0});curves.to_csv(out/'plate_endpoints.csv.gz',index=False,compression={'method':'gzip','mtime':0});pd.DataFrame(line_rows).to_csv(out/'per_role.csv',index=False)
    print(json.dumps(plain(result)))

if __name__=='__main__':run()
