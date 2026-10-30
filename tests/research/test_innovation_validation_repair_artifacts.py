"""Persistence and no-refit replay contracts for the repaired deployment."""
import importlib
from pathlib import Path
import sys

import numpy as np

STUDY = Path(__file__).resolve().parents[2] / "research" / "routes" / "functional_prediction" / "innovation_validation_repair1_20261020"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
C = importlib.import_module("r1_core")
G = importlib.import_module("r1_gates")
A = importlib.import_module("r1_artifacts")
V = importlib.import_module("r1_verify")


def test_artifact_roundtrip_preserves_actual_gate_and_observation_updates(tmp_path, monkeypatch):
    gate = G.Gate("g", np.array([0.3]), beta=np.array([0.2, -0.3, 0.1, 0.4, 0., 0.2]),
                  pi=.5, scope=(0,), probe_order=(3, 1, 0), evidence_cells=("a", "b"))
    program = C.Program("P", "gate", gates=("g",))
    fitted = C.Fitted(program, np.full(6, .02), states=np.array([[0], [1]]),
                      logprior=np.log([.5, .5]), mu=np.stack([-gate.beta / 2, gate.beta / 2]),
                      version="released-history", cells=("a", "b"), gate_ids=("g",), gates={"g": gate},
                      definition_key=program.key({"g": gate}))
    row = {"base": [0.5] * 6, "pool": [True] * 6, "probes": [3], "values": [.7]}
    original = A.replay([fitted], row)
    digest = A.save_fits(tmp_path / "actual.npz", [fitted])
    monkeypatch.setattr(C, "fit_program", lambda *a, **k: (_ for _ in ()).throw(AssertionError("refit forbidden")))
    loaded = A.load_fits(tmp_path / "actual.npz")
    assert A.replay(loaded, row) == original
    assert loaded[0].gates["g"].identity() == gate.identity()
    assert loaded[0].definition_key == fitted.definition_key
    assert A.gate_programs(loaded) == A.gate_programs([fitted])
    assert A.file_hash(tmp_path / "actual.npz") == digest


def test_repair_verifier_refuses_empty_run(tmp_path):
    assert V.verify_run(tmp_path)["status"] == "INCOMPLETE"
