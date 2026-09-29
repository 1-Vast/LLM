"""Shared schema and retrieval episode fixture for case-memory tests."""
from __future__ import annotations

from maestro import case_memory as CM

Q = CM.ScientificMeasurementStatus.QUALIFIED


def _sha(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _episode(case_id: str = "case-1", kind: CM.CaseKind = CM.CaseKind.CANONICAL,
             hypothesis_updates=(), observations=None, failures=(), adaptation=()) -> CM.ScientificEpisode:
    observations = observations if observations is not None else (
        CM.EpisodeObservation("cond-1", Q, "l1000", cell_line="A549", time_h=24.0, dose_nM=10000.0,
                              readout="gene:EGR1", value=2.1, direction=1, replicate_agreement=0.9),
    )
    return CM.ScientificEpisode(
        case_id=case_id, case_version=1, case_kind=kind,
        problem_type="mechanism_contrast_transcriptomic",
        user_question="Does the compound act through the nominal target?",
        raw_data_references=(CM.RawDataRef("file:///state.npz", _sha(case_id), "prepared_state_table"),),
        data_quality_report={"replicate_agreement_median": 0.9},
        context_fingerprint={"dataset": "l1000", "assay": "l1000", "context": "A549",
                             "biological_system": "l1000", "measurement_type": "transcriptomic",
                             "control_design": "vehicle", "intervention_type": "compound",
                             "cell_line": "A549", "time_h": 24.0, "dose_nM": 10000.0},
        initial_observations=observations,
        initial_hypotheses=(
            CM.HypothesisClaim("H_on", "on-target mechanism", predicted={"a1": "match_h1"}),
            CM.HypothesisClaim("H_off", "off-target mechanism", predicted={"a1": "match_h2"}),
            CM.HypothesisClaim("H_art", "assay artifact", advisory=True),
        ),
        hypothesis_graph={"nodes": 4, "edges": 3},
        retrieved_cases=(),
        adaptation_map=adaptation,
        candidate_actions=(
            CM.CandidateAction("a1", "transcriptomic repeat", "l1000", 8.0, 2.0, "signed_state_change"),
            CM.CandidateAction("a2", "orthogonal phenotype", "phenotypic", 24.0, 4.0, "phenotype"),
        ),
        virtual_cell_forecasts=(
            CM.ForecastRecord("a1", "H_on", {"match_h1": 0.7, "match_h2": 0.2, "unresolved": 0.1},
                              12, "case-memory-production-1", "test"),
        ),
        predicted_outcome_branches=(),
        real_measurements=(),
        measurement_quality={},
        qualified_evidence=(),
        hypothesis_updates=hypothesis_updates,
        next_action={},
        branching_interpretation_plan=(
            CM.BranchingPlan("a1", {"match_h1": "update:match_h1", "match_h2": "update:match_h2"},
                             "orthogonal:a2", "invalid:no_biological_hypothesis_update"),
        ),
        final_decision={"status": "open", "basis": "no real measurement yet"},
        failure_modes=failures,
        calibration_history=(),
        provenance={"builder": "test", "sources": "test", "created_at": "2026-09-29",
                    "data_origin": "real"},
    )
