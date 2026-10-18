"""Audit 1: the evaluation contract (replicate aggregation, reference, threshold, uncertainty).

File summary
- Path: research/seed_attribution_20261017/audit_contract.py
- Purpose: measure, on the exposed PRISM 19Q4 data, what the frozen `program_revision_20261017`
  implementation does where `common.qualified_hits` and `engine.Domain` disagree, what the
  library's variance estimate does out of sample, and what both change in the frozen decisions.
  Development analysis only; no frozen file or result is edited.
- Sections written to AUDIT_CONTRACT.json:
  - mismatch: how many pairs and drugs rest on one replicate, how many source drugs have an undefined
    frozen threshold (NaN, so they are never nominated), the threshold differences, and the label flips
    that would follow if the frozen score threshold had defined the endpoint;
  - variance: frozen (fitted-on-the-same-residuals) versus cross-fitted library variance, and the mean
    standardised squared error of each on the held-out target lines (1.0 is calibrated);
  - decisions: the frozen implementation and each repair, S and the seed library, I1 and I2, paired per
    line with a cluster bootstrap over lineages, including the number of nominations that change;
  - event: sign-condition discordance and reliability of the Gaussian crossing score.
- Interfaces: ``python -B audit_contract.py`` (writes AUDIT_CONTRACT.json once; refuses if present).
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corrected as C  # noqa: E402
import contract  # noqa: E402
import engine  # noqa: E402
import revise  # noqa: E402
from common import paired, write_json  # noqa: E402
from vc import Program, ProgramLibrary  # noqa: E402

warnings.filterwarnings("ignore")
OUT = HERE / "AUDIT_CONTRACT.json"


def seed_library() -> ProgramLibrary:
    return ProgramLibrary([Program(s, g, "seed") for s, g in revise.SEED_LIBRARY])


def hits_of(truth, score, fold, T):
    nom = engine.nominate(score, truth.tie_drug[fold.drows])
    h, u = engine.score_nominations(truth, nom, fold.drows, T)
    return nom, h, u


def summarise(h, groups, label):
    return {"label": label, "hits_per_line": float(np.mean(h))}


def main() -> None:
    if OUT.exists():
        raise SystemExit("AUDIT_EXISTS")
    t0 = time.time()
    frozen = engine.Domain(open_future=True)
    cor = C.CorrectedDomain(open_future=True)
    ep = cor.endpoint
    src_line, src_drug = cor.src_line, cor.src_drug
    drows = np.flatnonzero(src_drug)
    train = np.flatnonzero(src_line)
    L = cor.lines
    T = np.flatnonzero(L.line_split.isin(["future_line", "future_lineage"]).to_numpy())
    groups = L.primary_tissue.to_numpy()[T]
    probes = json.loads((HERE.parent / "program_revision_20261017" / "LIBRARIES.json").read_text(encoding="utf-8"))["_bench"]["probes"]
    out = {"status": "DEVELOPMENT (exposed PRISM 19Q4; no frozen result edited)"}

    # ---------------------------------------------------------------- 1. mismatch census
    sd = src_drug[:, None] & src_line[None, :]
    fut = src_drug[:, None] & ~src_line[None, :]
    n_rep = ep.n_rep
    frozen_nan = ~np.isfinite(frozen.thr) & src_drug
    contract_nan = ep.undefined_reference & src_drug
    both_med = np.where(ep.n_rep == 2, ep.m, np.nan)
    with np.errstate(all="ignore"):
        med_both = np.nanmedian(both_med[:, src_line], axis=1)
    thr_both = np.where(np.isfinite(med_both), np.minimum(-1.0, med_both - 1.0), np.nan)
    both_def = src_drug & np.isfinite(thr_both) & np.isfinite(ep.thr)
    diff = (ep.thr - thr_both)[both_def]
    # labels if the frozen score threshold had defined the endpoint
    with np.errstate(invalid="ignore"):
        hit_frozen_thr = ep.known & ep.negative & (ep.m <= frozen.thr[:, None])
    flips = (hit_frozen_thr != ep.hit)
    fut_hits = ep.hit & fut
    out["mismatch"] = {
        "pairs_source_block": {"both_replicates": float((n_rep[sd] == 2).mean()), "one_replicate": float((n_rep[sd] == 1).mean()),
                               "none": float((n_rep[sd] == 0).mean())},
        "known_pairs_resting_on_one_replicate_source": float((n_rep[sd] == 1).sum() / (n_rep[sd] >= 1).sum()),
        "future_hits": int(fut_hits.sum()),
        "future_hits_on_one_replicate": int((fut_hits & (n_rep == 1)).sum()),
        "source_drugs": int(src_drug.sum()),
        "frozen_threshold_undefined_source_drugs": int(frozen_nan.sum()),
        "frozen_undefined_never_nominated": "NaN scores sort last in lexsort; checked in the decisions section",
        "contract_threshold_undefined_source_drugs": int(contract_nan.sum()),
        "restored_by_contract": int((frozen_nan & ~contract_nan).sum()),
        "frozen_undefined_drugs_future_hit_share": float(fut_hits[frozen_nan].sum() / fut_hits[src_drug].sum()),
        "threshold_differs_drugs": int((np.abs(diff) > 1e-9).sum()),
        "threshold_defined_in_both": int(both_def.sum()),
        "threshold_difference_contract_minus_frozen": {"mean": float(diff.mean()), "max_abs": float(np.abs(diff).max()),
                                                       "quantiles_abs": [float(x) for x in np.quantile(np.abs(diff), [0.5, 0.9, 0.99])]},
        "label_flips_if_frozen_threshold_defined_the_endpoint": {"future_block": int(flips[fut].sum()), "source_block": int(flips[sd].sum())},
        "hits_future_block_contract": int(ep.hit[fut].sum()),
        "hits_future_block_with_frozen_threshold": int(hit_frozen_thr[fut].sum()),
    }
    print("mismatch done", round(time.time() - t0), flush=True)

    # ---------------------------------------------------------------- folds
    folds = {}
    for info in ("I1", "I2"):
        folds[info] = C.SafeContextFold(cor, train, T, info, probes)
    seed = seed_library()
    thr_frozen = frozen.thr[drows]
    thr_cor = np.where(np.isfinite(cor.thr[drows]), cor.thr[drows], -np.inf)
    rep_cache = {}

    # ---------------------------------------------------------------- 2. variance
    f = folds["I2"]
    ctx_tr, ctx_te = f.contexts()
    lib = seed.copy()
    lib.fit(f.R_train, lib.states(ctx_tr), cor.df, f.drows)
    in_scope = np.array(lib.scope_cols).any(1)
    v_base = f.oos_var
    v_frozen = np.where(np.isfinite(lib.resid_var), lib.resid_var, v_base)
    v_cross = C.crossfit_variance(f, seed)
    corr = lib.correction(lib.states(ctx_te), cor.df, f.drows, novel=False)
    mean_base, mean_lib = f.base_mean, f.base_mean + corr
    Yt = cor.Ymean[np.ix_(f.drows, T)]
    ok = np.isfinite(Yt)

    def std_sq(mean, var):
        z2 = np.where(ok, (Yt - mean) ** 2 / var[:, None], np.nan)
        return z2

    sc = in_scope
    out["variance"] = {
        "drugs_in_program_scope": int(sc.sum()),
        "median_ratio_frozen_to_base_variance_in_scope": float(np.median(v_frozen[sc] / v_base[sc])),
        "median_ratio_crossfit_to_base_variance_in_scope": float(np.median(v_cross[sc] / v_base[sc])),
        "median_ratio_frozen_to_crossfit_in_scope": float(np.median(v_frozen[sc] / v_cross[sc])),
        "out_of_scope_variance_identical_to_base": bool(np.allclose(v_cross[~sc], v_base[~sc])),
        "target_standardised_squared_error_in_scope": {
            "frozen_variance": float(np.nanmean(std_sq(mean_lib, v_frozen)[sc])),
            "crossfit_variance": float(np.nanmean(std_sq(mean_lib, v_cross)[sc])),
            "base_variance": float(np.nanmean(std_sq(mean_lib, v_base)[sc])),
            "note": "mean of (Ymean - mean)^2 / variance over observed target pairs of in-scope drugs; 1.0 is calibrated; the endpoint adds rep_var/6 to all arms",
        },
    }
    print("variance done", round(time.time() - t0), flush=True)

    # ---------------------------------------------------------------- 3. decisions
    arms = {}
    frozen_undefined = ~np.isfinite(thr_frozen)
    contract_undefined = ~np.isfinite(cor.thr[drows])
    restored = frozen_undefined & ~contract_undefined
    thr_median_only = np.where(frozen_undefined, np.nan, thr_cor)       # contract median, restored drugs still excluded
    thr_restore_only = np.where(restored, thr_cor, thr_frozen)         # frozen thresholds, restored drugs added
    known_rate = cor.known[np.ix_(drows, train)].mean(1)

    def run(name, info, corrector, thr, mean_from, var_from, weight=None):
        fold = folds[info]
        _, _, score = C.decide(fold, corrector, thr, mean_from, var_from, cache=rep_cache)
        if weight is not None:
            score = score * weight[:, None]
        nom, h, u = hits_of(cor, score, fold, T)
        arms[name] = {"nom": nom, "hits": h, "unknown": u}
        return arms[name]

    for info in ("I1", "I2"):
        for tag, corrector in (("S", None), ("seed", seed)):
            vf = "frozen" if corrector else "base"
            run(f"{tag}|{info}|frozen", info, corrector, thr_frozen, "lib", vf)
            run(f"{tag}|{info}|median_only", info, corrector, thr_median_only, "lib", vf)
            run(f"{tag}|{info}|restore_only", info, corrector, thr_restore_only, "lib", vf)
            run(f"{tag}|{info}|threshold", info, corrector, thr_cor, "lib", vf)
            if corrector is not None:
                run(f"{tag}|{info}|variance", info, corrector, thr_frozen, "lib", "crossfit")
            run(f"{tag}|{info}|repaired", info, corrector, thr_cor, "lib", "crossfit" if corrector else "base")
            run(f"{tag}|{info}|repaired_availability", info, corrector, thr_cor, "lib",
                "crossfit" if corrector else "base", weight=known_rate)
    frozen_res = json.loads((HERE.parent / "program_revision_20261017" / "RESULTS.json").read_text(encoding="utf-8"))
    ref = frozen_res["B_table_hits_unknown_per_line"]
    repro = {}
    for tag, name in (("S", "strong"), ("seed", "seed_fixed")):
        for info in ("I1", "I2"):
            repro[f"{tag}|{info}"] = {"frozen_results_json": ref[f"{name}|{info}"]["all"][0],
                                      "this_pipeline_frozen_mode": float(arms[f"{tag}|{info}|frozen"]["hits"].mean())}
    out["reproduction_of_frozen_results"] = repro
    dec = {}
    for info in ("I1", "I2"):
        for tag in ("S", "seed"):
            ref_arm = arms[f"{tag}|{info}|frozen"]
            row = {"frozen_hits_per_line": float(ref_arm["hits"].mean()), "frozen_unknown_per_line": float(ref_arm["unknown"].mean())}
            steps = ["median_only", "restore_only", "threshold"] + (["variance"] if tag == "seed" else []) + ["repaired", "repaired_availability"]
            for step in steps:
                a = arms[f"{tag}|{info}|{step}"]
                st = paired(a["hits"] - ref_arm["hits"], groups)
                same = np.mean([len(set(a["nom"][:, j]) & set(ref_arm["nom"][:, j])) for j in range(len(T))])
                row[step] = {"hits_per_line": float(a["hits"].mean()), "unknown_per_line": float(a["unknown"].mean()),
                             "minus_frozen": st, "mean_shared_nominations_of_10": float(same)}
            dec[f"{tag}|{info}"] = row
    gains = {}
    for info in ("I1", "I2"):
        for step_s, step_e in (("frozen", "frozen"), ("median_only", "median_only"), ("restore_only", "restore_only"),
                               ("threshold", "threshold"), ("repaired", "repaired"),
                               ("repaired_availability", "repaired_availability")):
            gains[f"{info}|{step_e}"] = paired(arms[f"seed|{info}|{step_e}"]["hits"] - arms[f"S|{info}|{step_s}"]["hits"], groups)
    out["decisions"] = dec
    out["seed_minus_strong"] = gains
    nom_frozen = arms["S|I2|frozen"]["nom"]
    nom_cor = arms["S|I2|threshold"]["nom"]
    kn = cor.known[np.ix_(drows, T)]
    ht = cor.hit[np.ix_(drows, T)]
    cols = np.tile(np.arange(len(T)), (nom_cor.shape[0], 1))
    is_restored = np.isin(nom_cor, np.flatnonzero(restored))
    hn, kn_n = ht[nom_cor, cols], kn[nom_cor, cols]
    out["restored_drugs"] = {
        "frozen_undefined_drugs_nominated_by_frozen_S_I2": int(np.isin(nom_frozen, np.flatnonzero(frozen_undefined)).sum()),
        "restored_nominations_by_repaired_S_I2": int(is_restored.sum()),
        "nominations_total": int(nom_cor.size),
        "hit_rate_among_known_restored": float(hn[is_restored & kn_n].mean()),
        "hit_rate_among_known_other": float(hn[~is_restored & kn_n].mean()),
        "unknown_share_restored": float((~kn_n[is_restored]).mean()),
        "unknown_share_other": float((~kn_n[~is_restored]).mean()),
        "source_known_rate_restored_mean": float(known_rate[restored].mean()),
        "source_known_rate_other_mean": float(known_rate[~restored & ~contract_undefined].mean()),
        "one_replicate_share_of_known_pairs_restored": 1.0,
    }
    print("decisions done", round(time.time() - t0), flush=True)

    # ---------------------------------------------------------------- 4. event structure and reliability
    fold = folds["I2"]
    _, _, score = C.decide(fold, None, thr_cor, "lib", "base")
    knownT = cor.known[np.ix_(drows, T)]
    hitT = cor.hit[np.ix_(drows, T)]
    s = score[knownT]
    y = hitT[knownT].astype(float)
    order = np.argsort(s)
    bins = np.array_split(order, 10)
    rel = [{"decile": i + 1, "mean_score": float(s[b].mean()), "observed_hit_rate": float(y[b].mean()), "n": int(len(b))}
           for i, b in enumerate(bins)]
    from scipy.stats import rankdata
    ranks = rankdata(s)
    n1, n0 = y.sum(), len(y) - y.sum()
    auroc = float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    top = np.argsort(-score, axis=0)[:10]
    top_pred = np.take_along_axis(score, top, 0)
    top_known = np.take_along_axis(knownT, top, 0)
    top_hit = np.take_along_axis(hitT, top, 0)
    singleton_drug = (cor.endpoint.n_rep[np.ix_(drows, train)] == 1).sum(1) / np.maximum((cor.endpoint.n_rep[np.ix_(drows, train)] >= 1).sum(1), 1)
    heavy = singleton_drug >= 0.5
    by_type = {}
    for label, sel in (("drugs_with_majority_one_replicate_pairs", heavy), ("other_drugs", ~heavy)):
        km = knownT & sel[:, None]
        by_type[label] = {"drugs": int(sel.sum()), "mean_score_known_pairs": float(score[km].mean()),
                          "observed_hit_rate_known_pairs": float(hitT[km].mean()), "known_pairs": int(km.sum())}
    out["event"] = {
        "by_drug_type": by_type,
        "sign_condition": contract.sign_discordance(ep, ~src_line),
        "reliability_of_crossing_score_strong_I2_future_lines": rel,
        "auroc_known_pairs": auroc,
        "mean_score_vs_hit_rate_known_pairs": [float(s.mean()), float(y.mean())],
        "top10_nominations": {"mean_predicted": float(np.nanmean(np.where(top_known, top_pred, np.nan))),
                              "observed_hit_rate_among_known": float(top_hit[top_known].mean())},
        "reading": "the Gaussian crossing score ranks pairs; it is not shown to be a calibrated probability of the complete qualified-hit event",
    }
    out["seconds"] = round(time.time() - t0, 1)
    write_json(OUT, out)
    print(json.dumps({k: out[k] for k in ("mismatch", "seed_minus_strong")}, indent=1)[:6000])


if __name__ == "__main__":
    main()
