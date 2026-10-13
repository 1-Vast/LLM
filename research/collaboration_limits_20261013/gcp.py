"""GCP workstream: why the deterministic model beat the evidence agents, and whether decisions align with hits.

File summary
- Path: research/collaboration_limits_20261013/gcp.py
- Purpose: diagnose the 2026-10-13 GCP evidence-transfer result and test an endpoint-aligned decoder.
- Core points:
  - The frozen study (`research/evidence_transfer_20261013`) is used read-only, through its own loaders.
  - `deterministic` re-implements its ridge/phenotype blend so leave-one-out and jackknife fits are fast;
    `parity` proves it equals the frozen predictions.
  - `diagnose` reads only data that was already opened: reference, development and the exposed test.
    Every result on the exposed test is labelled EXPOSED and selects nothing.
  - `fresh-*` commands handle the never-opened target lines (A549, NPC, Astrocyte). They refuse to run
    before `PROTOCOL.md` is frozen in `FREEZE.json`.
- Commands: parity, diagnose, donors, decoder, fresh-metadata, fresh-prepare, fresh-choose, fresh-evaluate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
PRIOR = ROOT / "research/evidence_transfer_20261013"
sys.path.insert(0, str(PRIOR))
sys.path.insert(0, str(ROOT / "src"))
import study as ET  # noqa: E402  (frozen study module, read-only)
from virtual_cell.knowledge_transfer import fit_ridge_map  # noqa: E402

THRESHOLD = 0.5          # log2 effect required for a hit (inherited, not tuned)
DRAWS = 4000             # Monte Carlo draws for P(hit)
SEED = int(hashlib.sha256(b"collaboration-limits-20261013").hexdigest()[:8], 16)


# A dry run sends the fresh pipeline through the already-opened original lines into a scratch folder,
# so code paths are exercised before the one-shot fresh evaluation. It never touches fresh outcomes.
DRY = os.environ.get("GCP_DRYRUN", "")
OUT = Path(DRY) if DRY else STUDY


def write_json(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- model
def deterministic(Yref: np.ndarray, anchors: np.ndarray, *, k: int = 5) -> dict:
    """The frozen study's ridge, phenotype and blend predictions, standardized, on its feature mask.

    Yref: references x 4 lines x features (raw, NaN allowed); anchors: queries x features (raw).
    """
    keep = np.isfinite(Yref).all(axis=(0, 1))
    y = Yref[..., keep]
    scale = np.maximum(y.reshape(-1, y.shape[-1]).std(axis=0, ddof=1), .1)
    y = y / scale
    anchor = anchors[:, keep] / scale
    anchor = np.where(np.isfinite(anchor), anchor, y[:, 0].mean(axis=0))
    ref_center = y[:, 0].mean(axis=0)
    sim = ET.cosine(anchor[:, None] - ref_center, y[None, :, 0] - ref_center)
    ridge = []
    for t in range(1, y.shape[1]):
        target_mean = y[:, t].mean(0)
        fitted = fit_ridge_map(y[:, 0] - ref_center, y[:, t] - target_mean, lams=(1., 10., 100., 1000.))
        ridge.append((anchor - ref_center) @ fitted.B + target_mean)
    ridge = np.stack(ridge, axis=1)
    pheno = []
    for i in range(len(anchor)):
        order = np.argsort(-sim[i], kind="stable")[:k]
        w = np.maximum(sim[i, order], 0)
        w = w / w.sum() if w.sum() else np.full(len(order), 1 / len(order))
        pheno.append(anchor[i] + np.einsum("r,rtf->tf", w, y[order, 1:] - y[order, :1]))
    pheno = np.asarray(pheno)
    return {"ridge": ridge, "phenotype": pheno, "no_agent_model": .5 * ridge + .5 * pheno,
            "keep": keep, "scale": scale, "y": y, "anchor": anchor, "sim": sim}


def donor_prediction(model: dict, i: int, donors: list[int]) -> np.ndarray:
    """Equal-weight residual transfer from fixed donors (the agents' decoder), standardized."""
    y = model["y"]
    return model["anchor"][i] + (y[donors, 1:] - y[donors, :1]).mean(0)


# ---------------------------------------------------------------- data
def load(split: str):
    compounds = [c for c in ET.eligible_metadata() if c["split"] == split]
    tensor, replicates, features = ET.load_tensor(split, compounds)
    return compounds, tensor, replicates, features


def qualifying(truth: np.ndarray, replicates: dict, keep: np.ndarray, targets=(1, 2, 3)) -> np.ndarray:
    """Signed hit table: +1/-1 where that direction qualifies as a hit, 0 otherwise (queries x targets x kept)."""
    cols = np.flatnonzero(keep)
    out = np.zeros((len(truth), len(targets), len(cols)), dtype=int)
    for i in range(len(truth)):
        for a, t in enumerate(targets):
            if (i, t) not in replicates:
                continue
            for b, f in enumerate(cols):
                raw = replicates[i, t][:, f]
                raw = raw[np.isfinite(raw)]
                mean = truth[i, t, f]
                if len(raw) >= 2 and np.isfinite(mean) and abs(mean) > THRESHOLD:
                    if np.all(raw > 0) and mean > 0:
                        out[i, a, b] = 1
                    elif np.all(raw < 0) and mean < 0:
                        out[i, a, b] = -1
    return out


def hits_of(actions: list[tuple[int, int, int]], table: np.ndarray) -> np.ndarray:
    return np.array([int(table[i, t, f] == s) for i, (t, f, s) in enumerate(actions)])


# ---------------------------------------------------------------- decoders
def decode_z(pred_std: np.ndarray) -> list[tuple[int, int, int]]:
    """The frozen decoder: largest absolute standardized prediction."""
    flat = pred_std.reshape(len(pred_std), -1)
    j = np.argmax(np.abs(flat), axis=1)
    F = pred_std.shape[-1]
    return [(int(x // F), int(x % F), 1 if flat[i, x] >= 0 else -1) for i, x in enumerate(j)]


def decode_raw(pred_raw: np.ndarray) -> list[tuple[int, int, int]]:
    """Largest absolute raw (log2) prediction: removes only the scale mismatch."""
    return decode_z(pred_raw)


def p_hit(pred_raw: np.ndarray, sigma: np.ndarray, tau: np.ndarray, n_rep: np.ndarray, *, seed: int = SEED) -> np.ndarray:
    """P(observed mean beyond THRESHOLD in the predicted direction and every replicate agreeing).

    pred_raw: queries x targets x features; sigma: targets x features SD of the true mean around the
    prediction; tau: targets x features replicate SD; n_rep: queries x targets replicate counts.
    Returns queries x targets x features for the predicted sign.
    """
    rng = np.random.default_rng(seed)
    nmax = int(np.max(n_rep))
    z = rng.standard_normal((DRAWS, 1, 1, 1))
    eps = rng.standard_normal((DRAWS, nmax, 1, 1))
    out = np.zeros(pred_raw.shape)
    sign = np.where(pred_raw >= 0, 1.0, -1.0)
    for i in range(len(pred_raw)):
        for t in range(pred_raw.shape[1]):
            n = int(n_rep[i, t])
            if n < 2:
                continue
            m = sign[i, t] * pred_raw[i, t]                      # features
            mu = m[None] + sigma[t][None] * z[:, 0, 0]           # draws x features
            reps = mu[:, None, :] + tau[t][None, None, :] * eps[:, :n, 0, :]
            ok = (reps.mean(1) > THRESHOLD) & (reps > 0).all(1)
            out[i, t] = ok.mean(0)
    return out


def decode_phit(pred_raw: np.ndarray, sigma, tau, n_rep) -> tuple[list[tuple[int, int, int]], np.ndarray]:
    P = p_hit(pred_raw, sigma, tau, n_rep)
    flat = P.reshape(len(P), -1)
    j = np.argmax(flat, axis=1)
    F = P.shape[-1]
    acts = [(int(x // F), int(x % F), 1 if pred_raw[i, x // F, x % F] >= 0 else -1) for i, x in enumerate(j)]
    return acts, P


def replicate_sd(replicates: dict, n: int, cols: np.ndarray, targets=(1, 2, 3)) -> np.ndarray:
    """Pooled within-unit replicate SD per target x feature (raw log2)."""
    out = np.zeros((len(targets), len(cols)))
    for a, t in enumerate(targets):
        ss, df = np.zeros(len(cols)), np.zeros(len(cols))
        for i in range(n):
            if (i, t) not in replicates:
                continue
            r = replicates[i, t][:, cols]
            fin = np.isfinite(r)
            cnt = fin.sum(0)
            mean = np.where(cnt > 0, np.nansum(r, 0) / np.maximum(cnt, 1), 0)
            ss += np.nansum(np.where(fin, (r - mean) ** 2, 0), 0)
            df += np.maximum(cnt - 1, 0)
        out[a] = np.sqrt(ss / np.maximum(df, 1))
    return out


def replicate_counts(replicates: dict, n: int, targets=(1, 2, 3)) -> np.ndarray:
    return np.array([[len(replicates[i, t]) if (i, t) in replicates else 0 for t in targets] for i in range(n)])


# ---------------------------------------------------------------- reference leave-one-out
def reference_loo(ry: np.ndarray) -> dict:
    """Each reference predicted from the others (raw units on the full 40-feature axis)."""
    R, L, F = ry.shape
    out = {name: np.full((R, L - 1, F), np.nan) for name in ("ridge", "phenotype", "no_agent_model")}
    for r in range(R):
        mask = np.arange(R) != r
        m = deterministic(ry[mask], ry[r:r + 1, 0])
        cols = np.flatnonzero(m["keep"])
        for name in out:
            out[name][r][:, cols] = m[name][0] * m["scale"]
    return out


def sigma_from_loo(loo_raw: np.ndarray, truth: np.ndarray, tau: np.ndarray, n_rep: np.ndarray, cols: np.ndarray,
                   exclude: int | None = None) -> np.ndarray:
    """SD of the true mean around the prediction: residual variance minus mean replicate variance."""
    resid = loo_raw[:, :, cols] - truth[:, 1:, cols]
    if exclude is not None:
        resid = np.delete(resid, exclude, axis=0)
    var = np.nanmean(resid ** 2, axis=0)
    rep_var = tau ** 2 / np.maximum(np.median(n_rep, axis=0), 1)[:, None]
    return np.sqrt(np.maximum(var - rep_var, 0.25 * var))


# ---------------------------------------------------------------- commands
def parity() -> dict:
    ref, ry, _, _ = load("reference")
    test = [c for c in ET.eligible_metadata() if c["split"] == "test"]
    anchors, _, _ = ET.load_tensor("test", test, anchors_only=True)
    m = deterministic(ry, anchors[:, 0])
    with np.load(PRIOR / "predictions.npz") as z:
        diffs = {name: float(np.max(np.abs(m[name] - z[name]))) for name in ("ridge", "phenotype", "no_agent_model")}
        same_actions = decode_z(m["no_agent_model"]) == [(a["target"] - 1, a["feature"], a["sign"])
                                                          for a in ET.selected_actions(z["no_agent_model"])]
    result = {"max_abs_difference": diffs, "no_agent_actions_identical": bool(same_actions)}
    print(json.dumps(result))
    return result


def _agent_donors(reference: list, queries: list) -> dict:
    """Final agent donor indices per arm and query (empty = fallback to phenotype weights)."""
    audit = json.loads((PRIOR / "AGENT_AUDIT.json").read_text(encoding="utf-8"))
    index = {c["pert_id"]: j for j, c in enumerate(reference)}
    qpos = {c["pert_id"]: i for i, c in enumerate(queries)}
    out = {}
    for row in audit:
        out.setdefault(row["arm"], {})[qpos[row["query"]]] = {
            "final": [index[d] for d in row["final_donors"]], "initial": [index[d] for d in row["initial_donors"]],
            "requested": [index[d] for d in row["requested"]]}
    return out


def diagnose() -> dict:
    ref, ry, rrep, _ = load("reference")
    dev, dy, drep, _ = load("development")
    test, ty, trep, _ = load("test")
    base = deterministic(ry, ry[:, 0])
    keep, scale = base["keep"], base["scale"]
    cols = np.flatnonzero(keep)
    out: dict = {"labels": {"reference_loo": "development (opened before)", "development": "development (opened before)",
                            "test": "EXPOSED: evaluated once on 2026-10-13; diagnostic only, selects nothing"}}

    # --- replicate noise and the scale mismatch
    tau = replicate_sd(rrep, len(ref), cols)
    out["scale_vs_threshold"] = {
        "feature_scale_quantiles": np.quantile(scale, [0, .25, .5, .75, 1]).round(3).tolist(),
        "features_with_scale_below_threshold": int((scale < THRESHOLD).sum()),
        "replicate_sd_quantiles": np.quantile(tau, [0, .25, .5, .75, 1]).round(3).tolist()}

    # --- reference leave-one-out: predictions, sigma, hit tables
    loo = reference_loo(ry)
    rtable = qualifying(ry, rrep, keep)
    rn = replicate_counts(rrep, len(ref))
    sets = {"reference_loo": (loo, ry, rtable, rn)}

    # --- development and exposed test predictions from all references
    for name, (yq, rep) in {"development": (dy, drep), "test": (ty, trep)}.items():
        m = deterministic(ry, yq[:, 0])
        raw = {k: np.full((len(yq), 3, ry.shape[2]), np.nan) for k in ("ridge", "phenotype", "no_agent_model")}
        for k in raw:
            raw[k][:, :, cols] = m[k] * scale
        sets[name] = (raw, yq, qualifying(yq, rep, keep), replicate_counts(rep, len(yq)))

    decoders = {}
    for name, (raw, yq, table, n_rep) in sets.items():
        res = {}
        hit_density = (table != 0).mean(axis=(1, 2))
        res["qualifying_actions_per_compound_mean"] = float((table != 0).sum(axis=(1, 2)).mean())
        res["random_action_hit_rate"] = float(hit_density.mean() / 2)   # a random sign halves it
        res["compounds_with_any_qualifying_action"] = int(((table != 0).sum(axis=(1, 2)) > 0).sum())
        for model in ("ridge", "phenotype", "no_agent_model"):
            pr = raw[model][:, :, cols]
            z_acts = decode_z(pr / scale)
            raw_acts = decode_raw(pr)
            if name == "reference_loo":
                sig = np.stack([sigma_from_loo(raw[model], yq, tau, n_rep, cols, exclude=i) for i in range(len(yq))])
                P = np.stack([p_hit(pr[i:i + 1], sig[i], tau, n_rep[i:i + 1])[0] for i in range(len(yq))])
            else:
                sig = sigma_from_loo(loo[model], ry, tau, rn, cols)
                P = p_hit(pr, sig, tau, n_rep)
            flat = P.reshape(len(P), -1)
            jj = np.argmax(flat, axis=1)
            p_acts = [(int(x // len(cols)), int(x % len(cols)), 1 if pr[i, x // len(cols), x % len(cols)] >= 0 else -1)
                      for i, x in enumerate(jj)]
            chosen_raw = np.array([abs(pr[i, t, f]) for i, (t, f, s) in enumerate(z_acts)])
            res[model] = {
                "hits_z_decoder": int(hits_of(z_acts, table).sum()),
                "hits_raw_decoder": int(hits_of(raw_acts, table).sum()),
                "hits_phit_decoder": int(hits_of(p_acts, table).sum()),
                "n": len(table),
                "z_decoder_predicted_raw_below_threshold": int((chosen_raw < THRESHOLD).sum()),
                "z_decoder_hits_when_raw_below_threshold": int(hits_of(z_acts, table)[chosen_raw < THRESHOLD].sum()),
                "mean_phit_of_phit_choice": float(flat.max(1).mean()),
                "phit_choice_expected_vs_realised": [float(flat.max(1).sum()), int(hits_of(p_acts, table).sum())],
                "phit_calibration_all_actions": _calibration(P, table, pr)}
        decoders[name] = res
    out["decoders"] = decoders

    # --- exposed test: discordance, donors and decoder stability
    out["exposed_test"] = _exposed_test(ref, ry, test, ty, trep, keep, scale, cols)
    write_json("diagnostics_gcp.json", out)
    print(json.dumps(out["decoders"], indent=1)[:4000])
    return out


def _calibration(P: np.ndarray, table: np.ndarray, pr: np.ndarray) -> dict:
    sign = np.where(pr >= 0, 1, -1)
    y = (table == sign).astype(float).ravel()
    p = P.ravel()
    bins = np.array([0, .05, .1, .2, .4, .6, 1.0001])
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (p >= lo) & (p < hi)
        if m.any():
            rows.append({"bin": [float(lo), float(min(hi, 1))], "n": int(m.sum()), "mean_p": float(p[m].mean()),
                         "hit_rate": float(y[m].mean())})
    from sklearn.metrics import roc_auc_score
    auc = float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else None
    auc_abs = float(roc_auc_score(y, np.abs(pr).ravel())) if 0 < y.sum() < len(y) else None
    return {"bins": rows, "brier": float(np.mean((p - y) ** 2)), "auroc_phit": auc, "auroc_abs_raw_prediction": auc_abs,
            "base_rate": float(y.mean())}


def _exposed_test(ref, ry, test, ty, trep, keep, scale, cols) -> dict:
    with np.load(PRIOR / "predictions.npz") as z:
        frozen = {k: z[k] for k in z.files}
    table = qualifying(ty, trep, keep)
    arms = ("no_agent_model", "integrated", "conventional", "agent_only", "source_free_initial", "phenotype", "ridge")
    acts = {a: decode_z(frozen[a]) for a in arms}
    hits = {a: hits_of(acts[a], table) for a in arms}
    rows = []
    for i, c in enumerate(test):
        flat = np.sort(np.abs(frozen["no_agent_model"][i]).ravel())[::-1]
        rows.append({"compound": c["name"], "hits": {a: int(hits[a][i]) for a in arms},
                     "same_action_no_agent_vs_integrated": acts["no_agent_model"][i] == acts["integrated"][i],
                     "no_agent_margin_top1_minus_top2_z": float(flat[0] - flat[1]),
                     "qualifying_actions": int((table[i] != 0).sum())})
    # Jackknife over references: how often does one reference change the deterministic hit count?
    donors = _agent_donors(ref, test)
    jack = {"no_agent_model": [], "integrated": [], "difference": []}
    m_full = deterministic(ry, ty[:, 0])
    for r in range(len(ref)):
        mask = np.arange(len(ref)) != r
        m = deterministic(ry[mask], ty[:, 0])
        if not np.array_equal(m["keep"], keep):
            continue
        remap = {j: (j if j < r else j - 1) for j in range(len(ref)) if j != r}
        integ = []
        for i in range(len(test)):
            d = [remap[j] for j in donors["integrated"].get(i, {}).get("final", []) if j != r]
            donor = donor_prediction(m, i, d) if d else m["phenotype"][i]
            integ.append(.5 * m["ridge"][i] + .5 * donor)
        h0 = hits_of(decode_z(m["no_agent_model"]), table).sum()
        h1 = hits_of(decode_z(np.asarray(integ)), table).sum()
        jack["no_agent_model"].append(int(h0))
        jack["integrated"].append(int(h1))
        jack["difference"].append(int(h0 - h1))
    # Donor overlap and donor-only accuracy (exposed)
    donor_rows = {}
    y = m_full["y"]
    truth_std = ty[:, 1:, :][..., keep] / scale
    for arm in ("integrated", "conventional", "agent_only"):
        overlap, cos_agent, cos_pheno, rank = [], [], [], []
        for i in range(len(test)):
            top5 = list(np.argsort(-m_full["sim"][i], kind="stable")[:5])
            d = donors[arm].get(i, {}).get("final", [])
            if not d:
                continue
            overlap.append(len(set(d) & set(top5)) / len(set(d) | set(top5)))
            order = np.argsort(np.argsort(-m_full["sim"][i], kind="stable"))
            rank.append(float(np.mean(order[d]) + 1))
            pa = donor_prediction(m_full, i, d) - m_full["anchor"][i]
            pp = m_full["phenotype"][i] - m_full["anchor"][i]
            tt = truth_std[i] - m_full["anchor"][i]
            ok = np.isfinite(tt).all(-1)
            cos_agent.append(float(np.mean(ET.cosine(pa[ok], tt[ok]))))
            cos_pheno.append(float(np.mean(ET.cosine(pp[ok], tt[ok]))))
        donor_rows[arm] = {"queries_with_agent_donors": len(overlap), "jaccard_with_phenotype_top5": float(np.mean(overlap)),
                           "mean_anchor_similarity_rank_of_agent_donors": float(np.mean(rank)),
                           "residual_cosine_agent_donors": float(np.mean(cos_agent)),
                           "residual_cosine_phenotype_top5_same_queries": float(np.mean(cos_pheno))}
    discordant = [r for r in rows if r["hits"]["no_agent_model"] != r["hits"]["integrated"]]
    return {"label": "EXPOSED", "hit_counts": {a: int(hits[a].sum()) for a in arms},
            "discordant_no_agent_vs_integrated": discordant,
            "identical_actions_no_agent_vs_integrated": int(sum(r["same_action_no_agent_vs_integrated"] for r in rows)),
            "jackknife_over_references": {k: {"min": int(min(v)), "max": int(max(v)), "mean": float(np.mean(v)),
                                              "fraction_difference_le_0": float(np.mean(np.array(v) <= 0)) if k == "difference" else None}
                                          for k, v in jack.items()},
            "donors": donor_rows, "per_compound": rows}


# ---------------------------------------------------------------- endpoint-aligned decision model
def decision_model(ry: np.ndarray, rrep: dict) -> dict:
    """Everything the aligned decoder needs, estimated from references only.

    * b: slope of observed on predicted response (reference leave-one-out, through the origin): the
      shrinkage that removes regression to the mean from selected actions.
    * sigma: SD of the true mean around b x prediction, net of replicate noise (targets x features).
    * tau: pooled replicate SD (targets x features).
    * platt: logistic recalibration of the chosen action's P(hit), fitted on reference leave-one-out
      per-line choices with sigma re-estimated without the query.
    """
    from scipy.optimize import minimize
    R = len(ry)
    base = deterministic(ry, ry[:, 0])
    keep, scale = base["keep"], base["scale"]
    cols = np.flatnonzero(keep)
    tau = replicate_sd(rrep, R, cols)
    rn = replicate_counts(rrep, R)
    loo = reference_loo(ry)
    lpred, ltruth = loo["no_agent_model"][:, :, cols], ry[:, 1:, cols]
    ok = np.isfinite(ltruth) & np.isfinite(lpred)
    b = float(np.sum(lpred[ok] * ltruth[ok]) / np.sum(lpred[ok] ** 2))
    rep_var = tau ** 2 / np.maximum(np.median(rn, axis=0), 1)[:, None]

    def sigma(exclude=None):
        r = b * lpred - ltruth
        if exclude is not None:
            r = np.delete(r, exclude, axis=0)
        var = np.nanmean(r ** 2, axis=0)
        return np.sqrt(np.maximum(var - rep_var, .25 * var))

    P = np.stack([p_hit(b * lpred[i:i + 1], sigma(i), tau, rn[i:i + 1])[0] for i in range(R)])
    table = qualifying(ry, rrep, keep)
    chosen = []
    for i in range(R):
        for t in range(3):
            j = int(np.argmax(P[i, t]))
            chosen.append((P[i, t, j], int(table[i, t, j] == (1 if lpred[i, t, j] >= 0 else -1))))
    chosen = np.array(chosen)
    lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))

    def nll(w):
        q = 1 / (1 + np.exp(-(w[0] + w[1] * lg(chosen[:, 0]))))
        return -np.sum(chosen[:, 1] * np.log(q + 1e-12) + (1 - chosen[:, 1]) * np.log(1 - q + 1e-12))

    platt = minimize(nll, [0., 1.]).x
    return {"keep": keep, "scale": scale, "cols": cols, "tau": tau, "b": b, "sigma": sigma(),
            "platt": [float(platt[0]), float(platt[1])], "reference_loo_per_line_hits": int(chosen[:, 1].sum()),
            "reference_loo_per_line_n": len(chosen)}


def calibrated(p: np.ndarray, platt: list[float]) -> np.ndarray:
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return 1 / (1 + np.exp(-(platt[0] + platt[1] * np.log(p / (1 - p)))))


def per_line_actions(pred_raw: np.ndarray, scale: np.ndarray, P: np.ndarray | None, kind: str) -> list[tuple[int, int, int]]:
    """One (target, feature, sign) decision per compound and target line, flattened compound-major."""
    acts = []
    for i in range(len(pred_raw)):
        for t in range(pred_raw.shape[1]):
            score = {"z": np.abs(pred_raw[i, t] / scale), "raw": np.abs(pred_raw[i, t]), "phit": None}[kind]
            j = int(np.argmax(P[i, t] if kind == "phit" else score))
            acts.append((t, j, 1 if pred_raw[i, t, j] >= 0 else -1))
    return acts


def across_line_action(pred_raw: np.ndarray, scale: np.ndarray, P: np.ndarray | None, kind: str) -> list[tuple[int, int, int]]:
    if kind == "z":
        return decode_z(pred_raw / scale)
    if kind == "raw":
        return decode_raw(pred_raw)
    flat = P.reshape(len(P), -1)
    F = P.shape[-1]
    return [(int(x // F), int(x % F), 1 if pred_raw[i, x // F, x % F] >= 0 else -1) for i, x in enumerate(np.argmax(flat, 1))]


def per_line_hits(actions: list, table: np.ndarray) -> np.ndarray:
    L = table.shape[1]
    return np.array([int(table[k // L, t, f] == s) for k, (t, f, s) in enumerate(actions)])


def development_decoder() -> dict:
    """The development evidence for the aligned decoder (reference leave-one-out and development split)."""
    ref, ry, rrep, _ = load("reference")
    dev, dy, drep, _ = load("development")
    dm = decision_model(ry, rrep)
    m = deterministic(ry, dy[:, 0])
    pred = m["no_agent_model"] * dm["scale"]
    dn = replicate_counts(drep, len(dev))
    P = p_hit(dm["b"] * pred, dm["sigma"], dm["tau"], dn)
    table = qualifying(dy, drep, dm["keep"])
    out = {"label": "development split; decision model fitted on references only",
           "b": dm["b"], "platt": dm["platt"],
           "reference_loo_per_line_phit_hits": [dm["reference_loo_per_line_hits"], dm["reference_loo_per_line_n"]]}
    for kind in ("z", "raw", "phit"):
        acts = per_line_actions(pred, dm["scale"], P, kind)
        out[f"per_line_hits_{kind}"] = int(per_line_hits(acts, table).sum())
        out[f"across_line_hits_{kind}"] = int(hits_of(across_line_action(pred, dm["scale"], P, kind), table).sum())
    acts = per_line_actions(pred, dm["scale"], P, "phit")
    q = calibrated(np.array([P[k // 3, t, f] for k, (t, f, s) in enumerate(acts)]), dm["platt"])
    h = per_line_hits(acts, table)
    out.update({"per_line_n": len(acts), "calibrated_expected_hits": float(q.sum()), "realised_hits": int(h.sum()),
                "hit_rate_q_ge_half": float(h[q >= .5].mean()), "hit_rate_q_lt_half": float(h[q < .5].mean()),
                "n_q_ge_half": int((q >= .5).sum())})
    write_json("development_decoder.json", out)
    print(json.dumps(out, indent=1))
    return out


# ---------------------------------------------------------------- fresh target lines (pre-registered)
FRESH_LINES = ("A375", "MCF7", "PC3", "YAPC") if DRY else ("A375", "A549", "NPC", "Astrocyte")
FRESH_CACHE = OUT / "cache" if DRY else ROOT / "data/external/gcp2020/fresh_lines"


def _sample_key(sample: dict) -> str:
    pid = sample["pert_id"]
    return pid if pid.startswith("BRD-") else "GCP-" + ET._connectivity(sample["isomeric_smiles"])


def fresh_metadata() -> dict:
    """Eligibility and design replicate counts for the fresh lines, from sample metadata only."""
    manifest = json.loads((ET.CACHE / "metadata.json").read_text(encoding="utf-8"))
    counts: dict = {}
    for plate in manifest["plates"]:
        for s in plate["samples"]:
            if s["pert_type"] == "trt_cp" and s["cell_id"] in FRESH_LINES:
                key = (_sample_key(s), s["cell_id"], float(s["pert_dose"]))
                counts[key] = counts.get(key, 0) + 1
    eligible = {}
    for split in ("reference", "development", "test"):
        rows = []
        for c in ET.eligible_metadata():
            if c["split"] != split:
                continue
            n = [counts.get((c["pert_id"], line, c["selected_dose"]), 0) for line in FRESH_LINES]
            if min(n) >= 2:
                rows.append({"pert_id": c["pert_id"], "name": c["name"], "dose": c["selected_dose"], "design_samples": n})
        eligible[split] = rows
    plates = sorted(p["url"] for p in manifest["plates"] if {s["cell_id"] for s in p["samples"]} <= set(FRESH_LINES))
    result = {"lines": FRESH_LINES, "plates": plates, "eligible": eligible,
              "counts": {k: len(v) for k, v in eligible.items()},
              "metadata_sha256": hashlib.sha256((ET.CACHE / "metadata.json").read_bytes()).hexdigest(),
              "outcomes_opened": False}
    write_json("FRESH_METADATA.json", result)
    print(json.dumps(result["counts"]))
    return result


def _require_freeze() -> dict:
    if DRY:
        return {}
    freeze_path = STUDY / "FREEZE.json"
    if not freeze_path.exists():
        raise SystemExit("FREEZE_MISSING: freeze PROTOCOL.md before opening fresh outcomes")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for relative, digest in freeze["sha256"].items():
        data = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f"FREEZE_MISMATCH: {relative}")
    return freeze


def fresh_prepare() -> dict:
    """Download fresh-line LVL3 plates and normalise exactly as the prior study (LVL3 minus same-plate DMSO median)."""
    _require_freeze()
    meta = json.loads((OUT / "FRESH_METADATA.json").read_text(encoding="utf-8"))
    FRESH_CACHE.mkdir(parents=True, exist_ok=True)
    plates, provenance = [], []
    for url4 in meta["plates"]:
        url = url4.replace("_LVL4.gct", "_LVL3.gct")
        path = ET.CACHE / "matrices" / url.rsplit("/", 1)[1]
        if not path.exists():
            for attempt in range(3):
                try:
                    with ET._open(url) as response:
                        payload = response.read()
                    path.write_bytes(payload)
                    break
                except OSError:
                    if attempt == 2:
                        raise
        with path.open(encoding="utf-8") as stream:
            dims, header, samples = ET._header(stream)
            values = {}
            for _ in range(dims[0]):
                row = stream.readline().rstrip("\r\n").split("\t")
                values[row[0]] = np.asarray(row[dims[2] + 1:], dtype=float)
        controls = [i for i, s in enumerate(samples) if s["pert_iname"].lower() == "dmso"
                    and s["pert_type"] in {"ctrl_vehicle", "ctl_vehicle", "trt_ctl", "trt_cp"}
                    and s["pert_dose"] in {"0", "0.0", "0.1pct", "0.1"} and s["pert_vehicle"].lower() == "dmso"]
        if len(controls) < 2:
            raise SystemExit("NO_REPLICATED_VEHICLE: " + url)
        if len({s["cell_id"] for s in samples}) != 1:
            raise SystemExit("PLATE_MIXES_CONTEXTS: " + url)
        for f, v in values.items():
            fin = v[controls][np.isfinite(v[controls])]
            values[f] = v - np.median(fin) if len(fin) >= 2 else np.full_like(v, np.nan)
        plates.append((samples, values))
        provenance.append({"url": url, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "cell": samples[0]["cell_id"], "vehicle_wells": len(controls)})
    features = sorted(set.intersection(*(set(v) for _, v in plates)))
    grouped: dict = {}
    for samples, values in plates:
        for i, s in enumerate(samples):
            if s["pert_type"] != "trt_cp" or s["pert_iname"].lower() in ET.CONTROL_NAMES:
                continue
            key = (_sample_key(s), s["cell_id"], float(s["pert_dose"]))
            grouped.setdefault(key, []).append(np.asarray([values[f][i] for f in features]))
    roles = {"fresh_reference": ("reference",), "fresh_anchor": ("development", "test"), "fresh_target": ("development", "test")}
    for name, splits in roles.items():
        units = []
        for split in splits:
            for c in meta["eligible"][split]:
                lines = FRESH_LINES if name == "fresh_reference" else (("A375",) if name == "fresh_anchor" else FRESH_LINES[1:])
                for line in lines:
                    reps = grouped.get((c["pert_id"], line, c["dose"]))
                    if reps is not None and len(reps) >= 2:
                        units.append((c["pert_id"], line, c["dose"], np.asarray(reps)))
        np.savez_compressed(FRESH_CACHE / (name + ".npz"), features=np.asarray(features),
                            pert_id=np.asarray([u[0] for u in units]), line=np.asarray([u[1] for u in units]),
                            dose=np.asarray([u[2] for u in units]),
                            mean=np.asarray([np.nanmean(u[3], 0) for u in units]),
                            replicate_values=np.concatenate([u[3] for u in units]),
                            replicate_offsets=np.cumsum([0] + [len(u[3]) for u in units]))
    result = {"plates": provenance, "features": len(features),
              "files": {n: hashlib.sha256((FRESH_CACHE / (n + ".npz")).read_bytes()).hexdigest() for n in roles},
              "target_outcomes_summarised": False}
    write_json("FRESH_PREPARATION.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "plates"}))
    return result


def fresh_tensor(name: str, compounds: list[dict], lines: tuple) -> tuple[np.ndarray, dict, list]:
    with np.load(FRESH_CACHE / (name + ".npz"), allow_pickle=False) as z:
        features = z["features"].tolist()
        tensor = np.full((len(compounds), len(lines), len(features)), np.nan)
        reps = {}
        lookup = {(str(p), str(l), float(d)): k for k, (p, l, d) in enumerate(zip(z["pert_id"], z["line"], z["dose"]))}
        for i, c in enumerate(compounds):
            for t, line in enumerate(lines):
                k = lookup.get((c["pert_id"], line, c["dose"]))
                if k is not None:
                    tensor[i, t] = z["mean"][k]
                    lo, hi = z["replicate_offsets"][k:k + 2]
                    reps[i, t] = z["replicate_values"][lo:hi]
    return tensor, reps, features


def _fresh_inputs():
    meta = json.loads((OUT / "FRESH_METADATA.json").read_text(encoding="utf-8"))
    refs = meta["eligible"]["reference"]
    queries = meta["eligible"]["development"] + meta["eligible"]["test"]
    ry, rrep, features = fresh_tensor("fresh_reference", refs, FRESH_LINES)
    anchors, _, _ = fresh_tensor("fresh_anchor", queries, ("A375",))
    design = np.array([[c["design_samples"][t] for t in (1, 2, 3)] for c in queries])
    return meta, refs, queries, ry, rrep, anchors[:, 0], design, features


def _agent_donors_fresh(refs: list, queries: list) -> dict:
    """Frozen agent donor sets from the 2026-10-13 run, re-indexed to the fresh references."""
    audit = json.loads((PRIOR / "AGENT_AUDIT.json").read_text(encoding="utf-8"))
    index = {c["pert_id"]: j for j, c in enumerate(refs)}
    qpos = {c["pert_id"]: i for i, c in enumerate(queries)}
    out: dict = {}
    for row in audit:
        if row["query"] not in qpos:
            continue
        out.setdefault(row["arm"], {})[qpos[row["query"]]] = {
            "final": [index[d] for d in row["final_donors"] if d in index],
            "initial": [index[d] for d in row["initial_donors"] if d in index],
            "dropped": [d for d in row["final_donors"] if d not in index]}
    return out


def fresh_choose() -> dict:
    """Every pre-registered decision, from references and A375 anchors only; fresh targets stay unopened."""
    _require_freeze()
    if (OUT / "FRESH_RESULTS.json").exists():
        raise SystemExit("ALREADY_EVALUATED: fresh choices are one-shot")
    meta, refs, queries, ry, rrep, anchors, design, features = _fresh_inputs()
    dm = decision_model(ry, rrep)
    m = deterministic(ry, anchors)
    scale, cols = dm["scale"], dm["cols"]
    preds = {name: m[name] * scale for name in ("ridge", "phenotype", "no_agent_model")}
    y = m["y"]
    preds["reference_mean"] = np.broadcast_to(y[:, 1:].mean(0) * scale, preds["ridge"].shape).copy()
    donors = _agent_donors_fresh(refs, queries)
    test_ids = {c["pert_id"] for c in meta["eligible"]["test"]}
    test_rows = [i for i, c in enumerate(queries) if c["pert_id"] in test_ids]
    for arm in ("integrated", "conventional", "agent_only", "source_free_initial"):
        source = "integrated" if arm == "source_free_initial" else arm
        key = "initial" if arm == "source_free_initial" else "final"
        out = np.full_like(preds["ridge"], np.nan)
        for i in test_rows:
            d = donors.get(source, {}).get(i, {}).get(key, [])
            donor = donor_prediction(m, i, d) if d else m["phenotype"][i]
            out[i] = (donor if arm == "agent_only" else .5 * m["ridge"][i] + .5 * donor) * scale
        preds[arm] = out
    P = {name: p_hit(dm["b"] * np.nan_to_num(p), dm["sigma"], dm["tau"], design) for name, p in preds.items()}
    choices = {}
    for name, p in preds.items():
        rows = test_rows if name in ("integrated", "conventional", "agent_only", "source_free_initial") else list(range(len(queries)))
        pp, PP = np.nan_to_num(p), P[name]
        choices[name] = {kind: {"per_line": per_line_actions(pp, scale, PP, kind), "across_line": across_line_action(pp, scale, PP, kind),
                                "rows": rows} for kind in ("z", "raw", "phit")}
        choices[name]["phit"]["per_line_p"] = [float(PP[k // 3, t, f]) for k, (t, f, s) in enumerate(choices[name]["phit"]["per_line"])]
        choices[name]["phit"]["per_line_q"] = calibrated(np.array(choices[name]["phit"]["per_line_p"]), dm["platt"]).tolist()
    np.savez_compressed(OUT / "fresh_predictions.npz", **{k: np.nan_to_num(v) for k, v in preds.items()},
                        keep=dm["keep"], scale=scale, sigma=dm["sigma"], tau=dm["tau"])
    record = {"queries": [c["pert_id"] for c in queries], "test_rows": test_rows, "b": dm["b"], "platt": dm["platt"],
              "features": int(len(cols)), "choices": choices,
              "dropped_agent_donors": {a: {queries[i]["pert_id"]: v["dropped"] for i, v in d.items() if v["dropped"]} for a, d in donors.items()},
              "predictions_sha256": hashlib.sha256((OUT / "fresh_predictions.npz").read_bytes()).hexdigest(),
              "freeze_sha256": None if DRY else hashlib.sha256((STUDY / "FREEZE.json").read_bytes()).hexdigest()}
    write_json("FRESH_CHOICES.json", record)
    print(json.dumps({"queries": len(queries), "features": int(len(cols)), "b": dm["b"], "platt": dm["platt"]}))
    return record
def annotations(compounds: list) -> list[dict]:
    """Repurposing Hub MoA and targets matched by InChIKey connectivity block (metadata only)."""
    import csv
    hub = ROOT / "data/external/lincs_l1000_gse92742"
    with open(hub / "repurposing_drugs_20200324.txt", encoding="latin-1") as f:
        drugs = {r["pert_iname"]: r for r in csv.DictReader((l for l in f if not l.startswith("!")), delimiter="\t")}
    by_block = {}
    with open(hub / "repurposing_samples_20200324.txt", encoding="latin-1") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("!")), delimiter="\t"):
            if r.get("InChIKey") and r["pert_iname"] in drugs:
                by_block.setdefault(r["InChIKey"].split("-")[0], drugs[r["pert_iname"]])
    out = []
    for c in compounds:
        d = by_block.get(c["connectivity"])
        out.append({"moa": set(filter(None, (d or {}).get("moa", "").split("|"))),
                    "targets": set(filter(None, (d or {}).get("target", "").split("|")))} if d else None)
    return out


def _pharm_similarity(qa, ra) -> float:
    """Shared-MoA or target Jaccard; NaN when either compound is unannotated."""
    if qa is None or ra is None:
        return np.nan
    moa = 1.0 if qa["moa"] & ra["moa"] else 0.0
    t = qa["targets"] | ra["targets"]
    return max(moa, len(qa["targets"] & ra["targets"]) / len(t) if t else 0.0)


def donor_information() -> dict:
    """Does pharmacological similarity predict which measured donor transfers well, beyond phenotype?

    Development only: reference leave-one-out queries and the development split. For each query,
    the candidate menu is the frozen agents' menu (top 8 by anchor phenotype union top 8 by structure).
    """
    from scipy.stats import spearmanr
    ref, ry, rrep, _ = load("reference")
    dev, dy, drep, _ = load("development")
    receipts = ET.acquire_pharmacology(ET.eligible_metadata())
    ann_ref, ann_dev = annotations(ref), annotations(dev)
    fp_ref, fp_dev = ET.fingerprints(ref), ET.fingerprints(dev)
    stop = set("the a an and or of in to is as with for by from that this compound drug has it its was are on inhibitor activity".split())

    def tokens(c):
        import re
        text = " ".join(d["text"] for d in receipts.get(c["pert_id"], {}).get("descriptions", []))
        return set(re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())) - stop

    tok_ref, tok_dev = [tokens(c) for c in ref], [tokens(c) for c in dev]

    def tanimoto(a, b):
        inter = (a & b).sum()
        return inter / max(a.sum() + b.sum() - inter, 1)

    rows, policies = [], {}
    queries = [("reference_loo", r) for r in range(len(ref))] + [("development", i) for i in range(len(dev))]
    for split, q in queries:
        if split == "reference_loo":
            others = np.flatnonzero(np.arange(len(ref)) != q)
            m = deterministic(ry[others], ry[q:q + 1, 0])
            truth, qa, qt, qfp, qrep = ry[q], ann_ref[q], tok_ref[q], fp_ref[q], {(0, t): rrep[q, t] for t in (1, 2, 3) if (q, t) in rrep}
        else:
            others = np.arange(len(ref))
            m = deterministic(ry, dy[q:q + 1, 0])
            truth, qa, qt, qfp, qrep = dy[q], ann_dev[q], tok_dev[q], fp_dev[q], {(0, t): drep[q, t] for t in (1, 2, 3) if (q, t) in drep}
        keep, scale, y = m["keep"], m["scale"], m["y"]
        sim = m["sim"][0]
        chem = np.array([tanimoto(qfp, fp_ref[j]) for j in others])
        lex = np.array([len(qt & tok_ref[j]) / max(len(qt | tok_ref[j]), 1) for j in others])
        pharm = np.array([_pharm_similarity(qa, ann_ref[j]) for j in others])
        menu = sorted(set(np.argsort(-sim, kind="stable")[:8]) | set(np.argsort(-chem, kind="stable")[:8]))
        t_std = truth[1:, keep] / scale
        resid_true = t_std - m["anchor"][0]
        ok = np.isfinite(resid_true).all(-1)
        for d in menu:
            pd_ = y[d, 1:] - y[d, :1]
            acc = float(np.mean(ET.cosine(pd_[ok], resid_true[ok])))
            rows.append({"split": split, "query": int(q), "anchor_sim": float(sim[d]), "chem": float(chem[d]),
                         "lexical": float(lex[d]), "pharm": float(pharm[d]), "accuracy": acc})
        # Donor-selection policies under the frozen blend and both decoders.
        table = qualifying(truth[None], qrep, keep)

        def blend(donors, weights=None):
            pdn = m["anchor"][0] + (np.einsum("r,rtf->tf", weights, y[donors, 1:] - y[donors, :1]) if weights is not None
                                    else (y[donors, 1:] - y[donors, :1]).mean(0))
            return .5 * m["ridge"][0] + .5 * pdn

        top5 = list(np.argsort(-sim, kind="stable")[:5])
        w = np.maximum(sim[top5], 0)
        w = w / w.sum() if w.sum() else np.full(5, .2)
        pharm_menu = [d for d in menu if pharm[d] > 0]
        lex_menu = sorted(menu, key=lambda d: (-lex[d], -sim[d]))[:5]
        cand = {"phenotype_weighted_top5": blend(top5, w), "phenotype_equal_top5": blend(top5),
                "lexical_top5_in_menu": blend(lex_menu),
                "annotated_pharmacology_in_menu": blend(pharm_menu[:5]) if pharm_menu else blend(top5, w),
                "menu_equal_all": blend(menu)}
        for name, pred in cand.items():
            pr = pred[None]
            tt = t_std[None]
            cos = ET.cosine(pr - pr.mean(-1, keepdims=True), np.nan_to_num(tt - np.nanmean(tt, -1, keepdims=True)))
            okc = np.isfinite(tt).all(-1)[0]
            entry = policies.setdefault(split, {}).setdefault(name, {"hits_z": 0, "hits_raw": 0, "cos": [], "n": 0})
            entry["hits_z"] += int(hits_of(decode_z(pr), table).sum())
            entry["hits_raw"] += int(hits_of(decode_raw(pr * scale), table).sum())
            entry["cos"].append(float(cos[0, okc].mean()))
            entry["n"] += 1
    for split in policies:
        for name, e in policies[split].items():
            e["mean_cosine"] = float(np.mean(e.pop("cos")))
    # Within-query association of donor accuracy with each similarity, and the partial association
    # of pharmacology given anchor similarity (residualised within query).
    import collections
    by_q = collections.defaultdict(list)
    for r in rows:
        by_q[(r["split"], r["query"])].append(r)
    assoc = {}
    for key in ("anchor_sim", "chem", "lexical", "pharm"):
        rhos = []
        for rs in by_q.values():
            x = np.array([r[key] for r in rs]); a = np.array([r["accuracy"] for r in rs])
            fin = np.isfinite(x)
            if fin.sum() >= 4 and np.ptp(x[fin]) > 0:
                rhos.append(spearmanr(x[fin], a[fin]).statistic)
        assoc[key] = {"queries": len(rhos), "mean_within_query_spearman": float(np.nanmean(rhos))}
    partial = {}
    for key in ("chem", "lexical", "pharm"):
        xs, ys = [], []
        for rs in by_q.values():
            x = np.array([r[key] for r in rs]); s = np.array([r["anchor_sim"] for r in rs]); a = np.array([r["accuracy"] for r in rs])
            fin = np.isfinite(x)
            if fin.sum() >= 4 and np.ptp(x[fin]) > 0:
                X = np.column_stack([np.ones(fin.sum()), s[fin]])
                rx = x[fin] - X @ np.linalg.lstsq(X, x[fin], rcond=None)[0]
                ra = a[fin] - X @ np.linalg.lstsq(X, a[fin], rcond=None)[0]
                xs.append(rx); ys.append(ra)
        x, a = np.concatenate(xs), np.concatenate(ys)
        rng = np.random.default_rng(SEED)
        boots = []
        lens = np.cumsum([0] + [len(v) for v in xs])
        for _ in range(2000):
            pick = rng.integers(len(xs), size=len(xs))
            xb = np.concatenate([xs[p] for p in pick]); yb = np.concatenate([ys[p] for p in pick])
            boots.append(np.corrcoef(xb, yb)[0, 1])
        partial[key] = {"queries": len(xs), "partial_correlation_given_anchor_similarity": float(np.corrcoef(x, a)[0, 1]),
                        "query_bootstrap_95": np.quantile(boots, [.025, .975]).tolist()}
    result = {"label": "development data only (reference leave-one-out and development split)",
              "candidate_rows": len(rows), "association_with_single_donor_accuracy": assoc,
              "partial_given_anchor_similarity": partial, "policies": policies,
              "annotated_compounds": {"reference": sum(a is not None for a in ann_ref), "development": sum(a is not None for a in ann_dev)}}
    write_json("donor_information.json", result)
    print(json.dumps(result, indent=1))
    return result


def deterministic_partial(base: np.ndarray, memory: list, anchors: np.ndarray, keep: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """The frozen blend with admitted partial references (A375 anchor plus one measured target line).

    ``memory`` holds (anchor_raw, target_index 1..3, response_raw). Feature mask and scale stay those
    of the base references, so memory changes only which donors and ridge rows exist.
    Returns raw predictions, queries x 3 x kept features.
    """
    rows = [base[..., keep]]
    for a, t, r in memory:
        row = np.full((1,) + base.shape[1:], np.nan)
        row[0, 0], row[0, t] = a, r
        rows.append(row[..., keep])
    y = np.concatenate(rows) / scale
    ref_anchor_mean = y[:len(base), 0].mean(0)
    # Admitted anchors are imputed like query anchors; admission already required a complete response.
    y[len(base):, 0] = np.where(np.isfinite(y[len(base):, 0]), y[len(base):, 0], ref_anchor_mean)
    anchor = anchors[:, keep] / scale
    anchor = np.where(np.isfinite(anchor), anchor, ref_anchor_mean)
    center = y[:, 0].mean(0)
    sim = ET.cosine(anchor[:, None] - center, y[None, :, 0] - center)
    out = np.zeros((len(anchor), 3, keep.sum()))
    for t in (1, 2, 3):
        have = np.isfinite(y[:, t]).all(-1)
        target_mean = y[have, t].mean(0)
        fitted = fit_ridge_map(y[have, 0] - center, y[have, t] - target_mean, lams=(1., 10., 100., 1000.))
        ridge = (anchor - center) @ fitted.B + target_mean
        idx = np.flatnonzero(have)
        for i in range(len(anchor)):
            order = idx[np.argsort(-sim[i, idx], kind="stable")[:5]]
            w = np.maximum(sim[i, order], 0)
            w = w / w.sum() if w.sum() else np.full(len(order), 1 / len(order))
            pheno = anchor[i] + w @ (y[order, t] - y[order, 0])
            out[i, t - 1] = .5 * ridge[i] + .5 * pheno
    return out * scale


def _bootstrap(values_by_cluster: list[np.ndarray], stat, *, draws: int = 10000) -> list[float]:
    rng = np.random.default_rng(SEED)
    n = len(values_by_cluster)
    return np.quantile([stat([values_by_cluster[j] for j in rng.integers(n, size=n)]) for _ in range(draws)], [.025, .975]).tolist()


def fresh_evaluate() -> dict:
    """One-shot scoring of the frozen choices on the fresh target lines, then the exploratory memory loop."""
    sys.path.insert(0, str(ROOT))
    from tools.evaluation.scoring import cluster_signflip_test
    _require_freeze()
    if (OUT / "FRESH_RESULTS.json").exists():
        raise SystemExit("ALREADY_EVALUATED")
    record = json.loads((OUT / "FRESH_CHOICES.json").read_text(encoding="utf-8"))
    if record["predictions_sha256"] != hashlib.sha256((OUT / "fresh_predictions.npz").read_bytes()).hexdigest():
        raise SystemExit("CHOICES_TAMPERED")
    meta, refs, queries, ry, rrep, anchors, design, features = _fresh_inputs()
    truth, trep, _ = fresh_tensor("fresh_target", queries, FRESH_LINES[1:])
    full = np.concatenate([anchors[:, None], truth], axis=1)
    reps = {(i, t + 1): v for (i, t), v in trep.items()}
    with np.load(OUT / "fresh_predictions.npz") as z:
        keep, scale = z["keep"], z["scale"]
        preds = {k: z[k] for k in z.files if k not in ("keep", "scale", "sigma", "tau")}
    cols = np.flatnonzero(keep)
    table = qualifying(full, reps, keep)
    ids = record["queries"]
    choices = record["choices"]
    out: dict = {"n_queries": len(queries), "n_test_rows": len(record["test_rows"]),
                 "oracle_per_line_attainable": int((table != 0).any(-1).sum()),
                 "random_action_hit_rate": float((table != 0).mean() / 2)}

    def pl(name, kind):
        rows = choices[name][kind]["rows"]
        h = per_line_hits([tuple(a) for a in choices[name][kind]["per_line"]], table)
        return np.array([h[3 * i:3 * i + 3] for i in rows]), rows

    def al(name, kind):
        rows = choices[name][kind]["rows"]
        h = hits_of([tuple(a) for a in choices[name][kind]["across_line"]], table)
        return h[rows], rows

    summary = {}
    for name in choices:
        summary[name] = {}
        for kind in ("z", "raw", "phit"):
            h, rows = pl(name, kind)
            a, _ = al(name, kind)
            summary[name][kind] = {"per_line_hits": int(h.sum()), "per_line_n": int(h.size),
                                   "across_line_hits": int(a.sum()), "across_line_n": len(a)}
    out["hits"] = summary

    # ---- primary P1: per-line PHIT minus Z, no-agent model, all 47 compounds
    hp, _ = pl("no_agent_model", "phit")
    hz, _ = pl("no_agent_model", "z")
    diff = (hp - hz).ravel()
    clusters = [ids[i] for i in range(len(queries)) for _ in range(3)]
    p1 = cluster_signflip_test(diff.tolist(), clusters)
    p1["hit_rate_difference"] = float(diff.mean())
    p1["bootstrap_95"] = _bootstrap([hp[i] - hz[i] for i in range(len(queries))], lambda xs: np.concatenate(xs).mean())
    p1["pass"] = bool(p1["p_greater"] < .025)
    out["P1_aligned_decoder_per_line"] = p1

    # ---- primary P2: calibrated P(hit) separates hits (abstention value)
    q = np.array(choices["no_agent_model"]["phit"]["per_line_q"]).reshape(-1, 3)
    groups = [(q[i], hp[i]) for i in range(len(queries))]

    def gap(gs):
        qq = np.concatenate([g[0] for g in gs]); hh = np.concatenate([g[1] for g in gs])
        hi, lo = hh[qq >= .5], hh[qq < .5]
        return (hi.mean() if len(hi) else np.nan) - (lo.mean() if len(lo) else np.nan)

    boots = []
    rng = np.random.default_rng(SEED)
    for _ in range(10000):
        pick = rng.integers(len(groups), size=len(groups))
        boots.append(gap([groups[j] for j in pick]))
    lower = float(np.nanquantile(boots, .025))
    qa, ha = q.ravel(), hp.ravel()
    out["P2_calibrated_abstention"] = {
        "n_q_ge_half": int((qa >= .5).sum()), "hit_rate_q_ge_half": float(ha[qa >= .5].mean()) if (qa >= .5).any() else None,
        "n_q_lt_half": int((qa < .5).sum()), "hit_rate_q_lt_half": float(ha[qa < .5].mean()) if (qa < .5).any() else None,
        "difference": float(gap(groups)), "bootstrap_lower_2_5": lower, "pass": bool(lower > 0),
        "calibration_in_the_large": {"expected": float(qa.sum()), "realised": int(ha.sum()),
                                     "per_decision": float((qa.sum() - ha.sum()) / len(ha)),
                                     "bootstrap_95": _bootstrap([groups[i][0] - groups[i][1] for i in range(len(groups))],
                                                                lambda xs: np.concatenate(xs).mean())}}

    # ---- secondary contrasts
    sec = {}
    ha_p, _ = al("no_agent_model", "phit")
    ha_z, _ = al("no_agent_model", "z")
    sec["S1_across_line_phit_minus_z"] = cluster_signflip_test((ha_p - ha_z).tolist(), ids)
    hr, _ = pl("no_agent_model", "raw")
    sec["S2_per_line_raw_minus_z"] = cluster_signflip_test((hr - hz).ravel().tolist(), clusters)
    sec["S2_per_line_phit_minus_raw"] = cluster_signflip_test((hp - hr).ravel().tolist(), clusters)
    test_rows = record["test_rows"]
    test_ids = [ids[i] for i in test_rows]
    tclusters = [ids[i] for i in test_rows for _ in range(3)]
    # S3: donor accuracy (residual cosine against the anchor, standardized) on the 20 test compounds
    anchor_std = np.where(np.isfinite(anchors[:, keep]), anchors[:, keep], np.nan) / scale
    truth_std = truth[..., keep] / scale

    def residual_cos(name, rows):
        vals = []
        for i in rows:
            p = preds[name][i] / scale - anchor_std[i]
            tt = truth_std[i] - anchor_std[i]
            ok = np.isfinite(tt).all(-1) & np.isfinite(p).all(-1)
            vals.append(float(np.mean(ET.cosine(p[ok], tt[ok]))) if ok.any() else np.nan)
        return np.array(vals)

    s3 = {}
    for arm in ("integrated", "conventional", "agent_only", "source_free_initial"):
        comp = "phenotype" if arm == "agent_only" else "no_agent_model"
        a, c = residual_cos(arm, test_rows), residual_cos(comp, test_rows)
        d = a - c
        s3[arm] = {"comparator": comp, "mean_residual_cosine_arm": float(np.nanmean(a)), "mean_residual_cosine_comparator": float(np.nanmean(c)),
                   "difference": float(np.nanmean(d)), "bootstrap_95": _bootstrap([np.array([x]) for x in d[np.isfinite(d)]], lambda xs: np.concatenate(xs).mean()),
                   "signflip": cluster_signflip_test(d[np.isfinite(d)].tolist(), [test_ids[k] for k in np.flatnonzero(np.isfinite(d))])}
        h_arm, _ = pl(arm, "phit")
        h_cmp = hp[test_rows] if comp == "no_agent_model" else pl("phenotype", "phit")[0][test_rows]
        s3[arm]["per_line_phit_hits_arm_vs_comparator"] = [int(h_arm.sum()), int(h_cmp.sum())]
    sec["S3_agent_donors_vs_deterministic"] = s3
    # S4: replication of the frozen across-line Z comparison on fresh lines, test compounds
    s4 = {}
    base_al = al("no_agent_model", "z")[0][test_rows]
    for arm in ("integrated", "conventional", "agent_only", "source_free_initial"):
        h, _ = al(arm, "z")
        s4[arm] = {"hits_arm": int(h.sum()), "hits_no_agent_model": int(base_al.sum()), "n": len(h),
                   "signflip_no_agent_minus_arm": cluster_signflip_test((base_al - h).tolist(), test_ids)}
    sec["S4_frozen_endpoint_replication"] = s4
    # S5: zero arm (no anchor) and anchor value
    hzero, _ = pl("reference_mean", "phit")
    sec["S5_anchor_value_per_line_phit"] = {"reference_mean_hits": int(hzero.sum()), "no_agent_model_hits": int(hp.sum()),
                                            "signflip_anchor_minus_zero": cluster_signflip_test((hp - hzero).ravel().tolist(), clusters)}
    out["secondary"] = sec

    # ---- exploratory S6: memory loop (validated outcomes become partial references)
    out["S6_memory_loop"] = _memory_loop(ry, rrep, queries, anchors, design, truth, trep, table, keep, scale, record)
    write_json("FRESH_RESULTS.json", out)
    print(json.dumps({"P1": {k: out["P1_aligned_decoder_per_line"][k] for k in ("estimate", "hit_rate_difference", "p_greater", "pass")},
                      "P2": {k: out["P2_calibrated_abstention"][k] for k in ("hit_rate_q_ge_half", "hit_rate_q_lt_half", "bootstrap_lower_2_5", "pass")}}, indent=1))
    return out


def _memory_loop(ry, rrep, queries, anchors, design, truth, trep, table, keep, scale, record) -> dict:
    """Process fresh compounds in hash order; after each decision the chosen line is 'measured'.

    no_memory: base references only. memory: the measured (anchor, line, response) is admitted for
    later compounds. shuffled: the same line's response of a different compound is admitted with the
    anchor, breaking the anchor-response link while keeping the data volume.
    """
    sys.path.insert(0, str(ROOT))
    from tools.evaluation.scoring import cluster_signflip_test
    dm = decision_model(ry, rrep)
    cols = np.flatnonzero(keep)
    order = sorted(range(len(queries)), key=lambda i: hashlib.sha256(("memory:" + queries[i]["pert_id"]).encode()).hexdigest())
    partner = {order[k]: order[(k + 1) % len(order)] for k in range(len(order))}
    memories = {"no_memory": [], "memory": [], "shuffled": []}
    hits = {arm: {} for arm in memories}
    cos = {arm: {} for arm in memories}
    accessed = []
    truth_std = truth[..., keep] / scale
    anchor_std = anchors[:, keep] / scale
    for i in order:
        for arm, mem in memories.items():
            pred = deterministic_partial(ry, mem, anchors[i:i + 1], keep, scale)
            P = p_hit(dm["b"] * pred, dm["sigma"], dm["tau"], design[i:i + 1])
            acts = per_line_actions(pred, scale, P, "phit")
            hits[arm][i] = [int(table[i, t, f] == s) for t, f, s in acts]
            p = pred[0] / scale - anchor_std[i]
            tt = truth_std[i] - anchor_std[i]
            ok = np.isfinite(tt).all(-1)
            cos[arm][i] = float(np.mean(ET.cosine(p[ok], tt[ok]))) if ok.any() else np.nan
            if arm == "no_memory":
                continue
            t, f, s = across_line_action(pred, scale, P, "phit")[0]
            source = i if arm == "memory" else partner[i]
            if (source, t) in trep:
                accessed.append((arm, queries[source]["pert_id"], FRESH_LINES[t + 1]))
                if np.isfinite(truth[source, t][keep]).all():      # admission needs a complete response
                    mem.append((anchors[i], t + 1, truth[source, t]))
    later = order[len(order) // 2:]
    res = {"order": [queries[i]["pert_id"] for i in order], "admitted": {a: len(m) for a, m in memories.items()},
           "measurement_reads": len(accessed)}
    for arm in ("memory", "shuffled"):
        for span, rows in (("all", order[1:]), ("second_half", later)):
            dh = [np.sum(hits[arm][i]) - np.sum(hits["no_memory"][i]) for i in rows]
            dc = [cos[arm][i] - cos["no_memory"][i] for i in rows if np.isfinite(cos[arm][i])]
            res[f"{arm}_minus_no_memory_{span}"] = {
                "hits_difference": int(np.sum(dh)),
                "hits_signflip": cluster_signflip_test([float(x) for x in dh], [queries[i]["pert_id"] for i in rows]),
                "residual_cosine_difference": float(np.mean(dc)),
                "cosine_signflip": cluster_signflip_test(dc, [str(k) for k in range(len(dc))])}
    return res


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = {"parity": parity, "diagnose": diagnose, "donors": donor_information, "decoder": development_decoder,
                "fresh-metadata": fresh_metadata, "fresh-prepare": fresh_prepare, "fresh-choose": fresh_choose,
                "fresh-evaluate": fresh_evaluate}
    parser.add_argument("command", choices=tuple(commands))
    args = parser.parse_args()
    commands[args.command]()


if __name__ == "__main__":
    main()
