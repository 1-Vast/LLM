"""Executable probes behind FRAMEWORK_GAPS.md (agent C, phase 1). Read-only on src/; temporary SQLite files only.

File summary
- Path: research/astra/mono_pretraining_20261005/decisions/framework_gap_probes.py
- Purpose: show, with the production classes imported unchanged, that the gaps G1, G4, G5, G6 of FRAMEWORK_GAPS.md are
  real behaviour and not a reading of the code: (G1) pair/orientation conditions are refused as unexpressible, (G2) a
  prediction for an unselected candidate cannot be stored, (G4) an already measured action identifier can be planned again
  and a verify action is accepted without any earlier screen, (G5) an import retry without a caller-supplied result id fails
  and one with it is idempotent, (G6) two distinct candidates with the same line/source/time/conditions collapse to one
  reliability record, and descriptive-interval scores never move the reliability weight.
- Run: PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/framework_gap_probes.py
- Writes nothing under the repository (temporary directory only); no network, no API.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from agent.case_store import CaseStore, MeasurementResult
from maestro.judgment import PredictionReliabilityLedger
from maestro.models import EvidenceAction
from virtual_cell.interface import Intervention, SystemContext


def action(identifier: str, conditions=None) -> EvidenceAction:
    return EvidenceAction(identifier=identifier, description=identifier, cost=1.0, distinguishes=(), time_hours=96.0,
                          expected_conditions=conditions or {"intervention": "A|B"}, prediction_readout="p_hit")


def result(identifier: str, result_id: str | None = None) -> MeasurementResult:
    return MeasurementResult(action_identifier=identifier, statement="screen", source_id="plate1", context_identifier="L1",
                             time_hours=96.0, independent_units=1, quality_passed=True,
                             conditions={"intervention": "A|B"}, metrics={"p_hit": "1"}, result_id=result_id)


def main() -> None:
    work = Path(tempfile.mkdtemp(prefix="gap_probes_"))
    out = {}
    # G1 pair/orientation conditions are refused by the prediction binding
    try:
        Intervention(identifier="A|B", mode="drug", intended_targets=("X",)).for_action(
            action("a1", {"orientation": "SV", "anchor_conc": "0.5"}), SystemContext("L1", "line"), ("p_hit",))
        out["G1"] = "accepted"
    except ValueError as error:
        out["G1"] = f"refused: {error}"
    # G4 / G5 / G2 on the authoritative case store
    store = CaseStore(work / "a.sqlite")
    store.open_case("c1", budget=10)
    store.record_plan("c1", [action("screen:A|B")], ready_to_measure=True, context_identifier="L1")
    store.import_measurement("c1", result("screen:A|B", "r1"))
    snap = store.record_plan("c1", [action("screen:A|B")], ready_to_measure=True, context_identifier="L1")
    out["G4_replan_measured_identifier"] = f"accepted, state={snap.state.value}, plan_version={snap.plan_version}"
    other = CaseStore(work / "b.sqlite")
    other.open_case("c2", budget=10)
    snap = other.record_plan("c2", [action("verify:X|Y")], ready_to_measure=True, context_identifier="L1")
    out["G4_verify_without_screen"] = f"accepted, state={snap.state.value}"
    try:
        other.record_prediction("c2", 1, "screen:unchosen", "req1", {"x": 1})
        out["G2"] = "stored"
    except ValueError as error:
        out["G2"] = f"refused: {error}"
    third = CaseStore(work / "c.sqlite")
    third.open_case("c3", budget=10)
    third.record_plan("c3", [action("screen:A|B")], ready_to_measure=True, context_identifier="L1")
    third.import_measurement("c3", result("screen:A|B"))
    try:
        third.import_measurement("c3", result("screen:A|B"))
        out["G5_retry_without_id"] = "accepted"
    except ValueError as error:
        out["G5_retry_without_id"] = f"refused: {error}"
    fourth = CaseStore(work / "d.sqlite")
    fourth.open_case("c4", budget=10)
    fourth.record_plan("c4", [action("screen:A|B")], ready_to_measure=True, context_identifier="L1")
    first = fourth.import_measurement("c4", result("screen:A|B", "fixed"))
    again = fourth.import_measurement("c4", result("screen:A|B", "fixed"))
    out["G5_retry_with_id"] = f"created={first.created}, then created={again.created}"
    # G6 reliability ledger
    ledger = PredictionReliabilityLedger()
    common = dict(model_version="m1", readout="p_hit", descriptive_interval=(0.0, 0.5), context_identifier="SIDM1",
                  source_cluster="plate1", time_hours=96.0, condition_fingerprint='{"intervention":"drugA"}')
    a = ledger.record_pair(predicted_value=0.2, realized_value=1.0, action_identifier="pair:A|B", result_id="r1", **common)
    b = ledger.record_pair(predicted_value=0.1, realized_value=0.0, action_identifier="pair:C|D", result_id="r2", **common)
    out["G6_dedup"] = f"records={len(ledger.records)}, second candidate returned the first record={b is a}"
    for i in range(10):
        ledger.record_pair(model_version="m2", readout="p_hit", predicted_value=0.2, realized_value=0.0,
                           descriptive_interval=(0.0, 0.1), context_identifier="L", result_id=f"x{i}",
                           source_cluster=f"p{i}", time_hours=96.0, condition_fingerprint=str(i))
    s = ledger.summarize("m2", "p_hit", "L")
    out["G6_descriptive_only"] = (f"scored={s.scored}, graded interval hits={s.interval_hits}, miss_rate={s.miss_rate}, "
                                  f"weight={s.weight}, provisional={s.provisional}, revoked={s.revoked}")
    for key, value in out.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
