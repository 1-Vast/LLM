"""Post-run sensitivity and acquisition gaps; no new arm selection."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from research.astra.drylab_followup_20261007.tier_a import ARMS, GRID, HERE, ROOT, evaluate, load_replay, ridge_scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=HERE / "tier_a_run2")
    parser.add_argument("--output", type=Path, default=HERE / "diagnosis")
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    replay = load_replay()
    labels, _, menu = replay.load_data()
    labels["joint"] = labels.hit1 & labels.hit2
    features = pd.read_csv(args.run / "public_features.csv.gz")
    # TierA fixed-grid sensitivity: not a new selected policy or untouched result.
    records = []
    with threadpool_limits(limits=1):
        for cell in sorted(labels.SIDM.unique()):
            train = labels.index[labels.SIDM.ne(cell)].to_numpy()
            test = labels.index[labels.SIDM.eq(cell)].to_numpy()
            for lam in [100., 10., 1.]:
                delta = pd.Series(ridge_scores(train, test, features, ARMS["tier_a"], lam, labels), index=test)
                for role, g in labels.loc[test].groupby("role"):
                    base = evaluate(replay, g, g.prior_control_score.to_numpy())
                    for alpha in [.25, .5, 1.]:
                        res = evaluate(replay, g, g.prior_control_score.to_numpy() + alpha * delta.loc[g.index].to_numpy())
                        ins = set(res["screen_ids"]) - set(base["screen_ids"])
                        outs = set(base["screen_ids"]) - set(res["screen_ids"])
                        records.append(dict(SIDM=cell, role=role, alpha=alpha, ridge_lambda=lam,
                                            confirmations=res["confirmations"], extra=res["confirmations"] - base["confirmations"],
                                            swapped_in=len(ins), net_joint=int(g.iloc[list(ins)].joint.sum() - g.iloc[list(outs)].joint.sum()),
                                            max_abs_correction=float(np.abs(alpha * delta.loc[g.index]).max())))
    frame = pd.DataFrame(records)
    frame.to_csv(args.output / "fixed_grid_campaigns.csv", index=False)
    frame.groupby(["alpha", "ridge_lambda"])[["confirmations", "extra", "swapped_in", "net_joint"]].sum().to_csv(args.output / "fixed_grid_summary.csv")
    choices = pd.read_json(args.run / "fold_choices.json")
    # Gap table includes full menu and baseline decision boundary, never prioritizes by hidden joint outcomes.
    boundary = set()
    for _, g in menu.groupby(["SIDM", "role"]):
        local = g.reset_index()
        ordered = replay.ordering(local, local.prior_control_score)
        count = math.floor(.7 * math.ceil(.2 * len(g)))
        boundary.update(local.iloc[ordered[max(0, count-5):count+5]]["index"].tolist())
    features["near_static_boundary"] = features.index.isin(boundary)
    menu = menu.join(features[["eligible", "anchor_missing", "library_missing", "composite", "near_static_boundary"]])
    drug_rows = []
    for role in ["anchor", "library"]:
        idcol = "ANCHOR_ID" if role == "anchor" else "LIBRARY_ID"
        for drug, g in menu.groupby(idcol):
            missing = g[f"{role}_missing"].eq(1)
            drug_rows.append(dict(drug_id=drug, role=role, candidates=len(g),
                                  missing_support=int(missing.sum()), boundary_candidates=int(g.near_static_boundary.sum()),
                                  boundary_missing=int((missing & g.near_static_boundary).sum()),
                                  next_action="resolve_component_dose_vector" if "|" in drug else "retrieve_exact_dose_range_metadata_or_historical_curve",
                                  priority_basis="Public boundary proximity and support gap only; no target outcomes"))
    queue = pd.DataFrame(drug_rows).sort_values(["boundary_missing", "missing_support", "drug_id"], ascending=[False, False, True])
    queue.to_csv(args.output / "tier_a_acquisition_gaps.csv", index=False)
    report = {"status": "Post-run descriptive diagnosis; do not choose best grid point for deployment",
              "zero_correction_outer_choices": int(choices.alpha.eq(0).sum()), "total_outer_choices": len(choices),
              "boundary_rows": len(boundary), "boundary_eligible": int(features.loc[sorted(boundary), "eligible"].sum()),
              "missing_drug_role_entries": int(queue.missing_support.gt(0).sum()),
              "interpretation": "A selected zero correction tests this representation and inner selection opportunity, not a general no-information ceiling."}
    (args.output / "diagnostics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(frame.groupby(["alpha", "ridge_lambda"])[["confirmations", "extra", "swapped_in", "net_joint"]].sum().to_string())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
