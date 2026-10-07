"""Observable-condition matched repeats; exploratory, no new holdout claims.

Uses a new freeze with the standard vault. Reuses the author's fitted data and
the repository's cached raw-plate hierarchy. Does not mutate earlier studies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from research.astra.feedback_validation_20261003 import jaaks
from tools.datasets.combination_screens import open_vault, sha256

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "research/astra/knowledge_transfer_20261004/assets/jaaks.csv"
HIERARCHY = ROOT / "research/astra/reproducible_allocation_20261003/repeats/receipts/plate_hierarchy.csv"
PARTITION = ROOT / "research/astra/confirmation_campaign_20261004/protocol/partition.json"
ID = ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID"]
COND = ["LIBRARY_CONC", "anchor_set", "SEEDING_DENSITY", "RESEARCH_PROJECT", "DRUGSET_ID", "local_days"]
EVENT = ID + ["event"]
HKEY = ["Tissue", "ANCHOR_ID", "LIBRARY_ID", "LIBRARY_CONC", "anchor_set"]
NUMERIC = ["SYNERGY_DELTA_EMAX", "SYNERGY_OBS_EMAX", "SYNERGY_RMSE", "LIBRARY_RMSE"]
SEED = 20261005


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def plain(x):
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (tuple, list, np.ndarray)):
        return [plain(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def canonical(v):
    # Composite anchors are preserved rather than interpreted as one scalar.
    return "|".join(format(float(a), ".12g") for a in str(v).split("|"))


def prepare_design(raw, hierarchy):
    h = hierarchy.copy()
    if h.BARCODE.duplicated().any():
        raise ValueError("Nonunique plate hierarchy")
    for source, target in [("seeded", "seed_day"), ("scanned", "read_day")]:
        h[target] = pd.to_datetime(h[source], utc=True).dt.tz_convert("Europe/London").dt.date
    h["local_days"] = [(b-a).days for a, b in zip(h.seed_day, h.read_day)]
    cols = ["BARCODE", "event", "seeded", "seed_day", "local_days", "CELL_ID",
            "SEEDING_DENSITY", "DRUGSET_ID", "RESEARCH_PROJECT", "n_day1"]
    f = raw.merge(h[cols], on="BARCODE", how="left", validate="many_to_one")
    if f.event.isna().any():
        raise ValueError("Unmapped fitted plates")
    if f.duplicated(["BARCODE", "ANCHOR_ID", "LIBRARY_ID", "ANCHOR_CONC", "LIBRARY_CONC"]).any():
        raise ValueError("Duplicate fitted condition in a plate")
    for col in ("ANCHOR_CONC", "LIBRARY_CONC", "SEEDING_DENSITY"):
        f[col] = f[col].map(canonical)
    if (f.groupby(EVENT)[["LIBRARY_CONC", "SEEDING_DENSITY", "local_days", "DRUGSET_ID"]].nunique() > 1).any().any():
        raise ValueError("Multiple assay conditions within an ordered-pair seeding event")
    concentrations = f.groupby(EVENT).ANCHOR_CONC.agg(lambda s: ";".join(sorted(set(s))))
    f = f.join(concentrations.rename("anchor_set"), on=EVENT, validate="many_to_one")
    f["n_anchor"] = f.anchor_set.str.count(";") + 1
    # Design-only S/V partition; restrict to reciprocal ordered combinations.
    f["role"] = "outside"
    for tissue, g in f.groupby("Tissue"):
        side = jaaks.split_drugs(tissue, g)
        a, b = g.ANCHOR_ID.map(side), g.LIBRARY_ID.map(side)
        ok = a.notna() & b.notna() & a.ne(b)
        f.loc[g.index[ok], "role"] = np.where(a[ok].eq("S"), "SV", "VS")
    f["pair"] = ["|".join(sorted([a, b])) for a, b in zip(f.ANCHOR_ID, f.LIBRARY_ID)]
    reciprocal = f[f.role.ne("outside")].groupby(["Tissue", "SIDM", "pair"]).role.nunique()
    good = set(reciprocal[reciprocal.eq(2)].index)
    f["in_menu"] = [(t, s, p) in good for t, s, p in zip(f.Tissue, f.SIDM, f.pair)]
    return f


def event_labels(frame):
    f = frame.copy()
    syn = f.Synergy.astype(str).str.upper().str.strip().map(
        {"TRUE": 1., "FALSE": 0., "1": 1., "0": 0., "1.0": 1., "0.0": 0.})
    if syn.isna().any():
        raise ValueError("Unparseable synergy call")
    f["syn"] = syn
    keep = np.isfinite(f[NUMERIC].to_numpy(float)).all(axis=1) & f.SYNERGY_RMSE.le(.2) & f.LIBRARY_RMSE.le(.2)
    qc = {"rows": len(f), "excluded": int((~keep).sum()), "missing_rmse": int(f[["SYNERGY_RMSE", "LIBRARY_RMSE"]].isna().any(axis=1).sum())}
    design = f.groupby(EVENT, as_index=False).agg(**{x: (x, "first") for x in COND + ["seeded", "CELL_ID", "role", "pair", "in_menu", "n_anchor"]},
                                                    design_plates=("BARCODE", "nunique"), no_day1=("n_day1", lambda s: bool((s.astype(int) == 0).any())))
    per = f[keep].groupby(EVENT + ["ANCHOR_CONC"], as_index=False).agg(y=("SYNERGY_DELTA_EMAX", "mean"), syn=("syn", "mean"), nplates=("BARCODE", "nunique"))
    per["hit"] = per.syn.ge(.5)
    per["strict_hit"] = per.syn.gt(.5)
    lab = per.groupby(EVENT, as_index=False).agg(y=("y", "max"), hit=("hit", "max"), strict_hit=("strict_hit", "max"), valid_concs=("ANCHOR_CONC", "nunique"), plates_min=("nplates", "min"))
    events = design.merge(lab, on=EVENT, how="left", validate="one_to_one")
    events["valid"] = events.valid_concs.eq(events.n_anchor)
    events.loc[~events.valid, ["y", "hit", "strict_hit"]] = np.nan
    return events, f[keep], qc


def choose_repeats(events, repeat_lines, strict=True):
    rows, audit = [], {"ordered_pairs": 0, "no_qualified_two_event_condition": 0, "qc_lost_primary": 0}
    for key, all_events in events[events.SIDM.isin(repeat_lines) & events.in_menu].groupby(ID):
        audit["ordered_pairs"] += 1
        g = all_events.sort_values(["seeded", "event"])
        if strict:
            possible = []
            for condition, z in g[g.n_anchor.eq(2)].groupby(COND):
                if len(z) >= 2:
                    possible.append((-len(z), z.seeded.min(), str(condition), z))
            if not possible:
                audit["no_qualified_two_event_condition"] += 1
                continue
            g = sorted(possible, key=lambda z: z[:3])[0][3].sort_values(["seeded", "event"])
        if len(g) < 2:
            continue
        first = g.iloc[0]
        row = dict(zip(ID, key)) | {x: first[x] for x in COND + ["role", "pair"]}
        row["events_in_condition"] = len(g)
        row["matches_all_conditions_12"] = bool(all(g[x].iloc[0] == g[x].iloc[1] for x in COND))
        for i in range(3):
            for col in ["y", "hit", "strict_hit", "event", "seeded", "CELL_ID", "design_plates", "no_day1"]:
                row[f"{col}{i+1}"] = g[col].iloc[i] if i < len(g) else np.nan
        if not np.isfinite([row["y1"], row["y2"]]).all():
            audit["qc_lost_primary"] += 1
            continue
        row["same_culture_12"] = row["CELL_ID1"] == row["CELL_ID2"]
        row["gap_days_12"] = (pd.Timestamp(row["seeded2"])-pd.Timestamp(row["seeded1"])).total_seconds()/86400
        rows.append(row)
    return pd.DataFrame(rows), audit


def history_priors(events, target, repeat_lines):
    h = events[~events.SIDM.isin(repeat_lines) & events.valid & events.n_anchor.eq(2)].copy()
    # Average seeding events within a line, never let many repeated plates upweight history.
    h = h.groupby(HKEY + ["SIDM"], as_index=False).agg(y=("y", "mean"))
    assert not set(h.SIDM) & repeat_lines
    sets, assignment = {"full": set(h.SIDM), "A": set(), "B": set()}, {}
    rng = np.random.default_rng(SEED)
    for tissue, g in h.groupby("Tissue"):
        lines = rng.permutation(sorted(g.SIDM.unique()))
        a, b = set(lines[::2]), set(lines[1::2])
        sets["A"].update(a); sets["B"].update(b)
        assignment[tissue] = {"A": sorted(a), "B": sorted(b)}
    assert not sets["A"] & sets["B"]
    for name, keep in sets.items():
        hh = h[h.SIDM.isin(keep)]
        mu = hh.groupby("Tissue").y.mean()
        per = hh.groupby(HKEY).y.agg(["sum", "count"])
        pred, count = [], []
        for key in target[HKEY].itertuples(index=False, name=None):
            total, n = per.loc[key] if key in per.index else (0., 0.)
            pred.append((total + 2*mu.loc[key[0]])/(n+2))
            count.append(int(n))
        target[f"prior_{name}"] = pred
        target[f"history_n_{name}"] = count
    return target, {"assignments": assignment, "nonrepeat_lines": len(sets["full"]), "history_rows": len(h), "target_min_history": int(target.history_n_full.min()), "target_zero_history": int(target.history_n_full.eq(0).sum())}


def wcorr(x, y, w):
    w = np.asarray(w, float)
    if w.sum() <= 0:
        return np.nan
    x = np.asarray(x, float); y = np.asarray(y, float)
    dx, dy = x-np.average(x, weights=w), y-np.average(y, weights=w)
    den = np.sqrt(np.sum(w*dx*dx)*np.sum(w*dy*dy))
    return float(np.sum(w*dx*dy)/den) if den > 1e-20 else np.nan


def ratio(n, d):
    return float(n/d) if d else np.nan


def top(x, ids, frac=.2):
    k = int(np.ceil(len(x)*frac))
    order = np.lexsort((np.asarray(ids, str), -np.asarray(x, float)))
    mask = np.zeros(len(x), bool); mask[order[:k]] = True
    return mask


def metrics(g, w=None):
    w = np.ones(len(g)) if w is None else np.asarray(w, float)
    a, b = g.hit1.to_numpy(float), g.hit2.to_numpy(float)
    yy = {k:g[k].to_numpy(float) for k in ["y1", "y2", "prior_full", "prior_A", "prior_B"]}
    a11, a10, a01, a00 = [np.sum(w*z) for z in [a*b, a*(1-b), (1-a)*b, (1-a)*(1-b)]]
    n = w.sum(); p1 = ratio(a11+a10,n); p2=ratio(a11+a01,n)
    chance = p1*p2+(1-p1)*(1-p2)
    z = {"n": n, "pearson": wcorr(yy["y1"], yy["y2"],w),
         "spearman": wcorr(g.rank1,g.rank2,w),
         "residual_shared": wcorr(yy["y1"]-yy["prior_full"], yy["y2"]-yy["prior_full"],w),
         "residual_split": np.mean([wcorr(yy["y1"]-yy["prior_A"], yy["y2"]-yy["prior_B"],w), wcorr(yy["y1"]-yy["prior_B"], yy["y2"]-yy["prior_A"],w)]),
         "positive_agreement": ratio(2*a11,2*a11+a10+a01), "negative_agreement": ratio(2*a00,2*a00+a10+a01),
         "confirmation_given_R1": ratio(a11,a11+a10), "R1_positive":p1,"R2_positive":p2,
         "kappa":ratio(ratio(a11+a00,n)-chance,1-chance),
         "top20_overlap": ratio(np.sum(w*g.top1*g.top2),np.sum(w*g.top1)),
         "random_overlap": ratio(np.sum(w*g.top2),n),
         "mean_shift":ratio(np.sum(w*(yy["y2"]-yy["y1"])),n),
         "mae":ratio(np.sum(w*np.abs(yy["y2"]-yy["y1"])),n),
         "R2_hit_rate_top_R1":ratio(np.sum(w*g.top1*b),np.sum(w*g.top1)),
         "R2_hit_rate_top_prior":ratio(np.sum(w*g.top_prior*b),np.sum(w*g.top_prior)),
         "both_hit_rate_top_R1":ratio(np.sum(w*g.top1*a*b),np.sum(w*g.top1)),
         "both_hit_rate_top_prior":ratio(np.sum(w*g.top_prior*a*b),np.sum(w*g.top_prior))}
    return z


def add_ranks(pairs):
    parts = []
    for _, g in pairs.groupby(["Tissue", "SIDM", "role"]):
        g=g.copy()
        g["rank1"] = rankdata(g.y1); g["rank2"] = rankdata(g.y2)
        g["top1"] = top(g.y1,g.pair); g["top2"] = top(g.y2,g.pair)
        g["top_prior"] = top(g.prior_full,g.pair)
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def line_metrics(pairs):
    records=[]
    for (t,s,r), g in pairs.groupby(["Tissue","SIDM","role"]):
        records.append({"Tissue":t,"SIDM":s,"role":r,**metrics(g)})
    roles=pd.DataFrame(records)
    lines=roles.groupby(["Tissue","SIDM"]).mean(numeric_only=True).reset_index()
    return roles,lines


def line_boot(lines, count=5000):
    cols=[x for x in lines.columns if x not in ["Tissue","SIDM"]]
    rng=np.random.default_rng(SEED)
    idx=[g.index.to_numpy() for _,g in lines.groupby("Tissue")]
    val=lines[cols].to_numpy(float)
    draws=np.concatenate([rng.choice(i,(count,len(i)),replace=True) for i in idx],axis=1)
    means=np.nanmean(val[draws],axis=1)
    return {k:{"mean":float(np.nanmean(val[:,j])),"line_ci95":np.nanquantile(means[:,j],[.025,.975]).tolist(),"defined_lines":int(np.isfinite(val[:,j]).sum())} for j,k in enumerate(cols)}


def two_way(pairs,count=1000):
    # Fixed observed menus, prior, ranks and selected sets; reweight line and pair clusters.
    # Spearman is correlation of the fixed empirical ranks, not re-ranked pseudo-menus.
    rng=np.random.default_rng(SEED+1)
    lines=sorted(pairs.SIDM.unique()); li={s:i for i,s in enumerate(lines)}
    ps=sorted(pairs.pair.unique()); pi={p:i for i,p in enumerate(ps)}
    strata=[np.array([li[s] for s in sorted(g.SIDM.unique())]) for _,g in pairs.groupby("Tissue")]
    groups=[(li[s],g,g.pair.map(pi).to_numpy()) for (_,s,_),g in pairs.groupby(["Tissue","SIDM","role"])]
    selected=["pearson","residual_shared","residual_split","positive_agreement","confirmation_given_R1","top20_overlap"]
    boot=[]
    for _ in range(count):
        lw=np.bincount(np.concatenate([rng.choice(z,len(z)) for z in strata]),minlength=len(lines))
        pw=np.bincount(rng.integers(len(ps),size=len(ps)),minlength=len(ps))
        byline={}
        for j,g,ii in groups:
            if lw[j]:
                m=metrics(g,pw[ii]); byline.setdefault(j,[]).append([m[k] for k in selected])
        v=np.array([np.nanmean(byline[j],axis=0) for j in byline]);w=np.array([lw[j] for j in byline])[:,None]
        good=np.isfinite(v)
        boot.append(np.nansum(v*w,axis=0)/np.sum(good*w,axis=0))
    ci=np.nanquantile(boot,[.025,.975],axis=0)
    return {k:ci[:,j].tolist() for j,k in enumerate(selected)}


def third_event(pairs):
    rows=[]
    for (t,s,r),g in pairs[np.isfinite(pairs.y3)].groupby(["Tissue","SIDM","role"]):
        if len(g)<10:
            continue
        y=g.y3.to_numpy(float); h=g.hit3.to_numpy(float)
        rec={"Tissue":t,"SIDM":s,"role":r,"n":len(g)}
        for name,score in [("R1",g.y1),("R2",g.y2),("mean12",(g.y1+g.y2)/2),("prior",g.prior_full)]:
            sel=top(score,g.pair)
            rec[f"rho_{name}"]=wcorr(rankdata(score),rankdata(y),np.ones(len(y)))
            rec[f"R3_positive_count_{name}"]=float(h[sel].sum())
            rec[f"R1_R3_count_{name}"]=float((h*g.hit1.to_numpy(float))[sel].sum())
            rec[f"R2_R3_count_{name}"]=float((h*g.hit2.to_numpy(float))[sel].sum())
        for m in ["rho","R3_positive_count","R1_R3_count","R2_R3_count"]:
            for control in ["R1","R2","prior"]:
                rec[f"{m}_mean12_minus_{control}"]=rec[f"{m}_mean12"]-rec[f"{m}_{control}"]
        rows.append(rec)
    roles=pd.DataFrame(rows)
    lines=roles.groupby(["Tissue","SIDM"]).mean(numeric_only=True).reset_index()
    return roles,line_boot(lines)


def technical(frame, repeat_lines):
    f=frame[frame.SIDM.isin(repeat_lines) & frame.in_menu & frame.n_anchor.eq(2)]
    per=f.groupby(EVENT+["BARCODE"],as_index=False).agg(y=("SYNERGY_DELTA_EMAX","max"),hit=("syn",lambda x:bool((x>=.5).any())),concs=("ANCHOR_CONC","nunique"),role=("role","first"),pair=("pair","first"))
    rows=[]
    for key,g in per[per.concs.eq(2)].groupby(EVENT):
        if len(g)<2:continue
        g=g.sort_values("BARCODE",key=lambda s:s.astype(int))
        rows.append(dict(zip(EVENT,key))|{"role":g.role.iloc[0],"pair":g.pair.iloc[0],"y1":g.y.iloc[0],"y2":g.y.iloc[1],"hit1":g.hit.iloc[0],"hit2":g.hit.iloc[1]})
    d=pd.DataFrame(rows); out=[]
    for (t,s),g in d.groupby(["Tissue","SIDM"]):
        a,b=g.hit1.astype(float),g.hit2.astype(float)
        out.append({"Tissue":t,"SIDM":s,"n":len(g),"pearson":wcorr(g.y1,g.y2,np.ones(len(g))),"positive_agreement":ratio(2*sum(a*b),sum(a)+sum(b))})
    return d,pd.DataFrame(out)


def run(source=SOURCE):
    out=HERE/"results"
    out.mkdir(exist_ok=False)
    ticket=open_vault(HERE/"freeze.json",HERE/"outcome_access.jsonl",purpose="EXPLORATORY observable-condition repeats; chronological R1/R2/R3; existing exposed Jaaks only",source=source,root=ROOT)
    if ticket["data_sha256"] != "1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278":
        raise ValueError("Unexpected Jaaks release")
    raw=jaaks._read(source,jaaks.DESIGN_COLUMNS+jaaks.OUTCOME_COLUMNS)
    hierarchy=pd.read_csv(HIERARCHY,dtype=str)
    f=prepare_design(raw,hierarchy)
    part=json.loads(PARTITION.read_text())["split"]
    repeat_lines={s for a in part.values() for k in ["repeat_lines_HD","repeat_lines_E"] for s in a[k]}
    assert len(repeat_lines)==14
    events,qframe,qc=event_labels(f)
    strict,audit=choose_repeats(events,repeat_lines,True)
    loose,loose_audit=choose_repeats(events,repeat_lines,False)
    strict,hist=history_priors(events,strict,repeat_lines)
    strict=add_ranks(strict)
    roles,lines=line_metrics(strict)
    main=line_boot(lines);cross=two_way(strict)
    for k,ci in cross.items():main[k]["line_pair_ci95"]=ci
    r3,r3sum=third_event(strict)
    tech,techlines=technical(qframe,repeat_lines)
    # Strict-majority calls without changing selected conditions or continuous rankings.
    sc=strict.copy();sc["hit1"]=sc.strict_hit1;sc["hit2"]=sc.strict_hit2
    _,sl=line_metrics(sc)
    comparison=loose[ID+["event1","event2","matches_all_conditions_12"]].merge(strict[ID+["event1","event2"]],on=ID,how="outer",suffixes=("_old","_strict"),indicator=True)
    both=comparison[comparison._merge.eq("both")]
    qualification={"fitted_rows":len(f),"repeat_rows":int(f.SIDM.isin(repeat_lines).sum()),"repeat_plates":int(f[f.SIDM.isin(repeat_lines)].BARCODE.nunique()),"repeat_events":int(f[f.SIDM.isin(repeat_lines)].event.nunique()),"strict_pairs":len(strict),"lines":strict.SIDM.nunique(),"same_culture_fraction_12":strict.same_culture_12.mean(),"no_day1_either_fraction":(strict.no_day11.astype(bool)|strict.no_day12.astype(bool)).mean(),"gap_days_median":strict.gap_days_12.median(),"local_days":strict.local_days.value_counts().to_dict(),"strict_audit":audit,"loose_audit":loose_audit,"old_pairs":len(loose),"old_conditions_mismatch":int((~loose.matches_all_conditions_12).sum()),"retained_both":len(both),"events_changed":int((both.event1_old.ne(both.event1_strict)|both.event2_old.ne(both.event2_strict)).sum()),"dropped_old":int(comparison._merge.eq("left_only").sum()),"gained_new":int(comparison._merge.eq("right_only").sum())}
    summary={"label":"EXPLORATORY; 14 exposed repeat lines; no noise ceiling or policy verdict","qualification":qualification,"qc":qc,"history":hist,"main":main,"by_tissue":{t:line_boot(g.reset_index(drop=True)) for t,g in lines.groupby("Tissue")},"third_event":r3sum,"technical":line_boot(techlines),"strict_majority":line_boot(sl),"bootstrap":{"line":5000,"line_pair":1000,"line_pair_conditions":"fixed ranks, selected sets, prior and menus; no history refitting","seed":SEED},"ticket":ticket}
    dump(out/"summary.json",plain(summary))
    for name,data in [("events",events[events.SIDM.isin(repeat_lines)]),("paired_actions",strict),("per_role",roles),("per_line",lines),("third_event_per_role",r3),("technical_pairs",tech),("technical_per_line",techlines),("matching_changes",comparison)]:
        data.to_csv(out/f"{name}.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    print(json.dumps(plain({"qualification":qualification,"main":main,"third_event":r3sum}),ensure_ascii=False))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--source",type=Path,default=SOURCE)
    run(parser.parse_args().source)
