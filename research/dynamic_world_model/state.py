"""Minimal population-state, transition and scenario-card records for the measurement-choice study.

File summary
- Path: research/dynamic_world_model/state.py
- Purpose: the smallest state, transition and readout contract the study needed, kept in research
  because no component built on it met its promotion rule. A state is the population of one well
  at one time; every variable says whether it was measured, inferred from a measured variable,
  predicted by a model, or missing, and a state never claims to be the complete cell state.
- Core points:
  - `PopulationState.from_condition` builds the record from a prepared SciPlex3 condition:
    RNA shift measured; Hallmark activity and cell-cycle position inferred from RNA; cells recovered
    per well measured as a population-size proxy; protein, morphology, chromatin and metabolism missing.
  - `TransitionForecast` carries a forecast's arm, its source and target conditions, and its
    applicability; its evidence kind is always `model_prediction`.
  - A 24 h to 72 h transition is between matched populations in different wells: `paired_by` says
    `condition`, never `cell`.
- Interfaces: `VariableStatus`, `StateVariable`, `PopulationState`, `TransitionForecast`
- Depends on: common.py, numpy
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum

import numpy as np

import common as C

UNOBSERVED = ("protein", "morphology", "chromatin", "metabolism")


class VariableStatus(str, Enum):
    MEASURED = "measured"
    INFERRED = "inferred"            # computed from a measured variable by a declared rule
    PREDICTED = "predicted"          # produced by a model; never evidence
    MISSING = "missing"


@dataclass(frozen=True)
class StateVariable:
    name: str
    status: VariableStatus
    value: object = None
    derivation: str = ""


@dataclass(frozen=True)
class PopulationState:
    context: str                     # cell line
    time_hours: float
    intervention: str                # registered identifier; the compound's identity may be withheld
    dose_nM: float
    platform: str
    variables: tuple
    provenance: dict = field(default_factory=dict)
    is_complete_cell_state: bool = False

    def payload(self) -> dict:
        record = asdict(self)
        record["variables"] = [{**asdict(v), "status": v.status.value} for v in self.variables]
        return C.clean(record)

    @classmethod
    def from_condition(cls, data: C.Data, row: int, intervention: str) -> "PopulationState":
        r = data.conditions.iloc[row]
        y = data.shift[row].astype(float)
        symbols = list(data.genes.symbol)
        hallmark = {name: float(y[[symbols.index(g) for g in genes if g in symbols]].mean())
                    for name, genes in data.gene_sets.items() if any(g in symbols for g in genes)}
        top = sorted(hallmark.items(), key=lambda kv: -abs(kv[1]))[:5]
        cycle = {k: float(np.nanmean([r[f"{k}_rep1"], r[f"{k}_rep2"]])) for k in ("s_score", "g2m_score", "g2m_high")}
        size = float(np.nanmean([r.log2_count_ratio_rep1, r.log2_count_ratio_rep2]))
        variables = (
            StateVariable("rna_shift", VariableStatus.MEASURED,
                          {"genes": int(len(y)), "norm": float(np.linalg.norm(y)), "replicate_agreement": float(data.agreement[row])},
                          "pseudobulk log1p(CP10K) shift against the pooled vehicle of the same line, time and replicate"),
            StateVariable("hallmark_activity", VariableStatus.INFERRED, dict(top),
                          "mean rna_shift over MSigDB Hallmark members present; five largest in absolute value"),
            StateVariable("cell_cycle", VariableStatus.INFERRED, cycle,
                          "Tirosh S and G2M module means per cell, averaged per well; g2m_high is the fraction above the vehicle 90th percentile"),
            StateVariable("population_size", VariableStatus.MEASURED, {"log2_cells_vs_vehicle_well": size},
                          "cells recovered in the well against the mean vehicle well on the same plate; a proxy, not viability"),
            *(StateVariable(name, VariableStatus.MISSING, None, "not measured by sci-RNA-seq3") for name in UNOBSERVED),
        )
        provenance = {"source": "SciPlex3 (Srivatsan et al. 2020), Figshare release, label offset +1",
                      "wells": [r.well_rep1, r.well_rep2], "plates": [r.plate_rep1, r.plate_rep2],
                      "cells": [int(r.n_cells_rep1), int(r.n_cells_rep2)]}
        return cls(r.cell_line, float(r.time), intervention, float(r.dose), "sci-RNA-seq3", variables, provenance)


@dataclass(frozen=True)
class TransitionForecast:
    source: tuple                    # (line, time, dose) of the measured state
    target: tuple
    arm: str
    applicable: bool
    refusal: str | None = None
    paired_by: str = "condition"     # the two populations are different wells; never "cell"
    evidence_kind: str = "model_prediction"
    note: str = "planning-only: a forecast chooses which real measurement to buy and is never imported as a result"
