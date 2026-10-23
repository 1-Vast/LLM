"""Pre-access tests for actual leakage, symmetry and gem contrast risks."""
import importlib.util
from pathlib import Path
import numpy as np

spec = importlib.util.spec_from_file_location('predictor', Path(__file__).with_name('predict.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

rng = np.random.default_rng(20261023)
a, b = rng.normal(size=(12, 4, 3)), rng.normal(size=(12, 4, 3))
f = p.design(a, b)
swap = p.design(b, a)
for key in f:
    np.testing.assert_allclose(f[key], swap[key], rtol=0, atol=1e-14)
np.testing.assert_allclose(f['diagonal'], (a*b).mean(axis=1))
y = rng.normal(size=(12, 3))
train, assess = np.arange(8), np.arange(8, 12)
for name in p.MODELS:
    first = p.fit(name, f, y, train, assess, .1)
    poisoned = y.copy(); poisoned[assess] = np.nan
    second = p.fit(name, f, poisoned, train, assess, .1)
    np.testing.assert_array_equal(first, second)
    assert np.isfinite(first).all()
print('PASS: pair-swap, gem-averaged product, heldout-label poisoning; no biological files opened')
