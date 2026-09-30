"""Round-2 STATE interface re-check: seeds, row counts and group labels on the registered condition only.

File summary
- Path: research/identifiability_audit/state_recheck.py
- Purpose: repeat the Round-1 target-row sensitivity across independent seeds, sweep the target row
  count, and vary the target rows' batch/group label while the control rows and the target label stay
  fixed. The served shift of the registered condition is the only quantity discussed.
- Core points:
  - Expression perturbation is repeated under three seeds, and replacement by control values under
    three further seeds, so "invariant" is a statement about seeds and not about one draw.
  - Row count is swept (full, half, quarter, tenth) with two independent draws at the half size, so
    the draw-to-draw variation is separated from the size effect.
  - Group labels are changed three ways: to one existing plate, to an absent plate id, and by
    swapping plate labels between halves of the target rows.
  - Deleting every target row is recorded as `unsupported_query`, an interface refusal.
  - No action ranking in the frozen SciPlex3 B or L1000 LT tasks consumes a STATE prediction, so no
    action-ordering effect of these changes can be measured and none is claimed.
- Run: <state python> -m research.identifiability_audit.state_recheck [--out DIR]
- Interfaces: `build`, `main`
- Depends on: anndata, numpy; research/identifiability_audit/state_sensitivity.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "state_recheck"
SEEDS_EXPRESSION = (101, 202, 303)
SEEDS_REPLACEMENT = (111, 222, 333)
SEEDS_HALF = (401, 402)
FRACTIONS = (1.0, 0.5, 0.25, 0.1)


def build(out: Path, python: Path) -> dict:
    from research.identifiability_audit import state_sensitivity as S

    out.mkdir(parents=True, exist_ok=True)
    frame, matrix = S.load_asset()
    labels = frame[S.PERT_COLUMN].to_numpy()
    control = np.flatnonzero(labels == S.CONTROL)
    target = np.flatnonzero(labels == S.TARGET)

    def assemble(target_index, control_index, frame_values=None, matrix_values=None):
        order = np.concatenate([control_index, target_index])
        sub = frame.iloc[order].copy()
        mat = matrix[order].copy()
        if matrix_values is not None:
            mat[len(control_index):] = matrix_values
        if frame_values is not None:
            for column, value in frame_values.items():
                if callable(value):
                    sub.loc[sub.index[len(control_index):], column] = value(target_index)
                else:
                    sub.loc[sub.index[len(control_index):], column] = value
        return sub.reset_index(drop=True), mat

    plans: dict[str, tuple] = {}
    plans["baseline"] = assemble(target, control)
    for seed in SEEDS_EXPRESSION:
        rng = np.random.default_rng(seed)
        plans[f"expression_permuted_s{seed}"] = assemble(
            target, control, matrix_values=matrix[target[rng.permutation(len(target))]])
    for seed in SEEDS_REPLACEMENT:
        rng = np.random.default_rng(seed)
        plans[f"expression_replaced_s{seed}"] = assemble(
            target, control, matrix_values=matrix[control[rng.choice(len(control), len(target), replace=True)]])
    for fraction in FRACTIONS:
        if fraction == 1.0:
            continue
        seeds = SEEDS_HALF if fraction == 0.5 else (int(fraction * 1000),)
        for seed in seeds:
            rng = np.random.default_rng(seed)
            size = max(1, int(round(fraction * len(target))))
            kept = np.sort(rng.choice(target, size=size, replace=False))
            plans[f"rows_{int(fraction * 100)}pct_s{seed}"] = assemble(kept, control)
    existing = str(frame[S.BATCH_COLUMN].iloc[control[0]])
    plans["plate_single_existing"] = assemble(target, control, frame_values={S.BATCH_COLUMN: existing})
    plans["plate_absent_id"] = assemble(target, control, frame_values={S.BATCH_COLUMN: "plate99"})
    plans["plate_half_swap"] = assemble(
        target, control,
        frame_values={S.BATCH_COLUMN: lambda idx: np.where(
            np.arange(len(idx)) < len(idx) // 2, existing, "plate7")})

    records = {}
    for name, (sub, mat) in plans.items():
        path = out / "queries" / f"{name}.h5ad"
        digest = S.write_query(path, sub, mat)
        records[name] = S.run_arm(name, path, out, python)
        records[name]["query_sha256"] = digest
        print(name, "served" if records[name].get("served") else records[name].get("refusal"), flush=True)

    deletion = S.deletion_arm(out, python, frame, matrix)
    records["target_rows_deleted"] = deletion
    print("target_rows_deleted", deletion.get("refusal"), flush=True)

    base = np.array(records["baseline"]["vector"], dtype=float)
    norm = float(np.linalg.norm(base))
    arms = []
    for name, record in sorted(records.items()):
        if not record.get("served"):
            arms.append({"arm": name, "served": False, "refusal": record.get("refusal"),
                         "refusal_class": record.get("refusal_class"), "errors": record.get("errors", [])})
            continue
        vector = np.array(record["vector"], dtype=float)
        arms.append({"arm": name, "served": True, "delta_l2": float(np.linalg.norm(vector)),
                     "relative_l2_change": float(np.linalg.norm(vector - base)) / norm,
                     "cosine_to_baseline": float(vector @ base / (np.linalg.norm(vector) * norm)),
                     "max_abs_coordinate_change": float(np.abs(vector - base).max()),
                     "target_cells": record["perturbation_cells"],
                     "embedding_identical_to_baseline": bool(
                         record.get("vector_sha256") == records["baseline"].get("vector_sha256"))})
    report = {
        "context": S.CONTEXT, "control_label": S.CONTROL, "target_label": S.TARGET,
        "checkpoint": str(S.MODEL_DIR.relative_to(ROOT)).replace("\\", "/"), "seed": S.SEED,
        "python": str(python),
        "target_rows": int(len(target)), "control_rows": int(len(control)),
        "seeds": {"expression_permutation": list(SEEDS_EXPRESSION),
                  "expression_replacement": list(SEEDS_REPLACEMENT),
                  "half_draws": list(SEEDS_HALF)},
        "arms": arms,
        "action_ranking_effect": {
            "measured": False,
            "reason": "no registered STATE context exists for SciPlex3 B or L1000 LT, so no action "
                      "ranking in those tasks consumes a STATE prediction; only the served shift of "
                      "the registered condition is compared here"},
        "scope": "statements are about the registered context NCI-H596, the registered target label "
                 "and the registered checkpoint; they say nothing about untested compounds, times "
                 "or doses",
    }
    (out / "state_recheck.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


def main() -> None:
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    report = build(Path(args.out), Path(args.python))
    for arm in report["arms"]:
        print(json.dumps(arm))


if __name__ == "__main__":
    main()
