"""Verify the repair diagnostic, separately from the legacy scientific verdict."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

import r1_artifacts as A
import r1_core as C
import r1_diagnostic as D

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify_run(out):
    out = Path(out)
    problems, n_replayed, n_gates = [], 0, 0
    if not (out / "FREEZE.json").is_file() or not (out / "SUMMARY.json").is_file():
        return {"status": "INCOMPLETE", "problems": ["Missing freeze or completed summary"]}
    frozen = json.loads((out / "FREEZE.json").read_text(encoding="utf-8"))
    if set(frozen.get("files", {})) != set(D.freeze()["files"]):
        problems.append("Frozen source file coverage incomplete")
    for name, digest in frozen["files"].items():
        if not (HERE / name).is_file() or A.file_hash(HERE / name) != digest:
            problems.append(f"Frozen source changed: {name}")
    if frozen["config"] != D.CONFIG:
        problems.append("Diagnostic config changed")
    if (out / "FAILED.json").exists():
        problems.append("Diagnostic has a failure record")
    streams = []
    for kind in D.CONFIG["kinds"]:
        for seed in D.CONFIG["seeds"]:
            sid = f"{kind}_{seed}"
            path = out / f"{sid}.json"
            if not path.exists():
                problems.append(f"Missing stream {sid}")
                continue
            stream = json.loads(path.read_text(encoding="utf-8"))
            streams.append(stream)
            artifacts, counts, cells = {}, Counter(), Counter()
            for row in stream["rows"]:
                key = (row["arm"], row["gen"], row["role"], row["contract"])
                counts[key] += 1
                cells[key + (row["cell"],)] += 1
                artifact = out / row["artifact"]
                if artifact not in artifacts:
                    if not artifact.exists() or A.file_hash(artifact) != row["artifact_sha256"]:
                        problems.append(f"{sid}: artifact absent or changed {row['artifact']}")
                        continue
                    artifacts[artifact] = A.load_fits(artifact)
                fits = artifacts[artifact]
                if A.file_hash(artifact) != row["artifact_sha256"]:
                    problems.append(f"{sid}: row artifact hash mismatch")
                if A.gate_programs(fits) != row["programs"]:
                    problems.append(f"{sid}: model identity mismatch")
                if len(row["probes"]) != len(set(row["probes"])) or len(row["probes"]) > D.CONFIG["budget"]:
                    problems.append(f"{sid}: query uniqueness/budget violated")
                if len(row["probes"]) != len(row["values"]):
                    problems.append(f"{sid}: query value coverage mismatch")
                pool = np.asarray(row["pool"], bool)
                if len(row["nominated"]) != 5 or len(set(row["nominated"])) != 5 or not pool[row["nominated"]].all():
                    problems.append(f"{sid}: illegal nominations")
                if row["contract"] == "T" and pool[row["probes"]].any():
                    problems.append(f"{sid}: transfer probe entered target pool")
                if A.replay(fits, row) != row["nominated"]:
                    problems.append(f"{sid}: stored nominations not reproduced")
                n_replayed += 1
                n_gates += int(bool(row["programs"]))
            for arm in D.CONFIG["arms"]:
                for generation in range(1, 5):
                    for contract in ("E", "T"):
                        if counts[(arm, generation, "task", contract)] != 4:
                            problems.append(f"{sid}: missing {arm}/{generation}/{contract} task stratum")
                        expected_cells = {f"c{8 + (generation - 1) * 4 + index:02d}" for index in range(4)}
                        actual = {key[-1]: count for key, count in cells.items()
                                  if key[:4] == (arm, generation, "task", contract)}
                        if actual != {cell: 1 for cell in expected_cells}:
                            problems.append(f"{sid}: task cell identity/duplicates {arm}/{generation}/{contract}")
            if set(stream["generation_records"]) != {"inh_kg", "rst_kg"}:
                problems.append(f"{sid}: library generation records incomplete")
            for arm, records in stream["generation_records"].items():
                if [rec["gen"] for rec in records] != [1, 2, 3, 4]:
                    problems.append(f"{sid}: missing generations for {arm}")
                for rec in records:
                    generation = rec["gen"]
                    if rec["n_candidates"] > D.CONFIG["candidate_cap_each_generation"]:
                        problems.append(f"{sid}: candidate cap exceeded")
                    if rec["archive_size_after"] != len(rec["library_after"]["archive"]):
                        problems.append(f"{sid}: inflated archive count")
                    if counts[(arm, generation, "anchor", "E")] != 2:
                        problems.append(f"{sid}: missing anchor stratum")
                    actual = {key[-1]: count for key, count in cells.items()
                              if key[:4] == (arm, generation, "anchor", "E")}
                    if actual != {"c24": 1, "c28": 1}:
                        problems.append(f"{sid}: anchor cell identity/duplicates {arm}/{generation}")
                    for row in stream["rows"]:
                        if row["arm"] != arm:
                            continue
                        after = row["role"] == "anchor" and row["gen"] == generation
                        following = row["role"] == "task" and row["gen"] == generation + 1
                        if after or following:
                            actual = [pr["pid"] for pr in row["programs"]]
                            expected = [] if rec["deployed_at_checkpoint"] is None else [rec["deployed_at_checkpoint"]]
                            if actual != expected:
                                problems.append(f"{sid}: checkpoint {arm}/{generation} does not match actual deployment")
    saved = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
    if len(streams) == len(D.CONFIG["kinds"]) * len(D.CONFIG["seeds"]):
        regenerated = D.summary(streams)
        if any(saved.get(key) != value for key, value in regenerated.items()):
            problems.append("Summary is not reproduced from stored rows")
    if saved.get("elapsed_seconds", float("inf")) > D.CONFIG["maximum_seconds"]:
        problems.append("Elapsed ceiling exceeded")
    return {"status": "REPAIR_ENGINEERING_OK" if not problems else "REPAIR_ENGINEERING_FAILED",
            "problems": sorted(set(problems)), "streams": len(streams),
            "replayed_rows": n_replayed, "replayed_gate_rows": n_gates,
            "innovation_effectiveness": "NOT_ESTABLISHED", "real_data_opened": False}


def preserved():
    before = json.loads((HERE / "PRESERVED_BEFORE.json").read_text(encoding="utf-8"))
    changed = [name for name, digest in before.items()
               if not (ROOT / name).is_file() or A.file_hash(ROOT / name) != digest]
    return {"checked_files": len(before), "changed_files": changed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=HERE / "DEVELOPMENT_RUN")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = verify_run(args.run)
    result["preservation"] = preserved()
    if result["preservation"]["changed_files"]:
        result["status"] = "REPAIR_ENGINEERING_FAILED"
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "REPAIR_ENGINEERING_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
