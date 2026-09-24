"""Real engagement, phenotype and dependency records, with their own null model.

File summary
- Path: src/evaluation/engagement_sources.py
- Purpose: turn four local releases into the records an engagement case needs, keeping each
  quantity separate and each call backed by a measured null rather than by a chosen cut-off.
  The engagement asset is the living-cell arm of a proteome-wide thermal-stability screen;
  the phenotype, the dependency and the independent binding test come from three other
  releases, so a case never rests on one study.
- Core points:
  - The engagement call is calibrated on the release's own vehicle channels: the threshold
    is a quantile of the vehicle-versus-vehicle effect distribution, and the *measured*
    false-positive rate is reported on a held-out half of those vehicle groups with a
    one-sided Clopper-Pearson bound. Nothing here is a chosen significance level: the
    quantile follows the project's declared 95% convention and the error is measured.
  - A thermal-stability shift is its own quantity. It is not occupancy and not proximal
    activity, so it is typed `ENGAGEMENT_SHIFT` and cannot discharge a premise that asks
    for either of those.
  - A protein the screen did not quantify yields no record at all: the capability reports
    that it does not cover the entity, instead of returning a null effect as evidence of
    no engagement.
  - Every loader records the file digest it read, and the exposure concentration and
    duration are reported as undeclared where the local asset does not state them.
- Interfaces: `EngagementAsset`, `EngagementCall`, `NullModel`, `load_engagement_asset`,
  `load_gdsc2`, `Gdsc2Record`, `load_depmap_profile`, `DepMapProfile`, `load_kinobeads`,
  `KinobeadsRecord`, `clopper_pearson_upper`, `normalise_compound`
- Depends on: evaluation.xlsx, maestro.models (quantity typing only)
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from .xlsx import Workbook, sheet_digest

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

# The project's declared interval convention is 95% (Wilson and bootstrap intervals in
# `score_table.py`, the drug bootstrap in the State receipts). The engagement threshold
# inherits it rather than introducing a new significance level: a pre-specified protein is
# called engaged when its vehicle-referenced effect exceeds the 95th percentile of the
# vehicle-versus-vehicle effect distribution.
NULL_QUANTILE = 0.95
VEHICLE_PREFIX = "DMSO"
ENGAGEMENT_UNITS = "log2_pisa_vehicle_referenced_shift"
ENGAGEMENT_QUANTITY = "engagement_shift"


def normalise_compound(name: str) -> str:
    """Compound identity for cross-release matching: case and punctuation folded away.

    Local assets name the same compound as `MK-2206 (dihydrochloride)`, `MK-2206` and
    `MK2206`. No local release carries a structure identifier for every compound, and
    RDKit is absent, so identity is matched on the folded name and every unmatched name
    is reported rather than guessed.
    """

    stripped = re.sub(r"\(.*?\)", " ", name)
    return re.sub(r"[^a-z0-9]", "", stripped.lower())


def clopper_pearson_upper(successes: int, trials: int, *, confidence: float = 0.95) -> float | None:
    """One-sided upper confidence bound for a binomial rate, by bisection on the tail.

    Used for the measured false-positive rate of the engagement call: with zero
    exceedances on a held-out half the bound is what is reportable, and the point
    estimate of zero is not.
    """

    if trials <= 0:
        return None
    if successes >= trials:
        return 1.0
    alpha = 1.0 - confidence
    try:  # the exact bound is a beta quantile; scipy is part of the recorded environment
        from scipy.stats import beta

        return float(beta.ppf(confidence, successes + 1, trials - successes))
    except ImportError:  # pragma: no cover - the fallback is the same bound by bisection
        pass

    log_choose = math.lgamma(trials + 1)

    def log_tail(probability: float) -> float:
        # log P(X <= successes) under Binomial(trials, probability), summed in log space so
        # a hold-out of a hundred thousand vehicle samples cannot overflow a float.
        terms = [
            log_choose
            - math.lgamma(count + 1)
            - math.lgamma(trials - count + 1)
            + count * math.log(probability)
            + (trials - count) * math.log1p(-probability)
            for count in range(0, successes + 1)
        ]
        peak = max(terms)
        return peak + math.log(sum(math.exp(term - peak) for term in terms))

    low, high = 1e-15, 1.0 - 1e-15
    target = math.log(alpha)
    for _ in range(100):
        middle = (low + high) / 2.0
        if log_tail(middle) > target:
            low = middle
        else:
            high = middle
    return high


@dataclass(frozen=True)
class NullModel:
    """The measured vehicle-versus-vehicle distribution behind an engagement call."""

    quantile: float
    threshold: float
    vehicle_groups: int
    null_samples: int
    calibration_groups: tuple[str, ...]
    holdout_groups: tuple[str, ...]
    holdout_samples: int
    holdout_exceedances: int
    holdout_rate: float | None
    holdout_rate_upper_95: float | None

    def payload(self) -> Mapping[str, object]:
        return {
            "quantile": self.quantile,
            "threshold_absolute_log2": round(self.threshold, 6),
            "vehicle_groups": self.vehicle_groups,
            "null_samples": self.null_samples,
            "calibration_groups": list(self.calibration_groups),
            "holdout_groups": list(self.holdout_groups),
            "holdout_samples": self.holdout_samples,
            "holdout_exceedances": self.holdout_exceedances,
            "holdout_false_positive_rate": None if self.holdout_rate is None else round(self.holdout_rate, 8),
            "holdout_false_positive_rate_upper_95": (
                None if self.holdout_rate_upper_95 is None else round(self.holdout_rate_upper_95, 8)
            ),
            "basis": (
                "the threshold is the declared quantile of the pooled vehicle-versus-vehicle "
                "absolute effects on the calibration half of the vehicle groups; the rate is "
                "measured on the held-out half and bounded by a one-sided Clopper-Pearson interval"
            ),
        }


@dataclass(frozen=True)
class EngagementCall:
    """One pre-specified protein's engagement effect in one compound's channel pair."""

    compound: str
    entity: str
    protein_identifier: str
    effect_log2: float
    replicates: tuple[float, ...]
    engaged: bool
    rank_by_absolute_effect: int
    proteins_quantified: int

    def payload(self) -> Mapping[str, object]:
        return {
            "compound": self.compound,
            "entity": self.entity,
            "protein_identifier": self.protein_identifier,
            "effect_log2": round(self.effect_log2, 6),
            "replicates": [round(value, 6) for value in self.replicates],
            "engaged": self.engaged,
            "rank_by_absolute_effect": self.rank_by_absolute_effect,
            "proteins_quantified": self.proteins_quantified,
        }


@dataclass(frozen=True)
class EngagementAsset:
    """The living-cell engagement matrix, its null model and its provenance."""

    source: str
    path: Path
    sha256: str
    sheet: str
    context_identifier: str
    exposure_note: str
    compounds: tuple[str, ...]
    vehicle_groups: tuple[str, ...]
    proteins: tuple[str, ...]
    gene_symbols: Mapping[str, tuple[str, ...]]
    effects: Mapping[str, Mapping[str, tuple[float, ...]]]
    null: NullModel

    def covers(self, compound: str) -> bool:
        return normalise_compound(compound) in {normalise_compound(name) for name in self.compounds}

    def column_for(self, compound: str) -> str | None:
        folded = normalise_compound(compound)
        for name in self.compounds:
            if normalise_compound(name) == folded:
                return name
        return None

    def quantified(self, gene: str) -> tuple[str, ...]:
        return self.gene_symbols.get(gene, ())

    def call(self, compound: str, gene: str) -> EngagementCall | None:
        """The engagement call for one compound and one gene, or None when not covered."""

        column = self.column_for(compound)
        if column is None:
            return None
        identifiers = self.quantified(gene)
        if not identifiers:
            return None
        values = self.effects.get(column, {})
        candidates = [name for name in identifiers if name in values]
        if not candidates:
            return None
        # A gene with several quantified protein entries is scored on the entry with the
        # largest absolute effect, and the entry is named in the record.
        ordered = sorted(candidates, key=lambda name: (-abs(_mean(values[name])), name))
        chosen = ordered[0]
        replicates = values[chosen]
        effect = _mean(replicates)
        magnitudes = sorted((abs(_mean(pair)) for pair in values.values()), reverse=True)
        rank = magnitudes.index(abs(effect)) + 1
        return EngagementCall(
            compound=column,
            entity=gene,
            protein_identifier=chosen,
            effect_log2=effect,
            replicates=tuple(replicates),
            engaged=abs(effect) >= self.null.threshold,
            rank_by_absolute_effect=rank,
            proteins_quantified=len(values),
        )

    def engaged_genes(self, compound: str) -> tuple[tuple[str, float, int], ...]:
        """Every quantified gene whose effect crosses the measured null, with its rank."""

        column = self.column_for(compound)
        if column is None:
            return ()
        values = self.effects.get(column, {})
        by_gene: dict[str, float] = {}
        for identifier, replicates in values.items():
            gene = identifier.split("_")[0]
            effect = _mean(replicates)
            if abs(effect) > abs(by_gene.get(gene, 0.0)):
                by_gene[gene] = effect
        ordered = sorted(by_gene.items(), key=lambda item: -abs(item[1]))
        return tuple(
            (gene, effect, position + 1)
            for position, (gene, effect) in enumerate(ordered)
            if abs(effect) >= self.null.threshold
        )

    def provenance(self) -> Mapping[str, object]:
        return {
            "source": self.source,
            "path": self.path.as_posix(),
            "sha256": self.sha256,
            "sheet": self.sheet,
            "context_identifier": self.context_identifier,
            "exposure": self.exposure_note,
            "compounds": len(self.compounds),
            "vehicle_groups": len(self.vehicle_groups),
            "proteins_quantified": len(self.proteins),
            "quantity": ENGAGEMENT_QUANTITY,
            "units": ENGAGEMENT_UNITS,
            "null_model": self.null.payload(),
        }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise ValueError("a null model needs at least one sample")
    ordered = sorted(values)
    position = quantile * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[int(position)]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def load_engagement_asset(
    path: Path,
    *,
    member: str | None = None,
    sheet: str = "Cell-based data",
    source: str,
    context_identifier: str,
    exposure_note: str,
    quantile: float = NULL_QUANTILE,
) -> EngagementAsset:
    """Read one thermal-stability matrix and calibrate its call on its own vehicle channels.

    Columns are ``<label>_Log2FC_Rep<n>``; a label beginning with ``DMSO`` is a vehicle
    group, and every other label is a compound. Replicates are averaged inside a label,
    which is also how the null is built, so threshold and effect are the same statistic.
    ``member`` names the workbook inside a downloaded archive; the digest recorded is the
    archive's, which is the file whose provenance was recorded at download.
    """

    workbook = Workbook(path, member=member)
    rows = workbook.rows(sheet)
    header = next(rows)
    labels: dict[int, tuple[str, str]] = {}
    for position, value in enumerate(header):
        if position == 0 or not isinstance(value, str):
            continue
        match = re.match(r"^(?P<label>.+)_Log2FC_Rep(?P<replicate>\d+)$", value.strip())
        if match is None:
            continue
        labels[position] = (match.group("label").strip(), match.group("replicate"))
    if not labels:
        raise ValueError(f"{path.name}:{sheet} declares no '<label>_Log2FC_Rep<n>' columns.")
    per_label: dict[str, dict[str, list[float]]] = {}
    proteins: list[str] = []
    for row in rows:
        if not row or not isinstance(row[0], str):
            continue
        identifier = row[0].strip()
        proteins.append(identifier)
        for position, (label, _replicate) in labels.items():
            value = row[position] if position < len(row) else None
            if not isinstance(value, (int, float)):
                continue
            per_label.setdefault(label, {}).setdefault(identifier, []).append(float(value))
    workbook.close()

    vehicles = tuple(sorted(name for name in per_label if name.upper().startswith(VEHICLE_PREFIX)))
    compounds = tuple(sorted(name for name in per_label if name not in set(vehicles)))
    if len(vehicles) < 4:
        raise ValueError(f"{path.name}:{sheet} carries {len(vehicles)} vehicle groups; a split-half null needs at least four.")
    calibration = tuple(vehicles[index] for index in range(0, len(vehicles), 2))
    holdout = tuple(name for name in vehicles if name not in set(calibration))
    calibration_samples = [
        abs(_mean(values)) for name in calibration for values in per_label[name].values() if values
    ]
    threshold = _quantile(calibration_samples, quantile)
    holdout_samples = [
        abs(_mean(values)) for name in holdout for values in per_label[name].values() if values
    ]
    exceedances = sum(1 for value in holdout_samples if value >= threshold)
    null = NullModel(
        quantile=quantile,
        threshold=threshold,
        vehicle_groups=len(vehicles),
        null_samples=len(calibration_samples),
        calibration_groups=calibration,
        holdout_groups=holdout,
        holdout_samples=len(holdout_samples),
        holdout_exceedances=exceedances,
        holdout_rate=exceedances / len(holdout_samples) if holdout_samples else None,
        holdout_rate_upper_95=clopper_pearson_upper(exceedances, len(holdout_samples)),
    )
    symbols: dict[str, list[str]] = {}
    for identifier in proteins:
        symbols.setdefault(identifier.split("_")[0], []).append(identifier)
    return EngagementAsset(
        source=source,
        path=Path(path),
        sha256=sheet_digest(path),
        sheet=f"{member}:{sheet}" if member else sheet,
        context_identifier=context_identifier,
        exposure_note=exposure_note,
        compounds=compounds,
        vehicle_groups=vehicles,
        proteins=tuple(proteins),
        gene_symbols={gene: tuple(values) for gene, values in symbols.items()},
        effects={
            label: {identifier: tuple(values) for identifier, values in entries.items()}
            for label, entries in per_label.items()
        },
        null=null,
    )


@dataclass(frozen=True)
class Gdsc2Record:
    """One fitted GDSC2 dose-response curve for one drug in one cell line."""

    dataset: str
    cell_line: str
    sanger_model_id: str
    cosmic_id: str
    drug_id: str
    drug_name: str
    putative_target: str
    pathway: str
    minimum_concentration: float
    maximum_concentration: float
    ln_ic50: float
    auc: float
    rmse: float
    z_score: float

    @property
    def ic50_micromolar(self) -> float:
        return math.exp(self.ln_ic50)

    @property
    def within_tested_range(self) -> bool:
        """The release's own reading of an active curve: IC50 inside the screened range.

        GDSC fits extrapolate beyond the tested concentrations, so the release reports
        MIN_CONC and MAX_CONC beside LN_IC50. A fitted IC50 above the maximum screened
        concentration is an extrapolation, which is why it is the release's own boundary
        that decides activity here rather than a threshold chosen for this package.
        """

        return self.ic50_micromolar <= self.maximum_concentration + 1e-12

    def source_id(self) -> str:
        return (
            "GDSC2-8.5:GDSC2_fitted_dose_response_27Oct23.xlsx:"
            f"{self.sanger_model_id}:{self.drug_id}:{self.drug_name}"
        )

    def payload(self) -> Mapping[str, object]:
        return {
            "cell_line": self.cell_line,
            "sanger_model_id": self.sanger_model_id,
            "cosmic_id": self.cosmic_id,
            "drug_id": self.drug_id,
            "drug_name": self.drug_name,
            "putative_target": self.putative_target,
            "pathway": self.pathway,
            "ln_ic50": round(self.ln_ic50, 6),
            "ic50_micromolar": round(self.ic50_micromolar, 6),
            "auc": round(self.auc, 6),
            "rmse": round(self.rmse, 6),
            "z_score": round(self.z_score, 6),
            "minimum_concentration_micromolar": self.minimum_concentration,
            "maximum_concentration_micromolar": self.maximum_concentration,
            "ic50_within_tested_range": self.within_tested_range,
        }


def load_gdsc2(path: Path, *, cell_lines: Sequence[str], cache: Path | None = None) -> tuple[Gdsc2Record, ...]:
    """Read the fitted GDSC2 curves for the named cell lines, with an optional local cache."""

    wanted = set(cell_lines)
    if cache is not None and cache.is_file():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        if set(payload.get("cell_lines", ())) == wanted and payload.get("sha256") == sheet_digest(path):
            return tuple(Gdsc2Record(**row) for row in payload["rows"])
    workbook = Workbook(path)
    rows = workbook.rows("Sheet 1")
    header = [str(value) for value in next(rows)]
    index = {name: position for position, name in enumerate(header)}
    records: list[Gdsc2Record] = []
    for row in rows:
        if len(row) <= index["CELL_LINE_NAME"]:
            continue
        name = row[index["CELL_LINE_NAME"]]
        if not isinstance(name, str) or name not in wanted:
            continue
        records.append(
            Gdsc2Record(
                dataset=str(row[index["DATASET"]]),
                cell_line=name,
                sanger_model_id=str(row[index["SANGER_MODEL_ID"]]),
                cosmic_id=str(row[index["COSMIC_ID"]]),
                drug_id=str(row[index["DRUG_ID"]]),
                drug_name=str(row[index["DRUG_NAME"]]),
                putative_target=str(row[index["PUTATIVE_TARGET"]]),
                pathway=str(row[index["PATHWAY_NAME"]]),
                minimum_concentration=float(row[index["MIN_CONC"]]),
                maximum_concentration=float(row[index["MAX_CONC"]]),
                ln_ic50=float(row[index["LN_IC50"]]),
                auc=float(row[index["AUC"]]),
                rmse=float(row[index["RMSE"]]),
                z_score=float(row[index["Z_SCORE"]]),
            )
        )
    workbook.close()
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                {
                    "cell_lines": sorted(wanted),
                    "sha256": sheet_digest(path),
                    "rows": [record.__dict__ for record in records],
                },
                indent=1,
            ),
            encoding="utf-8",
        )
    return tuple(records)


@dataclass(frozen=True)
class DepMapProfile:
    """One model's gene-effect and expression values, plus panel-wide dependency fractions."""

    model_id: str
    cell_line: str
    gene_effect: Mapping[str, float]
    expression: Mapping[str, float]
    dependent_fraction: Mapping[str, float] = field(default_factory=dict)
    digests: Mapping[str, str] = field(default_factory=dict)

    def effect(self, gene: str) -> float | None:
        return self.gene_effect.get(gene)

    def abundance(self, gene: str) -> float | None:
        return self.expression.get(gene)


def load_depmap_profile(
    *,
    directory: Path,
    model_id: str,
    cell_line: str,
    genes: Sequence[str] = (),
    dependency_threshold: float = -0.5,
    cache: Path | None = None,
) -> DepMapProfile:
    """Read one model's CRISPR and expression rows, and the panel fraction for named genes."""

    effect_path = directory / "CRISPRGeneEffect.csv"
    expression_path = directory / "OmicsExpressionProteinCodingGenesTPMLogp1.csv"
    key = f"{model_id}-{len(genes)}"
    if cache is not None and cache.is_file():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        if payload.get("key") == key:
            return DepMapProfile(
                model_id=model_id,
                cell_line=cell_line,
                gene_effect=payload["gene_effect"],
                expression=payload["expression"],
                dependent_fraction=payload["dependent_fraction"],
                digests=payload["digests"],
            )
    effects = _model_row(effect_path, model_id)
    expression = _model_row(expression_path, model_id)
    fractions = _dependent_fraction(effect_path, set(genes), dependency_threshold) if genes else {}
    profile = DepMapProfile(
        model_id=model_id,
        cell_line=cell_line,
        gene_effect=effects,
        expression=expression,
        dependent_fraction=fractions,
        digests={
            effect_path.name: sheet_digest(effect_path),
            expression_path.name: sheet_digest(expression_path),
        },
    )
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                {
                    "key": key,
                    "gene_effect": profile.gene_effect,
                    "expression": profile.expression,
                    "dependent_fraction": profile.dependent_fraction,
                    "digests": profile.digests,
                },
                indent=1,
            ),
            encoding="utf-8",
        )
    return profile


def _model_row(path: Path, model_id: str) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        genes = [column.split(" (")[0].strip() for column in header]
        for row in reader:
            if not row or row[0] != model_id:
                continue
            values: dict[str, float] = {}
            for position, raw in enumerate(row):
                if position == 0 or raw in ("", "NA", "NaN"):
                    continue
                try:
                    values[genes[position]] = float(raw)
                except ValueError:
                    continue
            return values
    raise ValueError(f"model '{model_id}' is absent from {path.name}")


def _dependent_fraction(path: Path, genes: set[str], threshold: float) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        columns: dict[str, int] = {}
        for position, column in enumerate(header):
            symbol = column.split(" (")[0].strip()
            if symbol in genes and symbol not in columns:
                columns[symbol] = position
        counts = {symbol: [0, 0] for symbol in columns}
        for row in reader:
            for symbol, position in columns.items():
                raw = row[position] if position < len(row) else ""
                if raw in ("", "NA", "NaN"):
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    continue
                counts[symbol][1] += 1
                if value <= threshold:
                    counts[symbol][0] += 1
    return {
        symbol: (hits / total)
        for symbol, (hits, total) in counts.items()
        if total
    }


@dataclass(frozen=True)
class KinobeadsRecord:
    """One competition-binding record from a cell-lysate kinobeads profile.

    This is deliberately never an engagement supplier: it is a foreign-lysate estimate,
    which the framework refuses for a direct in-context engagement premise. It is loaded
    only as an always-hidden independent test of an engagement-based decision.
    """

    compound: str
    gene: str
    apparent_kd_nanomolar: float | None
    classification: str
    lysate: str
    source_row: int

    def source_id(self) -> str:
        return f"Klaeger-2017:Klaeger_allTargets.xlsx:Kinobeads:row{self.source_row}:{self.compound}:{self.gene}"


def load_kinobeads(path: Path, *, compounds: Sequence[str] = ()) -> tuple[KinobeadsRecord, ...]:
    """Read the kinobeads target table, optionally restricted to named compounds."""

    wanted = {normalise_compound(name) for name in compounds} if compounds else None
    workbook = Workbook(path)
    rows = workbook.rows("Kinobeads")
    header = [str(value) if value is not None else "" for value in next(rows)]
    index = {name: position for position, name in enumerate(header)}
    records: list[KinobeadsRecord] = []
    for number, row in enumerate(rows, start=2):
        if len(row) <= index["Gene Name"]:
            continue
        compound = row[index["Drug"]]
        gene = row[index["Gene Name"]]
        if not isinstance(compound, str) or not isinstance(gene, str):
            continue
        if wanted is not None and normalise_compound(compound) not in wanted:
            continue
        raw = row[index["Apparent Kd"]] if index["Apparent Kd"] < len(row) else None
        records.append(
            KinobeadsRecord(
                compound=compound.strip(),
                gene=gene.strip(),
                apparent_kd_nanomolar=float(raw) if isinstance(raw, (int, float)) else None,
                classification=str(row[index["Target Classification"]]) if index["Target Classification"] < len(row) else "",
                lysate=str(row[index["Lysate"]]) if index["Lysate"] < len(row) else "",
                source_row=number,
            )
        )
    workbook.close()
    return tuple(records)
