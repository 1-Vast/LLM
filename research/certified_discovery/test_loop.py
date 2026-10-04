"""Contracts of the world model, the screens, the vault and the campaign loop.

File summary
- Path: research/certified_discovery/test_loop.py
- Purpose: the properties the confirmatory protocol relies on, checked on synthetic data.
- Core points: the target line's labels cannot move anything before feedback (no leakage); the
  Woodbury posterior equals a dense Gaussian process; every arm spends exactly the same budget
  in both terminal variants; the ALMANAC builder and the vault refuse by name; an LLM planner's
  bad reply or failure falls back with a named code instead of silently counting as a choice.
- Depends on: numpy, pandas, research.certified_discovery.
"""
from __future__ import annotations

import json
import zipfile
from types import SimpleNamespace

import numpy as np
import pytest

from research.certified_discovery import agent, screens
from research.certified_discovery.llm_agent import LLMPlannerArm, SpendBook
from research.certified_discovery.world import TransferWorld, WorldConfig


def synthetic_library(seed: int = 0, drugs: int = 9, lines: int = 6) -> screens.Library:
    rng = np.random.default_rng(seed)
    pairs = [(i, j) for i in range(drugs) for j in range(i + 1, drugs)]
    a = np.array([p[0] for p in pairs for _ in range(lines)], np.int32)
    b = np.array([p[1] for p in pairs for _ in range(lines)], np.int32)
    c = np.array([l for _ in pairs for l in range(lines)], np.int32)
    drug_effect = rng.normal(0, 4, size=(drugs, lines))
    pair_effect = rng.normal(0, 5, size=len(pairs)).repeat(lines)
    y = pair_effect + drug_effect[a, c] + drug_effect[b, c] + rng.normal(0, 3, size=a.size)
    mono = rng.random((drugs, lines))
    expected = 1 - (1 - mono[a, c]) * (1 - mono[b, c])
    return screens.Library("synthetic", tuple(f"d{i}" for i in range(drugs)), tuple(f"l{i}" for i in range(lines)),
                           a, b, c, y, np.full(a.size, 16, np.int32), expected, mono, mono ** 2, 3.0)


def test_target_labels_do_not_move_the_prior_or_the_fitted_variances():
    lib = synthetic_library()
    world = TransferWorld(lib, 2)
    scrambled = synthetic_library()
    target = scrambled.c == 2
    scrambled.y[target] = np.random.default_rng(9).normal(50, 20, size=target.sum())
    other = TransferWorld(scrambled, 2)
    assert np.allclose(world.prior_target, other.prior_target)
    assert np.allclose(world.prior_var_target, other.prior_var_target)
    assert (world.s_line, world.s_drug, world.s_noise) == pytest.approx((other.s_line, other.s_drug, other.s_noise))


def test_woodbury_posterior_equals_a_dense_gaussian_process():
    lib = synthetic_library(1)
    world = TransferWorld(lib, 0)
    measured = np.array([0, 3, 5, 8, 13])
    values = lib.y[world.rows[measured]]
    mean, var = world.posterior(measured, values)
    Z = world.Z_target
    K = Z @ world.A @ Z.T
    C = K[np.ix_(measured, measured)] + world.s_noise * np.eye(measured.size)
    dense_mean = world.prior_target + K[:, measured] @ np.linalg.solve(C, values - world.prior_target[measured])
    dense_var = np.diag(K) - np.einsum("ij,ji->i", K[:, measured], np.linalg.solve(C, K[measured])) + world.s_noise
    assert np.allclose(mean, dense_mean) and np.allclose(var, dense_var)


def test_feedback_switch_and_shuffle_control_change_what_they_should():
    lib = synthetic_library(2)
    full = TransferWorld(lib, 1)
    shuffled = TransferWorld(lib, 1, WorldConfig(shuffle_seed=5))
    nocontext = TransferWorld(lib, 1, WorldConfig(context=False))
    assert full.X_target.shape[1] > nocontext.X_target.shape[1]
    assert not np.allclose(full.X_target, shuffled.X_target)
    frozen = TransferWorld(lib, 1, WorldConfig(feedback=False))
    measured = np.array([0, 1, 2])
    assert np.allclose(frozen.posterior(measured, np.array([30.0, 30.0, 30.0]))[0], frozen.prior_target)
    assert not np.allclose(full.posterior(measured, np.array([30.0, 30.0, 30.0]))[0], full.prior_target)


def test_every_arm_spends_the_same_budget_in_both_terminal_variants():
    lib = synthetic_library(3)
    world = TransferWorld(lib, 4)
    spec = agent.CampaignSpec(budget_fraction=0.25, rounds=3, kappa=2, audit_seeds=3)
    arms = [agent.RandomArm(world.rows.size, 0), agent.HeuristicArm(world, "potency"), agent.HistoryArm(world),
            agent.WorldArm(world, "wm_full"), agent.MenuRandomArm(world, 0), agent.OracleArm(world)]
    budgets = set()
    for arm in arms:
        record = agent.run_campaign(lib, world, arm, spec, seed=1)
        budgets.add(record["budget"])
        assert record["exploit"]["hits"] <= record["budget"]
        for draw in record["certify"]:
            assert draw["audit"] == record["budget"] - record["batch"] * (spec.rounds - 1)
    assert len(budgets) == 1


class _StubClient:
    def __init__(self, replies):
        self.replies = list(replies)

    def complete_json(self, messages, max_tokens=None):
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply, SimpleNamespace(usage={"prompt_tokens": 100, "completion_tokens": 10})


def test_llm_planner_falls_back_by_name(tmp_path):
    lib = synthetic_library(4)
    world = TransferWorld(lib, 0)
    book = SpendBook(tmp_path / "spend.json", ceiling_usd=1.0)
    arm = LLMPlannerArm(world, _StubClient([{"chosen": [999]}, RuntimeError("down")]), book, batch=3, mode="blind")
    available = np.ones(world.rows.size, bool)
    first = arm.choose(available, np.array([], int), np.array([]), 3)
    second = arm.choose(available, np.array([], int), np.array([]), 3)
    assert first.size == 3 and second.size == 3
    assert [e["code"] for e in arm.events] == ["LLM_INVALID_SELECTION", "LLM_UNAVAILABLE"]
    assert json.loads((tmp_path / "spend.json").read_text())["calls"] == 1
    poor = SpendBook(tmp_path / "poor.json", ceiling_usd=0.0)
    capped = LLMPlannerArm(world, _StubClient([]), poor, batch=3, mode="named")
    capped.choose(available, np.array([], int), np.array([]), 3)
    assert capped.events[-1]["code"] == "SPEND_CEILING"


def _fake_almanac(path):
    header = ("COMBODRUGSEQ,SCREENER,STUDY,TESTDATE,PLATE,PANELNBR,CELLNBR,PREFIX1,NSC1,SAMPLE1,CONCINDEX1,CONC1,"
              "CONCUNIT1,PREFIX2,NSC2,SAMPLE2,CONCINDEX2,CONC2,CONCUNIT2,PERCENTGROWTH,PERCENTGROWTHNOTZ,TESTVALUE,"
              "CONTROLVALUE,TZVALUE,EXPECTEDGROWTH,SCORE,VALID,PANEL,CELLNAME")
    rows = [header]
    seq = 0
    for cell in ("A", "B"):
        for (d1, d2) in ((740, 750), (740, 752), (750, 752)):
            for i in (1, 2, 3):
                for j in (1, 2, 3):
                    seq += 1
                    score = 15.0 if (d1, d2) == (740, 750) and cell == "A" else 1.0
                    rows.append(f"{seq},FG,s,d,p,1,1,S,{d1},1,{i},{i}e-6,M,S,{d2},1,{j},{j}e-6,M,40,40,1,1,1,55,{score},Y,P,{cell} ")
            for d, conc_index in ((d1, 1), (d2, 2)):
                seq += 1
                rows.append(f"{seq},FG,s,d,p,1,1,S,{d},1,{conc_index},1e-6,M,S,,,0,,,60,60,1,1,1,,,Y,P,{cell} ")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ComboDrugGrowth_Nov2017.csv", "\n".join(rows) + "\n")


def test_almanac_builder_and_vault_refuse_by_name(tmp_path):
    source = tmp_path / "combo.zip"
    _fake_almanac(source)
    with pytest.raises(screens.VaultRefusal) as sealed:
        screens.build_almanac({}, tmp_path / "lib.npz", source=source)
    assert sealed.value.code == "VAULT_SEALED"
    with pytest.raises(screens.VaultRefusal) as missing:
        screens.open_vault(tmp_path / "freeze.json", tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    assert missing.value.code == "VAULT_SEALED"
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("v1")
    freeze = tmp_path / "freeze.json"
    freeze.write_text(json.dumps({"files": {"frozen.txt": screens.sha256(frozen)}}))
    ticket = screens.open_vault(freeze, tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    assert ticket["prior_openings"] == 0
    frozen.write_text("v2")
    with pytest.raises(screens.VaultRefusal) as changed:
        screens.open_vault(freeze, tmp_path / "vault.jsonl", purpose="t", source=source, root=tmp_path)
    assert changed.value.code == "FREEZE_MISMATCH"
    names = tmp_path / "names.txt"
    names.write_text("740\tMethotrexate\n750\tBusulfan\n752\tThioguanine\n752\t6-Thioguanine\n")
    lib = screens.build_almanac(ticket, tmp_path / "lib.npz", source=source, names_path=names)
    assert len(lib) == 6 and lib.lines == ("A", "B")
    assert lib.drugs == ("Methotrexate", "Busulfan", "Thioguanine")
    assert lib.hits.sum() == 1 and lib.y.max() == pytest.approx(15.0)
    assert np.all(lib.cost_points == 9)
    assert np.allclose(lib.mono_mean[~np.isnan(lib.mono_mean)], 0.4)
