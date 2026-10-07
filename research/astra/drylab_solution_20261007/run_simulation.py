"""Dry-lab replay. Public menus, private outcomes, paid releases, explicit round budget.

Run: python run_simulation.py
Requires numpy, pandas. No network, LLM, GPU, or wet-lab experiment is invoked.
Source data were previously exposed. Every scientific result here is exploratory.
"""
from __future__ import annotations
import hashlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
KEY = ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID", "LIBRARY_CONC", "anchor_set",
       "SEEDING_DENSITY", "RESEARCH_PROJECT", "DRUGSET_ID", "local_days"]
HKEY = ["Tissue", "ANCHOR_ID", "LIBRARY_ID", "LIBRARY_CONC", "anchor_set"]
SCORES = ["simple_score", "prior_control_score", "hotspot_score", "dependency_score",
          "target_dependency_score", "rna_binary_score"]
FRACTIONS = [.7, .6, .8, .5, .9]  # ties prefer the original contract
PUBLIC = KEY + ["role", "pair"] + SCORES


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_data():
    dtype = {k: str for k in KEY + ["role", "pair"]}
    full = pd.read_csv(ROOT / "data/predictions.csv.gz", dtype=dtype)
    raw = pd.read_csv(ROOT / "data/raw_pairs.csv.gz", dtype=dtype)
    assert not full.duplicated(KEY).any() and not raw.duplicated(KEY).any()
    full = full.merge(raw[KEY + ["raw_y1"]], on=KEY, how="left", validate="one_to_one")
    for col in ["hit1", "hit2"]:
        assert full[col].dtype == bool
    public = full[PUBLIC].copy()  # allowlist: no target labels, future metadata or y1/y2
    assert not any(c.startswith(("hit", "raw_", "event", "y1", "y2", "rank1", "rank2")) for c in public)
    return full, raw, public


@dataclass(frozen=True)
class ReleasedScreen:
    index: int
    positive: bool
    raw: float | None


class ReplayLab:
    """Outcome authority; policies receive only public menus and purchased releases.

    Python object isolation is a code contract, not a security sandbox. Original
    published positive calls are retained; raw endpoints only drive feedback.
    """
    def __init__(self, truth, rounds=2):
        self._truth = truth.reset_index(drop=True)
        self.n = len(truth)
        self.budget = math.ceil(.2 * self.n)
        self.rounds, self.round, self.spent = rounds, 1, 0
        self.screened, self.confirmed, self.hits = {}, set(), set()
        self.trace = []

    def advance(self, round_id):
        if not self.round < round_id <= self.rounds:
            raise ValueError("invalid_round_transition")
        self.round = round_id

    def _check(self, indices, stage):
        values = list(indices)
        if any(isinstance(i, (bool, np.bool_)) or not isinstance(i, (int, np.integer)) for i in values):
            raise ValueError("noninteger_candidate")
        values = [int(i) for i in values]
        if len(values) != len(set(values)) or any(i < 0 or i >= self.n for i in values):
            raise ValueError("duplicate_or_unknown_candidate")
        if self.spent + len(values) > self.budget:
            raise ValueError("budget_exceeded")
        if stage == "screen":
            if self.round >= self.rounds:
                raise ValueError("screen_too_late")
            if any(i in self.screened for i in values):
                raise ValueError("duplicate_screen_purchase")
        else:
            if self.round != self.rounds:
                raise ValueError("confirmation_round_required")
            if any(i not in self.screened or not self.screened[i].positive or i in self.confirmed for i in values):
                raise ValueError("confirmation_prerequisite_or_duplicate")
        return values

    def screen(self, indices):
        values = self._check(indices, "screen")
        out = []
        for i in values:
            row = self._truth.iloc[i]
            raw = float(row.raw_y1) if np.isfinite(row.raw_y1) else None
            value = ReleasedScreen(i, bool(row.hit1), raw)
            self.screened[i] = value
            self.spent += 1
            self.trace.append({"round": self.round, "stage": "screen", "index": i,
                               "pair": row.pair, "positive": value.positive,
                               "raw": raw, "spent": self.spent})
            out.append(value)
        return out

    def confirm(self, indices):
        values = self._check(indices, "confirm")
        for i in values:
            positive = bool(self._truth.iloc[i].hit2)
            self.confirmed.add(i)
            if positive:
                self.hits.add(i)
            self.spent += 1
            self.trace.append({"round": self.round, "stage": "confirm", "index": i,
                               "pair": self._truth.iloc[i].pair, "positive": positive,
                               "spent": self.spent})


def ordering(menu, values):
    return np.lexsort((menu.pair.to_numpy(), -np.asarray(values, float)))


def percentile(values):
    return pd.Series(np.asarray(values)).rank(method="average").to_numpy() / len(values)


def finish(lab, menu, verify_scores):
    if lab.round < lab.rounds:
        lab.advance(lab.rounds)
    possible = [int(i) for i in ordering(menu, verify_scores) if i in lab.screened and lab.screened[i].positive]
    lab.confirm(possible[:lab.budget-lab.spent])
    return {"confirmations": len(lab.hits), "spent": lab.spent, "budget": lab.budget,
            "screened": len(lab.screened), "verified": len(lab.confirmed),
            "unused": lab.budget-lab.spent, "rounds": lab.rounds,
            "screen_ids": sorted(lab.screened), "confirmed_ids": sorted(lab.hits), "trace": lab.trace}


def fixed_replay(truth, menu, column="prior_control_score", fraction=.7):
    lab = ReplayLab(truth, 2)
    ns = math.floor(fraction*lab.budget)
    lab.screen(ordering(menu, menu[column])[:ns].tolist())
    return finish(lab, menu, menu[column])


def feature_kernel(menu, targets=None):
    rows = []
    for row in menu.itertuples():
        values = set()
        for role, drug in [("anchor", row.ANCHOR_ID), ("library", row.LIBRARY_ID)]:
            for component in drug.split("|"):
                if targets is None:
                    values.add(role+":"+component)
                else:
                    genes = targets.get(component, [])
                    values.update(role+":gene:"+g for g in genes)
                    if not genes:
                        values.add(role+":unmapped_drug:"+component)
        rows.append(values)
    cols = {x: i for i, x in enumerate(sorted(set().union(*rows)))}
    X = np.zeros((len(rows), len(cols)))
    for i, row in enumerate(rows):
        for x in row:
            X[i, cols[x]] = 1
    X /= np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1)
    return X @ X.T


def probes(menu, kernel, ns, count=4):
    base = menu.prior_control_score.to_numpy()
    candidates = ordering(menu, base)[:min(len(menu), 2*ns)].tolist()
    selected = [candidates[0]]
    while len(selected) < min(count, ns):
        rest = [i for i in candidates if i not in selected]
        # Diversity is only a proposal; no outcome is available here.
        chosen = min(rest, key=lambda i: (float(np.max(kernel[i, selected])), -base[i], str(menu.pair.iloc[i])))
        selected.append(chosen)
    return selected


def raw_reference(raw, menu):
    target = str(menu.SIDM.iloc[0])
    history = raw[raw.SIDM.ne(target)].copy()
    assert target not in set(history.SIDM)
    tissue = menu.Tissue.iloc[0]
    history = history[history.Tissue.eq(tissue) & np.isfinite(history.raw_y1)]
    mean = float(history.raw_y1.mean())
    scale = max(float(history.raw_y1.std()), .05)
    agg = history.groupby(HKEY).raw_y1.agg(["sum", "count"])
    out = []
    for key in menu[HKEY].itertuples(index=False, name=None):
        if key in agg.index:
            z = agg.loc[key]
            out.append((float(z["sum"])+5*mean)/(float(z["count"])+5))
        else:
            out.append(mean)
    return np.array(out), scale


def feedback_replay(truth, menu, kernel, reference, scale, mode="none", seed=0, probe_ids=None):
    lab = ReplayLab(truth, 3)
    ns = math.floor(.7*lab.budget)
    initial = probes(menu, kernel, ns) if probe_ids is None else probe_ids
    released = lab.screen(initial)
    score = percentile(menu.prior_control_score)
    usable = [x for x in released if x.raw is not None]
    if mode != "none" and usable:
        observed = np.array([x.index for x in usable])
        residual = np.array([(x.raw-reference[x.index])/scale for x in usable])
        if mode == "shuffled":
            residual = np.random.default_rng(seed).permutation(residual)
        delta = kernel[:, observed] @ np.linalg.solve(kernel[np.ix_(observed, observed)]+np.eye(len(observed)), residual)
        score = score + .25 * (delta-delta.mean())
    available = [int(i) for i in ordering(menu, score) if i not in lab.screened]
    lab.advance(2)
    lab.screen(available[:ns-len(initial)])
    result = finish(lab, menu, menu.prior_control_score)
    result["missing_raw_probes"] = sum(x.raw is None for x in released)
    result["probe_ids"] = initial
    return result


def paired_ci(frame, arm, baseline):
    x = frame[frame.arm.isin([arm, baseline])].groupby(["SIDM", "arm"]).confirmations.mean().unstack()
    d = (x[arm]-x[baseline]).to_numpy()
    rng = np.random.default_rng(20261007)
    b = d[rng.integers(len(d), size=(2000, len(d)))].mean(axis=1)
    return {"mean_delta_per_line_role": float(d.mean()), "cell_bootstrap_ci95": np.quantile(b, [.025, .975]).tolist(),
            "improved_cells": int((d>0).sum()), "worse_cells": int((d<0).sum()), "tied_cells": int((d==0).sum())}


def invariants(full, raw, menu):
    results = {}
    g = full[(full.SIDM==full.SIDM.iloc[0]) & (full.role==full.role.iloc[0])].reset_index(drop=True)
    m = g[PUBLIC].copy()
    poison = g.copy()
    poison["hit1"] = ~poison.hit1
    poison["hit2"] = ~poison.hit2
    poison["raw_y1"] = 999
    results["public_menu_unchanged_by_target_outcomes"] = m.equals(poison[PUBLIC])
    k = feature_kernel(m)
    results["first_batch_unchanged_by_target_outcomes"] = probes(m,k,22)==probes(poison[PUBLIC],k,22)
    ref, scale = raw_reference(raw,m)
    a = feedback_replay(g,m,k,ref,scale,"true")
    poison2 = g.copy();poison2["hit2"] = ~poison2.hit2
    b = feedback_replay(poison2,m,k,ref,scale,"true")
    results["R2_poisoning_preserves_all_purchases"] = [(x["round"],x["stage"],x["index"]) for x in a["trace"]] == [(x["round"],x["stage"],x["index"]) for x in b["trace"]]
    checks = [("overspend_rejected", lambda lab: lab.screen(list(range(lab.budget+1)))),
              ("negative_index_rejected", lambda lab: lab.screen([-1])),
              ("float_index_rejected", lambda lab: lab.screen([1.2])),
              ("duplicate_batch_rejected", lambda lab: lab.screen([0,0])),
              ("confirm_without_screen_rejected", lambda lab: (lab.advance(2),lab.confirm([0]))),
              ("screen_at_deadline_rejected", lambda lab: (lab.advance(2),lab.screen([0]))),
              ("duplicate_purchase_rejected", lambda lab: (lab.screen([0]),lab.screen([0])))]
    for name, fn in checks:
        lab = ReplayLab(g)
        try:
            fn(lab)
            results[name] = False
        except ValueError:
            results[name] = True
    assert all(results.values()), results
    return results


def synthetic_controls():
    """Gaussian latent block worlds test information routing, not biological effect."""
    out = {}
    for informative in [False, True]:
        gains = []
        for seed in range(200):
            rng = np.random.default_rng(seed)
            n, blocks = 120, 6
            group = np.arange(n)%blocks
            base = rng.normal(0,.5,n)
            latent = rng.normal(0,1,blocks) if informative else np.zeros(blocks)
            truth = base+latent[group]+rng.normal(0,.2,n)
            # One probe per block: identical procurement for update and no-update.
            probe = np.array([np.argmax(np.where(group==b,base,-np.inf)) for b in range(blocks)])
            observed = truth[probe]+rng.normal(0,.15,len(probe))
            correction = observed-base[probe]
            avail = np.setdiff1d(np.arange(n),probe)
            static = avail[np.argsort(-base[avail])[:18]]
            feedback = avail[np.argsort(-(base[avail]+correction[group[avail]]))[:18]]
            # Independent second measurement at unchanged condition.
            confirm = truth+rng.normal(0,.2,n)
            positive = (truth>1)&(confirm>1)
            gains.append(int(positive[feedback].sum()-positive[static].sum()))
        out["informative" if informative else "no_information"] = {"seeds":200,"mean_extra_confirmations":float(np.mean(gains)),"note":"Synthetic; no biological efficacy claim"}
    assert out["informative"]["mean_extra_confirmations"] > 0
    return out


def main():
    start = time.perf_counter()
    RESULTS.mkdir(exist_ok=True)
    full, raw, _ = load_data()
    annotations = pd.read_csv(ROOT/"data/targets.csv",dtype={"drug_id":str})
    targets = {d: sorted(set(g.gene.dropna().astype(str))) for d,g in annotations.groupby("drug_id")}
    groups = [(t,s,r,g.reset_index(drop=True)) for (t,s,r),g in full.groupby(["Tissue","SIDM","role"])]
    records, grid, traces, cache = [], [], [], {}
    def save(t,s,r,arm,res,seed=0):
        rec = {"Tissue":t,"SIDM":s,"role":r,"arm":arm,"seed":seed}
        rec.update({k:v for k,v in res.items() if k not in ["screen_ids","confirmed_ids","trace","probe_ids"]})
        records.append(rec)
        if seed==0:
            traces.extend(dict(Tissue=t,SIDM=s,role=r,arm=arm,**x) for x in res["trace"])
    for t,s,r,g in groups:
        m = g[PUBLIC]
        for col in SCORES:
            for f in FRACTIONS:
                res = fixed_replay(g,m,col,f)
                cache[(s,r,col,f)] = res
                grid.append({"Tissue":t,"SIDM":s,"role":r,"column":col,"fraction":f,
                             "confirmations":res["confirmations"],"spent":res["spent"]})
                if f==.7:
                    save(t,s,r,"frozen_"+col,res)
        kernel = feature_kernel(m)
        ref, scale = raw_reference(raw,m)
        initial = probes(m,kernel,math.floor(.7*math.ceil(.2*len(m))))
        for arm, mode in [("three_round_static","none"),("three_round_drug_feedback","true")]:
            save(t,s,r,arm,feedback_replay(g,m,kernel,ref,scale,mode,probe_ids=initial))
        target_kernel = feature_kernel(m,targets)
        save(t,s,r,"three_round_target_feedback",feedback_replay(g,m,target_kernel,ref,scale,"true",probe_ids=initial))
        for seed in range(10):
            save(t,s,r,"three_round_shuffled_feedback",feedback_replay(g,m,kernel,ref,scale,"shuffled",seed=seed,probe_ids=initial),seed)
    gridframe = pd.DataFrame(grid)
    choices = []
    for s in sorted(full.SIDM.unique()):
        dev = gridframe[gridframe.SIDM.ne(s)]
        assert s not in set(dev.SIDM)
        for label, cols in [("LOCO_static_budget",["prior_control_score"]),("LOCO_score_and_budget",SCORES)]:
            options = [(col,f) for col in cols for f in FRACTIONS]
            quality = {(col,f): float(dev[dev.column.eq(col)&dev.fraction.eq(f)].confirmations.mean()) for col,f in options}
            col,f = max(options,key=lambda z:quality[z])
            choices.append({"heldout_cell":s,"arm":label,"column":col,"fraction":f,"training_cells":13,
                            "dev_mean_confirmations":quality[(col,f)]})
            for t,ss,r,g in groups:
                if ss==s:
                    save(t,s,r,label,cache[(s,r,col,f)])
    df = pd.DataFrame(records)
    # Average algorithm seeds within each cell-role before averaging/summing biology.
    per = df.groupby(["Tissue","SIDM","role","arm"]).mean(numeric_only=True).reset_index()
    summary = per.groupby("arm").agg(confirmations=("confirmations","sum"),spent=("spent","sum"),
                                    budget=("budget","sum"),rounds=("rounds","max"),unused=("unused","sum")).reset_index()
    baseline = per[per.arm.eq("frozen_prior_control_score")]
    assert baseline.confirmations.sum()==92 and baseline.spent.sum()==762
    for col in SCORES[2:]:
        for t,s,r,g in groups:
            assert cache[(s,r,col,.7)]["confirmed_ids"]==cache[(s,r,"prior_control_score",.7)]["confirmed_ids"]
    diagnostics = {
        "status":"Exploratory replay on exposed data; no trained model promotion",
        "rows":len(full),"cells":int(full.SIDM.nunique()),"campaigns":len(groups),
        "raw_available":int(full.raw_y1.notna().sum()),"raw_missing":int(full.raw_y1.isna().sum()),
        "tests":invariants(full,raw,full[PUBLIC]),"synthetic_controls":synthetic_controls(),
        "contrasts":{},"wall_seconds":time.perf_counter()-start,
        "limits":["Source positive labels are published fitted calls, not event-independent refits.",
                  "Public menus are retrospective complete-repeat subsets, not a prospective sampled menu.",
                  "Raw references use other exposed repeat cells; this is leave-cell-out development, not untouched validation.",
                  "Dose/role keys are preserved. Raw normalized intensities were not independently rebuilt.",
                  "Shared culture and cross-cell drug-pair dependence persist.",
                  "Three rounds may improve or worsen results and impose extra delay; credits do not price this delay.",
                  "No claims about independent cultures, real monetary savings, clinical benefit or LLM contribution."]}
    for arm,base in [("LOCO_static_budget","frozen_prior_control_score"),("LOCO_score_and_budget","LOCO_static_budget"),
                     ("three_round_drug_feedback","three_round_static"),("three_round_target_feedback","three_round_static"),
                     ("three_round_drug_feedback","three_round_shuffled_feedback")]:
        diagnostics["contrasts"][arm+"_minus_"+base] = paired_ci(per,arm,base)
    df.to_csv(RESULTS/"campaigns.csv",index=False)
    summary.to_csv(RESULTS/"summary.csv",index=False)
    gridframe.to_csv(RESULTS/"sensitivity_grid.csv",index=False)
    pd.DataFrame(choices).to_csv(RESULTS/"fold_choices.csv",index=False)
    with (RESULTS/"purchase_traces.jsonl").open("w") as f:
        for trace in traces:
            f.write(json.dumps(trace,ensure_ascii=False,allow_nan=False)+"\n")
    dump(RESULTS/"diagnostics.json",diagnostics)
    dump(RESULTS/"manifest.json",{"source_commit":"96f264312b9296053c1202611b2496e2deb630ac",
                                 "input_sha256":{p.name:sha(p) for p in sorted((ROOT/"data").iterdir())},
                                 "protocol_sha256":sha(ROOT/"PROTOCOL.json"),"script_sha256":sha(__file__)})
    print(summary.to_string(index=False))
    print(json.dumps(diagnostics,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
