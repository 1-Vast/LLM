"""Replay all archived decisive task models; never refit or reconstruct hidden outcomes.

The original package remains immutable. A documented checkpoint exception is a
failure, not a waiver. Old anchor models were not archived and cannot be replayed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parents[1] / "observation_acquisition" / "innovation_validation_20261020"
ARMS = ("inh_kg", "inh_pol", "rst_kg", "fix_kg")
CONTRACTS = ("E", "T", "FO")
KINDS = ("null", "lowrank", "alias", "compose")
REPLAY_CODE = ("iv_core.py", "iv_replay.py", "iv_worlds.py")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public_features(kind, seed):
    """Exactly the public RNG prefix of the frozen generator, ending before R.

    No World object, residuals, effect parameters, or outcome matrix is created.
    Dimensions are part of the original frozen synthetic design.
    """
    rng = np.random.default_rng(10_000 * seed + 17 * KINDS.index(kind) + 5)
    n_drugs, n_cells = 28, 32
    ii, jj = np.triu_indices(n_drugs, 1)
    module = np.repeat(np.arange(4), n_drugs // 4)[rng.permutation(n_drugs)]
    classes = {(a, b): k for k, (a, b) in enumerate((a, b) for a in range(4) for b in range(a, 4))}
    pc = np.array([classes[tuple(sorted((module[i], module[j])))] for i, j in zip(ii, jj)])
    level = rng.uniform(0.30, 0.50, n_drugs)
    mono = np.clip(level[:, None] + 0.05 * rng.standard_normal((n_drugs, n_cells)), 0.02, 0.95)
    ai, aj = mono[ii], mono[jj]
    mask = np.zeros(len(ii), dtype=bool)
    for cls in np.unique(pc):
        mask[np.flatnonzero(pc == cls)[::2]] = True
    features = {f"c{k:02d}": (1 - (1 - ai[:, k]) * (1 - aj[:, k]),
                              np.minimum(ai[:, k], aj[:, k]), np.maximum(ai[:, k], aj[:, k]))
                for k in range(n_cells)}
    return features, mask


def legacy_replay():
    """Load the original numerical belief update, never repair-package code."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(LEGACY))
    replay = importlib.import_module("iv_replay")
    for name in ("iv_replay", "iv_core"):
        module = sys.modules[name]
        if Path(module.__file__).resolve() != (LEGACY / f"{name}.py").resolve():
            raise RuntimeError(f"Refusing non-legacy replay module: {module.__file__}")
    return replay


def used_programs(row):
    return {p.split(":")[0] for p in row["programs"]}


def checkpoint_failures(sid, rows, records, exceptions):
    """Compare declared deployment with every recorded actual use; never waive."""
    failures = []
    for arm, generations in records.items():
        for gen in generations:
            checkpoint = gen["gen"]
            deployed = gen["deployed_at_checkpoint"]
            expected = set() if deployed is None else {deployed}
            affected = []
            for row in rows:
                if row["arm"] != arm:
                    continue
                is_anchor = row["role"] in ("A_old", "A_new") and row["gen"] == checkpoint
                is_next_task = row["role"] == "task" and row["gen"] == checkpoint + 1
                if (is_anchor or is_next_task) and used_programs(row) != expected:
                    affected.append({"cell": row["cell"], "role": row["role"], "contract": row["contract"],
                                     "gen": row["gen"], "actual_programs": sorted(used_programs(row))})
            if affected:
                declared = any(e.get("stream") == sid and e.get("arm") == arm and e.get("gen") == checkpoint
                               for e in exceptions)
                failures.append({"stream": sid, "arm": arm, "checkpoint": checkpoint,
                                 "declared_programs": sorted(expected), "affected_rows": affected,
                                 "listed_in_known_exceptions": declared, "exception_waived": False})
    return failures


def audit_package(source=LEGACY):
    source = Path(source).resolve()
    result = {"source": str(source), "status": "INCOMPLETE", "problems": [], "checkpoint_failures": [],
              "anchor_models": {"status": "NOT_REPLAYABLE", "rows_without_archived_checkpoint_model": 0,
                                "reason": "The legacy package saved pre-batch task models, not post-checkpoint anchor models."},
              "scope": "Stored nominations and deployment records only; no refit, API, utility re-estimation, or hidden outcomes.",
              "input_sha256": {}}
    problems = result["problems"]
    mandatory = [source / "CONFIG.json", source / "FREEZE.json"]
    missing = [str(p) for p in mandatory if not p.is_file()]
    if missing:
        problems.extend(f"Missing mandatory evidence: {p}" for p in missing)
        return result
    cfg = json.loads(mandatory[0].read_text(encoding="utf-8"))
    freeze = json.loads(mandatory[1].read_text(encoding="utf-8"))
    if freeze.get("config") != cfg:
        problems.append("Configuration differs from FREEZE.json")
    for name in REPLAY_CODE:
        actual = digest(LEGACY / name)
        result["input_sha256"][str(LEGACY / name)] = actual
        if freeze.get("files", {}).get(name) != actual:
            problems.append(f"Frozen replay code not authenticated: {name}")
    for path in mandatory:
        result["input_sha256"][str(path)] = digest(path)
    if problems:
        return result
    lo, hi = cfg["streams"]["eval_seeds"]
    expected_streams = {f"{kind}_{seed}" for kind in cfg["streams"]["kinds"] for seed in range(lo, hi + 1)}
    expected_streams |= {f"{kind}_{seed}_dec" for kind in cfg["streams"]["decoupled_kinds"] for seed in range(lo, hi + 1)}
    observed_streams = {p.name.removesuffix(".json.gz") for p in (source / "RUN/eval/streams").glob("*.json.gz")}
    if observed_streams != expected_streams:
        problems.append(f"Stream coverage mismatch: missing={sorted(expected_streams - observed_streams)}, unexpected={sorted(observed_streams - expected_streams)}")
    ex_path = source / "KNOWN_EXCEPTIONS.json"
    exceptions = json.loads(ex_path.read_text(encoding="utf-8")).get("exceptions", []) if ex_path.exists() else []
    if ex_path.exists():
        result["input_sha256"][str(ex_path)] = digest(ex_path)
    replay = legacy_replay()
    coverage = {"expected_streams": len(expected_streams), "observed_streams": len(observed_streams),
                "expected_task_rows": 0, "replayed_task_rows": 0, "matching_nominations": 0,
                "replayed_rows_with_gate": 0, "expected_strata": 0, "complete_strata": 0,
                "by_arm_generation_contract": {}}
    by_stratum = defaultdict(Counter)
    for sid in sorted(expected_streams & observed_streams):
        path = source / "RUN/eval/streams" / f"{sid}.json.gz"
        model_path = source / "RUN/eval/models" / f"{sid}.npz"
        result["input_sha256"][str(path)] = digest(path)
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            data = json.load(handle)
        rows = data["rows"]
        features, probe_mask = public_features(data["kind"], data["seed"])
        generated_sid = f"{data['kind']}_{data['seed']}{'_dec' if data['decoupled'] else ''}"
        if generated_sid != sid or data.get("sid") != sid:
            problems.append(f"{sid}: stream metadata identity mismatch")
        expected_batches = [[f"c{k:02d}" for k in range(8 + 4 * b, 12 + 4 * b)] for b in range(4)]
        if data["schedule"]["batches"] != expected_batches:
            problems.append(f"{sid}: task schedule differs from the frozen generator")
        expected_rows = Counter((arm, gen, contract, cell)
                                for gen, cells in enumerate(expected_batches, 1)
                                for arm in ARMS for contract in CONTRACTS for cell in cells)
        selected = [row for row in rows if row["role"] == "task" and row["arm"] in ARMS and row["contract"] in CONTRACTS]
        observed_rows = Counter((r["arm"], r["gen"], r["contract"], r["cell"]) for r in selected)
        if expected_rows != observed_rows:
            problems.append(f"{sid}: decisive row coverage mismatch, missing={list((expected_rows - observed_rows).items())[:5]}, extra={list((observed_rows - expected_rows).items())[:5]}")
        coverage["expected_task_rows"] += sum(expected_rows.values())
        expected_strata = Counter((a, g, c) for a, g, c, cell in expected_rows)
        coverage["expected_strata"] += len(expected_strata)
        stream_replayed = Counter()
        for stratum, nrows in expected_strata.items():
            by_stratum[stratum]["expected"] += nrows
        result["checkpoint_failures"].extend(checkpoint_failures(sid, rows, data["generation_records"], exceptions))
        result["anchor_models"]["rows_without_archived_checkpoint_model"] += sum(r["role"] in ("A_old", "A_new") for r in rows)
        if not model_path.is_file():
            problems.append(f"Missing archived task models: {model_path}")
            continue
        result["input_sha256"][str(model_path)] = digest(model_path)
        with np.load(model_path, allow_pickle=False) as models:
            for row in selected:
                arm, gen, contract = row["arm"], row["gen"], row["contract"]
                stratum = (arm, gen, contract)
                where = f"{sid}/{arm}/gen{gen}/{contract}/{row['cell']}"
                actual = used_programs(row)
                stored = {key.split("|")[2] for key in models.files
                          if key.startswith(f"{arm}|b{gen}|") and key.endswith("|meta")} - {"N", "U", "C"}
                if stored != actual:
                    problems.append(f"{where}: stored gate programs {sorted(stored)} differ from row {sorted(actual)}")
                if len(row["probes"]) != len(row["values"]):
                    problems.append(f"{where}: probe/value length mismatch")
                    continue
                if len(row["probes"]) != len(set(row["probes"])):
                    problems.append(f"{where}: duplicate probes")
                    continue
                pool = np.ones(len(probe_mask), dtype=bool) if contract == "E" else ~probe_mask
                if contract != "E" and any(not probe_mask[p] for p in row["probes"]):
                    problems.append(f"{where}: illegal transfer probe")
                    continue
                try:
                    aref, amin, amax = features[row["cell"]]
                    nom, _ = replay.replay_nomination(models, arm, gen, aref, amin, amax, row["probes"], row["values"], pool)
                except (KeyError, ValueError, IndexError) as error:
                    problems.append(f"{where}: stored-model replay failed: {error}")
                    continue
                coverage["replayed_task_rows"] += 1
                coverage["replayed_rows_with_gate"] += bool(actual)
                by_stratum[stratum]["replayed"] += 1
                stream_replayed[stratum] += 1
                if nom == row["nominated"]:
                    coverage["matching_nominations"] += 1
                    by_stratum[stratum]["matched"] += 1
                else:
                    problems.append(f"{where}: nomination mismatch: replay={nom}, stored={row['nominated']}")
        coverage["complete_strata"] += sum(stream_replayed[s] == n for s, n in expected_strata.items())
    coverage["by_arm_generation_contract"] = {f"{a}/gen{g}/{c}": dict(v) for (a, g, c), v in sorted(by_stratum.items())}
    result["coverage"] = coverage
    if result["checkpoint_failures"]:
        result["status"] = "INVALID_LEGACY_CHECKPOINT"
    elif problems:
        result["status"] = "INVALID_LEGACY_EVIDENCE"
    else:
        result["status"] = "TASK_REPLAY_OK_ANCHORS_NOT_REPLAYABLE"
    result["strict_pass"] = not problems and not result["checkpoint_failures"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=LEGACY)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.resolve().is_relative_to(args.source.resolve()):
        parser.error("Audit output must be outside the immutable source package")
    result = audit_package(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "coverage": result.get("coverage"),
                      "checkpoint_failures": len(result["checkpoint_failures"]),
                      "other_problems": len(result["problems"]), "out": str(args.out)}, indent=2))
    return 0 if result.get("strict_pass", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
