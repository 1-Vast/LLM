"""Research preflight refuses absent assets and authenticates immutable byte pins."""
import hashlib
import json
import sys
from pathlib import Path

import pytest
from tools import research_validation

ROOT = Path(__file__).resolve().parents[1]


def test_research_runner_requires_the_repository_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="checkout-local"):
        research_validation.main()


def test_unreleased_protocol_never_defaults_to_core_tests(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(sys, "argv", ["tools.research_validation", "--collect-only"])
    monkeypatch.setattr(pytest, "main", lambda args: pytest.fail("must not run core tests"))
    assert research_validation.main() == 2
    assert "BLOCKED/ASSET_MISSING" in capsys.readouterr().out


def test_research_runner_targets_only_explicit_registered_tests(monkeypatch):
    targets = []
    target = "tests/test_evaluation_isolation.py"
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(sys, "argv", ["tools.research_validation", "--tests", target, "--collect-only"])
    monkeypatch.setattr(pytest, "main", lambda args: targets.append(args) or 0)
    assert research_validation.main() == 0
    assert targets == [[str(ROOT / target), "--collect-only"]]


def test_research_verification_preflight_reports_missing_assets(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (study / "FREEZE.json").write_text('{"inputs": {"missing.bin": "abc"}}')
    assert research_validation.blocked_assets(tmp_path, [("study", "result.json")]) == ["missing.bin", "result.json"]


def test_frozen_input_and_verifier_pins_cannot_be_weakened(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    data = tmp_path / "input.bin"
    data.write_bytes(b"measurement")
    verifier = study / "verify.py"
    verifier.write_text('raise RuntimeError("must not execute")')
    freeze = study / "FREEZE.json"
    freeze.write_text(json.dumps({"inputs": {"input.bin": hashlib.sha256(data.read_bytes()).hexdigest()}}))
    pin = study / "VERIFY_FREEZE.json"
    pin.write_text(json.dumps({"verifier_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest(),
                               "trial_freeze_sha256": hashlib.sha256(freeze.read_bytes()).hexdigest()}))
    (tmp_path / "result.json").write_text('{}')
    studies = [("study", "result.json")]
    assert research_validation.blocked_assets(tmp_path, studies) == []
    data.write_bytes(b"changed")
    verifier.write_text('print("changed")')
    freeze.write_text(freeze.read_text() + "\n")
    assert research_validation.blocked_assets(tmp_path, studies) == [
        "input.bin (SHA256_MISMATCH)", "study/FREEZE.json (SHA256_MISMATCH)",
        "study/verify.py (SHA256_MISMATCH)"]
