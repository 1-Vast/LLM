"""Virtual-cell interfaces kept separate from MAESTRO's decision controller.

File summary
- Path: src/virtual_cell/__init__.py
- Purpose: export the world-model contract, the swappable ladder, calibration and
  the pinned State adapter.
- Core points:
  - The agent decides; the virtual cell only simulates.
  - Every predictor returns intervals plus confidence and an applicability flag.
  - Simulation is billed as compute, never as experiment budget.
- Interfaces: `PredictionRequest`, `StatePrediction`, `Interval`,
  `SupportRegistry`, `CalibrationReport`, `PerturbationTable`,
  `LinearPerturbationBaseline`, `HierarchicalDoseResponseModel`,
  `CompositeWorldModel`, `SimulationCostLedger`, `StateCapabilityAdapter`.
  `PredictionCache`, `ConditionPanel`, `run_panel`, `score_panel_gene_sets`, `rank_conditions`,
  `score_panel_against_observations`, `build_backend`.
- Depends on: maestro.models
"""

from .applicability import ApplicabilityVerdict, SupportLevel, SupportRecord, SupportRegistry
from .backends import BACKEND_CHOICES, build_backend
from .cache import PredictionCache
from .biology import (
    BackendDescription,
    BridgeModel,
    ChainSegment,
    Connector,
    ConnectorKind,
    MeasurementModel,
    Observable,
    UNIT_CONVERSIONS,
    UnitConversion,
)
from .calibration import (
    CalibrationPair,
    CalibrationReport,
    ScaleCalibration,
    compare_models,
    evaluate_exit_conditions,
    fit_scale,
    score,
    stratify,
)
from .pathway_readout import (
    BackgroundPool,
    ExpressivityAudit,
    GeneSet,
    StandardisedScore,
    expressivity_audit,
    load_background_pool,
    pathway_observable,
    score_gene_set,
    standardised_score,
)
from .receipts import ValidationReceipt
from .interface import (
    Interval,
    IntervalKind,
    Intervention,
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellQueryTemplate,
    UnavailableVirtualCellWorldModel,
    VirtualCellWorldModel,
)
from .ladder import (
    SHUFFLE_CONTROL,
    DevelopmentMeanShiftBaseline,
    HierarchicalDoseResponseModel,
    LinearPerturbationBaseline,
    PerturbationTable,
    shuffled,
)
from .panel import (
    ConditionPanel,
    KnowledgeAnnotation,
    PanelCondition,
    PanelCriterion,
    PanelGeneSetScore,
    PanelNotRanked,
    PanelRanking,
    PanelRankingEntry,
    PanelRow,
    PanelRun,
    execute_spec,
    load_panel_spec,
    rank_conditions,
    read_artifact_values,
    run_panel,
    score_panel_against_observations,
    score_panel_gene_sets,
)
from .state_adapter import (
    DatasetRegistration,
    StateAdapterConfig,
    StateCapabilityAdapter,
    VirtualCellRegistry,
    load_registry,
)
from .world_model import CompositeWorldModel, SimulationCostLedger, table_from_anndata

__all__ = [
    "ApplicabilityVerdict",
    "BACKEND_CHOICES",
    "BackendDescription",
    "BackgroundPool",
    "BridgeModel",
    "CalibrationPair",
    "CalibrationReport",
    "ChainSegment",
    "CompositeWorldModel",
    "ConditionPanel",
    "KnowledgeAnnotation",
    "Connector",
    "ConnectorKind",
    "DatasetRegistration",
    "DevelopmentMeanShiftBaseline",
    "ExpressivityAudit",
    "GeneSet",
    "MeasurementModel",
    "Observable",
    "ScaleCalibration",
    "SupportLevel",
    "UNIT_CONVERSIONS",
    "UnitConversion",
    "ValidationReceipt",
    "VirtualCellRegistry",
    "fit_scale",
    "load_background_pool",
    "load_registry",
    "HierarchicalDoseResponseModel",
    "Interval",
    "IntervalKind",
    "Intervention",
    "LinearPerturbationBaseline",
    "ModelCapabilities",
    "PanelCondition",
    "PanelCriterion",
    "PanelGeneSetScore",
    "PanelNotRanked",
    "PanelRanking",
    "PanelRankingEntry",
    "PanelRow",
    "PanelRun",
    "PerturbationTable",
    "PredictionCache",
    "PredictionRequest",
    "QueryAssessment",
    "QuerySupport",
    "SHUFFLE_CONTROL",
    "SimulationCostLedger",
    "StateAdapterConfig",
    "StateCapabilityAdapter",
    "StatePrediction",
    "SupportRecord",
    "SupportRegistry",
    "SystemContext",
    "UnavailableVirtualCellWorldModel",
    "VirtualCellQueryTemplate",
    "VirtualCellWorldModel",
    "compare_models",
    "build_backend",
    "evaluate_exit_conditions",
    "execute_spec",
    "load_panel_spec",
    "rank_conditions",
    "read_artifact_values",
    "run_panel",
    "safe_predict",
    "score",
    "score_panel_against_observations",
    "score_panel_gene_sets",
    "shuffled",
    "stratify",
    "table_from_anndata",
]
