"""Analytic two-dimensional operation witness; no biology or foreign imports."""
import json
import pathlib

def target(theta):
    x, y = theta
    return (-y, x)

def detached_target_gradient(theta):
    x, y = theta
    a, b = target(theta)
    return (x - a, y - b)

def ordinary_stateful_update(theta, step):
    # A standard optimizer may compute precisely the same vector field.
    x, y = theta
    return (x - step * (x + y), y - step * (y - x))

points = [(0., 0.), (1., 0.), (0., 1.), (2., -3.)]
for theta in points:
    g = detached_target_gradient(theta)
    updated = tuple(t - 0.1 * v for t, v in zip(theta, g))
    assert updated == ordinary_stateful_update(theta, 0.1)

# d(g_x)/dy = +1 and d(g_y)/dx = -1: no twice-differentiable
# static scalar potential has this exact gradient on an open set.
result = {
    'target': 'T(theta)=(-theta_y,theta_x)',
    'detached_gradient': '(theta_x+theta_y,theta_y-theta_x)',
    'cross_partials': {'d_gx_d_y': 1, 'd_gy_d_x': -1},
    'static_smooth_scalar_gradient_equivalent': False,
    'ordinary_stop_gradient_target_loss_equivalent': True,
    'ordinary_stateful_vector_update_equivalent': True,
    'checked_points': len(points), 'checks': 'PASS',
    'scope': 'Exact limited operation boundary, not biological performance or a new mechanism.',
}
root = pathlib.Path(__file__).resolve().parents[3]
(root / 'log/20261023/mechanism_reentry/critic/TARGET_FIELD_CHECK.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
