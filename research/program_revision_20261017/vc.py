"""Virtual Cell core: a strong inductive response model plus an editable library of response programs.

File summary
- Path: research/program_revision_20261017/vc.py
- Purpose: predict a drug x line response matrix at 2.5 uM for lines and drugs never seen in
  training, from legal decision-time inputs, and turn predictions into hit probabilities.
- Strong model (`StrongModel`, the inductive multitask baseline):
  - y[d,c] = a_d + b_c + U_d . V_c (rank r), fitted by ridge-weighted alternating least squares
    on observed entries only (no imputation enters the loss).
  - New line: the line state s = [b_c, V_c] has a ridge prior from the purchased line features
    (mean and leave-one-out residual covariance); measured probe readouts update it by Bayesian
    linear regression. New drug: t = [a_d, U_d] has a kernel-ridge prior from fingerprint, MoA
    and target tokens; pooled probe readouts update it the same way.
  - Nothing here substitutes a prediction for a measurement: probes are separate inputs.
- Program library (`Program`, `ProgramLibrary`):
  - A program is (scope over drugs, state over lines). Scope: ``all``, ``moa:<token>`` or
    ``target:<gene>`` (legal for unseen drugs). State: an expression over observable atoms
    ``mut:<gene>`` (DNA panel), ``lin:<tissue>`` (free), ``expr:<gene>`` (marker panel or
    RNA-seq), ``probe:<core>`` (one well), ``b`` (the strong model's posterior line offset), with
    ``and``/``andnot`` for binary atoms and ``mul`` for a continuous atom gated by a binary one.
  - Prediction: y = strong + sum_k 1[d in S_k] B_dk phi_k(c). Loadings are fitted on
    cross-fitted residuals of the strong model, with a hierarchical prior B_dk ~ N(beta_k, tau)
    (beta_k = scope-shared loading). Unseen drugs use beta_k. This is a conditional low-rank /
    mixture-of-experts style correction with explicit observable gates; it is not new by itself.
  - Each program declares its measurement program (`requirements`).
- Scores: `hit_probability` is P(mean(X2,X3) <= min(-1, median_d - 1)) under a Gaussian
  predictive with per-drug cross-fitted residual variance.
- Interfaces: `StrongModel`, `Program`, `ProgramLibrary`, `parse_state`, `hit_probability`,
  `top_k`, `ridge_prior`, `blr`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np
from scipy.special import ndtr


# ---------------------------------------------------------------- linear-Gaussian helpers

def ridge_prior(Z: np.ndarray, S: np.ndarray, alphas=(0.1, 1.0, 10.0, 100.0, 1000.0)):
    """Ridge map Z -> S with alpha by leave-one-out; returns (W, mean_z, mean_s, cov, alpha).

    ``cov`` is the leave-one-out residual covariance (the prior covariance for a new row).
    With no features, the prior is the training mean and covariance of S.
    """

    mu_s = S.mean(0)
    if Z is None or Z.shape[1] == 0:
        C = np.cov(S.T) if len(S) > 1 else np.eye(S.shape[1])
        return None, None, mu_s, np.atleast_2d(C), None
    mu_z = Z.mean(0)
    Zc, Sc = Z - mu_z, S - mu_s
    n, p = Zc.shape
    best = None
    U, sv, Vt = np.linalg.svd(Zc, full_matrices=False)
    for a in alphas:
        # Hat matrix diagonal and LOO residuals in closed form.
        f = sv ** 2 / (sv ** 2 + a)
        H_diag = (U ** 2 * f).sum(1)
        fit = U @ (f[:, None] * (U.T @ Sc))
        loo = (Sc - fit) / np.maximum(1 - H_diag, 1e-6)[:, None]
        err = (loo ** 2).sum()
        if best is None or err < best[0]:
            best = (err, a, loo)
    _, a, loo = best
    W = Vt.T @ ((sv / (sv ** 2 + a))[:, None] * (U.T @ Sc))
    C = np.cov(loo.T) if n > 1 else np.eye(S.shape[1])
    return W, mu_z, mu_s, np.atleast_2d(C), a


def blr(m0, C0, H, y, noise):
    """Posterior of s ~ N(m0, C0) after y = H s + e, e ~ N(0, diag(noise))."""

    if H.shape[0] == 0:
        return m0, C0
    P0 = np.linalg.inv(C0 + 1e-9 * np.eye(len(m0)))
    Hn = H / noise[:, None]
    P = P0 + H.T @ Hn
    C = np.linalg.inv(P)
    m = C @ (P0 @ m0 + Hn.T @ y)
    return m, C


# ---------------------------------------------------------------- strong inductive model

@dataclass
class StrongModel:
    rank: int = 10
    lam: float = 5.0
    iters: int = 12
    seed: int = 20261017

    def fit(self, Y: np.ndarray):
        """Y: (drugs, lines) training means with NaN for unobserved entries."""

        D, L = Y.shape
        obs = np.isfinite(Y)
        Yz = np.where(obs, Y, 0.0)
        a = np.array([Y[d, obs[d]].mean() if obs[d].any() else 0.0 for d in range(D)])
        resid = np.where(obs, Y - a[:, None], 0.0)
        b = np.array([resid[obs[:, c], c].mean() if obs[:, c].any() else 0.0 for c in range(L)])
        R0 = np.where(obs, Y - a[:, None] - b[None, :], 0.0)
        U0, sv, Vt = np.linalg.svd(R0, full_matrices=False)
        r = self.rank
        U = U0[:, :r] * np.sqrt(sv[:r])
        V = Vt[:r].T * np.sqrt(sv[:r])
        lam = self.lam
        for _ in range(self.iters):
            # line step: [b_c, V_c] given a, U
            Xd = np.column_stack([np.ones(D), U])
            reg = lam * np.eye(r + 1)
            reg[0, 0] = 1e-6
            for c in range(L):
                o = obs[:, c]
                X = Xd[o]
                sol = np.linalg.solve(X.T @ X + reg, X.T @ (Yz[o, c] - a[o]))
                b[c], V[c] = sol[0], sol[1:]
            # drug step: [a_d, U_d] given b, V
            Xl = np.column_stack([np.ones(L), V])
            for d in range(D):
                o = obs[d]
                X = Xl[o]
                sol = np.linalg.solve(X.T @ X + reg, X.T @ (Yz[d, o] - b[o]))
                a[d], U[d] = sol[0], sol[1:]
        self.a, self.b, self.U, self.V = a, b, U, V
        fit = a[:, None] + b[None, :] + U @ V.T
        res = np.where(obs, Y - fit, np.nan)
        self.resid_var = np.nan_to_num(np.nanmean(res ** 2, axis=1), nan=np.nanmean(res ** 2))
        self.line_state = np.column_stack([b, V])
        self.drug_state = np.column_stack([a, U])
        return self

    # -- new lines
    def line_prior(self, Ztrain):
        self._lp = ridge_prior(Ztrain, self.line_state)
        return self

    def predict_lines(self, Znew, probes=None, probe_noise=None):
        """Posterior line states and predicted (drugs, new lines) means.

        probes: list (one per new line) of dict {drug_index: readout} on TRAINING drug axis.
        probe_noise: per-drug noise variance for a single-replicate readout.
        Returns (mean (D, n), state_means (n, r+1), state_covs (n, r+1, r+1)).
        """

        W, mu_z, mu_s, C0, _ = self._lp
        n = 1 if Znew is None else len(Znew)
        if probes is not None:
            n = len(probes)
        Hfull = np.column_stack([np.ones(len(self.a)), self.U])
        means, covs = [], []
        for i in range(n):
            m0 = mu_s.copy() if W is None else mu_s + (Znew[i] - mu_z) @ W
            m, C = m0, C0
            if probes is not None and probes[i]:
                idx = np.array(sorted(probes[i]), int)
                y = np.array([probes[i][j] for j in idx]) - self.a[idx]
                m, C = blr(m0, C0, Hfull[idx], y, probe_noise[idx])
            means.append(m)
            covs.append(C)
        S = np.array(means)
        mean = self.a[:, None] + Hfull @ S.T
        return mean, S, np.array(covs)

    # -- new drugs
    def drug_prior(self, Ftrain, alphas=(1.0, 10.0, 100.0, 1000.0)):
        self._dp = ridge_prior(Ftrain, self.drug_state, alphas)
        return self

    def predict_drugs(self, Fnew, line_states, pool_probes=None, noise=None):
        """Predicted means (new drugs, lines) for given line states [b, V] (n_lines, r+1).

        pool_probes: list per new drug of dict {line_index: readout} on the line_states axis.
        Returns (mean (n_drugs, n_lines), drug_state_means, drug_state_covs).
        """

        W, mu_z, mu_s, C0, _ = self._dp
        G = np.column_stack([np.ones(len(line_states)), line_states[:, 1:]])
        out, ms, cs = [], [], []
        for i in range(len(Fnew)):
            m0 = mu_s + (Fnew[i] - mu_z) @ W
            m, C = m0, C0
            if pool_probes is not None and pool_probes[i]:
                idx = np.array(sorted(pool_probes[i]), int)
                y = np.array([pool_probes[i][j] for j in idx]) - line_states[idx, 0]
                m, C = blr(m0, C0, G[idx], y, np.full(len(idx), noise))
            out.append(G @ m + line_states[:, 0])
            ms.append(m)
            cs.append(C)
        return np.array(out), np.array(ms), np.array(cs)


# ---------------------------------------------------------------- program language

BINARY = ("mut", "lin")
CONTINUOUS = ("expr", "probe", "b")


def parse_state(text: str):
    """State grammar: atom | and(A,B) | andnot(A,B) | mul(C,G). Atoms: mut:G lin:T expr:G probe:CORE b."""

    text = text.strip()
    for op in ("andnot", "and", "mul"):
        if text.startswith(op + "("):
            inner = text[len(op) + 1:-1]
            depth, cut = 0, None
            for i, ch in enumerate(inner):
                depth += ch == "("
                depth -= ch == ")"
                if ch == "," and depth == 0:
                    cut = i
                    break
            if cut is None or not text.endswith(")"):
                raise ValueError(f"bad_state:{text}")
            return (op, parse_state(inner[:cut]), parse_state(inner[cut + 1:]))
    if text == "b":
        return ("b",)
    kind, _, arg = text.partition(":")
    if kind not in BINARY + CONTINUOUS or not arg:
        raise ValueError(f"bad_atom:{text}")
    return (kind, arg)


def state_text(tree) -> str:
    if tree[0] in ("and", "andnot", "mul"):
        return f"{tree[0]}({state_text(tree[1])},{state_text(tree[2])})"
    return "b" if tree[0] == "b" else f"{tree[0]}:{tree[1]}"


def atoms(tree):
    if tree[0] in ("and", "andnot", "mul"):
        return atoms(tree[1]) + atoms(tree[2])
    return [tree]


def is_binary(tree) -> bool:
    if tree[0] in ("and", "andnot"):
        return True
    if tree[0] == "mul":
        return False
    return tree[0] in BINARY


@dataclass
class Program:
    scope: str
    state: str
    origin: str = "seed"
    note: str = ""

    @property
    def key(self) -> str:
        return f"{self.scope}|{state_text(parse_state(self.state))}"

    def requirements(self) -> dict:
        req = {"panel": False, "markers": set(), "probes": set()}
        for at in atoms(parse_state(self.state)):
            if at[0] == "mut":
                req["panel"] = True
            elif at[0] == "expr":
                req["markers"].add(at[1])
            elif at[0] == "probe":
                req["probes"].add(at[1])
        return req

    def complexity(self) -> int:
        return len(atoms(parse_state(self.state))) + (0 if self.scope == "all" else 1)


class LineContext:
    """Observable line data for state evaluation: feature arrays plus per-line probe readouts."""

    def __init__(self, feats: dict, rows: np.ndarray, probe_values: dict | None, b_post: np.ndarray):
        self.f = feats
        self.rows = np.asarray(rows)
        self.probe_values = probe_values or {}
        self.b_post = b_post
        self.panel_index = {g: i for i, g in enumerate(feats["panel_genes"])}
        self.lin_index = {g: i for i, g in enumerate(feats["lineage_names"])}
        self.expr_index = {g: i for i, g in enumerate(feats["expr_genes"])}

    def atom(self, at) -> np.ndarray:
        kind = at[0]
        if kind == "b":
            return np.asarray(self.b_post, float)
        name = at[1]
        if kind == "mut":
            if name not in self.panel_index:
                raise KeyError(f"unknown_panel_gene:{name}")
            return self.f["panel"][self.rows, self.panel_index[name]]
        if kind == "lin":
            if name not in self.lin_index:
                raise KeyError(f"unknown_lineage:{name}")
            return self.f["lineage"][self.rows, self.lin_index[name]]
        if kind == "expr":
            if name not in self.expr_index:
                raise KeyError(f"unknown_marker_gene:{name}")
            return self.f["expr"][self.rows, self.expr_index[name]]
        if kind == "probe":
            if name not in self.probe_values:
                raise KeyError(f"probe_not_measured:{name}")
            return self.probe_values[name]
        raise KeyError(kind)

    def state(self, tree) -> np.ndarray:
        op = tree[0]
        if op == "and":
            return self.state(tree[1]) * self.state(tree[2])
        if op == "andnot":
            return self.state(tree[1]) * (1 - self.state(tree[2]))
        if op == "mul":
            return self.state(tree[1]) * self.state(tree[2])
        return self.atom(tree)


def scope_mask(scope: str, dfeat: dict, drug_rows: np.ndarray) -> np.ndarray:
    if scope == "all":
        return np.ones(len(drug_rows), bool)
    kind, _, name = scope.partition(":")
    toks = dfeat["moa_tokens"] if kind == "moa" else dfeat["target_tokens"] if kind == "target" else None
    if toks is None:
        raise ValueError(f"bad_scope:{scope}")
    return np.array([name in toks[i] for i in drug_rows], bool)


@dataclass
class ProgramLibrary:
    programs: list = field(default_factory=list)
    tau: float = 20.0          # shrinkage of drug-specific loadings toward the scope loading
    shared_only: bool = False  # True: every drug in scope uses the shared loading only

    def copy(self):
        return ProgramLibrary([Program(p.scope, p.state, p.origin, p.note) for p in self.programs],
                              self.tau, self.shared_only)

    def keys(self):
        return [p.key for p in self.programs]

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(sorted(self.keys())).encode()).hexdigest()[:16]

    def requirements(self) -> dict:
        req = {"panel": False, "markers": set(), "probes": set()}
        for p in self.programs:
            r = p.requirements()
            req["panel"] |= r["panel"]
            req["markers"] |= r["markers"]
            req["probes"] |= r["probes"]
        return req

    def complexity(self) -> int:
        return sum(p.complexity() for p in self.programs)

    def states(self, ctx: LineContext) -> np.ndarray:
        if not self.programs:
            return np.zeros((len(ctx.rows), 0))
        return np.column_stack([ctx.state(parse_state(p.state)) for p in self.programs])

    def fit(self, R: np.ndarray, Phi: np.ndarray, dfeat: dict, drug_rows: np.ndarray):
        """R: (drugs, train lines) cross-fitted residuals (NaN = unobserved); Phi: (train lines, K)."""

        K = len(self.programs)
        self.mu = Phi.mean(0) if K else np.zeros(0)
        self.sd = Phi.std(0) + 1e-9 if K else np.zeros(0)
        X = (Phi - self.mu) / self.sd if K else Phi
        D = R.shape[0]
        M = np.column_stack([scope_mask(p.scope, dfeat, drug_rows) for p in self.programs]) if K else np.zeros((D, 0), bool)
        self.scope_cols = M
        B = np.zeros((D, K))
        beta = np.zeros(K)
        if K == 0:
            self.B, self.beta = B, beta
            return self
        obs = np.isfinite(R)
        for _ in range(4):
            for d in range(D):
                ks = np.flatnonzero(M[d])
                if len(ks) == 0:
                    continue
                o = obs[d]
                Xo = X[o][:, ks]
                if self.shared_only:
                    B[d, ks] = beta[ks]
                    continue
                A = Xo.T @ Xo + self.tau * np.eye(len(ks))
                B[d, ks] = np.linalg.solve(A, Xo.T @ R[d, o] + self.tau * beta[ks])
            if self.shared_only:
                # shared loadings by pooled least squares over scope drugs
                Xs, ys = [], []
                rows = []
                for d in range(D):
                    ks = np.flatnonzero(M[d])
                    if len(ks) == 0:
                        continue
                    o = obs[d]
                    Z = np.zeros((o.sum(), K))
                    Z[:, ks] = X[o][:, ks]
                    Xs.append(Z)
                    ys.append(R[d, o])
                Xa, ya = np.vstack(Xs), np.concatenate(ys)
                beta = np.linalg.solve(Xa.T @ Xa + 1e-3 * np.eye(K), Xa.T @ ya)
                for d in range(D):
                    ks = np.flatnonzero(M[d])
                    B[d, ks] = beta[ks]
                break
            for k in range(K):
                beta[k] = B[M[:, k], k].mean() if M[:, k].any() else 0.0
        self.B, self.beta = B, beta
        fitted = (X @ B.T).T if K else np.zeros_like(R)
        res = np.where(obs, R - fitted, np.nan)
        self.resid_var = np.nanmean(res ** 2, axis=1)
        self.base_var = np.nanmean(np.where(obs, R, np.nan) ** 2, axis=1)
        return self

    def correction(self, Phi_new: np.ndarray, dfeat: dict, drug_rows: np.ndarray, novel: bool) -> np.ndarray:
        """(drugs, new lines) additive correction. Novel drugs use the scope-shared loading."""

        K = len(self.programs)
        if K == 0:
            return np.zeros((len(drug_rows), len(Phi_new)))
        X = (Phi_new - self.mu) / self.sd
        if novel:
            M = np.column_stack([scope_mask(p.scope, dfeat, drug_rows) for p in self.programs])
            B = M * self.beta[None, :]
        else:
            B = self.B
        return B @ X.T


def hit_probability(mean, var, thr):
    """P(response <= thr) under N(mean, var); arrays broadcast as (drugs, lines)."""

    return ndtr((thr - mean) / np.sqrt(np.maximum(var, 1e-6)))


def top_k(score: np.ndarray, k: int, tie: np.ndarray) -> np.ndarray:
    """Indices of the k largest scores per column; ties broken by a fixed hashed order."""

    order = np.lexsort((tie[:, None].repeat(score.shape[1], 1), -score), axis=0)
    return order[:k]
