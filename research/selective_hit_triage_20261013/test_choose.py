"""Frozen test choices: every non-LLM arm's acquisitions and nominations, made before any test outcome opens.

File summary
- Path: research/selective_hit_triage_20261013/test_choose.py
- Purpose: make the pre-registered choices for the 128 test compounds (8 campaigns of 16) from
  pre-confirmation evidence only, and lock them by digest so evaluate.py scores exactly these.
- Core points:
  - Requires FREEZE.json. Only development outcomes are read, to fit the learned arms and the
    calibration; test outcomes are never opened here.
  - Budgets per campaign:
    - B = b x 16 confirmation curves (b in 0.5, 1, 2), at most three lines per compound;
    - in the loop arms, K = 4 compounds receive PRISM secondary dose-response.
  - Loop arms (`loop_scores`): an acquisition rule picks K compounds from pre-acquisition evidence;
    bought compounds are then rescored with their secondary selectivity z. Scores are sums scaled
    by 1/sqrt(number of terms), as settled on development.
    - CONV_LOOP: top acquisition on -z_r.
    - MAESTRO_LOOP: frontier acquisition on -(z_r + ctx).
    - The factorial cells CONV_frontier and MAESTRO_top.
    - The full-cost arms CONV_ALL and MAESTRO_ALL, which buy every available secondary.
  - Scientific Decision Review arms (`review.review_campaign`, SDR_ARMS) store one GO / NO_GO /
    NEED_MORE_EVIDENCE record per compound. MAESTRO_LOOP's records come from the same engine with
    vetoes off, and the run stops if that engine does not reproduce MAESTRO_LOOP's choices
    (REVIEW_ENGINE_MISMATCH).
  - Write-once: TEST_CHOICES.json and CHOICES_LOCK.json. A rerun recomputes and must match the
    locked digest (REPRODUCED), or it stops (CHOICES_MISMATCH).
- Interfaces: `components`, `loop_scores`, `build`, `load_choices`, `pair_id`, `SDR_ARMS`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone

import numpy as np

from arms import FEATURE_SETS, acquire_secondary, deterministic_scores, fit_model, load_table, nominate, predict
from census import HERE
from dev import campaigns as dev_campaigns, labels
from dev_explore2 import K_FRACTION, frontier_pick, top_pick
from outcomes import qualified_outcomes, require_freeze
from review import explanation_features, review_campaign

BUDGETS = (0.5, 1.0, 2.0)
LOOP_ARMS = {"CONV_LOOP": ("conventional", "top"), "MAESTRO_LOOP": ("maestro", "frontier"),
             "CONV_frontier": ("conventional", "frontier"), "MAESTRO_top": ("maestro", "top")}
SDR_ARMS = {"SDR_veto": {"veto": True, "acquire": "frontier"},
            "SDR_acquire": {"veto": False, "acquire": "explanation"},
            "SDR_veto_acquire": {"veto": True, "acquire": "explanation"},
            "SDR_unverified": {"veto": True, "acquire": "frontier", "admit_predictions": True},
            "SDR_full": {"veto": True, "acquire": "explanation", "rerank": True}}
CHOICES = HERE / "TEST_CHOICES.json"
LOCK = HERE / "CHOICES_LOCK.json"


def pair_id(core: str, line: str) -> str:
    return f"{core}|{line}"


def components(t: dict, rows: np.ndarray) -> dict:
    ctx = t["ctx_pred"][rows]
    sec = t["sec_auc_z"][rows]
    return {"zr": t["z_r"][rows], "ctx": np.where(np.isfinite(ctx), ctx, 0.0), "sec": sec, "has": np.isfinite(sec),
            "core": t["core"][rows], "line": t["line"][rows]}


def loop_scores(c: dict, sel: np.ndarray, B: int, K: int, kind: str, rule: str) -> tuple[set, np.ndarray]:
    """Bought compounds and post-acquisition score for one campaign (``sel`` indexes into ``c``)."""
    zr, ctx, sec, has = c["zr"][sel], c["ctx"][sel], c["sec"][sel], c["has"][sel]
    pre, terms = (-zr, 1) if kind == "conventional" else (-(zr + ctx), 2)
    if rule == "top":
        bought = top_pick(pre, c["core"][sel], has, K)
    elif rule == "frontier":
        bought = frontier_pick(pre, c["core"][sel], c["line"][sel], B, has, K)
    elif rule == "all":
        bought = set(c["core"][sel][has])
    else:
        raise ValueError(rule)
    use = np.isin(c["core"][sel], list(bought)) & has
    post = pre / np.sqrt(terms)
    post[use] = (pre[use] - sec[use]) / np.sqrt(terms + 1)
    return bought, post


def _calibrator(score: np.ndarray, bought: np.ndarray, y: np.ndarray) -> dict:
    from sklearn.linear_model import LogisticRegression
    X = np.column_stack([score, bought, score * bought])
    m = LogisticRegression(C=1e4, max_iter=5000).fit(X, y)
    return {"intercept": float(m.intercept_[0]), "coef": [float(v) for v in m.coef_[0]], "features": ["score", "bought", "score_x_bought"]}


def calibrate(cal: dict, score: np.ndarray, bought: np.ndarray) -> np.ndarray:
    X = np.column_stack([score, bought, score * bought])
    return 1.0 / (1.0 + np.exp(-(cal["intercept"] + X @ np.array(cal["coef"]))))


def _dev_calibration(t: dict) -> dict:
    """Map MAESTRO_LOOP and D3 scores to probabilities on development (b = 1 acquisitions)."""
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    rows = np.flatnonzero(t["role"] == "development")
    y, ev, _ = labels(t, rows, qualified_outcomes("development"))
    c = components(t, rows)
    score, bought = np.full(len(rows), np.nan), np.zeros(len(rows))
    for camp in dev_campaigns(split["development"]):
        sel = np.flatnonzero(np.isin(c["core"], camp))
        got, post = loop_scores(c, sel, len(camp), int(round(K_FRACTION * len(camp))), "maestro", "frontier")
        score[sel] = post
        bought[sel] = (np.isin(c["core"][sel], list(got)) & c["has"][sel]).astype(float)
    ok = ev & np.isfinite(score)
    zr_ok = ev & np.isfinite(c["zr"])
    return {"MAESTRO_LOOP": _calibrator(score[ok], bought[ok], y[ok]),
            "D3_two_way_z": _calibrator(-c["zr"][zr_ok], np.zeros(zr_ok.sum()), y[zr_ok]),
            "fitted_on": "development evaluable pairs, MAESTRO_LOOP scores from b = 1 frontier acquisitions"}


def _rerank_coefficients(t: dict, drows: np.ndarray, dy: np.ndarray, dev_ev: np.ndarray) -> dict:
    """SDR_full's breadth re-ranking, fitted once on every decision-relevant development pair (as dev_review.py per fold)."""
    from sklearn.linear_model import LogisticRegression
    c, ex = components(t, drows), explanation_features(t, drows)
    pre = -(c["zr"] + c["ctx"]) / np.sqrt(2)
    relevant = dev_ev & (pre >= 2.0)
    X = np.column_stack([pre, np.log1p(ex["breadth"]), ex["generic_fraction"]])[relevant]
    coef = LogisticRegression(C=1.0, max_iter=2000).fit(X, dy[relevant]).coef_[0]
    return {"beta": float(coef[1] / coef[0]), "gamma": float(-coef[2] / coef[0]), "pairs": int(relevant.sum())}


def build() -> dict:
    t = load_table()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    camps = split["test_campaigns"]
    rows = np.flatnonzero(t["role"] == "test")
    c = components(t, rows)
    pairs = np.array([pair_id(a, b) for a, b in zip(c["core"], c["line"])])

    # learned arms: fitted once on every evaluable development pair
    drows = np.flatnonzero(t["role"] == "development")
    dy, dev_ev, _ = labels(t, drows, qualified_outcomes("development"))
    learned = {}
    for name, feats in FEATURE_SETS.items():
        tr = dev_ev & (np.isfinite(t["sec_auc_z"][drows]) if name == "VC+S" else True)
        learned[name] = predict(fit_model(t, drows[tr], dy[tr], feats), t, rows, feats)
    static = {k: v[rows] for k, v in deterministic_scores(t).items()}
    static.update(learned)
    static["MAESTRO"] = -(c["zr"] + c["ctx"]) / np.sqrt(2)
    ex = explanation_features(t, rows)
    sdr = _rerank_coefficients(t, drows, dy, dev_ev)

    out: dict = {"label": "TEST CHOICES (made before any test outcome is opened)", "campaigns": camps,
                 "k_secondary_per_campaign": int(round(K_FRACTION * 16)), "budgets": list(BUDGETS), "sdr_rerank": sdr, "arms": {}}
    for b in BUDGETS:
        arms: dict = {}
        for name, s in static.items():
            arms[name] = {"campaigns": []}
            for camp in camps:
                sel = np.flatnonzero(np.isin(c["core"], camp))
                nom = sel[nominate(s[sel], c["core"][sel], c["line"][sel], int(round(b * len(camp))))]
                arms[name]["campaigns"].append({"nominations": pairs[nom].tolist(), "bought": []})
        for name, (kind, rule) in list(LOOP_ARMS.items()) + [("CONV_ALL", ("conventional", "all")), ("MAESTRO_ALL", ("maestro", "all"))]:
            arms[name] = {"campaigns": []}
            for camp in camps:
                sel = np.flatnonzero(np.isin(c["core"], camp))
                B, K = int(round(b * len(camp))), int(round(K_FRACTION * len(camp)))
                bought, post = loop_scores(c, sel, B, K, kind, rule)
                nom = sel[nominate(post, c["core"][sel], c["line"][sel], B)]
                arms[name]["campaigns"].append({"nominations": pairs[nom].tolist(), "bought": sorted(bought)})
        for rule in ("uncertain", "top"):                                   # learned loop arms (dev.py)
            arms[f"LOOP_{rule}"] = {"campaigns": []}
            for camp in camps:
                sel = np.flatnonzero(np.isin(c["core"], camp))
                K = int(round(K_FRACTION * len(camp)))
                bought = acquire_secondary(learned["VC"][sel], c["core"][sel], c["has"][sel], K, rule)
                use = np.isin(c["core"][sel], list(bought)) & c["has"][sel]
                mixed = learned["VC"][sel].copy()
                mixed[use] = learned["VC+S"][sel][use]
                nom = sel[nominate(mixed, c["core"][sel], c["line"][sel], int(round(b * len(camp))))]
                arms[f"LOOP_{rule}"]["campaigns"].append({"nominations": pairs[nom].tolist(), "bought": sorted(bought)})
        for name, opt in [("MAESTRO_LOOP", None)] + list(SDR_ARMS.items()):    # Scientific Decision Review arms
            for ci, camp in enumerate(camps):
                sel = np.flatnonzero(np.isin(c["core"], camp))
                B, K = int(round(b * len(camp))), int(round(K_FRACTION * len(camp)))
                if opt is None:                                             # MAESTRO_LOOP's own decisions, same choices
                    r = review_campaign(c, ex, sel, B, K, veto=False, acquire="frontier")
                    rec = arms[name]["campaigns"][ci]
                    if pairs[sel[r["nominated"]]].tolist() != rec["nominations"] or sorted(r["bought"]) != rec["bought"]:
                        raise SystemExit("REVIEW_ENGINE_MISMATCH: review_campaign does not reproduce MAESTRO_LOOP")
                    rec["decisions"] = r["decisions"]
                    continue
                beta, gamma = (sdr["beta"], sdr["gamma"]) if opt.get("rerank") else (0.0, 0.0)
                r = review_campaign(c, ex, sel, B, K, beta=beta, gamma=gamma, veto=opt["veto"], acquire=opt["acquire"],
                                    admit_predictions=opt.get("admit_predictions", False))
                arms.setdefault(name, {"campaigns": []})["campaigns"].append(
                    {"nominations": pairs[sel[r["nominated"]]].tolist(), "bought": sorted(r["bought"]), "decisions": r["decisions"]})
        for v in arms.values():
            v["nominations"] = sum(len(x["nominations"]) for x in v["campaigns"])
            v["secondary_bought"] = sum(len(x["bought"]) for x in v["campaigns"])
        out["arms"][str(b)] = arms

    # calibrated predictions for the MAESTRO_LOOP and D3 nominations (calibration fitted on development)
    cal = _dev_calibration(t)
    out["calibration"] = cal
    index = {p: k for k, p in enumerate(pairs)}
    out["predicted"] = {}
    for b in BUDGETS:
        for name in ("MAESTRO_LOOP", "D3_two_way_z"):
            preds = []
            for ci, camp in enumerate(camps):
                sel = np.flatnonzero(np.isin(c["core"], camp))
                rec = out["arms"][str(b)][name]["campaigns"][ci]
                if name == "MAESTRO_LOOP":
                    _, post = loop_scores(c, sel, int(round(b * len(camp))), int(round(K_FRACTION * len(camp))), "maestro", "frontier")
                    s = dict(zip(pairs[sel], post))
                    bought = set(rec["bought"])
                    preds += [float(calibrate(cal[name], np.array([s[p]]), np.array([float(p.split("|")[0] in bought and c["has"][index[p]])]))[0])
                              for p in rec["nominations"]]
                else:
                    preds += [float(calibrate(cal[name], np.array([-c["zr"][index[p]]]), np.zeros(1))[0]) for p in rec["nominations"]]
            out["predicted"][f"{name}:{b}"] = preds
    digest = hashlib.sha256()
    for name in sorted(static):
        digest.update(np.ascontiguousarray(np.round(np.where(np.isfinite(static[name]), static[name], -1e9), 10)).tobytes())
    out["static_score_sha256"] = digest.hexdigest()
    return out


def load_choices() -> dict:
    text = CHOICES.read_text(encoding="utf-8")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if hashlib.sha256(text.replace("\r\n", "\n").encode()).hexdigest() != lock["sha256"]:
        raise SystemExit("CHOICES_MISMATCH: TEST_CHOICES.json differs from CHOICES_LOCK.json")
    return json.loads(text)


def main() -> None:
    freeze = require_freeze()
    text = json.dumps(build(), indent=1) + "\n"
    digest = hashlib.sha256(text.encode()).hexdigest()
    if LOCK.exists():
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        if lock["sha256"] != digest:
            raise SystemExit(f"CHOICES_MISMATCH: recomputed {digest} != locked {lock['sha256']}")
        print("REPRODUCED", digest)
        return
    CHOICES.write_bytes(text.encode())
    LOCK.write_bytes((json.dumps({"locked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sha256": digest,
                                  "freeze_locked_utc": freeze["locked_utc"], "python": sys.version.split()[0]}, indent=1) + "\n").encode())
    print("LOCKED", digest)


if __name__ == "__main__":
    main()
