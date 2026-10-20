"""Synthetic task streams for the mechanism experiment (software/method controls; not biological evidence).

A stream = one independent random world (drugs, modules, hidden mechanism parameters) plus an ordered schedule of cell backgrounds:
  H0       initial released history (full labels, shared by every method)
  batches  four batches of task campaigns; each batch is released in full after its campaigns (shared source-data release)
  A_old    anchor backgrounds drawn from the early distribution (never released)
  A_new    anchor backgrounds drawn from the late distribution (never released)
Mechanism kinds: null, lowrank, alias (repeated decision-relevant aliasing by hidden gates), compose (gates + late-appearing gates + conjunction).
`decoupled=True` is the witness-to-target control: gate effects in task and anchor cells are drawn independently per class, so a probe in one class
carries no information about the others, while anchors, nuisance and noise are unchanged.
"""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path

SVC = Path(__file__).resolve().parents[1] / "self_improving_virtual_cell_20261020"
if str(SVC) not in sys.path:
    sys.path.insert(0, str(SVC))

from svc_world import Static, World  # noqa: E402

KINDS = ("null", "lowrank", "alias", "compose")
N_DRUGS = 28
N_H0, N_BATCH, N_PER_BATCH, N_ANCHOR = 8, 4, 4, 4


def make_stream(kind: str, seed: int, decoupled: bool = False, n_drugs: int = N_DRUGS) -> dict:
    assert kind in KINDS
    rng = np.random.default_rng(10_000 * seed + 17 * KINDS.index(kind) + 5)
    rng_dec = np.random.default_rng(10_000 * seed + 99)
    n_cells = N_H0 + N_BATCH * N_PER_BATCH + 2 * N_ANCHOR
    drugs = tuple(f"d{k:02d}" for k in range(n_drugs))
    ii, jj = np.triu_indices(n_drugs, 1)
    n = len(ii)
    module = np.repeat(np.arange(4), n_drugs // 4)[rng.permutation(n_drugs)]
    static = Static(drugs, ii, jj, module, tuple(f"{drugs[i]}+{drugs[j]}" for i, j in zip(ii, jj)))
    cells = tuple(f"c{k:02d}" for k in range(n_cells))
    sched = {"H0": list(cells[:N_H0]), "batches": [list(cells[N_H0 + b * N_PER_BATCH: N_H0 + (b + 1) * N_PER_BATCH]) for b in range(N_BATCH)]}
    base = N_H0 + N_BATCH * N_PER_BATCH
    sched["A_old"], sched["A_new"] = list(cells[base: base + N_ANCHOR]), list(cells[base + N_ANCHOR:])
    level = rng.uniform(0.30, 0.50, n_drugs)
    mono = np.clip(level[:, None] + 0.05 * rng.standard_normal((n_drugs, n_cells)), 0.02, 0.95)
    ai, aj = mono[ii], mono[jj]
    Aref = 1 - (1 - ai) * (1 - aj)
    mu = 0.02 * rng.standard_normal(n)
    delta = 0.01 * rng.standard_normal((n_drugs, n_cells))                       # shared-anchor drug-cell nuisance
    noise = 0.01 * rng.standard_normal((n, n_cells))
    R = mu[:, None] + delta[ii] + delta[jj] + noise
    cls = static.pair_class
    n_cls = len(static.classes)
    meta = {"kind": kind, "seed": seed, "decoupled": decoupled}
    late_cells = set(sched["batches"][2]) | set(sched["batches"][3]) | set(sched["A_new"])
    task_cells = {c for b in sched["batches"] for c in b} | set(sched["A_old"]) | set(sched["A_new"])
    if kind == "lowrank":
        L = rng.standard_normal((n, 2)) * 0.035
        S = rng.standard_normal((n_cells, 2))
        R = R + L @ S.T
    elif kind in ("alias", "compose"):
        G = 3 if kind == "alias" else 4
        scopes, amp, load = [], [], []
        for g in range(G):
            sc = rng.choice(n_cls, 2, replace=False)
            scopes.append(sc)
            amp.append(rng.uniform(0.14, 0.24) * rng.choice([-1.0, 1.0]))
            load.append(rng.uniform(0.6, 1.4, n))
        states = np.zeros((n_cells, G), int)
        for k, c in enumerate(cells):
            for g in range(G):
                p = 0.5
                if kind == "compose" and g >= 2:
                    p = 0.55 if c in late_cells else 0.0
                states[k, g] = rng.random() < p
        conj_class = int(rng.integers(n_cls)) if kind == "compose" else None
        conj_amp = rng.uniform(0.08, 0.12) * rng.choice([-1.0, 1.0]) if kind == "compose" else 0.0
        eff = np.zeros((n, n_cells))
        for k, c in enumerate(cells):
            for g in range(G):
                for q in scopes[g]:
                    s = states[k, g]
                    if decoupled and c in task_cells:
                        s = int(rng_dec.random() < 0.5)                      # independent per class: the witness relation is broken
                    eff[cls == q, k] += amp[g] * load[g][cls == q] * s
            if kind == "compose" and states[k, 0] * states[k, 1]:
                eff[cls == conj_class, k] += conj_amp
        R = R + eff
        meta.update({"gate_scopes": [s.tolist() for s in scopes], "gate_amp": amp, "gate_load": [l.tolist() for l in load], "states": states.tolist(), "conj_class": conj_class, "conj_amp": float(conj_amp)})
    world = World(static, cells, Aref, np.minimum(ai, aj), np.maximum(ai, aj), Aref + R, label=f"stream_{kind}_{seed}{'_dec' if decoupled else ''}")
    world.meta = meta
    return {"world": world, "schedule": sched, "meta": meta}
