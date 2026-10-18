"""Erratum: the secondary equal-lineage bootstrap of analyse.py dropped the multiplicity of resampled lineages.

File summary
- Path: research/seed_attribution_20261017/erratum_equal_lineage_bootstrap.py
- Purpose: separate, unfrozen record of one defect in a SECONDARY statistic of the frozen study, and its
  correction recomputed from the public per-lineage means in RESULTS.json only (no PRISM data, no records).
- Defect: `analyse.cluster_boot` draws lineage indices with replacement, concatenates the lines of the drawn
  lineages, and passes them to `equal_cluster_mean`, which takes `sorted(set(g))`. A lineage drawn twice
  therefore counts once, and a lineage not drawn is dropped, so the statistic is the mean over the DISTINCT
  drawn lineages, not over the 21 draws. A correct cluster bootstrap of the equal-lineage mean is the mean of the
  21 drawn lineage means, repeats included.
- Unaffected: the primary tests and Holm family (`common.paired` weights drawn clusters by sums[picks]/sizes[picks]
  and keeps multiplicity), the point estimates, the pooled and stratum contrasts, the leave-one-lineage-out
  ranges. Stop decisions are unchanged (nothing here is a gate).
- Steps: (1) replay the flawed estimator from the per-lineage means with the frozen seed and 2,000 draws and
  require it to match the saved intervals exactly (proves the diagnosis and the data path); (2) apply the
  corrected statistic to the SAME index draws; (3) repeat with 100,000 draws for Monte Carlo stability.
- Interfaces: `python -B erratum_equal_lineage_bootstrap.py` writes ERRATUM_equal_lineage_bootstrap.json once.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED, BOOT = 20261017, 2000
LAYERS = ("policy", "I2", "I1")


def lineage_means(results: dict, layer: str) -> tuple[list[str], np.ndarray, np.ndarray]:
    per = results["lineage_support"][layer]["per_lineage"]
    labels = sorted(per)
    return labels, np.array([per[l]["mean"] for l in labels], float), np.array([per[l]["lines"] for l in labels], float)


def flawed_stat(means: np.ndarray, pick: np.ndarray) -> float:
    """What analyse.equal_cluster_mean computed: the mean over the distinct drawn lineages."""

    return float(means[np.unique(pick)].mean())


def corrected_stat(means: np.ndarray, pick: np.ndarray) -> float:
    """Equal-lineage mean of the draw with multiplicity: each drawn lineage counts once per draw."""

    return float(means[pick].mean())


def intervals(means: np.ndarray, draws: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(means), size=(draws, len(means)))
    flawed = np.array([flawed_stat(means, p) for p in picks])
    fixed = means[picks].mean(1)
    q = lambda v: [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))]
    return {"flawed_ci95": q(flawed), "corrected_ci95": q(fixed),
            "corrected_mean_of_draws": float(fixed.mean()),
            "share_of_draws_with_repeated_lineage": float(np.mean([len(np.unique(p)) < len(p) for p in picks])),
            "mean_distinct_lineages_per_draw": float(np.mean([len(np.unique(p)) for p in picks]))}


def main() -> None:
    out_path = HERE / "ERRATUM_equal_lineage_bootstrap.json"
    if out_path.exists():
        raise SystemExit("erratum record exists; write-once")
    results = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    rows = {}
    for layer in LAYERS:
        labels, means, sizes = lineage_means(results, layer)
        saved = results["standardised"][layer]["equal_lineage_weights"]
        estimate = float(means.mean())
        replay = intervals(means, BOOT, SEED)
        reproduces = bool(np.isclose(estimate, saved["estimate"], atol=1e-12)
                          and np.allclose(replay["flawed_ci95"], saved["ci95"], atol=1e-12))
        large = intervals(means, 100000, SEED + 1)
        rows[layer] = {
            "n_lineages": len(labels), "equal_lineage_estimate": estimate,
            "saved_interval_flawed": saved["ci95"],
            "flawed_replay_from_public_means_matches_saved": reproduces,
            "corrected_interval_same_2000_draws": replay["corrected_ci95"],
            "corrected_interval_100000_draws": large["corrected_ci95"],
            "flawed_interval_100000_draws": large["flawed_ci95"],
            "mean_distinct_lineages_per_draw": large["mean_distinct_lineages_per_draw"],
            "lower_bound_changes_sign": bool((saved["ci95"][0] > 0) != (large["corrected_ci95"][0] > 0)),
            "upper_bound_changes_sign": bool((saved["ci95"][1] > 0) != (large["corrected_ci95"][1] > 0)),
            "corrected_excludes_zero": bool(large["corrected_ci95"][0] > 0 or large["corrected_ci95"][1] < 0),
            "saved_excludes_zero": bool(saved["ci95"][0] > 0 or saved["ci95"][1] < 0),
        }
    record = {
        "study": "seed_attribution_20261017", "kind": "ERRATUM", "recorded": "2026-10-18",
        "defect": "analyse.cluster_boot -> equal_cluster_mean uses set(groups): repeated lineages counted once, undrawn lineages dropped",
        "scope": "secondary equal-lineage interval only (RESULTS.json standardised.*.equal_lineage_weights.ci95; quoted in REPORT.md and EVIDENCE.md)",
        "unaffected": ["primary tests P1-P3 and Holm p (common.paired keeps multiplicity)", "all point estimates",
                       "pooled, stratum and leave-one-lineage-out numbers", "NOT_CONFIRMED verdicts and every stop decision"],
        "source": "RESULTS.json per-lineage means only; no PRISM data or per-line records read; analyse.py and FREEZE.json untouched",
        "layers": rows,
    }
    out_path.write_bytes((json.dumps(record, indent=1, allow_nan=False) + "\n").encode("utf-8"))
    for layer, r in rows.items():
        print(layer, "est %.4f" % r["equal_lineage_estimate"], "| saved", [round(x, 3) for x in r["saved_interval_flawed"]],
              "| replay matches", r["flawed_replay_from_public_means_matches_saved"],
              "| corrected", [round(x, 3) for x in r["corrected_interval_100000_draws"]],
              "| 2000-draw", [round(x, 3) for x in r["corrected_interval_same_2000_draws"]])


if __name__ == "__main__":
    main()
