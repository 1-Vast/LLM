"""Feasibility probe F1-F4 (exploratory, exposed data, no provider calls).

Block M's agent wrote, for every mechanism class and before any L1000 value was read, claims about
*where* (line_response for the nine lines), *when* (magnitude at 6 h and 24 h) and *which genes*
(proximal/late up/down landmark genes) the mechanism acts. Block M used them only inside a 424-way
falsification set size. This probe scores the claims directly against GSE92742 (all 1,586 block M
drugs; every value was opened by block M, so this is exploratory, not confirmatory).

F1  headroom: is line selectivity of a drug reproducible (6 h vs 24 h, class-mates)?
F2  where: LLM line claims vs generic line pattern, a DepMap genotype rule and class-mates.
F3  when: LLM 6 h/24 h claims vs observed time profile.
F4  which genes: LLM gene directions vs a gene-frequency baseline (Yuan et al. 2026 style).

Output: feasibility/probe_emh_claims.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BLOCK_M = ROOT / "research/astra/mechanism_falsification_20261010"
sys.path.insert(0, str(BLOCK_M))
import intervals as IV  # noqa: E402
import study as S  # noqa: E402

LINES = ("A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP")
DEPMAP_ID = {"A375": "ACH-000219", "A549": "ACH-000681", "HA1E": "ACH-001310", "HCC515": "ACH-000872",
             "HEPG2": "ACH-000739", "HT29": "ACH-000552", "MCF7": "ACH-000019", "PC3": "ACH-000090", "VCAP": "ACH-000115"}
LEVEL = {"none": 0.0, "weak": 1.0, "moderate": 2.0, "strong": 3.0}
DEP = ROOT / "data/external/depmap_19q4"
HUB = ROOT / "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt"
SEED = 20261011


def load():
    o, s = S.load_tier("open"), S.load_tier("sealed")
    X = np.concatenate([o["x"], s["x"]])
    drug = np.concatenate([o["drug"], s["drug"]]).astype(str)
    moa = np.concatenate([o["moa"], s["moa"]]).astype(str)
    return X, drug, moa, list(o["option"]), list(o["gene"])


def activity(X):
    """Percentile of each signature norm among all drugs measured at the same option."""
    n = np.linalg.norm(X, axis=2)
    a = np.full(n.shape, np.nan)
    for j in range(n.shape[1]):
        ok = np.isfinite(n[:, j])
        r = np.argsort(np.argsort(n[ok, j]))
        a[ok, j] = (r + 0.5) / ok.sum()
    return a


def logit(p):
    p = np.clip(p, 0.01, 0.99)
    return np.log(p / (1 - p))


def selectivity(a, options):
    """g[d, t, line]: logit activity centred across lines (NaN where unmeasured); t = 0 (6 h), 1 (24 h)."""
    g = np.full((a.shape[0], 2, len(LINES)), np.nan)
    for t, tag in enumerate(("6 h", "24 h")):
        for i, line in enumerate(LINES):
            g[:, t, i] = logit(a[:, options.index(f"{line}|{tag}")])
        g[:, t] -= np.nanmean(g[:, t], axis=1, keepdims=True)
    return g


def rho(p, q, min_n=5):
    ok = np.isfinite(p) & np.isfinite(q)
    if ok.sum() < min_n or np.nanstd(p[ok]) == 0 or np.nanstd(q[ok]) == 0:
        return np.nan
    return float(spearmanr(p[ok], q[ok]).statistic)


def summary(vals, clusters):
    v = np.asarray(vals, float)
    ok = np.isfinite(v)
    if ok.sum() < 5:
        return {"n": int(ok.sum())}
    est, lo, hi = IV.cluster_bootstrap(v[ok], np.asarray(clusters)[ok], n_boot=1000, seed=SEED)
    return {"n": int(ok.sum()), "mean": est, "ci95": [lo, hi]}


def paired(a, b, clusters):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 5:
        return {"n": int(ok.sum())}
    r = IV.paired_difference(a[ok], b[ok], np.asarray(clusters)[ok], n_boot=1000, seed=SEED)
    return {k: r[k] for k in ("n", "mean_difference", "ci95")}


def emh_table(variant):
    out = {}
    for f in sorted((BLOCK_M / "emh" / variant).glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec.get("status") == "ok" and rec.get("hypothesis"):
            out[rec["mechanism"]] = rec["hypothesis"]
    return out


def emh_lines(h):
    lr = h.get("line_response") or {}
    return np.array([LEVEL.get(str(lr.get(line, "")).lower(), np.nan) for line in LINES])


def emh_time(h):
    m = h.get("magnitude") or {}
    a, b = LEVEL.get(str(m.get("6h", "")).lower(), np.nan), LEVEL.get(str(m.get("24h", "")).lower(), np.nan)
    return b - a


def depmap_genotype(targets_by_drug):
    """Deterministic genotype rule per drug and line: centred log2(TPM+1) of its Hub targets plus 2 x
    the share of its targets carrying a deleterious or hotspot mutation in that line."""
    ids = [DEPMAP_ID[line] for line in LINES]
    rows = []
    for chunk in pd.read_csv(DEP / "CCLE_expression.csv", index_col=0, chunksize=200):
        rows.append(chunk.loc[chunk.index.intersection(ids)])
    expr = pd.concat(rows).reindex(ids)
    expr.columns = [c.split(" (")[0] for c in expr.columns]
    mut = pd.read_csv(DEP / "CCLE_mutations.csv", usecols=["Hugo_Symbol", "DepMap_ID", "Variant_Classification",
                                                         "isDeleterious", "isTCGAhotspot", "isCOSMIChotspot"])
    mut = mut[mut["DepMap_ID"].isin(ids) & (mut["Variant_Classification"] != "Silent")]
    mut = mut[mut["isDeleterious"].fillna(False) | mut["isTCGAhotspot"].fillna(False) | mut["isCOSMIChotspot"].fillna(False)]
    mutated = {(r.Hugo_Symbol, r.DepMap_ID) for r in mut.itertuples()}
    out = {}
    for d, targets in targets_by_drug.items():
        t = [g for g in targets if g in expr.columns]
        if not t:
            continue
        e = expr[t].to_numpy(float)  # (9, n_targets)
        e = e - np.nanmean(e, axis=0, keepdims=True)
        m = np.array([[float((g, i) in mutated) for g in t] for i in ids])
        out[d] = np.nanmean(e, axis=1) + 2.0 * m.mean(axis=1)
    return out


def main() -> dict:
    X, drug, moa, options, genes = load()
    a = activity(X)
    g = selectivity(a, options)
    act_max = np.nanmax(a, axis=1)
    active = act_max >= 0.9
    res = {"n_drugs": int(len(drug)), "n_active": int(active.sum()), "active_rule": "max option activity >= 0.9"}

    # ---------------- F1 headroom
    r_time = np.array([rho(g[d, 0], g[d, 1]) for d in range(len(drug))])
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(drug))
    r_time_null = np.array([rho(g[d, 0], g[perm[d], 1]) for d in range(len(drug))])
    gm = np.nanmean(g, axis=1)  # time-averaged selectivity (d, 9)
    classes = sorted(set(moa))
    mates = {c: np.where(active & (moa == c))[0] for c in classes}
    r_mate, r_generic = np.full(len(drug), np.nan), np.full(len(drug), np.nan)
    for d in np.where(active)[0]:
        others = [j for j in mates[moa[d]] if j != d]
        if others:
            r_mate[d] = rho(np.nanmean(gm[others], axis=0), gm[d])
        rest = active & (moa != moa[d])
        r_generic[d] = rho(np.nanmean(gm[rest], axis=0), gm[d])
    res["F1"] = {"time_6h_vs_24h_active": summary(r_time[active], moa[active]),
                 "time_null_active": summary(r_time_null[active], moa[active]),
                 "classmates_loo_active": summary(r_mate[active], moa[active]),
                 "generic_line_pattern_active": summary(r_generic[active], moa[active]),
                 "classmates_minus_generic": paired(r_mate[active], r_generic[active], moa[active])}

    # ---------------- F2 where (line claims)
    hub = pd.read_csv(HUB, sep="\t", comment="!")
    tmap = {str(r.pert_iname): [t for t in str(r.target).split("|") if t and t != "nan"] for r in hub.itertuples()}
    geno = depmap_genotype({d: tmap.get(d, []) for d in drug})
    r_geno = np.array([rho(geno[d], gm[i]) if d in geno else np.nan for i, d in enumerate(drug)])
    res["F2"] = {"n_drugs_with_targets_in_depmap": int(sum(d in geno for d in drug[active]))}
    for variant in ("nolit", "lit", "lit_critic"):
        E = emh_table(variant)
        pred = {c: emh_lines(h) for c, h in E.items()}
        flat = sum(1 for v in pred.values() if np.nanstd(v) == 0)
        r_llm = np.array([rho(pred[moa[d]], gm[d]) if moa[d] in pred else np.nan for d in range(len(drug))])
        r_llm0 = np.where(np.isnan(r_llm) & np.array([moa[d] in pred for d in range(len(drug))]), 0.0, r_llm)
        cls = list(pred)
        perm_vals = []
        for k in range(20):
            sh = dict(zip(cls, np.random.default_rng(SEED + k).permutation(cls)))
            pv = np.array([rho(pred[sh[moa[d]]], gm[d]) if moa[d] in pred else np.nan for d in range(len(drug))])
            perm_vals.append(np.where(np.isnan(pv) & np.array([moa[d] in pred for d in range(len(drug))]), 0.0, pv))
        r_perm = np.nanmean(np.array(perm_vals), axis=0)
        # does the LLM add to the generic line pattern? (equal-weight z-sum, no fitting)
        r_comb = np.full(len(drug), np.nan)
        for d in np.where(active)[0]:
            if moa[d] in pred and np.nanstd(pred[moa[d]]) > 0:
                rest = active & (moa != moa[d])
                gen = np.nanmean(gm[rest], axis=0)
                z = lambda v: (v - np.nanmean(v)) / (np.nanstd(v) + 1e-9)
                r_comb[d] = rho(z(gen) + z(pred[moa[d]]), gm[d])
            elif moa[d] in pred:
                r_comb[d] = r_generic[d]
        m = active
        res["F2"][variant] = {
            "classes_with_flat_line_claims": flat, "n_classes": len(pred),
            "llm": summary(r_llm0[m], moa[m]), "llm_nonflat_only": summary(r_llm[m], moa[m]),
            "permuted_llm": summary(r_perm[m], moa[m]),
            "llm_minus_permuted": paired(r_llm0[m], r_perm[m], moa[m]),
            "llm_plus_generic_minus_generic": paired(r_comb[m], r_generic[m], moa[m]),
            "llm_minus_genotype_rule": paired(r_llm0[m], r_geno[m], moa[m]),
            "llm_minus_classmates": paired(r_llm0[m], r_mate[m], moa[m]),
        }
    res["F2"]["genotype_rule"] = summary(r_geno[active], moa[active])
    res["F2"]["genotype_rule_minus_generic"] = paired(r_geno[active], r_generic[active], moa[active])

    # ---------------- F3 when (6 h vs 24 h)
    dt = np.nanmean(logit(a[:, [options.index(f"{l}|24 h") for l in LINES]]) - logit(a[:, [options.index(f"{l}|6 h") for l in LINES]]), axis=1)
    res["F3"] = {}
    for variant in ("nolit", "lit", "lit_critic"):
        E = emh_table(variant)
        pt = np.array([emh_time(E[moa[d]]) if moa[d] in E else np.nan for d in range(len(drug))])
        ok = active & np.isfinite(pt) & np.isfinite(dt)
        # class-mates LOO time profile (data ceiling)
        mate_dt = np.array([np.nanmean(dt[[j for j in mates[moa[d]] if j != d]]) if len(mates[moa[d]]) > 1 else np.nan
                            for d in range(len(drug))])
        okm = ok & np.isfinite(mate_dt)
        res["F3"][variant] = {"spearman_llm_vs_observed": float(spearmanr(pt[ok], dt[ok]).statistic), "n": int(ok.sum()),
                              "spearman_classmates_vs_observed": float(spearmanr(mate_dt[okm], dt[okm]).statistic),
                              "spearman_llm_on_same_drugs": float(spearmanr(pt[okm], dt[okm]).statistic), "n_mates": int(okm.sum())}

    # ---------------- F4 which genes (direction claims on active drug x option pairs)
    gi = {gname: i for i, gname in enumerate(genes)}
    act_pairs = [(d, o) for d in np.where(active)[0] for o in range(len(options)) if np.isfinite(a[d, o]) and a[d, o] >= 0.9]
    Z = np.stack([X[d, o] for d, o in act_pairs])
    pair_cls = np.array([moa[d] for d, _ in act_pairs])
    res["F4"] = {"n_active_pairs": len(act_pairs)}
    for variant in ("nolit", "lit"):
        E = emh_table(variant)
        llm_s, freq_s, perm_s, clus = [], [], [], []
        cls_list = list(E)
        sh = dict(zip(cls_list, np.random.default_rng(SEED).permutation(cls_list)))
        for c in sorted(set(pair_cls)):
            if c not in E:
                continue
            idx = np.where(pair_cls == c)[0]
            rest = Z[pair_cls != c]
            up_freq = np.argsort(-np.mean(rest > 1.0, axis=0))
            dn_freq = np.argsort(-np.mean(rest < -1.0, axis=0))

            def score(up, dn, rows):
                if not up and not dn:
                    return np.full(len(rows), np.nan)
                s = np.zeros(len(rows))
                if up:
                    s += np.mean(Z[rows][:, up], axis=1)
                if dn:
                    s -= np.mean(Z[rows][:, dn], axis=1)
                return s / (int(bool(up)) + int(bool(dn)))
            h, hp = E[c], E[sh[c]]
            up = [gi[x] for x in h.get("proximal_up", []) + h.get("late_up", []) if x in gi]
            dn = [gi[x] for x in h.get("proximal_down", []) + h.get("late_down", []) if x in gi]
            upp = [gi[x] for x in hp.get("proximal_up", []) + hp.get("late_up", []) if x in gi]
            dnp = [gi[x] for x in hp.get("proximal_down", []) + hp.get("late_down", []) if x in gi]
            llm_s += list(score(up, dn, idx))
            freq_s += list(score(list(up_freq[:len(up)]), list(dn_freq[:len(dn)]), idx))
            perm_s += list(score(upp, dnp, idx))
            clus += [c] * len(idx)
        res["F4"][variant] = {"llm_signed_mean_z": summary(llm_s, clus), "frequency_baseline": summary(freq_s, clus),
                              "permuted_llm": summary(perm_s, clus),
                              "llm_minus_frequency": paired(llm_s, freq_s, clus), "llm_minus_permuted": paired(llm_s, perm_s, clus)}
    out = HERE / "probe_emh_claims.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, indent=1))
