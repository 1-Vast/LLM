"""Regression tests for the held-out splits the ladder is scored on.

File summary
- Path: tests/test_ladder_splits.py
- Purpose: pin what each split asks, so a split cannot be scored under a name that
  describes a different question.
- Core points:
  - `within_domain` is the interpolation sanity check: every (context, perturbation)
    entity is in the fit, and the held-out dose is interior. Holding out whole entities
    under this name made both dose-aware rungs abstain on every row it produced, which
    is a property of the split rather than of the models.
  - `leave_cell_line_out` and `leave_drug_out` hold out whole entities, where abstention
    is the correct behaviour and is expected.
- Interfaces: `test_within_domain_keeps_every_entity_in_the_fit()`,
  `test_within_domain_held_out_doses_are_interior()`,
  `test_dose_aware_rung_answers_within_domain_rows()`,
  `test_generalisation_splits_hold_out_whole_entities()`
- Depends on: virtual_cell.evaluation, virtual_cell.ladder, virtual_cell.interface
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from virtual_cell.evaluation import _split, _subset
from virtual_cell.interface import Intervention, PredictionRequest, SystemContext
from virtual_cell.ladder import LinearPerturbationBaseline, PerturbationTable


def _table() -> PerturbationTable:
    """Two contexts, three compounds, one dose series per pair, one short series."""

    rows = [
        ("A549", "alpha", 0.0), ("A549", "alpha", 1.0), ("A549", "alpha", 10.0), ("A549", "alpha", 100.0),
        ("A549", "beta", 0.0), ("A549", "beta", 1.0), ("A549", "beta", 10.0), ("A549", "beta", 100.0),
        ("A549", "gamma", 0.0), ("A549", "gamma", 10.0),
        ("MCF7", "alpha", 0.0), ("MCF7", "alpha", 1.0), ("MCF7", "alpha", 10.0), ("MCF7", "alpha", 100.0),
        ("MCF7", "beta", 0.0), ("MCF7", "beta", 1.0), ("MCF7", "beta", 10.0), ("MCF7", "beta", 100.0),
        ("MCF7", "gamma", 0.0), ("MCF7", "gamma", 10.0),
    ]
    values = [0.2 * index for index in range(len(rows))]
    return PerturbationTable(
        context_ids=tuple(row[0] for row in rows),
        perturbations=tuple(row[1] for row in rows),
        modes=("drug",) * len(rows),
        doses=tuple(row[2] for row in rows),
        # No time axis is declared: the fitted domain then carries no time range, which
        # is the state the SciPlex3 table is in.
        times=(float("nan"),) * len(rows),
        readouts=("proliferation_index",),
        values={"proliferation_index": tuple(values)},
        source="synthetic software fixture; not a biological record",
    )


def test_within_domain_keeps_every_entity_in_the_fit():
    table = _table()
    train, test = _split(table, "within_domain")
    assert test, "the interpolation check must score something"
    train_entities = {(table.context_ids[i], table.perturbations[i]) for i in train}
    test_entities = {(table.context_ids[i], table.perturbations[i]) for i in test}
    assert test_entities <= train_entities


def test_within_domain_held_out_doses_are_interior():
    table = _table()
    train, test = _split(table, "within_domain")
    train_doses: dict[tuple[str, str], list[float]] = {}
    for index in train:
        train_doses.setdefault((table.context_ids[index], table.perturbations[index]), []).append(
            float(table.doses[index])
        )
    for index in test:
        entity = (table.context_ids[index], table.perturbations[index])
        observed = train_doses[entity]
        assert min(observed) < float(table.doses[index]) < max(observed)


def test_dose_aware_rung_answers_within_domain_rows():
    """The bug this pins: an all-abstain split is not a within-domain split."""

    table = _table()
    train_index, test_index = _split(table, "within_domain")
    model = LinearPerturbationBaseline(_subset(table, train_index))
    test = _subset(table, test_index)
    abstained = 0
    for index in range(len(test.context_ids)):
        prediction = model.predict(
            PredictionRequest(
                request_id=f"split-test-{index}",
                case_id="split-test",
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
                    description="split test",
                    dataset_id="fixture",
                    control_dataset_id="fixture",
                ),
                readouts=("proliferation_index",),
                model_version=model.model_version,
            )
        )
        if not prediction.applicable:
            abstained += 1
            assert prediction.abstain_reason != "perturbation_unregistered"
    assert abstained == 0


def test_generalisation_splits_hold_out_whole_entities():
    table = _table()
    for mode, key in (("leave_cell_line_out", table.context_ids), ("leave_drug_out", table.perturbations)):
        train, test = _split(table, mode)
        held = {key[index] for index in test}
        seen = {key[index] for index in train}
        assert held and not (held & seen), mode
