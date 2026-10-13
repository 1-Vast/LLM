"""Development analysis: every arm on the 125 development compounds (their CTRP outcomes are opened).

File summary
- Path: research/selective_hit_triage_20261013/dev.py
- Purpose: choose the deterministic comparator, the budget and the decision-layer settings from
  development data only, and disclose what was seen before the test freeze.
- Core points:
  - Learned arms are scored out of fold: five folds grouped by mechanism family, so a compound's
    probability never comes from a model that saw its family.
  - Development compounds are dealt into eight pseudo-campaigns in hash order, mirroring the test
    campaigns. Each campaign nominates ``b x compounds`` pairs.
  - Outputs DEVELOPMENT.json. Nothing here reads a test compound's outcome.
"""
from __future__ import annotations

import hashlib
import json
import sys

import numpy as np

from arms import (CAP, FEATURE_SETS, INSUFFICIENT_EVIDENCE, acquire_secondary, deterministic_scores, fit_model,
                  load_table, nominate, predict)
from census import HERE, ROOT, SPLIT_SALT
from outcomes import ENDPOINT, qualified_outcomes

sys.path.insert(0, str(ROOT))
from tools.evaluation.scoring import cluster_signflip_test  # noqa: E402

BUDGETS = (0.5, 1.0, 2.0)
FOLDS = 5


def labels(t: dict, rows: np.ndarray, outcomes: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y, ev, pan = np.zeros(len(rows), bool), np.zeros(len(rows), bool), np.zeros(len(rows), bool)
    for k, r in enumerate(rows):
        o = outcomes.get(str(t["core"][r]))
        if o is None:
            continue
        pan[k] = o["pan_active"]
        rec = o["lines"].get(str(t["line"][r]))
        if rec is not None:
            ev[k], y[k] = True, rec["validated"]
    return y, ev, pan


def campaigns(cores: list[str], n: int = 8) -> list[list[str]]:
    order = sorted(cores, key=lambda c: hashlib.sha256(f"{SPLIT_SALT}:devcampaign:{c}".encode()).hexdigest())
    return [order[k::n] for k in range(n)]


def run_arm(score: np.ndarray, t: dict, rows: np.ndarray, camps: list[list[str]], b: float) -> np.ndarray:
    """Nominated row indices (into ``rows``) over all campaigns."""
    out = []
    core = t["core"][rows]
    for camp in camps:
        sel = np.flatnonzero(np.isin(core, camp))
        picked = nominate(score[sel], core[sel], t["line"][rows][sel], int(round(b * len(camp))))
        out += list(sel[picked])
    return np.array(out, dtype=int)


def summarise(nom: np.ndarray, y: np.ndarray, ev: np.ndarray, pan: np.ndarray, core: np.ndarray, cores: list[str]) -> dict:
    per = {c: 0 for c in cores}
    for k in nom:
        per[core[k]] += int(y[k])
    return {"nominations": int(len(nom)), "hits": int(y[nom].sum()), "hit_rate": float(y[nom].mean()) if len(nom) else None,
            "not_evaluable": int((~ev[nom]).sum()), "pan_active_nominations": int(pan[nom].sum()),
            "compounds_with_hit": int(sum(v > 0 for v in per.values())), "per_compound": per}


def main() -> None:
    t = load_table()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    cores = split["development"]
    rows = np.flatnonzero(t["role"] == "development")
    outcomes = qualified_outcomes("development")
    y, ev, pan = labels(t, rows, outcomes)
    core = t["core"][rows]
    fam = np.array([split["family"][c] for c in core])
    camps = campaigns(cores)
    res: dict = {"label": "DEVELOPMENT (125 compounds, outcomes opened)", "endpoint": ENDPOINT,
                 "pairs": int(len(rows)), "evaluable_pairs": int(ev.sum()), "validated_pairs": int(y.sum()),
                 "base_rate_evaluable": float(y[ev].mean()),
                 "base_rate_primary_hits": float(y[ev & (t["lfc"][rows] <= -1)].mean()),
                 "compounds_with_any_validated": int(len({c for c, v in zip(core, y) if v})),
                 "pan_active_compounds": int(sum(o["pan_active"] for o in outcomes.values())),
                 "compounds_with_outcomes": len(outcomes)}

    # ---- scores
    scores = {k: v[rows] for k, v in deterministic_scores(t).items()}
    folds = {}
    ufam = sorted(set(fam), key=lambda f: hashlib.sha256(f"{SPLIT_SALT}:fold:{f}".encode()).hexdigest())
    sizes = np.zeros(FOLDS)
    for f in sorted(ufam, key=lambda f: -(fam == f).sum()):
        k = int(np.argmin(sizes))
        folds[f] = k
        sizes[k] += (fam == f).sum()
    fold = np.array([folds[f] for f in fam])
    oof = {}
    for name, feats in FEATURE_SETS.items():
        p = np.full(len(rows), np.nan)
        for k in range(FOLDS):
            tr, te = (fold != k) & ev, fold == k
            if name == "VC+S":
                tr = tr & np.isfinite(t["sec_auc_z"][rows])
            m = fit_model(t, rows[tr], y[tr], feats)
            p[te] = predict(m, t, rows[te], feats)
        oof[name] = p
        scores[name] = p
    has_sec = np.isfinite(t["sec_auc_z"][rows])

    # ---- arms at each budget
    res["arms"] = {}
    for b in BUDGETS:
        res["arms"][str(b)] = {name: summarise(run_arm(s, t, rows, camps, b), y, ev, pan, core, cores) for name, s in scores.items()}
        # closed loop: buy secondary for a quarter of each campaign's compounds
        for rule in ("uncertain", "top"):
            mixed = oof["VC"].copy()
            bought = set()
            for camp in camps:
                sel = np.isin(core, camp)
                got = acquire_secondary(oof["VC"][sel], core[sel], has_sec[sel], int(round(0.25 * len(camp))), rule)
                bought |= got
            use = np.isin(core, list(bought)) & has_sec
            mixed[use] = oof["VC+S"][use]
            s = summarise(run_arm(mixed, t, rows, camps, b), y, ev, pan, core, cores)
            s["secondary_bought"] = len(bought)
            res["arms"][str(b)][f"LOOP_{rule}"] = s
        allsec = np.where(has_sec, oof["VC+S"], oof["VC"])
        s = summarise(run_arm(allsec, t, rows, camps, b), y, ev, pan, core, cores)
        s["secondary_bought"] = int(len(set(core[has_sec])))
        res["arms"][str(b)]["LOOP_all"] = s

    # ---- paired contrasts at b = 1 (compound clusters)
    def per(name, b="1.0"):
        return np.array([res["arms"][b][name]["per_compound"][c] for c in cores], dtype=float)
    det = [k for k in ("D1_magnitude", "D2_compound_z", "D3_two_way_z", "D3f_two_way_z_hits", "D4_target_mutation")]
    res["best_deterministic_by_budget"] = {b: max(det, key=lambda k: res["arms"][b][k]["hits"]) for b in res["arms"]}
    contrasts = {}
    for b in res["arms"]:
        bd = res["best_deterministic_by_budget"][b]
        for a, c in (("VC", bd), ("VC", "ML"), ("ML", bd), ("ML+context", "ML"), ("ML+mechanism", "ML"),
                     ("ML+transcriptional", "ML"), ("LOOP_uncertain", "VC"), ("LOOP_top", "VC"), ("LOOP_all", "VC"),
                     (bd, "zero"), (bd, "random")):
            d = per(a, b) - per(c, b)
            st = cluster_signflip_test(d.tolist(), cores)
            contrasts[f"{b}:{a}-{c}"] = {"difference": float(d.sum()), "p_greater": st["p_greater"], "p_two_sided": st["p_two_sided"]}
    res["contrasts"] = contrasts

    # ---- calibration (out of fold) and abstention for the VC model at b = 1
    p = oof["VC"]
    bins = [0, .05, .1, .2, .3, .5, .7, 1.01]
    res["calibration_VC_oof"] = [{"bin": [lo, hi], "n": int(((p >= lo) & (p < hi) & ev).sum()),
                                  "mean_p": float(p[(p >= lo) & (p < hi) & ev].mean()) if ((p >= lo) & (p < hi) & ev).any() else None,
                                  "rate": float(y[(p >= lo) & (p < hi) & ev].mean()) if ((p >= lo) & (p < hi) & ev).any() else None}
                                 for lo, hi in zip(bins[:-1], bins[1:])]
    nom = run_arm(p, t, rows, camps, 1.0)
    res["abstention_VC_b1"] = {}
    for tau in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        keep = nom[p[nom] >= tau]
        res["abstention_VC_b1"][str(tau)] = {"nominations": int(len(keep)), "hits": int(y[keep].sum()),
                                              "hit_rate": float(y[keep].mean()) if len(keep) else None,
                                              "expected_hits": float(p[keep].sum()), "refusal": INSUFFICIENT_EVIDENCE}
    res["expected_vs_realised_b1"] = {name: {"expected": float(oof[name][run_arm(oof[name], t, rows, camps, 1.0)].sum()),
                                             "realised": res["arms"]["1.0"][name]["hits"]} for name in ("ML", "VC", "VC+S")}
    for b in res["arms"]:
        for v in res["arms"][b].values():
            v.pop("per_compound")
    (HERE / "DEVELOPMENT.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    brief = {b: {k: (v["hits"], v["nominations"]) for k, v in res["arms"][b].items()} for b in res["arms"]}
    print(json.dumps({k: res[k] for k in ("pairs", "evaluable_pairs", "validated_pairs", "base_rate_evaluable", "base_rate_primary_hits",
                                          "compounds_with_any_validated", "pan_active_compounds", "compounds_with_outcomes")}, indent=1))
    print(json.dumps(brief, indent=1))
    print(json.dumps(res["best_deterministic_by_budget"]))
    print(json.dumps(contrasts, indent=1))
    print(json.dumps(res["abstention_VC_b1"], indent=1))
    print(json.dumps(res["calibration_VC_oof"]))
    print(json.dumps(res["expected_vs_realised_b1"]))


if __name__ == "__main__":
    main()
