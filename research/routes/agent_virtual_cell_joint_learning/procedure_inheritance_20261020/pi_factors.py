"""Response-factor learning: regime profiles proposed from released residuals, validated by leave-one-background-out replay of the SAME planner.

mode 'on'  (factor inheritance ON):  start from the previously validated labelling/library, new backgrounds are assigned to it, <= CAND_CAP candidate libraries per generation.
mode 'off' (factor inheritance OFF): start from the empty (null-only) library every generation on the same released data with the same CAND_CAP.
A candidate is an `add` (new profile from >=2 mutually close unexplained residuals) or a `refine` (reassign all backgrounds, recompute profiles). It becomes the incumbent only if
the replay passes the lifecycle rule (gain >= EPS_VAL, wins > losses, wins >= 2; ties never promote). Replays read only released (fully measured) backgrounds.
"""
from __future__ import annotations

import time

import numpy as np

import pi_model as M

CAND_CAP = 12
EPS_VAL = 0.004
B_LIB = 4


def noise_s2(E):
    med = np.median(E)
    mad = np.median(np.abs(E - med))
    return float((1.4826 * mad) ** 2)


def promote_rule(gain, wins, losses):
    return bool(gain >= EPS_VAL and wins > losses and wins >= 2)


def promote_rule_plan(gain, wins, losses):
    """Plan lifecycle on a 4-background validation batch: a plan acts only on the regimes it covers, so `wins >= 2` is unreachable for most batches; the plan rule needs one strict win,
    no more losses than wins and the same gain threshold. The library rule above is unchanged. Every plan record also stores whether the strict library rule would have passed."""
    return bool(gain >= EPS_VAL and wins > losses and wins >= 1)


def compare(u_new, u_old):
    d = np.asarray(u_new) - np.asarray(u_old)
    return {"gain": float(d.mean()), "wins": int((d > 1e-9).sum()), "losses": int((d < -1e-9).sum()), "n": int(len(d))}


def lib_from_labels(E, labels, exclude=None, min_members=2, s2_floor=None):
    """Build a library from labelled residuals. Label 0 = null, 1..m = regimes, -1 = unexplained. Regimes with too few members are dropped."""
    labels = np.asarray(labels)
    use = np.ones(len(labels), bool)
    if exclude is not None:
        use[exclude] = False
    ids = sorted(int(c) for c in np.unique(labels[use]) if c > 0 and (labels[use] == c).sum() >= min_members)
    profiles, counts = [np.zeros(E.shape[1])], [float((labels[use] == 0).sum())]
    resid = [E[use & (labels == 0)]]
    for c in ids:
        sel = use & (labels == c)
        mu = E[sel].mean(0)
        profiles.append(mu)
        counts.append(float(sel.sum()))
        resid.append(E[sel] - mu)
    R = np.vstack(resid) if sum(len(r) for r in resid) else np.zeros((0, E.shape[1]))
    s2 = float((R ** 2).mean()) if len(R) else (s2_floor or 0.0013)
    s2 = max(s2, s2_floor or 0.0)
    return M.Lib(np.array(profiles), counts, s2), ids


def assign(E, profiles, s2_ref):
    """Nearest-profile assignment (null included); -1 when no profile explains the residual vector."""
    P = E.shape[1]
    thr = P * s2_ref * (1 + 4 * np.sqrt(2.0 / P))
    cand = np.vstack([np.zeros(P)] + list(profiles)) if len(profiles) else np.zeros((1, P))
    d2 = ((E[:, None, :] - cand[None, :, :]) ** 2).sum(2)
    lab = d2.argmin(1)
    lab = np.where(d2.min(1) > thr, -1, lab)
    return lab, d2.min(1)


def replay_kg1(E, A, labels, ids_eval, B=B_LIB, s2_floor=None):
    """Leave-one-background-out replay of the Kg1 planner; the recorded vector plays the role of both truth and read table."""
    out = []
    for j in ids_eval:
        lib, _ = lib_from_labels(E, labels, exclude=j, min_members=1, s2_floor=s2_floor)
        camp = M.Camp(A[j], A[j] + E[j], T=A[j] + E[j])
        out.append(M.run_campaign(lib, camp, B, M.Kg1())["utility"])
    return np.array(out)


def _propose_add(E, labels, s2_ref, tried):
    P = E.shape[1]
    un = [i for i in range(len(labels)) if labels[i] == -1 and i not in tried]
    if len(un) < 2:
        return None
    en = [(float((E[i] ** 2).sum()), i) for i in un]
    for _, seed in sorted(en, key=lambda t: (-t[0], t[1])):
        near = [i for i in un if ((E[i] - E[seed]) ** 2).sum() < 2 * P * s2_ref * 1.35]
        if len(near) >= 2:
            new = labels.copy()
            new[near] = max(int(labels.max()), 0) + 1
            return new, seed, near
        tried.add(seed)
    return None


def _propose_refine(E, labels, s2_ref):
    lib, ids = lib_from_labels(E, labels, min_members=2)
    new, _ = assign(E, list(lib.L[1:]), s2_ref)
    # map nearest-profile index (1..) back to label ids
    mapped = np.where(new > 0, np.array([0] + ids)[np.clip(new, 0, len(ids))], new)
    return mapped


def learn(mode, prev_labels, E, A, ids, cap=CAND_CAP):
    """One generation of factor learning. `ids` are the released background ids aligned with the rows of E/A; prev_labels maps id -> label (mode 'on')."""
    t0 = time.process_time()
    s2_ref = noise_s2(E)
    s2_floor = max(s2_ref, 1.5 * M.M2)
    n = len(ids)
    if mode == "on" and prev_labels:
        old = {i: l for i, l in prev_labels.items() if i in ids}
        labels = np.full(n, -2)
        for r, i in enumerate(ids):
            if i in old:
                labels[r] = old[i]
        lib0, kept = lib_from_labels(E[labels > -2], labels[labels > -2], min_members=2) if (labels > -2).any() else (None, [])
        new_idx = np.nonzero(labels == -2)[0]
        if len(new_idx):
            profs = [] if lib0 is None else list(lib0.L[1:])
            lab_new, _ = assign(E[new_idx], profs, s2_ref)
            kmap = np.array([0] + kept)
            labels[new_idx] = np.where(lab_new > 0, kmap[np.clip(lab_new, 0, len(kept))], lab_new)
    else:
        labels, _ = assign(E, [], s2_ref)
    t_in = time.process_time()
    replays = 0
    inc_u = replay_kg1(E, A, labels, range(n), s2_floor=s2_floor)
    replays += n
    records, tried = [], set()
    n_cand, refined = 0, False
    while n_cand < cap:
        prop = _propose_add(E, labels, s2_ref, tried)
        kind = "add"
        if prop is None:
            if refined:
                break
            cand, seed, near = _propose_refine(E, labels, s2_ref), None, None
            kind, refined = "refine", True
            if (cand == labels).all():
                break
        else:
            cand, seed, near = prop
        u = replay_kg1(E, A, cand, range(n), s2_floor=s2_floor)
        replays += n
        n_cand += 1
        cmp = compare(u, inc_u)
        ok = promote_rule(cmp["gain"], cmp["wins"], cmp["losses"])
        records.append({"kind": kind, "seed": None if seed is None else int(ids[seed]), "members": None if near is None else [int(ids[i]) for i in near],
                        "status": "demonstrated" if ok else "rejected", **cmp})
        if ok:
            labels, inc_u = cand, u
            if kind == "add":
                refined = False
        elif kind == "add":
            tried.update(near)
    lib, kept = lib_from_labels(E, labels, min_members=2, s2_floor=s2_floor)
    final = np.where(np.isin(labels, kept) | (labels <= 0), labels, -1)
    return {"labels": {int(i): int(l) for i, l in zip(ids, final)}, "lib": lib, "records": records, "n_candidates": n_cand, "n_replays": replays,
            "cpu_s": time.process_time() - t0, "cpu_search_s": time.process_time() - t_in, "n_regimes": lib.n_regimes}
