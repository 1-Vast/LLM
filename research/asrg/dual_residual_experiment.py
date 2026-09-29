"""Offline E0-DIR falsification experiment on the registered SciPlex holdout.

The prediction arrays are public to the router; ``observed`` is evaluator-private
and is only used after a branch has selected a final candidate.  This is a
decision-routing test, not a chemCPA or functional-mechanism claim.
"""
from __future__ import annotations

import argparse, json, os
from pathlib import Path
import numpy as np


def loss(y: np.ndarray, g: np.ndarray) -> float:
    return float(np.mean((y - g) ** 2) / (np.mean(g ** 2) + 1e-8))


def run(root: Path, *, api_tasks: int = 0) -> dict:
    base = root / "log/20260915/model_validation/training_v1"
    z = np.load(base / "heldout_predictions.npz", allow_pickle=False)
    observed = z["observed"].astype("float64")
    actual = z["multimodal_neural"].astype("float64")
    ideal = z["chemistry_context_neural"].astype("float64")
    n = len(observed)
    # Deterministic anonymised tasks.  Each task's target is public to the router
    # only through g; its observed response is held back until scoring.
    tasks = []
    for i in range(0, n, 11):
        pool = np.array([j for j in range(n) if j != i], dtype=int)
        # Menus are fixed from predictions only: four realization and four
        # hypothesis candidates, with no observed values used in construction.
        dr = np.sum((actual[pool] - actual[i]) ** 2, axis=1)
        dh = np.sum((ideal[pool] - ideal[i]) ** 2, axis=1)
        real = pool[np.argsort(dr)[:4]]
        remaining = pool[~np.isin(pool, real)]
        hyp = remaining[np.argsort(np.sum((ideal[remaining] - ideal[i]) ** 2, axis=1))[:4]]
        # A fixed nonzero target is registered before routing. It is a model
        # target, not a held-out response.
        g = np.mean(actual, axis=0)
        rg = g - ideal[i]
        rr = ideal[i] - actual[i]
        # Equal-information baseline chooses the candidate with the lower
        # predicted distance to g, while DIR uses the larger residual branch.
        branch_a = "repair_realization" if np.linalg.norm(rr) >= np.linalg.norm(rg) else "repair_hypothesis"
        scored = []
        for branch, menu in (("repair_realization", real), ("repair_hypothesis", hyp)):
            pred = actual[menu] if branch == "repair_realization" else ideal[menu]
            k = int(menu[np.argmin(np.sum((pred - (rg + ideal[i])) ** 2, axis=1))])
            scored.append((branch, k))
        branch_b, chosen_b = min(scored, key=lambda x: loss(actual[x[1]], g))
        chosen_a = dict(scored)[branch_a]
        tasks.append({"task": f"T_{i:04d}", "target_index": i,
                      "branch_a": branch_a, "a": chosen_a,
                      "branch_b": branch_b, "b": chosen_b,
                      "real_menu": real.tolist(), "hyp_menu": hyp.tolist(),
                      "goal_residual_norm": float(np.linalg.norm(rg)),
                      "realization_residual_norm": float(np.linalg.norm(rr))})
    rows = []
    for t in tasks:
        g = np.mean(actual, axis=0)
        la, lb = loss(observed[t["a"]], g), loss(observed[t["b"]], g)
        rows.append({"task": t["task"], "loss_dir": la, "loss_baseline": lb,
                     "gain_baseline_minus_dir": lb - la, "branch_dir": t["branch_a"],
                     "branch_baseline": t["branch_b"]})
    gains = np.array([r["gain_baseline_minus_dir"] for r in rows])
    report = {"protocol": "E0-DIR-v1-local-holdout", "tasks": len(rows),
              "prediction_source": str(base), "observed_used_only_for_scoring": True,
              "delta_mean": float(gains.mean()),
              "delta_min": 0.05,
              "dir_better_fraction": float(np.mean(gains > 0)),
              "ci95_task_bootstrap": np.quantile(
                  np.random.default_rng(20260924).choice(gains, (5000, len(gains)), replace=True).mean(1), [0.025, 0.975]).tolist(),
              "rows": rows,
              "api": {"requested": api_tasks, "performed": 0, "status": "optional_router_not_used_in_primary"}}
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(run(args.workspace), indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
