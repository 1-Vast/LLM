"""Dry run of the S1 machinery on fabricated mono records with planted context structure."""
import json

import numpy as np
import pandas as pd

from research.astra.mono_pretraining_20261005 import common as cm
from research.astra.mono_pretraining_20261005 import run_s1 as r1
from research.astra.mono_pretraining_20261005.bilinear import MonoConfig


def fabricate(n_cells=260, n_drugs=12, n_j=40, seed=0):
    g = np.random.default_rng(seed)
    sidms = [f"SIDM{i:05d}" for i in range(n_cells)]
    z = g.normal(size=(n_cells, 14))
    W = g.normal(size=(14, 4)) / 4
    E = g.normal(size=(n_drugs, 4))
    beta = g.normal(size=n_drugs)
    tissues = np.array(["Breast", "Large Intestine", "Pancreas", "Lung", "Skin"])[g.integers(0, 5, n_cells)]
    jl = list(range(n_j))
    tissues[jl] = np.array(["Breast", "Large Intestine", "Pancreas"])[np.arange(n_j) % 3]
    fold = {sidms[i]: (["Breast", "Colon", "Pancreas"][i % 3], (i // 3) % 5 if i < n_j - 9 else "E") for i in jl}
    rows = []
    for c in range(n_cells):
        for d in range(n_drugs):
            y = beta[d] + (z[c] @ W) @ E[d] + g.normal(0, 0.3)
            rows.append(dict(sidm=sidms[c], crow=c, drow=d, y_rel=y, eligible_primary_pretrain=c >= n_j,
                             NOT_ELIGIBLE_target_line_own_mono_diagnostic_only=c < n_j,
                             proposed_mono_split="val" if c % 5 == 0 else "train"))
    m = pd.DataFrame(rows)
    m["jaaks_line"] = m.sidm.isin(fold)
    m["fold"] = m.sidm.map(lambda s: fold[s][1] if s in fold else None)
    cells = pd.DataFrame({"cmp_tissue": tissues}, index=sidms)
    lin = {t: i for i, t in enumerate(sorted(set(tissues)))}
    return dict(sidms=sidms, z=z, row={s: i for i, s in enumerate(sidms)}, fold=fold, m=m, cells=cells,
                lineage=np.array([lin[t] for t in tissues]), n_drugs=n_drugs + 2, n_mapped=n_drugs)


def test_pretrain_perm_and_g1_on_planted_structure(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "RESULTS", tmp_path)
    monkeypatch.setattr(r1, "PARAMS_DIR", tmp_path / "mono_params")
    monkeypatch.setattr(cm, "N_PERM", 2)
    P = fabricate()
    (tmp_path / "mono_params").mkdir()
    cfg = MonoConfig(steps=400)
    for k in cm.FOLDS:
        pool = r1.train_pool(P, k)
        held = P["m"][P["m"].jaaks_line & (P["m"].fold == k)]
        assert not set(pool.sidm) & set(held.sidm)                      # held-out lines never in that fold's training
        for arm, kw in [("pre", dict(seed=1))] + [(f"dperm{i}", dict(seed=5 + i, drug_perm_seed=i)) for i in range(2)] \
                + [(f"cperm{i}", dict(seed=9 + i, cell_perm_seed=i)) for i in range(2)]:
            p = r1.fit_arm(P, pool, cfg, **kw)
            np.savez(tmp_path / "mono_params" / f"F{k}_{arm}.npz", **p)
    px = r1.train_pool(P, None)
    assert not px.jaaks_line.any()
    r1.run_g1(P, lambda m: None)
    g1 = json.loads((tmp_path / "s1_g1.json").read_text())
    arms = g1["arms"]
    assert arms["pre"]["within_cell"] > arms["drug_mean"]["within_cell"] + 0.02
    assert arms["pre"]["per_drug"] > max(arms["dperm0"]["per_drug"], arms["cperm0"]["per_drug"])
    assert "passed" in g1["G1"]
