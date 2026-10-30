"""Typed experimental/state programs: Q (measurement plan), phi (state coordinates), f (response model), Omega.

A program is a JSON spec in a small grammar. `fit_program` learns f from released history by simulating the
program's own measurement plan on each released cell (leave-that-cell-out), so Q, phi and f execute without
reading any evaluation target. `run_program` executes a fitted program on a Campaign through its ledgered
`query`. Fitted programs serialise to JSON with every array needed to reproduce predictions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass

import numpy as np

from svc_world import SHORTLIST_K, Campaign, History, Static, digest, shortlist

GRAMMAR_VERSION = "1"
PROBE_RULES = ("random", "coverage", "variance", "aoptimal", "witness", "exploit", "focus")
BASELINE_ONLY_RULES = ("bayes_voi",)
COORD_TYPES = ("global", "class", "drug", "latent")
INTERACTIONS = ("class", "anchor", "product")
LIMITS = {"max_entries": 8, "max_stages": 3, "max_latent": 4, "max_complexity": 14}
K_MAX = 4


# --------------------------------------------------------------------------- spec validation / canonical form
def base_spec() -> dict:
    """The base library program P0: global + two latent coordinates; coverage probes then confirmation."""
    return {"phi": [{"t": "global"}, {"t": "latent", "k": 2}],
            "Q": [{"kind": "probe", "frac": 0.5, "rule": "coverage", "cond": None}, {"kind": "confirm", "frac": 0.5}],
            "f": {"type": "ridge", "inter": [], "lam": 3.0}}


def n_entries(spec: dict) -> int:
    return sum(int(c["k"]) if c["t"] == "latent" else 1 for c in spec["phi"])


def complexity(spec: dict) -> int:
    inter = len(spec["f"].get("inter", []))
    stages = sum(1 for s in spec["Q"] if s["kind"] == "probe") + sum(1 for s in spec["Q"] if s.get("cond"))
    return n_entries(spec) + inter + stages


def validate_spec(spec, static: Static | None = None, allow_baseline_rules: bool = False) -> list:
    """Return a list of violations (empty when the spec is inside the declared grammar). Unknown keys are rejected."""
    errors = []
    if not isinstance(spec, dict) or set(spec) != {"phi", "Q", "f"}:
        return ["spec must be an object with exactly the keys phi, Q, f"]
    phi, Q, f = spec["phi"], spec["Q"], spec["f"]
    if not isinstance(phi, list) or not phi or not isinstance(Q, list) or not Q or not isinstance(f, dict):
        return ["phi and Q must be non-empty lists and f an object"]
    seen = set()
    for c in phi:
        if not isinstance(c, dict) or c.get("t") not in COORD_TYPES:
            errors.append(f"bad coordinate {c!r}")
            continue
        allowed = {"global": {"t"}, "class": {"t", "a", "b"}, "drug": {"t", "d"}, "latent": {"t", "k"}}[c["t"]]
        if set(c) != allowed:
            errors.append(f"coordinate keys {sorted(c)} not allowed for {c['t']}")
            continue
        key = json.dumps(c, sort_keys=True)
        if key in seen:
            errors.append(f"duplicate coordinate {key}")
        seen.add(key)
        if c["t"] == "latent" and not (isinstance(c["k"], int) and 1 <= c["k"] <= LIMITS["max_latent"]):
            errors.append("latent k out of range")
        if static is not None and c["t"] == "class" and not (isinstance(c["a"], int) and isinstance(c["b"], int) and (c["a"], c["b"]) in static.classes):
            errors.append("class coordinate not a known (a<=b) module class")
        if static is not None and c["t"] == "drug" and not (isinstance(c["d"], int) and 0 <= c["d"] < static.n_drugs):
            errors.append("drug coordinate out of range")
    if sum(1 for c in phi if c["t"] == "latent") > 1:
        errors.append("at most one latent coordinate block")
    if errors:
        return errors
    if n_entries(spec) > LIMITS["max_entries"]:
        errors.append("too many state entries")
    kinds = [s.get("kind") for s in Q if isinstance(s, dict)]
    if len(Q) > LIMITS["max_stages"] or any(k not in ("probe", "confirm") for k in kinds) or "probe" not in kinds:
        errors.append("Q needs 1..3 stages of kind probe/confirm with at least one probe")
    if kinds.count("confirm") > 1 or (kinds.count("confirm") == 1 and kinds[-1] != "confirm"):
        errors.append("at most one confirm stage and it must be last")
    total = 0.0
    rules = PROBE_RULES + (BASELINE_ONLY_RULES if allow_baseline_rules else ())
    for s in Q:
        if not isinstance(s, dict) or not isinstance(s.get("frac"), (int, float)) or not 0 < s["frac"] <= 1:
            errors.append("stage frac must be in (0, 1]")
            continue
        total += float(s["frac"])
        if s["kind"] == "probe":
            if set(s) != {"kind", "frac", "rule", "cond"} or s["rule"] not in rules:
                errors.append(f"bad probe stage {s!r}")
                continue
            cond = s["cond"]
            if cond is not None:
                if not isinstance(cond, dict) or set(cond) != {"coord", "thr", "else"} or cond.get("else") not in rules + ("confirm",):
                    errors.append(f"bad condition {cond!r}")
                elif not (isinstance(cond["coord"], int) and 0 <= cond["coord"] < n_entries(spec)):
                    errors.append("condition coordinate index out of range")
        elif set(s) != {"kind", "frac"}:
            errors.append(f"bad confirm stage {s!r}")
    if abs(total - 1.0) > 1e-9:
        errors.append("stage fractions must sum to 1")
    if set(f) != {"type", "inter", "lam"} or f["type"] not in ("ridge", "gbm") or not isinstance(f["inter"], list) or any(i not in INTERACTIONS for i in f["inter"]) \
            or not isinstance(f["lam"], (int, float)) or not 0.01 <= f["lam"] <= 1000:
        errors.append("bad response model f")
    if not errors and complexity(spec) > LIMITS["max_complexity"]:
        errors.append("program complexity above the declared limit")
    return errors


def canonical(spec: dict) -> str:
    s = copy.deepcopy(spec)
    s["phi"] = sorted(s["phi"], key=lambda c: json.dumps(c, sort_keys=True))
    s["f"]["inter"] = sorted(s["f"]["inter"])
    return json.dumps(s, sort_keys=True)


def entries_of(spec: dict) -> list:
    out = []
    for c in spec["phi"]:
        if c["t"] == "latent":
            out.extend({"t": "latent", "j": j} for j in range(int(c["k"])))
        else:
            out.append(dict(c))
    return out


# --------------------------------------------------------------------------- prior (cell-independent history statistics)
@dataclass
class Prior:
    pm: np.ndarray
    w: np.ndarray
    fbar: np.ndarray
    pv: np.ndarray
    V: np.ndarray
    lam_z: float
    n_cells: int

    def z1(self, Aref, amin, amax):
        F = np.stack([Aref, amin, amax], -1)
        return self.pm + (F - self.fbar) @ self.w

    def as_json(self):
        return {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in self.__dict__.items()}

    @classmethod
    def from_json(cls, d):
        return cls(**{k: (np.array(v) if isinstance(v, list) else v) for k, v in d.items()})


def fit_prior(hist: History, excl: int | None = None) -> Prior:
    keep = [k for k in range(len(hist.cells)) if k != excl]
    R = hist.R[:, keep]
    pm = R.mean(1)
    F = np.stack([hist.Aref[:, keep], hist.amin[:, keep], hist.amax[:, keep]], -1)
    fbar = F.mean(1)
    dF = (F - fbar[:, None, :]).reshape(-1, 3)
    dR = (R - pm[:, None]).reshape(-1)
    w = np.linalg.solve(dF.T @ dF + 1.0 * np.eye(3), dF.T @ dR)
    E1 = (R - pm[:, None]) - ((F - fbar[:, None, :]) @ w)
    U, s, _ = np.linalg.svd(E1, full_matrices=False)
    V = U[:, :K_MAX] * s[:K_MAX] / np.sqrt(len(keep))
    explained = (s[:K_MAX] ** 2).sum() / max((s ** 2).sum(), 1e-12)
    lam_z = float(max(1e-6, (1.0 - explained) * (E1 ** 2).mean()))
    return Prior(pm, w, fbar, E1.var(1), V, lam_z, len(keep))


class HistoryCache:
    """Leave-one-cell-out priors computed once per released history and shared by every program."""

    def __init__(self, hist: History):
        self.hist = hist
        self.full = fit_prior(hist)
        self.loo = [fit_prior(hist, h) for h in range(len(hist.cells))]


# --------------------------------------------------------------------------- state and features
def state_vector(entries, prior: Prior, static: Static, probed, e_obs):
    """phi: observed residuals at probed pairs -> state entries z (shrunk means; latent by ridge). Unknown scope -> 0."""
    z = np.zeros(len(entries))
    probed = np.asarray(probed, dtype=int)
    e = np.asarray(e_obs, dtype=float)
    if len(probed) == 0:
        return z
    k_lat = max([ent["j"] + 1 for ent in entries if ent["t"] == "latent"], default=0)
    if k_lat:
        Vp = prior.V[probed, :k_lat]
        zl = np.linalg.solve(Vp.T @ Vp + prior.lam_z * np.eye(k_lat), Vp.T @ e)
    pc = static.pair_class
    classes = static.classes
    for t, ent in enumerate(entries):
        if ent["t"] == "global":
            z[t] = e.sum() / (len(e) + 1.0)
        elif ent["t"] == "class":
            m = pc[probed] == classes.index((ent["a"], ent["b"]))
            z[t] = e[m].sum() / (m.sum() + 1.0)
        elif ent["t"] == "drug":
            m = (static.pair_i[probed] == ent["d"]) | (static.pair_j[probed] == ent["d"])
            z[t] = e[m].sum() / (m.sum() + 1.0)
        else:
            z[t] = zl[ent["j"]]
    return z


def scope_features(entries, prior: Prior, static: Static):
    """For each state entry, the pair-level scope features (matrix [n, s_t]) that gate where it transfers."""
    n = static.n
    pc = static.pair_class
    classes = static.classes
    out = []
    for ent in entries:
        if ent["t"] == "global":
            out.append(np.ones((n, 1)))
        elif ent["t"] == "class":
            out.append((pc == classes.index((ent["a"], ent["b"]))).astype(float)[:, None])
        elif ent["t"] == "drug":
            out.append(((static.pair_i == ent["d"]) | (static.pair_j == ent["d"])).astype(float)[:, None])
        else:
            out.append(prior.V[:, ent["j"]:ent["j"] + 1])
    return out


def feature_matrix(spec, entries, z, prior, static, Aref_c, anchor_scale):
    """f's design matrix [n, F] for state z in a cell with anchors Aref_c."""
    n = static.n
    scopes = scope_features(entries, prior, static)
    cols = []
    onehot = np.eye(len(static.classes))[static.pair_class]
    anchor = ((Aref_c - anchor_scale[0]) / anchor_scale[1])[:, None]
    for t, S in enumerate(scopes):
        cols.append(S * z[t])
        if "class" in spec["f"]["inter"]:
            cols.append(onehot * z[t])
        if "anchor" in spec["f"]["inter"]:
            cols.append(anchor * z[t])
    if "product" in spec["f"]["inter"]:
        for a in range(len(entries)):
            for b in range(a + 1, min(len(entries), a + 3)):
                cols.append(np.full((n, 1), z[a] * z[b]))
    return np.hstack(cols)


def gbm_matrix(entries, z, prior, static, Aref_c, amin, amax, z1):
    base = np.column_stack([prior.pm, prior.pv, z1, Aref_c, amin, amax])
    zz = np.tile(z, (static.n, 1))
    return np.hstack([base, zz, static.pair_class[:, None], static.pair_i[:, None], static.pair_j[:, None]])


# --------------------------------------------------------------------------- measurement rules
def _farthest_first(F, avail, n, start):
    chosen = [start]
    d = np.linalg.norm(F - F[start], axis=1)
    d[~avail] = -1
    d[chosen] = -1
    while len(chosen) < n:
        nxt = int(np.argmax(d))
        chosen.append(nxt)
        d = np.minimum(d, np.linalg.norm(F - F[nxt], axis=1))
        d[~avail] = -1
        d[chosen] = -1
    return chosen


def choose(rule, n, avail, env):
    """Pick n legal pairs. `env` carries only visible quantities (prior stats, common anchors, current state)."""
    idx = np.nonzero(avail)[0]
    n = min(int(n), len(idx))
    if n <= 0:
        return []
    pv, pred = env["prior"].pv, env["pred"]
    if rule == "random":
        return [int(p) for p in env["rng"].choice(idx, n, replace=False)]
    if rule == "variance":
        return [int(p) for p in idx[np.lexsort((idx, -pv[idx]))][:n]]
    if rule == "exploit":
        return [int(p) for p in idx[np.lexsort((idx, -pred[idx]))][:n]]
    if rule == "coverage":
        static = env["static"]
        F = np.column_stack([env["prior"].pm / (env["prior"].pm.std() + 1e-9), pv / (pv.std() + 1e-9),
                             pred / (pred.std() + 1e-9), np.eye(len(static.classes))[static.pair_class]])
        start = int(idx[np.argmax(pv[idx])])
        return [int(p) for p in _farthest_first(F, avail, n, start)]
    if rule in ("aoptimal", "bayes_voi"):
        K = max(2, env.get("k_lat", 2))
        V = env["prior"].V[:, :K]
        s2 = env["prior"].lam_z
        Sigma = np.eye(K)
        chosen = []
        M = np.zeros((K, K))
        if rule == "bayes_voi":
            sd = np.sqrt(np.einsum("ik,kl,il->i", V, Sigma, V) + s2)
            thr = np.sort(pred)[::-1][SHORTLIST_K]
            w = np.exp(-0.5 * ((pred - thr) / sd) ** 2)
            M = (V * w[:, None]).T @ V
        else:
            M = np.eye(K)
        for _ in range(n):
            a = V @ Sigma
            gain = np.einsum("ik,kl,il->i", a, M, a) / (np.einsum("ik,ik->i", a, V) + s2)
            gain = np.where(avail, gain, -np.inf)
            gain[chosen] = -np.inf
            p = int(np.argmax(gain))
            chosen.append(p)
            sv = Sigma @ V[p]
            Sigma = Sigma - np.outer(sv, sv) / (V[p] @ sv + s2)
        return chosen
    if rule in ("witness", "focus"):
        scopes = env["scope_sets"] if rule == "witness" else [env["scope_sets"][env["focus"]]]
        order = [list(s[np.lexsort((s, -pv[s]))]) for s in scopes if len(s)]
        chosen = []
        r = 0
        while len(chosen) < n and any(r < len(o) for o in order):
            for o in order:
                for p in o[r:r + 1]:
                    if avail[p] and p not in chosen and len(chosen) < n:
                        chosen.append(int(p))
            r += 1
        rest = [int(p) for p in idx[np.lexsort((idx, -pv[idx]))] if int(p) not in chosen]
        return chosen + rest[: n - len(chosen)]
    raise ValueError(rule)


def transfer_spec(spec: dict) -> dict:
    """Transfer contract: no direct confirmation of targets; a confirm stage's share goes to the last probe stage."""
    s = copy.deepcopy(spec)
    extra = sum(st["frac"] for st in s["Q"] if st["kind"] == "confirm")
    s["Q"] = [st for st in s["Q"] if st["kind"] == "probe"]
    s["Q"][-1]["frac"] = round(s["Q"][-1]["frac"] + extra, 12)
    return s


def stage_sizes(Q, B):
    sizes, used = [], 0
    for k, s in enumerate(Q):
        n = B - used if k == len(Q) - 1 else int(round(s["frac"] * B))
        n = max(0, min(n, B - used))
        sizes.append(n)
        used += n
    return sizes


def scope_sets_of(entries, prior, static):
    sets = []
    pc = static.pair_class
    for ent in entries:
        if ent["t"] == "global":
            sets.append(np.arange(static.n))
        elif ent["t"] == "class":
            sets.append(np.nonzero(pc == static.classes.index((ent["a"], ent["b"])))[0])
        elif ent["t"] == "drug":
            sets.append(np.nonzero((static.pair_i == ent["d"]) | (static.pair_j == ent["d"]))[0])
        else:
            col = np.abs(prior.V[:, ent["j"]])
            sets.append(np.argsort(-col)[: max(10, static.n // 8)])
    return sets


def execute_probes(spec, B, prior, static, anchors, query, avail, rng, zsd=None):
    """Run the probe stages of Q. `query(pairs)` returns recorded activity. Returns probed, residuals, z, stage log."""
    entries = entries_of(spec)
    Aref_c, amin_c, amax_c = anchors
    z1 = prior.z1(Aref_c, amin_c, amax_c)
    pred = Aref_c + z1
    sizes = stage_sizes(spec["Q"], B)
    probed, e_obs, log = [], [], []
    avail = avail.copy()
    k_lat = max([e["j"] + 1 for e in entries if e["t"] == "latent"], default=0)
    scopes = scope_sets_of(entries, prior, static)
    z = np.zeros(len(entries))
    for stage, n in zip(spec["Q"], sizes):
        if stage["kind"] != "probe":
            continue
        rule, focus = stage["rule"], 0
        cond = stage.get("cond")
        if cond is not None and probed:
            sd = zsd[cond["coord"]] if zsd is not None and zsd[cond["coord"]] > 0 else 1.0
            if abs(z[cond["coord"]]) / sd > cond["thr"]:
                rule, focus = "focus", cond["coord"]
            else:
                rule = cond["else"]
        if rule == "confirm":
            log.append({"stage": "probe->confirm (adaptive)", "n": n})
            continue
        env = {"prior": prior, "pred": pred, "static": static, "rng": rng, "k_lat": k_lat, "scope_sets": scopes, "focus": focus}
        picks = choose(rule, n, avail, env)
        recorded = query(picks)
        for p in picks:
            avail[p] = False
            probed.append(p)
            e_obs.append(recorded[p] - Aref_c[p] - z1[p])
        z = state_vector(entries, prior, static, probed, e_obs)
        log.append({"stage": rule if focus == 0 or rule != "focus" else f"focus:{focus}", "n": len(picks), "pairs": picks})
    return probed, np.array(e_obs), z, log


# --------------------------------------------------------------------------- fitting
@dataclass
class Fitted:
    spec: dict
    budget: int
    history_version: str
    prior: Prior
    coef: np.ndarray | None
    scale: np.ndarray | None
    anchor_scale: np.ndarray
    zsd: np.ndarray
    sigma_class: np.ndarray
    gbm: object = None
    n_train_rows: int = 0
    train_cells: tuple = ()

    def to_json(self) -> dict:
        if self.gbm is not None:
            raise TypeError("gradient-boosted baselines are not serialisable programs")
        return {"grammar": GRAMMAR_VERSION, "spec": self.spec, "budget": self.budget, "history_version": self.history_version,
                "train_cells": list(self.train_cells), "prior": self.prior.as_json(), "coef": self.coef.tolist(), "scale": self.scale.tolist(),
                "anchor_scale": self.anchor_scale.tolist(), "zsd": self.zsd.tolist(), "sigma_class": self.sigma_class.tolist(),
                "n_train_rows": self.n_train_rows}

    @classmethod
    def from_json(cls, d):
        return cls(d["spec"], d["budget"], d["history_version"], Prior.from_json(d["prior"]), np.array(d["coef"]), np.array(d["scale"]),
                   np.array(d["anchor_scale"]), np.array(d["zsd"]), np.array(d["sigma_class"]), None, d["n_train_rows"], tuple(d["train_cells"]))


def _sim_rows(spec, hist, cache, static, B, seed, legal, zsd, transfer=False):
    entries = entries_of(spec)
    rows_X, rows_y, rows_pc, zs = [], [], [], []
    anchor_all = hist.Aref
    anchor_scale = np.array([anchor_all.mean(), anchor_all.std() + 1e-9])
    gb = spec["f"]["type"] == "gbm"
    for h in range(len(hist.cells)):
        prior = cache.loo[h]
        Aref_c, amin_c, amax_c = hist.Aref[:, h], hist.amin[:, h], hist.amax[:, h]
        truth_R = hist.R[:, h]
        z1 = prior.z1(Aref_c, amin_c, amax_c)

        def query(picks, _R=truth_R, _a=Aref_c):
            return {int(p): float(_a[p] + _R[p]) for p in picks}

        rng = np.random.default_rng(int.from_bytes(hashlib.sha256(f"{seed}|{h}|{canonical(spec)}".encode()).digest()[:8], "little"))
        probed, e_obs, z, _ = execute_probes(spec, B, prior, static, (Aref_c, amin_c, amax_c), query, legal.copy(), rng, zsd)
        zs.append(z)
        keep = ~legal if transfer else np.ones(static.n, bool)      # transfer: f is trained on target-side pairs only
        keep[probed] = False
        if gb:
            X = gbm_matrix(entries, z, prior, static, Aref_c, amin_c, amax_c, z1)
        else:
            X = feature_matrix(spec, entries, z, prior, static, Aref_c, anchor_scale)
        rows_X.append(X[keep])
        rows_y.append((truth_R - z1)[keep])
        rows_pc.append(static.pair_class[keep])
    return np.vstack(rows_X), np.concatenate(rows_y), np.concatenate(rows_pc), np.array(zs), anchor_scale


def fit_program(spec: dict, hist: History, cache: HistoryCache, static: Static, B: int, seed: int = 0, *, transfer: bool = False, probe_mask=None) -> Fitted:
    errors = validate_spec(spec, static, allow_baseline_rules=True)
    if errors:
        raise ValueError("; ".join(errors))
    sim_spec = transfer_spec(spec) if transfer else spec
    legal = np.ones(static.n, bool) if probe_mask is None else probe_mask
    has_cond = any(s.get("cond") for s in spec["Q"])
    zsd = np.ones(n_entries(spec))
    if has_cond:                                   # pass 1: scale of the state coordinates under the unconditional plan
        _, _, _, zs0, _ = _sim_rows(sim_spec, hist, cache, static, B, seed, legal, None, transfer)
        zsd = zs0.std(0) + 1e-9
    X, y, pc, zs, anchor_scale = _sim_rows(sim_spec, hist, cache, static, B, seed, legal, zsd, transfer)
    zsd = zs.std(0) + 1e-9 if not has_cond else zsd
    if spec["f"]["type"] == "gbm":
        from sklearn.ensemble import HistGradientBoostingRegressor
        model = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.08, max_iter=120, l2_regularization=1.0, min_samples_leaf=30,
                                              categorical_features=[X.shape[1] - 3, X.shape[1] - 2, X.shape[1] - 1], random_state=0, early_stopping=False)
        model.fit(X, y)
        pred = model.predict(X)
        coef = scale = None
    else:
        scale = X.std(0)
        scale[scale < 1e-12] = 1.0
        Xs = X / scale
        lam = float(spec["f"]["lam"]) * len(y) / 1000.0
        coef = np.linalg.solve(Xs.T @ Xs + lam * np.eye(Xs.shape[1]), Xs.T @ y)
        pred = Xs @ coef
        model = None
    res = y - pred
    sigma = np.array([res[pc == c].std() if (pc == c).sum() > 3 else res.std() for c in range(len(static.classes))])
    return Fitted(copy.deepcopy(sim_spec), B, hist.version, cache.full, coef, scale, anchor_scale, zsd, sigma, model, len(y), tuple(hist.cells))


# --------------------------------------------------------------------------- execution on a campaign
def predict_state(fit: Fitted, static: Static, anchors, z):
    Aref_c, amin_c, amax_c = anchors
    prior = fit.prior
    z1 = prior.z1(Aref_c, amin_c, amax_c)
    entries = entries_of(fit.spec)
    if fit.gbm is not None:
        e_hat = fit.gbm.predict(gbm_matrix(entries, z, prior, static, Aref_c, amin_c, amax_c, z1))
    else:
        X = feature_matrix(fit.spec, entries, z, prior, static, Aref_c, fit.anchor_scale)
        e_hat = (X / fit.scale) @ fit.coef
    return Aref_c + z1 + e_hat, z1, e_hat


def run_program(fit: Fitted, static: Static, campaign: Campaign, rng, *, pool_mask=None, transfer: bool = False) -> dict:
    """Execute Q, phi, f on a campaign. Transfer mode: probes only from campaign.probe_mask, nominations from pool_mask,
    and a confirm stage is spent as extra probes (no direct confirmation of targets)."""
    spec = transfer_spec(fit.spec) if transfer else copy.deepcopy(fit.spec)
    B = campaign.budget
    anchors = (campaign.Aref, campaign.amin, campaign.amax)
    pool = np.ones(static.n, bool) if pool_mask is None else pool_mask
    legal = np.ones(static.n, bool) if campaign.probe_mask is None else campaign.probe_mask.copy()
    entries = entries_of(spec)
    prior = fit.prior
    z1 = prior.z1(*anchors)
    pred0 = anchors[0] + z1

    def query(picks):
        return campaign.query(picks, stage="probe")

    probed, e_obs, z, log = execute_probes(spec, B, prior, static, anchors, query, legal, rng, fit.zsd)
    pred, _, e_hat = predict_state(fit, static, anchors, z)
    confirm_n = 0
    stages = spec["Q"]
    if not transfer and stages[-1]["kind"] == "confirm":
        confirm_n = campaign.left
        avail = np.array([p not in campaign.queried for p in range(static.n)]) & pool
        conf = choose("exploit", confirm_n, avail, {"prior": prior, "pred": pred})
        if conf:
            campaign.query(conf, stage="confirm")
    elif not transfer and campaign.left > 0:                     # adaptive conversion of unspent probe budget into confirmation
        avail = np.array([p not in campaign.queried for p in range(static.n)]) & pool
        conf = choose("exploit", campaign.left, avail, {"prior": prior, "pred": pred})
        if conf:
            campaign.query(conf, stage="confirm")
    score = pred.copy()
    for p, v in campaign.queried.items():
        score[p] = v                                              # recorded outcomes replace predictions (no imputation)
    nominated = shortlist(score, pool, SHORTLIST_K)
    return {"nominated": [int(p) for p in nominated], "z": z.tolist(), "prior_prediction": pred0, "final_prediction": pred,
            "probed": [int(p) for p in probed], "stage_log": log, "spent": campaign.spent}


def baseline_direct(prior: Prior, static: Static, campaign: Campaign, pool_mask=None) -> dict:
    """Direct confirmation: spend the whole budget on the top prior-predicted candidates, nominate the best recorded."""
    anchors = (campaign.Aref, campaign.amin, campaign.amax)
    pool = np.ones(static.n, bool) if pool_mask is None else pool_mask
    pred = anchors[0] + prior.z1(*anchors)
    avail = np.array([p not in campaign.queried for p in range(static.n)]) & pool
    picks = choose("exploit", campaign.budget, avail, {"prior": prior, "pred": pred})
    campaign.query(picks, stage="confirm")
    score = pred.copy()
    for p, v in campaign.queried.items():
        score[p] = v
    return {"nominated": [int(p) for p in shortlist(score, pool, SHORTLIST_K)], "spent": campaign.spent, "final_prediction": pred, "probed": [], "z": []}


def baseline_zero(prior: Prior, static: Static, campaign: Campaign, pool_mask=None) -> dict:
    anchors = (campaign.Aref, campaign.amin, campaign.amax)
    pool = np.ones(static.n, bool) if pool_mask is None else pool_mask
    pred = anchors[0] + prior.z1(*anchors)
    return {"nominated": [int(p) for p in shortlist(pred, pool, SHORTLIST_K)], "spent": 0, "final_prediction": pred, "probed": [], "z": []}
