"""Research-only class-conditioned completion of a partially measured response.

For every offered class c, y = base_mean[c] + V z + epsilon, where z ~ N(0, I)
and epsilon ~ N(0, diag(residual_var)). V and residual_var must be fitted only
on proper-training data. One shared covariance does not erase conditional means.
This is a response completion model, not a normalized e-process or STATE result.
"""
from __future__ import annotations

import numpy as np


class ConditionalWorld:
    """Condition each hypothesis on the same measured positions, without truth.

    update replaces the cumulative observed snapshot, as in the existing world
    interface. mean_scale returns class-by-position arrays. Already observed
    coordinates have their known value and zero conditional variance; unobserved
    coordinates retain diagonal residual noise. This forecasts the same response
    vector, not a future independent replicate of an already measured coordinate.
    """

    def __init__(self, V, residual_var, base_mean):
        self.V = np.array(V, dtype=float, copy=True)
        self.residual_var = np.array(residual_var, dtype=float, copy=True)
        self.base_mean = np.array(base_mean, dtype=float, copy=True)
        if (self.V.ndim != 2 or self.base_mean.ndim != 2
                or self.residual_var.shape != (self.V.shape[0],)
                or self.base_mean.shape[1] != self.V.shape[0]):
            raise ValueError("Expected V[position, latent], variance[position], mean[class, position]")
        if not all(np.isfinite(a).all() for a in
                   (self.V, self.residual_var, self.base_mean)):
            raise ValueError("Conditional priors must be finite")
        if np.any(self.residual_var <= 0):
            raise ValueError("Residual variances must be positive")
        self._mean = self.base_mean.copy()
        self._variance = self.residual_var + np.sum(self.V ** 2, axis=1)

    def update(self, purchased_vals, purchased_pos) -> None:
        vals = np.asarray(purchased_vals, dtype=float)
        pos = np.asarray(purchased_pos)
        if vals.ndim != 1 or pos.ndim != 1 or vals.shape != pos.shape:
            raise ValueError("Measured values and positions must be matching vectors")
        if len(pos) and (not np.issubdtype(pos.dtype, np.integer)
                         or np.issubdtype(pos.dtype, np.bool_)):
            raise ValueError("Measured positions must be integer indices")
        pos = pos.astype(int)
        if (np.any(pos < 0) or np.any(pos >= self.V.shape[0])
                or len(np.unique(pos)) != len(pos)):
            raise ValueError("Measured positions must be unique and in range")
        if not np.isfinite(vals).all():
            raise ValueError("Only finite measured values may condition the world")

        observed_basis = self.V[pos]
        precision = (np.eye(self.V.shape[1])
                     + observed_basis.T @ (observed_basis / self.residual_var[pos, None]))
        residuals = vals[None, :] - self.base_mean[:, pos]
        rhs = observed_basis.T @ (residuals / self.residual_var[pos]).T
        # Solve once for all hypothesis means and the shared latent covariance.
        solution = np.linalg.solve(precision, np.column_stack((rhs, np.eye(self.V.shape[1]))))
        latent_mean = solution[:, :self.base_mean.shape[0]].T
        latent_cov = solution[:, self.base_mean.shape[0]:]
        mean = self.base_mean + latent_mean @ self.V.T
        variance = self.residual_var + np.einsum("pi,ij,pj->p", self.V, latent_cov, self.V)
        mean[:, pos] = vals
        variance[pos] = 0.0
        self._mean, self._variance = mean, variance

    def mean_scale(self):
        return self._mean.copy(), np.broadcast_to(
            np.sqrt(self._variance), self.base_mean.shape).copy()

