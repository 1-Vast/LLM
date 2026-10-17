"""Development run on exposed PRISM 19Q4: tune on folds 0-1, estimate on folds 2-4.

File summary
- Path: research/indication_triage_20261016/develop.py
- Purpose: fix every free choice of the protocol on development data and measure the effect and
  variance the power calculation needs, without touching PRISM 24Q2.
- Core points:
  - Cross-fitting by MoA-family fold: each evaluated fold is predicted from a world model fitted
    on the other four folds. The generic profile G of the training folds defines the development
    endpoint (as in knowledge_reality's development run).
  - Tuning folds 0 and 1, primary budget w = 16 wells per compound:
    - `maestro_loop` grid: seed lines k1 in {0, 2, 4, 8}, adaptive lines per compound k2 in
      {8, 16, 32, 64}, adaptive line rule in {likely, uncertain};
    - `two_stage` first-panel lines k1 in {2, 4, 8}, second-stage lines k2 in {8, 16, 32, 64};
    - `probe_knn` neighbours in {10, 20, 40};
    - the H1 comparator is the arm in `policy.COMPARATORS` with most tuning hits.
    Ties go to the first option in the listed order.
  - Estimation folds 2, 3 and 4: every arm at w in {4, 8, 16, 32} with the tuned choices. The
    primary development contrast is maestro_loop minus the chosen comparator at w = 16, per
    campaign, with a one-sided sign-flip p.
  - Probe noise follows the replicate spread of the published value's effect bin (BUILD.json);
    sensitivity at 0 and 2 x that noise for the loop and the comparator at w = 16.
- Output: DEVELOPMENT.json (and a run log on stdout).
- Usage: `python -B develop.py [--smoke] [--out PATH]`.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import numpy as np

from common import CACHE, HERE, SEED, campaigns, events, h, sha256, sign_flip, write_json
from policy import ARMS, COMPARATORS, Context, grade, run_arm
from world import World

PRIMARY_W = 16
BUDGETS = (4, 8, 16, 32)
TUNING_FOLDS = (0, 1)
ESTIMATION_FOLDS = (2, 3, 4)
LOOP_GRID = [{"k1": k1, "k2": k2, "rule": rule}
             for k1, k2, rule in itertools.product((0, 2, 4, 8), (8, 16, 32, 64), ("likely", "uncertain"))]
TWO_STAGE_GRID = [{"k1": k1, "k2": k2} for k1, k2 in itertools.product((2, 4, 8), (8, 16, 32, 64))]
KNN_GRID = [{"knn": k} for k in (10, 20, 40)]


def load() -> dict:
    T = dict(np.load(CACHE / "tables.npz"))
    build = json.loads((HERE / "BUILD.json").read_text(encoding="utf-8"))
    if sha256(CACHE / "tables.npz") != build["tables_sha256"]:
        raise SystemExit("TABLES_DIGEST_MISMATCH: rerun build.py")
    noise = build["probe_noise"]
    T["sigma_probe"] = noise["sigma_probe"]
    T["noise_bins"] = noise["sigma_replicate_by_centre"]
    T["noise_factor"] = noise["median3_variance_factor"]
    return T


def probe_sd(Y: np.ndarray, T: dict, mult: float) -> np.ndarray:
    """Probe noise SD per (compound, line): replicate spread in the published value's effect bin."""

    b = T["noise_bins"]
    rep = np.select([Y <= -2.0, Y <= -1.0, Y <= 0.0],
                    [b["le_-2"]["sigma_replicate"], b["-2_-1"]["sigma_replicate"], b["-1_0"]["sigma_replicate"]],
                    b["gt_0"]["sigma_replicate"])
    return mult * np.sqrt(2.0 * T["noise_factor"]) * rep


def context(T: dict, fold: int, mult: float, smoke: bool) -> tuple[Context, list[np.ndarray]]:
    train = np.where(T["fold"] != fold)[0]
    test = np.where(T["fold"] == fold)[0]
    if smoke:
        test = test[np.array([h(str(c), "smoke") % 6 == 0 for c in T["cores"][test]])]
    Y = T["Y"].astype(np.float64)
    G = np.nanmedian(Y[train], axis=0)
    world = World(Y[train], T["fp"][train], G, max(T["sigma_probe"] * mult, 1e-3))
    cores = T["cores"][test]
    noise = np.stack([np.random.default_rng(h(str(c), "probe") % (2 ** 32)).standard_normal(Y.shape[1]) for c in cores])
    ctx = Context(world=world, cores=cores, Y=Y[test], truth=events(Y[test], G), prior=world.prior(T["fp"][test]),
                  noise=probe_sd(Y[test], T, mult) * noise, design=world.sparse_design(64), lineage=T["lineage"])
    return ctx, campaigns(cores)


def run(ctx: Context, camps: list[np.ndarray], arm: str, w: int, params: dict | None, fold: int) -> list[dict]:
    out = []
    for c, idx in enumerate(camps):
        g = grade(ctx, idx, run_arm(arm, ctx, idx, w, params), f"{fold}:{c}")
        g["actives"] = int((ctx.truth[idx].sum(1) >= 5).sum())
        g["events"] = int(ctx.truth[idx].sum())
        out.append(g)
    return out


def total(rows: list[dict]) -> int:
    return int(sum(r["hits"] for r in rows))


def summary(rows: list[dict]) -> dict:
    hits = np.array([r["hits"] for r in rows])
    cert = [r["certificate"] for r in rows]
    return {"campaigns": len(rows), "hits": int(hits.sum()), "hits_per_campaign": float(hits.mean()),
            "hit_rate": float(hits.sum() / max(sum(r["listed"] for r in rows), 1)),
            "lineage_hits": int(sum(r["lineage_hits"] for r in rows)),
            "wells": int(sum(r["wells"] for r in rows)), "failed_wells": int(sum(r["failed_wells"] for r in rows)),
            "cycles": rows[0]["cycles"] if rows else None,
            "certificate": {"coverage": float(np.mean([c["covered"] for c in cert])),
                            "violations": int(sum(not c["covered"] for c in cert)),
                            "mean_bound": float(np.mean([c["yield_bound"] for c in cert])),
                            "mean_remainder_hits": float(np.mean([c["remainder_hits"] for c in cert]))},
            **({"refused_POSTERIOR_INACTIVE": int(sum(r["refusals"]["POSTERIOR_INACTIVE"] for r in rows)),
                "adaptive_compounds": int(sum(r["adaptive_compounds"] for r in rows))} if "refusals" in rows[0] else {})}


def bootstrap_ci(d: np.ndarray, draws: int = 4000) -> list[float]:
    rng = np.random.default_rng(SEED)
    means = d[rng.integers(0, len(d), size=(draws, len(d)))].mean(1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None, help="write the result here instead of DEVELOPMENT.json")
    args = ap.parse_args()
    t0 = time.time()
    T = load()
    sigma = T["sigma_probe"]
    ctxs = {f: context(T, f, 1.0, args.smoke) for f in range(5)}
    print(f"contexts {time.time() - t0:.0f}s", flush=True)

    # ---- tuning ----------------------------------------------------------------------------
    def tuning_hits(arm, params):
        return sum(total(run(*ctxs[f], arm, PRIMARY_W, params, f)) for f in TUNING_FOLDS)

    loop_scores = [(tuning_hits("maestro_loop", p), -i, p) for i, p in enumerate(LOOP_GRID)]
    loop_params = max(loop_scores, key=lambda r: (r[0], r[1]))[2]
    print("loop tuned", loop_params, f"{time.time() - t0:.0f}s", flush=True)
    knn_scores = [(tuning_hits("probe_knn", p), -i, p) for i, p in enumerate(KNN_GRID)]
    knn_params = max(knn_scores, key=lambda r: (r[0], r[1]))[2]
    two_scores = [(tuning_hits("two_stage", p), -i, p) for i, p in enumerate(TWO_STAGE_GRID)]
    two_params = max(two_scores, key=lambda r: (r[0], r[1]))[2]
    params = {"maestro_loop": loop_params, "probe_knn": knn_params, "two_stage": two_params}
    comp_scores = {a: tuning_hits(a, params.get(a)) for a in COMPARATORS}
    comparator = max(COMPARATORS, key=lambda a: (comp_scores[a], -COMPARATORS.index(a)))
    tuning = {"folds": list(TUNING_FOLDS), "w": PRIMARY_W,
              "maestro_loop_grid": [{"params": p, "hits": s} for s, _, p in loop_scores],
              "probe_knn_grid": [{"params": p, "hits": s} for s, _, p in knn_scores],
              "two_stage_grid": [{"params": p, "hits": s} for s, _, p in two_scores],
              "comparator_hits": comp_scores, "maestro_loop_hits": max(r[0] for r in loop_scores),
              "chosen": {"maestro_loop": loop_params, "probe_knn": knn_params, "two_stage": two_params,
                         "comparator": comparator}}
    print("comparator", comparator, comp_scores, f"{time.time() - t0:.0f}s", flush=True)

    # ---- estimation ------------------------------------------------------------------------
    est: dict = {}
    for w in BUDGETS:
        for arm in ARMS:
            if arm in ("zero", "full_panel", "oracle") and w != PRIMARY_W:
                continue
            rows = [r for f in ESTIMATION_FOLDS for r in run(*ctxs[f], arm, w, params.get(arm), f)]
            est.setdefault(str(w), {})[arm] = {"summary": summary(rows), "per_campaign": [r["hits"] for r in rows]}
        print("budget", w, {a: v["summary"]["hits"] for a, v in est[str(w)].items()}, f"{time.time() - t0:.0f}s", flush=True)
    prim = est[str(PRIMARY_W)]
    loop = np.array(prim["maestro_loop"]["per_campaign"], dtype=float)
    comp = np.array(prim[comparator]["per_campaign"], dtype=float)
    d = loop - comp
    contrast = {"comparator": comparator, **sign_flip(d), "ci95_bootstrap": bootstrap_ci(d),
                "relative_gain": float(d.sum() / max(comp.sum(), 1)),
                "campaigns_loop_better": int((d > 0).sum()), "campaigns_tied": int((d == 0).sum())}
    curve = {}
    for w in BUDGETS:
        l = np.array(est[str(w)]["maestro_loop"]["per_campaign"], float)
        c = np.array(est[str(w)][comparator]["per_campaign"], float)
        curve[str(w)] = {"loop": float(l.sum()), "comparator": float(c.sum()), **sign_flip(l - c)}
    full = prim["full_panel"]["summary"]["hits"]
    secondary = {
        "full_panel_recovery": float(prim["maestro_loop"]["summary"]["hits"] / max(full, 1)),
        "full_panel_wells_ratio": float(prim["maestro_loop"]["summary"]["wells"] / max(prim["full_panel"]["summary"]["wells"], 1)),
        "loop_minus_structure": sign_flip(loop - np.array(prim["structure"]["per_campaign"], float)),
        "loop_minus_fixed_calibrated": sign_flip(loop - np.array(prim["fixed_calibrated"]["per_campaign"], float)),
        "loop_minus_two_stage": sign_flip(loop - np.array(prim["two_stage"]["per_campaign"], float)),
        "fixed_calibrated_minus_fixed_panel": sign_flip(np.array(prim["fixed_calibrated"]["per_campaign"], float)
                                                        - np.array(prim["fixed_panel"]["per_campaign"], float)),
        "budget_curve": curve,
    }

    # ---- probe-noise sensitivity -----------------------------------------------------------
    sens = {}
    for mult in (0.0, 2.0):
        rows_l, rows_c = [], []
        for f in ESTIMATION_FOLDS:
            ctx, camps = context(T, f, mult, args.smoke)
            rows_l += run(ctx, camps, "maestro_loop", PRIMARY_W, loop_params, f)
            rows_c += run(ctx, camps, comparator, PRIMARY_W, params.get(comparator), f)
        dl = np.array([r["hits"] for r in rows_l], float) - np.array([r["hits"] for r in rows_c], float)
        sens[str(mult)] = {"loop": total(rows_l), "comparator": total(rows_c), **sign_flip(dl)}
        print("noise", mult, sens[str(mult)], f"{time.time() - t0:.0f}s", flush=True)

    pop = {}
    for f in ESTIMATION_FOLDS:
        ctx, camps = ctxs[f]
        pop[str(f)] = {"compounds": int(len(ctx.cores)), "campaigns": len(camps),
                       "active": int((ctx.truth.sum(1) >= 5).sum()), "events": int(ctx.truth.sum())}
    out = args.out or HERE / ("DEVELOPMENT_SMOKE.json" if args.smoke else "DEVELOPMENT.json")
    write_json(out, {
        "reads": "PRISM 19Q4 primary (exposed) and the 24Q2 census line list; no 24Q2 response value",
        "smoke": bool(args.smoke), "sigma_probe": sigma, "primary_w": PRIMARY_W,
        "tuning": tuning, "population": pop, "primary_contrast": contrast, "secondary": secondary,
        "noise_sensitivity": sens,
        "estimation": {w: {a: v["summary"] for a, v in arms.items()} for w, arms in est.items()},
        "per_campaign_primary": {a: v["per_campaign"] for a, v in prim.items()},
        "tables_sha256": sha256(CACHE / "tables.npz"), "seconds": round(time.time() - t0, 1)})
    print("done", contrast, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
