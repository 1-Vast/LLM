"""Feature-group ablation and shuffle-control decomposition on O'Neil (development, exposed).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/coupling_ablation.py
- Purpose: quantify how much of the frozen world model's prior ranking power and of its
  campaign hits depends on target-line single-agent inputs (M), the target-line Bliss
  expectation that the O'Neil label subtracts (E), similarity-weighted history whose weights come
  from target-line singles (S), the drug-similarity kernel, and history-only inputs (H). Also
  decomposes the registered `wm_shuffled` control into its components.
- Core points:
  - Sanity first: the wrapper must reproduce the registered development totals (history 401,
    wm_static 407, wm_full 475, wm_nocontext 476, wm_shuffled 440) or the script stops.
  - Within-line Spearman correlations between `expected`/mono features and the label on both
    cached libraries (ALMANAC cache is exposed; exploratory only).
  - Bootstrap over target lines (4,000 draws, seed 20261003).
- Interfaces: `python coupling_ablation.py` -> outputs/coupling_ablation.json
- Depends on: common.py (frozen world/agent imported read-only).
"""
from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import stats

from common import (ALMANAC, GROUPS, ONEIL, MaskedWorld, PartialShuffleWorld, TransferWorld, WorldConfig,
                    bootstrap_ci, columns_for, load, prior_metrics, replace, run_arm, sha256_file, write_json)

VARIANTS = {
    # name: (columns or None, identity_kernel, context flag)
    "full": (None, False, True),                         # registered wm_full world
    "noE": (columns_for("HSM"), False, True),
    "noME": (columns_for("HS"), False, True),
    "H_kernel": (columns_for("H"), False, True),
    "nocontext": (None, True, False),                     # registered wm_nocontext world
    "H_E_idk": (columns_for("HE"), True, True),
    "H_ME_idk": (columns_for("HME"), True, True),
    "full_idk": (None, True, True),
}
SHUFFLES = {
    "all": ("line_sim", "drug_kernel", "mono", "expected_formula"),
    "line_sim": ("line_sim",),
    "drug_kernel": ("drug_kernel",),
    "mono": ("mono",),
    "expected_formula": ("expected_formula",),
    "mono+expected_formula": ("mono", "expected_formula"),
}
SHUFFLE_SEED_OFFSETS = (1000, 2000, 3000, 4000, 5000)   # 1000 + line is the registered seed


def run_line(line: int) -> dict:
    lib = load(ONEIL)
    y = lib.y[lib.c == line]
    out = {"line": line, "variants": {}, "shuffles": {}}
    for name, (cols, idk, ctx) in VARIANTS.items():
        cfg = WorldConfig(context=ctx)
        world = MaskedWorld(lib, line, cfg, columns=cols, identity_kernel=idk)
        rec = {"prior": prior_metrics(world, y)}
        for kind in ("wm_static", "wm_full"):
            rec[kind] = run_arm(lib, world, kind, line)["exploit"]["hits"]
        if name == "full":
            rec["history"] = run_arm(lib, world, "history", line)["exploit"]["hits"]
            rec["beta"] = world.beta.tolist()
            rec["x_sd"] = world.x_sd.tolist()
        out["variants"][name] = rec
    for name, comps in SHUFFLES.items():
        recs = []
        offsets = SHUFFLE_SEED_OFFSETS if name != "expected_formula" else SHUFFLE_SEED_OFFSETS[:1]
        for off in offsets:
            world = PartialShuffleWorld(lib, line, off + line, comps)
            recs.append({"seed": off + line, "prior": prior_metrics(world, y),
                         "wm_full": run_arm(lib, world, "wm_full", line)["exploit"]["hits"],
                         "wm_static": run_arm(lib, world, "wm_static", line)["exploit"]["hits"]})
        out["shuffles"][name] = recs
    # parity: frozen shuffled world (registered seed) vs PartialShuffleWorld(all)
    frozen = TransferWorld(lib, line, WorldConfig(shuffle_seed=1000 + line))
    mine = PartialShuffleWorld(lib, line, 1000 + line, SHUFFLES["all"])
    out["shuffle_parity_max_abs"] = float(np.max(np.abs(frozen.prior_target - mine.prior_target)))
    out["wm_shuffled_registered"] = run_arm(lib, frozen, "wm_full", line)["exploit"]["hits"]
    return out


def coupling_correlations(path) -> dict:
    lib = load(path)
    rows = {"spearman_expected_y": [], "spearman_monomin_y": [], "spearman_monomax_y": [],
            "spearman_potency_y": []}
    for l in range(len(lib.lines)):
        k = lib.c == l
        if k.sum() < 10:
            continue
        y = lib.y[k]
        ma, mb = lib.mono_mean[lib.a[k], l], lib.mono_mean[lib.b[k], l]
        rows["spearman_expected_y"].append(stats.spearmanr(lib.expected[k], y).correlation)
        rows["spearman_monomin_y"].append(stats.spearmanr(np.fmin(ma, mb), y).correlation)
        rows["spearman_monomax_y"].append(stats.spearmanr(np.fmax(ma, mb), y).correlation)
        rows["spearman_potency_y"].append(stats.spearmanr(np.nan_to_num(ma) + np.nan_to_num(mb), y).correlation)
    q = np.quantile(lib.expected, np.linspace(0, 1, 11))
    dec = np.clip(np.searchsorted(q, lib.expected, side="right") - 1, 0, 9)
    return {
        "library": lib.name, "experiments": int(lib.y.size), "lines": len(lib.lines),
        **{k: {"median": float(np.median(v)), "q25": float(np.percentile(v, 25)), "q75": float(np.percentile(v, 75)),
               "lines_negative": int(np.sum(np.array(v) < 0)), "n": len(v)} for k, v in rows.items()},
        "pooled_pearson_expected_y": float(np.corrcoef(lib.expected, lib.y)[0, 1]),
        "hit_rate_by_expected_decile": [float(lib.hits[dec == i].mean()) for i in range(10)],
    }


def summarise(per_line: list[dict]) -> dict:
    lines = sorted(r["line"] for r in per_line)
    by = {r["line"]: r for r in per_line}
    summary = {"variants": {}, "contrasts": {}, "shuffles": {}}
    for name in VARIANTS:
        static = np.array([by[l]["variants"][name]["wm_static"] for l in lines], float)
        full = np.array([by[l]["variants"][name]["wm_full"] for l in lines], float)
        pr = [by[l]["variants"][name]["prior"] for l in lines]
        summary["variants"][name] = {
            "wm_static_hits": float(static.sum()), "wm_full_hits": float(full.sum()),
            "prior_hits_top_budget": int(sum(p["hits_top_budget"] for p in pr)),
            "prior_spearman_median": float(np.median([p["spearman"] for p in pr])),
            "prior_auc_median": float(np.median([p["auc"] for p in pr if p["auc"] is not None])),
        }
    hist = np.array([by[l]["variants"]["full"]["history"] for l in lines], float)
    summary["history_hits"] = float(hist.sum())
    ref = {k: np.array([by[l]["variants"]["full"][k] for l in lines], float) for k in ("wm_static", "wm_full")}
    for name in VARIANTS:
        if name == "full":
            continue
        for kind in ("wm_static", "wm_full"):
            d = ref[kind] - np.array([by[l]["variants"][name][kind] for l in lines], float)
            summary["contrasts"][f"full-{name}:{kind}"] = {"mean_per_line": float(d.mean()), "sum": float(d.sum()),
                                                           "ci95": bootstrap_ci(d)}
        d = np.array([by[l]["variants"]["full"]["prior"]["hits_top_budget"] - by[l]["variants"][name]["prior"]["hits_top_budget"] for l in lines], float)
        summary["contrasts"][f"full-{name}:prior_top_budget"] = {"mean_per_line": float(d.mean()), "sum": float(d.sum()),
                                                                  "ci95": bootstrap_ci(d)}
    # history-only vs history arm
    for name in ("nocontext", "H_kernel"):
        d = np.array([by[l]["variants"][name]["wm_static"] for l in lines], float) - hist
        summary["contrasts"][f"{name}:wm_static-history"] = {"mean_per_line": float(d.mean()), "ci95": bootstrap_ci(d)}
    for name in SHUFFLES:
        full_mean = np.array([np.mean([r["wm_full"] for r in by[l]["shuffles"][name]]) for l in lines])
        static_mean = np.array([np.mean([r["wm_static"] for r in by[l]["shuffles"][name]]) for l in lines])
        first = np.array([by[l]["shuffles"][name][0]["wm_full"] for l in lines], float)
        d = ref["wm_full"] - full_mean
        summary["shuffles"][name] = {
            "wm_full_hits_mean_over_seeds": float(full_mean.sum()),
            "wm_full_hits_registered_seed": float(first.sum()),
            "wm_static_hits_mean_over_seeds": float(static_mean.sum()),
            "full_minus_shuffle_wm_full_per_line": float(d.mean()), "ci95": bootstrap_ci(d),
            "seeds_per_line": len(by[lines[0]]["shuffles"][name]),
        }
    summary["shuffle_parity_max_abs"] = float(max(by[l]["shuffle_parity_max_abs"] for l in lines))
    summary["wm_shuffled_registered_hits"] = float(sum(by[l]["wm_shuffled_registered"] for l in lines))
    beta = np.array([by[l]["variants"]["full"]["beta"] for l in lines])
    summary["full_prior_standardised_beta_median"] = dict(zip(
        ["pair_mean", "drug_max", "drug_min", "sim_pair_mean", "sim_drug_max", "sim_drug_min", "mono_mean_max",
         "mono_mean_min", "mono_top_max", "mono_top_min", "expected"], np.median(beta, axis=0).round(3).tolist()))
    return summary


def main() -> int:
    started = time.time()
    lib = load(ONEIL)
    with ProcessPoolExecutor(max_workers=16) as pool:
        per_line = list(pool.map(run_line, range(len(lib.lines))))
    summary = summarise(per_line)
    registered = {"history": 401, "wm_static": 407, "wm_full": 475, "wm_nocontext": 476, "wm_shuffled": 440}
    parity = {
        "history": summary["history_hits"], "wm_static": summary["variants"]["full"]["wm_static_hits"],
        "wm_full": summary["variants"]["full"]["wm_full_hits"],
        "wm_nocontext": summary["variants"]["nocontext"]["wm_full_hits"],
        "wm_shuffled": summary["wm_shuffled_registered_hits"],
    }
    payload = {
        "purpose": "WS2 coupling ablation on O'Neil (development, exposed) + coupling correlations",
        "library_sha256": {"oneil_v1.npz": sha256_file(ONEIL), "almanac_v1.npz": sha256_file(ALMANAC)},
        "registered_dev_totals": registered, "reproduced_totals": parity,
        "parity_ok": all(abs(parity[k] - registered[k]) < 0.5 for k in registered),
        "variants_definition": {k: {"columns": v[0], "identity_kernel": v[1], "context": v[2]} for k, v in VARIANTS.items()},
        "groups": GROUPS, "shuffle_components": SHUFFLES, "shuffle_seed_offsets": SHUFFLE_SEED_OFFSETS,
        "coupling_correlations": {"oneil": coupling_correlations(ONEIL), "almanac_exploratory": coupling_correlations(ALMANAC)},
        "summary": summary, "per_line": per_line, "wall_seconds": round(time.time() - started, 1),
    }
    path = write_json("coupling_ablation.json", payload)
    print(path, "parity", payload["parity_ok"], parity)
    for k, v in summary["variants"].items():
        print(f"{k:12s} static {v['wm_static_hits']:6.0f} full {v['wm_full_hits']:6.0f} prior@B {v['prior_hits_top_budget']:5d} rho {v['prior_spearman_median']:.3f}")
    for k, v in summary["contrasts"].items():
        print(k, round(v["mean_per_line"], 3), [round(x, 3) for x in v["ci95"]])
    for k, v in summary["shuffles"].items():
        print("shuffle", k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
