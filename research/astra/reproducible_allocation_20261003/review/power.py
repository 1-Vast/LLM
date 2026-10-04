"""Review A1: variance and sample size for a future frozen 2x2 (EXPLORATORY inputs).

File summary
- Path: research/astra/reproducible_allocation_20261003/review/power.py
- Purpose: size the confirmation of a future model x scheduler 2x2 from the observed line-level
  variance of earlier (exposed, already-written) Jaaks 2022 results, instead of an arbitrary
  60-line gate. Plan: review/plan.json (A1), written before this script read any per-line value.
- Core points:
  - Reads only derived result files of ../feedback_validation_20261003 (lines.jsonl, verdict.json,
    followup_verification.json). The raw release is not read; no vault/ticket opening is needed.
  - Unit = cell line (SV and VS replicates averaged where both exist); paired differences between
    arms; ratio-of-sums gain G as in the earlier verdict.
  - Normal-approximation sample sizes for superiority, threshold (lower bound > tau) and futility
    (upper bound < tau when the true gain is 0), checked by resampling-based power.
  - Pairs recur across lines: the design effect is taken from the earlier two-way bootstrap (S13).
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.review.power` from D:\\MAESTRO
  with PYTHONPATH="src;."; writes review/power.json (refuses to overwrite).
- Depends on: numpy, scipy.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = ROOT / "research/astra/feedback_validation_20261003/results"
OUT = HERE / "power.json"
SEED = 20261004
ARMS = ["history_mean", "history_rate", "ridge_static", "gbm_static", "feedback", "history_feedback",
        "rate_feedback", "offset_only", "random", "oracle_validated", "oracle_screen"]
BASE = "history_mean"


def load_lines(budget: str = "primary") -> dict:
    per = defaultdict(lambda: defaultdict(dict))
    with open(PRIOR / "jaaks_primary/lines.jsonl", encoding="utf-8") as handle:
        for raw in handle:
            rec = json.loads(raw)
            arms = rec["budgets"][budget]["arms"]
            for arm in ARMS:
                runs = arms[arm] if isinstance(arms[arm], list) else [arms[arm]]  # seeded arms: mean over seeds
                per[(rec["stratum"], rec["line"])][arm][rec["replicate"]] = tuple(
                    float(np.mean([r[f] for r in runs])) for f in ("validated", "screen_hits", "wells"))
            per[(rec["stratum"], rec["line"])]["_available"][rec["replicate"]] = float(rec["line_validated"])
            per[(rec["stratum"], rec["line"])]["_menu"][rec["replicate"]] = float(rec["candidates"])
    return per


def n_required(sd: float, delta: float, alpha: float = 0.025, power: float = 0.8) -> float:
    if delta <= 0:
        return math.inf
    return ((norm.ppf(1 - alpha) + norm.ppf(power)) * sd / delta) ** 2


def strat_boot_ratio(x: np.ndarray, y: np.ndarray, strata: np.ndarray, rng, reps: int = 10000) -> tuple:
    idx_by = [np.flatnonzero(strata == s) for s in np.unique(strata)]
    out = np.empty(reps)
    for r in range(reps):
        take = np.concatenate([rng.choice(ix, ix.size, replace=True) for ix in idx_by])
        out[r] = x[take].sum() / y[take].sum() - 1
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), float(out.std(ddof=1))


def sim_power(y: np.ndarray, d_sd: float, strata: np.ndarray, n_per: dict, gain: float, tau: float,
              rng, sims: int = 2000, boots: int = 400) -> float:
    """Resampling power of 'lower bound of G > tau' with n lines (stratified) and a true gain `gain`.

    Baseline per-line values are resampled from the observed static* values; the proposed arm adds
    gain * baseline + noise with the observed paired-difference SD (centred), truncated at 0.
    """
    hits = 0
    pools = {s: y[strata == s] for s in np.unique(strata)}
    for _ in range(sims):
        base = np.concatenate([rng.choice(pools[s], n_per[s], replace=True) for s in pools])
        lab = np.concatenate([[s] * n_per[s] for s in pools])
        prop = np.clip(base * (1 + gain) + rng.normal(0, d_sd, base.size), 0, None)
        idx_by = [np.flatnonzero(lab == s) for s in pools]
        gs = np.empty(boots)
        for b in range(boots):
            take = np.concatenate([rng.choice(ix, ix.size, replace=True) for ix in idx_by])
            gs[b] = prop[take].sum() / base[take].sum() - 1
        hits += np.percentile(gs, 2.5) > tau
    return hits / sims


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    rng = np.random.default_rng(SEED)
    per = load_lines()
    keys = sorted(per)
    strata = np.array([k[0] for k in keys])
    both = np.array([len(per[k][BASE]) == 2 for k in keys])

    def arm_val(arm: str, field: int = 0, rep: str | None = None) -> np.ndarray:
        vals = []
        for k in keys:
            reps = per[k][arm]
            if rep is None:
                vals.append(np.mean([v[field] for v in reps.values()]))
            else:
                vals.append(reps[rep][field] if rep in reps else np.nan)
        return np.array(vals, float)

    avail = np.array([np.mean(list(per[k]["_available"].values())) for k in keys])
    menu = np.array([np.mean(list(per[k]["_menu"].values())) for k in keys])
    base = arm_val(BASE)
    out: dict = {
        "status": "EXPLORATORY: derived from already-written results of an opened release (Jaaks 2022); no raw outcome read",
        "plan": "review/plan.json A1",
        "units": int(len(keys)), "units_with_both_replicates": int(both.sum()),
        "per_tissue_units": {s: int((strata == s).sum()) for s in np.unique(strata)},
        "menu_mean": float(menu.mean()),
        "validated_available_per_line": {"mean": float(avail.mean()), "sd": float(avail.std(ddof=1)),
                                         "total": float(avail.sum()), "zero_share": float((avail == 0).mean())},
        "arms": {}, "paired_vs_static_star": {}, "replicate_correlation": {},
    }
    for arm in ARMS:
        v = arm_val(arm)
        out["arms"][arm] = {"validated_total": float(v.sum()), "per_line_mean": float(v.mean()),
                            "per_line_sd": float(v.std(ddof=1)), "zero_share": float((v == 0).mean()),
                            "per_tissue_mean": {s: float(v[strata == s].mean()) for s in np.unique(strata)}}
        if arm != BASE:
            d = v - base
            lo, hi, sd_g = strat_boot_ratio(v, base, strata, rng, reps=4000)
            out["paired_vs_static_star"][arm] = {
                "mean_diff": float(d.mean()), "sd_diff": float(d.std(ddof=1)), "nonzero_share": float((d != 0).mean()),
                "G": float(v.sum() / base.sum() - 1), "G_ci_line_bootstrap": [lo, hi], "G_boot_sd": sd_g,
                "sd_diff_single_replicate_SV": float(np.nanstd(arm_val(arm, rep="SV") - arm_val(BASE, rep="SV"), ddof=1)),
                "sd_diff_single_replicate_VS": float(np.nanstd(arm_val(arm, rep="VS") - arm_val(BASE, rep="VS"), ddof=1))}
    for arm in [BASE, "feedback"]:
        sv, vs = arm_val(arm, rep="SV"), arm_val(arm, rep="VS")
        ok = ~np.isnan(sv) & ~np.isnan(vs)
        out["replicate_correlation"][arm] = float(np.corrcoef(sv[ok], vs[ok])[0, 1])
    d = arm_val("feedback", rep="SV") - arm_val(BASE, rep="SV")
    d2 = arm_val("feedback", rep="VS") - arm_val(BASE, rep="VS")
    ok = ~np.isnan(d) & ~np.isnan(d2)
    out["replicate_correlation"]["feedback_minus_static_diff"] = float(np.corrcoef(d[ok], d2[ok])[0, 1])

    # follow-up (verify-hits) contrasts: SD back-calculated from bootstrap interval half-width
    fu = json.loads((PRIOR / "followup_verification.json").read_text(encoding="utf-8"))
    fol = {}
    for name, c in fu["contrasts"].items():
        se = (c["mean_diff_ci"][1] - c["mean_diff_ci"][0]) / (2 * 1.96)
        fol[name] = {"mean_diff": c["mean_diff"], "se_backcalc": se, "sd_diff_backcalc": se * math.sqrt(c["lines"]),
                     "relative_gain": c["relative_gain"], "relative_gain_ci": c["relative_gain_ci"]}
    out["followup_verify_hits"] = {
        "note": "per-line values not stored by the earlier follow-up; SD = interval half-width / 1.96 x sqrt(125) (approximation)",
        "static_verify_hits_per_line_mean": fu["totals"]["static_verify_hits"]["verified_discoveries"] / fu["units"],
        "static_verify_hits_hidden_validated_among_screen_hits": fu["totals"]["static_verify_hits"]["hidden_validated_among_screen_hits"],
        "contrasts": fol}

    # headroom (ceilings on the primary endpoint)
    svh = fu["totals"]["static_verify_hits"]["verified_discoveries"]
    out["headroom"] = {
        "screen_only_oracle_validated_over_static_star": float(out["arms"]["oracle_validated"]["validated_total"] / base.sum() - 1),
        "verify_hits_ceiling_all_available_over_static_verify_hits": float(avail.sum() / svh - 1),
        "scheduler_only_ceiling_same_screens": float(fu["totals"]["static_verify_hits"]["hidden_validated_among_screen_hits"] / svh - 1),
        "note": "oracle_validated buys every validated pair in budget, so the available total bounds any policy's confirmed discoveries at this budget; the scheduler-only ceiling assumes the same screened pairs and verification of every validated screen hit"}

    # design effect from pairs recurring across lines (earlier S13 vs line bootstrap of the same G)
    ver = json.loads((PRIOR / "jaaks_primary/verdict.json").read_text(encoding="utf-8"))["primary"]
    line_ci = ver["primary_contrast"]["relative_gain_ci"]
    s13 = ver["secondary"].get("S13_two_way_bootstrap_lines_x_pairs") or {}
    out["design_effect"] = {"line_ci": line_ci, "S13_entry": s13}

    # sample sizes
    mu_b = float(base.mean())
    mu_vh = out["followup_verify_hits"]["static_verify_hits_per_line_mean"]
    sds = {"feedback_vs_static_screen_only (line mean of 2 replicates)": out["paired_vs_static_star"]["feedback"]["sd_diff"],
           "feedback_vs_static_single_replicate": out["paired_vs_static_star"]["feedback"]["sd_diff_single_replicate_SV"],
           "feedback_verify_hits_vs_static_verify_hits (backcalc)": fol["feedback_verify_hits_minus_static_verify_hits"]["sd_diff_backcalc"],
           "verify_hits_vs_paired (backcalc)": fol["static_verify_hits_minus_static_paired"]["sd_diff_backcalc"],
           "random_vs_static (upper bound on policy disagreement)": out["paired_vs_static_star"]["random"]["sd_diff"]}
    table = []
    for label, sd in sds.items():
        for mu_name, mu in (("verify_hits_baseline", mu_vh), ("screen_only_baseline", mu_b)):
            for tau in (0.0, 0.05, 0.10):
                for g in sorted({0.05, 0.10, 0.15, 0.20}):
                    if g <= tau:
                        continue
                    # Var of Yp - (1+tau) Yb approximated by sd of the paired difference (tau small)
                    table.append({"sd_label": label, "sd": sd, "baseline": mu_name, "baseline_mean": mu,
                                  "tau": tau, "true_gain": g,
                                  "n80": math.ceil(n_required(sd, (g - tau) * mu, power=0.8)),
                                  "n90": math.ceil(n_required(sd, (g - tau) * mu, power=0.9))})
    out["sample_size_normal"] = table
    # futility reachable: upper bound < tau when true gain 0 (power 0.8)
    out["futility_n80"] = {f"tau={tau}": {label: math.ceil(n_required(sd, tau * mu_vh)) for label, sd in sds.items()}
                           for tau in (0.05, 0.10)}

    # resampling check (verify-hits scale: rescale static* per-line values to the verify-hits mean)
    scale = mu_vh / mu_b
    y = base * scale
    sd_check = fol["feedback_verify_hits_minus_static_verify_hits"]["sd_diff_backcalc"]
    share = {s: (strata == s).mean() for s in np.unique(strata)}
    sim = []
    for n in (125, 250, 400):
        n_per = {s: max(1, round(n * share[s])) for s in share}
        for g, tau in ((0.10, 0.0), (0.15, 0.0), (0.20, 0.10), (0.25, 0.10)):
            sim.append({"n_lines": n, "true_gain": g, "tau": tau,
                        "power_lower_bound_above_tau": sim_power(y, sd_check, strata, n_per, g, tau, rng, sims=400, boots=300)})
    out["sample_size_resampling_check"] = {"sd_diff": sd_check, "baseline_rescaled_mean": float(y.mean()),
                                           "sims": 400, "boots": 300, "results": sim,
                                           "note": "coarse Monte Carlo (400 x 300) to check the normal approximation; MC SE about 0.02"}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("units", "validated_available_per_line", "paired_vs_static_star", "replicate_correlation",
                                          "followup_verify_hits", "headroom", "design_effect", "futility_n80")}, indent=1))
    return 0




def check() -> int:
    """Addendum (2026-10-04): resampling power at sample sizes near the normal-approximation answers.

    The first check in power.json used n = 125/250/400, where power is trivially 1; this addendum
    uses n near the normal-approximation sizes and also checks futility (upper bound < tau when the
    true gain is 0). Writes review/power_check.json (refuses to overwrite).
    """
    out_path = HERE / "power_check.json"
    if out_path.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {out_path}")
    rng = np.random.default_rng(SEED + 1)
    prior = json.loads(OUT.read_text(encoding="utf-8"))
    per = load_lines()
    keys = sorted(per)
    strata = np.array([k[0] for k in keys])
    base = np.array([np.mean([v[0] for v in per[k][BASE].values()]) for k in keys])
    mu_vh = prior["followup_verify_hits"]["static_verify_hits_per_line_mean"]
    y = base * (mu_vh / base.mean())
    share = {s: (strata == s).mean() for s in np.unique(strata)}
    pools = {s: y[strata == s] for s in share}
    sds = {"line_mean_of_2_replicates": prior["followup_verify_hits"]["contrasts"][
        "feedback_verify_hits_minus_static_verify_hits"]["sd_diff_backcalc"]}
    sds["single_replicate"] = sds["line_mean_of_2_replicates"] * (
        prior["paired_vs_static_star"]["feedback"]["sd_diff_single_replicate_SV"]
        / prior["paired_vs_static_star"]["feedback"]["sd_diff"])
    res = []
    for sd_label, sd in sds.items():
        for n, gain, tau, kind in ((40, 0.10, 0.0, "superiority"), (60, 0.10, 0.0, "superiority"),
                                   (40, 0.20, 0.10, "threshold"), (60, 0.20, 0.10, "threshold"),
                                   (150, 0.10, 0.05, "threshold"), (200, 0.10, 0.05, "threshold"),
                                   (40, 0.0, 0.10, "futility"), (60, 0.0, 0.10, "futility"),
                                   (150, 0.0, 0.05, "futility"), (200, 0.0, 0.05, "futility")):
            n_per = {s: max(1, round(n * share[s])) for s in share}
            hits = 0
            sims, boots = 500, 400
            for _ in range(sims):
                b = np.concatenate([rng.choice(pools[s], n_per[s], replace=True) for s in pools])
                lab = np.concatenate([[s] * n_per[s] for s in pools])
                p = np.clip(b * (1 + gain) + rng.normal(0, sd, b.size), 0, None)
                idx_by = [np.flatnonzero(lab == s) for s in pools]
                gs = np.empty(boots)
                for k in range(boots):
                    t = np.concatenate([rng.choice(ix, ix.size, replace=True) for ix in idx_by])
                    gs[k] = p[t].sum() / b[t].sum() - 1
                lo, hi = np.percentile(gs, [2.5, 97.5])
                hits += (lo > tau) if kind != "futility" else (hi < tau)
            res.append({"sd_label": sd_label, "sd_diff": sd, "n_lines": n, "true_gain": gain, "tau": tau,
                        "event": "lower bound > tau" if kind != "futility" else "upper bound < tau",
                        "power": hits / sims})
    note = ("Monte Carlo 500 studies x 400 bootstrap resamples (MC SE about 0.02). The generating model adds a "
            "constant relative gain plus Gaussian paired noise with the observed SD and truncates at 0; truncation "
            "slightly inflates the realised gain when the true gain is 0, so futility power is approximate.")
    out_path.write_text(json.dumps({"status": "EXPLORATORY (derived from exposed results)", "results": res, "note": note},
                                   indent=1), encoding="utf-8")
    for r in res:
        print(r)
    return 0


def check2() -> int:
    """Addendum 2 (2026-10-04): joint empirical resampling of (baseline, paired difference) per line.

    power_check.json generated the proposed arm as baseline x (1+gain) + Gaussian noise truncated at 0;
    with 29% zero-baseline lines the truncation adds about +2.5 points of spurious gain, which makes
    superiority look easier and futility harder than they are. This addendum resamples observed
    (static*, other-arm) line pairs jointly, centres the observed difference on zero and adds
    gain x baseline, with no truncation. Writes review/power_check2.json (refuses to overwrite).
    """
    out_path = HERE / "power_check2.json"
    if out_path.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {out_path}")
    rng = np.random.default_rng(SEED + 2)
    per = load_lines()
    keys = sorted(per)
    strata = np.array([k[0] for k in keys])
    share = {s: (strata == s).mean() for s in np.unique(strata)}
    base_all = {rep: np.array([per[k][BASE].get(rep, (np.nan,))[0] for k in keys]) for rep in ("SV", "VS")}
    base_mean = np.array([np.mean([v[0] for v in per[k][BASE].values()]) for k in keys])
    res = []
    for arm in ("feedback", "history_rate", "gbm_static"):
        arm_mean = np.array([np.mean([v[0] for v in per[k][arm].values()]) for k in keys])
        arm_sv = np.array([per[k][arm]["SV"][0] for k in keys])
        for design, b, a in (("line_mean_of_2_replicates", base_mean, arm_mean), ("single_replicate_SV", base_all["SV"], arm_sv)):
            d = a - b
            d = d - d.sum() / b.sum() * b          # remove the observed relative gain (ratio-of-sums null)
            for n, gain, tau, kind in ((40, 0.10, 0.0, "sup"), (60, 0.10, 0.0, "sup"), (100, 0.10, 0.0, "sup"),
                                       (60, 0.20, 0.10, "sup"), (100, 0.20, 0.10, "sup"),
                                       (60, 0.0, 0.10, "fut"), (100, 0.0, 0.10, "fut"), (150, 0.0, 0.10, "fut"),
                                       (200, 0.0, 0.05, "fut"), (400, 0.0, 0.05, "fut")):
                n_per = {s: max(1, round(n * share[s])) for s in share}
                pools = {s: np.flatnonzero(strata == s) for s in share}
                hits, sims, boots = 0, 400, 400
                for _ in range(sims):
                    take = np.concatenate([rng.choice(pools[s], n_per[s], replace=True) for s in pools])
                    lab = np.concatenate([[s] * n_per[s] for s in pools])
                    bb = b[take]
                    pp = bb * (1 + gain) + d[take]
                    idx_by = [np.flatnonzero(lab == s) for s in pools]
                    gs = np.empty(boots)
                    for k in range(boots):
                        t = np.concatenate([rng.choice(ix, ix.size, replace=True) for ix in idx_by])
                        gs[k] = pp[t].sum() / bb[t].sum() - 1
                    lo, hi = np.percentile(gs, [2.5, 97.5])
                    hits += (lo > tau) if kind == "sup" else (hi < tau)
                res.append({"difference_source": f"{arm} - {BASE}", "design": design, "n_lines": n, "true_gain": gain,
                            "tau": tau, "event": "lower bound > tau" if kind == "sup" else "upper bound < tau",
                            "power": hits / sims})
                print(res[-1])
    out_path.write_text(json.dumps({"status": "EXPLORATORY (derived from exposed results)", "results": res,
                                    "note": "screen-only validated discoveries (static* = history_mean) as the baseline scale; 400 studies x 400 bootstrap resamples (MC SE about 0.025)"},
                                   indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(check2() if "--check2" in sys.argv else check() if "--check" in sys.argv else main())
