"""Held-out evaluation of the world-model ladder on real data.

File summary
- Path: src/virtual_cell/evaluation.py
- Purpose: score the swappable rungs against held-out real measurements so the
  virtual cell is judged by calibration and action value, not by fit.
- Core points:
  - Leave-cell-line-out and leave-drug-out splits; never a random split only.
  - Reports interval coverage, width, MAE, Brier and log score per stratum.
  - Compares each rung to a naive mean predictor, the rung it must beat.
- Interfaces: `evaluate_ladder`, `LadderEvaluation`, `main`.
- Depends on: ladder.py, calibration.py, world_model.py
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from .calibration import CalibrationPair, compare_models, evaluate_exit_conditions, score, stratify
from .ladder import HierarchicalDoseResponseModel, LinearPerturbationBaseline, PerturbationTable
from .world_model import table_from_anndata


@dataclass(frozen=True)
class LadderEvaluation:
    split: str
    readout: str
    train_rows: int
    test_rows: int
    models: Mapping[str, dict[str, object]]
    verdicts: Mapping[str, str]
    notes: Mapping[str, object] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=True, indent=2, sort_keys=True)


def _split(table: PerturbationTable, mode: str, *, seed: int = 20260911) -> tuple[list[int], list[int]]:
    """Split by entity, never at random only; a random split hides extrapolation.

    ``within_domain`` is the interpolation sanity check: every (context, perturbation)
    entity stays in the fit, and one interior dose level per entity is held out, so the
    rows it is scored on are doses the entity's own training rows brace on both sides.
    Holding out whole entities under this name made it a leave-entity-out split in
    disguise -- both dose-aware rungs abstained on every row it produced, on 2026-09-11
    and again on 2026-09-19 -- which is a property of the split, not of the models.
    ``leave_dose_out`` removes one dose level of the entities that carry enough of them,
    and ``leave_cell_line_out`` and ``leave_drug_out`` are the generalisation tests,
    where a correctly behaving model is expected to abstain rather than to score well.
    """

    if mode == "within_domain":
        groups: dict[tuple[str, str], list[int]] = {}
        for index, pair in enumerate(zip(table.context_ids, table.perturbations)):
            groups.setdefault(pair, []).append(index)
        train: list[int] = []
        test: list[int] = []
        for pair in sorted(groups):
            indices = sorted(groups[pair], key=lambda index: table.doses[index])
            doses = sorted({float(table.doses[index]) for index in indices})
            if len(doses) < 3:
                # Fewer than three distinct doses leaves no interior level to hold out
                # without asking for an extrapolation the model should refuse.
                train.extend(indices)
                continue
            interior = doses[len(doses) // 2]
            train.extend(index for index in indices if float(table.doses[index]) != interior)
            test.extend(index for index in indices if float(table.doses[index]) == interior)
        return train, test
    if mode == "leave_dose_out":
        # Interpolation check: hold out one interior dose level per group so the
        # remaining points still brace it and the domain still contains it.
        groups: dict[tuple[str, str], list[int]] = {}
        for index, pair in enumerate(zip(table.context_ids, table.perturbations)):
            groups.setdefault(pair, []).append(index)
        train, test = [], []
        for indices in groups.values():
            ordered = sorted(indices, key=lambda index: table.doses[index])
            if len(ordered) < 4:
                train.extend(ordered)
                continue
            cut = len(ordered) // 2
            for position, index in enumerate(ordered):
                (test if position == cut else train).append(index)
        return train, test
    keys = list(table.context_ids) if mode == "leave_cell_line_out" else list(table.perturbations)
    held = sorted(set(keys))[: max(1, len(set(keys)) // 3)]
    train = [index for index, key in enumerate(keys) if key not in held]
    test = [index for index, key in enumerate(keys) if key in held]
    return train, test


def _subset(table: PerturbationTable, indices: Sequence[int]) -> PerturbationTable:
    return PerturbationTable(
        context_ids=tuple(table.context_ids[i] for i in indices),
        perturbations=tuple(table.perturbations[i] for i in indices),
        modes=tuple(table.modes[i] for i in indices),
        doses=tuple(table.doses[i] for i in indices),
        times=tuple(table.times[i] for i in indices),
        readouts=table.readouts,
        values={name: tuple(float(values[i]) for i in indices) for name, values in table.values.items()},
        source=table.source,
    )


def _naive_pairs(train: PerturbationTable, test: PerturbationTable, readout: str) -> list[CalibrationPair]:
    observed_train = [float(value) for value in train.values[readout]]
    mean = sum(observed_train) / len(observed_train)
    spread = (sum((value - mean) ** 2 for value in observed_train) / len(observed_train)) ** 0.5
    return [
        CalibrationPair(
            predicted=mean,
            low=mean - 1.645 * spread,
            high=mean + 1.645 * spread,
            observed=float(value),
            strata={"dose_bucket": _dose_bucket(dose)},
        )
        for dose, value in zip(test.doses, test.values[readout], strict=True)
    ]


def _dose_bucket(dose: float) -> str:
    if dose <= 0:
        return "control"
    if dose < 10:
        return "low"
    if dose < 1000:
        return "mid"
    return "high"


def evaluate_ladder(
    path: Path,
    *,
    split: str = "within_domain",
    readouts: Sequence[str] = ("proliferation_index",),
    max_cells: int = 200_000,
) -> LadderEvaluation:
    """Fit on one split, score on the other, and compare against a naive mean."""

    table = table_from_anndata(path, readout_columns=list(readouts), max_cells=max_cells)
    train_index, test_index = _split(table, split)
    if not train_index or not test_index:
        raise ValueError(f"Split '{split}' produced an empty side; the table is too small.")
    train, test = _subset(table, train_index), _subset(table, test_index)
    readout = table.readouts[0]
    notes = _fit_notes(train)

    # The one-hot arm is the control that makes the rest of this table readable: with
    # the dose axis removed, only entity identity remains, so the gap between it and
    # the dose-aware rungs is what the dose response is worth. Both behaviours on an
    # unseen entity are run, because they answer different questions -- abstention is
    # this framework's contract, and the training-mean fallback is what the published
    # one-hot models did under leave-drug-out.
    from .onehot_arm import OneHotIdentityBaseline

    rungs = {
        "naive_mean": None,
        "one_hot_identity": OneHotIdentityBaseline(train),
        "one_hot_identity_mean_fallback": OneHotIdentityBaseline(train, fall_back_to_training_mean=True),
        "linear_baseline": LinearPerturbationBaseline(train),
        "hierarchical_dose_response": HierarchicalDoseResponseModel(train, minimum_points=3),
    }
    reports: dict[str, dict[str, object]] = {}
    by_stratum: dict[str, dict[str, object]] = {}
    for name, model in rungs.items():
        if model is None:
            pairs = _naive_pairs(train, test, readout)
            abstained = 0
            abstain_reasons: dict[str, int] = {}
        else:
            pairs, abstained, abstain_reasons = _model_pairs(model, test, readout)
        report = score(pairs, probability_of=lambda pair: 1.0 / (1.0 + abs(pair.predicted)))
        reports[name] = {
            "pairs": report.pairs,
            "abstained": abstained,
            "abstention_rate": (abstained / len(test.doses)) if test.doses else None,
            "abstain_reasons": abstain_reasons,
            "interval_coverage": report.interval_coverage,
            "mean_interval_width": report.mean_interval_width,
            "mean_absolute_error": report.mean_absolute_error,
            "brier_score": report.brier_score,
            "log_score": report.log_score,
            "nominal_level": report.nominal_level,
            "exit_conditions": list(evaluate_exit_conditions(report)),
        }
        by_stratum[name] = stratify(pairs, "dose_bucket")

    candidate = {
        name: by_stratum[name]
        for name in (
            "one_hot_identity",
            "one_hot_identity_mean_fallback",
            "linear_baseline",
            "hierarchical_dose_response",
        )
    }
    verdicts = {
        name: compare_models(strata, by_stratum["naive_mean"])
        for name, strata in candidate.items()
    }
    return LadderEvaluation(
        split=split,
        readout=readout,
        train_rows=len(train_index),
        test_rows=len(test_index),
        models=reports,
        verdicts={name: json.dumps(value, sort_keys=True) for name, value in verdicts.items()},
        notes=notes,
    )


def _fit_notes(train: PerturbationTable) -> Mapping[str, object]:
    """Record why a rung may be unfittable, so an abstention is interpretable."""

    groups: dict[tuple[str, str], set[float]] = {}
    for context, perturbation, dose in zip(train.context_ids, train.perturbations, train.doses):
        groups.setdefault((context, perturbation), set()).add(float(dose))
    sizes = [len(doses) for doses in groups.values()]
    return {
        "minimum_dose_points_for_hill_curve": 4,
        "train_groups": len(sizes),
        "train_groups_with_insufficient_dose_points": sum(1 for size in sizes if size < 4),
        "median_dose_points_per_group": (sorted(sizes)[len(sizes) // 2] if sizes else 0),
    }


def _model_pairs(
    model, test: PerturbationTable, readout: str
) -> tuple[list[CalibrationPair], int, dict[str, int]]:
    """Return scored pairs plus the abstentions, which are a result, not a gap."""

    from .interface import Intervention, PredictionRequest, SystemContext

    pairs: list[CalibrationPair] = []
    abstained = 0
    reasons: dict[str, int] = {}
    for index in range(len(test.context_ids)):
        request = PredictionRequest(
            request_id=f"eval-{index}",
            case_id="evaluation",
            contrast_id="ladder",
            plan_version=1,
            intervention=Intervention(
                identifier=test.perturbations[index],
                mode="drug",
                intended_targets=(),
                dose=float(test.doses[index]),
                dose_unit="uM",
            ),
            context=SystemContext(
                identifier=test.context_ids[index],
                description="evaluation",
                dataset_id="evaluation",
                control_dataset_id="evaluation",
            ),
            readouts=(readout,),
            model_version=getattr(model, "model_version", "unknown"),
        )
        prediction = model.predict(request)
        if not prediction.applicable or readout not in prediction.state_change:
            abstained += 1
            reason = prediction.abstain_reason or "unsupported"
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        interval = prediction.intervals.get(readout)
        if interval is None:
            abstained += 1
            reasons["interval_missing"] = reasons.get("interval_missing", 0) + 1
            continue
        pairs.append(
            CalibrationPair(
                predicted=float(prediction.state_change[readout]),
                low=interval.low,
                high=interval.high,
                observed=float(test.values[readout][index]),
                strata={"dose_bucket": _dose_bucket(float(test.doses[index]))},
            )
        )
    return pairs, abstained, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the MAESTRO world-model ladder on held-out real data.")
    parser.add_argument("--adata", type=Path, default=Path("data/raw/sciplex3/sciplex_complete_middle_subset.h5ad"))
    parser.add_argument("--split", choices=("within_domain", "leave_dose_out", "leave_cell_line_out", "leave_drug_out"), default="within_domain")
    parser.add_argument("--readouts", nargs="+", default=["proliferation_index"])
    parser.add_argument("--max-cells", type=int, default=200_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    evaluation = evaluate_ladder(
        arguments.adata,
        split=arguments.split,
        readouts=tuple(arguments.readouts),
        max_cells=arguments.max_cells,
    )
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(evaluation.to_json(), encoding="utf-8")
    print(arguments.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
