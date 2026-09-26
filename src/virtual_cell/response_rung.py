"""A SciPlex3 transcriptional-response rung with coverage-checked intervals and pathway readouts.

File summary
- Path: src/virtual_cell/response_rung.py
- Purpose: serve planning-only predictions of a drug's 24 h transcriptional response in A549,
  K562 or MCF7 from its registered structure, only for readouts whose intervals were checked for
  coverage on held-out compounds and are narrower than the average-response baseline's.
- Core points:
  - The predictor is structure-nearest-neighbour retrieval over measured responses: the simplest
    arm that passed the 2026-09-26 audit's specificity rule, and the best arm on direction
    beyond the shared response. No arm there reached the anchor depth required for advisory
    ranking, so every prediction here stays planning-only.
  - A readout whose calibrated interval is no narrower than predicting the average drug's
    response carries no information about the compound and is refused by name. On 2026-09-26
    only the response magnitude passed; every Hallmark-program readout was refused.
  - A compound whose skeleton is in the reference library is refused: its measurement exists
    and must be used as a measurement, not re-served as a prediction.
  - Intervals are CALIBRATED only for readouts whose cross-conformal coverage receipt passed;
    every other readout carries a DESCRIPTIVE band, and the receipts decide the support level.
  - Structural novelty (maximum Tanimoto below the recorded threshold) sets in_distribution to
    False and selects the novel-compound calibration stratum.
- Interfaces: `ResponseRungConfig`, `SciPlexResponseRung`
- Depends on: interface.py, applicability.py, receipts.py, signature_retrieval.py; rdkit at runtime
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .applicability import SupportLevel, receipt_level
from .interface import (
    Interval,
    IntervalKind,
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
)
from .receipts import ValidationReceipt
from .signature_retrieval import SignatureLibrary, load_library

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
            split="five-fold cross-validation grouped by structure skeleton (185 units), SciPlex3 24 h",
            acceptance_criterion=(f"overall cross-conformal check passed (mean coverage of the {self.level:.2f} "
                                  f"interval in [0.75, 0.90], at least 90% of readouts at {floor:.2f} or above) and "
                                  f"this readout's held-out coverage is at least {floor:.2f}"),
            metric="interval_coverage", value=value, threshold=floor, passed=passed,
            holdout_verified=True, model_version=self.model_version, independent_units=185,
            caveats=("Coverage of a transcriptional readout; not a claim about engagement, viability or mechanism.",))

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
            if half is not None and receipt.validates(endpoint=readout, model_version=self.model_version):
                intervals[readout] = Interval(value - half, value + half, kind=IntervalKind.CALIBRATED, level=self.level,
                                              basis=f"cross-conformal residuals, stratum {stratum}; receipt {receipt.receipt_id}")
            elif half is not None:
                intervals[readout] = Interval(value - half, value + half, kind=IntervalKind.DESCRIPTIVE,
                                              basis=f"conformal residual quantile, stratum {stratum}; coverage receipt did not pass")
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
