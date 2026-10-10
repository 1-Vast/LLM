"""Same-spheroid phenotypes from Tahoe-100M obs codes: relative survival and cell-cycle shifts.

Tahoe-100M treats pooled "cell villages" of 50 lines per spheroid for 24 h, so a line's cell count
and its cells' phase calls come from the same culture unit as its RNA. This module turns per-cell
obs codes into per (line, condition, plate) phenotypes:

* relative survival = log2 share of the spheroid (denominator: a declared reference line set)
  minus the same share in that plate's control spheroids. Absolute survival is not identified:
  spheroid totals did not replicate across plates (2026-10-10 qualification, r = -0.12).
* phase log-odds shift = logit(p_phase | treated) - logit(p_phase | same-plate control).

Lines whose median treated-condition count falls below a declared minimum are refused as
``CONTEXT_UNDERCOUNTED`` rather than silently down-weighted. No expression value is read.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Sequence

import numpy as np

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
PHASES = ("G1", "S", "G2M")
PSEUDOCOUNT = 0.5
MIN_MEDIAN_TREATED_COUNT = 200

Table = Mapping[tuple[str, str, str], Mapping[str, int]]


def counts_from_codes(line: str, label_codes: np.ndarray, plate_codes: np.ndarray, phase_codes: np.ndarray,
                      label_names: Sequence[str], plate_names: Sequence[str], phase_names: Sequence[str]) -> dict:
    """Per (line, label, plate): total cells and cells per phase, from one line's obs code arrays."""
    if not (len(label_codes) == len(plate_codes) == len(phase_codes)):
        raise ValueError("obs code arrays differ in length")
    width = len(plate_names)
    key = np.asarray(label_codes, dtype=np.int64) * width + np.asarray(plate_codes, dtype=np.int64)
    uniq, inverse = np.unique(key, return_inverse=True)
    total = np.bincount(inverse)
    phase_index = {p: list(phase_names).index(p) for p in PHASES}
    per_phase = {p: np.bincount(inverse, weights=np.asarray(phase_codes) == code).astype(np.int64) for p, code in phase_index.items()}
    return {(line, str(label_names[k // width]), str(plate_names[k % width])): {"n": int(total[i]), **{p: int(per_phase[p][i]) for p in PHASES}}
            for i, k in enumerate(uniq)}


def qualify_lines(table: Table, lines: Iterable[str], *, control: str = CONTROL,
                  min_median: int = MIN_MEDIAN_TREATED_COUNT) -> tuple[list[str], dict[str, dict]]:
    """Keep lines whose median treated-condition count reaches ``min_median``; refuse the rest by name."""
    kept, refused = [], {}
    for line in lines:
        counts = [row["n"] for (l, label, _), row in table.items() if l == line and label != control]
        median = float(np.median(counts)) if counts else 0.0
        if median >= min_median:
            kept.append(line)
        else:
            refused[line] = {"reason": "CONTEXT_UNDERCOUNTED", "median_treated_count": median, "minimum": min_median}
    return kept, refused


def _logit(k: float, n: float) -> float:
    return float(np.log((k + PSEUDOCOUNT) / (n - k + PSEUDOCOUNT)))


def phenotype_frame(table: Table, lines: Sequence[str], denominator_lines: Sequence[str], *, control: str = CONTROL) -> dict:
    """Relative survival and phase log-odds shifts for ``lines`` against same-plate controls."""
    wells: dict = defaultdict(dict)
    for (line, label, plate), row in table.items():
        wells[(label, plate)][line] = row
    denominator = {w: sum(v[l]["n"] for l in denominator_lines if l in v) for w, v in wells.items()}
    out = {}
    for (label, plate), members in wells.items():
        if label == control or (control, plate) not in wells:
            continue
        base = wells[(control, plate)]
        if denominator[(label, plate)] <= 0 or denominator[(control, plate)] <= 0:
            continue
        for line in lines:
            if line not in members or line not in base:
                continue
            row, ref = members[line], base[line]
            record = {"survival": float(np.log2((row["n"] + PSEUDOCOUNT) / denominator[(label, plate)])
                                        - np.log2((ref["n"] + PSEUDOCOUNT) / denominator[(control, plate)])),
                      "n": row["n"], "n_control": ref["n"]}
            for phase in PHASES:
                record[phase] = _logit(row[phase], row["n"]) - _logit(ref[phase], ref["n"])
            out[(line, label, plate)] = record
    return out
