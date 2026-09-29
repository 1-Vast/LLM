"""Build a public-input/hidden-outcome model benchmark from protocol-v2.1 tables.

The source tables contain the exact measured outcomes used by the existing replay.
This builder deliberately writes them into two files.  ``public_episodes`` contains
only the information available before an action is purchased; ``hidden_outcomes``
contains the joined truth used by an evaluator after the policy has selected actions.
The split is by the source fold, with fold 0 reserved as a fixed evaluation fold.

Usage::

    python -m tools.datasets.benchmark

No model is fitted here and no synthetic outcome is generated.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import io
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "outputs/protocol_v2_1_20260927/e_data1"
DEFAULT_OUT = ROOT / "data/processed/model_experiment_v1"
TASKS = ("sciplex3_A", "sciplex3_B", "l1000_LT", "l1000_T")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _write_jsonl(path: Path, rows: Iterable[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    # gzip.open defaults to the current timestamp, which would make an otherwise
    # byte-identical rebuild produce a different artifact hash.
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as handle:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                            default=_json_default) + "\n")
    return sha256_file(path)


def _episode_id(row: dict) -> str:
    parts = (row["dataset"], str(row["tier"]), str(row["fold"]), row["compound"], row["h1"], row["h2"])
    return "|".join(str(item) for item in parts)


def _task_name(row: dict) -> str:
    return f"{row['dataset']}_{row['tier']}"


def _menu(settings: dict, task: str, outcomes: dict) -> list[dict]:
    setting = settings[task]
    days = setting["days"]
    return [
        {"action": str(action), "key": list(outcomes[action]["key"]), "days": float(days[action])}
        for action in sorted(outcomes)
    ]


def _public(row: dict, settings: dict) -> dict:
    task = _task_name(row)
    menu = _menu(settings, task, row["outcomes"])
    return {
        "schema": "maestro.model_public_episode.v1",
        "episode_id": _episode_id(row),
        "dataset": row["dataset"],
        "tier": str(row["tier"]),
        "fold": int(row["fold"]),
        "split": "evaluation" if int(row["fold"]) == 0 else "development",
        "compound": row["compound"],
        "unit": str(row["unit"]),
        "scaffold": row.get("scaffold"),
        "max_train_tanimoto": row.get("max_train_tanimoto"),
        "hypotheses": [row["h1"], row["h2"]],
        "menu": menu,
        "max_measurements": int(settings[task]["max_measurements"]),
        "budget_days": float(settings[task]["budget_days"]),
        "source_visibility": "pre_action_metadata_only",
    }


def _hidden(row: dict) -> dict:
    outcomes = []
    for action in sorted(row["outcomes"]):
        value = row["outcomes"][action]
        outcomes.append({
            "action": action,
            "key": list(value["key"]),
            "lifecycle": value["lifecycle"],
            "readout": value["readout"],
            "outcome": value["outcome"],
        })
    return {
        "schema": "maestro.model_hidden_outcome.v1",
        "episode_id": _episode_id(row),
        "truth": row["truth"],
        "outcomes": outcomes,
        "source_visibility": "post_action_evaluator_only",
    }


def build(*, source_dir: Path = SOURCE_DIR, out_dir: Path = DEFAULT_OUT,
          tasks: tuple[str, ...] = TASKS) -> dict:
    manifest_path = source_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing protocol-v2.1 manifest: {manifest_path}")
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    settings = source_manifest["settings"]
    for task in tasks:
        if task not in settings:
            raise ValueError(f"task is absent from source manifest: {task}")

    rows = []
    source_files = []
    for task in tasks:
        paths = sorted((source_dir / "tables").glob(f"{task}_*.jsonl.gz"))
        if not paths:
            raise FileNotFoundError(f"no source table files for {task}")
        for path in paths:
            source_files.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                                 "sha256": sha256_file(path)})
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    if _task_name(row) != task:
                        raise ValueError(f"source task mismatch in {path}: {_task_name(row)} != {task}")
                    rows.append(row)

    rows.sort(key=lambda r: (_task_name(r), int(r["fold"]), str(r["compound"]), str(r["h1"]), str(r["h2"])))
    ids = [_episode_id(row) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate episode_id in source tables")

    public_rows = [_public(row, settings) for row in rows]
    hidden_rows = [_hidden(row) for row in rows]
    out_dir.mkdir(parents=True, exist_ok=True)
    public_path = out_dir / "public_episodes.jsonl.gz"
    hidden_path = out_dir / "hidden_outcomes.jsonl.gz"
    public_hash = _write_jsonl(public_path, public_rows)
    hidden_hash = _write_jsonl(hidden_path, hidden_rows)

    tasks_summary = {}
    for task in tasks:
        selected = [row for row in rows if _task_name(row) == task]
        tasks_summary[task] = {
            "episodes": len(selected),
            "action_records": sum(len(row["outcomes"]) for row in selected),
            "evaluation_fold": 0,
            "evaluation_episodes": sum(int(row["fold"]) == 0 for row in selected),
            "development_episodes": sum(int(row["fold"]) != 0 for row in selected),
            "actions_per_episode": len(settings[task]["keys"]),
            "max_measurements": int(settings[task]["max_measurements"]),
            "budget_days": float(settings[task]["budget_days"]),
        }
    manifest = {
        "schema": "maestro.model_experiment_manifest.v1",
        "purpose": "offline model/planner comparison with hidden measured outcomes",
        "source": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "manifest_sha256": sha256_file(manifest_path),
            "tables": source_files,
            "protocol": "external-validation-2.1",
        },
        "tasks": tasks_summary,
        "episodes": len(rows),
        "action_records": sum(len(row["outcomes"]) for row in rows),
        "public_input": {
            "path": "public_episodes.jsonl.gz",
            "sha256": public_hash,
            "forbidden_fields": ["truth", "outcomes", "readout", "lifecycle", "score"],
        },
        "hidden_outcomes": {
            "path": "hidden_outcomes.jsonl.gz",
            "sha256": hidden_hash,
            "join_key": "episode_id",
        },
        "split": {
            "rule": "source fold 0 is evaluation; folds 1-4 are development",
            "unit": "source unit field; do not treat cells, wells or episodes as independent replicates",
        },
        "claims": {
            "allowed": ["offline replay integrity", "model-input leakage checks", "development policy comparison"],
            "not_allowed": ["independent external validation", "wet-lab efficacy", "mechanism truth", "calibration for deployment"],
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    manifest = build(source_dir=args.source_dir, out_dir=args.out_dir)
    print(f"built {manifest['episodes']} episodes in {args.out_dir}")
    print(f"tasks: {', '.join(sorted(manifest['tasks']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
