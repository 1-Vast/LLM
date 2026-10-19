"""Regression checks for read-only verification and write-once study outputs."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def test_decision_import_is_read_only(monkeypatch):
    def reject_write(*args, **kwargs):
        pytest.fail("importing decision logic must not write files")

    monkeypatch.setattr(Path, "write_text", reject_write)
    spec = importlib.util.spec_from_file_location("far_decide_readonly", HERE / "far_decide.py")
    spec.loader.exec_module(importlib.util.module_from_spec(spec))


def test_decision_matches_saved_result():
    from far_decide import decide

    assert decide() == json.loads((HERE / "DECISION.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("stage", ["search", "select", "test"])
def test_existing_stage_stops_before_data_access(stage, tmp_path, monkeypatch):
    import far_run

    output = tmp_path / f"records_{stage}.npz"
    output.write_bytes(b"existing record")
    model = tmp_path / "MODEL.json"
    model.write_bytes(b"existing model")
    monkeypatch.setattr(far_run, "HERE", tmp_path)
    monkeypatch.setattr(sys, "argv", ["far_run.py", stage])
    monkeypatch.setattr(far_run, "build", lambda *args: pytest.fail("must stop before loading data"))
    with pytest.raises(SystemExit, match="write-once"):
        far_run.main()
    assert output.read_bytes() == b"existing record"
    assert model.read_bytes() == b"existing model"


def test_existing_value_model_stops_before_data_access(tmp_path, monkeypatch):
    import far_v2_search

    model = tmp_path / "VALUE_MODEL.pkl"
    model.write_bytes(b"existing model")
    monkeypatch.setattr(far_v2_search, "HERE", tmp_path)
    monkeypatch.setattr(far_v2_search, "build", lambda *args: pytest.fail("must stop before loading data"))
    with pytest.raises(SystemExit, match="write-once"):
        far_v2_search.main()
    assert model.read_bytes() == b"existing model"


def test_verifier_rejects_wrong_decision_without_rewriting(monkeypatch, capsys):
    import far_analyse
    import far_decide
    import verify

    output = HERE / "DECISION.json"
    before = output.read_bytes()
    expected = json.loads((HERE / "CONTRASTS_test_U.json").read_text())["contrasts"]["far.gate-exploit.gate"]
    monkeypatch.setattr(far_decide, "decide", lambda: {})
    monkeypatch.setattr(far_analyse, "contrast", lambda *args: expected)
    with pytest.raises(SystemExit) as exc:
        verify.main()
    assert exc.value.code == 1
    assert "DECISION.json does not recompute" in capsys.readouterr().out
    assert output.read_bytes() == before
