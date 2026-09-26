"""Run the frozen independent L1000 decision evaluation (Phase 4).

File summary
- Path: research/sequence_audit/lincs_evaluate.py
- Purpose: on the prepared L1000 data, build each fold's validator with the SciPlex3 rules and
  calibration grid, check the feasibility gate, then run every registered arm through the matched
  runner on the same held-out episodes, and audit the step-1 forecasts against what each
  measurement actually read.
- Core points:
  - Nothing here is tuned. The validator, calibration grid, episode construction, arms, runner and
    utilities are the SciPlex3 ones; only the menu, the assay days and the data differ.
  - The gate (at least three of five folds whose calibrated validator can eliminate) is checked
    per tier before any arm runs; a tier that fails runs no arm.
  - The plate diagnostic records, for every eliminating step-1 reading, whether the nearest
    template of the winning class came from the same batch as the held-out measurement, against
    the share of that class's templates from that batch.
  - Refuses to run unless `PROTOCOL.md` and `protocol.json` match the hashes in `freeze.json`.
- Run: python research/sequence_audit/lincs_evaluate.py
- Depends on: lincs_prepare.py, policies.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lincs_prepare as LP  # noqa: E402
import policies as P  # noqa: E402

C, E, V = P.C, P.E, P.V
OUT = P.ROOT / "outputs" / "sequence_audit_20260926" / "l1000"
ARMS = ("production", "da", "da_unconditioned", "fixed", "one_step_utility", "two_step", "two_step_permuted",
        "two_step_fallback")
GATE_FOLDS = 3


def frozen() -> dict:
    freeze = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    for name in ("PROTOCOL.md", "protocol.json"):
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != freeze["sha256"][name]:
            raise SystemExit(f"{name} differs from the frozen version")
    return freeze


def context(data, tier, fold, detected, spec):
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    ft = C.build_fold_tables(data, tier, fold, detected)
    params = C.calibrate(ft, spec)
    rng = np.random.default_rng([C.SEED, int(fold), E.stable(tier.name)])
    train = [c for c in comp.index if comp.fold[c] != fold and comp.klass.get(c) in tier.pool]
    permuted = dict(zip(train, rng.permutation([comp.klass[c] for c in train])))
    ft_perm = C.build_fold_tables(data, tier, fold, detected, label_map=permuted)
    return E.FoldContext(data, tier, ft, ft_perm, params, detected, None, {}, {})


def nearest_template_batch(ctx, key, compound, klass) -> dict:
    """Whether the winning class's nearest template shares the held-out measurement's batch."""
    t = ctx.ft.tables[key]
    row = ctx.data.index[key][compound]
    y = ctx.data.shift[row].astype(np.float64)
    gy, dy, d = t.Y @ y, float(y @ t.S), t.s
    perp = np.sqrt(np.maximum(np.diag(t.G) - d * d / t.total, 1e-12))
    perp_y = math.sqrt(max(float(y @ y) - dy * dy / t.total, 1e-12))
    score = (gy - dy * d / t.total) / (perp_y * perp)
    members = np.flatnonzero((t.klass == klass) & t.detected)
    batch = ctx.data.conditions.batch
    own = batch[row]
    template_batches = [batch[ctx.data.index[key][t.names[j]]] for j in members]
    nearest = template_batches[int(np.argmax(score[members]))]
    return {"nearest_same_batch": nearest == own, "template_same_batch_share": float(np.mean([b == own for b in template_batches]))}


def menu_audit(ctx, compound, truth, h1, h2) -> list[dict]:
    forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1)
    labels = sorted(P.outcome_consequences(V.registered_rules(h1, h2)))
    rows = []
    for key in ctx.tier.keys:
        forecast = forecaster.forecast_key(key, h1, h2)
        result = E.execute(ctx, compound, key, h1, h2)
        outcome = result["outcome"]
        realised = {"quality_failed": "qc_failed", "undetected": "neutral", "ambiguous": "neutral"}.get(outcome)
        plate = {}
        if realised is None:
            eliminated = h2 if outcome == "eliminate_b" else h1
            realised = "wrong" if eliminated == truth else "correct"
            plate = nearest_template_batch(ctx, key, compound, h1 if outcome == "eliminate_b" else h2)
        p_truth = support = None
        branch = forecast.branch_for(truth)
        if branch is not None and forecast.refusal is None:
            alpha = {label: branch.probabilities.get(label, 0.0) * branch.support + 0.5 for label in labels}
            p_truth = alpha[V.MATCH[truth == h1]] / sum(alpha.values())
            support = min(b.support for b in forecast.branches)
        rows.append({"tier": ctx.tier.name, "fold": ctx.ft.fold, "compound": compound, "truth": truth, "h1": h1, "h2": h2,
                     "action": C.action_id(key), "line": key[0], "time": key[1], "served": forecast.refusal is None,
                     "refusal": forecast.refusal, "p_correct_truth_branch": p_truth, "support": support,
                     "realised": realised, **plate})
    return rows


def run_fold(task):
    tier_name, fold = task
    data = LP.load()
    tier = LP.tiers()[tier_name]
    setting = LP.setting(tier)
    detected = data.conditions.detected.to_numpy(bool)
    ctx = context(data, tier, fold, detected, C.load_protocol())
    table = P.arms("l1000", frozen_replay=True)
    fixed_first = setting.fixed_order[0]
    records, audit = [], []
    first_table = ctx.ft.tables[fixed_first]
    for compound, truth, decoy, h1, h2 in E.episode_list(ctx, fold):
        support = min(int(np.sum(first_table.klass == h)) for h in (h1, h2))
        for name in ARMS:
            row = P.run_matched(name, table[name], ctx, compound, truth, h1, h2, setting, qc_rule="continue")
            problems = P.audit_record(row, setting)
            if problems:
                raise AssertionError(f"{name} {compound} {h1}/{h2}: {problems}")
            records.append({"tier": tier_name, "fold": fold, "decoy": decoy, "contrast_support": support, **row})
        audit.extend(menu_audit(ctx, compound, truth, h1, h2))
    calibration = {k: v for k, v in ctx.params.items() if k != "grid"}
    return tier_name, fold, records, audit, calibration


def gate(tier_name) -> dict:
    data = LP.load()
    tier = LP.tiers()[tier_name]
    detected = data.conditions.detected.to_numpy(bool)
    spec = C.load_protocol()
    folds = {}
    for fold in range(LP.FOLDS):
        ft = C.build_fold_tables(data, tier, fold, detected)
        params = C.calibrate(ft, spec)
        folds[fold] = {k: v for k, v in params.items() if k != "grid"}
    passed = sum(bool(v["eliminates"]) for v in folds.values()) >= GATE_FOLDS
    return {"tier": tier_name, "folds": folds, "passed": passed}


def sources() -> dict:
    files = [HERE / "policies.py", HERE / "lincs_prepare.py", Path(__file__), HERE / "PROTOCOL.md", HERE / "protocol.json",
             Path(P.S.__file__), V.HERE / "evaluate.py", C.HERE / "common.py", C.HERE / "episodes.py",
             P.ROOT / "src/maestro/acquisition.py", P.ROOT / "src/maestro/outcome.py", P.ROOT / "src/maestro/selection.py"]
    return {str(Path(f).resolve().relative_to(P.ROOT)).replace("\\", "/"): hashlib.sha256(Path(f).read_bytes()).hexdigest()
            for f in files}


def main() -> None:
    freeze = frozen()
    gates = {name: gate(name) for name in ("LT", "T")}
    (OUT / "gate.json").write_bytes(json.dumps(gates, indent=1, default=str).encode("utf-8"))
    print(json.dumps({k: {"passed": v["passed"], "eliminating_folds": sum(bool(f["eliminates"]) for f in v["folds"].values())}
                      for k, v in gates.items()}), flush=True)
    tasks = [(name, fold) for name in ("LT", "T") if gates[name]["passed"] for fold in range(LP.FOLDS)]
    records, audit, calibration = [], [], {}
    with ProcessPoolExecutor(max_workers=5) as pool:
        for tier_name, fold, rows, menu, params in pool.map(run_fold, tasks):
            records.extend(rows)
            audit.extend(menu)
            calibration[f"{tier_name}|{fold}"] = params
            print(f"{tier_name} fold {fold}: {len(rows)} records", flush=True)
    (OUT / "episodes").mkdir(parents=True, exist_ok=True)
    (OUT / "episodes" / "episodes.jsonl").write_bytes("".join(json.dumps(C.clean(r)) + "\n" for r in records).encode("utf-8"))
    (OUT / "episodes" / "menu_audit.jsonl").write_bytes("".join(json.dumps(C.clean(r)) + "\n" for r in audit).encode("utf-8"))
    manifest = {"freeze": freeze, "gates": {k: v["passed"] for k, v in gates.items()}, "calibration": calibration,
                "records": len(records), "menu_rows": len(audit), "arms": list(ARMS), "source_sha256": sources(),
                "prepared_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(LP.OUT.iterdir()) if p.is_file()}}
    (OUT / "episodes" / "manifest.json").write_bytes(json.dumps(manifest, indent=1, default=str).encode("utf-8"))
    print(f"Wrote {len(records)} records and {len(audit)} menu rows", flush=True)


if __name__ == "__main__":
    main()
