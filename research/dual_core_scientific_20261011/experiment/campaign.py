"""Reference-only empirical world model and truthful, budgeted replay environment.

No policy has direct access to query viability arrays. The measured-data environment
owns outcomes and the policy receives only public availability and paid readouts.
This module calls no LLM and does not model causal mechanism or intervention timing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.special import ndtri

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
SEED = PROTOCOL["seed"]
BUDGETS = PROTOCOL["geometry"]["budgets"]
NODES = ndtri((np.arange(PROTOCOL["algorithm"]["quadrature_nodes"]) + 0.5)
              / PROTOCOL["algorithm"]["quadrature_nodes"])
TOP_K = 10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources() -> None:
    receipt = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in receipt["sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"SOURCE_DIGEST_MISMATCH: {relative}")


def project_rows(values: np.ndarray, basis: np.ndarray) -> np.ndarray:
    """Project complete rows off the fixed generic-sensitivity nuisance basis."""
    return values - (values @ basis) @ np.linalg.pinv(basis.T @ basis) @ basis.T


def observed_residual(values: np.ndarray, basis: np.ndarray) -> np.ndarray:
    out = np.full(len(values), np.nan)
    ok = np.isfinite(values)
    if ok.sum() >= 3:
        b = basis[ok]
        out[ok] = values[ok] - b @ np.linalg.lstsq(b, values[ok], rcond=None)[0]
    return out


def mean_top_utility(mean: np.ndarray) -> float:
    return float(-np.partition(mean, TOP_K - 1)[:TOP_K].mean())


def knowledge_gradient(mean: np.ndarray, cross: np.ndarray, variance: np.ndarray) -> np.ndarray:
    """Gaussian-moment EVSI for a terminal top-k utility, using fixed quadrature."""
    shifts = cross / np.sqrt(np.maximum(variance, 1e-12))[None, :]
    hypothetical = mean[None, None, :] + NODES[None, :, None] * shifts.T[:, None, :]
    utility = -np.partition(hypothetical, TOP_K - 1, axis=-1)[..., :TOP_K].mean(axis=-1)
    return utility.mean(axis=1) - mean_top_utility(mean)


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 30 or np.std(a[ok]) < 1e-12 or np.std(b[ok]) < 1e-12:
        return 0.0
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


@dataclass(frozen=True)
class QueryInput:
    drug: str
    moa: str
    role: str
    signature: np.ndarray
    have: np.ndarray
    menu: np.ndarray
    targets: np.ndarray


@dataclass
class Library:
    drug: np.ndarray
    moa: np.ndarray
    profiles: np.ndarray
    residuals: np.ndarray
    coefficients: np.ndarray
    signature: np.ndarray
    have: np.ndarray
    basis: np.ndarray
    lines: np.ndarray
    discovery: np.ndarray
    targets: np.ndarray
    panel: np.ndarray
    similarity_cache: dict = field(default_factory=dict, repr=False)

    def pool(self, query: QueryInput) -> np.ndarray:
        return np.where((self.drug != query.drug) & (self.moa != query.moa))[0]

    def similarity(self, query: QueryInput, pool: np.ndarray) -> np.ndarray:
        cache_key = (query.drug, id(query.signature), query.moa)
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        q = np.nan_to_num(query.signature)
        r = np.nan_to_num(self.signature[pool])
        norm = np.linalg.norm(r, axis=2) * np.linalg.norm(q, axis=1)[None, :]
        ok = self.have[pool] & query.have[None, :] & (norm > 0)
        cos = np.einsum("pog,og->po", r, q) / np.maximum(norm, 1e-12)
        total = np.where(ok, cos, 0).sum(axis=1)
        result = np.divide(total, ok.sum(axis=1), out=np.full(len(pool), np.nan), where=ok.sum(axis=1) > 0)
        self.similarity_cache[cache_key] = result
        return result

    def initial_weights(self, query: QueryInput, pool: np.ndarray, tau: float, use_l1000: bool) -> np.ndarray:
        if not use_l1000:
            return np.full(len(pool), 1 / len(pool))
        sim = self.similarity(query, pool)
        finite = np.isfinite(sim)
        if not finite.any():
            return np.full(len(pool), 1 / len(pool))
        sim = np.where(finite, sim, sim[finite].min())
        w = np.exp((sim - sim.max()) / tau)
        w /= w.sum()
        floor = PROTOCOL["algorithm"]["prior_floor_fraction"]
        return (1 - floor) * w + floor / len(w)

    def nuisance(self, pool: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        coef = self.coefficients[pool]
        floor = PROTOCOL["algorithm"]["nuisance_covariance_floor"]
        return coef.mean(axis=0), np.cov(coef.T) + floor * np.eye(2)

    def transfer(self, query: QueryInput) -> np.ndarray:
        pool = self.pool(query)
        sim = self.similarity(query, pool)
        idx = np.argsort(-np.where(np.isfinite(sim), sim, -np.inf), kind="stable")[:5]
        weight = np.maximum(np.nan_to_num(sim[idx]), 0)
        if weight.sum() <= 0:
            weight = np.ones(len(idx))
        return weight @ project_rows(self.residuals[pool[idx]][:, query.targets], self.basis[query.targets]) / weight.sum()


class MeasuredEnvironment:
    """Only this object owns query truth; actions reveal recorded, purchased values."""

    def __init__(self, library: Library, query: QueryInput, primary: np.ndarray,
                 secondary: np.ndarray, feedback_shuffle: bool = False):
        self.library = library
        self.query = query
        self._primary = primary.copy()
        self._secondary = secondary.copy()
        self._feedback = primary.copy()
        if feedback_shuffle:
            seed = SEED + int(hashlib.sha256(query.drug.encode()).hexdigest()[:8], 16)
            perm = np.random.default_rng(seed).permutation(query.menu)
            self._feedback[query.menu] = primary[perm]
        self.purchases: list[dict] = []

    def measure(self, line: int, value: float | None = None) -> float:
        if line not in self.query.menu or line in [p["line"] for p in self.purchases]:
            raise ValueError("INVALID_OR_DUPLICATE_PURCHASE")
        if len(self.purchases) >= max(BUDGETS):
            raise ValueError("BUDGET_EXCEEDED")
        result = float(self._feedback[line])
        self.purchases.append({"line": line, "line_id": str(self.library.lines[line]),
                               "observed": result, "predicted_evsi": value, "cost": 1})
        return result

    def score(self, prediction: np.ndarray) -> tuple[dict, dict]:
        t = self.query.targets
        basis = self.library.basis[t]
        selected = np.argsort(prediction, kind="stable")[:TOP_K]
        truth = observed_residual(self._primary[t], basis)
        hits = set(np.argsort(truth, kind="stable")[:max(1, round(0.1 * len(truth)))])
        score = {"utility": float(-truth[selected].mean()),
                 "precision": float(np.mean([int(i) in hits for i in selected])),
                 "selective_r": pearson(prediction, truth),
                 "n_targets": len(t), "n_selected": TOP_K,
                 "max_error": float(np.max(np.abs(prediction - truth))),
                 "active_query": bool(np.mean(self._primary[np.isfinite(self._primary)] < -1) >= 0.05)}
        s2 = observed_residual(self._secondary[t], basis)
        measured = np.isfinite(s2)
        chosen = selected[measured[selected]]
        score["secondary_n_targets"] = int(measured.sum())
        score["secondary_n_selected"] = len(chosen)
        if measured.sum() >= 50 and len(chosen) >= 5:
            ordered = np.where(measured)[0][np.argsort(s2[measured], kind="stable")]
            hits2 = set(ordered[:max(1, round(0.1 * measured.sum()))])
            score.update(secondary_utility=float(-s2[chosen].mean()),
                         secondary_precision=float(np.mean([int(i) in hits2 for i in chosen])),
                         secondary_r=pearson(prediction, s2))
        else:
            score.update(secondary_utility=None, secondary_precision=None, secondary_r=None)
        ledger = {"selected": [str(self.library.lines[t[j]]) for j in selected],
                  "target_lines": [str(self.library.lines[j]) for j in t],
                  "prediction": prediction.tolist(), "truth": truth.tolist(),
                  "secondary_truth": [None if not np.isfinite(v) else float(v) for v in s2],
                  "purchases": [dict(p) for p in self.purchases]}
        return score, ledger


class ParticlePosterior:
    def __init__(self, library: Library, query: QueryInput, tau: float, sigma: float,
                 use_l1000: bool = True):
        self.library = library
        self.query = query
        self.pool = library.pool(query)
        self.w = library.initial_weights(query, self.pool, tau, use_l1000)
        self.logw = np.log(self.w)
        self.sigma = sigma
        mean, self.nuisance_cov = library.nuisance(self.pool)
        self.nuisance_mean = np.broadcast_to(mean, (len(self.pool), 2)).copy()
        self.R = library.residuals[self.pool]
        self.Rt = project_rows(self.R[:, query.targets], library.basis[query.targets])
        self.Rc = self.R[:, query.menu]
        self.Bc = library.basis[query.menu]
        self.bought: list[int] = []

    def predict(self) -> np.ndarray:
        return self.w @ self.Rt

    def moment_values(self) -> np.ndarray:
        target_mean = self.predict()
        observation = self.Rc + self.nuisance_mean @ self.Bc.T
        observation_mean = self.w @ observation
        centered = observation - observation_mean
        cross = (self.Rt - target_mean).T @ (self.w[:, None] * centered)
        variance = (self.w[:, None] * centered ** 2).sum(axis=0)
        variance += np.einsum("li,ij,lj->l", self.Bc, self.nuisance_cov, self.Bc) + self.sigma ** 2
        gain = knowledge_gradient(target_mean, cross, variance)
        gain[[j for j, line in enumerate(self.query.menu) if int(line) in self.bought]] = -np.inf
        return gain

    def choose(self) -> tuple[int, float]:
        gain = self.moment_values()
        j = int(np.argmax(gain))
        return int(self.query.menu[j]), float(gain[j])

    def observe(self, line: int, outcome: float) -> None:
        b = self.library.basis[line]
        expected = self.R[:, line] + self.nuisance_mean @ b
        cross = self.nuisance_cov @ b
        variance = self.sigma ** 2 + b @ cross
        innovation = outcome - expected
        self.logw -= 0.5 * innovation ** 2 / variance
        self.logw -= self.logw.max()
        self.w = np.exp(self.logw)
        self.w /= self.w.sum()
        self.nuisance_mean += innovation[:, None] * cross[None, :] / variance
        self.nuisance_cov -= np.outer(cross, cross) / variance
        self.bought.append(line)


class GaussianPosterior:
    """Strong cheap local-library GP; batch designs cannot exploit unseen values."""

    def __init__(self, library: Library, query: QueryInput, tau: float, sigma: float):
        self.query = query
        self.sigma = sigma
        self.n_targets = len(query.targets)
        self.cols = np.concatenate([query.targets, query.menu])
        self.position = {int(line): j for j, line in enumerate(self.cols)}
        pool = library.pool(query)
        w = library.initial_weights(query, pool, tau, True)
        R = library.residuals[pool][:, self.cols]
        rm = w @ R
        centered = R - rm
        global_centered = R - R.mean(axis=0)
        theta, nuisance_cov = library.nuisance(pool)
        B = library.basis[self.cols]
        self.mean = rm + B @ theta
        alpha = PROTOCOL["algorithm"]["global_covariance_fraction"]
        self.covariance = centered.T @ (w[:, None] * centered)
        self.covariance += alpha * global_centered.T @ global_centered / max(len(pool) - 1, 1)
        self.covariance += B @ nuisance_cov @ B.T
        Bt = B[:self.n_targets]
        self.target_projector = np.eye(self.n_targets) - Bt @ np.linalg.pinv(Bt.T @ Bt) @ Bt.T
        self.bought: list[int] = []

    def predict(self) -> np.ndarray:
        return self.target_projector @ self.mean[:self.n_targets]

    def values(self, mode: str) -> np.ndarray:
        cross = self.target_projector @ self.covariance[:self.n_targets, self.n_targets:]
        variance = np.diag(self.covariance)[self.n_targets:] + self.sigma ** 2
        if mode == "kg":
            gain = knowledge_gradient(self.predict(), cross, variance)
        else:
            gain = (cross ** 2).sum(axis=0) / np.maximum(variance, 1e-12)
        gain[[j for j, line in enumerate(self.query.menu) if int(line) in self.bought]] = -np.inf
        return gain

    def observe(self, line: int, outcome: float | None) -> None:
        j = self.position[line]
        cross = self.covariance[:, j].copy()
        variance = self.covariance[j, j] + self.sigma ** 2
        if outcome is not None:
            self.mean += cross * (outcome - self.mean[j]) / variance
        self.covariance -= np.outer(cross, cross) / variance
        self.bought.append(line)


def run_policy(library: Library, query: QueryInput, environment: MeasuredEnvironment,
               arm: str, cfg: dict) -> tuple[list[dict], list[dict]]:
    start = time.perf_counter()
    tau, sigma = cfg["tau"], cfg["sigma"]
    rows, ledgers = [], []
    if arm == "source_only":
        prediction = library.transfer(query)
        for budget in BUDGETS:
            score, ledger = environment.score(prediction)
            rows.append(dict(score, arm=arm, budget=budget, spent=0, rounds=0,
                             seconds=time.perf_counter() - start))
            ledgers.append(dict(ledger, budget=budget))
        return rows, ledgers
    gaussian = arm.startswith("batch_gp")
    if gaussian:
        posterior = GaussianPosterior(library, query, tau, sigma)
        designer = GaussianPosterior(library, query, tau, sigma)
        plan, plan_values = [], []
        for _ in range(max(BUDGETS)):
            values = designer.values("ivr" if arm.endswith("ivr") else "kg")
            index = int(np.argmax(values))
            line = int(query.menu[index])
            plan.append(line)
            plan_values.append(float(values[index]))
            designer.observe(line, None)
    else:
        posterior = ParticlePosterior(library, query, tau, sigma, arm != "adaptive_without_l1000")
        plan = list(query.menu) if arm == "fixed_library" else None
        if arm == "random_library":
            seed = SEED + int(hashlib.sha256(query.drug.encode()).hexdigest()[:8], 16)
            plan = list(np.random.default_rng(seed).permutation(query.menu))
    for step in range(1, max(BUDGETS) + 1):
        if gaussian:
            line, value = plan[step - 1], plan_values[step - 1]
        elif plan is not None:
            line, value = int(plan[step - 1]), None
        else:
            line, value = posterior.choose()
        result = environment.measure(line, value)
        posterior.observe(line, result)
        if step in BUDGETS:
            prediction = posterior.predict()
            score, ledger = environment.score(prediction)
            rows.append(dict(score, arm=arm, budget=step, spent=step,
                             rounds=1 if plan is not None else step,
                             seconds=time.perf_counter() - start))
            ledgers.append(dict(ledger, budget=step))
    return rows, ledgers


def load_data() -> tuple[Library, list[tuple[QueryInput, np.ndarray, np.ndarray]]]:
    verify_sources()
    source = ROOT / "data/external/prism_19q4/derived"
    tiers = []
    for tier in ("open", "sealed"):
        with np.load(source / f"block_n_prism_{tier}.npz", allow_pickle=False) as z:
            tiers.append({key: z[key] for key in ("drug", "moa", "role", "line", "primary", "secondary")})
    data = {key: np.concatenate([tier[key] for tier in tiers])
            for key in ("drug", "moa", "role", "primary", "secondary")}
    assert np.array_equal(tiers[0]["line"], tiers[1]["line"])
    drug, moa, role = [data[key].astype(str) for key in ("drug", "moa", "role")]
    ref = np.where(role == "reference")[0]
    assert len(ref) == 701 and len(set(drug)) == len(drug)
    ltiers = []
    for tier in ("open", "sealed"):
        path = ROOT / f"data/external/lincs_l1000_gse92742/derived/block_m_landmark_{tier}.npz"
        with np.load(path, allow_pickle=False) as z:
            ltiers.append({key: z[key] for key in ("drug", "x")})
    position = {str(d): i for i, d in enumerate(np.concatenate([z["drug"] for z in ltiers]))}
    X = np.concatenate([z["x"] for z in ltiers])[[position[d] for d in drug]].astype(float)
    have = np.isfinite(X[..., 0])
    profiles = data["primary"][ref].astype(float)
    generic = np.nanmean(profiles, axis=0)
    g = (generic - generic.mean()) / max(generic.std(), 1e-12)
    basis = np.column_stack([np.ones(len(g)), g])
    coefficients, residuals = [], []
    for p in profiles:
        ok = np.isfinite(p)
        coef = np.linalg.lstsq(basis[ok], p[ok], rcond=None)[0]
        coefficients.append(coef)
        residuals.append(p - basis @ coef)
    R = np.array(residuals)
    line_mean = np.nanmean(R, axis=0)
    R = np.where(np.isfinite(R), R, line_mean[None, :])
    permutation = np.random.default_rng(SEED).permutation(len(g))
    discovery, targets = permutation[:len(g) // 2], permutation[len(g) // 2:]
    candidates = discovery[np.isfinite(profiles[:, discovery]).mean(axis=0) >= 0.9]
    panel = candidates[np.argsort(-np.var(R[:, candidates], axis=0), kind="stable")[:64]]
    if len(panel) < 16:
        raise RuntimeError("INSUFFICIENT_REFERENCE_QUALIFIED_MENU")
    library = Library(drug[ref], moa[ref], profiles, R, np.array(coefficients), X[ref], have[ref],
                      basis, tiers[0]["line"].astype(str), discovery, targets, panel)
    queries = []
    for i in np.where(role != "reference")[0]:
        menu = panel[np.isfinite(data["primary"][i, panel])]
        terminal = targets[np.isfinite(data["primary"][i, targets])]
        if not have[i].any() or len(menu) < 16 or len(terminal) < 50:
            continue
        query = QueryInput(str(drug[i]), str(moa[i]), str(role[i]), X[i], have[i], menu, terminal)
        queries.append((query, data["primary"][i].astype(float), data["secondary"][i].astype(float)))
    return library, queries
