"""Research preflight refuses absent assets and authenticates immutable byte pins."""
import hashlib
import json
import sys
from pathlib import Path

import pytest
from tools import research_validation

ROOT = Path(__file__).resolve().parents[2]


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
    target = "tests/evaluation/test_evaluation_isolation.py"
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


def _sha256_study(root, schema="sha256"):
    """A frozen study in the form the committed studies use: root-relative keys, LF-normalised digests."""
    study = root / "research" / "s"
    study.mkdir(parents=True)
    protocol = study / "PROTOCOL.md"
    protocol.write_bytes(b"# protocol\n")
    digest = hashlib.sha256(b"# protocol\n").hexdigest()
    key = "PROTOCOL.md" if schema == "files" else "research/s/PROTOCOL.md"
    (study / "FREEZE.json").write_text(json.dumps({"locked_utc": "x", schema: {key: digest}}))
    (study / "RESULT.json").write_text("{}")
    return [("research/s", "research/s/RESULT.json")], protocol


@pytest.mark.parametrize("schema", ["sha256", "files", "sha256_lf"])
def test_sha256_and_files_freezes_are_authenticated_not_skipped(tmp_path, schema):
    studies, protocol = _sha256_study(tmp_path, schema)
    blocked, checked = research_validation.authenticate(tmp_path, studies)
    assert blocked == [] and checked == {"research/s": (schema, 1)}
    protocol.write_bytes(b"# protocol, edited after the freeze\n")
    assert research_validation.blocked_assets(tmp_path, studies) == ["research/s/PROTOCOL.md (SHA256_MISMATCH)"]
    protocol.unlink()
    assert research_validation.blocked_assets(tmp_path, studies) == ["research/s/PROTOCOL.md"]


def test_crlf_checkout_matches_lf_freeze_only_where_the_schema_declares_it(tmp_path):
    studies, protocol = _sha256_study(tmp_path)
    protocol.write_bytes(b"# protocol\r\n")
    assert research_validation.blocked_assets(tmp_path, studies) == []
    raw = tmp_path / "raw.txt"
    raw.write_bytes(b"line\r\n")
    (tmp_path / "research" / "s" / "FREEZE.json").write_text(
        json.dumps({"inputs": {"raw.txt": hashlib.sha256(b"line\n").hexdigest()}}))
    assert research_validation.blocked_assets(tmp_path, studies) == ["raw.txt (SHA256_MISMATCH)"]


def test_sha256_lf_accepts_only_the_lf_normalised_digest(tmp_path):
    studies, protocol = _sha256_study(tmp_path, "sha256_lf")
    protocol.write_bytes(b"# protocol\r\n")
    assert research_validation.blocked_assets(tmp_path, studies) == []
    (tmp_path / "research" / "s" / "FREEZE.json").write_text(json.dumps(
        {"sha256_lf": {"research/s/PROTOCOL.md": hashlib.sha256(b"# protocol\r\n").hexdigest()}}))
    assert research_validation.blocked_assets(tmp_path, studies) == ["research/s/PROTOCOL.md (SHA256_MISMATCH)"]


@pytest.mark.parametrize("freeze, reason", [
    ({"protocol_sha256": "0" * 64, "loader_sha256": "1" * 64}, "FREEZE_SCHEMA_UNSUPPORTED"),
    ({"sha256": {}}, "FREEZE_SCHEMA_EMPTY"),
    ({"inputs": {"a": "0" * 64}, "sha256": {"a": "0" * 64}}, "FREEZE_SCHEMA_UNSUPPORTED"),
    ({"sha256": ["research/s/PROTOCOL.md"]}, "FREEZE_SCHEMA_EMPTY"),
])
def test_unsupported_or_empty_freeze_schemas_are_refused(tmp_path, freeze, reason):
    studies, _ = _sha256_study(tmp_path)
    (tmp_path / "research" / "s" / "FREEZE.json").write_text(json.dumps(freeze))
    blocked, checked = research_validation.authenticate(tmp_path, studies)
    assert len(blocked) == 1 and blocked[0].startswith(f"research/s/FREEZE.json ({reason}") and checked == {}


def test_frozen_paths_cannot_escape_the_checkout(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("x")
    studies, _ = _sha256_study(root)
    (root / "research" / "s" / "FREEZE.json").write_text(
        json.dumps({"sha256": {"../outside.txt": hashlib.sha256(b"x").hexdigest()}}))
    assert research_validation.blocked_assets(root, studies) == ["../outside.txt (PATH_OUTSIDE_CHECKOUT)"]


def test_explicit_study_command_reports_counts_and_never_claims_research_verification(tmp_path, monkeypatch, capsys):
    (tmp_path / "pyproject.toml").write_text("")
    _, protocol = _sha256_study(tmp_path)
    monkeypatch.setattr(research_validation, "ROOT", tmp_path.resolve())
    monkeypatch.chdir(tmp_path)
    argv = ["tools.research_validation", "--verify", "--study", "research/s", "--result", "research/s/RESULT.json"]
    monkeypatch.setattr(sys, "argv", argv)
    assert research_validation.main() == 0
    out = capsys.readouterr().out
    assert "1 frozen files authenticated" in out and "Not executed: research verification" in out
    protocol.write_bytes(b"tampered\n")
    assert research_validation.main() == 2
    assert capsys.readouterr().out.startswith("BLOCKED/ASSET_MISSING\nresearch/s/PROTOCOL.md (SHA256_MISMATCH)")
    (tmp_path / "research" / "s" / "FREEZE.json").write_text(json.dumps({"protocol_sha256": "0" * 64}))
    assert research_validation.main() == 2
    assert capsys.readouterr().out.startswith("BLOCKED/FREEZE_SCHEMA_UNSUPPORTED")


def test_files_schema_resolves_study_then_checkout_and_still_authenticates(tmp_path):
    studies, _ = _sha256_study(tmp_path, "files")
    shared = tmp_path / "tools" / "scoring.py"
    shared.parent.mkdir()
    shared.write_bytes(b"def score():\n    return 0\n")
    freeze = tmp_path / "research" / "s" / "FREEZE.json"
    record = json.loads(freeze.read_text())
    record["files"]["tools/scoring.py"] = hashlib.sha256(shared.read_bytes()).hexdigest()
    freeze.write_text(json.dumps(record))
    assert research_validation.authenticate(tmp_path, studies) == ([], {"research/s": ("files", 2)})
    shared.write_bytes(b"def score():\n    return 1\n")
    assert research_validation.blocked_assets(tmp_path, studies) == ["research/s/tools/scoring.py (SHA256_MISMATCH)"]
    shared.unlink()
    assert research_validation.blocked_assets(tmp_path, studies) == ["research/s/tools/scoring.py"]
