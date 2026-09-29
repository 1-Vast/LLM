"""Recorded signature retrieval and the calibrated structure-based response backend."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
import numpy as np
from maestro.handoff import TOOL_SCHEMA_VERSION, json_loads, json_value, object_fields
from .applicability import SupportLevel, receipt_level, ValidationReceipt
from .interface import Interval, IntervalKind, ModelCapabilities, PredictionRequest, QueryAssessment, QuerySupport, StatePrediction


LIBRARY_SCHEMA = "maestro.virtual_cell.signature_library.v1"
DEFAULT_LIBRARY = Path("data/virtual_cell/sciplex3_signature_library")
MINIMUM_MATCHED_GENES = 200
NULL_DRAWS = 200


@dataclass(frozen=True)
class SignatureLibrary:
    """Measured, uncentered shifts per reference compound, line and dose, plus their metadata."""

    genes: tuple[str, ...]
    lines: tuple[str, ...]
    doses: tuple[float, ...]
    compounds: tuple[Mapping[str, str], ...]
    profiles: np.ndarray          # (entries, genes) log-expression shift against matched vehicle
    entry_compound: np.ndarray    # (entries,) index into compounds
    entry_line: np.ndarray        # (entries,) index into lines
    entry_dose: np.ndarray        # (entries,) index into doses
    systematic: np.ndarray        # (lines, doses, genes) mean shift over reference compounds
    metadata: Mapping[str, Any]

    def profile(self, compound: int, line: int, dose: int) -> np.ndarray | None:
        rows = np.flatnonzero((self.entry_compound == compound) & (self.entry_line == line) & (self.entry_dose == dose))
        return self.profiles[rows[0]] if len(rows) else None


def load_library(directory: Path) -> SignatureLibrary:
    """Load a library and refuse it when its arrays do not match their recorded digest."""

    directory = Path(directory)
    meta = json.loads((directory / "library.json").read_text(encoding="utf-8"))
    if meta.get("schema") != LIBRARY_SCHEMA:
        raise ValueError(f"signature_library_schema_unknown:{meta.get('schema')}")
    arrays = (directory / "library.npz").read_bytes()
    if hashlib.sha256(arrays).hexdigest() != meta.get("arrays_sha256"):
        raise ValueError("signature_library_digest_mismatch")
    data = np.load(directory / "library.npz", allow_pickle=False)
    return SignatureLibrary(
        genes=tuple(meta["genes"]), lines=tuple(meta["lines"]), doses=tuple(float(d) for d in meta["doses"]),
        compounds=tuple(meta["compounds"]), profiles=data["profiles"], entry_compound=data["entry_compound"],
        entry_line=data["entry_line"], entry_dose=data["entry_dose"], systematic=data["systematic"],
        metadata=meta)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / denominator) if denominator > 0 else 0.0


def retrieve(library: SignatureLibrary, query: Mapping[str, Any], *, top_k: int = 5, seed: int = 20260926) -> dict[str, Any]:
    """Rank reference classes by the best cosine similarity of their compounds to the query."""

    signatures = query["signatures"]
    excluded = {str(x).casefold() for x in query.get("exclude_reference_compounds", [])}
    rejected: list[dict[str, str]] = []
    gene_index = {g: i for i, g in enumerate(library.genes)}
    parts, used_lines, dose_notes = [], [], []
    shared = None
    for signature in signatures:
        line = signature["context"]
        if line not in library.lines:
            rejected.append({"context": line, "reason": f"context_not_in_library:{line}"})
            continue
        dose = float(signature["dose_nM"])
        if not math.isfinite(dose) or dose <= 0:
            rejected.append({"context": line, "reason": "dose_not_positive"})
            continue
        nearest = int(np.argmin([abs(math.log10(dose) - math.log10(d)) for d in library.doses]))
        if abs(math.log10(dose) - math.log10(library.doses[nearest])) > 1e-9:
            dose_notes.append(f"{line}: query dose {dose:g} nM compared at the nearest library dose "
                              f"{library.doses[nearest]:g} nM")
        values = signature["genes"]
        matched = {gene_index[g]: float(v) for g, v in values.items() if g in gene_index}
        if any(not math.isfinite(v) for v in matched.values()):
            raise ValueError("signature values must be finite")
        shared = set(matched) if shared is None else shared & set(matched)
        parts.append((library.lines.index(line), nearest, matched, bool(signature.get("centered", False))))
        used_lines.append(line)
    if not parts:
        return {"ranking": [], "nearest": [], "rejected": rejected or [{"reason": "no_usable_signature"}]}
    columns = np.array(sorted(shared or ()))
    if len(columns) < MINIMUM_MATCHED_GENES:
        rejected.append({"reason": f"too_few_library_genes_matched:{len(columns)}<{MINIMUM_MATCHED_GENES}"})
        return {"ranking": [], "nearest": [], "rejected": rejected, "genes_matched": int(len(columns))}
    query_vector = []
    for line, dose, matched, centered in parts:
        v = np.array([matched[c] for c in columns])
        query_vector.append(v if centered else v - library.systematic[line, dose, columns])
    q = np.concatenate(query_vector)
    references = []
    for index, compound in enumerate(library.compounds):
        if compound["name"].casefold() in excluded or compound.get("skeleton", "").casefold() in excluded:
            continue
        vectors = []
        for line, dose, _, _ in parts:
            profile = library.profile(index, line, dose)
            if profile is None:
                break
            vectors.append(profile[columns] - library.systematic[line, dose, columns])
        if len(vectors) == len(parts):
            references.append((compound, np.concatenate(vectors)))
    if not references:
        rejected.append({"reason": "no_reference_compound_covers_the_query_lines"})
        return {"ranking": [], "nearest": [], "rejected": rejected}
    matrix = np.stack([v for _, v in references])
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
    similarity = np.where(norms > 0, matrix @ q / np.maximum(norms, 1e-12), 0.0)
    order = np.argsort(-similarity)
    best: dict[str, tuple[float, str]] = {}
    for i in order:
        label = references[i][0]["class"]
        if label not in best:
            best[label] = (float(similarity[i]), references[i][0]["name"])
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(NULL_DRAWS):
        shuffled = q[rng.permutation(len(q))]
        null.append(float(np.max(matrix @ shuffled / np.maximum(np.linalg.norm(matrix, axis=1) * np.linalg.norm(shuffled), 1e-12))))
    threshold = float(np.quantile(null, 0.95))
    top = float(similarity[order[0]])
    return {
        "lines_compared": used_lines, "genes_matched": int(len(columns)), "reference_compounds": len(references),
        "ranking": [{"class": label, "best_cosine": round(value, 4), "best_reference": name}
                    for label, (value, name) in sorted(best.items(), key=lambda kv: -kv[1][0])[:top_k]],
        "nearest": [{"compound": references[i][0]["name"], "class": references[i][0]["class"],
                     "cosine": round(float(similarity[i]), 4)} for i in order[:top_k]],
        "permutation_null": {"draws": NULL_DRAWS, "max_cosine_q95": round(threshold, 4),
                             "best_above_null": top > threshold},
        "dose_notes": dose_notes, "rejected": rejected,
    }


def signature_retrieval(parameters: Mapping[str, Any], *, library_directory: Path | None = None,
                        workspace: Path | None = None) -> dict[str, Any]:
    """Tool entry: read a declared signature file and rank the reference classes it resembles."""

    object_fields(dict(parameters), {"dataset_path"}, set(), "parameters")
    path = Path(parameters["dataset_path"])
    data = json_loads(path.read_text(encoding="utf-8"))
    object_fields(data, {"schema_version", "signatures"}, {"exclude_reference_compounds", "top_k"}, "dataset")
    if data["schema_version"] != "1.0":
        raise ValueError("dataset schema_version must be 1.0")
    if not isinstance(data["signatures"], list) or not 1 <= len(data["signatures"]) <= 3:
        raise ValueError("signatures must list one to three per-line signatures")
    for signature in data["signatures"]:
        object_fields(signature, {"context", "dose_nM", "genes"}, {"centered"}, "signature")
        if not isinstance(signature["genes"], dict) or not signature["genes"]:
            raise ValueError("signature genes must be a nonempty object of symbol to shift")
    top_k = data.get("top_k", 5)
    if type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer from 1 to 20")
    root = Path(workspace) if workspace else Path(__file__).resolve().parents[2]
    directory = Path(library_directory) if library_directory else root / DEFAULT_LIBRARY
    if not (directory / "library.json").is_file():
        payload = {"ranking": [], "nearest": [], "rejected": [{"reason": "signature_library_missing"}]}
        library_meta: Mapping[str, Any] = {}
    else:
        library = load_library(directory)
        payload = retrieve(library, data, top_k=top_k)
        library_meta = library.metadata
    payload["library"] = {key: library_meta.get(key) for key in ("source", "validation", "created", "arrays_sha256")}
    payload["evidence_kind"] = "derived_analysis"
    payload["contradiction_flag"] = False
    observations = ([f"Most similar reference class: {payload['ranking'][0]['class']} "
                     f"(cosine {payload['ranking'][0]['best_cosine']})"] if payload.get("ranking") else
                    ["No ranking: " + "; ".join(r["reason"] for r in payload["rejected"])])
    limitations = [
        "Similarity of measured 24 h transcriptional responses in three cancer lines; not a mechanism, target "
        "engagement or viability claim.",
        "Classes are vendor annotations: similar responses arise from different targets, and a compound can act "
        "through several.",
        "A derived analysis of measurements; it cannot satisfy a measured premise or eliminate a hypothesis.",
    ]
    return json_value({"schema_version": TOOL_SCHEMA_VERSION, "payload": payload, "observations": observations,
                       "limitations": limitations, "artifacts": []})




NORM_READOUT = "transcript_shift_norm"


def _fingerprints(smiles: Sequence[str], bits: int = 2048) -> np.ndarray:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator

    RDLogger.DisableLog("rdApp.*")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=bits)
    rows = []
    for text in smiles:
        mol = Chem.MolFromSmiles(text) if isinstance(text, str) else None
        if mol is None:
            raise ValueError("structure_unparsable")
        rows.append(generator.GetFingerprintAsNumPy(mol).astype(np.float32))
    return np.asarray(rows)


def _skeleton(smiles: str) -> str:
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("structure_unparsable")
    fragments = Chem.GetMolFrags(mol, asMols=True)
    return Chem.MolToInchiKey(max(fragments, key=lambda m: m.GetNumHeavyAtoms())).split("-")[0]


@dataclass(frozen=True)
class ResponseRungConfig:
    """Where the rung's evidence lives and how it was calibrated."""

    library_directory: Path
    calibration_file: Path
    registrations: Mapping[str, str] = field(default_factory=dict)   # intervention identifier -> SMILES
    neighbours: int = 5
    novelty_threshold: float = 0.4
    time_hours: float = 24.0


class SciPlexResponseRung:
    """Structure-nearest-neighbour response prediction behind the shared world-model contract."""

    def __init__(self, config: ResponseRungConfig):
        self.config = config
        self.library: SignatureLibrary = load_library(config.library_directory)
        calibration = json.loads(Path(config.calibration_file).read_text(encoding="utf-8"))
        self.level = float(calibration["level"])
        self.quantiles: Mapping[str, Mapping[str, float | None]] = calibration["quantiles"]
        self.gene_sets: Mapping[str, Sequence[str]] = calibration["gene_sets"]
        self.coverage: Mapping[str, float] = calibration.get("coverage", {})
        self.acceptance = calibration.get("acceptance", {})
        # A readout whose calibrated interval is no narrower than the average-response baseline's
        # carries no information about the compound; it is refused rather than served.
        self.informative: Mapping[str, bool] = calibration["informative"]
        smiles = [c.get("smiles") for c in self.library.compounds]
        if any(not s for s in smiles):
            raise ValueError("signature_library_lacks_structures")
        self._fingerprints = _fingerprints(smiles)
        self._skeletons = {c["skeleton"] for c in self.library.compounds}
        gene_index = {g: i for i, g in enumerate(self.library.genes)}
        self._set_index = {f"hallmark:{name}": np.array([gene_index[g] for g in genes if g in gene_index])
                           for name, genes in self.gene_sets.items()}
        digest = hashlib.sha256()
        digest.update(str(self.library.metadata.get("arrays_sha256")).encode())
        digest.update(Path(config.calibration_file).read_bytes())
        self.model_version = "sciplex3_reference_response_" + digest.hexdigest()[:16]
        # The coverage receipts bind to the exact calibration file bytes they
        # were measured on; a rebuilt or edited file invalidates them by digest.
        self.calibration_sha256 = hashlib.sha256(Path(config.calibration_file).read_bytes()).hexdigest()
        self.receipts = tuple(self._receipt(readout) for readout in self.known_readouts)

    # ------------------------------------------------------------------ contract
    @property
    def name(self) -> str:
        return self.model_version

    @property
    def known_readouts(self) -> tuple[str, ...]:
        return (NORM_READOUT, *sorted(self._set_index))

    @property
    def served_readouts(self) -> tuple[str, ...]:
        return tuple(r for r in self.known_readouts if self.informative.get(r) is True)

    def _receipt(self, readout: str) -> ValidationReceipt:
        # The rule is the one written in research/biological_depth/calibration_spec.json before any
        # result was read: the overall check must pass, and this readout must reach the per-readout floor.
        floor = float(self.acceptance.get("per_readout_minimum", 0.70))
        overall = self.acceptance.get("overall_passed")
        value = self.coverage.get(readout)
        passed = None if value is None or overall is None else bool(overall and value >= floor)
        return ValidationReceipt(
            receipt_id=f"{self.model_version}:{readout}:cross_conformal",
            endpoint=readout,
            split="five-fold cross-validation grouped by structure skeleton (185 skeleton groups, "
                  "salts and stereoisomers of one molecule share a group), SciPlex3 24 h",
            acceptance_criterion=(f"overall cross-conformal check passed (mean coverage of the {self.level:.2f} "
                                  f"interval in [0.75, 0.90], at least 90% of readouts at {floor:.2f} or above) and "
                                  f"this readout's held-out coverage is at least {floor:.2f}"),
            metric="interval_coverage", value=value, threshold=floor, passed=passed,
            holdout_verified=True,
            holdout_basis=(
                "verified out-of-fold in the pre-registered calibration run "
                "(research/biological_depth/calibrate.py): folds are assigned at skeleton-group "
                "level, so a scored compound's own response entered neither its fold's training "
                "pool nor its fold's residual sample, and the acceptance rule was hashed in "
                "calibration_spec.json before any coverage was read. Not covered: any exposure of "
                "SciPlex3 to external pretraining, and the post-hoc informativeness width gate in "
                "build_rung_calibration.py, which was chosen after the widths were seen and can "
                "only withhold readouts, never widen a claim."
            ),
            model_version=self.model_version, independent_units=185,
            calibration_sha256=self.calibration_sha256, nominal_level=self.level,
            caveats=("Coverage of a transcriptional readout; not a claim about engagement, viability or mechanism.",
                     "Coverage is marginal over the measured condition grid; it does not assert coverage "
                     "after adaptive action selection on these predictions.",))

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="sciplex3_reference_response",
            model_version=self.model_version,
            input_representation="Morgan radius-2 2048-bit fingerprint of a registered structure, cell line and dose",
            perturbation_representation="registered SMILES",
            supported_modes=("drug",),
            requires_matched_control=True,
            supports_dose=True,
            supports_time=False,
            calibration_basis=f"cross-conformal residuals by compound fold at level {self.level:.2f}, "
                              "strata line x dose x structural novelty",
        )

    def _problems(self, request: PredictionRequest) -> tuple[list[str], list[str]]:
        missing, limitations = [], []
        if request.model_version != self.model_version:
            limitations.append("model_version_mismatch")
        intervention = request.intervention
        if intervention.mode != "drug":
            limitations.append(f"modality_unsupported:{intervention.mode}")
        if request.context.identifier not in self.library.lines:
            limitations.append(f"context_not_supported:{request.context.identifier}")
        if intervention.time_hours is None:
            missing.append("time_hours")
        elif abs(intervention.time_hours - self.config.time_hours) > 1e-9:
            limitations.append(f"time_not_supported:{intervention.time_hours:g}h")
        if intervention.dose is None:
            missing.append("dose")
        elif intervention.dose_unit != "nM":
            limitations.append(f"dose_unit_unsupported:{intervention.dose_unit}")
        elif not min(self.library.doses) <= intervention.dose <= max(self.library.doses):
            limitations.append("dose_outside_fitted_range")
        smiles = self.config.registrations.get(intervention.identifier)
        if smiles is None:
            missing.append("registered_structure")
        else:
            try:
                if _skeleton(smiles) in self._skeletons:
                    limitations.append("query_compound_in_reference_library:use_its_measurement")
            except ValueError:
                limitations.append("structure_unparsable")
        for readout in request.readouts:
            if readout not in self.known_readouts:
                limitations.append(f"readout_not_served:{readout}")
            elif readout not in self.served_readouts:
                limitations.append(f"readout_not_informative_beyond_average_response:{readout}")
        return missing, limitations

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        missing, limitations = self._problems(request)
        supported = not missing and not limitations
        status, notes = SupportLevel.UNKNOWN, ()
        if supported:
            wanted = [r for r in self.receipts if r.endpoint in request.readouts]
            level, notes = receipt_level(wanted, endpoints=tuple(request.readouts), model_version=self.model_version)
            status = level if all(r.validates(endpoint=r.endpoint, model_version=self.model_version)
                                  for r in wanted) else SupportLevel.EVALUATED_BELOW_ACCEPTANCE
        return QueryAssessment(QuerySupport.SUPPORTED if supported else QuerySupport.UNSUPPORTED,
                               tuple(missing), tuple(limitations), self.capabilities(), status, tuple(notes))

    # ------------------------------------------------------------------ prediction
    def _shift(self, fingerprint: np.ndarray, line: int, dose: float) -> tuple[np.ndarray, float]:
        inter = self._fingerprints @ fingerprint
        union = self._fingerprints.sum(1) + fingerprint.sum() - inter
        similarity = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        logs = np.log10(self.library.doses)
        position = float(np.clip(np.log10(dose), logs[0], logs[-1]))
        upper = int(min(np.searchsorted(logs, position), len(logs) - 1))
        lower = max(upper - 1, 0) if logs[upper] > position else upper
        weight = 0.0 if upper == lower else (position - logs[lower]) / (logs[upper] - logs[lower])

        def at(dose_index: int) -> np.ndarray:
            vectors, weights = [], []
            for j in np.argsort(-similarity):
                profile = self.library.profile(int(j), line, dose_index)
                if profile is not None:
                    vectors.append(profile)
                    weights.append(max(float(similarity[j]), 1e-6))
                if len(vectors) == self.config.neighbours:
                    break
            w = np.asarray(weights) / np.sum(weights)
            return np.tensordot(w, np.asarray(vectors), axes=1)

        vector = at(lower) if upper == lower else (1 - weight) * at(lower) + weight * at(upper)
        return vector, float(similarity.max())

    def predict(self, request: PredictionRequest) -> StatePrediction:
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            reason = "; ".join((*assessment.limitations, *(f"missing_input:{m}" for m in assessment.missing_inputs)))
            return StatePrediction(False, None, None, (reason or "out_of_domain",), request_id=request.request_id,
                                   model_version=self.model_version, in_distribution=False,
                                   abstain_reason=reason or "out_of_domain", compute_cost=0.0)
        line = self.library.lines.index(request.context.identifier)
        dose = float(request.intervention.dose)
        fingerprint = _fingerprints([self.config.registrations[request.intervention.identifier]])[0]
        vector, nearest = self._shift(fingerprint, line, dose)
        in_distribution = nearest >= self.config.novelty_threshold
        logs = np.log10(self.library.doses)
        stratum_dose = self.library.doses[int(np.argmin(np.abs(logs - math.log10(dose))))]
        stratum = f"{request.context.identifier}|{stratum_dose:g}|{'in' if in_distribution else 'novel'}"
        state_change, intervals = {}, {}
        for readout in request.readouts:
            value = float(np.linalg.norm(vector)) if readout == NORM_READOUT else float(vector[self._set_index[readout]].mean())
            state_change[readout] = value
            half = (self.quantiles.get(readout) or {}).get(stratum)
            receipt = next(r for r in self.receipts if r.endpoint == readout)
            qualified = not receipt.qualifies_coverage(
                calibration_sha256=self.calibration_sha256,
                nominal_level=self.level,
                endpoint=readout,
                model_version=self.model_version,
            )
            if half is not None and qualified:
                intervals[readout] = Interval(value - half, value + half, kind=IntervalKind.CALIBRATED, level=self.level,
                                              basis=f"cross-conformal residuals, stratum {stratum}; receipt {receipt.receipt_id}")
            elif half is not None:
                intervals[readout] = Interval(value - half, value + half, kind=IntervalKind.DESCRIPTIVE,
                                              basis=f"conformal residual quantile, stratum {stratum}; "
                                                    "no coverage receipt qualifies this readout")
        return StatePrediction(
            applicable=True, state_change=state_change,
            uncertainty=float(np.mean([i.width for i in intervals.values()])) if intervals else None,
            limitations=(
                "Planning-only prediction of a 24 h transcriptional response from structurally similar measured "
                "compounds; it is not a measurement and establishes no engagement, viability or mechanism.",
                f"Nearest reference similarity {nearest:.2f} (Tanimoto); below {self.config.novelty_threshold} "
                "the compound is structurally novel and the novel-compound calibration stratum applies.",
                "Between the four measured doses the response is interpolated in log dose; intervals use the "
                "nearer measured dose's calibration.",
            ),
            supported_variables=self.served_readouts, calibration_basis=self.capabilities().calibration_basis,
            request_id=request.request_id, model_version=self.model_version, intervals=intervals,
            confidence=None, in_distribution=bool(in_distribution), compute_cost=0.01,
            uncertainty_components={
                "neighbour_choice": "the k most similar measured compounds; a different k changes the answer",
                "measurement_noise": "carried by the reference measurements and covered by the conformal residuals",
                "structural_novelty": "handled by a separate calibration stratum, not extrapolated",
                "context_transfer": "none: only the three measured lines are served",
            },
        )
