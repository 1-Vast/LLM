"""Source-verified procedure selection: choose the Virtual Cell rank and the agent's procedure per domain.

File summary
- Path: src/agent/procedure_selection.py
- Purpose: before acting on new contexts, replay the candidate procedures on the domain's own
  source contexts and adopt a costlier procedure only on evidence. This is the agent's "verify
  before transferring a procedure" step: in the source study, bridging paid in a large, diffuse
  library and did not pay in a small, sparse panel, so no fixed procedure is right everywhere.
- Core points:
  - `source_replay` runs an inner cross-validation on source contexts only:
    - inner folds are by context, or by dependence group (``by_group=True``, for example
      patients with several samples);
    - inner events are recomputed from source outcomes only;
    - each candidate rank is tried with the procedures ``vc0`` (no bridge), ``b_exploit`` and
      ``b_lookahead``, all at the same well budget;
    - every inner held-out context returns its hits.
  - `choose` is a pure function of those inner records. The default rule, ``hybrid``, was
    chosen among three by minimax relative regret over four development settings:
    - rank: the best mean inner ``vc0`` hits (ties to the smaller rank);
    - procedure: a bridge only if its paired inner gain over ``vc0`` has z > `Z_BRIDGE`, because a
      bridge costs one extra assay round. The bridge with the larger z wins.
  - Two other rules are kept for audit:
    - ``evidence``: a one-SE rank rule, too conservative when whole lineages are new;
    - ``max``: any positive bridge gain switches, which follows inner noise.
  - With too little inner evidence (fewer than two inner records), the choice is ``vc0`` with
    basis ``NO_INNER_EVIDENCE``, never a bridge.
- Limits of the selection statistics (audit of 2026-10-17, ``research/feedback_attribution_20261017``):
  - `_paired` computes the inner standard error over sample rows. Inner folds are by patient
    (``by_group=True``), but the SE still treats a patient's samples as independent.
  - ``z > Z_BRIDGE`` is applied after choosing the rank among four and the larger of two bridge
    z values on the same inner records. It is a heuristic threshold, not a post-selection 95%
    guarantee.
  - Every procedure reuses the rank chosen for ``vc0``; in the confirmation the best inner rank
    for exploit differed from vc0's in some folds. Attribution comparisons need one fixed common
    rank; full method comparisons need an equal tuning budget per procedure. Both, and a
    generate-then-calibrate selector on disjoint patients, are development code in that study.
  - `SELECTION_STATUS` states the evidence grade.
- Interfaces: `hash_unit`, `hash_folds`, `source_replay`, `choose`, `select_procedure`,
  `ProcedureChoice`, `PROCEDURES`, `RANKS`, `RULES`, `Z_BRIDGE`, `SELECTION_STATUS`.
- Depends on: numpy, `virtual_cell.bridged_transfer`, `agent.bridge_design`.

Scope of the evidence: 2026-10-17, ``research/context_transfer_20261017``. One-shot Beat AML 2.0
confirmation; the domain is described in `virtual_cell.bridged_transfer`. The confirmed run used
rule ``hybrid`` with the lookahead as frozen (``lookahead_rule="lookahead_v1"``), inner folds by
patient.
- Choice: exploit-first bridging in all five patient-disjoint folds.
  - Inner exploit z was 2.3 to 3.4, and inner lookahead z −1.8 to −3.4.
  - Ranks were 40, 10, 20, 20 and 20.
- Supported (Holm over six hypotheses):
  - against the Virtual Cell alone: +0.073 hits per sample [+0.025, +0.127];
  - against pilot matching without the Virtual Cell: +0.229 [+0.162, +0.298];
  - against carrying the PRISM development procedure (lookahead) over unchanged: +0.108
    [+0.051, +0.172].
- Not shown:
  - It matched the best fixed procedure in hindsight, but trivially: it chose that procedure in
    every fold, so the difference is exactly zero.
  - It did not beat the standard exploit-first design; here it is that design.
  - The pre-registered expectation was that it would decline to bridge on Beat AML; it bridged.
- What the source check caught was a defect of ``lookahead_v1`` that appears only when measurement
  rates vary across items (`agent.bridge_design._lookahead`). The check worked as a verification
  step. It is not evidence that lookahead planning is worse for primary samples.
- Development: it bridged in all PRISM 19Q4 folds, 0/5 folds of a random AML-shaped proxy and
  2/5 of a structured one.
- The default ``lookahead_rule="lookahead"`` (corrected) has not been re-run through the selector
  on these domains, so the selector with that default is development-grade.
- The inner standard error treats contexts as independent (520 samples from 479 patients).
- What it does not establish: adaptivity (the same procedure in 5/5 folds) or an advantage over
  the fixed exploit pipeline (P2 = 0). Its value here was defect detection.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field

import numpy as np

from virtual_cell.bridged_transfer import BridgedTransferModel, selective_events

from .bridge_design import choose_bridge, nominate

PROCEDURES = ("vc0", "b_exploit", "b_lookahead")
RANKS = (5, 10, 20, 40)
ROUNDS = {"vc0": 1, "b_exploit": 2, "b_lookahead": 2}
Z_BRIDGE = 1.645
INNER_FOLDS = 3
NO_INNER_EVIDENCE = "NO_INNER_EVIDENCE"
SELECTION_STATUS = {
    ("hybrid", "lookahead_v1"): "ran once in the confirmation; chose exploit in 5/5 folds; no selection gain shown",
    ("hybrid", "lookahead"): "development: the corrected lookahead has not been run through the selector on held-out data",
}


def _h(key: str, salt: str) -> int:
    return int(hashlib.sha256(f"{salt}:{key}".encode()).hexdigest(), 16)


def hash_unit(keys, salt: str) -> np.ndarray:
    """A fixed pseudo-random value in [0, 1) per key; used for tie-breaks and random orders."""

    return np.array([(_h(str(k), salt) % (10 ** 12)) / 1e12 for k in keys])


def hash_folds(keys, salt: str, n: int) -> np.ndarray:
    return np.array([_h(str(k), salt) % n for k in keys])


def _replay(Y, X, events, fold_ids, targets, items, budget, k_bridge, rank, abs_gate, min_measured,
            impute_iters, contexts, lookahead_rule="lookahead"):
    order = hash_unit(items, "tie")
    rows = []
    for k in sorted(set(fold_ids.tolist())):
        tgt = np.flatnonzero((fold_ids == k) & targets)
        if len(tgt) == 0:
            continue
        src = np.flatnonzero(fold_ids != k)
        model = BridgedTransferModel(rank=rank, abs_gate=abs_gate, min_measured=min_measured,
                                     impute_iters=impute_iters).fit(Y[src], X[src])
        for c in tgt:
            x = X[c] if np.isfinite(X[c]).all() else None
            st0 = model.prior(x)
            rec = {"context": str(contexts[c])}
            rec["vc0"] = int(events[c][nominate(model.expected_hit(st0), budget, [], order)].sum())
            for name, rule in (("b_exploit", "exploit"), ("b_lookahead", lookahead_rule)):
                bridge = choose_bridge(rule, model, st0, k_bridge, budget, order)
                st1 = model.posterior(st0, bridge, Y[c, bridge])
                final = nominate(model.expected_hit(st1), budget - k_bridge, bridge, order)
                rec[name] = int(events[c][np.concatenate([bridge, final])].sum())
            rows.append(rec)
    return rows


def source_replay(Y, X, contexts, groups, items, budget: int, k_bridge: int, abs_gate=None,
                  min_measured: int = 10, impute_iters: int = 15, ranks=RANKS, by_group: bool = False,
                  salt: str = "procedure", max_inner_targets: int | None = None,
                  lookahead_rule: str = "lookahead") -> dict:
    """Inner replay on source contexts only: {rank: [{context, vc0, b_exploit, b_lookahead}]}.

    ``lookahead_rule="lookahead_v1"`` replays the lookahead exactly as the confirmed study did.
    """

    Y = np.asarray(Y, dtype=float)
    X = np.asarray(X, dtype=float)
    contexts, groups = np.asarray(contexts), np.asarray(groups)
    events, _ = selective_events(Y, abs_gate, min_measured)
    fid = hash_folds(groups if by_group else contexts, salt + ":inner", INNER_FOLDS)
    targets = np.ones(len(fid), bool)
    if max_inner_targets:
        targets[:] = False
        u = hash_unit(contexts, salt + ":subsample")
        for k in range(INNER_FOLDS):
            idx = np.flatnonzero(fid == k)
            targets[idx[np.argsort(u[idx])[:max_inner_targets]]] = True
    return {int(r): _replay(Y, X, events, fid, targets, np.asarray(items), budget, k_bridge, int(r), abs_gate,
                            min_measured, impute_iters, contexts, lookahead_rule) for r in ranks}


@dataclass
class ProcedureChoice:
    rank: int
    procedure: str
    rounds: int
    basis: str
    inner_targets: int
    inner_means: dict = field(default_factory=dict)
    bridge_gains: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def _paired(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.inf
    return float(d.mean()) if len(d) else 0.0, float(se)


RULES = ("hybrid", "evidence", "max")


def choose(inner_by_rank: dict, rule: str = "hybrid") -> ProcedureChoice:
    if rule not in RULES:
        raise ValueError(f"unknown rule {rule!r}")
    ranks = sorted(inner_by_rank, key=int)
    if not ranks:
        raise ValueError("no candidate rank")
    col = {r: {p: np.array([x[p] for x in inner_by_rank[r]], float) for p in PROCEDURES} for r in ranks}
    if min(len(col[r]["vc0"]) for r in ranks) < 2:
        r0 = int(ranks[0])
        return ProcedureChoice(r0, "vc0", 1, NO_INNER_EVIDENCE, int(len(col[ranks[0]]["vc0"])))
    means = {r: {p: float(col[r][p].mean()) for p in PROCEDURES} for r in ranks}
    best = max(ranks, key=lambda r: (means[r]["vc0"], -int(r)))
    if rule in ("max", "hybrid"):
        rank = best
    else:
        rank = next(r for r in ranks if (lambda m, se: m >= -se)(*_paired(col[r]["vc0"], col[best]["vc0"])))
    gains = {}
    for b in ("b_exploit", "b_lookahead"):
        m, se = _paired(col[rank][b], col[rank]["vc0"])
        gains[b] = {"gain": m, "se": se, "z": m / se if se > 0 else (np.inf if m > 0 else 0.0)}
    if rule == "max":
        b = max(("b_exploit", "b_lookahead"), key=lambda b: (gains[b]["gain"], b == "b_exploit"))
        procedure = b if gains[b]["gain"] > 0 else "vc0"
        basis = "max_rule_audit_only"
    else:
        b = max(("b_exploit", "b_lookahead"), key=lambda b: (gains[b]["z"], b == "b_exploit"))
        procedure = b if gains[b]["z"] > Z_BRIDGE else "vc0"
        basis = "bridge_gain_z_above_threshold" if procedure != "vc0" else "no_bridge_evidence"
    return ProcedureChoice(int(rank), procedure, ROUNDS[procedure], basis, int(len(inner_by_rank[rank])),
                           {str(r): means[r] for r in ranks}, gains)


def select_procedure(Y, X, contexts, groups, items, budget: int, k_bridge: int, **kw) -> ProcedureChoice:
    """`source_replay` then `choose` with the default (hybrid) rule."""

    return choose(source_replay(Y, X, contexts, groups, items, budget, k_bridge, **kw), "hybrid")
