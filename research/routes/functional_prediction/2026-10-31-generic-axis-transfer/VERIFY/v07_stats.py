"""Check 1: recompute every primary and secondary number from the saved predictions, with observed and generic
profiles re-derived by the verifier (derived_nci.npz, derived_prism.npz). Writes check1_stats.json.
"""
import csv
import json
import sys

import numpy as np

VER = "D:/MAESTRO/research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"
sys.path.insert(0, VER)
import vlib  # noqa: E402

STUDY = VER[: -len("VERIFY/")]
SETS = {"nci60": dict(min_lines=40, sign=+1.0), "prism24q2": dict(min_lines=50, sign=-1.0)}
ARMS = vlib.ARMS
TOL = 1e-6
CI_TOL = 0.005


def load_csv(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
    return rows


def per_compound(pred, obs, gen, min_lines, sign, eval_rule="both", count_rule="round"):
    n = len(obs)
    r = np.array([vlib.sel_r(pred[i], obs[i], gen[i], min_lines) for i in range(n)])
    h = np.array([vlib.hit_precision(pred[i], obs[i], gen[i], sign, eval_rule=eval_rule, count_rule=count_rule)
                  for i in range(n)])
    return r, h


def main():
    reported = json.load(open(STUDY + "RUN/RESULTS.json", encoding="utf-8"))
    checks, notes = [], []

    def add(name, expected, recomputed, diff, tol, ok=None):
        if ok is None:
            ok = bool(diff is not None and diff <= tol)
        checks.append({"name": name, "expected": expected, "recomputed": recomputed,
                       "max_abs_diff": diff, "tolerance": tol, "pass": bool(ok)})

    recomputed_all = {}
    for s, cfg in SETS.items():
        P = np.load(STUDY + f"RUN/predictions_{s}.npz")
        D = np.load(VER + ("derived_nci.npz" if s == "nci60" else "derived_prism.npz"))
        keys = [str(k) for k in D["key"]]
        assert keys == [str(k) for k in P["key"]], "key order differs"
        assert [str(x) for x in D["line"]] == [str(x) for x in P["line"]], "line order differs"
        obs = D["observed"]
        gen = D["generic"] if D["generic"].ndim == 2 else np.broadcast_to(D["generic"], obs.shape)
        act = D["active"].astype(bool)

        # saved observed / generic / active vs re-derived
        nanpat = bool(np.array_equal(np.isfinite(P["observed"]), np.isfinite(obs)))
        d = float(np.nanmax(np.abs(P["observed"] - obs)))
        add(f"{s}: saved observed profiles equal re-derived (NaN pattern equal: {nanpat})", "saved observed",
            "re-derived observed", d, TOL, ok=(nanpat and d <= TOL))
        d = float(np.max(np.abs(P["generic"] - gen)))
        add(f"{s}: saved generic profiles equal re-derived", "saved generic", "re-derived generic", d, TOL)
        add(f"{s}: saved active flags equal re-derived", int(P["active"].sum()), int(act.sum()),
            float((P["active"] != act).sum()), 0, ok=bool(np.array_equal(P["active"], act)))

        # per-compound statistics
        rows = load_csv(STUDY + f"RUN/metrics_{s}.csv")
        assert [r["key"] for r in rows] == keys
        csv_active = np.array([r["active"] == "True" for r in rows])
        add(f"{s}: metrics CSV active column equals re-derived", int(csv_active.sum()), int(act.sum()),
            float((csv_active != act).sum()), 0, ok=bool(np.array_equal(csv_active, act)))
        R, H = {}, {}
        n_undefined = {}
        for a in ARMS:
            r, h = per_compound(P[f"pred_{a}"], obs, gen, cfg["min_lines"], cfg["sign"])
            n_undefined[a] = int(np.isnan(r).sum())
            R[a] = np.where(np.isfinite(r), r, 0.0)
            H[a] = h
            exp_r = np.array([float(x[f"r_{a}"]) for x in rows])
            exp_h = np.array([float(x[f"hit_{a}"]) for x in rows])
            dr = float(np.max(np.abs(exp_r - R[a])))
            dh = float(np.nanmax(np.abs(exp_h - H[a]))) if np.isfinite(H[a]).all() else float("inf")
            add(f"{s}: per-compound selective r, arm {a} (n={len(keys)}; undefined={n_undefined[a]})",
                "metrics CSV r_" + a, "recomputed", dr, TOL)
            add(f"{s}: per-compound selective hit precision, arm {a}", "metrics CSV hit_" + a, "recomputed", dh, TOL)

        # hit-precision rule variants (ambiguity: which lines are 'evaluated', how 10% is rounded)
        variants = {}
        alt_secondary = {}
        for er in ("both", "observed"):
            for cr in ("floor", "round", "round_half_up", "ceil"):
                worst = 0.0
                hv = {}
                for a in ARMS:
                    _, h = per_compound(P[f"pred_{a}"], obs, gen, cfg["min_lines"], cfg["sign"], er, cr)
                    hv[a] = h
                    exp_h = np.array([float(x[f"hit_{a}"]) for x in rows])
                    worst = max(worst, float(np.nanmax(np.abs(exp_h - h))))
                variants[f"eval={er},count={cr}"] = worst
                if er == "both" and cr in ("floor", "ceil"):
                    alt_secondary[f"count={cr}"] = {
                        "hit_precision_active": {a: float(hv[a][act].mean()) for a in ARMS},
                        "H1": vlib.paired_one_sided(hv["C1"][act], hv["B0"][act]),
                        "H3": vlib.paired_one_sided(hv["C1"][act], hv["B1"][act])}
        n_eval = np.array([np.sum(np.isfinite(vlib.resid(P["pred_B0"][i], gen[i])) & np.isfinite(vlib.resid(obs[i], gen[i])))
                           for i in range(len(keys))])
        n_eval_obs = np.array([np.sum(np.isfinite(vlib.resid(obs[i], gen[i]))) for i in range(len(keys))])

        rep = reported["sets"][s]
        rec = {"n_queries": len(keys), "n_active": int(act.sum()), "n_lines": obs.shape[1]}
        for k in ("n_queries", "n_active", "n_lines"):
            add(f"{s}: {k}", rep[k], rec[k], float(abs(rep[k] - rec[k])), 0)

        def means(mask):
            return {a: float(R[a][mask].mean()) for a in ARMS}

        groups = {"primary_mean_active": means(act), "primary_mean_all": means(np.ones_like(act)),
                  "primary_mean_inactive": means(~act)}
        hp = {a: float(H[a][act].mean()) for a in ARMS}
        hp["Z"] = 0.1
        groups["hit_precision_active"] = hp
        for gname, vals in groups.items():
            dd = max(abs(rep[gname][a] - vals[a]) for a in vals)
            add(f"{s}: {gname}", rep[gname], vals, float(dd), TOL)
        add(f"{s}: zero_arm_primary", rep["zero_arm_primary"], 0.0, abs(rep["zero_arm_primary"]), TOL)

        # contrasts on actives
        def contrast(x, y, boot_seed):
            res = vlib.paired_one_sided(x[act], y[act])
            res["ci95"] = vlib.boot_ci(x[act] - y[act], 10000, boot_seed)
            res["ci95_study_seed_default_rng"] = vlib.boot_ci(x[act] - y[act], 10000, 20261031)
            return res

        fam = {"H1": contrast(R["C1"], R["B0"], 101), "H3": contrast(R["C1"], R["B1"], 103)}
        rej = vlib.holm([fam["H1"]["p_one_sided"], fam["H3"]["p_one_sided"]])
        fam["H1"]["holm_reject"], fam["H3"]["holm_reject"] = rej
        ctx = {"C1_vs_B2": contrast(R["C1"], R["B2"], 105), "B1_vs_B0": contrast(R["B1"], R["B0"], 107)}
        sec = {"H1": contrast(H["C1"], H["B0"], 109), "H3": contrast(H["C1"], H["B1"], 111)}
        # extra context reported in the protocol but not in RESULTS.json: every arm vs Z
        vsZ = {a: vlib.paired_one_sided(R[a][act], np.zeros(act.sum())) for a in ARMS if a != "L"}
        for block_name, block in (("family", fam), ("context", ctx), ("secondary_hit_precision", sec)):
            for cname, res in block.items():
                e = rep[block_name][cname]
                dd = max(abs(e["mean_difference"] - res["mean_difference"]), abs(e["t"] - res["t"]),
                         abs(e["p_one_sided"] - res["p_one_sided"]))
                add(f"{s}: {block_name} {cname} mean difference, t, one-sided p (n={res['n']})",
                    {k: e[k] for k in ("mean_difference", "t", "p_one_sided", "n")},
                    {k: res[k] for k in ("mean_difference", "t", "p_one_sided", "n")}, float(dd), TOL,
                    ok=(dd <= TOL and e["n"] == res["n"]))
                dci = max(abs(e["ci95"][0] - res["ci95"][0]), abs(e["ci95"][1] - res["ci95"][1]))
                add(f"{s}: {block_name} {cname} bootstrap 95% CI (verifier resampling, 10,000)", e["ci95"], res["ci95"],
                    float(dci), CI_TOL)
                if block_name == "family":
                    add(f"{s}: family {cname} Holm decision", e["holm_reject"], res["holm_reject"], None, 0,
                        ok=(e["holm_reject"] == res["holm_reject"]))
        # leakage control
        m, t, p = vlib.one_sample_two_sided(R["L"][act])
        valid = not (abs(m) > 0.03 and p < 0.01)
        e = rep["leakage_control"]
        add(f"{s}: leakage control mean r of L on actives and two-sided p", {"mean": e["mean"], "p_two_sided": e["p_two_sided"]},
            {"mean": m, "p_two_sided": p}, float(max(abs(e["mean"] - m), abs(e["p_two_sided"] - p))), TOL)
        add(f"{s}: leakage control validity", e["valid"], valid, None, 0, ok=(e["valid"] == valid))
        if s == "prism24q2":
            add(f"{s}: parsed_treatments", rep["parsed_treatments"], int(np.load(VER + "derived_prism.npz")["observed"].shape[0]),
                None, 0, ok=(rep["parsed_treatments"] == 101))
            add(f"{s}: dropped_in_pool", rep["dropped_in_pool"], [], None, 0, ok=(rep["dropped_in_pool"] == []))
        # contrasts the protocol lists but RESULTS.json does not report (computed here for the record)
        unreported = {"primary_arm_vs_Z": {}, "secondary_context": {}, "secondary_arm_vs_Z": {},
                      "secondary_mean_all": {a: float(H[a].mean()) for a in ARMS},
                      "secondary_mean_inactive": {a: float(H[a][~act].mean()) for a in ARMS}}
        for a in ARMS:
            z0 = np.zeros(int(act.sum()))
            rr = vlib.paired_one_sided(R[a][act], z0)
            rr["ci95"] = vlib.boot_ci(R[a][act], 10000, 201)
            unreported["primary_arm_vs_Z"][a] = rr
            hh = vlib.paired_one_sided(H[a][act], z0 + 0.1)
            hh["ci95"] = vlib.boot_ci(H[a][act] - 0.1, 10000, 203)
            unreported["secondary_arm_vs_Z"][a] = hh
        for cname, (x, y) in {"C1_vs_B2": ("C1", "B2"), "B1_vs_B0": ("B1", "B0")}.items():
            rr = vlib.paired_one_sided(H[x][act], H[y][act])
            rr["ci95"] = vlib.boot_ci(H[x][act] - H[y][act], 10000, 205)
            unreported["secondary_context"][cname] = rr
        np.savez(VER + f"percompound_{s}.npz", key=np.array(keys), active=act,
                 **{f"r_{a}": R[a] for a in ARMS}, **{f"hit_{a}": H[a] for a in ARMS})
        recomputed_all[s] = {"unreported_contrasts": unreported, "groups": groups, "family": fam, "context": ctx,
                             "secondary": sec, "leakage":
                             {"mean": m, "t": t, "p_two_sided": p, "valid": valid}, "vs_zero_arm": vsZ,
                             "n_undefined_r": n_undefined, "hit_rule_variants_max_abs_diff": variants, "secondary_under_alternative_hit_counts": alt_secondary,
                             "n_eval_lines_both_B0": [int(n_eval.min()), int(n_eval.max())],
                             "n_eval_lines_observed": [int(n_eval_obs.min()), int(n_eval_obs.max())]}

    # verdicts and promotion
    nf, pf = recomputed_all["nci60"]["family"], recomputed_all["prism24q2"]["family"]
    leak_ok = recomputed_all["nci60"]["leakage"]["valid"] and recomputed_all["prism24q2"]["leakage"]["valid"]
    verdict = {}
    for h in ("H1", "H3"):
        if not leak_ok:
            verdict[h] = "INVALID"
        elif nf[h]["holm_reject"] and pf[h]["holm_reject"]:
            verdict[h] = "REPLICATED"
        elif nf[h]["holm_reject"] and pf[h]["mean_difference"] > 0:
            verdict[h] = "CONFIRMED"
        else:
            verdict[h] = "NOT_CONFIRMED"
    promote = verdict["H1"] in ("CONFIRMED", "REPLICATED") and pf["H3"]["mean_difference"] >= 0
    add("verdict H1", reported["verdict"]["H1"], verdict["H1"], None, 0, ok=(reported["verdict"]["H1"] == verdict["H1"]))
    add("verdict H3", reported["verdict"]["H3"], verdict["H3"], None, 0, ok=(reported["verdict"]["H3"] == verdict["H3"]))
    add("promote_C1 (before verification)", reported["promote_C1"], promote, None, 0, ok=(reported["promote_C1"] == promote))
    for k in ("D", "K", "seed"):
        add(f"run constant {k}", reported[k], {"D": 5, "K": 20, "seed": 20261031}[k], None, 0,
            ok=(reported[k] == {"D": 5, "K": 20, "seed": 20261031}[k]))

    out = {"checks": checks, "recomputed": recomputed_all, "verdict": verdict, "promote_C1": promote}
    json.dump(out, open(VER + "check1_stats.json", "w", encoding="utf-8", newline="\n"), indent=1, default=float)
    npass = sum(c["pass"] for c in checks)
    print(f"{npass}/{len(checks)} checks pass")
    for c in checks:
        if not c["pass"]:
            print("FAIL:", c["name"], c["max_abs_diff"])
    for s in SETS:
        print(s, "undefined r:", recomputed_all[s]["n_undefined_r"])
        print(s, "hit-rule variants (max abs diff vs CSV):", recomputed_all[s]["hit_rule_variants_max_abs_diff"])
        print(s, "evaluated lines (both finite, B0):", recomputed_all[s]["n_eval_lines_both_B0"],
              "observed finite:", recomputed_all[s]["n_eval_lines_observed"])
        for blk in ("family", "context", "secondary"):
            for c, r in recomputed_all[s][blk].items():
                print(f"  {s} {blk} {c}: diff={r['mean_difference']:.6f} t={r['t']:.4f} p={r['p_one_sided']:.4g} "
                      f"ci={np.round(r['ci95'], 4).tolist()} ci_study_seed={np.round(r['ci95_study_seed_default_rng'], 4).tolist()}")
        print(f"  {s} leakage: {recomputed_all[s]['leakage']}")
        print(f"  {s} vs zero arm:", {a: (round(v['mean_difference'], 4), float('%.3g' % v['p_one_sided']))
                                       for a, v in recomputed_all[s]['vs_zero_arm'].items()})
    print("verdict:", verdict, "promote:", promote)


if __name__ == "__main__":
    main()
