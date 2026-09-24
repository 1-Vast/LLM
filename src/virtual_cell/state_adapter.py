"""Guarded adapter for invoking a pinned State checkpoint in ``maestro``.

File summary
- Path: src/virtual_cell/state_adapter.py
- Purpose: run the pretrained Arc State checkpoint behind the shared world-model
  contract, and refuse any query whose endpoint, context, controls, input
  schema, data asset or model version does not match what the checkpoint and
  the registered data actually are.
- Core points:
  - Every declared identifier is bound to a registered asset: a dataset id to a
    file with a recorded size and digest, its contexts and its control label; a
    control dataset id to the *same* asset as the treated rows, because State
    samples its basal cells from the file it is given.
  - Incompatible queries are rejected before any subprocess starts; the
    selected rows are then checked inside the State environment, where the
    declared context must contain both the perturbation and its controls.
  - Executability and validation are different answers. A runnable query
    reports ``UNKNOWN`` validation unless a registered receipt matches its
    endpoint, context and model version.
  - A prediction is a compact condition-level artifact with named or explicitly
    unresolved coordinates, digests, query rows and provenance. A bound scale
    calibration is applied at runtime and the raw values are kept beside it.
- Interfaces: `DatasetRegistration`, `VirtualCellRegistry`, `load_registry`,
  `StateAdapterConfig`, `StateCapabilityAdapter`, `file_sha256`.
- Depends on: src/virtual_cell/interface.py, applicability.py, receipts.py,
  calibration.py, artifacts.py, state_runner.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .applicability import SupportLevel, SupportRegistry, receipt_level
from .artifacts import load_feature_names, write_shift_artifact
from .calibration import ScaleCalibration
from .interface import (
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
)
from .receipts import ValidationReceipt

SHIFT_ENDPOINT = "x_hvg_perturbation_shift"
SHIFT_SUMMARIES = ("embedding_delta_l2", "mean_absolute_embedding_delta")
DEFAULT_MODEL_VERSION = "state_generalization_zeroshot_X_hvg"
_DIGESTS: dict[tuple[str, int, int], str] = {}
_INSPECTIONS: dict[tuple[str, ...], dict[str, object]] = {}
_INSPECTION_LIMIT = 256
_IDENTITY_HASH_LIMIT = 8 * 1024 * 1024


def file_sha256(path: Path) -> str:
    """SHA-256 of a file, cached per (path, size, modification time)."""

    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    cached = _DIGESTS.get(key)
    if cached is None:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 22), b""):
                digest.update(block)
        cached = digest.hexdigest()
        _DIGESTS[key] = cached
    return cached


def _argument_identity(argument: str) -> str:
    """Identify a path argument by what it is, not by where it currently sits.

    A small file is identified by digest, so an identical asset in another run
    directory is the same inspection input. A large one uses size and
    modification time instead: hashing a multi-gigabyte asset on every query
    would cost more than the subprocess the key exists to avoid.
    """

    path = Path(argument)
    try:
        stat = path.stat()
    except OSError:
        return argument
    if stat.st_size <= _IDENTITY_HASH_LIMIT:
        return f"{path.name}:{stat.st_size}:{file_sha256(path)}"
    return f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}"


def _inspection_key(command: Sequence[str]) -> tuple[str, ...]:
    """The inspect command as a cache key, with paths read as content identities.

    `--summary` is dropped: it says where the answer is written, so two queries
    that differ in nothing else share one inspection. The runner's own path is
    part of the key, so editing it invalidates every entry.
    """

    parts: list[str] = []
    skip_next = False
    for argument in command:
        if skip_next:
            skip_next = False
            continue
        if argument == "--summary":
            parts.append(argument)
            skip_next = True
            continue
        parts.append(_argument_identity(argument))
    return tuple(parts)


def _write_summary(path: Path, payload: Mapping[str, object]) -> None:
    """Write a runner summary in the same form the runner writes it."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True), encoding="utf-8")


def _is_the_running_interpreter(executable: Path | None) -> bool:
    """Whether the configured State interpreter is the one already running."""

    if executable is None:
        return False
    try:
        return Path(executable).resolve() == Path(sys.executable).resolve()
    except OSError:
        return False


def _load_runner_module():
    """Import the runner by path, so no console script or install step is needed."""

    path = Path(__file__).with_name("state_runner.py")
    spec = importlib.util.spec_from_file_location("maestro_state_runner", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the State runner from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class DatasetRegistration:
    """One registered data asset and the facts a query about it must agree with."""

    identifier: str
    path: Path
    sha256: str = ""
    size_bytes: int | None = None
    contexts: tuple[str, ...] = ()
    context_column: str = "cell_name"
    perturbation_column: str = "drugname_drugconc"
    control_label: str = "[('DMSO_TF', 0.0, 'uM')]"
    batch_column: str = "plate"
    embedding_key: str = "X_hvg"
    feature_count: int | None = None
    source: str = ""
    source_revision: str = ""
    exposure_hours: float | None = None
    feature_names_path: Path | None = None

    def incomplete_fields(self) -> tuple[str, ...]:
        """Registration facts that are absent, so the binding cannot be checked."""

        missing: list[str] = []
        if not self.sha256:
            missing.append("sha256")
        if self.size_bytes is None:
            missing.append("size_bytes")
        if not self.contexts:
            missing.append("contexts")
        if self.feature_count is None:
            missing.append("feature_count")
        return tuple(missing)


@dataclass(frozen=True)
class VirtualCellRegistry:
    """Datasets, model provenance, evaluation receipts and bound calibrations."""

    datasets: Mapping[str, DatasetRegistration]
    models: Mapping[str, Mapping[str, Any]]
    receipts: tuple[ValidationReceipt, ...] = ()
    scale_calibrations: tuple[ScaleCalibration, ...] = ()
    source_path: Path | None = None
    source_sha256: str | None = None

    def receipts_for(self, model_version: str) -> tuple[ValidationReceipt, ...]:
        return tuple(item for item in self.receipts if item.model_version in (None, model_version))

    def calibration_for(self, model_version: str) -> ScaleCalibration | None:
        return next((item for item in self.scale_calibrations if item.model_version == model_version), None)


def load_registry(workspace: Path, path: Path | None = None) -> VirtualCellRegistry:
    """Read the registry; a legacy path-only entry becomes an incomplete registration."""

    registry_path = path or workspace / "data" / "virtual_cell" / "registry.json"
    if not registry_path.is_file():
        return VirtualCellRegistry({}, {})
    raw = registry_path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    datasets: dict[str, DatasetRegistration] = {}
    for identifier, entry in dict(data.get("datasets", {})).items():
        if isinstance(entry, str):
            datasets[str(identifier)] = DatasetRegistration(
                identifier=str(identifier), path=workspace / entry, source="legacy path-only registration"
            )
            continue
        datasets[str(identifier)] = DatasetRegistration(
            identifier=str(identifier),
            path=workspace / str(entry["path"]),
            sha256=str(entry.get("sha256", "")),
            size_bytes=entry.get("size_bytes"),
            contexts=tuple(str(item) for item in entry.get("contexts", ())),
            context_column=str(entry.get("context_column", "cell_name")),
            perturbation_column=str(entry.get("perturbation_column", "drugname_drugconc")),
            control_label=str(entry.get("control_label", "[('DMSO_TF', 0.0, 'uM')]")),
            batch_column=str(entry.get("batch_column", "plate")),
            embedding_key=str(entry.get("embedding_key", "X_hvg")),
            feature_count=entry.get("feature_count"),
            source=str(entry.get("source", "")),
            source_revision=str(entry.get("source_revision", "")),
            exposure_hours=entry.get("exposure_hours"),
            feature_names_path=workspace / entry["feature_names"] if entry.get("feature_names") else None,
        )
    receipts = tuple(
        ValidationReceipt(**{key: tuple(value) if key == "caveats" else value for key, value in dict(item).items()})
        for item in data.get("receipts", ())
    )
    calibrations = tuple(
        ScaleCalibration(**{key: tuple(value) if key == "limitations" else value for key, value in dict(item).items()})
        for item in data.get("scale_calibrations", ())
    )
    return VirtualCellRegistry(
        datasets=datasets,
        models={str(key): dict(value) for key, value in dict(data.get("models", {})).items()},
        receipts=receipts,
        scale_calibrations=calibrations,
        source_path=registry_path,
        source_sha256=hashlib.sha256(raw).hexdigest(),
    )


@dataclass(frozen=True)
class StateAdapterConfig:
    checkpoint: Path
    config: Path
    model_version: str
    known_perturbations: frozenset[str] | None = None
    python_executable: Path | None = None
    dataset_paths: Mapping[str, Path] = field(default_factory=dict)
    output_directory: Path | None = None
    control_perturbation: str = "[('DMSO_TF', 0.0, 'uM')]"
    embedding_key: str = "X_hvg"
    perturbation_column: str = "drugname_drugconc"
    celltype_column: str = "cell_name"
    batch_column: str = "plate"
    timeout_seconds: float = 900.0
    support: SupportRegistry | None = None
    datasets: Mapping[str, DatasetRegistration] = field(default_factory=dict)
    input_dim: int | None = None
    # The coordinate identity of the checkpoint's *input* space, one entry per
    # input dimension and ``None`` where a coordinate was never identified. A
    # dataset can declare the right embedding key and the right feature count
    # and still be in a different basis, which every other check accepts; this
    # is the only field against which that can be detected.
    input_coordinate_names: tuple[str | None, ...] = ()
    served_readouts: tuple[str, ...] = (SHIFT_ENDPOINT, *SHIFT_SUMMARIES)
    validation_receipts: tuple[ValidationReceipt, ...] = ()
    scale_calibration: ScaleCalibration | None = None
    verify_asset_digests: bool = True
    # How the input/output validation runner is executed. "auto" runs it in this
    # interpreter when that interpreter is the configured State one -- same code,
    # same checks, without paying 6 s of imports in a fresh process -- and falls
    # back to a subprocess the moment the two differ. "subprocess" is the explicit
    # isolation path, "in_process" is the explicit in-process path.
    runner_mode: str = "auto"
    seed: int = 42
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def registration(self, identifier: str | None) -> DatasetRegistration | None:
        """The registered asset for an identifier; a bare legacy path is incomplete."""

        if not identifier:
            return None
        if identifier in self.datasets:
            return self.datasets[identifier]
        path = self.dataset_paths.get(identifier)
        if path is None:
            return None
        return DatasetRegistration(identifier=identifier, path=Path(path), source="legacy path-only registration")

    @classmethod
    def from_workspace(cls, workspace: Path, *, model_version: str = DEFAULT_MODEL_VERSION) -> "StateAdapterConfig":
        registry = load_registry(workspace)
        model = dict(registry.models.get(model_version, {}))
        directory = workspace / str(
            model.get("directory", "data/external/arc_state/weights/zeroshot/state_generalization_zeroshot_X_hvg")
        )
        configured_python = os.environ.get("MAESTRO_STATE_PYTHON")
        identity = model.get("input_coordinate_identity")
        coordinate_names: tuple[str | None, ...] = ()
        if identity:
            # Declared once per model version: the identity of the input space
            # this checkpoint was trained on. A dataset registered with the
            # right embedding key and the right feature count can still be in a
            # different basis, and this is the only fact that reveals it.
            coordinate_names, _ = load_feature_names(
                workspace / str(identity), int(model.get("input_dim") or 0)
            )
        return cls(
            checkpoint=directory / "checkpoints" / "final.ckpt",
            config=directory / "config.yaml",
            model_version=model_version,
            input_coordinate_names=coordinate_names,
            python_executable=Path(configured_python) if configured_python else Path(r"D:\anaconda\envs\maestro\python.exe"),
            dataset_paths={identifier: item.path for identifier, item in registry.datasets.items()},
            output_directory=workspace / "log" / "20260910" / "artifacts" / "state",
            datasets=registry.datasets,
            input_dim=model.get("input_dim"),
            validation_receipts=registry.receipts_for(model_version),
            scale_calibration=registry.calibration_for(model_version),
            provenance={key: value for key, value in model.items() if key != "directory"},
        )


def _feature_identity_problem(registration: DatasetRegistration) -> str | None:
    """Whether a registered coordinate-name file actually belongs to this asset.

    Coordinate names are verified against one file's bytes. Reusing them for a
    copy whose columns were reordered would label every coordinate with the
    wrong gene while every other check still passes, so the name file must name
    the digest of the asset it describes.
    """

    path = registration.feature_names_path
    if path is None:
        return None
    if not path.is_file():
        return f"feature_identity_missing:{registration.identifier}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return f"feature_identity_unreadable:{registration.identifier}"
    if payload.get("dataset_sha256") != registration.sha256:
        return f"feature_identity_not_bound_to_asset:{registration.identifier}"
    if registration.feature_count is not None and payload.get("feature_count") != registration.feature_count:
        return f"feature_identity_count_mismatch:{registration.identifier}"
    return None


def _input_basis_problem(config: "StateAdapterConfig", registration: DatasetRegistration) -> str | None:
    """Whether the asset's coordinates are the ones this checkpoint actually reads.

    A dataset can register the right embedding key and the right feature count
    and still store a *different basis* -- its own highly-variable-gene
    selection, for instance. Every other registered fact then agrees, the
    inference runs, and the prediction is computed from coordinates the
    checkpoint never saw. The model declares the identity of its input space;
    an asset that cannot be compared against it is reported as unverified
    rather than assumed to match, because assuming is what makes the failure
    silent.
    """

    declared = tuple(config.input_coordinate_names)
    if not declared:
        # Fail closed. A guard that passes when nothing is declared is not a guard,
        # and this was the exact silent path: with no declared input identity the
        # adapter accepted an asset whose coordinates were a different gene
        # selection, because every other registered fact -- embedding key, feature
        # count, context, control label, batch column -- agreed with it. A model that
        # declares no basis cannot be checked against one, so the query is refused by
        # name instead of being accepted unverified.
        return f"input_basis_undeclared:{registration.identifier}"
    try:
        names, _ = load_feature_names(registration.feature_names_path, len(declared))
    except (OSError, ValueError, json.JSONDecodeError):
        return f"input_basis_unreadable:{registration.identifier}"
    if all(name is None for name in names):
        return f"input_basis_unverified:{registration.identifier}"
    disagreeing = sum(
        1
        for expected, actual in zip(declared, names)
        if expected is not None and actual is not None and expected != actual
    )
    if disagreeing:
        return (
            f"input_basis_mismatch:{registration.identifier}:"
            f"{disagreeing}_of_{len(declared)}_coordinates_disagree"
        )
    return None


class StateCapabilityAdapter:
    """State inference that refuses what the checkpoint and the registered data are not."""

    def __init__(self, config: StateAdapterConfig):
        self._config = config

    @property
    def name(self) -> str:
        return f"arc_state:{self._config.model_version}"

    @property
    def config(self) -> StateAdapterConfig:
        return self._config

    def input_schema(self) -> str:
        return f"{self._config.embedding_key}:{self._config.input_dim}"

    def control_protocol(self, registration: DatasetRegistration) -> str:
        return (
            f"label={registration.control_label};pool=declared-context rows of the input asset;"
            f"basal=state tx infer sampling with replacement;seed={self._config.seed}"
        )

    def capabilities(self) -> ModelCapabilities:
        calibration = self._config.scale_calibration
        return ModelCapabilities(
            model_identifier="arc_state",
            model_version=self._config.model_version,
            input_representation=self.input_schema(),
            perturbation_representation="checkpoint perturbation map keyed by exact drug-condition label",
            supported_modes=("drug",),
            requires_matched_control=True,
            supports_dose=False,
            supports_time=False,
            calibration_basis=None if calibration is None else f"scale {calibration.scale:.4f}; {calibration.fitted_on}",
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        capabilities = self.capabilities()
        errors = request.validation_errors()
        if errors:
            return QueryAssessment(QuerySupport.UNSUPPORTED, (), errors, capabilities)
        missing, limitations = self._static_issues(request)
        if not missing and not limitations:
            payload = self._inspect(request)
            if not payload.get("valid"):
                limitations.extend(str(item) for item in payload.get("errors", ("State input inspection failed.",)))
        status: SupportLevel = SupportLevel.UNKNOWN
        notes: tuple[str, ...] = ()
        if not missing and not limitations:
            status, notes = self.validation_status(request)
        return QueryAssessment(
            support=QuerySupport.SUPPORTED if not missing and not limitations else QuerySupport.UNSUPPORTED,
            missing_inputs=tuple(missing),
            limitations=tuple(limitations),
            capabilities=capabilities,
            validation_status=status,
            validation_notes=notes,
        )

    def validation_status(self, request: PredictionRequest) -> tuple[SupportLevel, tuple[str, ...]]:
        """What registered receipts say about this endpoint, context and checkpoint."""

        receipts = self._config.validation_receipts
        if not receipts:
            return SupportLevel.UNKNOWN, ("no evaluation receipt is registered for this checkpoint",)
        level, problems = receipt_level(
            receipts,
            endpoints=tuple(request.readouts),
            context_identifier=request.context.identifier,
            model_version=self._config.model_version,
        )
        # The receipt floor means "no receipt matched this use". For a backend
        # with no observed-support table that is unknown, not observed support.
        if level is SupportLevel.OBSERVED_SUPPORT:
            return SupportLevel.UNKNOWN, problems
        return level, problems

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            return self._unsupported(request, assessment.limitations + assessment.missing_inputs)
        config = self._config
        registration = config.registration(request.context.dataset_id)
        assert registration is not None  # guaranteed by the static checks
        paths = self._paths(request)

        subset = self._run_runner(
            "subset", request, paths["subset_summary"], extra=("--subset-output", str(paths["subset"]))
        )
        if not subset.get("valid"):
            return self._unsupported(
                request, tuple(str(item) for item in subset.get("errors", ("query subset construction failed",)))
            )

        command = [
            str(config.python_executable), "-m", "state", "tx", "infer",
            "--adata", str(paths["subset"]),
            "--model-dir", str(config.config.parent),
            "--embed-key", config.embedding_key,
            "--pert-col", registration.perturbation_column,
            "--celltype-col", registration.context_column,
            "--batch-col", registration.batch_column,
            "--control-pert", registration.control_label,
            "--output", str(paths["output"]),
            "--seed", str(config.seed), "--quiet",
        ]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command, check=False, capture_output=True, text=True, timeout=config.timeout_seconds
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return self._unsupported(request, (f"State inference did not start or complete: {error}",))
        elapsed = time.perf_counter() - started
        paths["run_log"].write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            return self._unsupported(request, (f"State inference failed; inspect {paths['run_log']}",))

        validation = self._run_runner(
            "validate",
            request,
            paths["validation"],
            input_path=paths["subset"],
            output=paths["output"],
            extra=("--vector-output", str(paths["vector"])),
        )
        if not validation.get("valid"):
            return self._unsupported(
                request, tuple(str(item) for item in validation.get("errors", ("State output validation failed.",)))
            )

        raw = np.asarray(np.load(paths["vector"]), dtype=float)
        feature_names, identity_sha = load_feature_names(registration.feature_names_path, int(raw.shape[0]))
        calibration = config.scale_calibration
        protocol = self.control_protocol(registration)
        binding = (
            calibration.binding_mismatches(
                endpoint=SHIFT_ENDPOINT,
                context_identifier=request.context.identifier,
                model_version=config.model_version,
                input_schema=self.input_schema(),
                control_protocol=protocol,
            )
            if calibration is not None
            else ("no_scale_calibration_registered",)
        )
        calibrated = calibration.scale * raw if calibration is not None and not binding else None
        limitations = [
            "Planning-only State prediction of the transcript shift in X_hvg coordinates; it is not a measurement, "
            "not viability, not target engagement and not a mechanism verdict.",
            "Validation status: " + assessment.validation_status.value + ".",
        ]
        if calibrated is None:
            limitations.append(
                "No bound scale calibration was applied (" + ", ".join(binding) + "); magnitudes are raw model output."
            )
        provenance = {
            "backend": self.name,
            "model_version": config.model_version,
            "model_provenance": dict(config.provenance),
            "dataset_id": registration.identifier,
            "dataset_sha256": registration.sha256,
            "dataset_source": registration.source,
            "dataset_revision": registration.source_revision,
            "exposure_hours": registration.exposure_hours,
            "query_subset_sha256": subset.get("subset_sha256"),
            "query_row_ids_sha256": subset.get("row_ids_sha256"),
            "query_rows": {"control": subset.get("control_rows"), "perturbation": subset.get("perturbation_rows")},
            "query_plates": subset.get("plates"),
            "prediction_file_sha256": validation.get("output_sha256"),
            "control_protocol": protocol,
            "input_schema": self.input_schema(),
            "preprocessing": "registered obsm embedding used as stored; no transform applied by MAESTRO",
            "observation_function": "mean over predicted perturbation cells minus mean over predicted control cells",
            "command": command,
            "seed": config.seed,
            "wall_seconds": round(elapsed, 3),
            "scale_calibration": None
            if calibration is None
            else {
                "scale": calibration.scale,
                "fitted_on": calibration.fitted_on,
                "development_partition_sha256": calibration.development_partition_sha256,
                "binding_mismatches": list(binding),
                "applied": calibrated is not None,
            },
        }
        artifact_sha = write_shift_artifact(
            paths["artifact"],
            request_id=request.request_id,
            backend=self.name,
            model_version=config.model_version,
            endpoint=SHIFT_ENDPOINT,
            context_identifier=request.context.identifier,
            perturbation=request.intervention.identifier,
            control_label=registration.control_label,
            raw_vector=raw,
            calibrated_vector=calibrated,
            feature_names=feature_names,
            feature_identity_sha256=identity_sha,
            provenance=provenance,
            limitations=limitations,
        )
        summary = calibrated if calibrated is not None else raw
        return StatePrediction(
            applicable=True,
            state_change={
                "embedding_delta_l2": float(np.linalg.norm(summary)),
                "mean_absolute_embedding_delta": float(np.abs(summary).mean()),
                "raw_embedding_delta_l2": float(np.linalg.norm(raw)),
                "raw_mean_absolute_embedding_delta": float(np.abs(raw).mean()),
            },
            uncertainty=None,
            limitations=tuple(limitations),
            supported_variables=(SHIFT_ENDPOINT, *SHIFT_SUMMARIES),
            calibration_basis=None if calibrated is None else f"scale {calibration.scale:.4f}; {calibration.fitted_on}",
            request_id=request.request_id,
            model_version=config.model_version,
            artifact_ref=str(paths["artifact"]),
            intervals={},
            confidence=None,
            in_distribution=None,
            compute_cost=elapsed,
            artifact_sha256=artifact_sha,
            uncertainty_components={
                "predictor_randomness": "basal control cells are resampled with replacement under a fixed seed; "
                "seed-to-seed spread is measured in a separate invariance receipt and not propagated here",
                "measurement_noise": "not represented: the prediction has no observation-noise model",
                "batch_effects": "not represented: this checkpoint's batch encoder is disabled",
                "model_misspecification": "unquantified for this query; see the registered evaluation receipts",
                "training_overlap": "unknown for this context and perturbation; see the provenance receipt",
            },
        )

    def _static_issues(self, request: PredictionRequest) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        limitations: list[str] = []
        config = self._config
        if request.model_version != config.model_version:
            missing.append("matching model_version")
        if not config.checkpoint.is_file() or not config.config.is_file():
            missing.append("checkpoint and configuration files")
        if config.python_executable is None or not config.python_executable.is_file():
            missing.append("isolated maestro State Python environment")
        if request.intervention.mode not in self.capabilities().supported_modes:
            limitations.append("This checkpoint adapter only accepts declared drug perturbation conditions.")
        if not request.readouts:
            limitations.append("no_readout_requested")
        limitations.extend(
            f"readout_not_served:{readout}" for readout in request.readouts if readout not in config.served_readouts
        )

        registration = config.registration(request.context.dataset_id)
        if registration is None:
            missing.append("registered dataset_id")
        else:
            incomplete = registration.incomplete_fields()
            if incomplete:
                limitations.append(f"dataset_registration_incomplete:{registration.identifier}:{','.join(incomplete)}")
            if not registration.path.is_file():
                missing.append(f"dataset asset file for {registration.identifier}")
            elif registration.size_bytes is not None and registration.path.stat().st_size != registration.size_bytes:
                limitations.append(f"dataset_asset_size_mismatch:{registration.identifier}")
            elif config.verify_asset_digests and registration.sha256 and file_sha256(registration.path) != registration.sha256:
                limitations.append(f"dataset_asset_hash_mismatch:{registration.identifier}")
            identity_problem = _feature_identity_problem(registration)
            if identity_problem is not None:
                limitations.append(identity_problem)
            basis_problem = _input_basis_problem(config, registration)
            if basis_problem is not None:
                limitations.append(basis_problem)
            if registration.contexts and request.context.identifier not in registration.contexts:
                limitations.append(f"context_not_registered_for_dataset:{request.context.identifier}")
            if registration.embedding_key != config.embedding_key or (
                config.input_dim is not None
                and registration.feature_count is not None
                and registration.feature_count != config.input_dim
            ):
                limitations.append(
                    f"input_schema_mismatch:adapter reads {config.embedding_key} with {config.input_dim} features; "
                    f"dataset {registration.identifier} registers {registration.embedding_key} with "
                    f"{registration.feature_count}"
                )
            if request.intervention.identifier == registration.control_label:
                limitations.append("perturbation_is_the_control_label")

        control_identifier = request.context.control_dataset_id
        if not control_identifier:
            missing.append("matched control_dataset_id")
        else:
            control = config.registration(control_identifier)
            if control is None:
                limitations.append(f"control_dataset_unregistered:{control_identifier}")
            elif registration is not None and control.path.resolve() != registration.path.resolve():
                limitations.append(f"control_dataset_not_matched_to_input:{control_identifier}")

        if request.intervention.dose is not None or request.intervention.time_hours is not None:
            limitations.append(
                "Dose and time must be represented by the exact registered perturbation label, not unvalidated continuous State inputs."
            )
        if config.known_perturbations is not None and request.intervention.identifier not in config.known_perturbations:
            limitations.append("Unknown perturbations are rejected to prevent any fallback-to-control encoding.")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", request.request_id):
            limitations.append("request_id may only contain letters, digits, dot, underscore, and hyphen.")
        return missing, limitations

    def _inspect(self, request: PredictionRequest) -> dict[str, object]:
        paths = self._paths(request)
        return self._run_runner("inspect", request, paths["inspection"])

    def runs_runner_in_process(self) -> bool:
        """Whether the next runner call executes here rather than in a subprocess."""

        mode = self._config.runner_mode
        if mode == "in_process":
            return True
        if mode == "subprocess":
            return False
        return _is_the_running_interpreter(self._config.python_executable)

    def _run_runner_in_process(
        self, mode: str, arguments: Sequence[str], summary_path: Path
    ) -> dict[str, object]:
        """Run the same entry point here, with the same parsing and the same checks.

        This is the runner's own `main`, given the argument list the subprocess
        form would have used. It is only reached when the configured State
        interpreter *is* this interpreter, so nothing about which environment
        performs the check changes; what disappears is a fresh process that would
        import torch and anndata again for a few hundred milliseconds of work.
        """

        try:
            runner = _load_runner_module()
        except Exception as error:  # noqa: BLE001 - reported as a refusal, never raised
            return {"valid": False, "errors": [f"State runner could not be loaded: {error}"]}
        try:
            code = runner.main(list(arguments))
        except SystemExit as error:
            return {"valid": False, "errors": [f"State runner rejected the arguments: {error}"]}
        except Exception as error:  # noqa: BLE001
            return {"valid": False, "errors": [f"State runner raised: {type(error).__name__}: {error}"]}
        if not summary_path.is_file():
            return {"valid": False, "errors": [f"State runner returned {code} without a summary"]}
        try:
            return json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"valid": False, "errors": ["State runner produced invalid JSON."]}

    def _run_runner(
        self,
        mode: str,
        request: PredictionRequest,
        summary_path: Path,
        *,
        input_path: Path | None = None,
        output: Path | None = None,
        extra: tuple[str, ...] = (),
    ) -> dict[str, object]:
        config = self._config
        registration = config.registration(request.context.dataset_id)
        if registration is None:
            return {"valid": False, "errors": ["registered dataset_id"]}
        runner = Path(__file__).with_name("state_runner.py")
        arguments = [
            mode,
            "--input", str(input_path or registration.path),
            "--summary", str(summary_path),
            "--perturbation", request.intervention.identifier,
            "--control", registration.control_label,
            "--perturbation-column", registration.perturbation_column,
            "--embed-key", config.embedding_key,
            "--celltype-column", registration.context_column,
            "--batch-column", registration.batch_column,
            "--context-column", registration.context_column,
            "--context", request.context.identifier,
        ]
        if mode == "inspect":
            arguments.extend(("--perturbation-map", str(config.config.parent / "pert_onehot_map.pt")))
            if config.input_dim is not None:
                arguments.extend(("--expected-features", str(config.input_dim)))
        if output is not None:
            arguments.extend(("--output", str(output)))
        arguments.extend(extra)
        command = [str(config.python_executable), str(runner), *arguments]
        inspection_key = _inspection_key(command) if mode == "inspect" else None
        if inspection_key is not None:
            known = _INSPECTIONS.get(inspection_key)
            if known is not None:
                _write_summary(summary_path, known)
                return known
        summary_path.unlink(missing_ok=True)
        if self.runs_runner_in_process():
            payload = self._run_runner_in_process(mode, arguments, summary_path)
            if inspection_key is not None and payload.get("valid") and len(_INSPECTIONS) < _INSPECTION_LIMIT:
                _INSPECTIONS[inspection_key] = payload
            return payload
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=600.0)
        except (OSError, subprocess.TimeoutExpired) as error:
            return {"valid": False, "errors": [f"State validation runner failed: {error}"]}
        if not summary_path.is_file():
            tail = (completed.stderr or "").strip().splitlines()[-1:] or [""]
            return {"valid": False, "errors": [f"State runner returned {completed.returncode} without a summary: {tail[0]}"]}
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"valid": False, "errors": ["State validation runner produced invalid JSON."]}
        if inspection_key is not None and len(_INSPECTIONS) < _INSPECTION_LIMIT:
            _INSPECTIONS[inspection_key] = payload
        return payload

    def _paths(self, request: PredictionRequest) -> dict[str, Path]:
        output_directory = self._config.output_directory or self._config.config.parent / "maestro_artifacts"
        output_directory.mkdir(parents=True, exist_ok=True)
        stem = output_directory / request.request_id
        return {
            "subset": Path(f"{stem}.query.h5ad"),
            "subset_summary": Path(f"{stem}.query.json"),
            "output": Path(f"{stem}.predicted.h5ad"),
            "vector": Path(f"{stem}.shift.npy"),
            "artifact": Path(f"{stem}.shift.json"),
            "inspection": Path(f"{stem}.input.json"),
            "validation": Path(f"{stem}.output.json"),
            "run_log": Path(f"{stem}.state.log"),
        }

    @staticmethod
    def _unsupported(request: PredictionRequest, limitations: tuple[str, ...]) -> StatePrediction:
        return StatePrediction(
            applicable=False,
            state_change=None,
            uncertainty=None,
            limitations=limitations,
            request_id=request.request_id,
            model_version=request.model_version,
            confidence=None,
            in_distribution=False,
            abstain_reason="; ".join(limitations) or "state_query_unsupported",
            compute_cost=0.0,
        )
