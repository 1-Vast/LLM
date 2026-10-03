"""Deterministic software-only latency/work benchmarks; no biological gain claims."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time
from unittest.mock import patch

from agent.case_store import CaseStore, MeasurementResult
from agent.knowledge import EvidenceLedger, EvidenceStatus
from agent.memory import EpistemicStatus, MemoryKind, MemoryStore, RunLogger
from maestro.handoff import DecisionLayer, EvidenceLayer, ExecutionLayer, RoundRecord, WorldModelLayer
from maestro.models import EvidenceAction


def graph(root, count, kind):
    """Reverse insertion makes chain depth observable; setup is outside the timer.

    SQL clones valid templates to avoid per-row setup transactions. Visibility
    deliberately includes one missing ancestor, modelling an unverifiable legacy
    record; it is never ingested as qualified evidence.
    """
    if kind == "memory":
        store = MemoryStore(root / "memory.sqlite")
        entry = store.remember("fixture", kind=MemoryKind.EPISODIC,
                               status=EpistemicStatus.DERIVED, provenance="fixture", session_id="s")
        table, lineage = "memories", "parent_ids"
    else:
        store = EvidenceLedger(root / "evidence.sqlite")
        entry = store.add_evidence("fixture", source="fixture", context="fixture",
                                  status=EvidenceStatus.RETRIEVED)
        table, lineage = "evidence", "lineage_ids"
    with store._connection() as connection:
        template = dict(zip([r[1] for r in connection.execute(f"PRAGMA table_info({table})")],
                            connection.execute(f"SELECT * FROM {table} WHERE id = ?", (entry.identifier,)).fetchone()))
        connection.execute(f"DELETE FROM {table}")
        columns = tuple(template)
        rows = []
        for i in reversed(range(count)):
            row = dict(template, id=f"node:{i}")
            parents = [f"node:{i-1}"] if i else (["missing"] if kind == "visibility" else [])
            row[lineage] = ",".join(parents) if kind == "memory" else json.dumps(parents)
            rows.append(tuple(row[key] for key in columns))
        connection.executemany(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", rows)
    if kind == "memory":
        return lambda: store.retract("node:0")
    if kind == "evidence":
        return lambda: store.retract_evidence("node:0")
    def visible():
        with store._connection() as connection:
            return tuple(store._visible_evidence(connection, None))
    return visible


def audit(root, count):
    store = CaseStore(root / "cases.sqlite")
    store.open_case("case", budget=1)
    store.record_plan("case", (EvidenceAction("a", "Assay", 1, ("a", "b"), time_hours=24,
                      expected_conditions={"dose": "1 uM"}),), ready_to_measure=True, context_identifier="cells")
    store.import_measurement("case", MeasurementResult("a", "Observed", "fixture:assay", "cells", 24, 2, True,
                             conditions={"dose": "1 uM"}, result_id="result:a", plan_version=1))
    logger = RunLogger(root)
    plan = RoundRecord("session", 1, EvidenceLayer(missing_reason=("fixture_no_sources",)),
                       WorldModelLayer.no_model(), DecisionLayer(), ExecutionLayer())
    assert logger.round(plan, stage="plan", case_id="case", plan_version=1)
    view = replace(plan, execution=ExecutionLayer(result_id="result:a", contradiction_flag=True,
                                                belief_delta={"fixture-hypothesis": -1}))
    assert logger.round(view, stage="result", case_id="case", plan_version=1)
    receipts = logger.events_path.read_text(encoding="utf-8")
    with logger.events_path.open("a", encoding="utf-8") as stream:
        for _ in range(count - 1):
            stream.write(receipts)
            stream.write(json.dumps({"kind": "fixture_unrelated", "payload": {"case_id": "other"}}) + "\n")
    return lambda: logger.review_case("case", store)


def run(count, repeats):
    results = {}
    for kind in ("memory", "evidence", "visibility", "audit"):
        samples, outputs, reads = [], [], []
        for _ in range(repeats):
            with tempfile.TemporaryDirectory(prefix="maestro-efficiency-") as directory:
                root = Path(directory)
                operation = audit(root, count) if kind == "audit" else graph(root, count, kind)
                original_bytes, original_text = Path.read_bytes, Path.read_text
                file_reads = []
                def read_bytes(path, *args, **kwargs):
                    if path.parent.name == "rounds":
                        file_reads.append(str(path))
                    return original_bytes(path, *args, **kwargs)
                def read_text(path, *args, **kwargs):
                    if path.parent.name == "rounds":
                        file_reads.append(str(path))
                    return original_text(path, *args, **kwargs)
                with patch.object(Path, "read_bytes", read_bytes), patch.object(Path, "read_text", read_text):
                    start = time.perf_counter()
                    output = operation()
                    samples.append(time.perf_counter() - start)
                if kind in ("memory", "evidence"):
                    assert output == tuple(sorted(f"node:{i}" for i in range(count)))
                elif kind == "visibility":
                    assert output == ()
                else:
                    assert output["result_records"] == 1 and not output["judgement_never_changed"]
                outputs.append(hashlib.sha256(json.dumps(output, sort_keys=True).encode()).hexdigest())
                reads.append(len(file_reads))
        assert len(set(outputs)) == 1
        results[kind] = {"seconds": samples, "median_seconds": statistics.median(samples),
                         "output_sha256": outputs[0], "round_file_reads": reads}
    return {"fixture_version": 1, "count": count, "repeats": repeats,
            "python": platform.python_version(), "platform": platform.platform(),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "source_sha256": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
                              ("src/agent/memory.py", "src/agent/knowledge.py", __file__)},
            "scope": "synthetic software fixtures; timed operations only, patched read counters; no inference or biology",
            "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=600)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    result = run(args.count, args.repeats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
