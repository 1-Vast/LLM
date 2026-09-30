"""Run the case-quality audit and the replay-integrity check over every artefact the pipeline wrote.

File summary
- Path: research/maestro_vc_v1/run_audits.py
- Purpose: one command that audits the 20 fold snapshots the replay read (against each fold's held-out
  compounds and units), the four full case libraries, the second case family, and the pairing of every
  policy record with its evaluator record; it writes `outputs/scientific_case_memory/quality_audit.json`.
- Core points:
  - A fold snapshot is audited with the compounds and units of its own held-out fold, so a leak of a
    held-out compound into the memory the arms read is a named failure here.
  - The full libraries and the second family are audited without a held-out set (no compound is held out
    of a real user's memory) and their kind balance is reported.
  - The policy and evaluator tables written by `data_layer` are paired and verified with
    `build_episode_replay.verify_replay_integrity`.
- Run: python -m research.maestro_vc_v1.run_audits
- Interfaces: `main`
- Depends on: research/scientific_case_memory, data_layer outputs, replay outputs
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

from research.scientific_case_memory import build_episode_replay as ER
from research.scientific_case_memory import case_quality_audit as QA
from research.scientific_case_memory import case_store as CS

ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "outputs/maestro_vc_v1/replay"
CASES = ROOT / "outputs/scientific_case_memory"
PROCESSED = ROOT / "data/processed/maestro_vc_v1"


def _jsonl(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def main() -> dict:
    manifest = json.loads((REPLAY / "manifest.json").read_text(encoding="utf-8"))
    comps = {"sciplex3": pd.read_csv(ROOT / "outputs/biological_depth_20260926/prepared/compounds.csv"),
             "l1000": pd.read_csv(ROOT / "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv")}
    units = {"sciplex3": "skeleton", "l1000": "component"}
    report = {"fold_snapshots": {}, "libraries": {}, "second_family": None, "episode_integrity": {}}
    for task, info in sorted(manifest["tasks"].items()):
        dataset, tier, fold = task.split("_")[0], task.split("_")[1], int(task.split("_")[2])
        c = comps[dataset]
        held = c[c.fold == fold]
        store = CS.CaseStore(REPLAY / "snapshots" / f"cases_{task}.jsonl.gz")
        result = QA.audit_store(store, pool=info["pool"], heldout_compounds=held["compound"].astype(str),
                                heldout_units=held[units[dataset]].astype(str))
        report["fold_snapshots"][task] = {"cases": result["cases"], "passed": result["passed"], "balance": result["balance"],
                                          "failures": {k: v["failures"] for k, v in result["checks"].items() if v["failures"]},
                                          "digest": result["snapshot_digest"]}
    for path in sorted(CASES.glob("library_*.jsonl.gz")):
        store = CS.CaseStore(path)
        result = QA.audit_store(store)
        report["libraries"][path.stem] = {"cases": result["cases"], "passed": result["passed"], "balance": result["balance"],
                                          "failures": {k: v["failures"] for k, v in result["checks"].items() if v["failures"]}}
    family = CS.CaseStore(CASES / "cases_genetic_pharmacological_and_engagement.jsonl.gz")
    result = QA.audit_store(family)
    report["second_family"] = {"cases": result["cases"], "passed": result["passed"], "balance": result["balance"],
                               "failures": {k: v["failures"] for k, v in result["checks"].items() if v["failures"]}}
    policy = list(_jsonl(PROCESSED / "episode_table_policy_view.jsonl.gz"))
    evaluator = list(_jsonl(PROCESSED / "episode_table_evaluator_view.jsonl.gz"))
    problems = ER.verify_replay_integrity(policy, evaluator)
    report["episode_integrity"] = {"policy_records": len(policy), "evaluator_records": len(evaluator), "problems": problems[:20],
                                   "n_problems": len(problems), "steps": list(ER.REPLAY_STEPS)}
    report["all_passed"] = (all(v["passed"] for v in report["fold_snapshots"].values())
                            and all(v["passed"] for v in report["libraries"].values()) and report["second_family"]["passed"]
                            and not problems)
    out = CASES / "quality_audit.json"
    out.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = main()
    print("all passed:", r["all_passed"])
    for name, v in {**r["fold_snapshots"], **r["libraries"], "second_family": r["second_family"]}.items():
        print(name, v["cases"], "cases", "PASS" if v["passed"] else v["failures"])
    print("episode integrity problems:", r["episode_integrity"]["n_problems"])
