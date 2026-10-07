"""Rebuild operational-study metrics from frozen assets, logs and SQLite facts.

Does not import the study driver, call a provider or run STATE. Restart/retry
checks use fresh copies owned by this verification directory.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import sqlite3
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
STUDY = ROOT / "research/astra/agent_closed_loop_20261007"
PRIOR = ROOT / "research/astra/zeroshot_context_20261007"
sys.path[:0] = [str(ROOT), str(ROOT / "src")]


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def rows(path, table):
    with sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def close(actual, expected):
    assert np.isclose(float(actual), float(expected), rtol=1e-12, atol=1e-14), (actual, expected)


def check_arm(name, protocol, shadow):
    folder = STUDY / name
    summary = read_json(folder / "SUMMARY.json")
    events = read_lines(folder / "actions.jsonl")
    facts = rows(folder / "cases.sqlite", "results")
    plans = rows(folder / "cases.sqlite", "planned_actions")
    predictions = rows(folder / "cases.sqlite", "prediction_records")
    evidence = rows(folder / "evidence.sqlite", "evidence")
    assert not rows(folder / "cases.sqlite", "prediction_scores")
    assert len(facts) == summary["purchases"] == summary["state_backend_calls"]
    assert len(predictions) == len(plans) == len(facts)
    assert summary["fresh_state_inference_calls"] == 0
    assert summary["calibrated_runtime_scores"] == 0
    counts = {case["case_id"]: sum(fact["case_id"] == case["case_id"] for fact in facts)
              for case in summary["cases"]}
    assert sum(count == 2 for count in counts.values()) == summary["completed_cases"]
    assert sum(len(case["failures"]) for case in summary["cases"]) == summary["failures"]
    for case in summary["cases"]:
        assert len(case["phases"]) == counts[case["case_id"]]
        if "restored_decision" in case:
            first = case["first_feedback"]
            assert case["restored_decision"] == (float(first["profile_mse"]) > float(first["sampling_noise_estimate"]))
            assert case["facts_restored"] and not case["recovery_capabilities"]["scientific_continuation"]
    fact_index = {row["result_id"]: row for row in facts}
    error_sum = 0.0
    for index, event in enumerate(events):
        if event["event"] == "source_resolved":
            execution = event["execution"]
            receipt = execution["receipt"]
            assert execution["evidence_kind"] == "derived_analysis"
            assert receipt["state"] == "committed" and receipt["cost"] == 0.0
            assert receipt["input_sha256"] == digest(STUDY / "SOURCES.json")
            tool_hash = hashlib.sha256()
            for part in (ROOT / "tools/datasets/condition_sources.manifest.json",
                         ROOT / "tools/datasets/condition_sources_tool.py",
                         ROOT / "tools/datasets/condition_sources.py"):
                content = part.read_bytes()
                tool_hash.update(len(content).to_bytes(8, "big")); tool_hash.update(content)
            assert receipt["tool_version_sha256"] == tool_hash.hexdigest()
            output = {"schema_version": execution["schema_version"], "payload": execution["payload"],
                      "observations": execution["observations"], "limitations": execution["limitations"],
                      "artifacts": execution["artifacts"]}
            canonical = json.dumps(output, ensure_ascii=True, sort_keys=True, allow_nan=False, separators=(",", ":"))
            assert hashlib.sha256(canonical.encode()).hexdigest() == receipt["output_sha256"]
            record = next(row for row in evidence if row["id"] == event["evidence_id"])
            assert record["case_id"] == event["case_id"] and record["partition"] == "case"
            assert record["evidence_kind"] == "derived_analysis"
        if event["event"] != "paid_reveal":
            continue
        result_id = event["result_id"]
        fact = fact_index[result_id]
        case_id, version = event["case_id"], event["plan_version"]
        preceding = [item["event"] for item in events[:index] if item["case_id"] == case_id
                     and item.get("plan_version") == version]
        assert "plan_committed" in preceding and "profile_purchase_started" in preceding
        plan_event = next(item for item in events[:index] if item["event"] == "plan_committed"
                          and item["case_id"] == case_id and item["plan_version"] == version)
        request, prediction = plan_event["request"], plan_event["prediction"]
        source = request["observation_context"]
        assert prediction["request_id"] == request["request_id"] == event["request_id"]
        assert prediction["model_version"] == request["model_version"]
        assert request["case_id"] == case_id and request["plan_version"] == version
        assert request["intervention"]["time_hours"] == 24.0
        assert request["readouts"] == ["RNA_delta_rms"]
        assert source["native_axis"] == "X_hvg:2000"
        assert source["checkpoint_sha256"] == protocol["checkpoint"]["sha256"]
        observation_path = ROOT / event["source_reference"]
        file = observation_path.name.removesuffix(".npz")
        assert digest(observation_path) == read_json(PRIOR / "observations" / f"{file}.receipt.json")["sha256"]
        state_path = ROOT / request["context"]["dataset_id"]
        assert digest(state_path) == source["source_sha256"] == prediction["artifact_sha256"]
        native_receipt = read_json(PRIOR / "state_forecasts" / f"{file}.receipt.json")
        assert native_receipt["sha256"] == source["source_sha256"]
        assert native_receipt["treated_rows_read"] is False
        assert native_receipt["basal"][event["plate"]]["sha256"] == source["basal_input_sha256"]
        assert request["context"]["control_dataset_id"] == source["basal_input_sha256"]
        with np.load(observation_path, allow_pickle=False) as obs, np.load(state_path, allow_pickle=False) as state:
            select = np.flatnonzero((obs["label"] == event["label"]) & (obs["plate"] == event["plate"]))
            controls = np.flatnonzero(obs["ctrl_plate"] == event["plate"])
            native = np.flatnonzero((state["label"] == event["label"]) & (state["plate"] == event["plate"]))
            assert len(select) == len(controls) == len(native) == 1
            i, c, n = int(select[0]), int(controls[0]), int(native[0])
            assert i == event["observation_row"] and c == event["control_row"]
            observed = obs["mean"][i].astype(float) - obs["ctrl_mean"][c].astype(float)
            predicted = state["paired_delta"][n].astype(float)
            mse = float(np.mean((observed - predicted) ** 2))
            # Match original float32 summary arithmetic; persisted count is a Python int.
            noise = float(np.mean(obs["var"][i]) / int(obs["n"][i]) + np.mean(obs["ctrl_var"][c]) / int(obs["ctrl_n"][c]))
            metrics = {"RNA_delta_rms": float(np.sqrt(np.mean(observed ** 2))), "profile_mse": mse,
                       "sampling_noise_estimate": noise, "treated_cells": int(obs["n"][i]),
                       "reference_cells": int(obs["ctrl_n"][c])}
            for key, value in metrics.items():
                close(event["metrics"][key], value)
                close(json.loads(fact["metrics_json"])[key], value)
            close(prediction["state_change"]["RNA_delta_rms"], np.sqrt(np.mean(predicted ** 2)))
            saved_path = folder / event["profile"]
            assert digest(saved_path) == event["profile_sha256"]
            with np.load(saved_path, allow_pickle=False) as saved:
                assert np.array_equal(saved["observed_delta"], observed)
                assert np.array_equal(saved["predicted_delta"], predicted)
            error_sum += mse
        extraction = read_json(ROOT / f"data/external/tahoe_zeroshot_20261007/extract/plans/{file}.plan.json")
        control = next(group for group in extraction["groups"] if group["control"] and group["plate"] == event["plate"])
        ref_rows = {row for row, full, role in zip(control["rows"], control["full"], control["control_role"])
                    if full and role == "reference"}
        assert not ref_rows.intersection(native_receipt["basal"][event["plate"]]["source_rows"])
        assert fact["plan_version"] == version and fact["evidence_kind"] == "retrieved_source"
        pair = next(row for row in predictions if row["case_id"] == case_id and row["plan_version"] == version)
        assert pair["request_id"] == event["request_id"]
        assert json.loads(pair["payload_json"])["request"] == request
        result_record = next(row for row in evidence if json.loads(row["payload_json"]).get("result_id") == result_id)
        assert result_record["case_id"] == case_id and result_record["partition"] == "case"
        assert result_record["evidence_kind"] == "retrieved_source"
    close(sum(row["spent"] for row in rows(folder / "cases.sqlite", "cases")), summary["spent"])
    close(sum(row["cost"] for row in plans), summary["spent"])
    assert len({row["id"] for row in evidence}) == len(evidence) == 2 * len(facts)
    api = read_lines(folder / "api.jsonl") if (folder / "api.jsonl").is_file() else []
    assert len(api) == summary["api_completions"]
    usage = {}
    for call in api:
        assert call["status"] == "completed" and call["max_tokens"] <= 800
        for key, value in call["usage"].items():
            usage[key] = usage.get(key, 0) + value
    for key, value in usage.items():
        assert summary["provider_usage"][key] == value
    transport = read_lines(folder / "transport.jsonl") if (folder / "transport.jsonl").is_file() else []
    if "transport_attempts" in summary:
        assert len(transport) == summary["transport_attempts"]
        assert all(item["status"] == "connection_opened" for item in transport)
    if name in ("deterministic_run4", "live_run2"):
        refusals = [event for event in events if event["event"] == "pre_acquisition_refusal"]
        assert len(refusals) == len(facts) == 8
        assert all("missing_source_binding:source_sha256" in event["missing_inputs"] for event in refusals)
    # A real fresh runtime on copied facts retries both historical versions.
    from agent.case_store import CaseStore
    from agent.context import ContextBuilder, TaskInterpreter
    from agent.knowledge import EvidenceLedger
    from agent.llm import VisualInspector
    from agent.memory import MemoryStore, RunLogger
    from agent.orchestrator import MAESTROOrchestrator
    from agent.planner import MechanismContrastPlanner
    shadow.mkdir()
    for database_name in ("cases.sqlite", "evidence.sqlite", "memory.sqlite"):
        shutil.copy2(folder / database_name, shadow / database_name)
    store, memory = CaseStore(shadow / "cases.sqlite"), MemoryStore(shadow / "memory.sqlite")
    builder = ContextBuilder(EvidenceLedger(shadow / "evidence.sqlite"), memory)
    runtime = MAESTROOrchestrator(interpreter=TaskInterpreter(None), context_builder=builder,
        planner=MechanismContrastPlanner(None), visual_inspector=VisualInspector(None, "unused"),
        memory=memory, logger=RunLogger(shadow / "logs"), case_store=store, selection_strategy="budgeted_coverage")
    for fact in facts:
        before = store.snapshot(fact["case_id"])
        original = store.prediction_for_result(fact["case_id"], fact["result_id"])
        retry = runtime.import_measurement(fact["case_id"], store.measurement(fact["case_id"], fact["result_id"]))
        assert not retry.created and retry.snapshot.spent == before.spent
        assert store.prediction_for_result(fact["case_id"], fact["result_id"]) == original
        assert not runtime.recovery_capabilities(fact["case_id"])["scientific_continuation"]
    assert not runtime._reliability.records
    return dict(arm=name, cases=len(summary["cases"]), completed_cases=summary["completed_cases"],
                purchases=len(facts), spent=summary["spent"], failures=summary["failures"],
                api_calls=len(api), usage=usage, reconstructed_profile_mse_sum=error_sum,
                observed_transport_attempts=len(transport) if "transport_attempts" in summary else None,
                restart_retries_checked=len(facts), source_tool_authority="derived_analysis",
                paid_public_result_authority="retrieved_source", runtime_calibrated_scores=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a fresh verification output")
    frozen, protocol = read_json(STUDY / "PROTOCOL_FREEZE.json"), read_json(STUDY / "PROTOCOL.json")
    assert digest(STUDY / "PROTOCOL.json") == frozen["protocol_sha256"]
    assert digest(STUDY / "SOURCES.json") == frozen["sources_sha256"]
    assert digest(STUDY / "register.py") == frozen["registration_code_sha256"]
    assert digest(protocol["checkpoint"]["path"]) == protocol["checkpoint"]["sha256"]
    if any(name in ("deterministic_run4", "live_run2") for name in args.arms):
        execution_freeze = read_json(STUDY / "EXECUTION_FREEZE_V2.json")
        for category in ("code", "production"):
            assert all(digest(ROOT / relative) == expected for relative, expected in execution_freeze[category].items())
        amendment = read_json(STUDY / "EXECUTION_AMENDMENT.json")
        assert digest(STUDY / "live_run1/SUMMARY.json") == amendment["old_live_summary_sha256"]
    shadow_root = args.output.parent / (args.output.stem + "_restarts")
    shadow_root.mkdir()
    results = [check_arm(name, protocol, shadow_root / name) for name in args.arms]
    final = [name for name in args.arms if name in ("deterministic_run4", "live_run2")]
    if len(final) == 2:
        def comparison(name):
            records = [event for event in read_lines(STUDY / name / "actions.jsonl") if event["event"] == "paid_reveal"]
            return [(event["label"], event["plate"], event["plan_version"], event["metrics"]) for event in records]
        assert comparison(final[0]) == comparison(final[1])
    result = dict(verdict="PASS", created_utc=datetime.now(timezone.utc).isoformat(), arms=results,
                  fresh_state_inference_calls=0, biological_gain_established=False,
                  limitation="Saved exposed-development operational replay; agency and biological utility unproven.")
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2); handle.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
