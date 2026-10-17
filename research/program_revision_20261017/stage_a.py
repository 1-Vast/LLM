"""Stage A: qualification and implementation diagnostics on exposed SOURCE development data.

File summary
- Path: research/program_revision_20261017/stage_a.py
- Purpose: decide whether the strong model's errors carry decision-relevant structure beyond
  generic potency, overall sensitivity, batch, chemical near-duplicates, missingness and noise,
  and check the revision logic on synthetic worlds. Reads SOURCE drugs x SOURCE lines only
  (`Domain(open_future=False)`); no novel drug or held-out line response is visible.
- Sections (all written to STAGE_A.json):
  - A0 data: missingness, replicate reproducibility, endpoint prevalence.
  - A1 variance decomposition of 3-replicate means.
  - A2 decision ladder on development query lines (cross-fitted): item prior, additive, rank 1,
    strong under I0-I3, drug-specific ridge, strong + seed programs, more probes, and the
    unpriced full-X1-profile reference (a positive reference, not a purchasable design).
  - A3 batch: pool structure of out-of-sample residuals versus a within-lineage pool shuffle.
  - A4 chemical near-duplicates among source drugs.
  - A5 outcome-related missingness among nominations.
  - S1 state aliasing, S2 crossed design, S3 null edits, S4 planted-program positive control.
- Interfaces: ``python -B stage_a.py [--sections A0,A1,...]``.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from common import CACHE, HERE, paired, write_json
from engine import (INFO, STRONG, ContextFold, Domain, fixed_probe_design, nominate, ridge_baseline,
                    score_nominations)
from revise import SEED_LIBRARY, Bench, Edit, EnumerativeProposer, diagnose, evaluate_edit, run_revision
from vc import Program, ProgramLibrary, StrongModel, hit_probability


def dev_folds(dom):
    L = dom.lines
    src = np.flatnonzero(dom.src_line)
    proj, role = L.project.to_numpy(), L.role.to_numpy()
    out = []
    for p in sorted(set(proj[src])):
        q = np.flatnonzero((proj == p) & (role == "query"))
        out.append((p, np.setdiff1d(src, q), q))
    return out


def a0(dom):
    d, l = np.flatnonzero(dom.src_drug), np.flatnonzero(dom.src_line)
    X1, X2, X3 = [X[np.ix_(d, l)] for X in (dom.X1, dom.X2, dom.X3)]
    M = [~np.isfinite(X) for X in (X1, X2, X3)]
    m23 = np.nanmean(np.stack([X2, X3]), 0)
    ok = np.isfinite(X1) & np.isfinite(m23)
    hit = dom.hit[np.ix_(d, l)]
    known = dom.known[np.ix_(d, l)]
    x1hit = (X1 <= np.minimum(-1, dom.med[d][:, None] - 1))
    both_req = np.isfinite(X2) & np.isfinite(X3)
    return {
        "drugs": len(d), "lines": len(l),
        "missing_fraction": {"X1": float(M[0].mean()), "X2": float(M[1].mean()), "X3": float(M[2].mean()),
                             "X2_and_X3": float((M[1] & M[2]).mean())},
        "whole_column_missing_drugs": {"X1": int(M[0].all(1).sum()), "X2": int(M[1].all(1).sum()), "X3": int(M[2].all(1).sum())},
        "endpoint_known_fraction": float(known.mean()),
        "endpoint_known_fraction_if_both_replicates_required": float(both_req.mean()),
        "hit_rate_among_known": float(hit.sum() / known.sum()),
        "hits_per_line_quantiles": np.percentile(hit.sum(0), [10, 50, 90]).tolist(),
        "corr_X1_vs_X2X3_mean": float(np.corrcoef(X1[ok], m23[ok])[0, 1]),
        "P_hit_given_X1_meets_threshold": float(hit[ok & x1hit].mean()),
        "P_hit_given_X1_fails_threshold": float(hit[ok & ~x1hit].mean()),
        "outcome_related_missingness": {
            "frac_X1_le_-1_when_endpoint_known": float(np.nanmean(np.where(known & np.isfinite(X1), X1 <= -1, np.nan))),
            "frac_X1_le_-1_when_endpoint_unknown": float(np.nanmean(np.where(~known & np.isfinite(X1), X1 <= -1, np.nan)))},
        "replicate_variance_median": float(np.median(dom.rep_var[d])),
    }


def a1(dom):
    d, l = np.flatnonzero(dom.src_drug), np.flatnonzero(dom.src_line)
    Y = dom.Ymean[np.ix_(d, l)]
    obs = np.isfinite(Y)
    tot = np.nanvar(Y)
    out = {"total_variance": float(tot)}
    for r in (0, 1, 10, 20):
        if r == 0:
            a = np.nanmean(Y, 1)
            b = np.nanmean(Y - a[:, None], 0)
            fit = a[:, None] + b[None, :]
            ad = np.nanvar(Y - a[:, None])
            out["drug_mean_share"] = float(1 - ad / tot)
        else:
            m = StrongModel(rank=r, lam=2.0, iters=12).fit(Y)
            fit = m.a[:, None] + m.b[None, :] + m.U @ m.V.T
        res = np.where(obs, Y - fit, np.nan)
        out[f"in_sample_R2_rank{r}"] = float(1 - np.nanvar(res) / tot)
    out["replicate_noise_share_of_total(mean_of_3)"] = float(np.median(dom.rep_var[d]) / 3 / tot)
    return out


def ladder(dom, probes):
    folds = dev_folds(dom)
    res = {}
    groups = []
    arms = {}

    def add(name, h, u):
        arms.setdefault(name, {"hits": [], "unknown": []})
        arms[name]["hits"] += list(h)
        arms[name]["unknown"] += list(u)

    probes16 = fixed_probe_design(dom, 16)
    probes32 = fixed_probe_design(dom, 32)
    for p, tr, q in folds:
        groups += [p] * len(q)
        drows = np.flatnonzero(dom.src_drug)
        rate = np.nanmean(np.where(dom.known[np.ix_(drows, tr)], dom.hit[np.ix_(drows, tr)], np.nan), axis=1)
        add("item_prior", *score_nominations(dom, nominate(np.repeat(np.nan_to_num(rate)[:, None], len(q), 1), dom.tie_drug[drows]), drows, q))
        for name, strong in (("additive_rank0", {"rank": 1, "lam": 1e6, "iters": 12}),
                             ("rank1", {"rank": 1, "lam": 2.0, "iters": 12})):
            f = ContextFold(dom, tr, q, "I2", probes, strong=strong)
            add(name, *score_nominations(dom, nominate(f.apply(None)[2], dom.tie_drug[f.drows]), f.drows, q))
        for info in ("I0", "I1", "I2", "I3"):
            f = ContextFold(dom, tr, q, info, probes)
            add(f"strong_{info}", *score_nominations(dom, nominate(f.apply(None)[2], dom.tie_drug[f.drows]), f.drows, q))
            if info == "I2":
                lib = ProgramLibrary([Program(sc, st, "seed") for sc, st in SEED_LIBRARY])
                add("strong_I2+seed_programs", *score_nominations(dom, nominate(f.apply(lib)[2], dom.tie_drug[f.drows]), f.drows, q))
        mean, var = ridge_baseline(dom, tr, q, "I2", probes)
        sc = hit_probability(mean, var[:, None] + dom.rep_var[drows][:, None] / 6, dom.thr[drows][:, None])
        add("drug_ridge_I2", *score_nominations(dom, nominate(sc, dom.tie_drug[drows]), drows, q))
        for name, pr in (("strong_I2_16probes", probes16), ("strong_I2_32probes", probes32)):
            f = ContextFold(dom, tr, q, "I2", pr)
            add(name, *score_nominations(dom, nominate(f.apply(None)[2], dom.tie_drug[f.drows]), f.drows, q))
        allp = list(dom.drugs.core[drows])
        f = ContextFold(dom, tr, q, "I2", allp, inner_folds=2)
        add("reference_full_X1_profile_unpriced", *score_nominations(dom, nominate(f.apply(None)[2], dom.tie_drug[f.drows]), f.drows, q))
    g = np.array(groups)
    base = np.array(arms["strong_I2"]["hits"])
    for k, v in arms.items():
        h = np.array(v["hits"])
        res[k] = {"hits_per_line": float(h.mean()), "unknown_per_line": float(np.mean(v["unknown"])),
                  "vs_strong_I2": paired(h - base, g) if k != "strong_I2" else None}
    res["_note"] = "development query lines of the 10 source projects; cross-fitted; K=10 nominations"
    res["_probes"] = {"8": probes, "16": probes16, "32": probes32}
    return res


def a3_batch(dom, probes):
    """Within-drug residual variance explained by pool versus by a within-lineage pool shuffle."""

    src = np.flatnonzero(dom.src_line)
    f = ContextFold(dom, src, src[:1], "I2", probes)
    R = f.R_train
    pools = dom.lines.pool_id.to_numpy()[f.train]
    lin = dom.lines.primary_tissue.to_numpy()[f.train]

    def explained(labels):
        tot, ex = 0.0, 0.0
        for d in range(R.shape[0]):
            r = R[d]
            o = np.isfinite(r)
            if o.sum() < 20:
                continue
            rr = r[o] - r[o].mean()
            tot += (rr ** 2).sum()
            for g in set(labels[o]):
                m = labels[o] == g
                ex += m.sum() * rr[m].mean() ** 2
        return ex / tot

    rng = np.random.default_rng(20261017)
    shuffled = []
    for _ in range(5):
        perm = pools.copy()
        for t in set(lin):
            idx = np.flatnonzero(lin == t)
            perm[idx] = rng.permutation(perm[idx])
        shuffled.append(explained(perm))
    return {"pool_share_of_residual_variance": explained(pools),
            "within_lineage_shuffled_pool_share_mean": float(np.mean(shuffled)),
            "lineage_share_of_residual_variance": explained(lin),
            "n_pools": int(len(set(pools)))}


def a4_near_duplicates(dom):
    from rdkit import DataStructs
    from rdkit.Chem import rdFingerprintGenerator, MolFromSmiles
    d = np.flatnonzero(dom.src_drug)
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = [gen.GetFingerprint(MolFromSmiles(str(s).split(",")[0].strip())) for s in dom.drugs.smiles[d]]
    l = np.flatnonzero(dom.src_line)
    Y = dom.Ymean[np.ix_(d, l)]
    close, rnd = [], []
    rng = np.random.default_rng(1)
    for i in range(len(d)):
        sims = np.array(DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:]))
        for j in np.flatnonzero(sims >= 0.8):
            a, b = Y[i], Y[i + 1 + j]
            o = np.isfinite(a) & np.isfinite(b)
            if o.sum() > 20:
                close.append(np.corrcoef(a[o], b[o])[0, 1])
    for _ in range(500):
        i, j = rng.choice(len(d), 2, replace=False)
        o = np.isfinite(Y[i]) & np.isfinite(Y[j])
        if o.sum() > 20:
            rnd.append(np.corrcoef(Y[i][o], Y[j][o])[0, 1])
    return {"source_pairs_tanimoto_ge_0.8": len(close),
            "median_response_corr_near_duplicates": float(np.median(close)) if close else None,
            "median_response_corr_random_pairs": float(np.median(rnd)),
            "note": "novel drugs: see SPLITS.json max-Tanimoto census (median 0.316; 8 with Tc >= 0.6)"}


# ---------------------------------------------------------------- synthetic checks

def synthetic_domain(dom, effect, seed=7, noise_sd=0.5):
    """Copy of the real domain whose SOURCE responses are replaced by a low-rank world + effect."""

    import copy
    s = copy.copy(dom)
    s._model_cache = {}
    rng = np.random.default_rng(seed)
    d, l = np.flatnonzero(dom.src_drug), np.flatnonzero(dom.src_line)
    m = StrongModel(rank=5, lam=2.0, iters=8).fit(dom.Ymean[np.ix_(d, l)])
    base = m.a[:, None] + m.b[None, :] + m.U @ m.V.T + effect
    X = [np.full(dom.X1.shape, np.nan) for _ in range(3)]
    for k in range(3):
        X[k][np.ix_(d, l)] = base + rng.normal(0, noise_sd, base.shape)
    s.X1, s.X2, s.X3 = X
    st = np.stack(X)
    s.Ymean = np.nanmean(st, 0)
    from common import qualified_hits
    s.hit, s.known = qualified_hits(X[1], X[2], line_mask=dom.src_line)
    m23 = np.nanmean(np.stack([X[1], X[2]]), 0)
    s.med = np.nanmedian(m23[:, dom.src_line], axis=1)
    s.thr = np.minimum(-1.0, s.med - 1.0)
    s.rep_var = np.full(len(dom.drugs), noise_sd ** 2)
    s.true_mean = np.full(dom.X1.shape, np.nan)
    s.true_mean[np.ix_(d, l)] = base
    s.noise_sd = noise_sd
    return s


def _summ(c):
    return {k: c.get(k) for k in ("edit", "decision", "reason", "llr", "hits_new_only", "hits_cur_only",
                                  "distinguishing_pairs", "wells_new")}


def _query_gain(sdom, bench, lib):
    """Mean hits/line on development query lines: strong, strong + library, and the unattainable
    ceiling that ranks by the generating mean (noise-only uncertainty)."""

    h0, h1, h2 = [], [], []
    for p in bench.projects:
        f = bench.query[p]
        mean, var, sc = f.apply(None)
        h0 += list(score_nominations(sdom, nominate(sc, sdom.tie_drug[f.drows]), f.drows, f.target)[0])
        if lib is not None:
            sc1 = f.apply(lib)[2]
            h1 += list(score_nominations(sdom, nominate(sc1, sdom.tie_drug[f.drows]), f.drows, f.target)[0])
        if hasattr(sdom, "true_mean"):
            mo = sdom.true_mean[np.ix_(f.drows, f.target)]
            sc2 = hit_probability(mo, np.full(mo.shape, sdom.noise_sd ** 2 / 2), sdom.thr[f.drows][:, None])
            h2 += list(score_nominations(sdom, nominate(sc2, sdom.tie_drug[f.drows]), f.drows, f.target)[0])
    return {"strong": float(np.mean(h0)), "strong_plus_library": float(np.mean(h1)) if h1 else None,
            "ceiling_true_mean": float(np.mean(h2)) if h2 else None}


def _diag_rank(bench, scope, state):
    d = diagnose(bench, ProgramLibrary(), None, top=200)
    for i, c in enumerate(d["clusters"]):
        if c["scope"] == scope and c["state"] == state:
            return i + 1, c["t_all_support"]
    return None, None


def synthetic_checks(dom, probes):
    from vc import LineContext, Program, parse_state, scope_mask
    d, l = np.flatnonzero(dom.src_drug), np.flatnonzero(dom.src_line)
    n_d = len(dom.drugs)
    out = {}
    ctx = LineContext(dom.lf, np.arange(len(dom.lines)), {}, np.zeros(len(dom.lines)))
    mek = np.zeros(n_d, bool)
    mek[d] = scope_mask("moa:MEK inhibitor", dom.df, d)

    F = np.column_stack([np.ones(len(dom.lines)), dom.lf["lineage"], dom.lf["panel"]])

    def planted(state, size=-2.5, orthogonal=False):
        v = ctx.state(parse_state(state)) if state else np.zeros(len(dom.lines))
        if orthogonal:
            coef, *_ = np.linalg.lstsq(F[l], v[l], rcond=None)
            v = v - F @ coef
            v = v / (v[l].std() + 1e-9)
        return size * np.outer(mek, v)[np.ix_(d, l)], size * np.outer(mek, v)

    # S4 positive controls: (a) linear in a legal feature; (b) a conjunction the linear prior cannot express
    for tag, state, orth in (("S4a_planted_linear_mut", "mut:BRAF", False),
                             ("S4b_planted_conjunction", "and(mut:KRAS,mut:TP53)", False),
                             ("S4c_planted_conjunction_orthogonal", "and(mut:KRAS,mut:TP53)", True)):
        eff, eff_full = planted(state, -1.5 if orth else -2.5, orth)
        sdom = synthetic_domain(dom, eff)
        bench = Bench(sdom, "I1", probes)
        rank, t = _diag_rank(bench, "moa:MEK inhibitor", state)
        cur = bench.commit(ProgramLibrary())
        true_rec, ok = evaluate_edit(bench, ProgramLibrary(), cur, Edit("add", scope="moa:MEK inhibitor", state=state, origin="planted-truth", direction="sensitising"))
        decoy_rec, _ = evaluate_edit(bench, ProgramLibrary(), cur, Edit("add", scope="moa:HDAC inhibitor", state="mut:TP53", origin="decoy"))
        lib_e, traj_e, acc_e = run_revision(bench, ProgramLibrary(), EnumerativeProposer(6), rounds=1)
        out[tag] = {"state": state, "orthogonalised_to_linear_features": orth,
                    "positive_source_lines": int(ctx.state(parse_state(state))[l].sum()),
                    "diagnosis_rank_of_truth": rank, "diagnosis_t": t,
                    "truth_edit": _summ(true_rec), "decoy_edit": _summ(decoy_rec),
                    "enumerative_final_library": lib_e.keys(), "enumerative_accounting": acc_e,
                    "query_hits": _query_gain(sdom, bench, ok[0] if ok else ProgramLibrary()),
                    "query_hits_enumerative": _query_gain(sdom, bench, lib_e)}
        if tag == "S4a_planted_linear_mut":
            # S3 null edits on this world: exact and semantic duplicates must earn zero credit
            base = ProgramLibrary([Program("moa:MEK inhibitor", "mut:BRAF", "seed")])
            commit = bench.commit(base)
            nulls = []
            for e in (Edit("add", scope="moa:MEK inhibitor", state="mut:BRAF", origin="null-duplicate"),
                      Edit("narrow", key="moa:MEK inhibitor|mut:BRAF", scope="moa:MEK inhibitor", origin="null-same-scope"),
                      Edit("replace_state", key="moa:MEK inhibitor|mut:BRAF", state="mut:BRAF", origin="null-same-state"),
                      Edit("add", scope="moa:MEK inhibitor", state="and(mut:BRAF,mut:BRAF)", origin="null-idempotent"),
                      Edit("replace_state", key="moa:MEK inhibitor|mut:BRAF", state="and(mut:BRAF,mut:BRAF)", origin="null-rewrite"),
                      Edit("add", scope="moa:MEK inhibitor", state="mut:NOT_A_PANEL_GENE", origin="null-illegal")):
                rec, _ = evaluate_edit(bench, base, commit, e)
                nulls.append(_summ(rec))
            out["S3_null_edits"] = nulls
    # S3b null world: no planted structure; how often does the frozen rule accept an edit?
    sdom0 = synthetic_domain(dom, np.zeros((len(d), len(l))), seed=9)
    bench0 = Bench(sdom0, "I1", probes)
    lib0, traj0, acc0 = run_revision(bench0, ProgramLibrary(), EnumerativeProposer(6), rounds=1)
    out["S3b_null_world"] = {"accepted": [c["edit"] for e in traj0 for c in e["candidates"] if c["decision"] == "accepted"],
                             "acceptable": int(sum(c["decision"] in ("accepted", "acceptable_not_chosen") for e in traj0 for c in e["candidates"])),
                             "evaluated": acc0["evaluated"], "wells": acc0["distinguishing_wells"],
                             "query_hits": _query_gain(sdom0, bench0, lib0)}
    # S1 state aliasing: effect follows a hidden line state that no genomic atom measures
    rng = np.random.default_rng(11)
    hidden = np.zeros(len(dom.lines))
    hidden[:] = (rng.random(len(dom.lines)) < 0.3)
    eff_full = -2.5 * np.outer(mek, hidden)
    sdom1 = synthetic_domain(dom, eff_full[np.ix_(d, l)], seed=8)
    s1 = {}
    for info in ("I1", "I2"):
        bench1 = Bench(sdom1, info, probes)
        lib1, traj1, acc1 = run_revision(bench1, ProgramLibrary(), EnumerativeProposer(6), rounds=1)
        s1[info] = {"accepted": [c["edit"] for e in traj1 for c in e["candidates"] if c["decision"] == "accepted"],
                    "evaluated": acc1["evaluated"], "query_hits": _query_gain(sdom1, bench1, lib1)}
    s1["probe_in_scope"] = [c for c in probes if mek[dom.drug_index[c]]]
    s1["reading"] = ("I1 has no legal atom correlated with the hidden state (aliasing: oracle gain is not reachable); "
                     "under I2 a probe drug inside the scope measures the state directly")
    out["S1_state_aliasing"] = s1
    out["S2_crossed_design"] = crossed_design_check(dom)
    from revise import identifiable
    sc = mek[d]
    g = ctx.state(parse_state("mut:BRAF"))[l] > 0.5
    real = np.isfinite(dom.Ymean[np.ix_(d, l)])
    crossed = real & (np.outer(sc, g) | np.outer(~sc, ~g))
    out["S2_crossed_design"]["validator_identifiable_real_pattern"] = identifiable(real, sc, g)
    out["S2_crossed_design"]["validator_identifiable_crossed_pattern"] = identifiable(crossed, sc, g)
    return out


class _Fixed:
    name = "fixed-test"

    def __init__(self, edits):
        self.edits = edits
        self.used = False

    def propose(self, diagnosis, lib, bench):
        if self.used:
            return [], {}
        self.used = True
        return list(self.edits), {}


def crossed_design_check(dom):
    """Identifiability of a scope x gate interaction under two observation patterns."""

    from vc import scope_mask
    d, l = np.flatnonzero(dom.src_drug)[:200], np.flatnonzero(dom.src_line)
    scope = scope_mask("moa:MEK inhibitor", dom.df, np.flatnonzero(dom.src_drug))[:200]
    gi = list(dom.lf["panel_genes"]).index("BRAF")
    gate = dom.lf["panel"][l, gi] > 0.5

    def rank_deficit(mask):
        rows = []
        for i in range(len(d)):
            for j in range(len(l)):
                if mask[i, j]:
                    x = np.zeros(len(d) + len(l) + 1)
                    x[i] = 1
                    x[len(d) + j] = 1
                    x[-1] = float(scope[i] and gate[j])
                    rows.append(x)
        X = np.array(rows)
        r_full = np.linalg.matrix_rank(X)
        r_main = np.linalg.matrix_rank(X[:, :-1])
        return {"rank_with_interaction": int(r_full), "rank_main_effects_only": int(r_main),
                "interaction_identifiable": bool(r_full > r_main)}

    full = np.ones((len(d), len(l)), bool)
    crossed = np.outer(scope, gate) | np.outer(~scope, ~gate)
    return {"complete_design": rank_deficit(full), "crossed_design": rank_deficit(crossed),
            "reading": "when scope drugs are observed only in gate-on lines and others only in gate-off lines, "
                       "the interaction column lies in the span of drug and line offsets"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", default="A0,A1,A2,A3,A4,S")
    ap.add_argument("--merge", action="store_true", help="combine section parts into STAGE_A.json")
    args = ap.parse_args()
    parts = CACHE / "stage_a_parts"
    parts.mkdir(parents=True, exist_ok=True)
    if args.merge:
        out = {}
        for sec in ("meta", "A0", "A1", "A2", "A3", "A4", "S"):
            f = parts / f"{sec}.json"
            if f.exists():
                out.update(json.loads(f.read_text(encoding="utf-8")))
        write_json(HERE / "STAGE_A.json", out)
        print(sorted(out))
        return
    t0 = time.time()
    dom = Domain(open_future=False)
    probes = fixed_probe_design(dom, 8)
    write_json(parts / "meta.json", {"strong_model": STRONG, "probes_fixed_design": probes,
                                     "probe_names": [dom.drugs.name[dom.drug_index[c]] for c in probes]})
    jobs = {"A0": ("A0_data", lambda: a0(dom)), "A1": ("A1_variance", lambda: a1(dom)),
            "A2": ("A2_decision_ladder", lambda: ladder(dom, probes)), "A3": ("A3_batch", lambda: a3_batch(dom, probes)),
            "A4": ("A4_near_duplicates", lambda: a4_near_duplicates(dom)), "S": ("synthetic", lambda: synthetic_checks(dom, probes))}
    for sec in args.sections.split(","):
        name, fn = jobs[sec]
        t = time.time()
        res = fn()
        write_json(parts / f"{sec}.json", {name: res, f"_seconds_{sec}": round(time.time() - t, 1)})
        print(sec, round(time.time() - t0, 1), json.dumps(res)[:3000], flush=True)


if __name__ == "__main__":
    main()
