"""Backend construction, composite routing and compute accounting."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Mapping, Protocol, Sequence
from .interface import ModelCapabilities, PredictionRequest, QueryAssessment, QuerySupport, StatePrediction, safe_predict
from .state_adapter import DEFAULT_MODEL_VERSION, StateAdapterConfig, StateCapabilityAdapter


class WorldModelRung(Protocol):
    """One swappable predictor behind the shared contract."""

    name: str

    def capabilities(self) -> ModelCapabilities: ...

    def assess_query(self, request: PredictionRequest) -> QueryAssessment: ...

    def predict(self, request: PredictionRequest) -> StatePrediction: ...


@dataclass
class SimulationCostLedger:
    """Compute accounting kept strictly separate from experiment budget.

    Simulation is cheap and repeatable; buying a real result is neither. Mixing
    the two would let a policy look thrifty by simulating more instead of
    measuring.
    """

    cost_per_call: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cost_per_call", dict(self.cost_per_call))
        self.calls: dict[str, int] = {}
        self.abstentions: dict[str, int] = {}
        self.contract_violations: dict[str, int] = {}

    def record(self, name: str, *, abstained: bool, violation: bool) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1
        if abstained:
            self.abstentions[name] = self.abstentions.get(name, 0) + 1
        if violation:
            self.contract_violations[name] = self.contract_violations.get(name, 0) + 1

    def total_cost(self) -> float:
        return sum(self.cost_per_call.get(name, 1.0) * count for name, count in self.calls.items())

    def summary(self) -> dict[str, object]:
        return {
            "calls": dict(self.calls),
            "abstentions": dict(self.abstentions),
            "contract_violations": dict(self.contract_violations),
            "compute_cost": self.total_cost(),
        }


class CompositeWorldModel:
    """Try rungs in ladder order; never let a broken prediction leak through."""

    def __init__(
        self,
        rungs: Sequence[WorldModelRung],
        *,
        ledger: SimulationCostLedger | None = None,
        enforce_contract: bool = True,
    ):
        if not rungs:
            raise ValueError("A composite world model needs at least one rung.")
        # Routing, the compute ledger and every receipt identify a backend by
        # its name. Discovering a missing one halfway through a routing report
        # produced an AttributeError instead of a verdict, so the requirement is
        # checked here, where it can name the offending backend.
        seen: set[str] = set()
        for index, rung in enumerate(rungs):
            name = getattr(rung, "name", None)
            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    f"World-model rung {index} ({type(rung).__name__}) has no usable 'name'; "
                    "routing and cost accounting identify backends by name."
                )
            if name in seen:
                raise ValueError(f"World-model rung name '{name}' is registered twice.")
            seen.add(name)
        self._rungs = tuple(rungs)
        self._ledger = ledger or SimulationCostLedger()
        if not enforce_contract:
            raise ValueError("World-model contracts cannot be disabled.")
        self.last_rung: str | None = None

    @property
    def ledger(self) -> SimulationCostLedger:
        return self._ledger

    @property
    def name(self) -> str:
        """A composite is itself a rung, so it carries a name of its own."""

        return "composite[" + ",".join(rung.name for rung in self._rungs) + "]"

    def capabilities(self) -> ModelCapabilities:
        """The first rung's declaration, kept for the single-backend contract.

        Callers choosing among backends must use :meth:`catalog`: reporting one
        rung's capabilities for a composite describes the collection by its
        first member, which is how a viability backend became invisible behind
        a transcript one.
        """

        return self._rungs[0].capabilities()

    def catalog(self) -> tuple[ModelCapabilities, ...]:
        """Every registered backend's capability declaration, in registration order."""

        return tuple(rung.capabilities() for rung in self._rungs)

    def eligible_backends(self, request: PredictionRequest) -> tuple[WorldModelRung, ...]:
        """Every rung that supports this request, not merely the first one found.

        Eligibility is decided by each backend's own assessment of the actual
        request. Order is preserved so a caller can apply its own tie-break,
        but order no longer decides eligibility.
        """

        return tuple(
            rung
            for rung in self._rungs
            if rung.capabilities().model_version == request.model_version
            and rung.assess_query(request).support is QuerySupport.SUPPORTED
        )

    def routing_report(self, request: PredictionRequest) -> Mapping[str, object]:
        """Which backends were eligible, and why each of the others was not."""

        eligible: list[str] = []
        rejected: dict[str, list[str]] = {}
        for rung in self._rungs:
            if rung.capabilities().model_version != request.model_version:
                rejected[rung.name] = ["model_version_mismatch"]
                continue
            assessment = rung.assess_query(request)
            if assessment.support is QuerySupport.SUPPORTED:
                eligible.append(rung.name)
            else:
                rejected[rung.name] = [
                    *assessment.limitations,
                    *(f"missing_input:{item}" for item in assessment.missing_inputs),
                ] or [assessment.support.value]
        return {
            "requested_readouts": list(request.readouts),
            "registered_backends": [rung.name for rung in self._rungs],
            "eligible": eligible,
            "ineligible": rejected,
            "selected": eligible[0] if eligible else None,
            "selection_rule": "first eligible backend in registration order",
        }

    def predict_all(self, request: PredictionRequest) -> tuple[tuple[str, StatePrediction], ...]:
        """Every eligible backend's prediction, kept separate.

        Disagreement between eligible models is information. Averaging it away
        would invent a consensus none of them produced, and averaging unlike
        quantities or latent coordinates would not even be arithmetic on
        comparable numbers.
        """

        results: list[tuple[str, StatePrediction]] = []
        for rung in self._rungs:
            # An explicit comparison binds the same biological query to each
            # catalog version separately; single-model predict never rebinds it.
            bound = replace(request, model_version=rung.capabilities().model_version)
            if rung.assess_query(bound).support is not QuerySupport.SUPPORTED:
                continue
            _, prediction = safe_predict(rung, bound)
            violation = prediction.abstain_reason == "contract_violation"
            self._ledger.record(rung.name, abstained=not prediction.applicable, violation=violation)
            results.append((rung.name, prediction))
        return tuple(results)

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        for rung in self._rungs:
            if rung.capabilities().model_version != request.model_version:
                continue
            assessment = rung.assess_query(request)
            if assessment.support is QuerySupport.SUPPORTED:
                return assessment
        return QueryAssessment(
            QuerySupport.UNSUPPORTED,
            (),
            ("no_rung_supports_this_query",),
            self._rungs[-1].capabilities(),
        )

    def predict(self, request: PredictionRequest) -> StatePrediction:
        for rung in self.eligible_backends(request):
            _, prediction = safe_predict(rung, request)
            self.last_rung = rung.name
            violation = prediction.abstain_reason == "contract_violation"
            self._ledger.record(rung.name, abstained=not prediction.applicable, violation=violation)
            return prediction
        self._ledger.record("none", abstained=True, violation=False)
        return StatePrediction(
            applicable=False,
            state_change=None,
            uncertainty=None,
            limitations=("No registered world-model rung supports this query.",),
            request_id=request.request_id,
            model_version=request.model_version,
            confidence=None,
            in_distribution=False,
            abstain_reason="no_supported_rung",
            compute_cost=0.0,
        )




BACKEND_CHOICES = ("none", "state", "development_mean", "composite", "sciplex_response")
SCIPLEX_LIBRARY = Path("data/virtual_cell/sciplex3_signature_library")


def build_backend(
    choice: str,
    *,
    workspace: Path,
    dataset_id: str = "tahoe_c39",
    development_partition: Path | None = None,
    artifact_directory: Path | None = None,
    model_version: str = DEFAULT_MODEL_VERSION,
    structures: dict[str, str] | None = None,
):
    """Return the requested backend, or ``None`` for the declared ``none`` choice."""

    if choice not in BACKEND_CHOICES:
        raise ValueError(f"Unknown backend '{choice}'; choose one of {', '.join(BACKEND_CHOICES)}.")
    if choice == "none":
        return None
    if choice == "sciplex_response":
        if not structures:
            raise ValueError("The sciplex_response backend requires declared structures (identifier to SMILES).")
        from .signature_retrieval import ResponseRungConfig, SciPlexResponseRung

        directory = Path(workspace) / SCIPLEX_LIBRARY
        if not (directory / "calibration.json").is_file():
            raise ValueError(f"The sciplex_response backend needs its library and calibration under {SCIPLEX_LIBRARY}.")
        return SciPlexResponseRung(ResponseRungConfig(directory, directory / "calibration.json",
                                                      {str(k): str(v) for k, v in structures.items()}))
    backends = []
    if choice in ("state", "composite"):
        config = StateAdapterConfig.from_workspace(workspace, model_version=model_version)
        if artifact_directory is not None:
            config = replace(config, output_directory=artifact_directory)
        backends.append(StateCapabilityAdapter(config))
    if choice in ("development_mean", "composite"):
        if development_partition is None:
            raise ValueError("The development_mean backend requires a declared development partition.")
        from .ladder import fit_development_mean_baseline, load_partition
        from .state_adapter import load_registry

        registration = load_registry(workspace).datasets.get(dataset_id)
        if registration is None:
            raise ValueError(f"Dataset '{dataset_id}' is not registered.")
        backends.append(
            fit_development_mean_baseline(
                registration,
                load_partition(development_partition),
                artifact_directory=artifact_directory,
            )
        )
    return backends[0] if len(backends) == 1 else CompositeWorldModel(backends)
