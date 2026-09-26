"""Replay real planner prompts with legacy/full task state over synthetic catalogues.

Offline by default. --live makes eight text calls and four optional Jev calls,
excluding bounded transport retries. No measurement or biological model is run.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agent.configuration import MAESTROSettings
from agent.context import ContextBuilder, TaskIntent
from agent.knowledge import EvidenceLedger
from agent.llm import DeepSeekChatClient, LLMError
from agent.memory import MemoryStore
from agent.planner import MechanismContrastPlanner
from agent.typesafe import TypeSafeJevClient, TypeSafeSettings, choice
from maestro.models import EvidenceAction


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")


class CaptureClient:
    def complete_json(self, messages):
        self.messages = messages
        raise RuntimeError("capture_only")


def prepare(output):
    actions = (
        EvidenceAction("archive", "Review a matched existing public target-activity experiment; no new measurement.",
                       1, ("partial", "mode"), readout="target_activity"),
        EvidenceAction("new_assay", "Acquire a new matched target-activity measurement from an independent experiment.",
                       1, ("partial", "mode"), readout="target_activity"),
    )
    fixtures = []
    for expected, constraint in (
        ("archive", "Use existing public data only. Do not acquire new measurements."),
        ("new_assay", "Require a newly acquired independent experiment. Existing archive review cannot satisfy this request."),
    ):
        intent = TaskIntent("mechanism_diagnosis",
                            "Plan a target-activity check to distinguish incomplete perturbation from mode non-equivalence.",
                            ("TARGET",), ("compound",), "synthetic cell-A at 24 hours", "target_activity",
                            ("Synthetic planning fixture; no observed activity or outcome is supplied.",),
                            (constraint,), (), False, ("Target activity has not been observed by this agent.",))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            packet = ContextBuilder(EvidenceLedger(root / "e.sqlite"), MemoryStore(root / "m.sqlite")).build(intent)
        legacy = "TASK\n" + intent.research_question + "\n\nSUPPLIED EVIDENCE\n" + "\n".join(intent.supplied_evidence)
        for arm, rendered in (("legacy", legacy), ("complete", packet.rendered)):
            capture = CaptureClient()
            try:
                MechanismContrastPlanner(capture, contract_retries=0).propose(
                    replace(packet, rendered=rendered), actions,
                    required_hypothesis_identifiers=("partial", "mode"))
            except RuntimeError as error:
                if str(error) != "capture_only":
                    raise
            fixtures.append({"case_id": expected, "expected_action": expected, "arm": arm,
                             "intent": asdict(intent), "messages": capture.messages})
    protocol = {"scope": "Synthetic task-state transport and declared-constraint compliance; no scientific utility claim.",
                "repeats": 2, "max_output_tokens": 800, "temperature": 0,
                "fixtures": fixtures,
                "limits": ["Legacy is the exact previous mandatory rendering for an empty evidence/memory store.",
                           "Same model, catalogue, settings and caps; input information and actual tokens differ.",
                           "Only two constructed cases; repeats are not independent biological samples.",
                           "Replays actual initial planner prompts, not the full controller or tool execution.",
                           "The constraint determines the answer; this is not a hidden scientific benchmark."]}
    write(output / "protocol.json", protocol)
    return fixtures


def run(output, live):
    fixtures = prepare(output)
    if not live:
        print("Prepared four planner prompts; no API calls.")
        return
    settings = replace(MAESTROSettings.from_workspace(ROOT), max_tokens=800, timeout_seconds=45)
    jev_settings = TypeSafeSettings.from_workspace(ROOT)
    text_rows, jev_rows = [], []
    for repeat in range(2):
        for fixture in (fixtures if repeat == 0 else tuple(reversed(fixtures))):
            client = DeepSeekChatClient(settings)
            row = {key: fixture[key] for key in ("case_id", "arm", "expected_action")}
            row.update(repeat=repeat, prompt_sha256=hashlib.sha256(
                json.dumps(fixture["messages"], sort_keys=True).encode()).hexdigest())
            started = time.perf_counter()
            try:
                answer, response = client.complete_json(fixture["messages"])
                row.update(answer=answer, model=response.model,
                           constraint_satisfied=answer.get("action_identifier") == fixture["expected_action"])
            except (LLMError, ValueError, TypeError) as error:
                row.update(error_type=type(error).__name__, constraint_satisfied=False)
            row.update(seconds=time.perf_counter() - started, usage=client.provider_usage)
            text_rows.append(row)
            write(output / "text_results.json", text_rows)
            print(f"{row['case_id']} {row['arm']} repeat={repeat}: {row['constraint_satisfied']}", flush=True)
    if jev_settings:
        jev = TypeSafeJevClient(jev_settings)
        for fixture in fixtures:
            state = "Select an action consistent with the requested task and catalogue. This is a synthetic planning fixture.\n" + fixture["messages"][1]["content"]
            started = time.perf_counter()
            result = jev.evaluate(state, [choice("action", "Which listed action satisfies the task constraints?", ("archive", "new_assay"))])
            selected = result.answers.get("action")
            jev_rows.append({"case_id": fixture["case_id"], "arm": fixture["arm"], "state": state,
                             "seconds": time.perf_counter() - started,
                             "constraint_satisfied": selected is not None and selected.value == fixture["expected_action"],
                             "evaluation": asdict(result)})
            write(output / "jev_results.json", jev_rows)
    summary = {"scope": "Synthetic interface only; not equal-information or equal-token-use policy comparison.",
               "text": {arm: {"calls": len(rows), "constraint_satisfied": sum(r["constraint_satisfied"] for r in rows),
                              "tokens": sum(r["usage"].get("total_tokens", 0) for r in rows)}
                        for arm in ("legacy", "complete") if (rows := [r for r in text_rows if r["arm"] == arm])},
               "jev": {arm: {"calls": len(rows), "constraint_satisfied": sum(r["constraint_satisfied"] for r in rows)}
                       for arm in ("legacy", "complete") if (rows := [r for r in jev_rows if r["arm"] == arm])}}
    write(output / "summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Use a fresh empty output directory.")
    args.output.mkdir(parents=True, exist_ok=True)
    run(args.output, args.live)
