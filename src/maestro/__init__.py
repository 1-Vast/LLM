"""MAESTRO's scientific core: mechanism contrasts and constrained repair.

File summary
- Path: src/maestro/__init__.py
- Purpose: Re-export the deterministic control, decision, outcome, repair, and provenance layers.
- Core points:
  - Models define evidence-bounded records; reliability tracks revocable prediction use.
  - `MAESTROAgent` constructs/checks/repairs contrasts; `DecisionEngine` emits bounded actions.
- Interfaces: `MAESTROAgent`, `DecisionEngine`, `RepairController`, `InterpretationTable`, model classes
- Depends on: maestro.contrast, maestro.decision, maestro.models, maestro.outcome, maestro.repair, maestro.provenance, maestro.reliability, maestro.selection
"""

from .contrast import MAESTROAgent
from .composition import PlanComposer, PlanEvaluation, composition_is_legal, rank_plans, unmet_prerequisites
from .decision import (
    DEFAULT_REQUIREMENTS,
    DecisionEngine,
    DevelopmentDecision,
    EvidenceRequirement,
)
from .models import (
    CompositionRule,
    ContrastCheck,
    DecisionStatus,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    EvidenceObservation,
    EvidenceScope,
    FunctionalInterventionProfile,
    GatedEvidencePlan,
    MeasurementStatus,
    MechanismContrast,
    MechanismDecision,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    PlanAuthorization,
    RepairKind,
    RepairProposal,
)
from .outcome import (
    INCOMPLETE_PERTURBATION_FACTOR,
    MODE_COMPARATOR_FIELD,
    MODE_DIFFERENCE_FIELD,
    MeasuredPremise,
    PHENOTYPE_FIELD_PREFIX,
    REALISATION_FIELD,
    SUFFICIENT_FUNCTION_FIELD,
    EvidenceState,
    InterpretationTable,
    OutcomeClass,
    OutcomeInterpretation,
    OutcomeRule,
    UpdateRecord,
    ValidatedEvidenceUpdate,
    admit_evidence,
    default_rules_for,
    scope_rank,
)
from .pharmacology import (
    BindingMeasurement,
    EngagementEstimate,
    EngagementProfile,
    ExposureCondition,
    engagement_profile,
    occupancy_from_kd,
)
from .judgment import JudgmentLedger, JudgmentScope, JudgmentSummary, ScoredJudgment, TypedJudgment
from .provenance import SourceCluster, SourceClusterIndex, build_index
from .reliability import PredictionReliabilityLedger, ReliabilitySummary, ScoredPrediction
from .repair import (
    EXPECTED_GAIN,
    RepairController,
    RepairLedger,
    RepairOutcome,
    RepairRecord,
)
from .selection import BudgetedEvidencePlan, BudgetedEvidenceSelector

__all__ = [
    "CompositionRule",
    "ContrastCheck",
    "BudgetedEvidencePlan",
    "BudgetedEvidenceSelector",
    "DecisionStatus",
    "DEFAULT_REQUIREMENTS",
    "DecisionEngine",
    "DevelopmentAction",
    "DevelopmentDecision",
    "EvidenceAction",
    "EvidenceActionKind",
    "EvidenceKind",
    "EvidenceObservation",
    "EvidenceRequirement",
    "EvidenceScope",
    "EvidenceState",
    "EXPECTED_GAIN",
    "FunctionalInterventionProfile",
    "GatedEvidencePlan",
    "PlanComposer",
    "PlanEvaluation",
    "PlanAuthorization",
    "InterpretationTable",
    "MAESTROAgent",
    "MeasurementStatus",
    "MechanismContrast",
    "MechanismDecision",
    "MechanismHypothesis",
    "NonDiscriminabilityReason",
    "OutcomeClass",
    "OutcomeInterpretation",
    "OutcomeRule",
    "JudgmentLedger",
    "JudgmentScope",
    "JudgmentSummary",
    "PredictionReliabilityLedger",
    "ReliabilitySummary",
    "RepairController",
    "RepairKind",
    "RepairLedger",
    "RepairOutcome",
    "RepairProposal",
    "RepairRecord",
    "ScoredPrediction",
    "SourceCluster",
    "SourceClusterIndex",
    "UpdateRecord",
    "ValidatedEvidenceUpdate",
    "admit_evidence",
    "build_index",
    "composition_is_legal",
    "default_rules_for",
    "rank_plans",
    "scope_rank",
    "unmet_prerequisites",
    "INCOMPLETE_PERTURBATION_FACTOR",
    "MODE_COMPARATOR_FIELD",
    "MODE_DIFFERENCE_FIELD",
    "MeasuredPremise",
    "PHENOTYPE_FIELD_PREFIX",
    "REALISATION_FIELD",
    "SUFFICIENT_FUNCTION_FIELD",
]
