"""Synthetic fixtures for the functional-rule-revision pilot (software tests only; no biological meaning)."""
from __future__ import annotations

import copy
import importlib
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parents[2] / "research" / "routes" / "combination_resistant_transfer" / "functional_rule_revision_20261020"


def load_study():
    """Import the study modules from their research folder without installing them."""
    entry = str(STUDY)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return {name: importlib.import_module(name) for name in ("adapter", "design", "models", "evaluation", "llm_arm", "study")}


def small_config(study):
    cfg = copy.deepcopy(study.CONFIG)
    cfg.update({"n_modules": 3, "panel_pairs": 8, "cv_salts": ["cvA"], "pilot_pools": 15})
    cfg["ridge_configs"] = [[1.0, 3.0], [30.0, 10.0]]
    cfg["gbm_configs"] = [[3, 0.1, 30], [4, 0.1, 40]]
    cfg["fm_configs"] = [[2, 1.0], [2, 4.0]]
    cfg["edit_guard"] = {"min_relative_cv_change_all": -0.5, "min_scope_pairs_source_and_challenge": 3,
                         "min_scope_pairs_challenge": 1, "min_unmeasured_scope_pairs": 2}
    cfg["bootstrap"] = {"n": 60, "seed": 1, "alpha": 0.05, "primary_contrasts": 3, "cell_bootstrap_n": 30}
    return cfg


def synthetic_tables(mods, seed=0, n_drugs=14, n_cells=8):
    """A complete pair x cell table with a planted gated module-pair effect and a monotherapy panel."""
    adapter = mods["adapter"]
    rng = np.random.default_rng(seed)
    drugs = tuple(f"drug{k:02d}" for k in range(n_drugs))
    cells = tuple(f"cell{k}" for k in range(n_cells))
    pairs = tuple(combinations(drugs, 2))
    level = rng.uniform(0.1, 0.8, n_drugs)
    mono = np.clip(level[:, None] + 0.15 * rng.standard_normal((n_drugs, n_cells)), 0.02, 0.95)
    g_pair, g_cell, g_i, g_j = [], [], [], []
    for p, (a, b) in enumerate(pairs):
        for c in range(n_cells):
            g_pair.append(p)
            g_cell.append(c)
            g_i.append(drugs.index(a))
            g_j.append(drugs.index(b))
    g_pair, g_cell, g_i, g_j = (np.array(x, dtype=np.int32) for x in (g_pair, g_cell, g_i, g_j))
    ai, aj = mono[g_i, g_cell], mono[g_j, g_cell]
    a_ref = 1 - (1 - ai) * (1 - aj)
    n = len(g_pair)
    table = adapter.GroupTable(
        drugs, cells, pairs, g_pair, g_cell, np.array(["1"] * n, dtype=object), g_i, g_j, a_ref, ai, aj,
        np.ones(n, bool), np.array([""] * n, dtype=object), np.arange(n) + 2, np.full(n, 16, np.int32), np.zeros(n, np.int32),
        [() for _ in range(n)], [() for _ in range(n)], [() for _ in range(n)])
    drug_effect = 0.03 * rng.standard_normal(n_drugs)
    cell_effect = 0.02 * rng.standard_normal(n_cells)
    resid = drug_effect[g_i] + drug_effect[g_j] + cell_effect[g_cell] + 0.02 * rng.standard_normal(n)
    resid += 0.05 * ((g_i % 3 == 0) & (g_j % 3 == 1) & (g_cell % 2 == 0))
    return table, a_ref + resid


def build_context(mods, tmp_path, *, seed=0, f_poison=None, g_poison=None, cfg=None):
    adapter, design, study = mods["adapter"], mods["design"], mods["study"]
    table, a_obs = synthetic_tables(mods, seed)
    roles, _ = design.make_partition(table.pairs, table.drugs, seed0=7, min_s_pairs=6)
    role_g = roles[table.g_pair]
    a = a_obs.copy()
    rng = np.random.default_rng(99)
    if f_poison is not None:
        a[role_g == "F"] = f_poison(rng, int((role_g == "F").sum()))
    if g_poison is not None:
        a[role_g == "G"] = g_poison(rng, int((role_g == "G").sum()))
    sealed = tmp_path / "sealed"
    adapter.write_sealed(sealed, a, role_g)
    cfg = cfg or small_config(study)
    ctx = study.Context(table, roles, sealed, cfg, state_path=tmp_path / "vault_state.json")
    return ctx, table, roles


def comb_and_single(swap_orientation=False, drop_mono_batch=False, mono_range="full"):
    """Tiny raw-like dictionaries: 3 drugs, 1 cell, batch 1; combination grid 4 x 4 per pair."""
    doses = {"alpha": [0.1, 0.3, 1.0, 3.0], "beta": [0.2, 0.6, 2.0, 6.0], "gamma": [0.05, 0.15, 0.5, 1.5]}
    single = {k: [] for k in ("row", "batch", "cell", "drug", "conc", "x", "mu", "viability")}
    row = 2
    for drug, grid in doses.items():
        concs = np.geomspace(min(grid) / 3, max(grid) * 3, 8) if mono_range == "full" else np.geomspace(min(grid) * 2, max(grid) * 0.9, 8)
        for conc in concs:
            single["row"].append(row)
            single["batch"].append("2" if drop_mono_batch else "1")
            single["cell"].append("X1")
            single["drug"].append(drug)
            single["conc"].append(float(conc))
            single["x"].append(float(1.0 / (1.0 + conc)))
            single["mu"].append(0.0)
            single["viability"].append([0.5] * 6)
            row += 1
    comb = {k: [] for k in ("row", "batch", "cell", "drug_a", "drug_b", "conc_a", "conc_b", "x", "mu", "viability")}
    row = 2
    for a, b in (("alpha", "beta"), ("alpha", "gamma"), ("beta", "gamma")):
        for ca in doses[a]:
            for cb in doses[b]:
                first, second, c1, c2 = (b, a, cb, ca) if swap_orientation else (a, b, ca, cb)
                comb["row"].append(row)
                comb["batch"].append("1")
                comb["cell"].append("X1")
                comb["drug_a"].append(first)
                comb["drug_b"].append(second)
                comb["conc_a"].append(c1)
                comb["conc_b"].append(c2)
                comb["x"].append(0.4 / (1 + ca) / (1 + cb))
                comb["mu"].append(0.0)
                comb["viability"].append([0.5] * 4)
                row += 1
    conv = lambda d: {k: (np.array(v, dtype=object) if k in ("batch", "cell", "drug", "drug_a", "drug_b") else np.array(v, dtype=float if k not in ("row",) else np.int64)) for k, v in d.items()}  # noqa: E731
    return conv(comb), conv(single)
