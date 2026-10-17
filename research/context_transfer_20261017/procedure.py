"""Source-verified selection: the Virtual Cell's rank and the agent's procedure in a new domain.

File summary
- Path: research/context_transfer_20261017/procedure.py
- Purpose: before acting on held-out targets, replay the candidate choices on the domain's own
  source contexts (inner cross-validation, judged by hits at the same well budget) and adopt a
  costlier procedure only on evidence. This is the "verify before transferring a procedure" step
  of the transfer review (log/transfer_review_20261017/REVIEW.md s3, s10).
- Core points:
  - `menu_records` does all the compute once: for every outer fold and every rank in RANKS, the
    inner per-context hits of each procedure on source contexts (inner events recomputed from
    source outcomes only; inner folds mirror the outer split) and the outer per-target hits.
  - `choose` is a pure function of the inner records, so selection rules are cheap to compare
    and fully auditable. Rules:
    - "evidence" (final): rank by the one-standard-error rule on the Virtual Cell alone (the
      smallest rank whose paired inner deficit to the best rank is within one SE); then a bridge
      procedure only if its paired inner gain over no bridge has z > 1.645 (one-sided 5%),
      because a bridge costs an extra assay round; the bridge with the larger z wins.
    - "max" (development, disclosed): best mean rank on the Virtual Cell alone; any strictly
      positive bridge gain switches to that bridge.
    - "hybrid": the rank of "max", then the bridge threshold of "evidence".
    - The frozen rule is chosen among these three by the pre-declared criterion in
      RULE_CHOICE.md (minimax relative regret over four development settings).
  - `apply` turns a menu and a rule into per-target `auto` records.
- Interfaces: `menu_records(domain, fid, ...)`, `choose(inner_by_rank, rule)`,
  `apply(menu, rule)` -> ({context: record}, {fold: choice}),
  `with_rule(records, menu, rule)` (adds that rule's `*_{rule}` keys to cached records).
"""
from __future__ import annotations

import numpy as np

import replay
from common import folds, selective_events, tie_order

RANKS = (5, 10, 20, 40)
PROCEDURES = ("vc0", "b_exploit", "b_lookahead")
ROUNDS = {"vc0": 1, "b_exploit": 2, "b_lookahead": 2}
Z_BRIDGE = 1.645


def inner_domain(domain, src, abs_gate, min_measured):
    src = np.asarray(src)
    Ys = domain["Y"][src]
    ev, G = selective_events(Ys, abs_gate, min_measured)
    return {"Y": Ys, "X": domain["X"][src], "events": ev, "G": G, "contexts": domain["contexts"][src],
            "groups": domain["groups"][src], "items": domain["items"]}


def _inner_split(inner, by_group, max_inner_targets, salt):
    keys = inner["groups"] if by_group else inner["contexts"]
    fid = folds(keys, salt + ":inner", 3)
    filt = None
    if max_inner_targets:
        filt = np.zeros(len(fid), bool)
        u = tie_order(inner["contexts"], salt + ":subsample")
        for k in range(3):
            idx = np.flatnonzero(fid == k)
            filt[idx[np.argsort(u[idx])[:max_inner_targets]]] = True
    return fid, filt


def menu_records(domain, fid, budget, k_bridge, abs_gate, min_measured, impute_iters=0, by_group=False,
                 max_inner_targets=None, ranks=RANKS, outer=True, only_folds=None):
    menu = {}
    for k in sorted(set(fid.tolist())):
        if only_folds is not None and k not in only_folds:
            continue
        src = np.flatnonzero(fid != k)
        inner = inner_domain(domain, src, abs_gate, min_measured)
        ifid, filt = _inner_split(inner, by_group, max_inner_targets, f"procedure:{k}")
        entry = {"inner": {}, "outer": {}}
        for r in ranks:
            kw = dict(arms=PROCEDURES, rank=r, abs_gate=abs_gate, min_measured=min_measured,
                      impute_iters=impute_iters)
            recs = replay.run(inner, budget, k_bridge, fold_ids=ifid, context_filter=filt, **kw)
            entry["inner"][r] = [{"context": x["context"], **{p: x[p] for p in PROCEDURES}} for x in recs]
            if outer:
                recs = replay.run(domain, budget, k_bridge, fold_ids=fid, context_filter=fid == k, **kw)
                entry["outer"][r] = [{"context": x["context"], **{p: x[p] for p in PROCEDURES}} for x in recs]
        menu[int(k)] = entry
    return menu


def _paired(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.inf
    return float(d.mean()), float(se)


def choose(inner_by_rank: dict, rule: str = "evidence") -> dict:
    ranks = sorted(inner_by_rank, key=int)
    col = {r: {p: np.array([x[p] for x in inner_by_rank[r]], float) for p in PROCEDURES} for r in ranks}
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
    else:
        b = max(("b_exploit", "b_lookahead"), key=lambda b: (gains[b]["z"], b == "b_exploit"))
        procedure = b if gains[b]["z"] > Z_BRIDGE else "vc0"
    return {"rank": int(rank), "procedure": procedure, "inner_means": {str(r): means[r] for r in ranks},
            "bridge_gains": gains, "inner_targets": int(len(inner_by_rank[rank]))}


def apply(menu: dict, rule: str = "evidence"):
    out, choices = {}, {}
    for k, entry in menu.items():
        ch = choose(entry["inner"], rule)
        choices[int(k)] = ch
        rows = entry["outer"][ch["rank"]] if ch["rank"] in entry["outer"] else entry["outer"][str(ch["rank"])]
        for x in rows:
            out[x["context"]] = {"auto": x[ch["procedure"]], "auto_procedure": ch["procedure"],
                                 "auto_rank": ch["rank"], "auto_rounds": ROUNDS[ch["procedure"]],
                                 **{f"sel_{p}": x[p] for p in PROCEDURES}}
    return out, choices


def with_rule(records: list, menu: dict, rule: str) -> list:
    """Records with `auto_{rule}`, `sel_*_{rule}` etc. recomputed from the stored menu (pure)."""

    auto, _ = apply(menu, rule)
    return [{**r, **{f"{k}_{rule}": v for k, v in auto[r["context"]].items()}} for r in records]
