"""Two exact snapshot ambiguities and independent moment-ODE checks."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/observation_law_search'


def main():
    if (OUT / 'SNAPSHOT_RUN_STARTED.json').exists():
        raise FileExistsError('One-run guard: inspect saved run, do not repeat')
    freeze = json.loads((OUT / 'ROOT_FREEZE.json').read_text(encoding='utf-8'))
    for relative, digest in freeze['files'].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    started = datetime.now(timezone.utc).isoformat()
    (OUT / 'SNAPSHOT_RUN_STARTED.json').write_text(json.dumps({'utc': started}), encoding='utf-8')
    tick = time.perf_counter()
    gamma = .1
    grid_t = np.linspace(0, 1, 9)
    grid_x = np.linspace(-4, 5, 31)
    temporal = []
    for diffusion in [.25, 2.]:
        t, x = np.meshgrid(grid_t, grid_x, indexing='ij')
        z = x - t
        density = np.exp(gamma*t - z*z/2) / np.sqrt(2*np.pi)
        velocity = 1 - diffusion*z
        dt_density = (gamma + z)*density
        rhs = (diffusion + velocity*z + diffusion*(z*z-1) + gamma)*density
        residual = float(np.max(np.abs(dt_density - rhs)))
        analytic_shift = -(-np.expm1(-diffusion))/diffusion
        solution = solve_ivp(lambda t, y: [1-diffusion*(y[0]-t)-1],
                             [0., 1.], [0.], rtol=1e-11, atol=1e-13)
        assert solution.success
        numerical_shift = float(solution.y[0, -1] - 1)
        assert residual < 1e-12
        assert abs(numerical_shift - analytic_shift) < 1e-8
        temporal.append({'diffusivity': diffusion, 'max_pde_residual': residual,
                         'baseline_mean_T': 1., 'baseline_variance_T': 1.,
                         'force_u': -1., 'analytic_shift': analytic_shift,
                         'numerical_shift': numerical_shift,
                         'baseline_mass_T': float(np.exp(gamma))})

    diffusion, kappa = .1, .25
    rotation = np.array([[0., -1.], [1., 0.]])
    actions = {'A': np.array([-1., 0.]), 'B': np.array([0., -1.])}
    assert np.linalg.norm(actions['A']) == np.linalg.norm(actions['B']) == 1.
    covariance_T = (diffusion/kappa + (1-diffusion/kappa)*np.exp(-2*kappa)) * np.eye(2)
    assert abs(covariance_T[0, 0] - 1.) > .1
    autonomous = []
    for omega in [-2., 2.]:
        generator = -kappa*np.eye(2) + omega*rotation
        integral = np.expm1(complex(-kappa, omega))/complex(-kappa, omega)
        mean_map = np.array([[integral.real, -integral.imag],
                             [integral.imag, integral.real]])
        entries = {}
        for name, force in actions.items():
            def moment_rhs(t, y):
                mean, covariance = y[:2], y[2:].reshape(2, 2)
                return np.concatenate([generator@mean + force,
                    (generator@covariance + covariance@generator.T + 2*diffusion*np.eye(2)).ravel()])
            solution = solve_ivp(moment_rhs, [0., 1.],
                                 np.concatenate([np.zeros(2), np.eye(2).ravel()]),
                                 rtol=1e-11, atol=1e-13)
            assert solution.success
            mean = mean_map@force
            numeric_mean = solution.y[:2, -1]
            numeric_covariance = solution.y[2:, -1].reshape(2, 2)
            mean_error = float(np.max(np.abs(mean-numeric_mean)))
            covariance_error = float(np.max(np.abs(covariance_T-numeric_covariance)))
            assert mean_error < 1e-8 and covariance_error < 1e-8
            harm = float(np.exp(gamma)*ndtr(mean[0]/np.sqrt(covariance_T[0, 0])))
            entries[name] = {'force': force.tolist(), 'analytic_mean_T': mean.tolist(),
                             'numeric_mean_T': numeric_mean.tolist(),
                             'mean_error': mean_error, 'covariance_error': covariance_error,
                             'absolute_tail_harm': harm}
        # Direct PDE calculation in two dimensions: skew part has zero radial flux divergence.
        xy = np.array([[x, y] for x in grid_x for y in grid_x])
        max_residual = 0.
        for t in grid_t:
            variance = diffusion/kappa + (1-diffusion/kappa)*np.exp(-2*kappa*t)
            ds = -2*kappa*variance + 2*diffusion
            radius2 = np.sum(xy*xy, axis=1)
            density = np.exp(gamma*t-radius2/(2*variance))/(2*np.pi*variance)
            dt_density = (gamma-ds/variance+radius2*ds/(2*variance**2))*density
            velocity = xy@generator.T
            divergence_flux = (np.trace(generator)-np.sum(velocity*xy, axis=1)/variance)*density
            laplacian = (radius2/variance**2-2/variance)*density
            rhs = -divergence_flux + diffusion*laplacian + gamma*density
            max_residual = max(max_residual, float(np.max(np.abs(dt_density-rhs))))
        assert max_residual < 1e-12
        preferred = min(entries, key=lambda name: entries[name]['absolute_tail_harm'])
        autonomous.append({'omega': omega, 'actions': entries,
                           'baseline_mean_T': [0., 0.], 'baseline_mass_T': float(np.exp(gamma)),
                           'covariance_T': covariance_T.tolist(), 'max_pde_residual': max_residual,
                           'preferred_action': preferred})
    assert autonomous[0]['preferred_action'] == 'B'
    assert autonomous[1]['preferred_action'] == 'A'
    result = {'status': 'PASS_SYNTHETIC_ONLY', 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
              'wall_seconds': time.perf_counter()-tick, 'gamma': gamma,
              'time_dependent': temporal, 'autonomous': autonomous,
              'moment_ivp_solves': 6, 'fits': 0, 'biological_values_read': 0,
              'scope': 'Baseline-only snapshots; unrestricted time drift / autonomous nongradient drift. '
                       'Known interventions or linked transitions can distinguish these worlds. '
                       'Stipulated forces and tail burden are not measured drugs or efficacy.'}
    (OUT / 'SNAPSHOT_WITNESS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
