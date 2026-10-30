"""Strict legacy-audit contracts using synthetic archived arrays only."""
from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path

import numpy as np

PATH = Path(__file__).resolve().parents[2] / "research/routes/functional_prediction/innovation_validation_repair1_20261020/r1_audit.py"
SPEC = importlib.util.spec_from_file_location("r1_audit_tested", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def package(tmp_path, *, exception=False, omit_row=False):
    source = tmp_path / "legacy"
    streams = source / "RUN/eval/streams"
    streams.mkdir(parents=True)
    (source / "RUN/eval/models").mkdir()
    cfg = {"streams": {"kinds": ["alias"], "decoupled_kinds": [], "eval_seeds": [1, 1]}}
    (source / "CONFIG.json").write_text(json.dumps(cfg), encoding="utf-8")
    freeze = {"config": cfg, "files": {n: AUDIT.digest(AUDIT.LEGACY / n) for n in AUDIT.REPLAY_CODE}}
    (source / "FREEZE.json").write_text(json.dumps(freeze), encoding="utf-8")
    features, mask = AUDIT.public_features("alias", 1)
    batches = [[f"c{k:02d}" for k in range(8 + 4 * b, 12 + 4 * b)] for b in range(4)]
    arrays, rows, records = {}, [], {}
    for gen, batch in enumerate(batches, 1):
        arrays[f"prior|b{gen}|pm"] = np.zeros(len(mask))
        arrays[f"prior|b{gen}|w"] = np.zeros(3)
        arrays[f"prior|b{gen}|fbar"] = np.zeros((len(mask), 3))
        for arm in AUDIT.ARMS:
            prefix = f"{arm}|b{gen}|N"
            arrays[prefix + "|sigma"] = np.ones(len(mask)) * 0.1
            arrays[prefix + "|meta"] = np.array(json.dumps({"kind": "null", "gates": [], "conj": [], "k": 0, "version": "synthetic"}))
            deployed = "missing_gate" if exception and arm == "rst_kg" and gen == 4 else None
            records.setdefault(arm, []).append({"gen": gen, "deployed_at_checkpoint": deployed})
            for cell in batch:
                for contract in AUDIT.CONTRACTS:
                    pool = np.ones(len(mask), dtype=bool) if contract == "E" else ~mask
                    score = np.where(pool, features[cell][0], -np.inf)
                    nom = np.lexsort((np.arange(len(mask)), -score))[:5].tolist()
                    rows.append({"arm": arm, "role": "task", "cell": cell, "gen": gen, "contract": contract,
                                 "programs": [], "probes": [], "values": [], "nominated": nom})
            rows.append({"arm": arm, "role": "A_old", "cell": "c24", "gen": gen, "contract": "E", "programs": []})
    if omit_row:
        rows.remove(next(r for r in rows if r["role"] == "task" and r["arm"] == "rst_kg" and r["gen"] == 4 and r["contract"] == "T"))
    data = {"sid": "alias_1", "kind": "alias", "seed": 1, "decoupled": False,
            "schedule": {"batches": batches}, "rows": rows, "generation_records": records}
    with gzip.open(streams / "alias_1.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(data, handle)
    np.savez_compressed(source / "RUN/eval/models/alias_1.npz", **arrays)
    if exception:
        (source / "KNOWN_EXCEPTIONS.json").write_text(json.dumps({"exceptions": [{"stream": "alias_1", "arm": "rst_kg", "gen": 4}]}), encoding="utf-8")
    return source


def test_empty_package_fails_and_writes_machine_status(tmp_path):
    source = tmp_path / "empty"
    source.mkdir()
    output = tmp_path / "result.json"
    assert AUDIT.main(["--source", str(source), "--out", str(output)]) == 1
    assert json.loads(output.read_text())["status"] == "INCOMPLETE"


def test_all_arms_generations_contracts_are_replayed_without_fitting(tmp_path, monkeypatch):
    source = package(tmp_path)
    replay = AUDIT.legacy_replay()
    def forbidden(*args, **kwargs):
        raise AssertionError("The stored-evidence audit must never fit")
    monkeypatch.setattr(replay.C, "fit_program", forbidden)
    monkeypatch.setattr(replay.C, "build_models", forbidden)
    result = AUDIT.audit_package(source)
    assert result["status"] == "TASK_REPLAY_OK_ANCHORS_NOT_REPLAYABLE"
    coverage = result["coverage"]
    assert coverage["expected_task_rows"] == coverage["replayed_task_rows"] == coverage["matching_nominations"] == 192
    assert coverage["expected_strata"] == coverage["complete_strata"] == 48
    assert len(coverage["by_arm_generation_contract"]) == 48
    assert coverage["by_arm_generation_contract"]["rst_kg/gen4/T"] == {"expected": 4, "replayed": 4, "matched": 4}
    assert result["anchor_models"]["status"] == "NOT_REPLAYABLE"


def test_declared_known_checkpoint_exception_still_fails(tmp_path):
    source = package(tmp_path, exception=True)
    output = tmp_path / "result.json"
    assert AUDIT.main(["--source", str(source), "--out", str(output)]) == 1
    result = json.loads(output.read_text())
    assert result["status"] == "INVALID_LEGACY_CHECKPOINT"
    assert result["checkpoint_failures"][0]["listed_in_known_exceptions"] is True
    assert result["checkpoint_failures"][0]["exception_waived"] is False


def test_missing_later_restart_transfer_row_fails_coverage(tmp_path):
    result = AUDIT.audit_package(package(tmp_path, omit_row=True))
    assert result["strict_pass"] is False
    assert result["coverage"]["expected_task_rows"] == 192
    assert result["coverage"]["replayed_task_rows"] == 191
    assert result["coverage"]["complete_strata"] == 47
    assert any("coverage mismatch" in p for p in result["problems"])
