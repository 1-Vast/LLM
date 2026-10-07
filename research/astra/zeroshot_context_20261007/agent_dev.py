"""Agent opportunity analysis on development data only (no API calls).

Episodes: development held-out lines (both worlds, cross-fitted between the two lines) and
training contexts leave-one-out (simple world only). Primary design, registered before running:
each context's 146-label menu is split into two disjoint half-menus by drug hash (73 candidates,
k = 8 first-well screens, m = 5 flags). The full menu (k = 15, m = 10) is reported as secondary.

Scores use the independent replicate well B only: V = sum of validated root deviation energy y_B over
the flags; hits = flags among the menu's top 15% by y_B. Gates (registered here):
  G1 screening changes flags (mean symmetric difference vs no-screen > 0.5 flags per episode)
  G2 the competent knowledge-gradient policy improves V over no-screen on average
  G3 the attainable remainder (hindsight screen-oracle minus KG) is at least delta_agent in some world
  G0 (factorial only) the STATE world's calibrated STATE coefficient is not zero
delta_agent = median over development episodes of [mean y_B of the true top-m minus the menu median y_B]:
the value of turning one typical candidate into one typical true responder (one validated responder).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_data as ad  # noqa: E402
import agent_policy as ap  # noqa: E402
import world_models as wm  # noqa: E402
from world_dev import panel_keys  # noqa: E402

OUT = HERE / "agent_dev"
DESIGNS = {"half": {"menus": 2, "k": 8, "m": 5}, "full": {"menus": 1, "k": 15, "m": 10}}
FEATURES_SIMPLE = ("zdisp_B", "dev_B", "m0energy_B")


def menus(rows, n_menus):
    drugs = sorted({r["drug"] for r in rows}, key=lambda d: hashlib.sha256(f"menu:{d}".encode()).hexdigest())
    assign = {d: i % n_menus for i, d in enumerate(drugs)}
    return [[r for r in rows if assign[r["drug"]] == i] for i in range(n_menus)]


def design_matrix(rows, extra=()):
    cols = FEATURES_SIMPLE + tuple(extra)
    X = np.array([[1.0] + [float(ad.root(r[c])) for c in cols] for r in rows])
    return X


def fit_ols(X, y, ridge=1e-6):
    return np.linalg.solve(X.T @ X + ridge * np.eye(X.shape[1]), X.T @ y)


def ledoit_wolf(R):
    """Shrink a residual matrix's correlation toward identity (Ledoit-Wolf 2004 intensity)."""
    X = R - R.mean(0)
    n, p = X.shape
    S = X.T @ X / n
    sd = np.sqrt(np.maximum(np.diag(S), 1e-12))
    C = S / np.outer(sd, sd)
    Xs = X / sd
    pi = np.mean([(np.outer(x, x) - C) ** 2 for x in Xs], axis=0).sum()
    gamma = ((C - np.eye(p)) ** 2).sum()
    delta = float(np.clip(pi / n / max(gamma, 1e-12), 0, 1))
    return (1 - delta) * C + delta * np.eye(p), delta


def episode_values(rows, prior_mean, prior_sd, corr, a, b, obs_sd, k, m, seeds=(0, 1, 2)):
    """Run every registered policy on one menu; returns values and diagnostics (development only)."""
    yB = np.array([r["y_B"] for r in rows])
    yA = np.array([r["y_A"] for r in rows])
    n = len(rows)
    cov = np.outer(prior_sd, prior_sd) * corr
    make = lambda: ap.Belief(prior_mean.copy(), cov.copy(), np.full(n, obs_sd ** 2), b, a)
    top_R = set(np.argsort(-yB)[:max(1, int(round(0.15 * n)))].tolist())
    value = lambda f: float(yB[f].sum())
    hits = lambda f: int(len(set(f) & top_R))
    out = {}
    base_flags = ap.flags(make(), m)
    out["none"] = {"V": value(base_flags), "hits": hits(base_flags), "screens": 0, "flags": base_flags}
    prior_order = list(np.lexsort((np.arange(n), -prior_mean)))
    for name, policy in (("top_prior", ap.choose_top_prior), ("ucb", ap.choose_ucb), ("kg", ap.choose_kg)):
        f, order = ap.run_episode(make(), yA, k, m, policy, prior_order=prior_order)
        out[name] = {"V": value(f), "hits": hits(f), "screens": len(order), "flags": f, "order": order}
    rv = []
    for s in seeds:
        f, order = ap.run_episode(make(), yA, k, m, ap.choose_random, rng=np.random.default_rng(s))
        rv.append((value(f), hits(f)))
    out["random"] = {"V": float(np.mean([x[0] for x in rv])), "hits": float(np.mean([x[1] for x in rv])), "screens": k}
    oracle_flags = list(np.argsort(-yB)[:m])
    out["perfect_information"] = {"V": value(oracle_flags), "hits": hits(oracle_flags)}
    hindsight = list(np.argsort(-yB)[:k])
    belief = make()
    for i in hindsight:
        belief.update(int(i), yA[i])
    f = ap.flags(belief, m)
    out["screen_oracle"] = {"V": value(f), "hits": hits(f), "note": "hindsight: screens the true top-k by y_B"}
    out["kg_changed_flags"] = len(set(out["kg"]["flags"]) ^ set(base_flags)) / 2
    out["delta_one_responder"] = float(yB[oracle_flags].mean() - np.median(yB))
    out["n"] = n
    return out


def main():
    OUT.mkdir(exist_ok=True)
    started = time.perf_counter()
    dev_world = json.loads((HERE / "world_dev" / "DEV_RESULTS.json").read_text(encoding="utf-8"))
    v, fam, lam = dev_world["M0"]["selected"], dev_world["M1"]["selected_family"], dev_world["krr_lambda"]["selected"]
    panel = wm.Panel(panel_keys())
    wells = ad.menu_labels()
    meta = ad.drug_metadata()
    train_tables = {}
    for li, file in enumerate(panel.files):
        rows = ad.training_table(li, panel, wells, fam, lam, meta)
        if len(rows) >= 0.9 * len(wells):
            train_tables[file] = rows
    held = {n: ad.heldout_table(n, panel, wells, v, fam, lam, meta) for n in wm.SPLIT["development"]}
    for name, rows in {**train_tables, **held}.items():
        (OUT / "tables").mkdir(exist_ok=True)
        (OUT / "tables" / f"{name.replace('/', '_').replace(' ', '_')}.json").write_text(json.dumps(rows), encoding="utf-8")
    labels = sorted(wells)
    # Simple-world prior: OLS on training contexts, 5 context folds for training episodes.
    files = sorted(train_tables)
    fold = {f: i % 5 for i, f in enumerate(sorted(files, key=lambda f: hashlib.sha256(f.encode()).hexdigest()))}
    def stack(fs):
        rows = [r for f in fs for r in train_tables[f]]
        return design_matrix(rows), np.array([r["y_B"] for r in rows]), rows
    pred_train, resid = {}, {}
    for k in range(5):
        X, y, _ = stack([f for f in files if fold[f] != k])
        beta = fit_ols(X, y)
        for f in files:
            if fold[f] == k:
                Xf = design_matrix(train_tables[f])
                pred_train[f] = Xf @ beta
                resid[f] = np.array([r["y_B"] for r in train_tables[f]]) - pred_train[f]
    X_all, y_all, _ = stack(files)
    beta_simple = fit_ols(X_all, y_all)
    sd_train = float(np.std(np.concatenate(list(resid.values()))))
    # Residual correlation across menu labels (training contexts), Ledoit-Wolf shrinkage.
    full_ctx = [f for f in files if [r["label"] for r in train_tables[f]] == labels]
    Rmat = np.array([resid[f] for f in full_ctx])
    corr, shrink = ledoit_wolf(Rmat)
    # Screen observation model on training contexts (32-cell wells).
    ya = np.concatenate([[r["y_A"] for r in train_tables[f]] for f in files])
    yb = np.concatenate([[r["y_B"] for r in train_tables[f]] for f in files])
    bt, at = np.polyfit(yb, ya, 1)
    obs_sd_train = float(np.std(ya - (at + bt * yb)))
    # Development held-out lines: simple prior from training fit; STATE prior and observation model cross-fitted.
    names = list(held)
    calib = {}
    for n in names:
        rows = held[n]
        simple = design_matrix(rows) @ beta_simple
        calib[n] = {"simple": simple, "yB": np.array([r["y_B"] for r in rows]), "yA": np.array([r["y_A"] for r in rows]),
                    "state": np.array([float(ad.root(r["state_B"])) for r in rows])}
    world = {}
    for n in names:
        other = [o for o in names if o != n][0]
        co = calib[other]
        Xs = np.column_stack([np.ones(len(co["simple"])), co["state"]])
        coef = fit_ols(Xs, co["yB"] - co["simple"])
        b_h, a_h = np.polyfit(co["yB"], co["yA"], 1)
        obs_sd_h = float(np.std(co["yA"] - (a_h + b_h * co["yB"])))
        sd_simple = float(np.std(co["yB"] - co["simple"]))
        state_pred = calib[n]["simple"] + coef[0] + coef[1] * calib[n]["state"]
        sd_state = float(np.std(co["yB"] - (co["simple"] + coef[0] + coef[1] * co["state"])))
        world[n] = {"simple": (calib[n]["simple"], sd_simple), "state": (state_pred, sd_state),
                    "state_coef": coef.tolist(), "obs": (a_h, b_h, obs_sd_h)}
    results = {"created_utc": datetime.now(timezone.utc).isoformat(), "designs": DESIGNS,
               "menu_labels": len(labels), "training_contexts": len(files), "full_label_contexts_for_correlation": len(full_ctx),
               "simple_prior_coefficients": dict(zip(("intercept",) + FEATURES_SIMPLE, beta_simple.tolist())),
               "simple_prior_residual_sd_training": sd_train, "correlation_shrinkage": shrink,
               "training_observation_model": {"intercept": at, "slope": bt, "sd": obs_sd_train},
               "heldout_calibration": {n: {"state_coef": world[n]["state_coef"], "sd_simple": world[n]["simple"][1],
                                           "sd_state": world[n]["state"][1], "obs": list(world[n]["obs"])} for n in names},
               "M0_variant": v, "M1_family": fam, "krr_lambda": lam}
    label_index = {l: i for i, l in enumerate(labels)}
    episodes = []
    for dname, d in DESIGNS.items():
        for f in files:
            rows = train_tables[f]
            for mi, menu in enumerate(menus(rows, d["menus"])):
                idx = [rows.index(r) for r in menu]
                li = [label_index[r["label"]] for r in menu]
                res = episode_values(menu, pred_train[f][idx], np.full(len(idx), sd_train), corr[np.ix_(li, li)],
                                     at, bt, obs_sd_train, d["k"], d["m"])
                episodes.append({"design": dname, "context": f, "kind": "training_loo", "world": "simple", "menu": mi, **strip(res)})
        for n in names:
            rows = held[n]
            a_h, b_h, sd_h = world[n]["obs"]
            for wname in ("simple", "state"):
                mean, sd = world[n][wname]
                for mi, menu in enumerate(menus(rows, d["menus"])):
                    idx = [rows.index(r) for r in menu]
                    li = [label_index[r["label"]] for r in menu]
                    res = episode_values(menu, mean[idx], np.full(len(idx), sd), corr[np.ix_(li, li)], a_h, b_h, sd_h, d["k"], d["m"])
                    episodes.append({"design": dname, "context": n, "kind": "heldout_dev", "world": wname, "menu": mi, **strip(res)})
    (OUT / "episodes.json").write_text(json.dumps(episodes, indent=1), encoding="utf-8")
    summary = {}
    for dname in DESIGNS:
        for kind, wname in (("training_loo", "simple"), ("heldout_dev", "simple"), ("heldout_dev", "state")):
            eps = [e for e in episodes if e["design"] == dname and e["kind"] == kind and e["world"] == wname]
            if not eps:
                continue
            row = {"episodes": len(eps)}
            for p in ("none", "top_prior", "ucb", "kg", "random", "screen_oracle", "perfect_information"):
                row[f"V_{p}"] = float(np.mean([e[p]["V"] for e in eps]))
                row[f"hits_{p}"] = float(np.mean([e[p]["hits"] for e in eps]))
            row["kg_changed_flags"] = float(np.mean([e["kg_changed_flags"] for e in eps]))
            row["kg_minus_none"] = row["V_kg"] - row["V_none"]
            row["remainder_screen_oracle_minus_kg"] = row["V_screen_oracle"] - row["V_kg"]
            row["best_deterministic"] = max(("top_prior", "ucb", "kg"), key=lambda p: row[f"V_{p}"])
            row["delta_one_responder_median"] = float(np.median([e["delta_one_responder"] for e in eps]))
            summary[f"{dname}|{kind}|{wname}"] = row
    delta_agent = float(np.median([e["delta_one_responder"] for e in episodes if e["design"] == "half"]))
    gates = {}
    for dname in DESIGNS:
        for wname in ("simple", "state"):
            key = f"{dname}|heldout_dev|{wname}"
            s = summary[key]
            gates[key] = {"G1_changes_flags": s["kg_changed_flags"] > 0.5, "G2_kg_improves": s["kg_minus_none"] > 0,
                          "G3_remainder_at_least_delta_agent": s["remainder_screen_oracle_minus_kg"] >= delta_agent}
        s = summary[f"{dname}|training_loo|simple"]
        gates[f"{dname}|training_loo|simple"] = {"G1_changes_flags": s["kg_changed_flags"] > 0.5, "G2_kg_improves": s["kg_minus_none"] > 0,
                                                 "G3_remainder_at_least_delta_agent": s["remainder_screen_oracle_minus_kg"] >= delta_agent}
    results.update(summary=summary, delta_agent=delta_agent, gates=gates,
                   G0_state_coefficient_nonzero={n: abs(world[n]["state_coef"][1]) > 0 for n in names},
                   seconds=round(time.perf_counter() - started, 2), api_calls=0)
    (OUT / "AGENT_DEV_RESULTS.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps({k: results[k] for k in ("summary", "delta_agent", "gates", "heldout_calibration", "simple_prior_coefficients", "correlation_shrinkage")}, indent=1))


def strip(res):
    out = {}
    for k, v in res.items():
        if isinstance(v, dict):
            out[k] = {kk: (vv if not isinstance(vv, np.ndarray) else vv.tolist()) for kk, vv in v.items()}
        else:
            out[k] = v
    return out


if __name__ == "__main__":
    main()
