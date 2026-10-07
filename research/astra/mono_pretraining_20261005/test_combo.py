"""Integration contracts for the combination pipeline on a synthetic release with planted structure."""
import numpy as np
import pandas as pd
import pytest

from research.astra.confirmation_campaign_20261004.design import campaign as cp
from research.astra.feedback_validation_20261003 import jaaks
from research.astra.mono_pretraining_20261005.bilinear import (
    ComboConfig, MonoConfig, init_params, pretrain_mono)
from research.astra.mono_pretraining_20261005.combo import Fitter, training_rows

LINES, DRUGS, F, K = 14, 10, 14, 4


def planted_release(path, seed=0, signal=1.0):
    g = np.random.default_rng(seed)
    W = g.normal(size=(F, K)) / np.sqrt(F)
    E = g.normal(size=(DRUGS, K))
    rows, zs = [], {}
    for tissue in ("Colon", "Pancreas"):
        ids = [str(1000 + 10 * jaaks.TISSUE_CODE[tissue] + i) for i in range(DRUGS)]
        pair = g.normal(0, 0.05, (DRUGS, DRUGS))
        for line in range(LINES):
            sidm = f"SIDM{jaaks.TISSUE_CODE[tissue]}{line:03d}"
            z = g.normal(size=F)
            zs[sidm] = z
            u = (z @ W) @ E.T * signal * 0.12
            for doublet in range(DRUGS // 2):
                barcode = f"{tissue[0]}{line:03d}{doublet:02d}"
                for j in (2 * doublet, 2 * doublet + 1):
                    for i in range(DRUGS):
                        if i == j:
                            continue
                        for conc in (0.1, 1.0):
                            d = 0.1 + pair[min(i, j), max(i, j)] + u[i] + u[j] + g.normal(0, 0.03)
                            rows.append({"BARCODE": barcode, "Tissue": tissue, "CELL_LINE_NAME": f"L{line}",
                                         "SIDM": sidm, "ANCHOR_ID": ids[i], "ANCHOR_NAME": f"D{i}", "ANCHOR_CONC": conc,
                                         "LIBRARY_ID": ids[j], "LIBRARY_NAME": f"D{j}", "LIBRARY_CONC": 4.0,
                                         "SYNERGY_DELTA_EMAX": d, "SYNERGY_OBS_EMAX": float(np.clip(0.6 - d, 0, 1)),
                                         "SYNERGY_RMSE": 0.05, "LIBRARY_RMSE": 0.05, "Synergy": bool(d >= 0.2)})
    pd.DataFrame(rows).to_csv(path, index=False)
    return W, E, zs


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("planted")
    W, E, zs = planted_release(d / "r.csv")
    ticket = {"freeze_sha256": "TEST", "data_sha256": cp.sha256_file(d / "r.csv")}
    panels, _, cand = jaaks.build_panels(ticket, d / "r.csv")
    tissues = cp.build_tissues(panels, cand)
    sidms = sorted(zs)
    line_row = {s: i for i, s in enumerate(sidms)}
    z = np.stack([zs[s] for s in sidms])
    return dict(W=W, E=E, tissues=tissues, line_row=line_row, z=z, sidms=sidms)


def _drug_index(T):
    ids = sorted({x for p in T.pairs for x in p})
    return {d: i for i, d in enumerate(ids)}


def _mono(world, drug_index, seed=1, perm=False):
    g = np.random.default_rng(seed)
    n_cells = 200
    zc = g.normal(size=(n_cells, F))
    cell, drug = np.meshgrid(np.arange(n_cells), np.arange(len(drug_index)), indexing="ij")
    cell, drug = cell.ravel(), drug.ravel()
    y = ((zc @ world["W"])[cell] * world["E"][drug]).sum(1) + g.normal(0, 0.2, len(cell))
    if perm:
        drug = np.random.default_rng(5).permutation(len(drug_index))[drug]
    return pretrain_mono(zc, cell, drug, y, len(drug_index), MonoConfig(steps=500), seed=seed)


def _score_corr(world, tissue, init, cfg, hist_n=4):
    T = world["tissues"][tissue]
    di = _drug_index(T)
    fit = Fitter(world["z"], di, world["line_row"], np.ones(len(di), bool))
    lines = sorted(T.present_lines)
    target, hist = lines[-1], lines[:hist_n]
    H = cp.restrict(T, hist)
    tg = cp.make_target(T, H, target, "SV", allowed_history=lines[:-1], forbidden=[target])
    truth = cp.truth_of(T, tg)
    params = fit.fit("arm", init(di), H, cfg)
    score = fit.target_score(params, T, tg)
    tv = (truth["y_s"] + truth["y_v"]) / 2
    return np.corrcoef(score, tv)[0, 1], np.corrcoef(tg.q["S_both"], tv)[0, 1], tg, fit, H, di


def test_pretrained_beats_scratch_and_baseline_when_structure_is_shared(world):
    cfg = ComboConfig(features='invariant', steps=200, lr=0.02, l2_theta=0.3, l2_init=3.0)
    pre, base, *_ = _score_corr(world, "Colon", lambda di: _mono(world, di), cfg)
    scr, _, *_ = _score_corr(world, "Colon", lambda di: init_params(F, len(di), K, 1), cfg)
    assert pre > scr + 0.1 and pre > base, (pre, scr, base)


def test_history_never_contains_target_and_rows_exclude_own_line_prior(world):
    T = world["tissues"]["Colon"]
    lines = sorted(T.present_lines)
    H = cp.restrict(T, lines[:4])
    di = _drug_index(T)
    rows = training_rows(H, di, world["line_row"], np.ones(len(di), bool))
    assert lines[-1] not in set(rows["line"])
    for sidm in lines[:4]:
        assert abs(rows["y"][rows["line"] == sidm].mean()) < 1e-9 and abs(rows["y"].std() - 1) < 0.5          # centred within line


def test_target_outcome_poisoning_changes_nothing(world):
    cfg = ComboConfig(features='invariant', steps=60)
    a, _, tg, fit, H, di = _score_corr(world, "Pancreas", lambda di: init_params(F, len(di), K, 1), cfg)
    T2 = world["tissues"]["Pancreas"]
    import copy
    T3 = copy.deepcopy(T2)
    li = T3.lines.index(tg.sidm)
    for role in T3.arrays:
        for k in T3.arrays[role]:
            m = T3.c == li
            T3.arrays[role][k][m] = ~T3.arrays[role][k][m] if T3.arrays[role][k].dtype == bool else -T3.arrays[role][k][m]
    tg3 = cp.make_target(T3, cp.restrict(T3, sorted(H.present_lines)), tg.sidm, "SV",
                         allowed_history=sorted(H.present_lines), forbidden=[tg.sidm])
    fit2 = Fitter(world["z"], di, world["line_row"], np.ones(len(di), bool))
    p2 = fit2.fit("arm", init_params(F, len(di), K, 1), cp.restrict(T3, sorted(H.present_lines)), cfg)
    s1 = fit.target_score(fit.fit("arm", init_params(F, len(di), K, 1), H, cfg), T2, tg)
    s2 = fit2.target_score(p2, T3, tg3)
    assert np.array_equal(s1, s2)


def test_wrong_drug_mapping_removes_the_gain(world):
    cfg = ComboConfig(features='invariant', steps=200, lr=0.02, l2_theta=0.3, l2_init=3.0)
    pre, base, *_ = _score_corr(world, "Colon", lambda di: _mono(world, di), cfg)
    perm, *_ = _score_corr(world, "Colon", lambda di: _mono(world, di, perm=True), cfg)
    assert perm < pre - 0.1, (perm, pre)


def test_unmapped_drugs_are_excluded_from_training_and_abstain_at_scoring(world):
    T = world["tissues"]["Colon"]
    di = _drug_index(T)
    mapped = np.ones(len(di), bool)
    mapped[2] = False
    lines = sorted(T.present_lines)
    H = cp.restrict(T, lines[:4])
    rows = training_rows(H, di, world["line_row"], mapped)
    assert 2 not in set(rows["anchor"]) and 2 not in set(rows["library"])
    tg = cp.make_target(T, H, lines[-1], "SV", allowed_history=lines[:-1], forbidden=[lines[-1]])
    fit = Fitter(world["z"], di, world["line_row"], mapped)
    params = fit.fit("a", init_params(F, len(di), K, 1), H, ComboConfig(steps=40))
    score = fit.target_score(params, T, tg)
    pairs = [T.pairs[i] for i in tg.rows]
    has = np.array([di[p[0]] == 2 or di[p[1]] == 2 for p in pairs])
    assert has.any() and np.array_equal(score[has], tg.q["S_both"][has])


def test_own_mono_arm_uses_observed_shifts(world):
    T = world["tissues"]["Colon"]
    di = _drug_index(T)
    lines = sorted(T.present_lines)
    H = cp.restrict(T, lines[:4])
    tg = cp.make_target(T, H, lines[-1], "SV", allowed_history=lines[:-1], forbidden=[lines[-1]])
    beta = np.zeros(len(di))
    own = {}
    for sidm in lines:
        z = world["z"][world["line_row"][sidm]]
        for d in range(len(di)):
            own[(sidm, d)] = float(((z @ world["W"]) * world["E"][d]).sum())
    init = dict(init_params(F, len(di), K, 1), beta=beta)
    fit = Fitter(world["z"], di, world["line_row"], np.ones(len(di), bool), own=own)
    cfg = ComboConfig(features="h3", steps=200, l2_init=1e4, l2_theta=0.3)
    params = fit.fit("own", init, H, cfg)
    truth = cp.truth_of(T, tg)
    tv = (truth["y_s"] + truth["y_v"]) / 2
    assert np.corrcoef(fit.target_score(params, T, tg), tv)[0, 1] > np.corrcoef(tg.q["S_both"], tv)[0, 1]
