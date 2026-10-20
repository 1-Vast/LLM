"""Audit archived procedure execution without fitting, outcomes, or rescoring.

All task, anchor, and transplant rows are replayed from their saved artifacts and
logged observations. Public references are reconstructed without generating the
hidden response matrix. Behavior metadata is checked as well as action sequences.
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
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "procedure_inheritance_20261020"
ARMS = ("prior", "exploit", "f0_kg1", "f1_kg1", "f1_kg2", "f1_distill", "f0_plan", "f1_plan", "f1_plan_re", "f1_plan_nobranch")
EXIT_ARMS = ("f1_kg1", "f1_kg2", "f1_plan", "f1_distill")
FIELDS = ("queries", "nominated", "n_spent", "lib_fp", "exit_unknown", "unknown_step", "post_unknown",
          "plan_applicable", "plan_stop", "direct_fallback", "plan_id", "branch", "student_id")


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def legacy_modules():
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    modules = [importlib.import_module(name) for name in ("pi_model", "pi_plan", "pi_verify")]
    for module in modules:
        if Path(module.__file__).resolve().parent != SOURCE.resolve():
            raise RuntimeError(f"Refusing unexpected replay module {module.__file__}")
    return modules


def public_reference(seed, background):
    """The public RNG prefix only; never construct regimes, reads, or truth T."""
    rng = np.random.default_rng(seed)
    rng.permutation(66)
    base = rng.uniform(0.2, 0.6, 66)
    return base + np.random.default_rng([seed, 1000 + background]).normal(0, 0.04, 66)


def raw_plan_errors(plan):
    """Authenticate the actual input, including fields ignored by the old loader."""
    if plan is None:
        return []
    problems = []
    content, history = plan["content"], plan["history"]
    if object_sha(content) != plan["exec_sha"]:
        problems.append("raw content does not match exec_sha")
    if object_sha({"exec": plan["exec_sha"], "history": history}) != plan["pid"]:
        problems.append("raw history does not match pid")
    if content.get("schema") != "pi_plan_v1":
        problems.append("unsupported plan schema")
    if content.get("exits") != {"unknown_posterior_u": 0.5, "stop": -1, "inapplicable": "default_kg1"}:
        problems.append("serialized exits disagree with the executable contract")
    return problems


def coordinates(row):
    return row["arm"], row["role"], row["budget_arm"], row["bg"], row["ckpt"], row["batch"], row["contract"]


def expected_coordinates():
    expected = []
    for checkpoint in range(4):
        for arm in ARMS + ("f1_plan_xplant",):
            for budget in (3, 4):
                for background in range(8 + 4 * checkpoint, 12 + 4 * checkpoint):
                    expected.append((arm, "task", budget, background, checkpoint, checkpoint + 1, "E"))
        for arm in ARMS:
            if arm not in ("prior", "exploit"):
                for background in range(24 + 4 * checkpoint, 28 + 4 * checkpoint):
                    expected.append((arm, "anchor", 4, background, checkpoint, 0, "E"))
    return Counter(expected)


def coordinate_errors(rows, expected):
    actual = Counter(coordinates(row) for row in rows)
    missing, extra = expected - actual, actual - expected
    return {"missing": [{"coordinate": list(k), "count": n} for k, n in missing.items()],
            "extra_or_duplicate": [{"coordinate": list(k), "count": n} for k, n in extra.items()]}


def replay_row(model, library, agent, reference, budget, row):
    """Re-execute only logged reads. Unexpected reads fail; no outcome is supplied."""
    table = np.full(len(reference), np.nan)
    for pair, value in row["queries"]:
        table[pair] = value
    replayed = model.run_campaign(library, model.Camp(reference, table, T=None), budget, agent, arm=row["arm"])
    mismatches = []
    for field in FIELDS:
        if (field in row, row.get(field)) != (field in replayed, replayed.get(field)):
            mismatches.append({"field": field, "recorded_present": field in row, "replayed_present": field in replayed,
                               "recorded": row.get(field), "replayed": replayed.get(field)})
    return mismatches, replayed


class Archive(dict):
    @property
    def files(self):
        return list(self)


def audit(source=SOURCE):
    source = Path(source).resolve()
    result = {"status": "INCOMPLETE", "source": str(source), "problems": [], "mismatches": [],
              "scope": "Stored behavior only. No fit, hidden response generation, utility scoring, API, or new evaluation.",
              "sampling_unit": "(stream_id, background_id); arm/budget repeats are not independent backgrounds",
              "input_sha256": {}, "rows_replayed": 0, "raw_plans_checked": 0}
    problems = result["problems"]
    for name in ("CONFIG.json", "FREEZE.json"):
        if not (source / name).is_file():
            problems.append(f"Missing {name}")
    if problems:
        return result
    config = json.loads((source / "CONFIG.json").read_text(encoding="utf-8"))
    frozen = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    if frozen["config"] != config:
        problems.append("Configuration differs from frozen configuration")
    hashes = dict(frozen["files"])
    amendment_path = source / "FREEZE_AMENDMENT.json"
    if amendment_path.exists():
        amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
        if set(amendment["files"]) != {"pi_verify.py"}:
            problems.append("Unexpected amendment scope")
        for name, rec in amendment["files"].items():
            if hashes.get(name) != rec["pre_repair_sha256"]:
                problems.append(f"Invalid amendment predecessor for {name}")
            hashes[name] = rec["post_repair_sha256"]
    for name in ("pi_model.py", "pi_plan.py", "pi_verify.py", "pi_factors.py", "pi_world.py"):
        actual = file_sha(SOURCE / name)
        result["input_sha256"][str(SOURCE / name)] = actual
        if hashes.get(name) != actual:
            problems.append(f"Replay source does not match frozen hash: {name}")
    expected_sids = {f"{kind}_{seed}" for kind in config["streams"]["kinds"] for seed in config["streams"]["seeds"]}
    stream_dir = source / "RUN/eval/streams"
    available = {p.name.removesuffix(".json.gz") for p in stream_dir.glob("*.json.gz") if not p.name.endswith(".xplant.json.gz")}
    available_xp = {p.name.removesuffix(".xplant.json.gz") for p in stream_dir.glob("*.xplant.json.gz")}
    if available != expected_sids or available_xp != expected_sids:
        problems.append("Missing or extra stream/transplant evidence")
    if problems:
        return result
    streams, transplants = {}, {}
    for sid in sorted(expected_sids):
        for destination, suffix in ((streams, ".json.gz"), (transplants, ".xplant.json.gz")):
            path = stream_dir / f"{sid}{suffix}"
            result["input_sha256"][str(path)] = file_sha(path)
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                destination[sid] = json.load(handle)
    model, plan_module, verifier = legacy_modules()
    expected = expected_coordinates()
    unique = {name: set() for name in ("known", "novel", "known_exit", "novel_exit")}
    actor_sets = defaultdict(lambda: {name: set() for name in ("known", "novel", "known_exit", "novel_exit")})
    behavior = Counter()
    branches = defaultdict(Counter)
    result["expected_rows"] = len(expected_sids) * sum(expected.values())
    result["streams"] = len(expected_sids)
    with threadpool_limits(limits=1):
        for sid, stream in streams.items():
            checkpoint_set = [g["ckpt"] for g in stream["generations"]]
            if checkpoint_set != [0, 1, 2, 3]:
                problems.append(f"{sid}: checkpoint coverage mismatch")
            plan_keys = {f"{arm}|{checkpoint}|{budget}" for arm in ("f0_plan", "f1_plan", "f1_plan_re")
                         for checkpoint in range(4) for budget in (3, 4)}
            if set(stream["plans"]) != plan_keys:
                problems.append(f"{sid}: plan artifact coverage mismatch")
            for key, document in stream["plans"].items():
                raw_errors = raw_plan_errors(document)
                problems.extend(f"{sid}/{key}: {message}" for message in raw_errors)
                if document is not None:
                    result["raw_plans_checked"] += 1
                    if not raw_errors:
                        loaded = plan_module.Plan.from_json(document)
                        if loaded.content() != document["content"] or loaded.history() != document["history"]:
                            problems.append(f"{sid}/{key}: loaded artifact differs from serialized input")
            partner_sid = transplants[sid]["partner"]
            partner = streams.get(partner_sid)
            if partner is None or partner["kind"] != stream["kind"] or partner["seed"] == stream["seed"]:
                problems.append(f"{sid}: invalid transplant partner")
                continue
            model_path = source / "RUN/eval/models" / f"{sid}.npz"
            if not model_path.is_file():
                problems.append(f"{sid}: missing model artifact")
                continue
            result["input_sha256"][str(model_path)] = file_sha(model_path)
            with np.load(model_path, allow_pickle=False) as data:
                arrays = Archive({key: data[key] for key in data.files})
            rows = stream["rows"] + transplants[sid]["rows"]
            coverage = coordinate_errors(rows, expected)
            if coverage["missing"] or coverage["extra_or_duplicate"]:
                problems.append({"stream": sid, "coordinate_errors": coverage})
            for row in rows:
                where = {"stream": sid, "arm": row["arm"], "role": row["role"], "budget": row["budget_arm"],
                         "background": row["bg"], "checkpoint": row["ckpt"]}
                try:
                    library, agent, budget = verifier.agent_for(row["arm"], row["ckpt"], row["budget_arm"], arrays,
                                                              stream["plans"], partner["plans"], model, plan_module)
                    differences, replayed = replay_row(model, library, agent, public_reference(stream["seed"], row["bg"]), budget, row)
                except (KeyError, IndexError, ValueError, AssertionError) as error:
                    problems.append({**where, "replay_error": str(error)})
                    continue
                result["rows_replayed"] += 1
                if differences:
                    result["mismatches"].append({**where, "fields": differences})
                for field in ("exit_unknown", "plan_stop", "direct_fallback"):
                    behavior[field] += int(bool(replayed.get(field)))
                if row["role"] == "task" and row["arm"] in EXIT_ARMS:
                    background = (sid, row["bg"])
                    regime = stream["regimes"][str(row["bg"])]
                    if row["regime"] != regime:
                        problems.append({**where, "error": "row regime differs from archived background metadata"})
                    kind = "novel" if regime == 5 else "known"
                    unique[kind].add(background)
                    actor = actor_sets[f"{row['arm']}@{row['budget_arm']}"]
                    actor[kind].add(background)
                    if replayed["exit_unknown"]:
                        unique[kind + "_exit"].add(background)
                        actor[kind + "_exit"].add(background)
                if row["role"] == "task" and row["arm"] in ("f1_plan", "f1_plan_xplant"):
                    arm = row["arm"]
                    if "plan_applicable" in replayed:
                        behavior[f"{arm}_invocations_with_plan"] += 1
                        behavior[f"{arm}_applicable"] += int(replayed["plan_applicable"])
                        behavior[f"{arm}_inapplicable"] += int(not replayed["plan_applicable"])
                    if "branch" in replayed:
                        branches[f"{sid}/{arm}"][str(replayed["branch"])] += 1
    result["unique_backgrounds"] = {key: len(values) for key, values in unique.items()}
    result["unique_backgrounds_by_arm_budget"] = {actor: {key: len(values) for key, values in sets.items()}
                                                  for actor, sets in actor_sets.items()}
    result["behavior_invocation_counts_not_independent_samples"] = dict(behavior)
    result["branch_invocation_counts_not_independent_samples"] = {key: dict(value) for key, value in branches.items()}
    result["novelty_detection_evidence"] = "NO_SUCCESSFUL_DETECTION_ON_OBSERVED_NOVEL_BACKGROUNDS" if not unique["novel_exit"] else "DESCRIPTIVE_ONLY"
    result["transplant_content_coverage"] = "NOT_EXERCISED" if not behavior["f1_plan_xplant_applicable"] else "EXERCISED"
    result["status"] = "BEHAVIOR_REPLAY_OK" if not problems and not result["mismatches"] and result["rows_replayed"] == result["expected_rows"] else "BEHAVIOR_REPLAY_FAILED"
    result["innovation_effectiveness"] = "NOT_ESTABLISHED_BY_SOFTWARE_AUDIT"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.resolve().is_relative_to(args.source.resolve()):
        parser.error("Output must be outside the immutable original package")
    result = audit(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in ("status", "rows_replayed", "expected_rows", "raw_plans_checked", "unique_backgrounds", "transplant_content_coverage")}, indent=2))
    return 0 if result["status"] == "BEHAVIOR_REPLAY_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
