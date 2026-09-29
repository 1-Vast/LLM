from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from tools.datasets.benchmark import build


def test_dataset_catalog_reports_checksum_mismatch_and_unknown_license(tmp_path):
    import hashlib
    from tools.datasets.catalog import audit_source

    path = tmp_path / "matrix.csv"
    path.write_text("gene,value\nA,1\n", encoding="utf-8")
    source = {"id": "example", "path": path.name,
              "recorded_sha256": hashlib.sha256(b"different").hexdigest()}
    record = audit_source(source, root=tmp_path)
    assert record["checksum_status"] == "mismatch"
    assert record["licence"] == "unverified"
    assert record["columns"] == ["gene", "value"]


def test_dataset_fetch_commits_only_verified_bytes(tmp_path, monkeypatch):
    import hashlib
    import io
    from tools.datasets import catalog

    payload = b"registered source bytes"
    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    monkeypatch.setattr(catalog.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(payload))
    destination = tmp_path / "data/external/example.bin"
    digest = hashlib.sha256(payload).hexdigest()
    result = catalog.fetch("https://example.test/asset", destination, expected_sha256=digest)
    assert destination.read_bytes() == payload
    assert result["sha256"] == digest
    assert destination.with_suffix(".bin.provenance.json").exists()


def test_dataset_fetch_refuses_bad_hash_and_retains_existing_partial(tmp_path, monkeypatch):
    import io
    import pytest
    from tools.datasets import catalog

    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    monkeypatch.setattr(catalog.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(b"bad bytes"))
    destination = tmp_path / "data/external/example.bin"
    with pytest.raises(ValueError, match="mismatch"):
        catalog.fetch("https://example.test/asset", destination, expected_sha256="0" * 64)
    assert not destination.exists()
    partial = destination.with_name(destination.name + ".part")
    partial.write_bytes(b"another active download")
    with pytest.raises(FileExistsError):
        catalog.fetch("https://example.test/asset", destination, expected_sha256="0" * 64)
    assert partial.read_bytes() == b"another active download"


def test_dataset_fetch_enforces_size_and_destination_boundaries(tmp_path, monkeypatch):
    import io
    import pytest
    from tools.datasets import catalog

    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    monkeypatch.setattr(catalog.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(b"large payload"))
    destination = tmp_path / "data/external/example.bin"
    with pytest.raises(ValueError, match="budget"):
        catalog.fetch("https://example.test/asset", destination, expected_sha256="0" * 64, max_bytes=1)
    assert not destination.exists()
    assert not destination.with_name(destination.name + ".part").exists()
    with pytest.raises(ValueError, match="data/"):
        catalog.fetch("https://example.test/asset", tmp_path / "outside.bin", expected_sha256="0" * 64)
from tools.evaluation.scoring import score_sequence


def _read(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "outputs/protocol_v2_1_20260927/e_data1/manifest.json").exists(),
    reason="protocol-v2.1 source is not present",
)
def test_model_benchmark_separates_public_inputs_and_hidden_outcomes(tmp_path):
    manifest = build(out_dir=tmp_path)
    public = _read(tmp_path / "public_episodes.jsonl.gz")
    hidden = _read(tmp_path / "hidden_outcomes.jsonl.gz")
    assert len(public) == len(hidden) == manifest["episodes"]
    assert {row["episode_id"] for row in public} == {row["episode_id"] for row in hidden}
    forbidden = {"truth", "outcomes", "readout", "lifecycle", "score"}
    for row in public:
        assert forbidden.isdisjoint(row)
        assert row["source_visibility"] == "pre_action_metadata_only"
    for row in hidden:
        assert row["source_visibility"] == "post_action_evaluator_only"
        assert row["outcomes"]


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "outputs/protocol_v2_1_20260927/e_data1/manifest.json").exists(),
    reason="protocol-v2.1 source is not present",
)
def test_model_benchmark_actions_are_within_declared_menu(tmp_path):
    build(out_dir=tmp_path)
    public = {row["episode_id"]: row for row in _read(tmp_path / "public_episodes.jsonl.gz")}
    for row in _read(tmp_path / "hidden_outcomes.jsonl.gz"):
        allowed = {item["action"] for item in public[row["episode_id"]]["menu"]}
        assert {item["action"] for item in row["outcomes"]} <= allowed


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "outputs/protocol_v2_1_20260927/e_data1/manifest.json").exists(),
    reason="protocol-v2.1 source is not present",
)
def test_model_replay_scores_only_after_join_and_rejects_illegal_sequences(tmp_path):
    build(out_dir=tmp_path)
    public = _read(tmp_path / "public_episodes.jsonl.gz")[0]
    hidden = _read(tmp_path / "hidden_outcomes.jsonl.gz")[0]
    action = public["menu"][0]["action"]
    result = score_sequence(public, hidden, [action])
    assert result["episode_id"] == public["episode_id"]
    with pytest.raises(ValueError, match="action_not_in_menu"):
        score_sequence(public, hidden, ["not-a-real-action"])
    with pytest.raises(ValueError, match="public_hidden_episode_mismatch"):
        score_sequence(public, {**hidden, "episode_id": "other"}, [action])
