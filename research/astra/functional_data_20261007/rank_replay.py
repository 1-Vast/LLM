"""Qualified raw reference into the existing paid replay, no new executor."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from research.astra.functional_data_20261007.acquire import HERE
from research.astra.drylab_followup_20261007.tier_a import evaluate, ridge_scores, select, load_replay

COLS = ["exact_anchor_low_viability", "exact_anchor_high_viability", "exact_library_top_viability"]


def main():
    out = HERE / "ranking_results"
    out.mkdir(exist_ok=False)
    replay = load_replay()
    labels, _, menu = replay.load_data()
    features = pd.read_csv(HERE / "data_run3/candidate_features.csv.gz")
    assert len(features) == len(menu)
    features["eligible"] = features.exact_eligible
    labels["joint"] = labels.hit1 & labels.hit2
    # Fixed condition-matched mapping destruction, before nested selection.
    shuffled = features.copy()
    rng = np.random.default_rng(20261007)
    keys = menu[["Tissue", "LIBRARY_CONC", "anchor_set"]].copy()
    keys["eligible"] = features.eligible
    changed = 0
    for _, ids in keys.groupby(list(keys.columns)).groups.items():
        ids = np.asarray(list(ids))
        if len(ids) > 1 and bool(features.loc[ids[0], "eligible"]):
            source = rng.permutation(ids)
            shuffled.loc[ids, COLS] = features.loc[source, COLS].to_numpy()
            changed += int((~np.isclose(features.loc[ids, COLS], shuffled.loc[ids, COLS], equal_nan=True).all(axis=1)).sum())
    records, choices, swaps, traces = [], [], [], []
    with threadpool_limits(limits=1):
        for cell in sorted(menu.SIDM.unique()):
            train = labels.index[labels.SIDM.ne(cell)].to_numpy()
            test = labels.index[labels.SIDM.eq(cell)].to_numpy()
            base = labels.loc[test, "prior_control_score"].to_numpy()
            scores = {"frozen_static": pd.Series(base, index=test)}
            for name, F in [("raw_reference", features), ("raw_shuffled", shuffled)]:
                (alpha, lam), quality, history = select(replay, train, labels, F, COLS)
                assert cell not in history
                scores[name] = pd.Series(base + alpha * ridge_scores(train, test, F, COLS, lam, labels), index=test)
                choices.append(dict(SIDM=cell, arm=name, alpha=alpha, ridge_lambda=lam, training_cells=history, inner_confirmations=quality))
            for role, g in labels.loc[test].groupby("role"):
                results = {name: evaluate(replay, g, s.loc[g.index].to_numpy()) for name, s in scores.items()}
                baseline = set(results["frozen_static"]["screen_ids"])
                for name, res in results.items():
                    records.append(dict(SIDM=cell, role=role, arm=name, **{k: v for k, v in res.items() if k not in ["screen_ids", "confirmed_ids", "trace"]}))
                    traces.extend(dict(SIDM=cell, role=role, arm=name, **z) for z in res["trace"])
                    for direction, ids in [("in", set(res["screen_ids"]) - baseline), ("out", baseline - set(res["screen_ids"]))]:
                        for i in sorted(ids):
                            row = g.iloc[i]
                            swaps.append(dict(SIDM=cell, role=role, arm=name, direction=direction,
                                              **{k: row[k] for k in replay.KEY if k != "SIDM"}, pair=row.pair,
                                              joint_contribution=int(row.joint) * (1 if direction == "in" else -1)))
    frame = pd.DataFrame(records)
    frame.to_csv(out / "campaigns.csv", index=False)
    summary = frame.groupby("arm")[["confirmations", "spent", "budget", "unused"]].sum()
    summary.to_csv(out / "summary.csv")
    pd.DataFrame(choices).to_json(out / "fold_choices.json", orient="records", indent=2)
    pd.DataFrame(swaps).to_csv(out / "boundary_swaps.csv", index=False)
    with (out / "purchase_traces.jsonl").open("w", encoding="utf-8") as stream:
        for z in traces:
            stream.write(json.dumps(z, allow_nan=False) + "\n")
    assert summary.loc["frozen_static", "confirmations"] == 92
    assert summary.loc["frozen_static", "spent"] == 762
    (out / "claim_boundary.json").write_text(json.dumps({"status": "Exploratory sparse raw-reference ranking; no agent gain or deployment",
        "correction_grid": "Prior frozen drylab protocol unchanged", "swaps": len(swaps),
        "actually_changed_shuffle_rows": changed, "features": COLS,
        "source": "Historical111cell raw mono measurements; no target mono state used",
        "zero_correction_choices": sum(z["alpha"] == 0 for z in choices)}, indent=2) + "\n")
    print(summary.to_string())


if __name__ == "__main__":
    main()
