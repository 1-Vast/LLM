"""Index over a set of cases: dense reading tables, structure fingerprints and the stage-1 hard filter.

File summary
- Path: research/scientific_case_memory/case_index.py
- Purpose: hold what retrieval and the conditional world model need from a memory in arrays, built
  from `Case` objects and nothing else, so the memory really is the case set.
- Core points:
  - Reading codes. For each condition key, `code[key][reference, class]` is the registered
    validator's reading of that reference against each other pool class, with its whole
    independent unit left out: 0 matches its own class, 1 matches the decoy, 2 unresolved,
    3 undetected, -1 not scored (not measured, QC-failed, or the class itself). The codes come from
    the compact `HypothesisUpdate.codes` string of each case, one character per pool class.
  - Reading kinds follow from the codes (`KIND_OF_CODE`), so an ablation can remove failure and
    negative readings (codes 1 and 3) without removing the cases that hold them.
  - Stage 1 (`hard_filter`) excludes a case before any similarity is computed when its assay,
    measurement type, unit, time scale, dose scale, control design, quality status or intervention
    type is incompatible with the problem. Each exclusion carries a named reason.
  - `from_cases` needs a pool (the ordered hypothesis classes), the condition keys and, for the
    structure kernel, a fingerprint per compound. It never touches a label outside the cases.
- Interfaces: `CODE_OF`, `KIND_OF_CODE`, `ReadingTable`, `CaseIndex`, `hard_filter`, `encode_codes`,
  `decode_codes`
- Depends on: case_schema.py, numpy
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from . import case_schema as S

CODE_OF = {"matches_own_class": 0, "matches_decoy_class": 1, "unresolved": 2, "no_detectable_response": 3}
LABEL_OF_CODE = {v: k for k, v in CODE_OF.items()}
KIND_OF_CODE = {0: S.ReadingKind.CANONICAL, 1: S.ReadingKind.MISLEADING, 2: S.ReadingKind.AMBIGUOUS,
                3: S.ReadingKind.NEGATIVE}
FAILURE_CODES = (1, 3)
"""Codes removed when failure and negative precedents are ablated."""


def encode_codes(codes: Sequence[int]) -> str:
    return "".join("-" if c < 0 else str(int(c)) for c in codes)


def decode_codes(text: str) -> np.ndarray:
    return np.array([-1 if ch == "-" else int(ch) for ch in text], dtype=int)


@dataclass
class ReadingTable:
    """Reference readings at one condition key."""

    key: tuple
    names: list
    klass: np.ndarray
    code: np.ndarray
    detected: np.ndarray
    agreement: np.ndarray
    unit: np.ndarray
    row: dict = field(default_factory=dict)


def hard_filter(problem: Mapping[str, object], case: S.Case) -> tuple[bool, str | None]:
    """Stage 1: is this case even comparable? Returns (eligible, named reason when not).

    `problem` may carry any of: assay, measurement_type, unit, time_scale, dose_scale, control_design,
    intervention_type, biological_system, min_quality. Missing keys are not compared.
    """
    fp = case.context_fingerprint
    checks = (("biological_system", "biological_system"), ("assay", "assay"), ("measurement_type", "measurement_type"),
              ("unit", "unit"), ("time_scale", "time_scale"), ("dose_scale", "dose_scale"),
              ("control_design", "control_design"), ("intervention_type", "intervention_type"))
    for key, field_name in checks:
        want, have = problem.get(key), fp.get(field_name)
        if want is not None and have is not None and want != have:
            return False, f"incompatible_{key}:{have}!={want}"
    if problem.get("min_quality") is not None:
        quality = case.data_quality_report.get("passed_fraction")
        if quality is not None and quality < problem["min_quality"]:
            return False, "quality_below_minimum"
    if case.data_quality_report.get("usable") is False:
        return False, "case_marked_unusable"
    return True, None


class CaseIndex:
    def __init__(self, pool: Sequence[str], keys: Sequence[tuple], tables: Mapping[tuple, ReadingTable],
                 cases: Mapping[str, S.Case], fingerprints: np.ndarray | None, fp_pos: Mapping[str, int],
                 unit_of: Mapping[str, str], klass_of: Mapping[str, str]):
        self.pool = tuple(pool)
        self.cidx = {c: i for i, c in enumerate(self.pool)}
        self.keys = tuple(tuple(k) for k in keys)
        self.tables = dict(tables)
        self.cases = dict(cases)
        self.fp = fingerprints
        self.fp_pos = dict(fp_pos)
        self.unit_of = dict(unit_of)
        self.klass_of = dict(klass_of)

    # ------------------------------------------------------------------ construction
    @classmethod
    def from_cases(cls, cases: Sequence[S.Case], pool: Sequence[str], keys: Sequence[tuple], *,
                   fingerprints: np.ndarray | None = None, fp_pos: Mapping[str, int] | None = None,
                   include_kinds: Sequence[S.CaseKind] | None = None) -> "CaseIndex":
        pool = tuple(pool)
        keys = tuple(tuple(k) for k in keys)
        rows: dict[tuple, list] = {k: [] for k in keys}
        by_id: dict[str, S.Case] = {}
        unit_of, klass_of = {}, {}
        for case in cases:
            if include_kinds is not None and case.case_kind not in include_kinds:
                continue
            name = case.context_fingerprint["compound"]
            by_id[name] = case
            unit_of[name] = case.context_fingerprint.get("unit", name)
            klass_of[name] = case.context_fingerprint.get("hypothesis_class")
            obs = {o.condition_id: o for o in case.initial_observations}
            for u in case.hypothesis_updates:
                key = tuple(_key_of(u.action_id))
                if key not in rows:
                    continue
                o = obs.get(u.action_id)
                rows[key].append((name, klass_of[name], decode_codes(u.codes), bool(o.detected) if o and o.detected
                                  is not None else False, float(o.replicate_agreement) if o and o.replicate_agreement
                                  is not None else np.nan))
        tables = {}
        for key, entries in rows.items():
            entries.sort(key=lambda e: e[0])
            names = [e[0] for e in entries]
            code = np.full((len(names), len(pool)), -1, dtype=int)
            for i, e in enumerate(entries):
                n = min(len(e[2]), len(pool))
                code[i, :n] = e[2][:n]
            tables[key] = ReadingTable(key, names, np.array([e[1] for e in entries], dtype=object), code,
                                       np.array([e[3] for e in entries], dtype=bool),
                                       np.array([e[4] for e in entries], dtype=float),
                                       np.array([unit_of[n] for n in names], dtype=object),
                                       {n: i for i, n in enumerate(names)})
        return cls(pool, keys, tables, by_id, fingerprints, fp_pos or {}, unit_of, klass_of)

    # ------------------------------------------------------------------ views
    def masked(self, codes: Sequence[int]) -> "CaseIndex":
        """A copy in which readings with these codes are not scored (failure-case ablation)."""
        tables = {}
        for key, t in self.tables.items():
            code = t.code.copy()
            code[np.isin(code, list(codes))] = -1
            tables[key] = ReadingTable(t.key, t.names, t.klass, code, t.detected, t.agreement, t.unit, t.row)
        return CaseIndex(self.pool, self.keys, tables, self.cases, self.fp, self.fp_pos, self.unit_of, self.klass_of)

    def reading_kind_counts(self) -> dict[str, int]:
        out = {k.value: 0 for k in S.ReadingKind}
        for t in self.tables.values():
            for code, kind in KIND_OF_CODE.items():
                out[kind.value] += int((t.code == code).sum())
        return out

    def eligible(self, problem: Mapping[str, object]) -> tuple[list[str], dict[str, str]]:
        """Stage 1 over every case: eligible compound names and the named reason for each exclusion."""
        keep, dropped = [], {}
        for name, case in sorted(self.cases.items()):
            ok, reason = hard_filter(problem, case)
            if ok:
                keep.append(name)
            else:
                dropped[name] = reason or "excluded"
        return keep, dropped


def _key_of(action_id: str) -> tuple:
    """`A549|024h|10000nM` back to ('A549', 24.0, 10000.0)."""
    line, t, dose = action_id.split("|")
    return line, float(t.rstrip("h")), float(dose.rstrip("nM"))
