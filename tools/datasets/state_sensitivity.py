"""Paired real STATE forwards on real development control pools, not efficacy."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
import json

import anndata as ad
import h5py
import numpy as np
import pandas as pd

from virtual_cell.state_runner import _column
from tools.datasets.state_prospective_input import (
    CONTROL, CONTEXT, KEY, PERT, build_requests, digest, load_contract, predict, write_json,
)


def choose(scores, tolerance=1e-6):
    order = np.argsort(scores, kind="stable")
    return None if scores[order[1]] - scores[order[0]] <= tolerance else int(order[0])


def run(root, out):
    out.mkdir(parents=True, exist_ok=False)
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    contract = load_contract(root)
    write_json(out / "contract.json", contract)
    actions = [f"[('Trametinib', {dose}, 'uM')]" for dose in (0.05, 0.5, 5.0)]
    if any(a not in contract["mapping"] for a in actions):
        raise ValueError("exact action unavailable")
    endpoint = contract["axis"].index("0546:EGR1")
    seeds, count = [17, 42, 103], 16
    asset = Path(contract["hashes"]["dataset"]["path"])
    with h5py.File(asset) as handle:
        obs = pd.DataFrame({c: _column(handle["obs"], c) for c in [PERT, "plate", "cell_name"]})
        obs.index = _column(handle["obs"], handle["obs"].attrs["_index"])
        eligible = obs[(obs[PERT] == CONTROL) & (obs.cell_name == CONTEXT)]
        plates = sorted(p for p, group in eligible.groupby("plate") if len(group) >= 16)[:3]
        if len(plates) != 3:
            raise ValueError("three real matched-context pools required")
        pool_size = min(32, *(sum(eligible.plate == p) for p in plates))
        indices = {p: np.flatnonzero((obs.plate == p) & (obs[PERT] == CONTROL))[:pool_size] for p in plates}
        plan = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(), seeds=seeds, actions=actions,
                    queries_per_action=count, pool_size=int(pool_size), plates=plates,
                    source_rows_zero_based={p: rows.tolist() for p, rows in indices.items()},
                    baseline_selection="lexical first three plates with >=16 controls; first equal number of deposited rows",
                    endpoint="mean predicted log1p EGR1 coordinate 546; technical RNA surrogate, not survival",
                    selector="minimum endpoint; abstain if top-two gap <=1e-6",
                    state_permutation="cyclically replace whole baseline pools within NCI-H596, using already executed identical requests",
                    training_exposure="unknown; c39 is historical development material",
                    legality="controls collected at assay endpoint; no predecision or independent-culture claim",
                    matched_context="same cell line/assay; different plates are intentional technical pool replacements, not certified prospective matched controls",
                    prediction_improvement="not assessed without legal pre-treatment state-response pairs",
                    weights=contract["hashes"]["weights"], cost="unknown")
        write_json(out / "freeze.json", plan)
        baselines = {}
        for plate, rows in indices.items():
            frame = obs.iloc[rows].copy()
            frame["role"] = "baseline_control"
            baseline = ad.AnnData(obs=frame)
            baseline.obsm[KEY] = np.asarray(handle["obsm"][KEY][rows], dtype=np.float32)
            baseline.uns["state_feature_axis"] = np.asarray(contract["axis"])
            baseline.write_h5ad(out / f"baseline_{plate}.h5ad")
            baselines[plate] = baseline
    means, receipts, selection_rows = {}, [], []
    for plate in plates:
        for seed in seeds:
            key = f"{plate}_seed{seed}"
            query = build_requests(baselines[plate], actions, count, contract)
            path = out / f"{key}.h5ad"
            query.write_h5ad(path)
            receipt = predict(path, out / key, contract, actions, count, seed)
            receipts.append(dict(pool=plate, seed=seed, **receipt))
            if not receipt["valid"]:
                write_json(out / "partial_receipts.json", receipts)
                raise RuntimeError(f"forward failed: {key}")
            pred = np.load(out / key / "request_predictions.npy").reshape(len(actions), count, -1).mean(axis=1)
            means[plate, seed] = pred
            scores = pred[:, endpoint]
            selection_rows.append(dict(pool=plate, seed=seed, scores=scores.tolist(),
                                       selected=choose(scores), ranking=np.argsort(scores).tolist(),
                                       pairwise_action_contrasts=[float(scores[j] - scores[i]) for i, j in combinations(range(3), 2)]))
            print(key, "valid", flush=True)
    between, within, choices = [], [], {(r["pool"], r["seed"]): r["selected"] for r in selection_rows}
    for p, q in combinations(plates, 2):
        for seed in seeds:
            a, b = means[p, seed], means[q, seed]
            between.append(dict(pool_a=p, pool_b=q, seed=seed, rms=float(np.sqrt(np.mean((a-b)**2))),
                                max_abs=float(np.max(np.abs(a-b))), choice_changed=choices[p, seed] != choices[q, seed]))
    for p in plates:
        for s, t in combinations(seeds, 2):
            within.append(dict(pool=p, seed_a=s, seed_b=t,
                               rms=float(np.sqrt(np.mean((means[p,s]-means[p,t])**2))),
                               choice_changed=choices[p,s] != choices[p,t]))
    permutation = [{"question_pool": p, "replacement_pool": plates[(i+1)%3], "seed": s,
                    "original_choice": choices[p,s], "replacement_choice": choices[plates[(i+1)%3],s]}
                   for i,p in enumerate(plates) for s in seeds]
    pooled = {p: np.mean([means[p,s] for s in seeds], axis=0)[:,endpoint].tolist() for p in plates}
    summary = dict(scope="real development controls / STATE technical state sensitivity only",
                   successful_requests=len(receipts), actual_forwards=sum(r["forward_calls"] for r in receipts),
                   physical_attempts=0, selector_rows=selection_rows, seed_averaged_endpoint=pooled,
                   between_pool=between, within_pool_sampling=within, contextual_state_permutation=permutation,
                   mean_between_pool_rms=float(np.mean([r["rms"] for r in between])),
                   mean_within_pool_sampling_rms=float(np.mean([r["rms"] for r in within])),
                   between_pool_choice_changes=sum(r["choice_changed"] for r in between),
                   within_pool_choice_changes=sum(r["choice_changed"] for r in within),
                   globally_dominant_action=choices[plates[0],seeds[0]] if len(set(choices.values()))==1 else None,
                   biological_prediction_improvement="not_run", terminal_utility="not_identified",
                   deployment_value="not_identified", cost="unknown", receipts=receipts)
    write_json(out / "summary.json", summary)
    np.savez_compressed(out / "mean_predictions.npz", **{f"{p}_{s}": v for (p,s),v in means.items()})
    write_json(out / "manifest.json", {p.relative_to(out).as_posix():digest(p) for p in out.rglob("*") if p.is_file()})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root.resolve(), args.out.resolve())
    print(json.dumps({k:v for k,v in result.items() if k not in ["receipts","selector_rows","between_pool","within_pool_sampling","contextual_state_permutation"]}))
