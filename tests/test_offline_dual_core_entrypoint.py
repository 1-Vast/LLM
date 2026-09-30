"""Reviewed offline execution needs no live provider credentials."""
from dataclasses import asdict
import json
import sys

from agent import cli
from agent.llm import MAESTROSettings
from tests.fixtures.biological import PLAN, TASK, contract, results


def clear_provider(monkeypatch):
    for name in ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL", "DEEPSEEK_VISION_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_offline_settings_keep_the_declared_record_path(tmp_path, monkeypatch):
    clear_provider(monkeypatch)
    monkeypatch.setenv("MAESTRO_LOG_DIRECTORY", "reviewed-records")
    settings = MAESTROSettings.from_workspace(tmp_path, require_provider=False)
    assert settings.log_directory == tmp_path / "reviewed-records"
    assert settings.api_key == ""


def test_reviewed_cli_completes_a_typed_evidence_loop_without_credentials(tmp_path, monkeypatch, capsys):
    clear_provider(monkeypatch)
    actions, table, profile = contract()
    payloads = {
        "actions": [asdict(action) for action in actions], "profile": asdict(profile),
        "rules": [asdict(rule) for rule in table.rules],
        "results": {name: asdict(result) for name, result in results().items()},
        "planner": {"responses": {"task_triage": TASK, "contrast_planner": PLAN,
                    "repair_planner": {"action_identifier": None, "modified_fields": [],
                                       "rationale": "No additional catalogue action.", "remaining_limitations": []}}},
    }
    for name, payload in payloads.items():
        (tmp_path / (name + ".json")).write_text(json.dumps(payload, default=cli._json_default), encoding="utf-8")
    trace = tmp_path / "trace.json"
    monkeypatch.setattr(sys, "argv", [
        "maestro", "Verify the constructed evidence chain.", "--workspace", str(tmp_path),
        "--actions", str(tmp_path / "actions.json"), "--profile", str(tmp_path / "profile.json"),
        "--planner-template", str(tmp_path / "planner.json"), "--rules", str(tmp_path / "rules.json"),
        "--results", str(tmp_path / "results.json"), "--virtual-cell", "none", "--decision-critic", "off",
        "--state-directory", str(tmp_path / "runtime"), "--case-id", "offline-contract",
        "--budget", "5", "--max-rounds", "4", "--trace", str(trace),
    ])
    assert cli.main() == 0, capsys.readouterr().err
    payload = json.loads(trace.read_text())
    assert payload["planner"] == "reviewed_template"
    record = payload["record"]
    assert record["stop_reason"] == "decision:decided"
    assert record["decision"]["action"] == "change_intervention_mode"
    assert [r["action_identifier"] for r in record["reflections"]] == ["engagement", "function", "comparator"]
    assert record["decision"]["evidence_ids"]
