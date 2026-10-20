"""Frozen design objects: partition, functional modules, observable gates, edit dictionary, challenge panel.

Everything here is a function of identities, design metadata and the common monotherapy panel
(no combination outcome). The only learned structure, the module clustering, uses the
single-agent panel that is common initial information for every method.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, asdict
from itertools import combinations_with_replacement

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

PARTITION_SEED0 = 20261020
FRACTIONS = {"S": 0.60, "C": 0.15, "G": 0.10, "F": 0.15}
MIN_S_PAIRS_PER_DRUG = 9
N_MODULES = 4
PANEL_PAIRS = 60          # challenge budget (pairs; each measured in all 39 cells = one batch)
K_SHORTLIST = 5


def _hash_order(tag: str, items):
    return sorted(items, key=lambda x: hashlib.sha256(f"{tag}|{x}".encode()).hexdigest())


# --------------------------------------------------------------------------- partition
def make_partition(pairs: tuple, drugs: tuple, seed0: int = PARTITION_SEED0, max_draws: int = 500,
                   min_s_pairs: int = MIN_S_PAIRS_PER_DRUG):
    """Disjoint partition of canonical unordered pairs into S/C/G/F, 60/15/10/15.

    Coverage rule (identity only): every drug appears in at least MIN_S_PAIRS_PER_DRUG pairs of S.
    The first seed that satisfies it is used; the number of draws is recorded.
    """
    n = len(pairs)
    counts = {"S": round(FRACTIONS["S"] * n), "C": round(FRACTIONS["C"] * n), "G": round(FRACTIONS["G"] * n)}
    counts["F"] = n - sum(counts.values())
    for draw in range(max_draws):
        order = np.random.default_rng(seed0 + draw).permutation(n)
        roles = np.empty(n, dtype="<U1")
        start = 0
        for role in ("S", "C", "G", "F"):
            roles[order[start:start + counts[role]]] = role
            start += counts[role]
        degree = {d: 0 for d in drugs}
        for p, role in zip(pairs, roles):
            if role == "S":
                degree[p[0]] += 1
                degree[p[1]] += 1
        if min(degree.values()) >= min_s_pairs:
            return roles, {"seed": seed0 + draw, "draws": draw + 1, "counts": counts,
                           "min_S_pairs_per_drug": min(degree.values())}
    raise RuntimeError("no partition satisfied the S-coverage rule")


# --------------------------------------------------------------------------- modules and gates
def drug_cell_panel(g_i, g_j, g_cell, a_mi, a_mj, eligible, n_drugs, n_cells):
    """Monotherapy activity of each drug in each cell at its combination grid doses (derived reference)."""
    total = np.zeros((n_drugs, n_cells))
    count = np.zeros((n_drugs, n_cells))
    for i, j, c, ai, aj, ok in zip(g_i, g_j, g_cell, a_mi, a_mj, eligible):
        if ok:
            total[i, c] += ai
            count[i, c] += 1
            total[j, c] += aj
            count[j, c] += 1
    panel = np.where(count > 0, total / np.maximum(count, 1), np.nan)
    return panel


def make_modules(panel: np.ndarray, k: int = N_MODULES):
    """Ward clusters of the 38 drugs on their monotherapy activity profiles; ordered by mean activity (m0 = most active)."""
    filled = np.where(np.isfinite(panel), panel, np.nanmean(panel, axis=1, keepdims=True))
    tree = linkage(filled, method="ward")
    raw = fcluster(tree, t=k, criterion="maxclust") - 1
    means = [filled[raw == c].mean() for c in range(raw.max() + 1)]
    rank = {old: new for new, old in enumerate(np.argsort(means)[::-1])}
    return np.array([rank[c] for c in raw], dtype=int)


def make_gates(panel: np.ndarray, module: np.ndarray):
    """Observable cell conditions from the monotherapy panel: sensitivity above the across-cell median.

    Values: 1 satisfied, 0 not satisfied, -1 unknown (never treated as satisfied).
    """
    gates = {}
    def gate(values):
        out = np.full(len(values), -1, dtype=int)
        finite = np.isfinite(values)
        if finite.any():
            threshold = float(np.median(values[finite]))
            out[finite] = (values[finite] >= threshold).astype(int)
        return out
    gates["glob"] = gate(np.array([np.nanmean(panel[:, c]) if np.isfinite(panel[:, c]).any() else np.nan
                                   for c in range(panel.shape[1])]))
    for m in range(int(module.max()) + 1):
        rows = panel[module == m]
        gates[f"m{m}"] = gate(np.array([np.nanmean(rows[:, c]) if np.isfinite(rows[:, c]).any() else np.nan
                                        for c in range(panel.shape[1])]))
    return gates


# --------------------------------------------------------------------------- edit dictionary
@dataclass(frozen=True)
class Rule:
    """A bounded structural edit of the fixed model.

    kind 'split' : the shared component `target` ('X' cross-module, 'W' within-module) gets an
                   additional coefficient that applies only where the observable `gate` is satisfied.
    kind 'add'   : one additional shared component for drug pairs of module class `module_pair`.
    """
    id: str
    kind: str
    target: str
    gate: str | None
    module_pair: tuple | None

    def describe(self) -> str:
        if self.kind == "split":
            who = "cross-module pairs" if self.target == "X" else "within-module pairs"
            cond = "cell mean monotherapy activity >= across-cell median" if self.gate == "glob" else \
                f"cell sensitivity to module m{self.gate[1:]} >= across-cell median" if self.target == "X" else \
                "cell sensitivity to the pair's own module >= across-cell median"
            return f"split shared component of {who} by condition: {cond}"
        return f"add shared component for module pair m{self.module_pair[0]}-m{self.module_pair[1]}"


def build_dictionary(n_modules: int = N_MODULES):
    """Finite frozen dictionary from metadata only (16 edits for four modules)."""
    rules = []
    for gate in ["glob"] + [f"m{m}" for m in range(n_modules)]:
        rules.append(Rule(f"E{len(rules) + 1:02d}", "split", "X", gate, None))
    rules.append(Rule(f"E{len(rules) + 1:02d}", "split", "W", "own", None))
    for a, b in combinations_with_replacement(range(n_modules), 2):
        rules.append(Rule(f"E{len(rules) + 1:02d}", "add", "pair", None, (a, b)))
    return rules


def rule_column(rule: Rule, g_i, g_j, g_cell, module, gates):
    """Numerical feature of an edit for every group: its scope indicator (0 where not applicable/unknown)."""
    p, q = module[g_i], module[g_j]
    cross, within = (p != q), (p == q)
    if rule.kind == "add":
        a, b = rule.module_pair
        return (((p == a) & (q == b)) | ((p == b) & (q == a))).astype(float)
    if rule.target == "X":
        return (cross & (gates[rule.gate][g_cell] == 1)).astype(float)
    # W split: gate of the pair's own module
    own = np.zeros(len(g_i), dtype=bool)
    for m in range(int(module.max()) + 1):
        own |= within & (p == m) & (gates[f"m{m}"][g_cell] == 1)
    return own.astype(float)


# --------------------------------------------------------------------------- challenge panel
def module_pair_class(pair, module):
    a, b = sorted((int(module[pair[0]]), int(module[pair[1]])))
    return (a, b)


def choose_panel(c_pairs: list, pair_drugs: dict, module, budget: int = PANEL_PAIRS, seed: int = PARTITION_SEED0):
    """Design-balanced challenge panel from role C: equal allocation over module-pair classes, hash order within class."""
    classes = {}
    for p in c_pairs:
        classes.setdefault(module_pair_class(pair_drugs[p], module), []).append(p)
    ordered = {c: _hash_order(f"panel{seed}", ps) for c, ps in sorted(classes.items())}
    chosen, rank = [], 0
    while len(chosen) < budget and any(rank < len(v) for v in ordered.values()):
        for c in sorted(ordered):
            if rank < len(ordered[c]) and len(chosen) < budget:
                chosen.append(ordered[c][rank])
        rank += 1
    return sorted(chosen)


def shortlist(pred: np.ndarray, pair_ids: np.ndarray, k: int = K_SHORTLIST):
    """Indices of the k highest predictions; ties broken by the smaller pair id (deterministic)."""
    order = np.lexsort((pair_ids, -pred))
    return order[:k]
