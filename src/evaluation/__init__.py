"""Leakage-bounded retrospective case replay and baseline evaluation.

File summary
- Path: src/evaluation/__init__.py
- Purpose: Re-export replay cases, baseline policies, and the evaluation runner.
- Core points:
  - Frozen public cases are scored against hidden outcomes in an isolated runtime.
  - Baseline policies share MAESTRO's public menu for ablation comparison.
  - Laboratory-unit costing, the always-hidden final-test partition and the section 37 score table sit beside the licensing verdict.
- Interfaces: `EvaluationRunner`, `CaseRepository`, `MAESTROCorePolicy`, `build_evidence_base`, `build_cases`, `score_submission`, `build_score_table`, `load_costing_profile`, model classes
- Depends on: evaluation.baselines, evaluation.case_builder, evaluation.cases, evaluation.evidence_base, evaluation.lab_cost, evaluation.prediction_controls, evaluation.runner, evaluation.score_table, evaluation.scoring, evaluation.screening
"""

from .baselines import (
    ExpertWorkflowPolicy,
    LLMActionPolicy,
    MAESTROCorePolicy,
    MAESTROOrchestratorPolicy,
    PredictionValuePolicy,
    DecisionSubmission,
)
from .case_builder import CaseArchetype, ClassifiedCase, build_cases, write_cases
from .cases import (
    CaseRepository,
    FinalTestRecord,
    InitialEvidence,
    PublicCase,
    ReplayCase,
    ReplayEnvironment,
    RevealRefusal,
)
from .capabilities import (
    CapabilityOffer,
    CapabilityRegistry,
    CompiledRepair,
    ProposalRefusal,
    canonical_repair_identifier,
    compile_proposal,
    load_capability_registry,
)
from .engagement_sources import EngagementAsset, clopper_pearson_upper, load_engagement_asset
from .evidence_base import EvidenceBase, build_evidence_base
from .lab_cost import CostBasis, CostingProfile, LabCost, SequenceLabCost, SharedControl, load_costing_profile
from .prediction_controls import RemovedPredictionValuePolicy, ShuffledPredictionValuePolicy
from .adjudication import adjudication_packet, agreement, mechanical_verdict
from .llm_rows import ExplicitHypothesesLLMPolicy
from .proposal_arms import (
    LLMRegistryRepairPolicy,
    RegistryExpandedSelectionPolicy,
    RegistryRandomProposalPolicy,
    RegistryRepairRulePolicy,
)
from .provider_spend import SpendLedger, price_usage
from .voi_arm import SimpleModelVOIPolicy, fit_action_reliability
from .repair_replay import ProposalRecord, registry_extended_case, run_proposal_round
from .xlsx import Workbook
from .scoring import DecisionScore, DecisionVerdict, FinalTestVerdict, score_submission
from .runner import EvaluationReport, EvaluationRunner, PolicyResult, ReplayStep
from .score_table import build_score_table, exit_verdict
from .screening import CandidateAssessment, CandidateCase, assess_candidate, assess_registry, load_candidate_registry

__all__ = [
    "CandidateAssessment",
    "CandidateCase",
    "CapabilityOffer",
    "CapabilityRegistry",
    "CaseArchetype",
    "CaseRepository",
    "ClassifiedCase",
    "CompiledRepair",
    "CostBasis",
    "CostingProfile",
    "EngagementAsset",
    "DecisionScore",
    "DecisionSubmission",
    "DecisionVerdict",
    "EvaluationReport",
    "EvaluationRunner",
    "EvidenceBase",
    "ExpertWorkflowPolicy",
    "FinalTestRecord",
    "FinalTestVerdict",
    "InitialEvidence",
    "LLMActionPolicy",
    "LabCost",
    "MAESTROCorePolicy",
    "MAESTROOrchestratorPolicy",
    "ExplicitHypothesesLLMPolicy",
    "LLMRegistryRepairPolicy",
    "PolicyResult",
    "PredictionValuePolicy",
    "ProposalRecord",
    "ProposalRefusal",
    "PublicCase",
    "RegistryExpandedSelectionPolicy",
    "RegistryRandomProposalPolicy",
    "RegistryRepairRulePolicy",
    "RemovedPredictionValuePolicy",
    "ReplayCase",
    "ReplayEnvironment",
    "ReplayStep",
    "RevealRefusal",
    "Workbook",
    "SequenceLabCost",
    "SharedControl",
    "ShuffledPredictionValuePolicy",
    "SimpleModelVOIPolicy",
    "SpendLedger",
    "adjudication_packet",
    "agreement",
    "assess_candidate",
    "assess_registry",
    "build_cases",
    "build_evidence_base",
    "build_score_table",
    "canonical_repair_identifier",
    "clopper_pearson_upper",
    "compile_proposal",
    "exit_verdict",
    "fit_action_reliability",
    "load_candidate_registry",
    "load_capability_registry",
    "load_costing_profile",
    "load_engagement_asset",
    "mechanical_verdict",
    "price_usage",
    "registry_extended_case",
    "run_proposal_round",
    "score_submission",
    "write_cases",
]
