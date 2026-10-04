"""Empirical-Bayes world model for drug-combination response in a newly screened cell line.

File summary
- Path: src/virtual_cell/combination_world.py
- Purpose: the virtual-cell core of certified combination discovery. For one target line it
  predicts each candidate pair's synergy label (Bliss excess, percentage points) with a
  predictive variance, from three sources the agent may use before and during a campaign:
  combinations measured in OTHER lines (history), every line's single-agent responses (the
  cell's functional state), and the combinations the agent has bought in the target line.
- Core points:
  - Prior mean: ridge regression on history features, cross-fitted so a history row never sees
    its own line and no row sees the target line. `context=False` drops the cell-state features.
  - In-context residual r = line effect + drug effects in this line + noise. All algebra runs in
    (drugs + 1) dimensions through the Woodbury identity; a world build is about 0.1 s and a
    posterior update a few milliseconds on a 5,000-candidate line.
  - Variances are fitted by marginal likelihood on history lines only (empirical Bayes), with a
    numpy Nelder-Mead in log space, so the target line's labels never tune the model.
  - Refusals are named (`CombinationWorldRefusal`): TARGET_LINE_UNKNOWN, NO_HISTORY,
    MEASUREMENT_MISMATCH.
  - Promoted from research/certified_discovery/world.py (frozen there with its development and
    confirmatory evidence); parity with that copy is tested.
- Interfaces: `CombinationScreen`, `CombinationWorldConfig`, `CombinationWorld`,
  `CombinationWorldRefusal`, `normal_cdf`.
- Depends on: numpy.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


class CombinationWorldRefusal(ValueError):
    """The world model declines a query and names why."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class CombinationScreen:
    """Candidate experiments (unordered drug pair x line) and their measured labels."""

    drugs: tuple[str, ...]
    lines: tuple[str, ...]
    a: np.ndarray            # drug index, a < b
    b: np.ndarray
    c: np.ndarray            # line index
    y: np.ndarray            # label (target-line entries are read only through feedback)
    expected: np.ndarray     # Bliss-expected inhibition from single agents (context)
    mono_mean: np.ndarray    # (drugs, lines) single-agent inhibition, mean over combination doses
    mono_top: np.ndarray     # (drugs, lines) single-agent inhibition at the top dose
    threshold: float = 10.0  # hit = label > threshold


@dataclass(frozen=True)
class CombinationWorldConfig:
    context: bool = True
    feedback: bool = True
    drug_similarity: bool = True
    shuffle_seed: int | None = None
    ridge: float = 1.0
    shrink: float = 2.0


def normal_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF via the exact complementary error function."""
    flat = np.asarray(x, float).ravel()
    values = np.fromiter((0.5 * math.erfc(-v / math.sqrt(2.0)) for v in flat), float, flat.size)
    return values.reshape(np.shape(x))


def _zscore_columns(matrix: np.ndarray) -> np.ndarray:
    filled = np.where(np.isnan(matrix), np.nanmean(matrix, axis=0, keepdims=True), matrix)
    sd = filled.std(axis=0, keepdims=True)
    return (filled - filled.mean(axis=0, keepdims=True)) / np.where(sd > 0, sd, 1.0)


def _rbf_similarity(profiles: np.ndarray) -> np.ndarray:
    sq = np.sum(profiles ** 2, axis=1)
    d2 = np.maximum(sq[:, None] + sq[None, :] - 2 * profiles @ profiles.T, 0.0)
    off = d2[~np.eye(len(d2), dtype=bool)]
    tau2 = np.median(off) if off.size and np.median(off) > 0 else 1.0
    sim = np.exp(-d2 / (2 * tau2))
    np.fill_diagonal(sim, 0.0)
    return sim


def nelder_mead(function, start: np.ndarray, lower: np.ndarray, upper: np.ndarray,
                *, iterations: int = 600, tolerance: float = 1e-10) -> np.ndarray:
    """Bounded Nelder-Mead (clipped vertices); deterministic, numpy only."""
    dimension = start.size
    simplex = [np.clip(start, lower, upper)]
    for axis in range(dimension):
        vertex = start.copy()
        vertex[axis] += 0.5 if vertex[axis] + 0.5 <= upper[axis] else -0.5
        simplex.append(np.clip(vertex, lower, upper))
    values = [function(v) for v in simplex]
    for _ in range(iterations):
        order = np.argsort(values)
        simplex = [simplex[i] for i in order]
        values = [values[i] for i in order]
        if abs(values[-1] - values[0]) <= tolerance * (1.0 + abs(values[0])):
            break
        centroid = np.mean(simplex[:-1], axis=0)
        reflected = np.clip(centroid + (centroid - simplex[-1]), lower, upper)
        f_reflected = function(reflected)
        if f_reflected < values[0]:
            expanded = np.clip(centroid + 2.0 * (centroid - simplex[-1]), lower, upper)
            f_expanded = function(expanded)
            simplex[-1], values[-1] = (expanded, f_expanded) if f_expanded < f_reflected else (reflected, f_reflected)
        elif f_reflected < values[-2]:
            simplex[-1], values[-1] = reflected, f_reflected
        else:
            contracted = np.clip(centroid + 0.5 * (simplex[-1] - centroid), lower, upper)
            f_contracted = function(contracted)
            if f_contracted < values[-1]:
                simplex[-1], values[-1] = contracted, f_contracted
            else:
                best = simplex[0]
                simplex = [best] + [np.clip(best + 0.5 * (v - best), lower, upper) for v in simplex[1:]]
                values = [values[0]] + [function(v) for v in simplex[1:]]
    return simplex[int(np.argmin(values))]


class CombinationWorld:
    """Predict a target line's combination labels from history, cell state and feedback."""

    def __init__(self, screen: CombinationScreen, target_line: int,
                 config: CombinationWorldConfig = CombinationWorldConfig()):
        if not 0 <= int(target_line) < len(screen.lines):
            raise CombinationWorldRefusal("TARGET_LINE_UNKNOWN", f"line index {target_line}")
        self.screen, self.target, self.config = screen, int(target_line), config
        self.rows = np.flatnonzero(screen.c == self.target)
        if not np.any(screen.c != self.target):
            raise CombinationWorldRefusal("NO_HISTORY", "no other line carries measured combinations")
        self._build_context()
        self._build_history()
        self._fit_prior()
        self._fit_variances()

    def _build_context(self) -> None:
        s, cfg = self.screen, self.config
        n_drugs, n_lines = s.mono_mean.shape
        self.line_sim = _rbf_similarity(_zscore_columns(s.mono_mean.T))
        drug_sim = _rbf_similarity(_zscore_columns(s.mono_mean))
        self.mono_mean = np.nan_to_num(s.mono_mean, nan=float(np.nanmean(s.mono_mean)))
        self.mono_top = np.nan_to_num(s.mono_top, nan=float(np.nanmean(s.mono_top)))
        self.expected = np.asarray(s.expected, float).copy()
        if cfg.shuffle_seed is not None:
            rng = np.random.default_rng(cfg.shuffle_seed)
            line_perm, drug_perm = rng.permutation(n_lines), rng.permutation(n_drugs)
            self.line_sim = self.line_sim[np.ix_(line_perm, line_perm)]
            drug_sim = drug_sim[np.ix_(drug_perm, drug_perm)]
            for column in range(n_lines):
                order = rng.permutation(n_drugs)
                self.mono_mean[:, column] = self.mono_mean[order, column]
                self.mono_top[:, column] = self.mono_top[order, column]
            self.expected = 1.0 - (1.0 - np.clip(self.mono_mean[s.a, s.c], 0, 1)) * (
                1.0 - np.clip(self.mono_mean[s.b, s.c], 0, 1))
        self.drug_kernel = np.eye(n_drugs)
        if cfg.context and cfg.drug_similarity:
            self.drug_kernel = 0.5 * np.eye(n_drugs) + 0.5 * drug_sim

    def _build_history(self) -> None:
        s, cfg = self.screen, self.config
        n_drugs, n_lines = s.mono_mean.shape
        pairs, pair_id = np.unique(s.a.astype(np.int64) * n_drugs + s.b, return_inverse=True)
        history = s.c != self.target
        Y = np.zeros((pairs.size, n_lines))
        N = np.zeros((pairs.size, n_lines))
        np.add.at(Y, (pair_id[history], s.c[history]), s.y[history])
        np.add.at(N, (pair_id[history], s.c[history]), 1.0)
        D = np.zeros((n_drugs, n_lines))
        DN = np.zeros((n_drugs, n_lines))
        for drug in (s.a, s.b):
            np.add.at(D, (drug[history], s.c[history]), s.y[history])
            np.add.at(DN, (drug[history], s.c[history]), 1.0)
        mu, k0 = float(s.y[history].mean()), cfg.shrink
        W = self.line_sim.copy()
        W[:, self.target] = 0.0

        def features(rows: np.ndarray, exclude_own: bool) -> np.ndarray:
            p, a, b, c = pair_id[rows], s.a[rows], s.b[rows], s.c[rows]
            own = 1.0 if exclude_own else 0.0
            total, count = Y[p].sum(axis=1) - own * Y[p, c], N[p].sum(axis=1) - own * N[p, c]
            pair_mean = (total + k0 * mu) / (count + k0)
            da = (D[a].sum(axis=1) - own * D[a, c]) / np.maximum(DN[a].sum(axis=1) - own * DN[a, c], 1.0)
            db = (D[b].sum(axis=1) - own * D[b, c]) / np.maximum(DN[b].sum(axis=1) - own * DN[b, c], 1.0)
            columns = [pair_mean, np.maximum(da, db), np.minimum(da, db)]
            if cfg.context:
                w = W[c]
                sim_mean = (np.einsum("rl,rl->r", Y[p], w) + k0 * pair_mean) / (np.einsum("rl,rl->r", N[p], w) + k0)
                dwa = np.einsum("rl,rl->r", D[a], w) / np.maximum(np.einsum("rl,rl->r", DN[a], w), 1e-9)
                dwb = np.einsum("rl,rl->r", D[b], w) / np.maximum(np.einsum("rl,rl->r", DN[b], w), 1e-9)
                ma, mb = self.mono_mean[a, c], self.mono_mean[b, c]
                ta, tb = self.mono_top[a, c], self.mono_top[b, c]
                columns += [sim_mean, np.maximum(dwa, dwb), np.minimum(dwa, dwb), np.maximum(ma, mb),
                            np.minimum(ma, mb), np.maximum(ta, tb), np.minimum(ta, tb), self.expected[rows]]
            return np.column_stack(columns)

        self.history_rows = np.flatnonzero(history)
        self.X_history = features(self.history_rows, exclude_own=True)
        self.X_target = features(self.rows, exclude_own=False)

    def _fit_prior(self) -> None:
        X, y = self.X_history, self.screen.y[self.history_rows]
        self.x_mean, self.x_sd = X.mean(axis=0), X.std(axis=0)
        self.x_sd[self.x_sd == 0] = 1.0
        Z = (X - self.x_mean) / self.x_sd
        self.beta = np.linalg.solve(Z.T @ Z + self.config.ridge * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
        self.intercept = float(y.mean())
        self.history_residual = y - self._prior(X)
        self.prior_target = self._prior(self.X_target)

    def _prior(self, X: np.ndarray) -> np.ndarray:
        return self.intercept + ((X - self.x_mean) / self.x_sd) @ self.beta

    def _design(self, rows: np.ndarray) -> np.ndarray:
        Z = np.zeros((rows.size, self.drug_kernel.shape[0] + 1))
        Z[:, 0] = 1.0
        span = np.arange(rows.size)
        np.add.at(Z, (span, 1 + self.screen.a[rows]), 1.0)
        np.add.at(Z, (span, 1 + self.screen.b[rows]), 1.0)
        return Z

    def _fit_variances(self) -> None:
        s = self.screen
        stats = []
        for line in np.unique(s.c[self.history_rows]):
            idx = np.flatnonzero(s.c[self.history_rows] == line)
            Z = self._design(self.history_rows[idx])
            r = self.history_residual[idx]
            stats.append((idx.size, Z.T @ Z, Z.T @ r, float(r @ r)))
        total_var = float(np.var(self.history_residual))
        kernel_inv = np.linalg.inv(self.drug_kernel)
        kernel_logdet = float(np.linalg.slogdet(self.drug_kernel)[1])
        n_drugs = self.drug_kernel.shape[0]

        def negative_log_likelihood(log_params: np.ndarray) -> float:
            s_line, s_drug, s_noise = np.exp(log_params)
            A_inv = np.zeros((n_drugs + 1, n_drugs + 1))
            A_inv[0, 0] = 1.0 / s_line
            A_inv[1:, 1:] = kernel_inv / s_drug
            logdet_A = math.log(s_line) + n_drugs * math.log(s_drug) + kernel_logdet
            value = 0.0
            for n, ZtZ, Ztr, rr in stats:
                try:
                    L = np.linalg.cholesky(A_inv + ZtZ / s_noise)
                except np.linalg.LinAlgError:
                    return 1e18
                w = np.linalg.solve(L, Ztr)
                value += 0.5 * (rr / s_noise - (w @ w) / s_noise ** 2 + n * math.log(s_noise) + logdet_A
                                + 2 * np.log(np.diag(L)).sum())
            return float(value)

        lower = np.full(3, math.log(total_var * 1e-5))
        upper = np.full(3, math.log(total_var * 2))
        start = np.log([total_var * 0.05, total_var * 0.05, total_var * 0.8])
        self.negative_log_likelihood = negative_log_likelihood
        best = nelder_mead(negative_log_likelihood, start, lower, upper)
        self.s_line, self.s_drug, self.s_noise = (float(v) for v in np.exp(best))
        self.A = np.zeros((n_drugs + 1, n_drugs + 1))
        self.A[0, 0] = self.s_line
        self.A[1:, 1:] = self.s_drug * self.drug_kernel
        self.A_inv = np.linalg.inv(self.A)
        self.Z_target = self._design(self.rows)
        self.prior_var_target = np.einsum("ij,jk,ik->i", self.Z_target, self.A, self.Z_target) + self.s_noise

    def posterior(self, measured: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Predictive mean and variance of the measured label for every target-line candidate."""
        measured = np.asarray(measured, int)
        values = np.asarray(values, float)
        if measured.shape != values.shape:
            raise CombinationWorldRefusal("MEASUREMENT_MISMATCH", "measured indices and values differ in shape")
        if not self.config.feedback or measured.size == 0:
            return self.prior_target.copy(), self.prior_var_target.copy()
        Zm = self.Z_target[measured]
        covariance = np.linalg.inv(self.A_inv + Zm.T @ Zm / self.s_noise)
        effects = covariance @ (Zm.T @ (values - self.prior_target[measured])) / self.s_noise
        mean = self.prior_target + self.Z_target @ effects
        var = np.einsum("ij,jk,ik->i", self.Z_target, covariance, self.Z_target) + self.s_noise
        return mean, var

    def p_hit(self, mean: np.ndarray, var: np.ndarray) -> np.ndarray:
        return normal_cdf((mean - self.screen.threshold) / np.sqrt(var))
