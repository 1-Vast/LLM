"""Intake preserves evidence uncertainty and never executes supplied source code."""
import csv
import hashlib

import pytest

from research.astra.realisation_plan import TABLES, audit_review_inputs, run


def test_review_audit_does_not_execute_supplied_python(tmp_path):
    supplied = tmp_path / "inputs"
    supplied.mkdir()
    source = supplied / "probe.py"
    source.write_text("raise RuntimeError('must not execute')\ndef function():\n    pass\n")
    original = source.read_bytes()
    row, = audit_review_inputs(supplied, tmp_path)
    assert row["role"] == "source_code" and row["top_level_definitions"] == ["function"]
    assert row["sha256"] == hashlib.sha256(original).hexdigest()
    assert source.read_bytes() == original


def test_unknown_table_remains_unreviewed_and_cannot_certify_training(tmp_path):
    supplied = tmp_path / "inputs"
    supplied.mkdir()
    (supplied / "observations.csv").write_text("value\n1\n")
    output = tmp_path / "out"
    report = run(supplied, output, tmp_path)
    assert report["matched_training_table_present"] is None
    assert report["unknown_input_files"]
    assert not report["design"]["training_executed"]
    for name, fields in TABLES.items():
        with (output / name).open(newline="") as handle:
            assert list(csv.reader(handle)) == [list(fields)]
    with pytest.raises(FileExistsError):
        run(supplied, output, tmp_path)
