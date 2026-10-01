"""Frozen, sequential paired STATE grid on historical development controls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from itertools import combinations
import json
from pathlib import Path

import numpy as np

from research.astra.paired_state import run_comparison
from research.astra import paired_state, state_interaction
from tools.datasets.state_prospective_input import digest, load_contract, write_json


def analyze(rows, actions, tolerance=1e-6):
    """Apply the original negative-EGR1 utility and tie rule without tuning."""
    utility = -np.asarray([r["endpoint_scores"] for r in rows], dtype=float)
    selected = state_interaction.choices(utility, tolerance)
    centered = state_interaction.action_center(utility)
    keys = [(r["pool"], r["seed"]) for r in rows]
    comparisons = []
    for i, j in combinations(range(len(rows)), 2):
        p, s = keys[i]
        q, t = keys[j]
        if s != t and p != q:
            continue
        comparisons.append({
            "first": keys[i], "second": keys[j],
            "kind": "between_pool_same_seed" if s == t else "within_pool_sampling",
            "relation": state_interaction.compare_choices(selected[i], selected[j], utility[i], utility[j], tolerance),
            "raw_utility_RMS": float(np.sqrt(np.mean((utility[i] - utility[j]) ** 2))),
            "action_centered_RMS": float(np.sqrt(np.mean((centered[i] - centered[j]) ** 2))),
        })
    averaged = {pool: utility[[i for i, key in enumerate(keys) if key[0] == pool]].mean(axis=0)
                for pool in sorted({p for p, _ in keys})}
    counts = {kind: {relation: sum(c["kind"] == kind and c["relation"] == relation for c in comparisons)
                     for relation in sorted({c["relation"] for c in comparisons})}
              for kind in ("between_pool_same_seed", "within_pool_sampling")}
    return dict(scope="historical endpoint-control technical state/plate replacement; not prospective biology",
                action_labels=actions, utility="negative mean predicted log1p EGR1", tolerance=tolerance,
                row_keys=keys, endpoint_scores=(-utility).tolist(), choices=selected,
                endpoint_exact_zeros=int((utility == 0).sum()), endpoint_values=int(utility.size),
                action_centered_utility=centered.tolist(),
                double_centered_utility=state_interaction.double_center(utility).tolist(),
                comparisons=comparisons, comparison_counts=counts,
                seed_averaged_endpoint_scores={p: (-v).tolist() for p, v in averaged.items()},
                seed_averaged_choices={p: state_interaction.choices(v[None, :], tolerance)[0]
                                       for p, v in averaged.items()},
                globally_weakly_best_actions=[a for a in range(len(actions))
                                             if np.all(utility[:, a] >= utility.max(axis=1) - tolerance)],
                actual_prediction_improvement="not_tested", action_utility="not_identified",
                physical_CI="not_reported", independent_cultures="unknown", cost="unknown")


def run(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    history = root / "tools/datasets/audit_results/20261001_state_response/sensitivity_v1"
    plates, seeds = ["plate1", "plate10", "plate11"], [17, 42, 103]
    actions = [str([("Trametinib", dose, "uM")]) for dose in (0.05, 0.5, 5.0)]
    reused = root / "research/astra/results/20261002_paired_state_v2"
    contract = load_contract(root)
    files = [history / f"baseline_{plate}.h5ad" for plate in plates]
    files += [Path(__file__), Path(paired_state.__file__), Path(state_interaction.__file__)]
    files += [reused / name for name in ("receipt.json", "freeze.json", "paired_trace.json",
                                       "request_predictions.npy", "execution_source.py.txt")]
    inputs = {str(path): digest(path) for path in files}
    freeze = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope="technical pairing correction; historical assay-endpoint control pools",
                  plates=plates, seeds=seeds, actions=actions, queries_per_action=16,
                  endpoint="mean predicted EGR1 coordinate 546", utility="negative endpoint",
                  tolerance=1e-6, model_assets=contract["hashes"], inputs=inputs,
                  reused_cell={"pool": "plate1", "seed": 42, "directory": str(reused)},
                  execution="sequential subprocesses; no concurrent model inference",
                  state_sampling="sample once with replacement per pool/seed, shared across all actions",
                  biological_prediction_improvement="not_tested", physical_attempts=0,
                  independent_cultures="unknown", cost="unknown")
    write_json(out / "freeze.json", freeze)
    for source in (Path(__file__), Path(paired_state.__file__), Path(state_interaction.__file__)):
        (out / (source.name + ".txt")).write_bytes(source.read_bytes())
    write_json(out / "pre_execution_manifest.json", {
        "frozen_inputs": inputs,
        "frozen_artifacts": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        "model_assets": contract["hashes"],
    })
    rows, means = [], {}
    for pool in plates:
        for seed in seeds:
            for path, expected in inputs.items():
                if digest(path) != expected:
                    raise ValueError(f"frozen matrix input changed: {path}")
            cell = reused if pool == "plate1" and seed == 42 else out / f"{pool}_seed{seed}"
            receipt = (json.loads((cell / "receipt.json").read_text(encoding="utf-8"))
                       if cell == reused else run_comparison(root, history / f"baseline_{pool}.h5ad",
                                                            cell, actions, 16, seed))
            if not receipt["valid"]:
                write_json(out / "partial_results.json", rows)
                raise RuntimeError(f"matrix forward failed: {pool} seed {seed}")
            trace = json.loads((cell / "paired_trace.json").read_text(encoding="utf-8"))
            if len({call["basal_sha256"] for call in trace["calls"] if call["paired"]}) != 1:
                raise ValueError("unpaired action tensors in grid")
            matrix = np.load(cell / "request_predictions.npy").reshape(3, 16, 2000)
            means[f"{pool}_{seed}"] = matrix.mean(axis=1)
            rows.append(dict(pool=pool, seed=seed, directory=str(cell),
                             receipt_sha256=digest(cell / "receipt.json"),
                             prediction_sha256=digest(cell / "request_predictions.npy"),
                             endpoint_scores=[receipt["endpoint_scores"][a] for a in actions],
                             trace=trace, reused=cell == reused))
            write_json(out / "partial_results.json", rows)
            print(f"completed {len(rows)}/9: {pool} seed {seed}; paired={True}; reused={cell == reused}", flush=True)
    report = analyze(rows, actions)
    report.update(rows=rows, successful_cells=9, newly_executed_requests=8,
                  newly_executed_forwards=32, referenced_grid_forwards=36,
                  physical_attempts=0, frozen_input_hashes=inputs)
    write_json(out / "summary.json", report)
    np.savez_compressed(out / "mean_predictions.npz", **means)
    write_json(out / "manifest.json", {p.relative_to(out).as_posix(): digest(p)
                                       for p in out.rglob("*") if p.is_file()})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.out)
