"""Empirical-Bayes transfer world model for combination response in a new cell line.

File summary
- Path: research/certified_discovery/world.py
- Purpose: the virtual-cell core of the certified-discovery loop. For a target cell line it
  predicts every candidate pair's synergy label, with a predictive variance, from (i) the
  combination history measured in OTHER lines, (ii) the single-agent responses of every line
  (the cell's functional state, available before any combination is bought), and (iii) the
  combinations already bought in the target line (in-context feedback).
- Core points:
  - Prior mean: ridge regression on history features, cross-fitted so a history row never
    sees its own line or the target line. Features: the pair's mean label in other lines; its
    mean in functionally similar lines (similarity from single-agent profiles); drug-level
    means; single-agent potency of both drugs in the target line and their Bliss-expected
    inhibition. `context=False` keeps only the context-free history features.
  - In-context residual: a Gaussian process over target-line experiments whose kernel is a
    drug-in-line random effect (two drugs per experiment), optionally widened to functionally
    similar drugs. Its two variances are fitted by marginal likelihood on history lines'
    cross-fitted residuals (empirical Bayes), never on the target line.
  - `shuffle` permutes the cell-state context (line similarity, single-agent features, drug
    similarity) with a seeded permutation: the structure stays, the biology is destroyed.
  - Labels of the target line are never read except through `posterior(measured, values)`.
- Interfaces: `WorldConfig`, `TransferWorld`.
- Depends on: numpy, scipy (optimize, special), `screens.Library`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import optimize, special

from .screens import Library


@dataclass(frozen=True)
class WorldConfig:
    context: bool = True            # use single-agent cell-state features and similarities
    feedback: bool = True           # condition on target-line measurements
    drug_similarity: bool = True    # widen the in-context drug effect to similar drugs
    shuffle_seed: int | None = None # permute cell-state context (control)
    ridge: float = 1.0
    shrink: float = 2.0             # pseudo-count toward the global mean for history means
    eb_lines: int = 24              # history lines used for the empirical-Bayes variance fit
    eb_rows: int = 600              # rows per history line in that fit


def _zscore_columns(matrix: np.ndarray) -> np.ndarray:
    filled = np.where(np.isnan(matrix), np.nanmean(matrix, axis=0, keepdims=True), matrix)
    sd = filled.std(axis=0, keepdims=True)
    return (filled - filled.mean(axis=0, keepdims=True)) / np.where(sd > 0, sd, 1.0)


def _rbf_similarity(profiles: np.ndarray) -> np.ndarray:
    """exp(-d^2 / 2 tau^2) between rows, tau = median off-diagonal distance; zero diagonal."""
    sq = np.sum(profiles ** 2, axis=1)
    d2 = np.maximum(sq[:, None] + sq[None, :] - 2 * profiles @ profiles.T, 0.0)
    off = d2[~np.eye(len(d2), dtype=bool)]
    tau2 = np.median(off) if off.size and np.median(off) > 0 else 1.0
    sim = np.exp(-d2 / (2 * tau2))
    np.fill_diagonal(sim, 0.0)
    return sim


class TransferWorld:
    """Predict a target line's combination labels from history, cell state and feedback."""

    def __init__(self, library: Library, target_line: int, config: WorldConfig = WorldConfig()):
        self.lib = library
        self.target = int(target_line)
        self.config = config
        self.rows = np.flatnonzero(library.c == self.target)          # campaign candidates
        self._build_context()
        self._build_history()
        self._fit_prior()
        self._fit_variances()

    # ------------------------------------------------------------------ context
    def _build_context(self) -> None:
        lib, cfg = self.lib, self.config
        n_drugs, n_lines = lib.mono_mean.shape
        line_profiles = _zscore_columns(lib.mono_mean.T)               # lines x drugs
        drug_profiles = _zscore_columns(lib.mono_mean)                 # drugs x lines
        self.line_sim = _rbf_similarity(line_profiles)
        drug_sim = _rbf_similarity(drug_profiles)
        self.mono_mean = np.nan_to_num(lib.mono_mean, nan=float(np.nanmean(lib.mono_mean)))
        self.mono_top = np.nan_to_num(lib.mono_top, nan=float(np.nanmean(lib.mono_top)))
        self.expected = lib.expected.copy()
        if cfg.shuffle_seed is not None:
            rng = np.random.default_rng(cfg.shuffle_seed)
            line_perm = rng.permutation(n_lines)
            drug_perm = rng.permutation(n_drugs)
            self.line_sim = self.line_sim[np.ix_(line_perm, line_perm)]
            drug_sim = drug_sim[np.ix_(drug_perm, drug_perm)]
            for column in range(n_lines):                              # within-line drug shuffle
                order = rng.permutation(n_drugs)
                self.mono_mean[:, column] = self.mono_mean[order, column]
                self.mono_top[:, column] = self.mono_top[order, column]
            self.expected = 1.0 - (1.0 - np.clip(self.mono_mean[lib.a, lib.c], 0, 1)) * (
                1.0 - np.clip(self.mono_mean[lib.b, lib.c], 0, 1))
        self.drug_kernel = np.eye(n_drugs)
        if cfg.context and cfg.drug_similarity:
            self.drug_kernel = 0.5 * np.eye(n_drugs) + 0.5 * drug_sim

    # ------------------------------------------------------------------ history features
    def _build_history(self) -> None:
        lib, cfg = self.lib, self.config
        n_drugs, n_lines = lib.mono_mean.shape
        pair = lib.a.astype(np.int64) * n_drugs + lib.b
        pairs, pair_id = np.unique(pair, return_inverse=True)
        self.pair_id = pair_id
        history = lib.c != self.target
        n_pairs = pairs.size
        Y = np.zeros((n_pairs, n_lines))
        N = np.zeros((n_pairs, n_lines))
        np.add.at(Y, (pair_id[history], lib.c[history]), lib.y[history])
        np.add.at(N, (pair_id[history], lib.c[history]), 1.0)
        D = np.zeros((n_drugs, n_lines))
        DN = np.zeros((n_drugs, n_lines))
        for drug in (lib.a, lib.b):
            np.add.at(D, (drug[history], lib.c[history]), lib.y[history])
            np.add.at(DN, (drug[history], lib.c[history]), 1.0)
        self.global_mean = float(lib.y[history].mean())
        W = self.line_sim.copy()
        W[:, self.target] = 0.0                                       # target labels never enter
        k0, mu = cfg.shrink, self.global_mean

        def features(rows: np.ndarray, exclude_own: bool) -> np.ndarray:
            p, a, b, c = pair_id[rows], lib.a[rows], lib.b[rows], lib.c[rows]
            # A training row must not see anything from its own line, exactly as the target
            # line is unseen at the start of a campaign (pair x line is unique in a screen).
            own = 1.0 if exclude_own else 0.0
            s, n = Y[p].sum(axis=1) - own * Y[p, c], N[p].sum(axis=1) - own * N[p, c]
            pair_mean = (s + k0 * mu) / (n + k0)
            da = (D[a].sum(axis=1) - own * D[a, c]) / np.maximum(DN[a].sum(axis=1) - own * DN[a, c], 1.0)
            db = (D[b].sum(axis=1) - own * D[b, c]) / np.maximum(DN[b].sum(axis=1) - own * DN[b, c], 1.0)
            cols = [pair_mean, np.maximum(da, db), np.minimum(da, db)]
            if cfg.context:
                w = W[c]                                              # rows x lines (own col 0)
                ws = np.einsum("rl,rl->r", Y[p], w)
                wn = np.einsum("rl,rl->r", N[p], w)
                sim_mean = (ws + k0 * pair_mean) / (wn + k0)
                dwa = np.einsum("rl,rl->r", D[a], w) / np.maximum(np.einsum("rl,rl->r", DN[a], w), 1e-9)
                dwb = np.einsum("rl,rl->r", D[b], w) / np.maximum(np.einsum("rl,rl->r", DN[b], w), 1e-9)
                ma, mb = self.mono_mean[a, c], self.mono_mean[b, c]
                ta, tb = self.mono_top[a, c], self.mono_top[b, c]
                cols += [sim_mean, np.maximum(dwa, dwb), np.minimum(dwa, dwb), np.maximum(ma, mb),
                         np.minimum(ma, mb), np.maximum(ta, tb), np.minimum(ta, tb), self.expected[rows]]
            return np.column_stack(cols)

        self.history_rows = np.flatnonzero(history)
        self.X_history = features(self.history_rows, exclude_own=True)
        self.X_target = features(self.rows, exclude_own=False)

    # ------------------------------------------------------------------ prior mean
    def _fit_prior(self) -> None:
        X, y = self.X_history, self.lib.y[self.history_rows]
        self.x_mean, self.x_sd = X.mean(axis=0), X.std(axis=0)
        self.x_sd[self.x_sd == 0] = 1.0
        Z = (X - self.x_mean) / self.x_sd
        A = Z.T @ Z + self.config.ridge * np.eye(Z.shape[1])
        self.beta = np.linalg.solve(A, Z.T @ (y - y.mean()))
        self.intercept = float(y.mean())
        self.history_residual = y - self._prior(X)
        self.prior_target = self._prior(self.X_target)

    def _prior(self, X: np.ndarray) -> np.ndarray:
        return self.intercept + ((X - self.x_mean) / self.x_sd) @ self.beta

    # ------------------------------------------------------------------ in-context effects
    # Residual model in one line: r = lambda + u_a + u_b + noise, lambda ~ N(0, s_line),
    # u ~ N(0, s_drug * drug_kernel), noise ~ N(0, s_noise). With Z = [1, two-hot drugs] and
    # A = blockdiag(s_line, s_drug * drug_kernel), every quantity is (drugs+1)-dimensional
    # algebra through the Woodbury identity, never an experiments x experiments matrix.
    def _design(self, rows: np.ndarray) -> np.ndarray:
        n_drugs = self.drug_kernel.shape[0]
        Z = np.zeros((rows.size, n_drugs + 1))
        Z[:, 0] = 1.0
        span = np.arange(rows.size)
        np.add.at(Z, (span, 1 + self.lib.a[rows]), 1.0)
        np.add.at(Z, (span, 1 + self.lib.b[rows]), 1.0)
        return Z

    def _prior_cov(self, s_line: float, s_drug: float) -> np.ndarray:
        n_drugs = self.drug_kernel.shape[0]
        A = np.zeros((n_drugs + 1, n_drugs + 1))
        A[0, 0] = s_line
        A[1:, 1:] = s_drug * self.drug_kernel
        return A

    def _fit_variances(self) -> None:
        """Marginal-likelihood fit of (line, drug-in-line, noise) variances on history lines."""
        lib = self.lib
        stats = []
        for line in np.unique(lib.c[self.history_rows]):
            idx = np.flatnonzero(lib.c[self.history_rows] == line)
            Z = self._design(self.history_rows[idx])
            r = self.history_residual[idx]
            stats.append((idx.size, Z.T @ Z, Z.T @ r, float(r @ r)))
        total_var = float(np.var(self.history_residual))
        kernel_inv = np.linalg.inv(self.drug_kernel)
        _, kernel_logdet = np.linalg.slogdet(self.drug_kernel)
        n_drugs = self.drug_kernel.shape[0]

        def negative_log_likelihood(log_params: np.ndarray) -> float:
            s_line, s_drug, s_noise = np.exp(log_params)
            A_inv = np.zeros((n_drugs + 1, n_drugs + 1))
            A_inv[0, 0] = 1.0 / s_line
            A_inv[1:, 1:] = kernel_inv / s_drug
            logdet_A = np.log(s_line) + n_drugs * np.log(s_drug) + kernel_logdet
            value = 0.0
            for n, ZtZ, Ztr, rr in stats:
                M = A_inv + ZtZ / s_noise
                try:
                    L = np.linalg.cholesky(M)
                except np.linalg.LinAlgError:
                    return 1e18
                w = np.linalg.solve(L, Ztr)
                quad = rr / s_noise - (w @ w) / s_noise ** 2
                logdet = n * np.log(s_noise) + logdet_A + 2 * np.log(np.diag(L)).sum()
                value += 0.5 * (quad + logdet)
            return value

        start = np.log([total_var * 0.05, total_var * 0.05, total_var * 0.8])
        bounds = [(np.log(total_var * 1e-5), np.log(total_var * 2))] * 3
        result = optimize.minimize(negative_log_likelihood, start, method="L-BFGS-B", bounds=bounds)
        self.s_line, self.s_drug, self.s_noise = (float(v) for v in np.exp(result.x))
        self.A = self._prior_cov(self.s_line, self.s_drug)
        self.A_inv = np.linalg.inv(self.A)
        self.Z_target = self._design(self.rows)
        self.prior_var_target = np.einsum("ij,jk,ik->i", self.Z_target, self.A, self.Z_target) + self.s_noise

    # ------------------------------------------------------------------ prediction
    def posterior(self, measured: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Predictive mean and variance of the MEASURED label for every campaign candidate.

        `measured` indexes campaign candidates (0..len(rows)-1); `values` are their labels.
        """
        mean = self.prior_target.copy()
        var = self.prior_var_target.copy()
        if not self.config.feedback or len(measured) == 0:
            return mean, var
        measured = np.asarray(measured, int)
        Zm = self.Z_target[measured]
        resid = np.asarray(values, float) - self.prior_target[measured]
        precision = self.A_inv + Zm.T @ Zm / self.s_noise
        covariance = np.linalg.inv(precision)
        effects = covariance @ (Zm.T @ resid) / self.s_noise
        mean = mean + self.Z_target @ effects
        var = np.einsum("ij,jk,ik->i", self.Z_target, covariance, self.Z_target) + self.s_noise
        return mean, var

    def p_hit(self, mean: np.ndarray, var: np.ndarray) -> np.ndarray:
        return special.ndtr((mean - self.lib.threshold) / np.sqrt(var))
