"""Sealed confirmation of block M (run once, after FREEZE.json). Reads PROTOCOL_CONFIG.json only.

Every fit (basis, prototypes, noise, calibration, knowledge slopes, episode calibration) uses the
open tier's reference drugs, exactly as in development. Confirmation drugs are only scored. Arms
are listed in PROTOCOL_CONFIG.json; each arm is a config override, a hypothesis set and a list of
design policies. Outputs (in ``out_dir``): RESULTS.json (summaries, decisions) and ROWS.json
(per-episode records without drug-level expression).

``poison_seed`` replaces every confirmation expression value by seeded noise with the same
missingness (used by verify.py: design-only quantities must not change, outcomes must).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

import dev_programs as DP
import episodes as EP
import identifiability as ID
import intervals as IV
import revision as RV
import study as S

HERE = Path(__file__).resolve().parent
BINS = ((0.0, 0.5), (0.5, 0.75), (0.75, 1.01))


def protocol() -> dict:
    return json.loads((HERE / "PROTOCOL_CONFIG.json").read_text(encoding="utf-8"))


def project(b: S.Built, X: np.ndarray) -> np.ndarray:
    return np.where(np.isnan(X[..., :1]), np.nan, b.basis.project(np.nan_to_num(X)))


def step_at(r: dict, B: int) -> dict:
    return r["steps"][min(B, len(r["steps"])) - 1]


def coverage_block(rows: list[dict], B: int) -> dict:
    st = [step_at(r, B) for r in rows if r["steps"]]
    k = int(sum(s["covered"] for s in st))
    lo, hi = IV.wilson(k, len(st))
    return {"n": len(st), "coverage": k / len(st) if st else float("nan"), "wilson95": [lo, hi],
            "mean_set": float(np.mean([s["set_size"] for s in st])) if st else float("nan"),
            "median_set": float(np.median([s["set_size"] for s in st])) if st else float("nan"),
            "cred_coverage": float(np.mean([s["cred_covered"] for s in st])) if st else float("nan"),
            "cred_mean_set": float(np.mean([s["cred_size"] for s in st])) if st else float("nan")}


def strata_table(rows: list[dict], B: int, referenced: set, act: dict) -> dict:
    out = {"all": coverage_block(rows, B)}
    out["referenced"] = coverage_block([r for r in rows if r["moa"] in referenced], B)
    out["knowledge_only"] = coverage_block([r for r in rows if r["moa"] not in referenced], B)
    for lo, hi in BINS:
        rs = [r for r in rows if lo <= act[r["drug"]] < hi]
        if rs:
            out[f"activity_{lo:.2f}_{min(hi, 1):.2f}"] = coverage_block(rs, B)
    return out


def paired_sets(rows_a: list[dict], rows_b: list[dict], B: int, clusters: dict) -> dict:
    a = {r["drug"]: step_at(r, B)["set_size"] for r in rows_a if r["steps"]}
    b = {r["drug"]: step_at(r, B)["set_size"] for r in rows_b if r["steps"]}
    keys = sorted(set(a) & set(b))
    return IV.paired_difference(np.array([a[k] for k in keys]), np.array([b[k] for k in keys]),
                                np.array([clusters[k] for k in keys]))


def dry_tier(open_: dict, n: int) -> dict:
    """Stand-in for the sealed tier before the freeze: the first ``n`` development drugs."""
    idx = np.where(open_["role"] == "development")[0][:n]
    d = {k: (v[idx] if isinstance(v, np.ndarray) and v.ndim and len(v) == len(open_["drug"]) else v) for k, v in open_.items()}
    return d


def ranking_section(open_: dict, sealed: dict, base: dict, n_rand: int = 4) -> dict:
    """World model vs baselines as rankers of the true class (observed classes only, 212).

    Scorers: world model profile NLL (registered config), the same with class labels shuffled,
    nearest reference member (option-averaged gene-space cosine; kNN-1) and class-mean cosine
    (gene space). Profiles: all available options, and four drawn at random (seed per drug).
    Paired comparisons on the true class's rank (world model minus baseline; negative = better)
    with a class-cluster bootstrap.
    """
    import dev_ceiling as DC
    import falsify as F
    ref = open_["role"] == "reference"
    Xr, moa_r = open_["x"][ref], open_["moa"][ref]
    builds = {"world_model": S.build(open_, S.Config(**base)), "shuffled": S.build(open_, S.Config(**{**base, "permute_classes": True}))}
    b = builds["world_model"]
    lib = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    names = [b.models[i].name for i in lib]
    pos = {n: i for i, n in enumerate(names)}
    Z = {k: project(bb, sealed["x"]) for k, bb in builds.items()}
    fzs = {k: S.falsifier(bb) for k, bb in builds.items()}
    Xru = DC.unit(np.nan_to_num(Xr))
    members = {c: np.where(moa_r == c)[0] for c in names}
    cmean = {c: np.nanmean(Xr[members[c]], axis=0) for c in names}
    q = [i for i in range(len(sealed["drug"])) if sealed["moa"][i] in pos]
    ranks = {k: {"full": [], "rand4": []} for k in ("world_model", "shuffled", "nearest_member", "class_mean_cosine")}
    clusters = []
    for qi in q:
        avail = S.available(sealed, qi)
        rng = np.random.default_rng(20261010 + qi)
        sub = sorted(rng.choice(avail, size=min(n_rand, len(avail)), replace=False).tolist())
        ti = pos[sealed["moa"][qi]]
        xq = DC.unit(np.nan_to_num(sealed["x"][qi]))
        for key, opts in (("full", avail), ("rand4", sub)):
            for name in ("world_model", "shuffled"):
                fz = fzs[name]
                Q, bb_, A = fz.stats(Z[name][qi], opts, lib)
                nll, _ = F.score_from_stats(Q, bb_, A, fz.noise.tau2, len(opts))
                ranks[name][key].append(DC.rank_of(nll, ti, False))
            nn, cm = [], []
            for c in names:
                sims = []
                for j in members[c]:
                    sh = [o for o in opts if not np.isnan(Xr[j, o, 0])]
                    if sh:
                        sims.append(float(np.mean(np.sum(xq[sh] * Xru[j, sh], axis=1))))
                nn.append(max(sims) if sims else np.nan)
                sh = [o for o in opts if not np.isnan(cmean[c][o, 0])]
                cm.append(float(np.mean([DC.unit(cmean[c][o]) @ xq[o] for o in sh])) if sh else np.nan)
            ranks["nearest_member"][key].append(DC.rank_of(np.array(nn), ti, True))
            ranks["class_mean_cosine"][key].append(DC.rank_of(np.array(cm), ti, True))
        clusters.append(str(sealed["moa"][qi]))
    out = {"n": len(q), "n_classes": len(names)}
    for name, d in ranks.items():
        for key, r in d.items():
            r = np.array(r)
            out[f"{name}/{key}"] = {"median_rank": float(np.median(r)), "top5": float(np.mean(r <= 5)), "top20": float(np.mean(r <= 20)),
                                    "p90_rank": float(np.percentile(r, 90))}
    cl = np.array(clusters)
    for key in ("full", "rand4"):
        wm = np.array(ranks["world_model"][key])
        for other in ("shuffled", "nearest_member", "class_mean_cosine"):
            out[f"world_model_minus_{other}/{key}"] = IV.paired_difference(wm, np.array(ranks[other][key]), cl)
    return out


def main(out_dir: Path | None = None, poison_seed: int | None = None, with_llm: bool = True, arms_filter: list[str] | None = None,
         sections: tuple[str, ...] = ("ranking", "identifiability", "revision"), dry_run: int = 0,
         llm_n: tuple[int, int] | None = None) -> dict:
    t0 = time.time()
    P = protocol()
    out_dir = Path(out_dir) if out_dir else HERE
    out_dir.mkdir(parents=True, exist_ok=True)
    open_ = S.load_tier("open")
    sealed = dry_tier(open_, dry_run) if dry_run else S.load_tier("sealed")
    if poison_seed is not None:
        rng = np.random.default_rng(poison_seed)
        sealed["x"] = np.where(np.isnan(sealed["x"]), np.nan, rng.normal(0, 1, sealed["x"].shape).astype(np.float32))
    B = int(P["budget"])
    q = np.arange(len(sealed["drug"]))
    act_arr = DP.activity(sealed["x"], open_["x"][open_["role"] == "reference"])
    act = {str(d): float(a) for d, a in zip(sealed["drug"], act_arr)}
    clusters = {str(d): str(m) for d, m in zip(sealed["drug"], sealed["moa"])}
    results = {"protocol_sha256": __import__("hashlib").sha256((HERE / "PROTOCOL_CONFIG.json").read_bytes()).hexdigest(),
               "budget": B, "n_queries": int(len(q)), "poison_seed": poison_seed, "dry_run": dry_run, "arms": {}}
    all_rows = {}
    base = P["config"]
    referenced = None
    for arm in P["arms"]:
        if arms_filter is not None and arm["name"] not in arms_filter:
            continue
        cfg = S.Config(**{**base, **arm.get("override", {})})
        b = S.build(open_, cfg)
        if referenced is None:
            referenced = {m.name for m in b.models if m.kind != "knowledge"}
        Zs = project(b, sealed["x"])
        lib = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
        hf = (lambda qi, true: lib) if arm.get("hyp") == "library" else None
        rows = EP.run_queries(b, sealed, q, arm["policies"], B, hyp_filter=hf, z_override=Zs)
        for r in rows:
            r["arm"] = arm["name"]
        all_rows[arm["name"]] = rows
        results["arms"][arm["name"]] = {"config": asdict(cfg), "hyp": arm.get("hyp", "all"),
                                        "by_policy": {pol: {f"B{k}": strata_table([r for r in rows if r["policy"] == pol], k, referenced, act)
                                                            for k in range(1, B + 1)} for pol in arm["policies"]}}
        (out_dir / "ROWS.json").write_text(json.dumps(all_rows, indent=0), encoding="utf-8")
        print(arm["name"], {pol: round(v[f"B{B}"]["all"]["coverage"], 3) for pol, v in results["arms"][arm["name"]]["by_policy"].items()},
              {pol: round(v[f"B{B}"]["all"]["mean_set"], 1) for pol, v in results["arms"][arm["name"]]["by_policy"].items()}, flush=True)

    # paired set-size contrasts registered in PROTOCOL_CONFIG.json: [arm_a, policy_a, arm_b, policy_b, stratum]
    results["contrasts"] = {}
    for c in P["contrasts"]:
        if c["a"][0] not in all_rows or c["b"][0] not in all_rows:
            continue
        ra = [r for r in all_rows[c["a"][0]] if r["policy"] == c["a"][1]]
        rb = [r for r in all_rows[c["b"][0]] if r["policy"] == c["b"][1]]
        if c.get("stratum") == "knowledge_only":
            ra = [r for r in ra if r["moa"] not in referenced]
            rb = [r for r in rb if r["moa"] not in referenced]
        elif c.get("stratum") == "referenced":
            ra = [r for r in ra if r["moa"] in referenced]
            rb = [r for r in rb if r["moa"] in referenced]
        results["contrasts"][c["name"]] = paired_sets(ra, rb, B, clusters)
        cov = lambda rs: float(np.mean([step_at(r, B)["covered"] for r in rs if r["steps"]]))
        results["contrasts"][c["name"]].update({"coverage_a": cov(ra), "coverage_b": cov(rb)})

    if "ranking" in sections:
        results["ranking"] = ranking_section(open_, sealed, base)
        (out_dir / "RESULTS.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
        print("ranking", {k: v["median_rank"] for k, v in results["ranking"].items() if isinstance(v, dict) and "median_rank" in v}, flush=True)
    if "identifiability" not in sections and "revision" not in sections:
        results["seconds"] = round(time.time() - t0, 1)
        (out_dir / "RESULTS.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
        return results
    # identifiability (H5): predicted from reference drugs, realised on confirmation drugs
    main_arm = P["arms"][0]
    cfg = S.Config(**{**base, **main_arm.get("override", {}), "calib": "set"})
    b = S.build(open_, cfg)
    fz = S.falsifier(b)
    Zs = project(b, sealed["x"])
    classes = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    import dev_identifiability as DI
    R_pred = ID.predicted_cross_rejection(fz, classes, n_sim=P["identifiability"]["n_sim"], seed=cfg.seed, lam_pool=b.lam_pool)
    pred, base_rate, y, ai, bi, oi = DI.events(fz, Zs, sealed["moa"], q, classes, R_pred)
    results["identifiability"] = {"n_events": int(len(y)), "auc_pair": DI.auc(pred, y), "auc_pair_blind": DI.auc(base_rate, y),
                                  "realised_rate": float(y.mean()), "predicted_rate": float(pred.mean())}
    # paired bootstrap over query drugs for the AUC difference
    pos = {n: i for i, n in enumerate(fz.names[classes])}
    rng = np.random.default_rng(20261010)
    ev_q = []
    for qi in q:
        a = pos.get(sealed["moa"][qi])
        if a is None:
            continue
        n_ev = 0
        for o in range(Zs.shape[1]):
            if np.isnan(Zs[qi, o, 0]) or np.isnan(R_pred[a, 0, o]):
                continue
            m = (np.arange(len(classes)) != a) & ~np.isnan(R_pred[a, :, o])
            n_ev += int(m.sum())
        ev_q.append(np.full(n_ev, qi))
    ev_q = np.concatenate(ev_q) if ev_q else np.array([])
    uq = np.unique(ev_q)
    idx = {u: np.where(ev_q == u)[0] for u in uq}
    diffs = []
    for _ in range(int(P["identifiability"]["n_boot"])):
        pick = np.concatenate([idx[u] for u in rng.choice(uq, size=len(uq), replace=True)])
        diffs.append(DI.auc(pred[pick], y[pick]) - DI.auc(base_rate[pick], y[pick]))
    results["identifiability"]["auc_difference_ci95"] = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]

    # adequacy and revision (H6): library-only H0, falsify design, set calibration
    library = classes
    outside = np.array([i for i, m in enumerate(b.models) if m.kind == "knowledge"])
    bp = S.build(open_, S.Config(**{**asdict(cfg), "permute_emh": True}))
    fzp = S.falsifier(bp)
    Zp = project(bp, sealed["x"])
    lib_names = set(fz.names[library])
    rev_rows = []
    arms_llm = None
    if with_llm and P["revision"].get("agent"):
        import agent_arms as AA
        import dev_agent as DA
        arms_llm = AA.AgentArms(sorted(fz.names), sealed["genes"], sealed["options"], DA.noise_hint(open_))
    for qi in q:
        true = str(sealed["moa"][qi])
        avail = S.available(sealed, qi)
        ep = RV.library_episode(fz, Zs[qi], avail, library, B, seed=int(cfg.seed + qi))
        row = {"drug": str(sealed["drug"][qi]), "moa": true, "in_library": true in lib_names, "status": ep.status}
        if not row["in_library"]:
            prop, p = RV.compiled_ranking(fz, Zs[qi], ep.observed, outside)
            ti = int(np.where(fz.names[outside] == true)[0][0])
            row["compiled_success"] = bool(true in prop and p[ti] > fz.alpha)
            propp, pp = RV.compiled_ranking(fzp, Zp[qi], ep.observed, outside)
            row["compiled_permuted_success"] = bool(true in propp and pp[ti] > fzp.alpha)
            row["random_success_expected"] = float(5 / len(outside) * (p[ti] > fz.alpha))
            row["true_survives_outside"] = bool(p[ti] > fz.alpha)
            if arms_llm is not None and ep.status == "HYPOTHESIS_SET_EXHAUSTED":
                zg = {o: sealed["x"][qi, o] for o in ep.observed}
                prop_a, meta = arms_llm.revise(f"sealed:{qi}", zg, ep.observed, sorted(lib_names))
                row["agent_success"] = bool(true in prop_a and p[ti] > fz.alpha)
                row["agent_status"] = meta["status"]
        rev_rows.append(row)
    inn = [r for r in rev_rows if r["in_library"]]
    out = [r for r in rev_rows if not r["in_library"]]
    ex = [r for r in out if r["status"] == "HYPOTHESIS_SET_EXHAUSTED"]
    k_in = sum(r["status"] == "HYPOTHESIS_SET_EXHAUSTED" for r in inn)
    k_out = len(ex)
    rev = {"exhausted_in_library": [k_in, len(inn), IV.wilson(k_in, len(inn))],
           "exhausted_outside": [k_out, len(out), IV.wilson(k_out, len(out))]}
    for name, rs in (("all_outside", out), ("exhausted_outside", ex)):
        if rs:
            rev[name] = {"n": len(rs), "compiled": float(np.mean([r["compiled_success"] for r in rs])),
                         "compiled_permuted": float(np.mean([r["compiled_permuted_success"] for r in rs])),
                         "random_expected": float(np.mean([r["random_success_expected"] for r in rs])),
                         "true_survives_outside": float(np.mean([r["true_survives_outside"] for r in rs]))}
            ag = [r for r in rs if "agent_success" in r]
            if ag:
                rev[name]["agent"] = float(np.mean([r["agent_success"] for r in ag]))
                rev[name]["agent_n"] = len(ag)
    results["revision"] = rev

    # LLM arms on the registered subset of confirmation drugs (C1 agent alone, C3 interface, agent design)
    if with_llm and P.get("llm_arms"):
        import agent_arms as AA
        import dev_agent as DA
        L = P["llm_arms"]
        arms = AA.AgentArms(sorted(fz.names), sealed["genes"], sealed["options"], DA.noise_hint(open_))
        n_ref, n_know = llm_n if llm_n is not None else (L["n_ref"], L["n_know"])
        sub = DA.subset({**sealed, "role": np.full(len(q), "development")}, referenced, n_ref, n_know)
        llm_rows = []
        import threading
        from concurrent.futures import ThreadPoolExecutor
        lock = threading.Lock()

        def one(job):
            qi, mode = job
            avail = S.available(sealed, qi)
            zg = {o: sealed["x"][qi, o] for o in avail}
            rec = arms.episode(f"sealed:{qi}", zg, avail, B, mode, fz=fz, z_proj=Zs[qi])
            with lock:
                llm_rows.append({"drug": str(sealed["drug"][qi]), "moa": str(sealed["moa"][qi]), "mode": mode,
                                 "stratum": "referenced" if sealed["moa"][qi] in referenced else "knowledge_only", **rec})

        with ThreadPoolExecutor(int(L.get("workers", 8))) as pool:
            list(pool.map(one, [(qi, mode) for qi in sub for mode in L["modes"]]))
        llm_rows.sort(key=lambda r: (r["drug"], r["mode"]))
        summ = {}
        for mode in L["modes"]:
            for key in ("agent_set", "falsifier_set"):
                rs = [r for r in llm_rows if r["mode"] == mode]
                for k in range(1, B + 1):
                    sets = [r["steps"][min(k, len(r["steps"])) - 1].get(key) for r in rs if r["steps"]]
                    cov = [r["moa"] in (s if s is not None else fz.names) for r, s in zip(rs, sets)]
                    size = [len(s) if s is not None else len(fz.names) for s in sets]
                    kk = int(sum(cov))
                    summ[f"{mode}/{key}/B{k}"] = {"n": len(sets), "coverage": kk / max(len(sets), 1), "wilson95": IV.wilson(kk, len(sets)),
                                                   "mean_set": float(np.mean(size)) if size else float("nan"),
                                                   "stated_none": int(sum(s is None for s in sets))}
        results["llm_arms"] = {"n_queries": int(len(sub)), "drugs": [str(sealed["drug"][i]) for i in sub], "summary": summ,
                               "ledger_total_usd": round(arms.ledger.total_usd, 4)}
        (out_dir / "LLM_ROWS.json").write_text(json.dumps(llm_rows, indent=0), encoding="utf-8")

    results["decisions"] = decide(results, P)
    results["seconds"] = round(time.time() - t0, 1)
    (out_dir / "RESULTS.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    (out_dir / "REVISION_ROWS.json").write_text(json.dumps(rev_rows, indent=0), encoding="utf-8")
    return results


def decide(R: dict, P: dict) -> dict:
    """Apply the decision rules registered in PROTOCOL_CONFIG.json["rules"] (see PROTOCOL.md)."""
    rules = P["rules"]
    B = f"B{R['budget']}"
    out = {}
    if P["arms"][0]["name"] not in R["arms"]:
        main = None
    else:
        main = R["arms"][P["arms"][0]["name"]]["by_policy"][rules["primary_policy"]][B]
    if main is None:
        return _decide_rest(R, P, out)
    lo = main["all"]["wilson95"][0]
    tiers = {k: v for k, v in main.items() if k.startswith("activity_") and v["n"] >= rules["min_tier_n"]}
    out["H1_validity"] = {"coverage": main["all"]["coverage"], "wilson_lower": lo,
                          "tier_coverage": {k: v["coverage"] for k, v in tiers.items()},
                          "credible_coverage": main["all"]["cred_coverage"],
                          "pass": bool(lo >= rules["coverage_lower"] and all(v["coverage"] >= rules["tier_coverage_min"] for v in tiers.values())),
                          "uncalibrated_fails": bool(main["all"]["cred_coverage"] < rules["coverage_lower"])}
    return _decide_rest(R, P, out)


def _decide_rest(R: dict, P: dict, out: dict) -> dict:
    rules = P["rules"]
    for name, spec in rules["contrasts"].items():
        if spec["contrast"] not in R["contrasts"]:
            continue
        c = R["contrasts"][spec["contrast"]]
        # mean_difference = a - b; "a_smaller" means the CI lies entirely below zero
        hit = c["ci95"][1] < 0 if spec["direction"] == "a_smaller" else c["ci95"][0] > 0
        valid = c["coverage_a"] >= rules["comparator_coverage_min"] and c["coverage_b"] >= rules["comparator_coverage_min"]
        out[name] = {"mean_difference": c["mean_difference"], "ci95": c["ci95"], "coverage_a": c["coverage_a"],
                     "coverage_b": c["coverage_b"], "pass": bool(hit and valid),
                     "verdict": ("PASS" if hit and valid else "INVALID_COMPARISON" if hit and not valid else "NOT_SUPPORTED")}
    if "ranking" in R:
        c = R["ranking"]["world_model_minus_nearest_member/rand4"]
        out["H8_ranking_vs_knn"] = {"mean_rank_difference": c["mean_difference"], "ci95": c["ci95"], "pass": bool(c["ci95"][1] < 0)}
    if "identifiability" not in R:
        return out
    idf = R["identifiability"]
    out["H5_identifiability"] = {"auc_pair": idf["auc_pair"], "auc_pair_blind": idf["auc_pair_blind"],
                                 "ci95": idf["auc_difference_ci95"], "pass": bool(idf["auc_difference_ci95"][0] > 0)}
    rv = R["revision"]
    ex_in, ex_out = rv["exhausted_in_library"], rv["exhausted_outside"]
    out["H6_adequacy"] = {"exhausted_in": ex_in[0] / max(ex_in[1], 1), "exhausted_out": ex_out[0] / max(ex_out[1], 1),
                          "pass": bool(ex_out[2][0] > ex_in[2][1])}  # Wilson intervals do not overlap, outside higher
    if "all_outside" in rv:
        a = rv["all_outside"]
        out["H6_revision_compiled"] = {"compiled": a["compiled"], "random_expected": a["random_expected"],
                                       "compiled_permuted": a["compiled_permuted"], "n": a["n"]}
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0, help="score the first N development drugs instead of the sealed tier")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    r = main(out_dir=Path(a.out) if a.out else None, with_llm=not a.no_llm, dry_run=a.dry_run)
    print(json.dumps(r.get("decisions", {}), indent=1))
