"""Conformal selection versus fixed-budget nomination on the EXPOSED PRISM -> CTRP triage split (exploratory, post hoc).

Plan, fixed before the first run (2026-10-14):
  Unit of selection: a compound-cell pair. Outcome: the registered validated selective hit in CTRP v2
  (`evaluate_registered.registered_outcomes`). Cost: one CTRP confirmation curve per selected pair. A selected
  pair without a post-QC curve is consumed and is not a hit; such pairs are never used for training or
  calibration because they have no label.
  Scores: `ML+context` (the frozen gradient-boosted classifier on screen + context features, T1), `ML`
  (screen only) and `D3` (-z_r, deterministic). Conformal p-values follow Jin and Candes (2023) for the binary
  outcome: p_j = (1 + #{calibration non-hits with score > score_j}) / (n_cal + 1); selection is Benjamini-Hochberg
  at q in {0.05, 0.1, 0.2, 0.3}. Every method nominates the same number of pairs when compared at matched budget.
  Three regimes with the same training and calibration sizes, 10 random repeats each:
    R1 random compound split of development (compounds exchangeable; pairs of one compound still correlated)
    R2 development split by mechanism family (family shift inside development)
    R3 training and calibration from development, test = the frozen test split (family-disjoint by design)
  Weighted conformal p-values (R3 only) use a logistic density-ratio estimate; they address covariate shift only.
  Nothing here is a confirmation: development and test outcomes were exposed to earlier studies, and the
  ML+context comparator was itself a post hoc choice. The frozen study files are only read.

    python research/mechanism_falsification_20261014/conformal_triage.py   # writes CONFORMAL_TRIAGE.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parent
TRIAGE = STUDY.parent / "selective_hit_triage_20261013"
sys.path.insert(0, str(TRIAGE))

from arms import FEATURE_SETS, fit_model, load_table, predict  # noqa: E402
from dev import labels  # noqa: E402
from evaluate_registered import registered_outcomes  # noqa: E402
from outcomes import qualified_outcomes  # noqa: E402

QS = (0.05, 0.1, 0.2, 0.3)
REPEATS = 10
TRAIN_FRAC, CAL_FRAC = 0.40, 0.30
SEED = 20261014


def conformal_p(cal_score: np.ndarray, cal_hit: np.ndarray, test_score: np.ndarray, w_cal=None, w_test=None) -> np.ndarray:
    nulls = np.sort(cal_score[~cal_hit])
    greater = len(nulls) - np.searchsorted(nulls, test_score, side="right")
    if w_cal is None:
        return (1.0 + greater) / (len(cal_score) + 1.0)
    order = np.argsort(-cal_score[~cal_hit])
    ws = w_cal[~cal_hit][order]
    cum = np.concatenate([[0.0], np.cumsum(ws)])
    k = np.searchsorted(-cal_score[~cal_hit][order], -test_score, side="left")
    return (w_test + cum[k]) / (w_cal.sum() + w_test)


def bh(p: np.ndarray, q: float) -> np.ndarray:
    m = len(p)
    order = np.argsort(p, kind="stable")
    ok = np.flatnonzero(p[order] <= q * np.arange(1, m + 1) / m)
    sel = np.zeros(m, bool)
    if ok.size:
        sel[order[: ok.max() + 1]] = True
    return sel


def top_k(score: np.ndarray, k: int) -> np.ndarray:
    sel = np.zeros(len(score), bool)
    if k:
        sel[np.argsort(-score, kind="stable")[:k]] = True
    return sel


def metrics(sel: np.ndarray, hit: np.ndarray, evaluable: np.ndarray, pan: np.ndarray) -> dict:
    n = int(sel.sum())
    hits_sel = int((sel & hit).sum())
    total = int(hit.sum())
    unsel = int((~sel).sum())
    return {"selected": n, "hits": hits_sel, "FDP": (1 - hits_sel / n) if n else None, "recall": hits_sel / max(1, total),
            "false_omission_rate": int((~sel & hit).sum()) / max(1, unsel), "qc_failed_consumed": int((sel & ~evaluable).sum()),
            "share_in_pan_active_compounds": (int((sel & pan).sum()) / n) if n else None}


def summarise(rows: list[dict]) -> dict:
    out = {}
    for key in rows[0]:
        vals = np.array([r[key] for r in rows if r[key] is not None], float)
        out[key] = None if not vals.size else {"mean": round(float(vals.mean()), 4), "min": round(float(vals.min()), 4), "max": round(float(vals.max()), 4)}
    return out


def split_compounds(rng, cores: list[str], family: dict, mode: str):
    cores = sorted(cores)
    if mode == "random":
        order = list(rng.permutation(len(cores)))
        a, b = int(TRAIN_FRAC * len(cores)), int((TRAIN_FRAC + CAL_FRAC) * len(cores))
        return [{cores[i] for i in order[:a]}, {cores[i] for i in order[a:b]}, {cores[i] for i in order[b:]}]
    fams = sorted({family[c] for c in cores})
    rng.shuffle(fams)
    parts, sizes = [set(), set(), set()], [0, 0, 0]
    targets = [TRAIN_FRAC, CAL_FRAC, 1 - TRAIN_FRAC - CAL_FRAC]
    for f in fams:                                                   # greedy: fill the part furthest below its target share
        members = {c for c in cores if family[c] == f}
        j = int(np.argmax([targets[i] - sizes[i] / len(cores) for i in range(3)]))
        parts[j] |= members
        sizes[j] += len(members)
    return parts


def main() -> None:
    t = load_table()
    split = json.loads((TRIAGE / "SPLIT.json").read_text(encoding="utf-8"))
    family = split["family"]
    dev_out, test_out = qualified_outcomes("development"), registered_outcomes("test")[0]
    dev_rows, test_rows = np.flatnonzero(t["role"] == "development"), np.flatnonzero(t["role"] == "test")
    y_dev, ev_dev, _ = labels(t, dev_rows, dev_out)
    y_test, ev_test, pan_test = labels(t, test_rows, test_out)
    y_dev_pan = labels(t, dev_rows, dev_out)[2]
    core_dev, core_test = t["core"][dev_rows], t["core"][test_rows]
    feats = {"ML+context": FEATURE_SETS["ML+context"], "ML": FEATURE_SETS["ML"]}
    rng_master = np.random.default_rng(SEED)
    results: dict = {"label": "POST HOC, EXPLORATORY, EXPOSED DATA: no confirmatory claim", "plan": __doc__.split("Plan, fixed before the first run (2026-10-14):")[1].split("python research")[0].strip(),
                     "base_rates": {"development_validated_per_evaluable_pair": float(y_dev[ev_dev].mean()), "test_validated_per_evaluable_pair": float(y_test[ev_test].mean()),
                                    "development_compounds": len(set(core_dev)), "test_compounds": len(set(core_test)),
                                    "test_pairs": int(len(test_rows)), "test_evaluable": int(ev_test.sum()), "test_validated": int(y_test.sum())},
                     "regimes": {}}
    detail_r3 = None
    for regime in ("R1_random_compound_split_dev", "R2_family_split_dev", "R3_dev_to_frozen_test"):
        per_rep = {f"{m}|{q}": [] for m in ("conformal_ML+context", "conformal_ML", "conformal_D3") for q in QS}
        per_rep |= {f"fixedk_{m}|{q}": [] for m in ("ML+context", "ML", "D3", "line_prior") for q in QS}
        per_rep |= {f"weighted_ML+context|{q}": [] for q in QS}
        diag = []
        for rep in range(REPEATS):
            rng = np.random.default_rng(int(rng_master.integers(2 ** 31)))
            mode = "random" if regime.startswith(("R1", "R3")) else "family"
            parts = split_compounds(rng, sorted(set(core_dev)), family, mode)
            if regime.startswith("R3"):
                train_c, cal_c = parts[0], parts[1]                        # the third development part is unused
                tr_mask, ca_mask = np.isin(core_dev, sorted(train_c)) & ev_dev, np.isin(core_dev, sorted(cal_c)) & ev_dev
                te_rows_abs, te_y, te_ev, te_pan = test_rows, y_test, ev_test, pan_test
            else:
                tr_mask, ca_mask = np.isin(core_dev, sorted(parts[0])) & ev_dev, np.isin(core_dev, sorted(parts[1])) & ev_dev
                te_mask = np.isin(core_dev, sorted(parts[2]))
                te_rows_abs, te_y, te_ev, te_pan = dev_rows[te_mask], y_dev[te_mask], ev_dev[te_mask], y_dev_pan[te_mask]
            tr_rows, ca_rows = dev_rows[tr_mask], dev_rows[ca_mask]
            y_tr, y_ca = y_dev[tr_mask], y_dev[ca_mask]
            scores_cal, scores_te = {}, {}
            for name, fs in feats.items():
                model = fit_model(t, tr_rows, y_tr, fs)
                scores_cal[name], scores_te[name] = predict(model, t, ca_rows, fs), predict(model, t, te_rows_abs, fs)
            scores_cal["D3"], scores_te["D3"] = -t["z_r"][ca_rows], -t["z_r"][te_rows_abs]
            scores_te["line_prior"] = -t["line_med"][te_rows_abs]
            w_cal = w_te = None
            if regime.startswith("R3") and rep < 3:
                from sklearn.linear_model import LogisticRegression
                cols = FEATURE_SETS["ML+context"]
                xa = np.column_stack([t[f][ca_rows] for f in cols]); xb = np.column_stack([t[f][te_rows_abs] for f in cols])
                mu, sd = np.nanmean(xa, 0), np.nanstd(xa, 0) + 1e-9
                za, zb = np.nan_to_num((xa - mu) / sd), np.nan_to_num((xb - mu) / sd)
                lr = LogisticRegression(max_iter=500, C=0.1).fit(np.vstack([za, zb]), np.r_[np.zeros(len(za)), np.ones(len(zb))])
                ratio = lambda z: np.clip(np.exp(lr.decision_function(z)) * len(za) / len(zb), 0.02, 20.0)  # noqa: E731
                w_cal, w_te = ratio(za), ratio(zb)
                diag.append({"effective_sample_size_fraction": float(w_cal.sum() ** 2 / (w_cal ** 2).sum() / len(w_cal)),
                             "mean_weight_on_calibration": float(w_cal.mean())})
            for q in QS:
                for name in ("ML+context", "ML", "D3"):
                    sel = bh(conformal_p(scores_cal[name], y_ca, scores_te[name]), q)
                    per_rep[f"conformal_{name}|{q}"].append(metrics(sel, te_y, te_ev, te_pan))
                    if name == "ML+context":
                        k = int(sel.sum())
                        for m in ("ML+context", "ML", "D3", "line_prior"):
                            per_rep[f"fixedk_{m}|{q}"].append(metrics(top_k(scores_te[m], k), te_y, te_ev, te_pan))
                if w_cal is not None:
                    sel = bh(conformal_p(scores_cal["ML+context"], y_ca, scores_te["ML+context"], w_cal, w_te), q)
                    per_rep[f"weighted_ML+context|{q}"].append(metrics(sel, te_y, te_ev, te_pan))
            if regime.startswith("R3") and rep == 0:
                detail_r3 = (scores_cal["ML+context"], y_ca, scores_te["ML+context"], te_rows_abs, te_y, te_ev)
            diag_row = {"calibration_hit_rate": float(y_ca.mean()), "test_hit_rate": float(te_y[te_ev].mean()),
                        "calibration_mean_prob": float(scores_cal["ML+context"].mean()), "test_mean_prob": float(scores_te["ML+context"].mean())}
            diag.append(diag_row)
        results["regimes"][regime] = {"repeats": REPEATS, "by_method_and_q": {k: summarise(v) for k, v in per_rep.items() if v},
                                      "diagnostics_mean": {k: round(float(np.mean([d[k] for d in diag if k in d])), 4) for k in {kk for d in diag for kk in d}}}
        print(regime, "done")
    # matched-budget comparison: models fitted on all evaluable development pairs, top-k test pairs, bootstrap over test compounds
    tr_all = dev_rows[ev_dev]
    sc = {}
    for name in ("ML+context", "ML"):
        sc[name] = predict(fit_model(t, tr_all, y_dev[ev_dev], FEATURE_SETS[name]), t, test_rows, FEATURE_SETS[name])
    sc["D3"], sc["line_prior"] = -t["z_r"][test_rows], -t["line_med"][test_rows]
    cores = t["core"][test_rows]
    uniq = sorted(set(cores))
    idx = {c: np.flatnonzero(cores == c) for c in uniq}
    rng = np.random.default_rng(SEED + 1)
    boots = [np.concatenate([idx[uniq[i]] for i in rng.choice(len(uniq), size=len(uniq))]) for _ in range(1000)]
    matched: dict = {}
    for k in (50, 100, 250, 500, 1000):
        sels = {m: top_k(sc[m], k) for m in sc}
        entry = {}
        for m, sel in sels.items():
            met = metrics(sel, y_test, ev_test, pan_test)
            fdp = [1 - (sel[r] & y_test[r]).sum() / max(1, sel[r].sum()) for r in boots]
            entry[m] = {"hits": met["hits"], "FDP": met["FDP"], "FDP_ci95": [float(np.percentile(fdp, 2.5)), float(np.percentile(fdp, 97.5))],
                        "distinct_compounds": len(set(cores[sel])), "share_in_pan_active_compounds": met["share_in_pan_active_compounds"],
                        "qc_failed_consumed": met["qc_failed_consumed"]}
        for other in ("D3", "ML", "line_prior"):
            diff = [(sels["ML+context"][r] & y_test[r]).sum() - (sels[other][r] & y_test[r]).sum() for r in boots]
            entry[f"hits_difference_ML+context_minus_{other}"] = {"observed": int((sels["ML+context"] & y_test).sum() - (sels[other] & y_test).sum()),
                                                                   "ci95": [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))]}
        matched[str(k)] = entry
    results["matched_budget_fixed_k_all_development_fit"] = {"note": "top-k test pairs over the whole pool; the frozen study nominated per 16-compound campaign, so these counts are not comparable with its 38 hits",
                                                              "test_validated_total": int(y_test.sum()), "by_k": matched}
    sel500 = top_k(sc["ML+context"], 500)
    fam: dict = {}
    for k in np.flatnonzero(sel500):
        a = fam.setdefault(family[str(cores[k])], [0, 0])
        a[0] += 1
        a[1] += int(y_test[k])
    results["family_view_k500_ML+context"] = {f: {"selected": a, "hits": h, "FDP": 1 - h / a}
                                              for f, (a, h) in sorted(fam.items(), key=lambda kv: -kv[1][0])[:8]}
    results["structural_power_limit"] = {"test_units_m": int(len(test_rows)), "calibration_units_n_R3": int(len(ca_rows)),
                                         "smallest_possible_p": 1.0 / (len(ca_rows) + 1),
                                         "BH_threshold_for_first_rejection_q0.1": 0.1 / len(test_rows),
                                         "calibration_units_needed_to_reject_one_at_q0.1": int(len(test_rows) / 0.1),
                                         "reading": "with p_min = 1/(n+1), BH can reject k units only if 1/(n+1) <= q k / m, so a pool of m test units needs n >= m/(q k) calibration units"}
    (STUDY / "CONFORMAL_TRIAGE.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("wrote CONFORMAL_TRIAGE.json")


if __name__ == "__main__":
    main()
