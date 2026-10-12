"""Block Q decision layer: equal-budget profiling campaigns that complete a compound x line map.

A campaign has a library of compounds with no prior profile, a grid of (compound, line) cells that
can be profiled at one well each, a reference atlas, and a well budget W. Arms decide which cells
to profile; every unprofiled cell is then filled by the arm's predictor. The registered utility is
the mean, over truly active grid cells, of the final entry's centred cosine with the observed
response, a profiled cell counting 1.

Deterministic arms (the LLM arms are in ``llm_arms.py``):
* ``zero``: no wells, every entry predicts no change (centred cosine 0).
* ``generic``: no wells, every entry the line's generic active direction.
* ``vc_only``: no wells, RKT predictions.
* ``dense``: W // L random compounds profiled in all their lines (PRESAGE's exhaustive design).
* ``sparse_random``: random cells, at most one per compound per pass (PRESAGE's sparse design).
* ``sparse_hub``: each compound in random order profiled in its best "hub" line (highest mean
  outgoing specific transfer), the transfer-informed fixed design.
* ``ad_uncertainty``: four rounds of uncertainty sampling by applicability distance (route-blind).
* ``activity_greedy``: four rounds, highest certified P(active).
* ``maestro``: four rounds of certificate value of information (direct gain plus expected transfer
  gain to the compound's other lines), batches chosen by sequential greedy with in-batch updates.
* ``maestro_static``: the same value of information spent in one round (fixed-design turnaround).
* ``oracle``: four rounds by realised loss on active cells (an outcome-aware reference, not a policy).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

import engine
import rkt
from pool import perp

ROUNDS = 4
DETERMINISTIC_ARMS = ("zero", "generic", "vc_only", "dense", "sparse_random", "sparse_hub",
                      "ad_uncertainty", "activity_greedy", "maestro", "maestro_static", "oracle")


def seed_of(*parts) -> int:
    return int(hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest(), 16) % (2 ** 32)


def transfer_specific(atlas: rkt.Atlas, maps: dict, G: np.ndarray, thr: np.ndarray) -> np.ndarray:
    """kappa[s, t]: mean specific cosine of leave-one-out single-line transfer s -> t on active references."""
    L = atlas.Yc.shape[1]
    kappa = np.zeros((L, L))
    have = np.isfinite(atlas.Yc[..., 0]) & atlas.ref[:, None]
    for (s, t), m in maps.items():
        rows = have[:, s] & have[:, t]
        X = atlas.Yc[rows, s].astype(np.float64); Z = atlas.Yc[rows, t].astype(np.float64)
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        d = S ** 2 / (S ** 2 + m.lam)
        Zhat = U @ (d[:, None] * (U.T @ Z))
        H = (U ** 2 * d).sum(1)
        loo = Z - (Z - Zhat) / np.maximum(1 - H, 1e-6)[:, None]
        act = np.linalg.norm(Z + atlas.mu[t], axis=1) > thr[t]
        if act.sum() >= 5:
            Gt = np.repeat(G[t][None], int(act.sum()), 0)
            kappa[s, t] = float(np.mean(rkt.centred_cosine(perp(loo[act], Gt), perp(Z[act], Gt))))
    return kappa


@dataclass
class Campaign:
    cid: str
    atlas: rkt.Atlas
    maps: dict
    pooler: object
    G: np.ndarray
    gamma: float
    thr: np.ndarray
    library: np.ndarray          # atlas row indices of the library compounds
    grid: np.ndarray             # n_lib x L boolean: profileable cells
    kappa: np.ndarray
    cache: dict = field(default_factory=dict)

    @property
    def L(self):
        return self.atlas.Yc.shape[1]

    def truth_active(self) -> np.ndarray:
        raw = np.linalg.norm(np.nan_to_num(self.atlas.Yc[self.library] + self.atlas.mu[None]), axis=2)
        return self.grid & (raw > self.thr[None])

    def static_routes(self, T: int, rows: np.ndarray) -> dict:
        """Visibility-independent routes (structure, knowledge) for library rows, computed once per line."""
        if T not in self.cache:
            self.cache[T] = {"chem": rkt.route_chem(self.atlas, self.library, T),
                             "know": rkt.route_know(self.atlas, self.library, T)}
        return {r: engine.slice_route(o, rows) for r, o in self.cache[T].items()}

    def vc_state(self, measured: np.ndarray):
        """Certified predictions for every unmeasured grid cell, given the measured cells."""
        n, L = self.grid.shape
        out = {"dir": np.zeros((n, L, self.atlas.Yc.shape[2])), "p": np.zeros((n, L)), "rho": np.zeros((n, L)),
               "ecos": np.zeros((n, L)), "topsim": np.zeros((n, L)), "refusal": np.full((n, L), "", "<U40")}
        for T in range(L):
            rows = np.flatnonzero(self.grid[:, T] & ~measured[:, T])
            if not len(rows):
                continue
            q = self.library[rows]
            blk = engine.query_block(self.atlas, q, T, measured[rows], self.maps, self.thr,
                                     static=self.static_routes(T, rows))
            direction, s, cert, ecos = engine.predict_block(blk, self.pooler, self.G, self.gamma)
            out["dir"][rows, T] = direction; out["p"][rows, T] = cert.p_active; out["rho"][rows, T] = np.where(cert.refusal == "", cert.rho, 0)
            out["ecos"][rows, T] = ecos; out["refusal"][rows, T] = cert.refusal
            sims = [np.where(blk.routes[r].available, blk.routes[r].support[:, 0], 0) for r in ("pheno", "chem", "know")]
            out["topsim"][rows, T] = np.max(np.stack(sims, 1), 1)
        return out

    def score(self, measured: np.ndarray, entries: np.ndarray) -> dict:
        """Registered utility and secondaries for a final map (entries: n x L x p unit or zero)."""
        act = self.truth_active()
        truth = self.atlas.Yc[self.library]
        cos = rkt.centred_cosine(entries.reshape(-1, entries.shape[2]), np.nan_to_num(truth).reshape(-1, truth.shape[2])).reshape(act.shape)
        credit = np.where(measured, 1.0, cos)
        a = act
        return {"utility": float(credit[a].mean()) if a.any() else float("nan"),
                "usable": float((credit[a] >= 0.5).mean()) if a.any() else float("nan"),
                "n_active": int(a.sum()), "wells": int(measured.sum())}


def _take(scores: np.ndarray, measured: np.ndarray, grid: np.ndarray, k: int, *, one_per_compound: bool, rng) -> np.ndarray:
    cand = grid & ~measured
    s = np.where(cand, scores + 1e-9 * rng.random(scores.shape), -np.inf)
    chosen = np.zeros_like(measured)
    order = np.argsort(-s, axis=None)
    used = set()
    for flat in order:
        if chosen.sum() >= k or not np.isfinite(s.flat[flat]):
            break
        i, t = np.unravel_index(flat, s.shape)
        if one_per_compound and i in used:
            continue
        chosen[i, t] = True
        used.add(i)
    if chosen.sum() < k and one_per_compound:  # fill any shortfall without the per-compound limit
        rest = np.where(chosen, -np.inf, s)
        for flat in np.argsort(-rest, axis=None)[: k - int(chosen.sum())]:
            if np.isfinite(rest.flat[flat]):
                chosen[np.unravel_index(flat, s.shape)] = True
    return chosen


def hub_order(kappa: np.ndarray) -> np.ndarray:
    return np.argsort(-kappa.mean(axis=1))


def run_arm(c: Campaign, arm: str, W: int) -> dict:
    rng = np.random.default_rng(seed_of(c.cid, arm, W))
    n, L = c.grid.shape
    measured = np.zeros((n, L), bool)
    rounds = 0
    if arm in ("zero", "generic", "vc_only"):
        pass
    elif arm == "dense":
        per = max(1, W // L)
        for i in rng.permutation(n):
            if measured.sum() >= W:
                break
            cells = np.flatnonzero(c.grid[i])
            take = cells[: max(0, min(len(cells), W - int(measured.sum())))]
            measured[i, take] = True
        rounds = 1
    elif arm in ("sparse_random", "sparse_hub"):
        hubs = hub_order(c.kappa)
        while measured.sum() < W and (c.grid & ~measured).any():
            for i in rng.permutation(n):
                if measured.sum() >= W:
                    break
                free = np.flatnonzero(c.grid[i] & ~measured[i])
                if not len(free):
                    continue
                if arm == "sparse_random":
                    t = rng.choice(free)
                else:
                    t = next(h for h in hubs if h in set(free))
                measured[i, t] = True
        rounds = 1
    elif arm == "maestro_static":
        measured |= maestro_batch(c, c.vc_state(measured), measured, W, rng)
        rounds = 1
    else:
        batch = int(np.ceil(W / ROUNDS))
        for r in range(ROUNDS):
            k = min(batch, W - int(measured.sum()))
            if k <= 0:
                break
            if arm == "oracle":
                st = c.vc_state(measured)
                truth = np.nan_to_num(c.atlas.Yc[c.library])
                cos = rkt.centred_cosine(st["dir"].reshape(-1, truth.shape[2]), truth.reshape(-1, truth.shape[2])).reshape(n, L)
                scores = np.where(c.truth_active(), 1 - cos, 0.0)
                pick = _take(scores, measured, c.grid, k, one_per_compound=False, rng=rng)
            else:
                st = c.vc_state(measured)
                if arm == "ad_uncertainty":
                    scores = 1 - st["topsim"]
                    pick = _take(scores, measured, c.grid, k, one_per_compound=True, rng=rng)
                elif arm == "activity_greedy":
                    pick = _take(st["p"], measured, c.grid, k, one_per_compound=False, rng=rng)
                elif arm == "maestro":
                    pick = maestro_batch(c, st, measured, k, rng)
                else:
                    raise ValueError(arm)
            measured |= pick
            rounds += 1
    return finish(c, arm, measured, rounds)


def maestro_value(c: Campaign, st: dict, measured: np.ndarray) -> np.ndarray:
    """Expected utility gain of profiling each cell: its own gain plus transfer to the compound's other lines."""
    g2 = c.gamma ** 2
    p, ecos, rho = st["p"], st["ecos"], st["rho"]
    open_ = c.grid & ~measured
    direct = p * (1 - ecos)
    n, L = c.grid.shape
    transfer = np.zeros((n, L))
    for t in range(L):
        rho_after = np.maximum(rho, c.kappa[t][None, :])          # profiling line t opens t -> t' transfer
        e_after = np.sqrt(g2 + rho_after ** 2 * (1 - g2))
        gain = np.where(open_, p * np.clip(e_after - ecos, 0, None), 0.0)
        gain[:, t] = 0.0
        transfer[:, t] = gain.sum(1)
    return np.where(open_, direct + transfer, -np.inf)


def maestro_batch(c: Campaign, st: dict, measured: np.ndarray, k: int, rng) -> np.ndarray:
    """Sequential greedy batch: after each pick, the compound's expected accuracies are updated as if
    the picked line were profiled, so a batch does not double-count one compound's transfer gain."""
    g2 = c.gamma ** 2
    rho = st["rho"].copy()
    ecos = st["ecos"].copy()
    m = measured.copy()
    chosen = np.zeros_like(measured)
    jitter = 1e-9 * rng.random(measured.shape)
    for _ in range(k):
        v = maestro_value(c, {"p": st["p"], "ecos": ecos, "rho": rho}, m) + jitter
        if not np.isfinite(v).any():
            break
        i, t = np.unravel_index(int(np.argmax(v)), v.shape)
        chosen[i, t] = m[i, t] = True
        rho[i] = np.maximum(rho[i], c.kappa[t])
        ecos[i] = np.maximum(ecos[i], np.sqrt(g2 + rho[i] ** 2 * (1 - g2)))
    return chosen


def naive_fill(c: Campaign, measured: np.ndarray) -> np.ndarray:
    """Fill without a virtual cell: the mean of the compound's profiles in lines where it was active,
    otherwise the line's generic direction (what a laboratory would assume with no model)."""
    n, L = c.grid.shape
    Yl = np.nan_to_num(c.atlas.Yc[c.library]).astype(np.float64)
    raw = np.linalg.norm(np.nan_to_num(c.atlas.Yc[c.library] + c.atlas.mu[None]), axis=2)
    act_seen = measured & (raw > c.thr[None])
    entries = np.repeat(c.G[None], n, 0).astype(np.float64)
    for i in np.flatnonzero(act_seen.any(1)):
        entries[i] = rkt.unit_rows(Yl[i, act_seen[i]].mean(0))[None]
    return entries


def finish(c: Campaign, arm: str, measured: np.ndarray, rounds: int, *, fill: str = "vc") -> dict:
    """Score the arm's own map, plus the same profiled cells under the VC and the naive fill."""
    n, L = c.grid.shape
    p = c.atlas.Yc.shape[2]
    vc_entries = c.vc_state(measured)["dir"]
    naive = naive_fill(c, measured)
    if arm == "zero":
        entries = np.zeros((n, L, p))
    elif arm == "generic":
        entries = np.repeat(c.G[None], n, 0)
    else:
        entries = vc_entries if fill == "vc" else naive
    out = c.score(measured, entries)
    out.update({"arm": arm, "rounds": rounds, "fill": fill,
                "utility_vcfill": c.score(measured, vc_entries)["utility"],
                "utility_naivefill": c.score(measured, naive)["utility"]})
    return out
