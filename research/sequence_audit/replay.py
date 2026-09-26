"""Replay every SciPlex3 comparator arm under one set of sequence rules (Phase 2), and later the revision.

File summary
- Path: research/sequence_audit/replay.py
- Purpose: rerun the follow-up's comparison on the same episodes, folds, validator and evidence
  path, with every arm going through `policies.run_matched`: the same menu and time order, two
  measurements and 16 assay-days, the same QC-failure rule, the same stops and terminal utility.
- Core points:
  - Two QC rules are replayed: `continue` (primary: a failed assay is charged, updates nothing,
    and every arm chooses again) and `stop` (sensitivity: every arm stops after a QC failure).
  - The original follow-up records are never touched; this writes a separately labelled replay.
  - `--arms` restricts the run; the revised arm (`two_step_fallback`) is added only after the
    protocol that defines it is frozen (`protocol.json`), and its SciPlex3 result is exploratory.
  - Every record is audited for rule violations (`policies.audit_record`); any violation aborts.
- Run: python research/sequence_audit/replay.py [--arms a,b] [--label phase2]
- Depends on: policies.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import policies as P  # noqa: E402

C, E, V = P.C, P.E, P.V
OUT = P.ROOT / "outputs" / "sequence_audit_20260926"
PHASE2_ARMS = ("production", "magnitude", "da", "da_unconditioned", "fixed", "one_step_utility", "two_step",
               "two_step_permuted")
QC_RULES = ("continue", "stop")


def run_fold(task):
    tier_name, fold, arm_names = task
    data, protocol = C.load(), C.load_protocol()
    detected = C.detected_flags(data, C.detection_null(data, protocol))
    magnitude = E.Magnitude(data, detected)
    table = P.arms("sciplex3", frozen_replay=True)
    records = []
    for ctx, f in E.contexts(data, protocol, detected, magnitude, tier_names=(tier_name,), folds=(fold,)):
        setting = P.sciplex3_setting(ctx.tier)
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, f):
            for qc_rule in QC_RULES:
                for name in arm_names:
                    row = P.run_matched(name, table[name], ctx, compound, truth, h1, h2, setting, qc_rule=qc_rule)
                    problems = P.audit_record(row, setting)
                    if problems:
                        raise AssertionError(f"{name} {compound} {h1}/{h2}: {problems}")
                    records.append({"tier": tier_name, "fold": f, "decoy": decoy, **row})
    return records


def sources() -> dict:
    files = [HERE / "policies.py", Path(__file__), P.S.__file__, V.HERE / "evaluate.py", C.HERE / "common.py",
             C.HERE / "episodes.py", P.ROOT / "src" / "maestro" / "acquisition.py", P.ROOT / "src" / "maestro" / "outcome.py",
             P.ROOT / "src" / "maestro" / "selection.py"]
    return {str(Path(f).resolve().relative_to(P.ROOT)).replace("\\", "/"): hashlib.sha256(Path(f).read_bytes()).hexdigest()
            for f in files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", default=",".join(PHASE2_ARMS))
    parser.add_argument("--label", default="phase2_matched_replay")
    args = parser.parse_args()
    arm_names = tuple(args.arms.split(","))
    out = OUT / args.label
    out.mkdir(parents=True, exist_ok=True)
    tasks = [(tier, fold, arm_names) for tier in ("B", "A") for fold in range(5)]
    records = []
    with ProcessPoolExecutor(max_workers=5) as pool:
        for task, rows in zip(tasks, pool.map(run_fold, tasks)):
            records.extend(rows)
            print(f"{task[:2]}: {len(rows)} records", flush=True)
    (out / "episodes.jsonl").write_bytes("".join(json.dumps(C.clean(r)) + "\n" for r in records).encode("utf-8"))
    manifest = {"label": args.label, "arms": list(arm_names), "qc_rules": list(QC_RULES), "records": len(records),
                "status": "SciPlex3 episodes already analysed by blocks 2, 3 and the follow-up; exploratory",
                "rules": {"measurements": 2, "budget_days": 16.0, "order": "distinct actions, nondecreasing exposure time "
                          "including failed assays", "qc": "continue: failed assay charged, no evidence, arm asked again; "
                          "stop: every arm stops after a QC failure", "utility": {"correct": 1, "wrong": -2, "exhausted": -2,
                          "undetermined": 0, "deferred": 0}},
                "source_sha256": sources(),
                "data_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(C.PREPARED.iterdir()) if p.is_file()}}
    (out / "manifest.json").write_bytes(json.dumps(manifest, indent=1).encode("utf-8"))
    print(f"Wrote {len(records)} records to {out}", flush=True)


if __name__ == "__main__":
    main()
