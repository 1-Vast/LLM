"""Stage 5: world-model ladder for zero-shot context transfer (depth-corrected comparisons).

Evaluation lines are refused until WORLD_FREEZE.json exists and its protocol hash matches
WORLD_PROTOCOL.json. Development lines (PANC-1, HepG2/C3A) are used for every selection.
Training contexts supply the panel; STATE was trained on them, so they are never scored as
STATE evidence (only as an in-sample leakage diagnostic).

Every panel-based forecast is linear in the training contexts' observed responses:
    forecast(g) = sum_l W[l, g] * Delta(l, g)  (+ gamma_S * devS(g) for STATE rungs)
Training contexts were subsampled to 32 treated cells per well, so a panel forecast carries its
own sampling variance sum_l W[l,g]^2 * noise_l(g). STATE was trained on full-depth data and has
none. Comparing raw squared errors would penalise the comparators for my subsampling, so every
comparison uses the depth-corrected squared error
    SE_corr = mean_g (forecast - Delta_L)^2 - sum_l W^2 noise_l - noise_L,
an unbiased estimate of the error the same estimator would have with infinitely deep wells,
against the noise-free response of the held-out line.

Rungs for held-out line L and (label, plate) group g:
  M0   panel perturbation mean (equal or precision weights; chosen on development)
  M1   M0 + gamma_K * dev, dev from basal similarity: k=5 nearest contexts (registered) or kernel
       ridge over contexts (added comparator; lambda chosen by leave-one-context-out on training)
  M2   M0 + gamma_S * devS, devS = S(L,g) - mean_l S(l,g) (frozen checkpoint, paired DMSO, 256 cells)
  M21  M1 + gamma_S * devS
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from remote import CACHE  # noqa: E402

SPLIT = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
HELDOUT = SPLIT["files"]  # name -> file
TRAIN_FILES = [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in set(HELDOUT.values())]
GAMMAS = (0.0, 0.25, 0.5, 1.0)
K_NEIGHBOURS = 5
KRR_LAMBDAS = (0.1, 1.0, 10.0, 100.0)
GATE_LAMBDAS = (0.0, 0.5, 2.0, 8.0)
MIN_TREATED, MIN_REFERENCE, MIN_PANEL_LINES, MIN_PANEL_CELLS = 50, 100, 30, 8
CONTROL = "[('DMSO_TF', 0.0, 'uM')]"


def guard(names):
    evaluation = [n for n in names if n in SPLIT["evaluation"]]
    if not evaluation:
        return
    freeze = HERE / "WORLD_FREEZE.json"
    if not freeze.exists():
        raise PermissionError("evaluation lines refused: WORLD_FREEZE.json absent")
    frozen = json.loads(freeze.read_text(encoding="utf-8"))
    actual = hashlib.sha256((HERE / "WORLD_PROTOCOL.json").read_bytes()).hexdigest()
    if frozen["protocol_sha256"] != actual:
        raise PermissionError("evaluation lines refused: protocol changed after freeze")


def load_obs(file):
    return dict(np.load(CACHE / "observations" / f"{file}.npz"))


def load_state(file):
    return dict(np.load(CACHE / "state_forecasts" / f"{file}.npz"))


def responses(obs):
    """Delta, sampling noise and split-half deltas per group, keyed (label, plate)."""
    ctrl = {p: i for i, p in enumerate(obs["ctrl_plate"])}
    ci = np.array([ctrl[p] for p in obs["plate"]])
    delta = obs["mean"].astype(np.float64) - obs["ctrl_mean"][ci]
    with np.errstate(invalid="ignore"):
        var_t = np.nanmean(obs["var"], 1) if obs["var"].size else np.zeros(0)
    noise = var_t / np.maximum(obs["n"], 1) + np.mean(obs["ctrl_var"][ci], 1) / np.maximum(obs["ctrl_n"][ci], 1)
    deltaA = obs["meanA"].astype(np.float64) - obs["ctrl_meanA"][ci]
    deltaB = obs["meanB"].astype(np.float64) - obs["ctrl_meanB"][ci]
    full_well_noise = var_t / np.maximum(obs["available_full"], 1) + \
        np.mean(obs["ctrl_var"][ci], 1) / np.maximum(obs["ctrl_available_full"][ci], 1)
    keys = list(zip(obs["label"].tolist(), obs["plate"].tolist()))
    return {"keys": keys, "delta": delta, "noise": noise, "deltaA": deltaA, "deltaB": deltaB,
            "n": obs["n"], "ref_n": obs["ctrl_n"][ci], "full_well_noise": full_well_noise}


class Panel:
    """Training-context responses (NaN-free with an availability mask) and STATE forecasts."""

    def __init__(self, keys, files=None):
        self.files = list(files) if files is not None else list(TRAIN_FILES)
        self.keys = list(keys)
        index = {k: i for i, k in enumerate(self.keys)}
        L, K = len(self.files), len(self.keys)
        self.delta = np.zeros((L, K, 2000), dtype=np.float32)
        self.noise = np.full((L, K), np.nan)
        self.noise_gene = np.zeros((L, K, 2000), dtype=np.float32)  # per-coordinate sampling variance
        self.state = np.zeros((L, K, 2000), dtype=np.float16)  # in-sample diagnostic only
        state_ok = np.zeros((L, K), bool)
        self.basal = np.zeros((L, 2000))
        for li, file in enumerate(self.files):
            obs = load_obs(file)
            r = responses(obs)
            ctrl = {p: i for i, p in enumerate(obs["ctrl_plate"])}
            for j, key in enumerate(r["keys"]):
                if key in index and obs["n"][j] >= MIN_PANEL_CELLS:
                    self.delta[li, index[key]] = r["delta"][j]
                    self.noise[li, index[key]] = r["noise"][j]
                    c = ctrl[key[1]]
                    self.noise_gene[li, index[key]] = obs["var"][j] / obs["n"][j] + obs["ctrl_var"][c] / obs["ctrl_n"][c]
            s = load_state(file)
            for j, key in enumerate(zip(s["label"].tolist(), s["plate"].tolist())):
                if key in index:
                    self.state[li, index[key]] = s["paired_delta"][j]
                    state_ok[li, index[key]] = True
            self.basal[li] = np.average(obs["basal_mean"], axis=0, weights=obs["basal_n"])
        self.avail = np.isfinite(self.noise)
        self.noise0 = np.where(self.avail, self.noise, 0.0)
        self.coverage = self.avail.sum(0)
        self.state_mean = (self.state.astype(np.float32) * state_ok[..., None]).sum(0) / np.maximum(state_ok.sum(0), 1)[:, None]
        self.state_coverage = state_ok.sum(0)

    # ---- weight matrices (L, K) ----
    def w_equal(self):
        return self.avail / np.maximum(self.avail.sum(0), 1)

    def w_precision(self):
        w = np.where(self.avail, 1.0 / np.maximum(self.noise0, 1e-12), 0.0)
        return w / np.maximum(w.sum(0), 1e-300)

    def w_m0(self, variant):
        return {"equal": self.w_equal, "precision": self.w_precision}[variant]()

    def similarity(self, basal, exclude=None):
        keep = np.ones(len(self.files), bool)
        if exclude is not None:
            keep[exclude] = False
        centre = self.basal[keep].mean(0)
        a, b = basal - centre, self.basal - centre
        return (b @ a) / (np.linalg.norm(b, axis=1) * np.linalg.norm(a) + 1e-12), keep

    def w_knn_dev(self, basal, exclude=None):
        corr, keep = self.similarity(basal, exclude)
        order = [i for i in np.argsort(-corr) if keep[i]][:K_NEIGHBOURS]
        near = np.zeros(len(self.files), bool)
        near[order] = True
        avail = self.avail & keep[:, None]
        near_avail = avail & near[:, None]
        return near_avail / np.maximum(near_avail.sum(0), 1) - avail / np.maximum(avail.sum(0), 1)

    def krr_alpha(self, basal, lam, exclude=None):
        keep = np.ones(len(self.files), bool)
        if exclude is not None:
            keep[exclude] = False
        X = self.basal[keep]
        centre = X.mean(0)
        Xc, x = X - centre, basal - centre
        G = Xc @ Xc.T
        scale = np.trace(G) / len(G)
        alpha = np.zeros(len(self.files))
        alpha[keep] = np.linalg.solve(G + lam * scale * np.eye(len(G)), Xc @ x)
        return alpha

    def w_krr_dev(self, basal, lam, exclude=None):
        alpha = self.krr_alpha(basal, lam, exclude)
        keep = np.ones(len(self.files), bool)
        if exclude is not None:
            keep[exclude] = False
        avail = self.avail & keep[:, None]
        a = alpha[:, None] * avail
        return a - avail * (a.sum(0) / np.maximum(avail.sum(0), 1))[None, :]

    def gate(self, basal, W0, cols, lam, exclude=None):
        """Per-coordinate weighted regression of the panel response on that coordinate's basal level.

        Returns (deviation from the M0 forecast, per-coordinate dev weights' noise pieces) for cols:
        dev[k, j] = sum_l d[l, k, j] * Delta[l, k, j],  d = w0 * (x_l - xbar)(x_L - xbar) / (SSw (1 + lam)).
        """
        x = self.basal  # (L, J): basal-half DMSO means of training contexts
        out = np.zeros((len(cols), 2000))
        n0d = np.zeros(len(cols))
        ndd = np.zeros(len(cols))
        for a in range(0, len(cols), 100):
            c = np.asarray(cols[a:a + 100])
            w0 = W0[:, c].copy()  # (L, k)
            if exclude is not None:
                w0[exclude] = 0.0
                w0 = w0 / np.maximum(w0.sum(0), 1e-300)
            xbar = w0.T @ x  # (k, J)
            xc = x[:, None, :] - xbar[None]  # (L, k, J)
            ss = np.einsum("lk,lkj->kj", w0, xc ** 2)
            coef = (basal[None] - xbar) / np.maximum(ss * (1 + lam), 1e-12)  # (k, J)
            d = w0[..., None] * xc * coef[None]  # (L, k, J)
            out[a:a + 100] = np.einsum("lkj,lkj->kj", d, self.delta[:, c].astype(np.float64))
            ng = self.noise_gene[:, c].astype(np.float64)
            n0d[a:a + 100] = np.einsum("lk,lkj,lkj->k", w0, d, ng) / 2000
            ndd[a:a + 100] = np.einsum("lkj,lkj->k", d ** 2, ng) / 2000
        return out, n0d, ndd

    # ---- application ----
    def apply(self, W, cols=None):
        cols = np.arange(len(self.keys)) if cols is None else np.asarray(cols)
        out = np.zeros((len(cols), 2000))
        for a in range(0, len(cols), 200):
            c = cols[a:a + 200]
            out[a:a + 200] = np.einsum("lk,lkd->kd", W[:, c], self.delta[:, c], optimize=True)
        return out

    def noise_of(self, W, cols=None):
        cols = np.arange(len(self.keys)) if cols is None else np.asarray(cols)
        return (W[:, cols] ** 2 * self.noise0[:, cols]).sum(0)

    def select_krr_lambda(self, chunk=150):
        """Leave-one-context-out over training contexts only; depth-corrected deviation error."""
        errors = {}
        L = len(self.files)
        for lam in KRR_LAMBDAS:
            total, count = 0.0, 0
            for li in range(L):
                Wd = self.w_krr_dev(self.basal[li], lam, exclude=li)
                Wm = self.avail.copy()
                Wm[li] = False
                Wm = Wm / np.maximum(Wm.sum(0), 1)
                cols = np.flatnonzero(self.avail[li] & (self.coverage >= MIN_PANEL_LINES))
                for a in range(0, len(cols), chunk):
                    c = cols[a:a + chunk]
                    W = Wm[:, c] + Wd[:, c]
                    pred = np.einsum("lk,lkd->kd", W, self.delta[:, c], optimize=True)
                    se = np.mean((pred - self.delta[li, c]) ** 2, 1) - (W ** 2 * self.noise0[:, c]).sum(0) - self.noise0[li, c]
                    total += se.sum(); count += len(c)
            errors[str(lam)] = total / count
        best = min(errors, key=errors.get)
        return float(best), errors


def target(name, panel):
    """Observed responses and STATE forecasts for one held-out line, aligned to panel keys."""
    file = HELDOUT[name]
    obs = load_obs(file)
    r = responses(obs)
    s = load_state(file)
    skey = {k: j for j, k in enumerate(zip(s["label"].tolist(), s["plate"].tolist()))}
    pidx = {k: i for i, k in enumerate(panel.keys)}
    rows = [j for j, k in enumerate(r["keys"]) if k in pidx and k in skey]
    keys = [r["keys"][j] for j in rows]
    pi = np.array([pidx[k] for k in keys])
    si = np.array([skey[k] for k in keys])
    basal = np.average(obs["basal_mean"], axis=0, weights=obs["basal_n"])
    eligible = (r["n"][rows] >= MIN_TREATED) & (r["ref_n"][rows] >= MIN_REFERENCE) & (panel.coverage[pi] >= MIN_PANEL_LINES)
    S = s["paired_delta"][si].astype(np.float64)
    dmso_index = {p: i for i, p in enumerate(s["dmso_plates"])}
    raw = s["predicted_mean"][si] - s["basal_mean_by_plate"][[dmso_index[k[1]] for k in keys]]
    return {"name": name, "keys": keys, "panel_index": pi, "eligible": eligible,
            "delta": r["delta"][rows], "noise": r["noise"][rows], "deltaA": r["deltaA"][rows], "deltaB": r["deltaB"][rows],
            "full_well_noise": r["full_well_noise"][rows], "n": r["n"][rows],
            "S": S, "S_raw": raw.astype(np.float64), "devS": S - panel.state_mean[pi], "basal": basal}


def corrected_se(pred, obs, model_noise, eval_noise):
    return np.mean((pred - obs) ** 2, axis=1) - model_noise - eval_noise


def parse_label(label):
    """Single-compound Tahoe label "[('name', dose, 'uM')]" -> (name, dose); names may contain commas."""
    import ast
    (name, dose, unit), = ast.literal_eval(label)
    return name, float(dose)


def drug_of(key):
    return parse_label(key[0])[0]


def dose_of(key):
    return parse_label(key[0])[1]


def cluster_bootstrap(values, clusters, reps=2000, seed=20261007):
    values = np.asarray(values, float)
    ids = np.unique(clusters)
    members = {c: np.flatnonzero(clusters == c) for c in ids}
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(reps):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([members[c] for c in pick])
        stats.append(values[idx].mean())
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))
