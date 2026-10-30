"""Evaluation harness, diagnosis, candidate operators and the generational library loop.

Contracts
  E  end-to-end : all pairs are legal to measure; direct confirmation allowed and counted (direct-measurement replay).
  T  transfer   : probes are legal only on a probe half of the pairs; nominations come from the disjoint other half.
Every method gets the same history, anchors, budget, pool and shortlist size.
"""
from __future__ import annotations

import copy
import hashlib
import json
import time

import numpy as np

import svc_programs as P
from svc_world import SHORTLIST_K, World, realized_utility

BUILTIN_SPLITS = {"real": (9, 3, 3, 3, 6, 15), "synthetic": (6, 2, 2, 2, 4, 8)}
MAX_GENERATIONS = 3
MAX_CANDIDATES = 12


def stable_int(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "little")


def split_cells(cells, kind: str) -> dict:
    order = sorted(cells, key=lambda c: hashlib.sha256(f"svc20261020|{c}".encode()).hexdigest())
    h0, d1, d2, d3, a, t = BUILTIN_SPLITS[kind]
    cuts = np.cumsum([h0, d1, d2, d3, a, t])
    assert cuts[-1] == len(order), (cuts, len(order))
    parts = np.split(np.array(order, dtype=object), cuts[:-1])
    return {k: list(v) for k, v in zip(["H0", "D1", "D2", "D3", "A", "T"], parts)}


def task_masks(static, cell, seed, contract):
    n = static.n
    if contract == "E":
        return None, np.ones(n, bool)
    rng = np.random.default_rng(stable_int("mask", cell, seed))
    probe = np.zeros(n, bool)
    probe[rng.permutation(n)[: n // 2]] = True
    return probe, ~probe


class Clock:
    def __init__(self):
        self.t = {}

    def add(self, key, dt):
        self.t[key] = self.t.get(key, 0.0) + dt

    @property
    def total(self):
        return sum(self.t.values())


CLOCK = Clock()


class Memo:
    """Priors computed once per released history within a process (they depend only on released cells)."""

    def __init__(self, world: World):
        self.world, self.h, self.c = world, {}, {}

    def hist(self, cells):
        k = tuple(cells)
        if k not in self.h:
            self.h[k] = self.world.history(list(cells))
        return self.h[k]

    def cache(self, cells):
        k = tuple(cells)
        if k not in self.c:
            self.c[k] = P.HistoryCache(self.hist(cells))
        return self.c[k]


# ----------------------------------------------------------------------------- arms and running one task
def baseline_arms() -> dict:
    ridge = lambda inter=(), lam=3.0: {"type": "ridge", "inter": list(inter), "lam": lam}  # noqa: E731
    return {
        "zero": {"kind": "zero"},
        "direct": {"kind": "direct"},
        "refit": {"kind": "program", "spec": P.base_spec()},
        "gbm_multitask": {"kind": "program", "spec": {**P.base_spec(), "f": {"type": "gbm", "inter": [], "lam": 3.0}}},
        "latent_fingerprint": {"kind": "program", "spec": {"phi": [{"t": "latent", "k": 3}], "Q": [{"kind": "probe", "frac": 0.5, "rule": "coverage", "cond": None}, {"kind": "confirm", "frac": 0.5}], "f": ridge()}},
        "matrix_completion_aopt": {"kind": "program", "spec": {"phi": [{"t": "latent", "k": 3}], "Q": [{"kind": "probe", "frac": 0.5, "rule": "aoptimal", "cond": None}, {"kind": "confirm", "frac": 0.5}], "f": ridge()}},
        "adequate_interaction": {"kind": "program", "spec": {"phi": [{"t": "global"}, {"t": "latent", "k": 3}], "Q": P.base_spec()["Q"], "f": ridge(("class", "anchor", "product"))}},
        "bayes_voi_joint": {"kind": "program", "spec": {"phi": [{"t": "global"}, {"t": "latent", "k": 3}], "Q": [{"kind": "probe", "frac": 0.5, "rule": "bayes_voi", "cond": None}, {"kind": "confirm", "frac": 0.5}], "f": ridge(("class",))}},
        "capacity_gbm": {"kind": "program", "spec": {"phi": [{"t": "global"}, {"t": "latent", "k": 4}], "Q": P.base_spec()["Q"], "f": {"type": "gbm", "inter": ["class", "anchor", "product"], "lam": 1.0}}},
    }


def run_arm_on_cell(arm, world, memo, static, cell, hist_cells, B, seed, contract, fitted_cache=None):
    """Fit on released `hist_cells` (never containing `cell`), execute on a fresh campaign for `cell`, return decisions + utility."""
    assert cell not in hist_cells
    t0 = time.perf_counter()
    hist, cache = memo.hist(hist_cells), memo.cache(hist_cells)
    probe, pool = task_masks(static, cell, seed, contract)
    campaign = world.campaign(cell, B, probe_mask=probe)
    rng = np.random.default_rng(stable_int("run", cell, seed))
    if arm["kind"] == "zero":
        out = P.baseline_zero(cache.full, static, campaign, pool)
    elif arm["kind"] == "direct":
        if contract == "T":
            raise ValueError("direct confirmation of targets is not a legal action under the transfer contract")
        out = P.baseline_direct(cache.full, static, campaign, pool)
    else:
        key = (canon(arm), tuple(hist_cells), B, seed, contract, cell if contract == "T" else "")
        fit = fitted_cache.get(key) if fitted_cache is not None else None
        if fit is None:
            fit = P.fit_program(arm["spec"], hist, cache, static, B, seed, transfer=(contract == "T"), probe_mask=probe)
            if fitted_cache is not None:
                fitted_cache[key] = fit
        out = P.run_program(fit, static, campaign, rng, pool_mask=pool, transfer=(contract == "T"))
    u = realized_utility(world, campaign, out["nominated"], pool)
    CLOCK.add(arm.get("name", arm["kind"]), time.perf_counter() - t0)
    return {"cell": cell, **u, "nominated": out["nominated"], "spent": campaign.spent, "probed": out.get("probed", []),
            "stage_log": out.get("stage_log", []), "z": out.get("z", []), "pred": out.get("final_prediction"),
            "queried": sorted(campaign.queried)}


def canon(arm):
    return arm["kind"] + (P.canonical(arm["spec"]) if "spec" in arm else "")


def evaluate(arm, world, memo, static, eval_cells, hist_cells, B, seed, contract, nested=False, fitted_cache=None):
    """Per-cell utilities. nested=True: eval cells are inside hist_cells and each is held out of its own fit."""
    res = []
    for c in eval_cells:
        hc = [h for h in hist_cells if h != c] if nested else list(hist_cells)
        res.append(run_arm_on_cell(arm, world, memo, static, c, hc, B, seed, contract, fitted_cache))
    return res


def utilities(res):
    return np.array([r["utility"] for r in res])


# ----------------------------------------------------------------------------- diagnosis
def diagnose(world, memo, static, arm, hist_cells, B, seed, contract, fitted_cache=None):
    """Decision-relevant failure analysis of the incumbent on released cells (nested leave-one-cell-out)."""
    res = evaluate(arm, world, memo, static, hist_cells, hist_cells, B, seed, contract, nested=True, fitted_cache=fitted_cache)
    n, h = static.n, len(hist_cells)
    resid = np.zeros((n, h))
    relevant = np.zeros((n, h), bool)
    for k, r in enumerate(res):
        truth = world.truth_column(hist_cells[k])
        resid[:, k] = truth - r["pred"]
        top_true = np.argsort(-truth)[:2 * SHORTLIST_K]
        top_pred = np.argsort(-r["pred"])[:2 * SHORTLIST_K]
        relevant[np.concatenate([top_true, top_pred]), k] = True
    pc = static.pair_class
    n_cls = len(static.classes)

    def class_scores(rm):
        sc = np.zeros(n_cls)
        for c in range(n_cls):
            sel = (pc == c)[:, None] & relevant
            cnt = sel.sum(0)
            m = np.where(cnt > 0, (rm * sel).sum(0) / np.maximum(cnt, 1), 0.0)
            sc[c] = float(((m - m.mean()) ** 2).sum() * np.sqrt((cnt > 0).sum()))
        return sc

    scores = class_scores(resid)
    rng = np.random.default_rng(stable_int("diag", seed, h))
    null_max = []
    for _ in range(40):                                  # permute which cell each pair's residual came from
        perm = np.stack([rng.permutation(h) for _ in range(n)])
        null_max.append(class_scores(np.take_along_axis(resid, perm, 1)).max())
    floor = float(np.quantile(null_max, 0.95))
    s = np.linalg.svd(resid - resid.mean(1, keepdims=True), compute_uv=False)
    latent_share = float(s[0] ** 2 / max((s ** 2).sum(), 1e-12))
    order = [int(c) for c in np.argsort(-scores) if scores[c] > floor]
    util = utilities(res)
    ref = utilities(evaluate({"kind": "zero"}, world, memo, static, hist_cells, hist_cells, B, seed, contract, nested=True))
    verdict = "explainable" if order else "no_program_explains"
    direct_u = None
    if contract == "E":
        direct_u = float(utilities(evaluate({"kind": "direct"}, world, memo, static, hist_cells, hist_cells, B, seed, contract, nested=True)).mean())
        if direct_u >= util.mean() - 1e-9 and not order:
            verdict = "direct_confirmation_dominates"
    return {"verdict": verdict, "failing_classes": order[:4], "class_scores": np.round(scores, 5).tolist(), "noise_floor": round(floor, 5),
            "latent_share": round(latent_share, 4), "incumbent_dev_utility": float(util.mean()), "zero_dev_utility": float(ref.mean()),
            "direct_dev_utility": direct_u, "decision_relevant_pairs_per_cell": int(relevant.sum(0).mean())}


# ----------------------------------------------------------------------------- operators
REPR_OPS = ("add_class", "add_class_pair", "latent_up", "latent_down", "inter_class", "inter_anchor", "inter_product", "lam_up", "lam_down", "drop_class")
PROC_OPS = ("rule_witness", "rule_aoptimal", "rule_variance", "cond_focus", "frac_more_probe", "frac_less_probe")


def apply_op(spec, op, diag, rng, static):
    s = copy.deepcopy(spec)
    fail = diag["failing_classes"]
    classes = static.classes
    lat = [c for c in s["phi"] if c["t"] == "latent"]
    cls_coords = [c for c in s["phi"] if c["t"] == "class"]
    probe_stages = [st for st in s["Q"] if st["kind"] == "probe"]
    if op == "add_class":
        cand = [c for c in fail if {"t": "class", "a": classes[c][0], "b": classes[c][1]} not in s["phi"]]
        if not cand:
            return None
        c = cand[int(rng.integers(len(cand)))] if len(cand) > 1 else cand[0]
        s["phi"].append({"t": "class", "a": classes[c][0], "b": classes[c][1]})
    elif op == "add_class_pair":
        cand = [c for c in fail if {"t": "class", "a": classes[c][0], "b": classes[c][1]} not in s["phi"]][:2]
        if len(cand) < 2:
            return None
        for c in cand:
            s["phi"].append({"t": "class", "a": classes[c][0], "b": classes[c][1]})
    elif op == "drop_class":
        if not cls_coords:
            return None
        s["phi"].remove(cls_coords[int(rng.integers(len(cls_coords)))])
    elif op == "latent_up":
        if lat:
            if lat[0]["k"] >= 4:
                return None
            lat[0]["k"] += 1
        else:
            s["phi"].append({"t": "latent", "k": 2})
    elif op == "latent_down":
        if not lat or lat[0]["k"] <= 1:
            return None
        lat[0]["k"] -= 1
    elif op in ("inter_class", "inter_anchor", "inter_product"):
        name = op.split("_")[1]
        if name in s["f"]["inter"]:
            return None
        s["f"]["inter"].append(name)
    elif op == "lam_up":
        s["f"]["lam"] = min(300.0, s["f"]["lam"] * 3)
    elif op == "lam_down":
        s["f"]["lam"] = max(0.3, s["f"]["lam"] / 3)
    elif op in ("rule_witness", "rule_aoptimal", "rule_variance"):
        rule = op.split("_")[1]
        if probe_stages[0]["rule"] == rule:
            return None
        probe_stages[0]["rule"] = rule
    elif op == "cond_focus":
        coords = P.entries_of(s)
        idx = [i for i, e in enumerate(coords) if e["t"] in ("class", "latent")]
        if not idx or len(probe_stages) >= 2 or probe_stages[0].get("cond"):
            return None
        i = idx[int(rng.integers(len(idx)))]
        first = probe_stages[0]
        first_frac = first["frac"]
        first["frac"] = round(first_frac * 0.6, 6)
        conf = [st for st in s["Q"] if st["kind"] == "confirm"]
        second = {"kind": "probe", "frac": round(first_frac - first["frac"], 6), "rule": "witness", "cond": {"coord": i, "thr": 0.5, "else": "confirm"}}
        s["Q"].insert(1, second)
    elif op in ("frac_more_probe", "frac_less_probe"):
        conf = [st for st in s["Q"] if st["kind"] == "confirm"]
        if not conf:
            return None
        d = 0.25 if op == "frac_more_probe" else -0.25
        new = round(conf[0]["frac"] - d, 6)
        if not 0.1 <= new <= 0.9:
            return None
        conf[0]["frac"] = new
        # redistribute onto the probe stages proportionally
        tot = sum(st["frac"] for st in probe_stages)
        for st in probe_stages:
            st["frac"] = round(st["frac"] / tot * (1 - new), 6)
        probe_stages[-1]["frac"] = round(1 - new - sum(st["frac"] for st in probe_stages[:-1]), 6)
    else:
        raise ValueError(op)
    errs = P.validate_spec(s, static)
    return None if errs else s


def propose(spec, diag, static, seed, gen, ops, k=MAX_CANDIDATES):
    rng = np.random.default_rng(stable_int("propose", seed, gen, P.canonical(spec)))
    out, seen = [], {P.canonical(spec)}
    from itertools import zip_longest
    reprs, procs = [o for o in ops if o in REPR_OPS], [o for o in ops if o in PROC_OPS]
    order = [o for pair in zip_longest(reprs, procs) for o in pair if o is not None]      # interleave so the 12-candidate cap does not favour one family
    for round_ in range(3):                       # a few passes so random-choice operators can return different specs
        for op in order:
            s = apply_op(spec, op, diag, rng, static)
            if s is None:
                continue
            key = P.canonical(s)
            if key in seen:
                continue
            seen.add(key)
            out.append({"op": op, "spec": s})
        if len(out) >= k:
            break
    # combine two single edits (compositional candidates)
    base = list(out)
    for i in range(len(base)):
        for j in range(i + 1, len(base)):
            if len(out) >= k:
                break
            if base[i]["op"].split("_")[0] == base[j]["op"].split("_")[0]:
                continue
            s = apply_op(base[i]["spec"], base[j]["op"], diag, rng, static)
            if s is not None and P.canonical(s) not in seen:
                seen.add(P.canonical(s))
                out.append({"op": base[i]["op"] + "+" + base[j]["op"], "spec": s})
    return out[:k]


# ----------------------------------------------------------------------------- library loop
class Library:
    def __init__(self, name):
        self.name, self.entries, self.counter = name, [], 0
        self.log = []

    def add(self, spec, parent, op, gen, status):
        self.counter += 1
        e = {"id": f"{self.name}-p{self.counter:02d}", "spec": spec, "parent": parent, "op": op, "gen": gen, "status": status, "evidence": {}}
        self.entries.append(e)
        return e

    def get(self, pid):
        return next(e for e in self.entries if e["id"] == pid)


def validate(lib, incumbent, new_cells, hist_cells, name, world, memo, static, B, seed, contract, fitted_cache):
    """Judge a provisional program on cells released after it was selected; demonstrate it or retire it and restore the parent."""
    parent = lib.get(incumbent["parent"])
    hc_before = [c for c in hist_cells if c not in new_cells]
    a = utilities(evaluate({"kind": "program", "spec": incumbent["spec"], "name": name}, world, memo, static, new_cells, hc_before, B, seed, contract, fitted_cache=fitted_cache))
    b = utilities(evaluate({"kind": "program", "spec": parent["spec"], "name": name}, world, memo, static, new_cells, hc_before, B, seed, contract, fitted_cache=fitted_cache))
    gain = float((a - b).mean())
    incumbent["evidence"]["validation"] = {"cells": list(new_cells), "paired_gain": gain, "wins": int((a > b).sum()), "n": len(a)}
    if gain >= 0 and (a >= b).sum() >= np.ceil(len(a) / 2):
        incumbent["status"] = "demonstrated"
        return incumbent, None
    incumbent["status"] = "retired"
    return parent, incumbent["id"]


def evolve(name, world, memo, static, cells, seed, B, contract, ops, inherit=True, delta_acc=0.0015, win_frac=0.6, generations=MAX_GENERATIONS,
           fitted_cache=None, candidate_fn=None):
    """Generational loop. Returns the library (with status transitions) and per-generation records.

    Rules fixed before comparative scoring: a candidate is ACCEPTED (provisional) when its mean paired dev gain over the incumbent is
    >= delta_acc on the released cells and it wins on >= win_frac of them; a provisional program is DEMONSTRATED when it does not lose
    to its parent on the next batch of cells not used to select it, else RETIRED (parent restored). The best of 12 candidates by dev
    score is the only one nominated each generation."""
    lib = Library(name)
    root = lib.add(P.base_spec(), None, "base", 0, "demonstrated")
    incumbent, records = root, []
    hist_cells = list(cells["H0"])
    for g in range(1, generations + 1):
        rec = {"gen": g, "history_cells": list(hist_cells)}
        if not inherit:                                   # learned programs are deleted, raw history is kept
            incumbent = root
        elif g > 1 and incumbent["status"] == "provisional":
            incumbent, retired = validate(lib, incumbent, cells[f"D{g - 1}"], hist_cells, name, world, memo, static, B, seed, contract, fitted_cache)
            if retired:
                rec["retired"] = retired
        arm = {"kind": "program", "spec": incumbent["spec"], "name": name}
        diag = diagnose(world, memo, static, arm, hist_cells, B, seed, contract, fitted_cache)
        rec["diagnosis"] = diag
        cands = []
        if candidate_fn is not None:                      # external proposer (API arm): it sees the diagnosis and may answer "none"
            cands = candidate_fn(g, diag, incumbent["spec"], hist_cells)
        elif diag["verdict"] == "explainable":
            seed_spec = incumbent["spec"] if inherit else P.base_spec()
            cands = propose(seed_spec, diag, static, seed, g, ops)
        rec["n_candidates"] = len(cands)
        base_u = utilities(evaluate(arm, world, memo, static, hist_cells, hist_cells, B, seed, contract, nested=True, fitted_cache=fitted_cache))
        if not inherit and diag["verdict"] == "explainable":
            # the restarted search is compared with the incumbent it did not inherit from
            pass
        scored = []
        for c in cands:
            u = utilities(evaluate({"kind": "program", "spec": c["spec"], "name": name}, world, memo, static, hist_cells, hist_cells, B, seed, contract, nested=True, fitted_cache=fitted_cache))
            wins, losses = int((u > base_u + 1e-12).sum()), int((u < base_u - 1e-12).sum())
            scored.append({**c, "dev_mean": float(u.mean()), "gain": float((u - base_u).mean()), "wins": wins, "losses": losses,
                           "win_frac": wins / (wins + losses) if wins + losses else 0.0})              # ties are not decisive cells
        rec["candidates"] = [dict(s) for s in scored]               # specs kept: every accepted/rejected candidate is auditable
        rec["candidate_specs"] = [s["spec"] for s in scored]
        rec["incumbent_dev_mean"] = float(base_u.mean())
        accepted = [s for s in scored if s["gain"] >= delta_acc and s["win_frac"] >= win_frac]
        if accepted:
            best = max(accepted, key=lambda s: (s["gain"], P.canonical(s["spec"])))
            ent = lib.add(best["spec"], incumbent["id"], best["op"], g, "provisional")
            ent["evidence"]["selection"] = {"dev_gain": best["gain"], "win_frac": best["win_frac"], "n_dev_cells": len(hist_cells), "diagnosis_failing_classes": diag["failing_classes"]}
            incumbent = ent
            rec["accepted"] = ent["id"]
        else:
            rec["accepted"] = None
            rec["reason"] = diag["verdict"] if not cands else "no candidate met the acceptance rule"
        rec["incumbent_after"] = incumbent["id"]
        records.append(rec)
        hist_cells = hist_cells + list(cells[f"D{g}"])
    if inherit and incumbent["status"] == "provisional":
        incumbent, retired = validate(lib, incumbent, cells[f"D{generations}"], hist_cells, name, world, memo, static, B, seed, contract, fitted_cache)
        if retired:
            records[-1]["retired_after"] = retired
    final_cells = list(hist_cells)
    return lib, incumbent, records, final_cells


def program_json(entry, fitted: P.Fitted | None, static):
    d = {"id": entry["id"], "parent": entry["parent"], "op": entry["op"], "gen": entry["gen"], "status": entry["status"], "evidence": entry["evidence"], "spec": entry["spec"],
         "omega": omega_of(entry, static)}
    if fitted is not None and fitted.gbm is None:
        d["fitted"] = fitted.to_json()
    return d


def omega_of(entry, static):
    """Applicability, unknowns, support, counterexamples and version dependencies of a program (declared, not tested)."""
    spec = entry["spec"]
    return {"requires": ["monotherapy-derived reference and activity range", "released history cells (version-pinned below)"],
            "scope_classes": [[c["a"], c["b"]] for c in spec["phi"] if c["t"] == "class"],
            "unknowns": ["effect outside the listed module classes", "doses/time other than the 4x4 grid endpoint A", "cells unlike the released history"],
            "support": entry["evidence"].get("selection"), "counterexamples": entry["evidence"].get("validation"),
            "version_dependencies": {"grammar": P.GRAMMAR_VERSION, "history_version": "set at fit"}}
