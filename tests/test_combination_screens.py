"""Research scope: combination-screen builders, vault, and parity of promoted with frozen research code.

File summary
- Path: tests/test_combination_screens.py
- Purpose: the promoted dataset builder and replay reproduce the frozen research implementation
  of certified discovery; the ALMANAC builder and vault refuse by name on a synthetic release.
- Core points: the synthetic-release tests need pandas only; the O'Neil parity tests need the
  local O'Neil supplement (data/raw/oneil2026_qualification) and fail, not skip, without it.
- Depends on: numpy, pandas, tools.datasets.combination_screens, tools.evaluation.discovery_replay,
  research.certified_discovery (frozen comparison target).
"""
from __future__ import annotations

import json
import random
import zipfile

import numpy as np
import pytest

from maestro import certification as promoted
from research.certified_discovery import certify as frozen_certify
from research.certified_discovery import screens as frozen_screens
from research.certified_discovery.world import TransferWorld
from tools.datasets import combination_screens as screens
from tools.evaluation import discovery_replay
from virtual_cell.combination_world import CombinationWorld


def _fake_release(path):
    header = ("COMBODRUGSEQ,SCREENER,STUDY,TESTDATE,PLATE,PANELNBR,CELLNBR,PREFIX1,NSC1,SAMPLE1,CONCINDEX1,CONC1,"
              "CONCUNIT1,PREFIX2,NSC2,SAMPLE2,CONCINDEX2,CONC2,CONCUNIT2,PERCENTGROWTH,PERCENTGROWTHNOTZ,TESTVALUE,"
              "CONTROLVALUE,TZVALUE,EXPECTEDGROWTH,SCORE,VALID,PANEL,CELLNAME")
    rows, seq = [header], 0
    for cell in ("A", "B"):
        for d1, d2 in ((740, 750), (740, 752), (750, 752)):
            for i in (1, 2, 3):
                for j in (1, 2, 3):
                    seq += 1
                    score = 15.0 if (d1, d2, cell) == (740, 750, "A") else 1.0
                    rows.append(f"{seq},FG,s,d,p,1,1,S,{d1},1,{i},{i}e-6,M,S,{d2},1,{j},{j}e-6,M,40,40,1,1,1,55,{score},Y,P,{cell} ")
        for d in (740, 750, 752):
            seq += 1
            rows.append(f"{seq},FG,s,d,p,1,1,S,{d},1,1,1e-6,M,S,,,0,,,60,60,1,1,1,,,Y,P,{cell} ")
        seq += 1
        rows.append(f"{seq},FG,s,d,p,1,1,S,740,1,0,1e-6,M,S,,,0,,,0,0,1,1,1,,,Y,P,{cell} ")   # undocumented pattern
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ComboDrugGrowth_Nov2017.csv", "\n".join(rows) + "\n")


def test_almanac_builder_and_vault(tmp_path):
    source = tmp_path / "release.zip"
    _fake_release(source)
    with pytest.raises(screens.VaultRefusal) as sealed:
        screens.build_almanac({}, source=source)
    assert sealed.value.code == "VAULT_SEALED"
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("v1")
    freeze = tmp_path / "freeze.json"
    freeze.write_text(json.dumps({"files": {"frozen.txt": screens.sha256(frozen)}}))
    ticket = screens.open_vault(freeze, tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    frozen.write_text("v2")
    with pytest.raises(screens.VaultRefusal) as changed:
        screens.open_vault(freeze, tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    assert changed.value.code == "FREEZE_MISMATCH"
    names = tmp_path / "names.txt"
    names.write_text("740\tMethotrexate\n750\tBusulfan\n752\tThioguanine\n752\t6-Thioguanine\n")
    library = screens.build_almanac(ticket, source=source, names_path=names)
    assert library.screen.drugs == ("Methotrexate", "Busulfan", "Thioguanine")
    assert int(library.hits.sum()) == 1 and np.all(library.cost_points == 9)
    assert library.provenance["excluded_undocumented_rows"] == 2
    assert np.allclose(library.screen.mono_mean, 0.4)
    screens.save_library(library, tmp_path / "lib.npz")
    again = screens.load_library(tmp_path / "lib.npz")
    assert np.array_equal(again.screen.y, library.screen.y) and again.days_per_round == 3.0


def test_promoted_certificate_equals_the_frozen_research_certificate():
    rng = np.random.default_rng(0)
    for trial in range(200):
        n = int(rng.integers(5, 60))
        shortlist = list(range(n))
        scores = rng.normal(size=n).round(1)                       # ties included on purpose
        audit = sorted(random.Random(trial).sample(shortlist, int(rng.integers(0, n))))
        hits = (rng.random(len(audit)) < 0.4).tolist()
        new = promoted.certify(shortlist, scores, audit, hits, alpha=0.2, delta=0.1)
        old = frozen_certify.certify(np.array(shortlist), scores, np.array(audit, int), np.array(hits, bool), alpha=0.2, delta=0.1)
        assert list(new.nominated) == old.nominated.tolist() and new.yield_bound == old.yield_bound
        assert new.refusal == old.refusal


@pytest.fixture(scope="module")
def oneil():
    return screens.build_oneil()


def test_promoted_oneil_builder_reproduces_the_frozen_library(oneil, tmp_path):
    frozen = frozen_screens.build_oneil(force=True, cache=tmp_path / "frozen_rebuild.npz")
    s = oneil.screen
    assert s.drugs == frozen.drugs and s.lines == frozen.lines
    assert np.array_equal(s.a, frozen.a) and np.array_equal(s.b, frozen.b) and np.array_equal(s.c, frozen.c)
    assert np.allclose(s.y, frozen.y) and np.allclose(s.expected, frozen.expected)
    assert np.allclose(s.mono_mean, frozen.mono_mean) and np.allclose(s.mono_top, frozen.mono_top)
    assert int(oneil.hits.sum()) == 749 and len(s.y) == 22737


@pytest.mark.parametrize("line", [0, 17, 38])
def test_promoted_world_matches_the_frozen_world_on_oneil(oneil, line):
    frozen_library = frozen_screens.load_library(frozen_screens.CACHE / "oneil_v1.npz")
    new, old = CombinationWorld(oneil.screen, line), TransferWorld(frozen_library, line)
    assert np.allclose(new.X_target, old.X_target) and np.allclose(new.prior_target, old.prior_target)
    # The frozen fit (scipy L-BFGS-B) stops early on the flat line-variance direction; the promoted
    # Nelder-Mead reaches an equal or better likelihood with the line variance at its lower bound.
    frozen_point = np.log([old.s_line, old.s_drug, old.s_noise])
    promoted_point = np.log([new.s_line, new.s_drug, new.s_noise])
    assert new.negative_log_likelihood(promoted_point) <= new.negative_log_likelihood(frozen_point) + 1e-6
    assert new.s_drug == pytest.approx(old.s_drug, rel=0.02) and new.s_noise == pytest.approx(old.s_noise, rel=0.02)
    measured = np.arange(0, 45, 3)
    values = oneil.screen.y[new.rows[measured]]
    assert np.corrcoef(new.posterior(measured, values)[0], old.posterior(measured, values)[0])[0, 1] > 0.9999


def test_promoted_replay_reproduces_the_frozen_development_hits(oneil, tmp_path):
    path = tmp_path / "oneil.npz"
    screens.save_library(oneil, path)
    spec = {"budget_fraction": 0.1, "rounds": 4, "kappa": 2, "alpha": 0.2, "delta": 0.1, "audit_seeds": 2, "random_seeds": 2}
    records = [r for line in range(len(oneil.screen.lines))
               for r in discovery_replay.replay_line((str(path), line, spec, ("history", "wm_full", "wm_static")))]
    totals = {arm: sum(r["exploit"]["hits"] for r in records if r["arm"] == arm) for arm in ("history", "wm_full", "wm_static")}
    # Frozen development record (results/dev_20261003_v2): history 401, wm_full 475, wm_static 407.
    assert totals["history"] == 401
    assert abs(totals["wm_full"] - 475) <= 3 and abs(totals["wm_static"] - 407) <= 3
