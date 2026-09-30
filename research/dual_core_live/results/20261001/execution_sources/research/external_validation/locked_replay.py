"""Locked replay: every registered arm, sealed from hidden outcomes, on identical episodes and rules.

File summary
- Path: research/external_validation/locked_replay.py
- Purpose: run the frozen ladder (`arms.py`) on each (dataset, tier, fold) through
  `sequence_audit.policies.run_matched`, write one record per episode and arm, the manifests, the
  fold-boundary checks and the evaluation-side prediction diagnostics.
- Core points:
  - Refuses to run unless `freeze.json` verifies (except `--smoke`, which prints integrity counts
    only, never an outcome rate). A dataset whose role is `external_test` additionally needs a
    registered manifest and an opened vault; none is registered, so that path refuses by name.
  - Arms get `firewall.seal(ctx)`; the executor runs on the real context and reveals only what an
    arm buys (registered reading to the runner, profile to `Visible`).
  - Each record carries the menus the arm was offered, so identical menus are checked, not assumed.
  - Prediction diagnostics (virtual cell, ridge and the training-target mean against the measured
    profile) are computed outside the policy path; they never reach an arm.
- Run: python -m research.external_validation.locked_replay [--smoke] [--workers N]
- Depends on: arms.py, firewall.py, research/sequence_audit (policies, lincs_prepare, lincs_evaluate)
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

import numpy as np
import pandas as pd

from . import arms as A
from . import firewall as F
from . import ontology as O

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs" / "external_validation_20260927"
P, C, E = A.P, A.C, A.E

import lincs_evaluate as LE  # noqa: E402  (on sys.path through arms -> sequence_audit)
import lincs_prepare as LP  # noqa: E402

TASKS = [(dataset, tier, fold) for dataset, tiers in (("sciplex3", ("A", "B")), ("l1000", ("LT", "T")))
         for tier in tiers for fold in range(5)]
UNIT = {"sciplex3": "skeleton", "l1000": "component"}
SENSITIVITY = {"sciplex3": ("compound", "murcko_scaffold", "plate_cohort"), "l1000": ("identity", "batch_cohort")}

# JSON itself does not define a representation for binary floating point values.  A replay
# generated on two BLAS/Python builds can therefore differ in the last bit even when every
# menu, action and outcome is the same (for example 0.31938088801938413 versus
# 0.3193808880193838).  This boundary is deliberately applied only when records are
# serialised; decisions continue to use the full precision values.  Fifteen decimal places
# retain substantially more precision than any registered gate and make the persisted replay
# independent of those last-bit differences.
REPLAY_FLOAT_DIGITS = 15


def canonical_replay_value(value):
    """Return a JSON-safe replay value with platform-stable diagnostic floats.

    The policy and executor still operate on their original ``float64`` values.  Canonicalising
    only the audit record prevents a formatting-level last-bit difference from being mistaken for
    a changed scientific result while preserving action, outcome and decision fields exactly.
    """
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            return None
        rounded = round(number, REPLAY_FLOAT_DIGITS)
        # Avoid persisting ``-0.0``: it is numerically equal but has a different JSON spelling.
        return 0.0 if rounded == 0.0 else rounded
    if isinstance(value, dict):
        return {key: canonical_replay_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_replay_value(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    return value


# ------------------------------------------------------------------------------ data
def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def l1000_smiles() -> dict:
    pert = pd.read_csv(LP.DATA / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str).fillna("")
    return {pid: (s if s and s != "-666" else None) for pid, s in zip(pert.pert_id, pert.canonical_smiles)}


def units(dataset: str) -> pd.DataFrame:
    """Independent unit and sensitivity clusters per compound (the block-4 definitions)."""
    if dataset == "sciplex3":
        analyze = _module(ROOT / "research/sequence_audit/analyze.py", "sequence_audit_analyze")
        frame = analyze.sciplex3_units().rename(columns={"scaffold": "murcko_scaffold"})
        frame["compound"] = frame.index
        return frame
    analyze = _module(ROOT / "research/sequence_audit/lincs_analyze.py", "sequence_audit_lincs_analyze")
    table = analyze.units()
    frame = pd.DataFrame({name: series for name, series in table.items()})
    frame["compound"] = frame.index
    compounds = pd.read_csv(LP.OUT / "compounds.csv").set_index("compound")
    frame["murcko_scaffold"] = compounds.scaffold.reindex(frame.index)
    return frame


def load(dataset: str, tier_name: str, fold: int):
    spec = C.load_protocol()
    if dataset == "l1000":
        data = LP.load()
        smiles = l1000_smiles()
        data.compounds["smiles"] = [smiles.get(c) for c in data.compounds.compound]
        tier = LP.tiers()[tier_name]
        detected = data.conditions.detected.to_numpy(bool)
        ctx = LE.context(data, tier, fold, detected, spec)
        setting = LP.setting(tier)
    else:
        data = C.load()
        detected = C.detected_flags(data, C.detection_null(data, spec))
        # External replay uses the label-independent tier builder.  The
        # historical ``contexts`` function remains available for development
        # replays, but it is not allowed to define the held-out menu here.
        ontology = O.load()
        ctx, _ = next(E.metadata_contexts(
            data, spec, detected, None, tier_names=(tier_name,), folds=(fold,),
            hypothesis_pools=ontology.pools,
        ))
        setting = P.sciplex3_setting(ctx.tier)
    return data, ctx, setting


def batches_of(data, dataset: str, compounds, keys) -> set:
    out = set()
    for key in keys:
        for compound, row in data.index.get(key, {}).items():
            if compound in compounds:
                r = data.conditions.iloc[row]
                if dataset == "l1000":
                    out.add(str(r.batch))
                else:
                    out.update(str(p) for p in (r.get("plate_rep1"), r.get("plate_rep2")) if isinstance(p, str))
    return out


# ------------------------------------------------------------------------------ integrity
def menu_problems(record: dict, offered: list, setting) -> list[str]:
    problems, executed = [], []
    for i, menu in enumerate(offered):
        remaining = setting.budget_days - sum(setting.days(tuple(s["key"])) for s in executed)
        expected = [C.action_id(k) for k in P.legal_menu(setting, executed, remaining)]
        if menu != expected:
            problems.append(f"menu_differs_at_step_{i}")
        if i < len(record["steps"]):
            executed.append(record["steps"][i])
    return problems


def wells(keys) -> int:
    """`episodes.lab_cost`'s well rule without its SciPlex3 day table: two wells per measurement,
    four shared vehicle wells for each new (line, time), counted once."""
    return 2 * len(keys) + 4 * len({(k[0], k[1]) for k in keys})


def executor(real_ctx, visible_of):
    def run(_ctx, compound, key, h1, h2):
        result = E.execute(real_ctx, compound, key, h1, h2)
        row = result.get("row")
        visible_of().reveal(key, real_ctx.data.shift[row] if result["qc"] and row is not None else None)
        return result
    return run


# ------------------------------------------------------------------------------ one task
def run_task(task, unit_frame: pd.DataFrame, *, limit: int | None = None) -> dict:
    from threadpoolctl import threadpool_limits
    dataset, tier_name, fold = task
    with threadpool_limits(limits=1):
        data, ctx, setting = load(dataset, tier_name, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        sealed = F.seal(ctx, heldout, vc_factory=lambda d, det: A.StructureVC(d, det))
        sealed.extra["structure_vc"] = sealed.magnitude
        episodes = E.episode_list(ctx, fold)[:limit] if limit else E.episode_list(ctx, fold)
        sealed.extra["vc_partner"] = A.vc_partners(sorted({e[0] for e in E.episode_list(ctx, fold)}), fold, tier_name)
        view_problems = F.sealed_view_problems(sealed, heldout)
        state = {"visible": None}
        run = executor(ctx, lambda: state["visible"])
        table = A.build(ctx, E.execute)
        records, problems = [], list(view_problems)
        for compound, truth, decoy, h1, h2 in episodes:
            for name, arm in table.items():
                state["visible"] = F.Visible()
                sealed.extra["visible"] = state["visible"]
                offered, clock = [], [0.0]

                def wrapped(c_, compound_, h1_, h2_, executed, menu, remaining, setting_, state_, arm=arm):
                    offered.append([C.action_id(k) for k in menu])
                    # Construct the typed policy boundary at every decision
                    # point.  The sealed context remains available to legacy
                    # arms for compatibility, while new arms can consume only
                    # this immutable public projection.
                    policy_actions = tuple(P.make_action(k, h1_, h2_, setting_) for k in menu)
                    sealed.extra["policy_input"] = F.project_policy_view(
                        sealed.extra["visible"], legal_actions=policy_actions,
                        budget=float(remaining),
                        provenance={"dataset": dataset, "tier": tier_name, "fold": str(fold)},
                    )
                    F.assert_policy_input(sealed.extra["policy_input"])
                    start = time.perf_counter()
                    try:
                        return arm(c_, compound_, h1_, h2_, executed, menu, remaining, setting_, state_)
                    finally:
                        clock[0] += time.perf_counter() - start

                row = P.run_matched(name, wrapped, sealed, compound, truth, h1, h2, setting, qc_rule="continue", execute=run)
                violations = P.audit_record(row, setting) + menu_problems(row, offered, setting)
                if name not in ("oracle",) and any((s.get("note") or {}).get("reads_hidden_outcomes") for s in row["steps"]):
                    violations.append("non_oracle_read_hidden_outcomes")
                if A.REGISTRY.get(name, {}).get("vc", "masked") == "masked" and \
                        any((s.get("note") or {}).get("used_vc") for s in row["steps"]):
                    violations.append("masked_arm_used_vc")
                problems += [f"{name}:{compound}:{v}" for v in violations]
                keys = [tuple(s["key"]) for s in row["steps"]]
                base, _, price = name.partition("@")
                spec = A.REGISTRY.get(base, {})
                row.update({"dataset": dataset, "tier": tier_name, "fold": fold, "decoy": decoy,
                            "arm": base, "price": float(price) if price else (A.PRICE if base in A.SWEEP or base in (
                                "marginal_only", "retrieval") else None),
                            "rung": spec.get("rung"), "control": bool(spec.get("control")),
                            "reads_hidden_outcomes": bool(spec.get("reads_hidden_outcomes")),
                            "offered": offered, "wells": wells(keys),
                            "compute_seconds": clock[0], "provider_usd": 0.0,
                            "used_vc": any((s.get("note") or {}).get("used_vc") for s in row["steps"]),
                            "candidates_remaining": sorted({h1, h2} - set(row["steps"][-1]["eliminated"] if row["steps"] else []))})
                for column in [UNIT[dataset], *SENSITIVITY[dataset]]:
                    row[f"cluster_{column}"] = str(unit_frame[column].get(compound, f"none:{compound}")) \
                        if column in unit_frame.columns else compound
                row["unit"] = row[f"cluster_{UNIT[dataset]}"]
                records.append(C.clean(row))

        # ---- evaluation-side diagnostics: never passed to an arm
        vc = sealed.extra["structure_vc"]
        ridge = A.ridge_predictor(sealed)
        diagnostics, features = [], []
        test_compounds = sorted({e[0] for e in episodes})
        for compound in test_compounds:
            features.append({"dataset": dataset, "tier": tier_name, "fold": fold, "compound": compound,
                             "max_train_tanimoto": vc.max_similarity(compound)})
            for key in setting.keys:
                r = data.index.get(key, {}).get(compound)
                if r is None or not C.qc_passed(data, r):
                    continue
                y = data.shift[r].astype(np.float64)
                mean = ctx.ft.tables[key].Y.mean(axis=0) if key in ctx.ft.tables and len(ctx.ft.tables[key].names) else None
                entry = {"dataset": dataset, "tier": tier_name, "fold": fold, "compound": compound,
                         "action": C.action_id(key), "detected": bool(ctx.detected[r]),
                         "measured_norm": float(np.linalg.norm(y))}
                for label, pred in (("vc", vc.profile(compound, key)), ("ridge", ridge.predict(compound, key)),
                                    ("train_mean", mean)):
                    if pred is None:
                        continue
                    pred = np.asarray(pred, dtype=np.float64)
                    entry[f"cos_{label}"] = float(pred @ y / max(np.linalg.norm(pred) * np.linalg.norm(y), 1e-12))
                    entry[f"norm_{label}"] = float(np.linalg.norm(pred))
                diagnostics.append(entry)

        train = {c for t in ctx.ft.tables.values() for c in t.names}
        boundary = F.boundary_report(
            {"compounds": train, "groups": {unit_frame[UNIT[dataset]].get(c) for c in train},
             "scaffolds": {unit_frame["murcko_scaffold"].get(c) for c in train},
             "batches": batches_of(data, dataset, train, setting.keys)},
            {"compounds": set(test_compounds), "groups": {unit_frame[UNIT[dataset]].get(c) for c in test_compounds},
             "scaffolds": {unit_frame["murcko_scaffold"].get(c) for c in test_compounds},
             "batches": batches_of(data, dataset, set(test_compounds), setting.keys)})
        problems += F.internal_boundary_problems(boundary)
        episode_manifest = {
            "manifest_version": "1", "dataset": dataset, "tier": tier_name, "fold": int(fold),
            "setting": {"menu": [C.action_id(k) for k in setting.keys], "budget_days": setting.budget_days,
                        "max_measurements": setting.max_measurements, "qc_rule": "continue",
                        "fixed_order": [C.action_id(k) for k in setting.fixed_order]},
            "episodes": [{"episode_id": f"{dataset}|{tier_name}|{fold}|{c}|{a}|{b}", "compound": c, "h1": a, "h2": b,
                          "unit": str(unit_frame[UNIT[dataset]].get(c, c))} for c, _, _, a, b in episodes]}
        calibration = {k: v for k, v in ctx.params.items() if k != "grid"}
        return {"task": task, "records": records, "diagnostics": diagnostics, "features": features,
                "boundary": boundary, "problems": problems, "episode_manifest": episode_manifest,
                "validator": C.clean(calibration), "episodes": len(episodes)}


# ------------------------------------------------------------------------------ driver
def verify_freeze() -> dict:
    freeze = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    problems = F.verify_freeze(freeze)
    if problems:
        raise F.FreezeMismatch("; ".join(problems))
    return freeze


def write_jsonl_gz(path: Path, rows) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(canonical_replay_value(row), allow_nan=False, sort_keys=True) + "\n")


def smoke() -> None:
    """Integrity only: counts of records and violations, never an outcome rate."""
    for task in (("sciplex3", "A", 0), ("l1000", "T", 0)):
        result = run_task(task, units(task[0]), limit=3)
        print(json.dumps({"task": task, "records": len(result["records"]), "problems": len(result["problems"]),
                          "problem_examples": result["problems"][:5],
                          "arms": sorted({r["policy"] for r in result["records"]})}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--role", default="development", choices=("development", "external_test"))
    args = parser.parse_args()
    if args.role == "external_test":
        raise F.ExternalStudyUnavailable("external_study_not_registered: see manifests/external_candidates.json")
    if args.smoke:
        smoke()
        return
    freeze = verify_freeze()
    out = OUT / "replay"
    out.mkdir(parents=True, exist_ok=True)
    frames = {name: units(name) for name in ("sciplex3", "l1000")}
    started = datetime.now(timezone.utc).isoformat()
    summary = {"files": {}, "problems": {}, "boundary": {}, "validator": {}, "episodes": {}}
    diagnostics, features, manifests = [], [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(run_task, task, frames[task[0]]): task for task in TASKS}
        for job in as_completed(jobs):
            result = job.result()
            dataset, tier, fold = result["task"]
            name = f"{dataset}_{tier}_{fold}"
            write_jsonl_gz(out / f"{name}.jsonl.gz", result["records"])
            summary["files"][name] = len(result["records"])
            summary["episodes"][name] = result["episodes"]
            summary["problems"][name] = result["problems"]
            summary["boundary"][name] = result["boundary"]
            summary["validator"][name] = result["validator"]
            diagnostics += result["diagnostics"]
            features += result["features"]
            manifests.append(result["episode_manifest"])
            print(f"{name}: {len(result['records'])} records, {len(result['problems'])} problems", flush=True)
    pd.DataFrame(diagnostics).to_csv(OUT / "prediction_diagnostics.csv", index=False, lineterminator="\n")
    pd.DataFrame(features).to_csv(OUT / "compound_features.csv", index=False, lineterminator="\n")
    manifest_dir = OUT / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for manifest in manifests:
        F.check_manifest(manifest, "episode_manifest")
        path = manifest_dir / f"episodes_{manifest['dataset']}_{manifest['tier']}_{manifest['fold']}.json"
        path.write_bytes(json.dumps(manifest, indent=1).encode("utf-8"))
    summary.update({"freeze": freeze, "started_at_utc": started, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "internal replay on development data; not external validation",
                    "records": sum(summary["files"].values()), "arms": A.executed_arms(), "not_executed": {n: s["reason"] for n, s in A.REGISTRY.items()
                                                             if s.get("status") == "registered_not_executed"},
                    "environment": {"python": sys.version, "executable": sys.executable, "workers": args.workers}})
    (OUT / "replay_manifest.json").write_bytes(json.dumps(C.clean(summary), indent=1).encode("utf-8"))
    total = sum(len(v) for v in summary["problems"].values())
    print(f"Saved {summary['records']} records; integrity problems: {total}", flush=True)


if __name__ == "__main__":
    main()
