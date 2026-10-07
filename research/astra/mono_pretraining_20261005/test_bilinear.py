"""Synthetic contracts for the shared head (software correctness only; says nothing about biology)."""
import numpy as np

from research.astra.mono_pretraining_20261005.bilinear import (
    ComboConfig, MonoConfig, finetune_combo, init_params, predict_combo, predict_mono, pretrain_mono)


def _world(seed=0, n_cells=300, n_drugs=12, f=14, k=4, noise=0.3):
    g = np.random.default_rng(seed)
    z = g.normal(size=(n_cells, f))
    W = g.normal(size=(f, k)) / np.sqrt(f)
    E = g.normal(size=(n_drugs, k))
    beta = g.normal(size=n_drugs)
    return g, z, W, E, beta, noise


def _mono_records(g, z, W, E, beta, noise):
    cells, drugs = np.meshgrid(np.arange(len(z)), np.arange(len(E)), indexing="ij")
    cells, drugs = cells.ravel(), drugs.ravel()
    y = beta[drugs] + ((z @ W)[cells] * E[drugs]).sum(1) + g.normal(0, noise, len(cells))
    return cells, drugs, y


def test_mono_recovers_planted_structure_on_heldout_cells():
    g, z, W, E, beta, noise = _world()
    tr, te = np.arange(240), np.arange(240, 300)
    cells, drugs, y = _mono_records(g, z[tr], W, E, beta, noise)
    p = pretrain_mono(z[tr], cells, drugs, y, len(E), MonoConfig(steps=800), seed=1)
    cc, dd, yy = _mono_records(g, z[te], W, E, beta, 0.0)
    assert np.corrcoef(predict_mono(p, z[te], cc, dd), yy)[0, 1] > 0.9


def test_invariant_features_symmetry_and_rotation_contract():
    p = init_params(14, 6, 4, seed=3)
    z = np.random.default_rng(2).normal(size=(5, 14))
    c, a, b = np.zeros(1, int), np.array([1]), np.array([4])
    sym = dict(p, features="invariant", theta=np.array([0.7, -0.4, 0.0]))
    assert np.allclose(predict_combo(sym, z, c, a, b), predict_combo(sym, z, c, b, a))
    anti = dict(p, features="invariant", theta=np.array([0.0, 0.0, 1.3]))
    assert np.allclose(predict_combo(anti, z, c, a, b), -predict_combo(anti, z, c, b, a))
    Q, _ = np.linalg.qr(np.random.default_rng(4).normal(size=(4, 4)))
    rot = dict(sym, W=sym["W"] @ Q, E=sym["E"] @ Q)
    assert np.allclose(predict_combo(sym, z, c, a, b), predict_combo(rot, z, c, a, b))   # basis-free
    el = dict(p, features="elementwise", theta=np.random.default_rng(1).normal(size=12))
    elr = dict(el, W=el["W"] @ Q, E=el["E"] @ Q)
    assert not np.allclose(predict_combo(el, z, c, a, b), predict_combo(elr, z, c, a, b))  # coordinate-wise is not


def _combo_task(seed, planted):
    g, z, W, E, beta, noise = _world(seed)
    th = np.array([0.8, -0.5, 0.0])

    def make(cells, n):
        c = g.choice(cells, n)
        a, b = g.integers(0, len(E), n), g.integers(0, len(E), n)
        y = predict_combo({"W": W, "E": E, "beta": np.zeros(len(E)), "theta": th, "features": "invariant"}, z, c, a, b) if planted \
            else g.normal(size=n)
        return c, a, b, y + g.normal(0, 0.1, n)

    return g, z, W, E, beta, make


def test_pretraining_helps_when_combo_depends_on_the_same_structure():
    g, z, W, E, beta, make = _combo_task(5, planted=True)
    tr = np.arange(240)
    cells, drugs, y = _mono_records(g, z[tr], W, E, beta, 0.3)
    pre = pretrain_mono(z[tr], cells, drugs, y, len(E), MonoConfig(steps=800), seed=1)
    scratch = init_params(14, len(E), 4, seed=1)
    c, a, b, yc = make(np.arange(240, 244), 40)             # sparse combination history: 4 cells, 40 rows
    ct, at, bt, yt = make(np.arange(250, 300), 400)
    cfg = ComboConfig(features='invariant', steps=300, lr=0.02, l2_theta=0.1, l2_init=1.0)
    scores = {}
    for name, init in (("pre", pre), ("scratch", scratch)):
        m = finetune_combo(init, z, c, a, b, yc - yc.mean(), cfg)
        scores[name] = np.corrcoef(predict_combo(m, z, ct, at, bt), yt)[0, 1]
    assert scores["pre"] > scores["scratch"] + 0.15, scores


def test_pretraining_does_not_help_when_combo_is_unrelated():
    g, z, W, E, beta, make = _combo_task(7, planted=False)
    tr = np.arange(240)
    cells, drugs, y = _mono_records(g, z[tr], W, E, beta, 0.3)
    pre = pretrain_mono(z[tr], cells, drugs, y, len(E), MonoConfig(steps=800), seed=1)
    c, a, b, yc = make(np.arange(240, 244), 40)
    ct, at, bt, yt = make(np.arange(250, 300), 400)
    m = finetune_combo(pre, z, c, a, b, yc - yc.mean(), ComboConfig(features='invariant', steps=300, lr=0.02, l2_theta=1.0, l2_init=1.0))
    assert abs(np.corrcoef(predict_combo(m, z, ct, at, bt), yt)[0, 1]) < 0.2


def test_finetune_is_deterministic():
    g, z, W, E, beta, make = _combo_task(9, planted=True)
    c, a, b, yc = make(np.arange(240, 244), 40)
    p1 = init_params(14, len(E), 4, seed=1)
    m1 = finetune_combo(p1, z, c, a, b, yc, ComboConfig(features='invariant', steps=50))
    m2 = finetune_combo(dict(p1), z, c, a, b, yc, ComboConfig(features='invariant', steps=50))
    assert all(np.array_equal(m1[k], m2[k]) for k in ("W", "E", "theta"))


def test_zero_residual_gives_zero_head():
    g, z, W, E, beta, make = _combo_task(11, planted=True)
    c, a, b, _ = make(np.arange(240, 244), 40)
    m = finetune_combo(init_params(14, len(E), 4, seed=1), z, c, a, b, np.zeros(40), ComboConfig(features='invariant', steps=50))
    assert np.allclose(m["theta"], 0.0, atol=1e-9)


def test_potency_features_carry_drug_level_information_only_when_pretrained():
    g, z, W, E, beta, _ = _world(13)
    n = 400
    a, b = g.integers(0, len(E), n), g.integers(0, len(E), n)
    c = g.integers(0, 50, n)
    sig = lambda x: 1 / (1 + np.exp(-x / 2))
    y = 2.0 * (sig(beta[a]) * sig(beta[b])) - 1.0 + g.normal(0, 0.05, n)       # depends on drug-level potency only
    pre = {"W": W, "E": E * 0, "beta": beta}
    scr = init_params(14, len(E), 4, seed=1)
    cfg = ComboConfig(features="p3", steps=300, lr=0.05, l2_theta=0.01, l2_init=1.0)
    s_pre = predict_combo(finetune_combo(pre, z, c, a, b, y - y.mean(), cfg), z, c, a, b)
    s_scr = predict_combo(finetune_combo(scr, z, c, a, b, y - y.mean(), cfg), z, c, a, b)
    assert np.corrcoef(s_pre, y)[0, 1] > 0.8 and abs(np.corrcoef(s_scr, y)[0, 1]) < 0.3 if np.ptp(s_scr) > 0 else True
