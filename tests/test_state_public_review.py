"""Contracts for preserving unqualified/changed public source evidence."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import urllib.error

import pytest

from tools.datasets import state_public_review as review


def _source(name, body, **kwargs):
    return {
        "id": name, "url": "https://example.org/metadata", "sha256": hashlib.sha256(body).hexdigest(),
        "max_bytes": 4096, "license": None, "license_scope": "test fixture", "version": "test",
        "format": "json", "identity": 1, "identity_path": ["id"], **kwargs,
    }


def _plan(tmp_path, sources):
    path = tmp_path / "pins.json"
    path.write_text(json.dumps({"sources": sources}), encoding="utf-8")
    return path


def _fixture(tmp_path, name, body):
    directory = tmp_path / "fixtures"
    directory.mkdir(exist_ok=True)
    (directory / (name + ".raw")).write_bytes(body)
    return directory


class _Response(io.BytesIO):
    def __init__(self, body, status=200):
        super().__init__(body)
        self.code = status
        self.headers = {"Content-Type": "text/html"}


def test_offline_reproduction_never_calls_network_and_refuses_existing_output(tmp_path, monkeypatch):
    body = b'{"id":1}'
    source = _source("source", body)
    plan = _plan(tmp_path, [source])
    fixtures = _fixture(tmp_path, "source", body)
    monkeypatch.setattr(review.urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("offline network call"))
    out = tmp_path / "out"
    summary = review.run(out, pins_path=plan, fixtures=fixtures)
    assert summary["negative_receipts"] == 0
    assert summary["state_gain_gate_passed"] is False
    assert (out / "source.raw").read_bytes() == body
    before = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        review.run(out, pins_path=plan, fixtures=fixtures)
    assert (out / "summary.json").read_bytes() == before


def test_changed_source_is_retained_but_not_used_for_verified_metadata(tmp_path):
    original, changed = b'{"id":1}', b'{"id":1,"new":true}'
    source = _source("source", original)
    plan = _plan(tmp_path, [source])
    fixtures = _fixture(tmp_path, "source", changed)
    out = tmp_path / "out"
    summary = review.run(out, pins_path=plan, fixtures=fixtures)
    assert summary["negative_receipts"] == 1
    assert summary["parsed_metadata"] == {}
    assert (out / "source.raw").read_bytes() == changed
    receipt = json.loads((out / "receipts.json").read_text())[0]
    assert "source_hash_changed" in receipt["errors"]


def test_http_200_challenge_page_is_a_negative_receipt(tmp_path, monkeypatch):
    body = b'<html>Checking your browser</html>'
    plan = _plan(tmp_path, [_source("source", body)])
    monkeypatch.setattr(review.urllib.request, "urlopen", lambda *args, **kwargs: _Response(body))
    out = tmp_path / "out"
    summary = review.run(out, pins_path=plan)
    receipt = json.loads((out / "receipts.json").read_text())[0]
    assert receipt["http_status"] == 200
    assert receipt["qualification"] == "negative_receipt"
    assert any(error.startswith("metadata_parse_failed") for error in receipt["errors"])
    assert summary["parsed_metadata"] == {}
    assert (out / "source.raw").read_bytes() == body


def test_http_error_body_and_status_are_retained(tmp_path, monkeypatch):
    body = b'{"id":1}'
    plan = _plan(tmp_path, [_source("source", body)])

    def fail(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.org/metadata", 503, "unavailable", {}, io.BytesIO(body))

    monkeypatch.setattr(review.urllib.request, "urlopen", fail)
    out = tmp_path / "out"
    summary = review.run(out, pins_path=plan)
    receipt = json.loads((out / "receipts.json").read_text())[0]
    assert receipt["http_status"] == 503
    assert receipt["errors"] == ["http_status"]
    assert (out / "source.raw").read_bytes() == body
    assert summary["parsed_metadata"] == {}


def test_transport_failure_has_a_named_negative_receipt(tmp_path, monkeypatch):
    plan = _plan(tmp_path, [_source("source", b'{"id":1}')])

    def fail(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(review.urllib.request, "urlopen", fail)
    out = tmp_path / "out"
    assert review.run(out, pins_path=plan)["negative_receipts"] == 1
    receipt = json.loads((out / "receipts.json").read_text())[0]
    assert receipt["http_status"] is None
    assert any("URLError" in error for error in receipt["errors"])
    assert (out / "source.raw").read_bytes() == b""


def test_bounded_response_preserves_received_prefix_and_marks_incomplete(tmp_path, monkeypatch):
    body = b'{"id":1}'
    plan = _plan(tmp_path, [_source("source", body, max_bytes=4)])
    monkeypatch.setattr(review.urllib.request, "urlopen", lambda *args, **kwargs: _Response(body))
    out = tmp_path / "out"
    review.run(out, pins_path=plan)
    receipt = json.loads((out / "receipts.json").read_text())[0]
    assert receipt["retained_response_complete"] is False
    assert "byte_budget_exceeded" in receipt["errors"]
    assert (out / "source.raw").read_bytes() == body[:5]


def test_compressed_metadata_budget_is_enforced(tmp_path, monkeypatch):
    body = gzip.compress(b"x" * 40)
    source = _source("source", body, format="gzip_soft", identity="GSE1")
    plan = _plan(tmp_path, [source])
    fixtures = _fixture(tmp_path, "source", body)
    monkeypatch.setattr(review, "DECOMPRESSED_LIMIT", 32)
    out = tmp_path / "out"
    summary = review.run(out, pins_path=plan, fixtures=fixtures)
    receipt = json.loads((out / "receipts.json").read_text())[0]
    assert summary["negative_receipts"] == 1
    assert any("decompressed metadata exceeds" in error for error in receipt["errors"])
    assert (out / "source.raw").read_bytes() == body


def test_valid_json_with_wrong_record_identity_is_not_accepted(tmp_path):
    body = b'{"id":2}'
    plan = _plan(tmp_path, [_source("source", body)])
    fixtures = _fixture(tmp_path, "source", body)
    out = tmp_path / "out"
    summary = review.run(out, pins_path=plan, fixtures=fixtures)
    assert summary["negative_receipts"] == 1
    assert summary["parsed_metadata"] == {}


def test_invalid_clone_matrix_axis_is_not_silently_transposed(tmp_path):
    columns = ["Library", "Cell barcode", "Time point", "Cell type annotation", "Cytokine condition", "SPRING-x", "SPRING-y"]
    table = gzip.compress(("\t".join(columns) + "\na\tb\t2\tu\tf\t0\t0\na\tc\t4\tu\tf\t0\t0\n").encode())
    matrix = gzip.compress(b"%%MatrixMarket matrix coordinate integer general\n%\n2 3 1\n1 1 1\n")
    sources = [_source("larry_cytokine_metadata", table, format="gzip_tsv", columns=columns),
               _source("larry_cytokine_clones", matrix, format="gzip_mtx")]
    fixtures = _fixture(tmp_path, sources[0]["id"], table)
    _fixture(tmp_path, sources[1]["id"], matrix)
    summary = review.run(tmp_path / "out", pins_path=_plan(tmp_path, sources), fixtures=fixtures)
    assert summary["clone_linkage"] == {"error": "clone_to_metadata_axis_mismatch"}
    assert summary["state_gain_gate_passed"] is False


@pytest.mark.parametrize("bad_value", ["NaN", "inf", "-1"])
def test_count_parser_refuses_nonfinite_and_negative_measurements(bad_value):
    columns = ["drug1", "cell.line", "drug1.conc", "well", "upid", "time", "cell.count", "drug1.units"]
    body = (",".join(columns) + f"\ndrug,cell,1,A01,plate,0,{bad_value},M\n").encode()
    with pytest.raises(ValueError, match="invalid count"):
        review.parse_metadata(body, {"format": "csv_counts", "columns": columns})
