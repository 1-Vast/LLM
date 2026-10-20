"""Stage logic for the functional-rule-revision pilot (freeze -> challenge -> retention -> final).

All stage functions take a Context (tables, partition, sealed outcome files, configuration) and an
output directory, so the same code runs on the real data and on synthetic fixtures in tests.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

import adapter
import design as D
import evaluation as E
import models as M

CONFIG = {
    "k_shortlist": D.K_SHORTLIST, "n_modules": D.N_MODULES, "panel_pairs": D.PANEL_PAIRS, "folds": M.N_FOLDS,
    "cv_salts": ["cvA", "cvB"], "pilot_salt": "pilot",
    "ridge_configs": [list(c) for c in M.RIDGE_CONFIGS], "gbm_configs": [list(c) for c in M.GBM_CONFIGS],
    "fm_configs": [list(c) for c in M.FM_CONFIGS], "max_configs_per_model": 12, "max_dictionary_edits": 16,
    "margin_default": 0.02, "margin_rule": "min(0.02, round(0.25 * S-estimated regret of the fixed model, 3))",
    "retention": {"tau_fraction_of_margin": 0.5, "mse_ratio_tolerance": 0.02},
    "counterexample_abs_z": 2.0,
    "edit_guard": {"min_relative_cv_change_all": -0.0025, "min_scope_pairs_source_and_challenge": 10,
                   "min_scope_pairs_challenge": 3, "min_unmeasured_scope_pairs": 2},
    "bootstrap": {"n": 2000, "seed": 20261020, "alpha": 0.05, "primary_contrasts": 3, "cell_bootstrap_n": 1000},
    "pilot_pool_pairs": None, "pilot_pools": 300,
    "api": {"enabled": True, "arm": "LLM edit selection over the same dictionary and evidence table",
            "max_http_attempts": 4, "max_logical_requests": 2, "max_output_tokens": 1024, "max_input_tokens": 6000,
            "top_counterexamples_sent": 25},
}


def jdump(path: Path, obj) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, default=_default) + "\n",
                          encoding="utf-8", newline="\n")


def jload(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def digest_obj(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=_default).encode()).hexdigest()


# --------------------------------------------------------------------------- context
class Context:
    def __init__(self, T: adapter.GroupTable, role_pair, sealed_dir: Path, cfg: dict = CONFIG, state_path: Path | None = None):
        self.T, self.cfg = T, cfg
        self.role_pair = np.asarray(role_pair)
        self.role_g = self.role_pair[T.g_pair]
        self.vault = adapter.OutcomeVault(sealed_dir, T.g_pair, {p: r for p, r in enumerate(self.role_pair)}, state_path=state_path)
        n_drugs, n_cells = len(T.drugs), len(T.cells)
        self.panel_mat = D.drug_cell_panel(T.g_i, T.g_j, T.g_cell, T.a_mono_i, T.a_mono_j, T.eligible, n_drugs, n_cells)
        self.module = D.make_modules(self.panel_mat, cfg["n_modules"])
        self.gates = D.make_gates(self.panel_mat, self.module)
        self.rules = D.build_dictionary(cfg["n_modules"])
        self.rule_by_id = {r.id: r for r in self.rules}
        ok = T.eligible
        self.rows_S = np.nonzero((self.role_g == "S") & ok)[0]
        self.rows_G = np.nonzero((self.role_g == "G") & ok)[0]
        self.rows_F = np.nonzero((self.role_g == "F") & ok)[0]
        self.rows_C = np.nonzero((self.role_g == "C") & ok)[0]
        self.store = M.build_features(T, self.module, self.gates, self.rules, self.role_g == "S")
        self.pair_drugs = {k: p for k, p in enumerate(T.pairs)}
        index = {d: k for k, d in enumerate(T.drugs)}
        self.pair_drug_idx = {k: (index[p[0]], index[p[1]]) for k, p in enumerate(T.pairs)}
        self.a_ref = T.a_ref

    def gid(self, g: int) -> str:
        T = self.T
        return f"{T.drugs[T.g_i[g]]}+{T.drugs[T.g_j[g]]}|{T.cells[T.g_cell[g]]}"

    def pool(self, rows):
        return E.Pool.from_rows(rows, self.T.g_pair, self.T.g_cell, len(self.T.cells), self.pair_drugs)

    def edit_scope_groups(self, edit_id):
        return self.store.X[:, self.store.edit_index[edit_id]].toarray().ravel() > 0

    def code_files(self):
        return ["adapter.py", "design.py", "models.py", "evaluation.py", "llm_arm.py", "study.py", "run.py", "PROTOCOL.md"]


# --------------------------------------------------------------------------- generic fitting helpers
def oof_predictions(fit_predict, store, rows, y, salt):
    pf = M.pair_folds(np.unique(store.pair[rows]), salt)
    fold = np.array([pf[int(p)] for p in store.pair[rows]])
    out = np.zeros(len(rows))
    for f in range(M.N_FOLDS):
        out[fold == f] = fit_predict(rows[fold != f], y[fold != f], rows[fold == f])
    return out


def ridge_fp(store, edits, config):
    return lambda tr, ytr, te: M.fit_ridge(store, tr, ytr, edits, config).predict(store, te)


def gbm_fp(store, config):
    return lambda tr, ytr, te: M.fit_gbm(store, tr, ytr, tuple(config)).predict(store.gbm[te])


def fm_fp(store, config):
    def fp(tr, ytr, te):
        model = M.FMModel(config[0], config[1], seed=0)
        model.fit(*M.fm_inputs(store, tr), ytr)
        return model.predict(*M.fm_inputs(store, te))
    return fp


def tune_learner(store, rows, y, salts, factory, configs):
    scores = M.cv_generic(rows, y, store, salts, lambda cfg, tr, ytr, te: factory(store, cfg)(tr, ytr, te), [tuple(c) for c in configs])
    best = min(scores, key=lambda c: (scores[c], c))
    return best, scores


# --------------------------------------------------------------------------- freeze (S only)
def precision_pilot(ctx: Context, yS_resid, pred_oof: dict, n_pool_pairs: int, n_pools: int, seed: int = 20261020):
    """Pool-sampling precision from source-side out-of-fold predictions (no C/G/F information)."""
    T = ctx.T
    pool = ctx.pool(ctx.rows_S)
    A = np.full(len(T.g_pair), np.nan)
    A[ctx.rows_S] = yS_resid + ctx.a_ref[ctx.rows_S]
    truth = pool.matrix(A)
    preds = {}
    for name, resid in pred_oof.items():
        full = np.full(len(T.g_pair), np.nan)
        full[ctx.rows_S] = ctx.a_ref[ctx.rows_S] + resid
        preds[name] = pool.matrix(full)
    rng = np.random.default_rng(seed)
    n_pairs = truth.shape[0]
    n_pool_pairs = min(n_pool_pairs, n_pairs - 1)
    fpc = 1.0 / np.sqrt(max(1e-9, 1.0 - n_pool_pairs / n_pairs))
    draws = {m: [] for m in preds}
    oracle = []
    for _ in range(n_pools):
        subset = np.sort(rng.choice(n_pairs, n_pool_pairs, replace=False))
        for m, p in preds.items():
            draws[m].append(E.utility(p, truth, subset))
        oracle.append(E.oracle_utility(truth, subset))
    draws = {m: np.array(v) for m, v in draws.items()}
    oracle = np.array(oracle)
    out = {"n_pool_pairs": n_pool_pairs, "n_pools": n_pools, "finite_population_correction": float(fpc),
           "mean_utility": {m: float(v.mean()) for m, v in draws.items()},
           "mean_oracle": float(oracle.mean()),
           "regret": {m: float((oracle - v).mean()) for m, v in draws.items()}, "contrasts_vs_fixed": {}}
    for m in preds:
        if m == "fixed":
            continue
        d = draws[m] - draws["fixed"]
        sd = float(d.std() * fpc)
        out["contrasts_vs_fixed"][m] = {"mean_delta": float(d.mean()), "sd_delta_corrected": sd,
                                        "min_detectable_effect_80pct_power_two_sided_5pct": float(2.8 * sd)}
    return out


def choose_margin(pilot: dict, cfg: dict) -> float:
    regret = pilot["regret"]["fixed"]
    return float(max(0.001, min(cfg["margin_default"], round(0.25 * regret, 3))))


def stage_freeze(ctx: Context, out: Path, *, api_enabled: bool = True, here: Path | None = None) -> dict:
    t0 = time.time()
    cfg, store, T = ctx.cfg, ctx.store, ctx.T
    yS = ctx.vault.source()
    rows = ctx.rows_S
    r = yS[rows] - ctx.a_ref[rows]
    best0, scores0 = M.tune_ridge(store, rows, r, (), cfg["cv_salts"])
    pilot_salt = cfg["pilot_salt"]
    oof = {"bliss_reference": np.zeros(len(rows)),
           "fixed": oof_predictions(ridge_fp(store, (), best0), store, rows, r, pilot_salt)}
    full_ids = tuple(rule.id for rule in ctx.rules)
    best_full, _ = M.tune_ridge(store, rows, r, full_ids, cfg["cv_salts"][:1])
    oof["full_dictionary"] = oof_predictions(ridge_fp(store, full_ids, best_full), store, rows, r, pilot_salt)
    best_gbm, _ = tune_learner(store, rows, r, cfg["cv_salts"][:1], gbm_fp, cfg["gbm_configs"])
    oof["gbm"] = oof_predictions(gbm_fp(store, best_gbm), store, rows, r, pilot_salt)
    best_fm, _ = tune_learner(store, rows, r, cfg["cv_salts"][:1], fm_fp, cfg["fm_configs"])
    oof["fm"] = oof_predictions(fm_fp(store, best_fm), store, rows, r, pilot_salt)
    n_pool = cfg["pilot_pool_pairs"] or int(len(ctx.pool(ctx.rows_F).pair_ids))
    pilot = precision_pilot(ctx, r, oof, n_pool, cfg["pilot_pools"])
    margin = choose_margin(pilot, cfg)
    worst_mde = max(v["min_detectable_effect_80pct_power_two_sided_5pct"] for v in pilot["contrasts_vs_fixed"].values() if True)
    design_label = "ESTIMATION_PILOT" if worst_mde > margin else "CONFIRMATORY_DEVELOPMENT"
    sd_oof = float(np.std(r - oof["fixed"]))
    # challenge panel: design metadata only
    c_pairs = sorted({int(p) for p in T.g_pair[ctx.rows_C]})
    panel = D.choose_panel(c_pairs, ctx.pair_drug_idx, ctx.module, cfg["panel_pairs"])
    freeze = {
        "stage": "freeze (source-side information only; C, G, F outcome files not opened)",
        "config": cfg, "design_label": design_label, "margin": margin,
        "margin_justification": "default 0.02 exceeds the source-side headroom (see precision_pilot.regret); adjusted per the registered rule before C",
        "retention_tau": margin * cfg["retention"]["tau_fraction_of_margin"],
        "modules": {T.drugs[k]: int(ctx.module[k]) for k in range(len(T.drugs))},
        "gate_threshold_rule": "cell mean monotherapy activity (all drugs / module drugs) >= across-cell median; -1 unknown is never satisfied",
        "gates": {name: {T.cells[c]: int(v[c]) for c in range(len(T.cells))} for name, v in ctx.gates.items()},
        "dictionary": [{"id": rule.id, "kind": rule.kind, "target": rule.target, "gate": rule.gate,
                        "module_pair": rule.module_pair, "description": rule.describe(),
                        "scope_groups_all_roles": int(ctx.edit_scope_groups(rule.id).sum())} for rule in ctx.rules],
        "dictionary_size": len(ctx.rules),
        "initial_model": {"structure": "fixed ridge: cell + drug + module + within/cross shared components + 3 numeric terms + drug-by-cell terms",
                          "source_tuned_config": list(best0), "source_cv_mse": scores0[best0],
                          "source_oof_residual_sd": sd_oof},
        "source_tuned_comparators": {"full_dictionary_config": list(best_full), "gbm_config": list(best_gbm), "fm_config": list(best_fm)},
        "precision_pilot": pilot, "worst_min_detectable_effect": worst_mde,
        "panel": {"n_pairs": len(panel), "pairs": ["|".join(ctx.pair_drugs[p]) for p in panel], "pair_ids": panel,
                  "n_pair_cell_groups": int(len(panel) * len(T.cells)),
                  "selection": "equal allocation over module-pair classes, hash order within class; design metadata and the common monotherapy panel only",
                  "cost_note": "counted in pair-cell groups; not a verified physical cost (no plate/control/bundle identifiers)"},
        "partition_sha256": digest_obj(ctx.role_pair.tolist()),
        "code_sha256": {name: adapter.sha256_text(Path(here) / name) for name in ctx.code_files() if here and (Path(here) / name).exists()},
        "verdict_rule": VERDICT_RULE, "api_registration": {
            "include_api_arm": bool(api_enabled and cfg["api"]["enabled"]),
            "rationale": "a concise edit-selection contract (menu of 16 edit ids over a numerical evidence table) is implementable within the registered limits; activation does not depend on any deterministic result, G or F",
            **cfg["api"]},
        "seconds": round(time.time() - t0, 1)}
    jdump(out / "FREEZE.json", freeze)
    return freeze


VERDICT_RULE = {
    "primary_contrasts": ["revision_deployed - refit", "revision_deployed - full_dictionary_deployed", "revision_deployed - conventional_deployed"],
    "uncertainty": "pair-group bootstrap (2000 draws, whole pairs with all cells, shortlists reselected inside each draw); one-sided lower/upper bounds at alpha/3 (Holm-conservative Bonferroni)",
    "sensitivity": "delete-one-drug jackknife standard error (normal bound at the same level) and cell bootstrap",
    "PROMISING_INTERNAL_DEVELOPMENT": "deployed revision != refit AND for all three contrasts estimate >= margin AND pair-bootstrap lower bound > 0 AND drug-jackknife lower bound > 0",
    "UNSUPPORTED": "upper bound of (revision_raw_candidate - refit) < margin: a useful gain over same-data refitting is excluded at the registered margin",
    "STANDARD_STRUCTURE_LEARNING_SUFFICIENT": "flag when a deployed full-dictionary or conventional procedure beats the refit with lower bound > 0 while the revision does not",
    "INCONCLUSIVE": "otherwise; a non-significant difference is not read as equivalence",
}


# --------------------------------------------------------------------------- challenge
def verify_freeze(ctx: Context, here: Path, freeze: dict) -> None:
    recorded = freeze["code_sha256"]
    for name, h in recorded.items():
        now = adapter.sha256_text(here / name)
        if now != h:
            raise RuntimeError(f"frozen file changed after freeze: {name}")
    if freeze["partition_sha256"] != digest_obj(ctx.role_pair.tolist()):
        raise RuntimeError("partition changed after freeze")


def edit_evidence(ctx: Context, rows_sc, y_sc, is_c, config, pre_flagged_mask, panel_rows_all):
    """Candidate-edit evidence table from legal S+C information only."""
    store, cfg, T = ctx.store, ctx.cfg, ctx.T
    ids = [r.id for r in ctx.rules]
    scores = M.cv_ridge(store, rows_sc, y_sc, [()] + [(i,) for i in ids], [config], cfg["cv_salts"], masks={"C": is_c})
    base = scores[((), config)]
    table = []
    guard = cfg["edit_guard"]
    sc_pairs_in = lambda mask_rows, scope: len({int(p) for p in store.pair[mask_rows][scope[mask_rows]]})  # noqa: E731
    unmeasured_rows = np.concatenate([ctx.rows_G, ctx.rows_F])
    flagged_rows = rows_sc[pre_flagged_mask]
    for rule in ctx.rules:
        s = scores[((rule.id,), config)]
        scope = ctx.edit_scope_groups(rule.id)
        in_s = rows_sc[~is_c]
        in_c = rows_sc[is_c]
        pairs_sc = sc_pairs_in(rows_sc, scope)
        pairs_c = sc_pairs_in(in_c, scope)
        pairs_unmeasured = sc_pairs_in(unmeasured_rows, scope)
        rel_all = (base["all"] - s["all"]) / base["all"]
        rel_c = (base["C"] - s["C"]) / base["C"]
        flagged_in_scope = int(scope[flagged_rows].sum())
        in_c_scope = int(scope[in_c].sum())
        ok = (rel_all >= guard["min_relative_cv_change_all"] and pairs_sc >= guard["min_scope_pairs_source_and_challenge"]
              and pairs_c >= guard["min_scope_pairs_challenge"] and pairs_unmeasured >= guard["min_unmeasured_scope_pairs"])
        table.append({"id": rule.id, "kind": rule.kind, "description": rule.describe(),
                      "relative_cv_gain_challenge": float(rel_c), "relative_cv_gain_all": float(rel_all),
                      "scope_pairs_source_and_challenge": pairs_sc, "scope_pairs_challenge": pairs_c,
                      "scope_pairs_unmeasured": pairs_unmeasured, "challenge_groups_in_scope": in_c_scope,
                      "flagged_counterexamples_in_scope": flagged_in_scope, "guard_ok": bool(ok)})
    return table


def select_edit_deterministic(table):
    eligible = [t for t in table if t["guard_ok"]]
    if not eligible:
        return "NO_EDIT"
    best = max(eligible, key=lambda t: (t["relative_cv_gain_challenge"], -int(t["id"][1:])))
    return best["id"]


def opaque_maps(ctx: Context, seed: int = 20261020):
    T = ctx.T
    def perm(prefix, items):
        order = sorted(items, key=lambda x: hashlib.sha256(f"{seed}|{prefix}|{x}".encode()).hexdigest())
        return {x: f"{prefix}{k + 1:02d}" for k, x in enumerate(order)}
    return {"drug": perm("D", range(len(T.drugs))), "cell": perm("L", range(len(T.cells))), "pair": perm("P", sorted(set(T.g_pair.tolist())))}


def build_api_summary(ctx, table, flagged, z, resid_obs, resid_pred, panel_rows_all, top_n):
    maps = opaque_maps(ctx)
    T = ctx.T
    order = np.argsort(-np.abs(z[flagged]))[:top_n]
    obs_rows = []
    legal_ids = []
    for rank, k in enumerate(order, start=1):
        g = panel_rows_all[flagged][k]
        oid = f"O{rank:03d}"
        legal_ids.append(oid)
        obs_rows.append({"obs": oid, "pair": maps["pair"][int(T.g_pair[g])], "cell": maps["cell"][int(T.g_cell[g])],
                         "module_class": "M%d-M%d" % tuple(sorted((int(ctx.module[T.g_i[g]]), int(ctx.module[T.g_j[g]])))),
                         "predicted_residual": round(float(resid_pred[flagged][k]), 4),
                         "observed_residual": round(float(resid_obs[flagged][k]), 4), "standardised_error": round(float(z[flagged][k]), 2)})
    edits = [{"id": t["id"], "edit": t["description"].replace(" by condition:", ", only where:").replace("module m", "module M")
              .replace("pair m", "pair M").replace(" m", " M"),
              "relative_cv_gain_on_challenge_groups": round(t["relative_cv_gain_challenge"], 5),
              "relative_cv_gain_on_all_training_groups": round(t["relative_cv_gain_all"], 5),
              "scope_pairs_in_training": t["scope_pairs_source_and_challenge"], "scope_pairs_in_challenge": t["scope_pairs_challenge"],
              "flagged_counterexamples_in_scope": t["flagged_counterexamples_in_scope"], "meets_frozen_guard": t["guard_ok"]}
             for t in table]
    summary = {
        "task": "Choose at most one structural edit of a fitted ridge model of the residual between observed combination activity and a multiplicative single-agent reference (units: activity 0-1).",
        "model": "fixed structure: cell + drug + module + within/cross-module shared components + drug-by-cell terms",
        "frozen_rules": "the deterministic selector picks the guard-passing edit with the highest relative_cv_gain_on_challenge_groups, else NO_EDIT",
        "n_challenge_groups_flagged": int(flagged.sum()), "edit_menu": edits, "largest_counterexamples": obs_rows}
    return summary, legal_ids


def _components(ctx: Context, model: M.RidgeModel):
    names = [ctx.store.names[c] for c in model.cols]
    w = dict(zip(names, model.weights.tolist()))
    pick = lambda prefix: {k: v for k, v in w.items() if k.startswith(prefix)}  # noqa: E731
    theta = np.array([v for k, v in w.items() if k.startswith("theta")])
    return {"config_lambda_base_lambda_theta": list(model.config), "n_parameters": int(len(model.cols)),
            "intercept": w.get("intercept0"), "shared_within_module": w.get("shared_0"), "shared_cross_module": w.get("shared_1"),
            "numeric_slopes_[A_ref,a_min,a_max]": [w.get("num0"), w.get("num1"), w.get("num2")],
            "module_effects": [w.get(f"module{k}") for k in range(int(ctx.module.max()) + 1)],
            "cell_effect_mean_sd": [float(np.mean(list(pick("cell").values()))), float(np.std(list(pick("cell").values())))],
            "drug_effect_mean_sd": [float(np.mean(list(pick("drug").values()))), float(np.std(list(pick("drug").values())))],
            "drug_by_cell_effect_mean_sd": [float(theta.mean()), float(theta.std())],
            "edit_coefficients": {k: v for k, v in w.items() if k.startswith("edit_")}}


def stage_challenge(ctx: Context, out: Path, freeze: dict, *, proposer=None) -> dict:
    """Initial model -> sealed pre-challenge predictions -> disclose C -> diagnose -> refit and candidates -> sealed nominations."""
    t0 = time.time()
    cfg, store, T = ctx.cfg, ctx.store, ctx.T
    yS = ctx.vault.source()
    rows_s = ctx.rows_S
    r_s = yS[rows_s] - ctx.a_ref[rows_s]
    config0 = tuple(freeze["initial_model"]["source_tuned_config"])
    initial = M.fit_ridge(store, rows_s, r_s, (), config0)
    panel = freeze["panel"]["pair_ids"]
    panel_rows = ctx.rows_C[np.isin(T.g_pair[ctx.rows_C], panel)]
    pred_pre = initial.predict(store, panel_rows)
    pre = {"stage": "pre-challenge predictions of the frozen initial model for every challenge group (made before disclosure)",
           "groups": [ctx.gid(g) for g in panel_rows], "predicted_residual": np.round(pred_pre, 8).tolist()}
    pre["sha256"] = digest_obj(pre)
    jdump(out / "PRECHALLENGE_PREDICTIONS.json", pre)
    # ---- disclosure of the acquired panel (the only reading of C)
    yC = ctx.vault.disclose_challenge(panel)
    r_c = yC[panel_rows] - ctx.a_ref[panel_rows]
    sd = freeze["initial_model"]["source_oof_residual_sd"]
    z = (r_c - pred_pre) / sd
    flagged = np.abs(z) > cfg["counterexample_abs_z"]
    rows_sc = np.concatenate([rows_s, panel_rows])
    y_sc = np.concatenate([r_s, r_c])
    is_c = np.concatenate([np.zeros(len(rows_s), bool), np.ones(len(panel_rows), bool)])
    flagged_sc = np.concatenate([np.zeros(len(rows_s), bool), flagged])
    # ---- refit (fixed structure) with full tuning budget on S+C
    config_refit, refit_scores = M.tune_ridge(store, rows_sc, y_sc, (), cfg["cv_salts"])
    refit = M.fit_ridge(store, rows_sc, y_sc, (), config_refit)
    # ---- evidence table and deterministic selection
    table = edit_evidence(ctx, rows_sc, y_sc, is_c, config_refit, flagged_sc, panel_rows)
    selected_det = select_edit_deterministic(table)
    api_summary, legal_ids = build_api_summary(ctx, table, flagged, z, r_c, pred_pre, panel_rows, cfg["api"]["top_counterexamples_sent"])
    diag = {"n_challenge_groups": int(len(panel_rows)), "n_flagged": int(flagged.sum()),
            "flag_rule": f"|(observed - predicted residual)/{sd:.6f}| > {cfg['counterexample_abs_z']}",
            "challenge_mse_initial": float(np.mean((r_c - pred_pre) ** 2)), "challenge_mse_zero_residual": float(np.mean(r_c ** 2)),
            "edit_evidence": table, "deterministic_selection": selected_det}
    # ---- candidates per arm
    models = {"initial": ("ridge", initial), "refit": ("ridge", refit)}
    arms = {}

    def candidate_edit(arm, edit_id):
        if edit_id == "NO_EDIT":
            arms[arm] = {"candidate": None, "reason": "NO_EDIT"}
            return
        cfg_e, _ = M.tune_ridge(store, rows_sc, y_sc, (edit_id,), cfg["cv_salts"])
        model = M.fit_ridge(store, rows_sc, y_sc, (edit_id,), cfg_e)
        models[arm] = ("ridge", model)
        arms[arm] = {"candidate": edit_id, "config": list(cfg_e)}

    candidate_edit("revision", selected_det)
    # full dictionary
    full_ids = tuple(rule.id for rule in ctx.rules)
    cfg_full, _ = M.tune_ridge(store, rows_sc, y_sc, full_ids, cfg["cv_salts"])
    models["fulldict"] = ("ridge", M.fit_ridge(store, rows_sc, y_sc, full_ids, cfg_full))
    arms["fulldict"] = {"candidate": "ALL_EDITS", "config": list(cfg_full)}
    # conventional structure learning: champion by S+C grouped validation
    cfg_gbm, sc_gbm = tune_learner(store, rows_sc, y_sc, cfg["cv_salts"], gbm_fp, cfg["gbm_configs"])
    cfg_fm, sc_fm = tune_learner(store, rows_sc, y_sc, cfg["cv_salts"], fm_fp, cfg["fm_configs"])
    champion = "gbm" if sc_gbm[cfg_gbm] <= sc_fm[cfg_fm] else "fm"
    arms["conventional"] = {"candidate": champion, "config": list(cfg_gbm if champion == "gbm" else cfg_fm),
                            "cv_mse": {"gbm": sc_gbm[cfg_gbm], "fm": sc_fm[cfg_fm], "ridge_refit": refit_scores[config_refit]}}
    # LLM-assisted secondary arm
    api = {"enabled": bool(freeze["api_registration"]["include_api_arm"])}
    if api["enabled"] and proposer is not None:
        receipt = proposer(api_summary, [r.id for r in ctx.rules], legal_ids)
        api["receipt"] = receipt
        selected = receipt.get("selected") if receipt.get("outcome") in ("VALID_EDIT", "VALID_NO_EDIT") else None
        if selected is None:
            arms["api"] = {"candidate": None, "reason": "API_" + str(receipt.get("outcome")) + "_FALLBACK_TO_REFIT"}
        else:
            candidate_edit("api", selected)
    else:
        arms["api"] = {"candidate": None, "reason": "API_NOT_RUN"}
    # ---- predictions for unmeasured pools (sealed before any G read)
    unmeasured = np.concatenate([ctx.rows_G, ctx.rows_F])
    resid = {}
    for name, (kind, model) in models.items():
        resid[name] = model.predict(store, unmeasured)
    kind_conv = arms["conventional"]
    if champion == "gbm":
        resid["conventional"] = M.fit_gbm(store, rows_sc, y_sc, tuple(cfg_gbm)).predict(store.gbm[unmeasured])
    else:
        fm = M.FMModel(cfg_fm[0], cfg_fm[1], seed=0)
        fm.fit(*M.fm_inputs(store, rows_sc), y_sc)
        resid["conventional"] = fm.predict(*M.fm_inputs(store, unmeasured))
    for arm in ("revision", "api"):
        if arm not in resid:
            resid[arm] = resid["refit"].copy()
    resid["bliss_reference"] = np.zeros(len(unmeasured))
    np.savez_compressed(out / "SEALED_PREDICTIONS.npz", rows=unmeasured, **{f"resid_{k}": v for k, v in resid.items()})
    # ---- executable before/after rules for edit arms
    rules_out = {}
    for arm in ("revision", "api"):
        edit_id = arms[arm].get("candidate")
        if edit_id is None:
            rules_out[arm] = {"edit": None, "reason": arms[arm].get("reason")}
            continue
        rule = ctx.rule_by_id[edit_id]
        scope = ctx.edit_scope_groups(edit_id)
        delta = resid[arm] - resid["refit"]
        in_scope = scope[unmeasured]
        flagged_ids = [ctx.gid(g) for g in panel_rows[flagged & scope[panel_rows]]]
        rules_out[arm] = {
            "edit": {"id": rule.id, "kind": rule.kind, "target": rule.target, "gate": rule.gate, "module_pair": rule.module_pair,
                     "description": rule.describe()},
            "expression": "R_hat(group) = R_hat_refit_structure(group) + beta_edit * scope_indicator(group); scope_indicator = 1 where "
                          + rule.describe().split(": ", 1)[-1] if rule.kind == "split" else
                          "R_hat(group) = R_hat_refit_structure(group) + beta_edit * 1[module pair of the drug pair is m%d-m%d]" % tuple(rule.module_pair),
            "observable_condition": ({"gate": rule.gate, "values_per_cell": freeze["gates"].get(rule.gate)} if rule.gate not in (None, "own") else
                                     {"gate": "own module sensitivity", "values_per_cell": {k: v for k, v in freeze["gates"].items() if k != "glob"}}) if rule.gate else None,
            "unknown_condition_behavior": "gate value -1 -> scope indicator 0; unknown is never treated as satisfied",
            "before": _components(ctx, refit), "after": _components(ctx, models[arm][1]),
            "scope": {"groups_all_roles": int(scope.sum()),
                      "pairs_in_source_and_challenge": int(len({int(p) for p in store.pair[rows_sc][scope[rows_sc]]})),
                      "pairs_among_unmeasured": int(len({int(p) for p in store.pair[unmeasured][in_scope]}))},
            "supporting_observations": {"challenge_counterexamples_in_scope": flagged_ids,
                                        "n_challenge_groups_in_scope": int(scope[panel_rows].sum()),
                                        "source_pairs_in_scope": sorted({"|".join(ctx.pair_drugs[int(p)]) for p in store.pair[rows_s][scope[rows_s]]})},
            "effect_on_unmeasured": {"n_groups_in_scope": int(in_scope.sum()),
                                     "mean_abs_change_in_scope": float(np.abs(delta[in_scope]).mean()) if in_scope.any() else 0.0,
                                     "mean_abs_change_out_of_scope": float(np.abs(delta[~in_scope]).mean()) if (~in_scope).any() else 0.0,
                                     "file": f"RULE_EFFECTS_{arm}.csv"},
            "sharing_check": "edit scope covers more than one drug pair in the evidence and among unmeasured candidates"
                             if int(len({int(p) for p in store.pair[unmeasured][in_scope]})) > 1 else "FAILED: scope covers <=1 unmeasured pair"}
        lines = ["group,role,in_scope,delta_residual_vs_refit"]
        for g, s_, d_ in zip(unmeasured, in_scope, delta):
            lines.append(f"{ctx.gid(g)},{ctx.role_g[g]},{int(s_)},{d_:.8f}")
        (out / f"RULE_EFFECTS_{arm}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    jdump(out / "RULES.json", rules_out)
    # ---- nominations (sealed before G): top-k per cell for every prediction set
    nominations = {}
    for name, rs in resid.items():
        full = np.full(len(T.g_pair), np.nan)
        full[unmeasured] = ctx.a_ref[unmeasured] + rs
        for role, rows in (("G", ctx.rows_G), ("F", ctx.rows_F)):
            pool = ctx.pool(rows)
            sel = E.top_k(pool.matrix(full))
            nominations.setdefault(name, {})[role] = {T.cells[c]: ["|".join(ctx.pair_drugs[int(pool.pair_ids[i])]) for i in sel[:, c]]
                                                       for c in range(len(T.cells))}
    jdump(out / "NOMINATIONS_SEALED.json", nominations)
    trace = {"common_training_set": {"n_groups": int(len(rows_sc)), "sha256": digest_obj(rows_sc.tolist()),
                                     "note": "every arm (refit, revision, full dictionary, conventional, API) is fitted and tuned on exactly these S+C groups"},
             "order": ["frozen initial model fitted on S", "predictions for the challenge panel recorded and hashed",
                       "C panel disclosed (the only reading of C)", "counterexamples flagged against the recorded predictions",
                       "same S+C data given to every method", "edit evidence table computed on S+C",
                       "one candidate edit per arm", "unmeasured predictions and nominations sealed before G"],
             "prechallenge_sha256": pre["sha256"], "diagnosis": diag, "arms": arms, "api": api,
             "refit": {"config": list(config_refit), "cv_mse": refit_scores[config_refit]},
             "vault_ledger": ctx.vault.ledger, "seconds": round(time.time() - t0, 1),
             "sealed_predictions_sha256": adapter.sha256_file(out / "SEALED_PREDICTIONS.npz"),
             "nominations_sha256": adapter.sha256_text(out / "NOMINATIONS_SEALED.json")}
    jdump(out / "CHALLENGE_TRACE.json", trace)
    jdump(out / "API_SUMMARY_SENT.json", api_summary) if api["enabled"] and proposer is not None else None
    return trace


# --------------------------------------------------------------------------- retention (single G query per arm)
def stage_retention(ctx: Context, out: Path, freeze: dict) -> dict:
    cfg = ctx.cfg
    sealed = np.load(out / "SEALED_PREDICTIONS.npz")
    rows = sealed["rows"]
    resid = {k[len("resid_"):]: sealed[k] for k in sealed.files if k.startswith("resid_")}
    trace = jload(out / "CHALLENGE_TRACE.json")
    pos = {int(g): k for k, g in enumerate(rows)}
    tau = freeze["retention_tau"]
    tol = cfg["retention"]["mse_ratio_tolerance"]
    pool = ctx.pool(ctx.rows_G)
    decisions = {}
    for arm in ("revision", "fulldict", "conventional", "api"):
        info = trace["arms"][arm]
        if info.get("candidate") is None:
            decisions[arm] = {"candidate_available": False, "accepted": False, "deployed": "refit", "reason": info.get("reason")}
            continue
        scope = ctx.edit_scope_groups(info["candidate"]) if arm in ("revision", "api") else None

        def evaluator(yG, arm=arm, scope=scope):
            full_c = np.full(len(ctx.T.g_pair), np.nan)
            full_r = np.full(len(ctx.T.g_pair), np.nan)
            g = ctx.rows_G
            idx = np.array([pos[int(x)] for x in g])
            full_c[g] = ctx.a_ref[g] + resid[arm][idx]
            full_r[g] = ctx.a_ref[g] + resid["refit"][idx]
            truth = pool.matrix(yG)
            u_c, u_r = E.utility(pool.matrix(full_c), truth), E.utility(pool.matrix(full_r), truth)
            ratio = E.mse_ratio(full_c[g], full_r[g], yG[g])
            out_ratio = None
            if scope is not None and (~scope[g]).any():
                out_ratio = E.mse_ratio(full_c[g], full_r[g], yG[g], ~scope[g])
            return {"utility_candidate": u_c, "utility_refit": u_r, "delta_utility": u_c - u_r, "oracle_utility": E.oracle_utility(truth),
                    "mse_ratio_all": ratio, "mse_ratio_out_of_scope": out_ratio}

        m = ctx.vault.retention_query(arm, evaluator)
        complexity_ok = bool(len(ctx.rules) <= cfg["max_dictionary_edits"] and cfg["max_configs_per_model"] <= 12
                             and len(cfg["ridge_configs"]) <= 12 and len(cfg["gbm_configs"]) <= 12 and len(cfg["fm_configs"]) <= 12)
        accepted = bool(m["delta_utility"] >= tau and m["mse_ratio_all"] <= 1 + tol
                        and (m["mse_ratio_out_of_scope"] is None or m["mse_ratio_out_of_scope"] <= 1 + tol) and complexity_ok)
        decisions[arm] = {"candidate_available": True, "candidate": info["candidate"], "metrics": m, "criteria": {
            "delta_utility_at_least": tau, "mse_ratio_all_at_most": 1 + tol, "mse_ratio_out_of_scope_at_most": 1 + tol,
            "complexity_within_limits": complexity_ok}, "accepted": accepted, "deployed": arm if accepted else "refit"}
    result = {"decisions": decisions, "vault_ledger_after_G": ctx.vault.ledger,
              "note": "G is a consumed development resource; a rejection returns the fixed-structure refit and authorises no further edit"}
    jdump(out / "RETENTION.json", result)
    return result


# --------------------------------------------------------------------------- final evaluation (single F opening)
def decide(results: dict, margin: float, alpha: float = 0.05, n_primary: int = 3) -> dict:
    """Verdict from stored contrast summaries (no data access); implements VERDICT_RULE."""
    prim = results["primary"]
    names = ["vs_refit", "vs_full_dictionary", "vs_conventional"]
    retained = results["revision_retained_at_G"]
    gain_ok = all(prim[n]["estimate"] >= margin and prim[n]["lower_bound_pair_bootstrap"] > 0
                  and prim[n]["lower_bound_drug_jackknife"] > 0 for n in names)
    raw = results["raw_candidate_vs_refit"]
    excluded = raw["upper_bound_pair_bootstrap"] < margin
    standard = [k for k in ("full_dictionary", "conventional") if results["standard_vs_refit"][k]["lower_bound_pair_bootstrap"] > 0]
    if retained and gain_ok:
        label = "PROMISING_INTERNAL_DEVELOPMENT"
    elif excluded:
        label = "UNSUPPORTED"
    else:
        label = "INCONCLUSIVE"
    return {"label": label, "retained_at_G": bool(retained), "useful_gain_over_refit_excluded": bool(excluded),
            "standard_structure_learning_beats_refit": standard,
            "STANDARD_STRUCTURE_LEARNING_SUFFICIENT_flag": bool(standard) and label != "PROMISING_INTERNAL_DEVELOPMENT",
            "margin": margin}


def stage_final(ctx: Context, out: Path, freeze: dict) -> dict:
    cfg, T = ctx.cfg, ctx.T
    sealed = np.load(out / "SEALED_PREDICTIONS.npz")
    rows = sealed["rows"]
    resid = {k[len("resid_"):]: sealed[k] for k in sealed.files if k.startswith("resid_")}
    retention = jload(out / "RETENTION.json")["decisions"]
    pos = {int(g): k for k, g in enumerate(rows)}
    pool = ctx.pool(ctx.rows_F)
    idx = np.array([pos[int(g)] for g in ctx.rows_F])
    deployed = {"refit": resid["refit"], "initial": resid["initial"], "bliss_reference": resid["bliss_reference"]}
    for arm in ("revision", "fulldict", "conventional", "api"):
        deployed[f"{arm}_raw"] = resid[arm]
        deployed[f"{arm}_deployed"] = resid[arm] if retention[arm]["accepted"] else resid["refit"]
    margin = freeze["margin"]
    bcfg = cfg["bootstrap"]

    def evaluator(yF):
        truth = pool.matrix(yF)
        full = {}
        for name, rs in deployed.items():
            vec = np.full(len(T.g_pair), np.nan)
            vec[ctx.rows_F] = ctx.a_ref[ctx.rows_F] + rs[idx]
            full[name] = vec
        preds = {name: pool.matrix(v) for name, v in full.items()}
        oracle = E.oracle_utility(truth)
        per_method = {}
        refit_err = (full["refit"][ctx.rows_F] - yF[ctx.rows_F]) ** 2
        for name, v in full.items():
            err = (v[ctx.rows_F] - yF[ctx.rows_F]) ** 2
            worse = err > refit_err + 1e-12
            per_method[name] = {"utility": E.utility(preds[name], truth), "regret": oracle - E.utility(preds[name], truth),
                                "activity_mse": float(err.mean()),
                                "negative_transfer_fraction_of_groups_worse_than_refit": float(worse.mean()),
                                "negative_transfer_mean_excess_where_worse": float((err - refit_err)[worse].mean()) if worse.any() else 0.0,
                                "changes_vs_refit_groups": int((np.abs(v[ctx.rows_F] - full["refit"][ctx.rows_F]) > 1e-9).sum())}
        contrasts = [("revision_deployed", "refit"), ("revision_deployed", "fulldict_deployed"), ("revision_deployed", "conventional_deployed"),
                     ("revision_raw", "refit"), ("revision_raw", "fulldict_raw"), ("revision_raw", "conventional_raw"),
                     ("refit", "initial"), ("refit", "bliss_reference"), ("initial", "bliss_reference"),
                     ("fulldict_deployed", "refit"), ("conventional_deployed", "refit"), ("fulldict_raw", "refit"), ("conventional_raw", "refit"),
                     ("api_deployed", "revision_deployed"), ("api_deployed", "refit"), ("api_raw", "refit"), ("api_raw", "revision_raw")]
        draws, util_draws, oracle_draws = E.paired_bootstrap(preds, truth, contrasts, bcfg["n"], bcfg["seed"], "pair")
        cell_draws, _, _ = E.paired_bootstrap(preds, truth, contrasts[:3], bcfg["cell_bootstrap_n"], bcfg["seed"] + 1, "cell")
        jk = E.drug_jackknife(preds, truth, pool.pair_ids, ctx.pair_drugs, contrasts[:6])
        from statistics import NormalDist
        z_one = NormalDist().inv_cdf(1 - bcfg["alpha"] / bcfg["primary_contrasts"])
        table = {}
        for c in contrasts:
            d = draws[c]
            est = E.utility(preds[c[0]], truth) - E.utility(preds[c[1]], truth)
            entry = {"estimate": est, "ci95_two_sided": [float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))],
                     "lower_bound_pair_bootstrap": float(np.quantile(d, bcfg["alpha"] / bcfg["primary_contrasts"])),
                     "upper_bound_pair_bootstrap": float(np.quantile(d, 1 - bcfg["alpha"] / bcfg["primary_contrasts"])),
                     "bootstrap_share_positive": float((d > 0).mean())}
            if c in jk:
                entry["drug_jackknife_se"] = jk[c]["jackknife_se"]
                entry["lower_bound_drug_jackknife"] = est - z_one * jk[c]["jackknife_se"]
                entry["upper_bound_drug_jackknife"] = est + z_one * jk[c]["jackknife_se"]
            if c in cell_draws:
                entry["cell_bootstrap_ci95"] = [float(np.quantile(cell_draws[c], 0.025)), float(np.quantile(cell_draws[c], 0.975))]
            table[f"{c[0]} - {c[1]}"] = entry
        primary = {}
        for key, c in (("vs_refit", contrasts[0]), ("vs_full_dictionary", contrasts[1]), ("vs_conventional", contrasts[2])):
            primary[key] = table[f"{c[0]} - {c[1]}"]
        # secondary: interpolated functional reference residual on the SAME shortlists (ranking stays by predicted activity)
        aref = np.full(len(T.g_pair), np.nan)
        aref[ctx.rows_F] = ctx.a_ref[ctx.rows_F]
        resid_truth = truth - pool.matrix(aref)
        sec_contrasts = contrasts[:3] + [("refit", "initial"), ("fulldict_deployed", "refit"), ("conventional_deployed", "refit")]
        sec_draws, _, _ = E.paired_bootstrap(preds, resid_truth, sec_contrasts, bcfg["n"], bcfg["seed"] + 2, "pair")
        secondary = {"definition": "macro-cell mean of R = A - A_ref over each method's activity-ranked shortlist; interpolated functional reference residual, not validated Bliss synergy",
                     "methods": {name: E.utility(preds[name], resid_truth) for name in preds},
                     "contrasts": {f"{c[0]} - {c[1]}": {"estimate": E.utility(preds[c[0]], resid_truth) - E.utility(preds[c[1]], resid_truth),
                                                          "ci95_two_sided": [float(np.quantile(sec_draws[c], 0.025)), float(np.quantile(sec_draws[c], 0.975))]}
                                   for c in sec_contrasts}}
        results = {
            "oracle_utility": oracle, "secondary_reference_residual": secondary, "methods": per_method, "contrasts": table, "primary": primary,
            "revision_retained_at_G": bool(retention["revision"]["accepted"]),
            "raw_candidate_vs_refit": table["revision_raw - refit"],
            "standard_vs_refit": {"full_dictionary": table["fulldict_deployed - refit"], "conventional": table["conventional_deployed - refit"]},
            "n_pairs": int(truth.shape[0]), "n_cells": int(truth.shape[1]), "shortlist_k": cfg["k_shortlist"]}
        results["verdict"] = decide(results, margin, bcfg["alpha"], bcfg["primary_contrasts"])
        rows_csv = ["group,pair,cell,activity_observed,activity_reference," + ",".join(sorted(full))]
        for g in ctx.rows_F:
            rows_csv.append(",".join([ctx.gid(g).replace(",", ";"), "|".join(ctx.pair_drugs[int(T.g_pair[g])]), T.cells[T.g_cell[g]],
                                      f"{yF[g]:.6f}", f"{ctx.a_ref[g]:.6f}"] + [f"{full[m][g]:.6f}" for m in sorted(full)]))
        results["_csv"] = rows_csv
        return results

    results = ctx.vault.final_evaluation(evaluator)
    csv = results.pop("_csv")
    (out / "PREDICTIONS_F.csv").write_text("\n".join(csv) + "\n", encoding="utf-8", newline="\n")
    results["vault_ledger"] = ctx.vault.ledger
    results["predictions_csv_sha256"] = adapter.sha256_text(out / "PREDICTIONS_F.csv")
    jdump(out / "RESULTS.json", results)
    return results
