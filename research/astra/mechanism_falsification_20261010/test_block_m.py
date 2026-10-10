"""Engine checks for block M (synthetic data; no L1000 values)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import falsify as F  # noqa: E402


def synthetic(n_class=12, per_class=8, n_opt=6, k=10, seed=0, noise=1.0):
    rng = np.random.default_rng(seed)
    protos = rng.normal(0, 1.5, size=(n_class, n_opt, k))
    protos[: n_class // 3] = 0.0  # a third of the classes are inert
    labels, Z = [], []
    for c in range(n_class):
        for _ in range(per_class):
            lam = max(0.0, rng.normal(1, 0.3))
            Z.append(lam * protos[c] + rng.normal(0, noise, size=(n_opt, k)))
            labels.append(str(c))
    return np.array(Z), np.array(labels), protos


def build(Z, labels, ref, alpha=0.1, mode="absolute", n_bins=1):
    data = F.class_prototypes(Z, labels, ref, None, 0.0)
    models = [F.HypothesisModel(name=c, proto=p, n=n, kind="data") for c, (p, n) in sorted(data.items())]
    ref_idx = np.where(ref)[0]
    own = np.zeros((len(ref_idx),) + Z.shape[1:])
    bucket = []
    for j, i in enumerate(ref_idx):
        mates = ref & (labels == labels[i])
        mates[i] = False
        own[j] = Z[mates].mean(axis=0)
        bucket.append(F.bucket_of(int(mates.sum()), "data"))
    noise = F.NoiseModel(var=np.ones(Z.shape[1:]), tau2=0.09)
    names = [m.name for m in models]
    cal = F.Calibration(Z=Z[ref_idx], own_proto=own, bucket=np.array(bucket), noise=noise,
                        P=np.stack([m.proto for m in models]), cal_class=np.array([names.index(labels[i]) for i in ref_idx]),
                        mode=mode, n_bins=n_bins)
    resid = np.stack([Z[ref_idx][:, o] - own[:, o] for o in range(Z.shape[1])])
    return F.Falsifier(models, cal, resid, alpha, np.arange(Z.shape[1]))


def test_score_paths_agree():
    Z, labels, _ = synthetic()
    ref = np.zeros(len(Z), bool)
    ref[::2] = True
    fz = build(Z, labels, ref)
    z = Z[1]
    opts = [0, 3]
    hyp = np.arange(len(fz.models))
    Q, b, A = fz.stats(z, opts, hyp)
    s1, _ = F.score_from_stats(Q, b, A, fz.noise.tau2, len(opts))
    o = np.array(opts)
    s2, _ = F.score_batch(np.repeat(z[o][None], len(hyp), 0), fz.P[:, o], fz.noise, o)
    assert np.allclose(s1, s2)


def test_conformal_coverage_on_correct_model():
    Z, labels, _ = synthetic(per_class=16, seed=1)
    ref = np.zeros(len(Z), bool)
    ref[::2] = True
    fz = build(Z, labels, ref, alpha=0.1)
    q = np.where(~ref)[0]
    cov = []
    for i in q:
        res = fz.run(Z[i], list(range(Z.shape[1])), "fixed", 2, labels[i], seed=int(i))
        cov.append(labels[i] in res.surviving[-1] if res.surviving else True)
    # 96 queries; nominal 0.9 (leave-self-out prototypes make it slightly conservative)
    assert np.mean(cov) >= 0.82


def test_falsify_policy_not_worse_than_random_on_sets():
    Z, labels, _ = synthetic(per_class=16, seed=2, n_opt=8)
    ref = np.zeros(len(Z), bool)
    ref[::2] = True
    fz = build(Z, labels, ref)
    q = np.where(~ref)[0][:60]
    sizes = {}
    for pol in ("falsify", "random"):
        s = []
        for i in q:
            res = fz.run(Z[i], list(range(Z.shape[1])), pol, 1, labels[i], seed=int(i))
            s.append(len(res.surviving[-1]))
        sizes[pol] = np.mean(s)
    assert sizes["falsify"] <= sizes["random"] + 0.5


def test_sealed_tier_refused_before_freeze(tmp_path, monkeypatch):
    import study as S
    if (S.HERE / "FREEZE.json").exists():
        pytest.skip("freeze exists; the sealed tier is open by design")
    with pytest.raises(SystemExit, match="TIER_SEALED"):
        S.load_tier("sealed")


@pytest.mark.parametrize("mode,n_bins", [("relative", 1), ("relative", 2)])
def test_relative_scores_cover_active_classes(mode, n_bins):
    """Relative scores keep coverage for drugs of responsive classes, not only on average."""
    Z, labels, protos = synthetic(per_class=24, seed=3)
    ref = np.zeros(len(Z), bool)
    ref[::2] = True
    fz = build(Z, labels, ref, alpha=0.1, mode=mode, n_bins=n_bins)
    active = {str(c) for c in range(len(protos)) if np.abs(protos[c]).sum() > 0}
    q = np.where(~ref)[0]
    cov_active = []
    for i in q:
        res = fz.run(Z[i], list(range(Z.shape[1])), "fixed", 2, labels[i], seed=int(i))
        if labels[i] in active:
            cov_active.append(labels[i] in res.surviving[-1] if res.surviving else True)
    assert np.mean(cov_active) >= 0.8
    cal, _ = fz.cal.scores((0, 1), np.arange(len(fz.models)))
    assert all((v >= 0).all() for v in cal.values())  # own LOO score minus a minimum that includes it


def test_episode_calibration_covers_adaptive_design():
    """Calibrating the whole falsify procedure keeps coverage when the design adapts to the data."""
    Z, labels, _ = synthetic(per_class=24, seed=4, n_opt=8)
    ref = np.zeros(len(Z), bool)
    ref[::2] = True
    fz = build(Z, labels, ref, alpha=0.1, mode="relative", n_bins=2)
    sc = F.episode_calibration(fz, "falsify", 3, seed=0)
    assert len(sc.tables) == 3 and sc.n_rows[0] == int(ref.sum())
    q = np.where(~ref)[0]
    cov = []
    for i in q:
        res = fz.run(Z[i], list(range(Z.shape[1])), "falsify", 3, labels[i], seed=int(i), step_cal=sc, stop_on_single=False)
        cov.append(labels[i] in res.surviving[-1])
    assert np.mean(cov) >= 0.8
