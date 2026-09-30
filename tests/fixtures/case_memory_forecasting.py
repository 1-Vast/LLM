"""Shared condition-labelled synthetic cases for forecasting and orchestration tests."""
from __future__ import annotations

from maestro import problem_compiler as PC
from maestro import case_memory as CM
from maestro import adaptive_retrieval as DR
from maestro import hypothesis_forecast as HF
from maestro.models import EvidenceAction, MechanismContrast, MechanismHypothesis


Q = CM.ScientificMeasurementStatus.QUALIFIED
H1, H2 = "response_realised", "response_not_realised"


def _sha(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _episode(case_id: str, direction: int, eliminated: tuple[str, ...] = (H2,),
             assay: str = "readout_measurement") -> CM.ScientificEpisode:
    updates = ()
    if eliminated:
        updates = (CM.HypothesisUpdate("a1", (H1, H2), "measured", eliminated, True),)
    return CM.ScientificEpisode(
        case_id=case_id, case_version=1, case_kind=CM.CaseKind.CANONICAL,
        problem_type="mechanism_contrast_transcriptomic", user_question="mechanism?",
        raw_data_references=(CM.RawDataRef("file:///state.npz", _sha(case_id), "prepared_state_table"),),
        data_quality_report={}, context_fingerprint={
            "dataset": "fixture", "assay": assay, "context": "fixture",
            "biological_system": "", "measurement_type": "", "control_design": "",
            "intervention_type": "", "time_h": 24.0},
        initial_observations=(CM.EpisodeObservation(
            "c1", Q, assay, cell_line="NCI-H596", dose_nM=500.0, time_h=24.0, readout="EGR1", value=2.0, direction=direction),),
        initial_hypotheses=(CM.HypothesisClaim(H1, "realised"), CM.HypothesisClaim(H2, "not realised")),
        hypothesis_graph={}, retrieved_cases=(), adaptation_map=(),
        candidate_actions=tuple(CM.CandidateAction(a, "assay", assay, 8.0, 2.0, "x",
                                                  cell_line="NCI-H596", time_h=24.0, dose_nM=500.0)
                                for a in ("measure_low", "measure_high")),
        virtual_cell_forecasts=(), predicted_outcome_branches=(), real_measurements=(),
        measurement_quality={}, qualified_evidence=(), hypothesis_updates=updates, next_action={},
        branching_interpretation_plan=(), final_decision={"status": "open", "basis": "fixture"},
        failure_modes=(), calibration_history=(),
        provenance={"builder": "test", "sources": "test", "created_at": "2026-09-29",
                    "data_origin": "synthetic"},
    )


def _store(episodes) -> CM.EpisodeStore:
    store = CM.EpisodeStore()
    # Two independently labelled synthetic strata. Merely listing a hypothesis is not evidence
    # that its conditional outcome distribution was observed.
    from dataclasses import replace
    for episode in episodes:
        if episode.real_measurements:
            store.append(episode)
            continue
        for h, label in ((H1, "match_h1"), (H2, "match_h2")):
            if episode.initial_observations[0].direction < 0:
                label = "unresolved"
            measurements = tuple(CM.RealMeasurement(
                a.action_id, Q, label, 1, "synthetic fixture", h, (H1, H2), sampling_frame="all_attempts")
                for a in episode.candidate_actions)
            store.append(replace(episode, case_id=episode.case_id + ":" + h,
                                 real_measurements=measurements))
    return store


def _contrast() -> MechanismContrast:
    return MechanismContrast("k1", (MechanismHypothesis(H1, "realised"),
                                    MechanismHypothesis(H2, "not realised")), (), None)


def _actions() -> tuple[EvidenceAction, ...]:
    return (EvidenceAction("measure_low", "low dose", 1.0, (H1, H2), time_hours=24.0),
            EvidenceAction("measure_high", "high dose", 1.0, (H1, H2), time_hours=24.0))


def _state(direction: int) -> HF.UserStateContext:
    return HF.UserStateContext(
        directional_state=DR.directional_state_from_shift({"EGR1": 2.0 * direction}),
        intervention_identity="drugA", cell_context="NCI-H596", time_h=24.0, dose_nM=500.0,
        assay="readout_measurement")


def _compiled_problem() -> PC.CompiledProblem:
    records = [
        PC.MeasurementRecord("r1", "EGR1", 2.0, "treated", Q, cell_line="NCI-H596",
                             time_value=24.0, time_unit="h", replicate_group="g1"),
        PC.MeasurementRecord("r2", "FOS", -1.0, "treated", Q, cell_line="NCI-H596",
                             time_value=24.0, time_unit="h", replicate_group="g1"),
        PC.MeasurementRecord("r3", "DMSO", 0.0, "control", Q, is_control=True),
    ]
    compiled = PC.compile_problem("user-1", "Is the response on-target?", records,
                              intervention="drugA", nominal_target="TARGET_A",
                              assay_hint="readout_measurement")
    from dataclasses import replace
    return replace(compiled, context={**compiled.context, "outcome_mode": "attempted_experiment"})
