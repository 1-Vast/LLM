"""Contract tests for bridged context transfer and source-verified procedure selection.

Covers src/virtual_cell/bridged_transfer.py, src/agent/bridge_design.py and
src/agent/procedure_selection.py on small synthetic domains.
"""
from __future__ import annotations

import numpy as np
import pytest

from agent.bridge_design import BRIDGE_RULES, choose_bridge, fixed_panel, nominate, run_campaign
from agent.procedure_selection import (NO_INNER_EVIDENCE, PROCEDURES, Z_BRIDGE, choose, hash_folds, hash_unit,
                                       source_replay)
from virtual_cell.bridged_transfer import (ITEM_AXIS_MISMATCH, TOO_FEW_SOURCE_CONTEXTS, BridgedTransferModel,
                                           TransferRefused, normal_cdf, selective_events)


def _domain(n=90, d=40, genes=30, seed=0, missing=0.1):
    rng = np.random.default_rng(seed)
    f = rng.normal(size=(n, 2))
    V = rng.normal(size=(d, 2))
    Y = f @ V.T + 0.3 * rng.normal(size=(n, d))
    X = f @ rng.normal(size=(2, genes)) + 0.2 * rng.normal(size=(n, genes))
    Y[rng.random((n, d)) < missing] = np.nan
    return Y, X


def _model(Y, X, rank=2):
    return BridgedTransferModel(rank=rank, n_pcs=5, n_genes=30, min_measured=10, impute_iters=5).fit(Y, X)


def test_selective_events_follow_the_registered_rule():
    rng = np.random.default_rng(1)
    Y = rng.normal(scale=0.1, size=(60, 5))
    Y[7, 2] = -5.0
    Y[:, 4] = np.nan
    Y[:3, 4] = 0.0
    ev, G = selective_events(Y, None, 20)
    assert ev[7, 2]
    assert not ev[:, 4].any()
    gated, _ = selective_events(Y, -10.0, 20)
    assert not gated.any()
    assert G.shape == (60,)


def test_fit_refuses_by_name():
    Y, X = _domain(n=30)
    with pytest.raises(TransferRefused) as err:
        BridgedTransferModel(rank=40).fit(Y, X)
    assert err.value.code == TOO_FEW_SOURCE_CONTEXTS
    with pytest.raises(TransferRefused) as err:
        BridgedTransferModel(rank=2).fit(Y, X[:-1])
    assert err.value.code == ITEM_AXIS_MISMATCH


def test_scores_are_expected_hits_per_well_and_unmeasured_items_score_low():
    Y, X = _domain()
    Y[:, 3] = np.nan
    m = _model(Y, X)
    st = m.prior(X[0])
    assert st.prior_source == "basal"
    assert m.expected_hit(st) == pytest.approx(m.measured_rate * m.event_prob(st))
    assert m.measured_rate[3] == pytest.approx(0.5 / (len(Y) + 1))
    assert m.prior(None).prior_source == "population"


def test_measuring_items_shrinks_their_uncertainty_and_misfit_needs_a_value():
    Y, X = _domain()
    m = _model(Y[:80], X[:80])
    st0 = m.prior(X[85])
    st1 = m.posterior(st0, [0, 1, 2], Y[85, [0, 1, 2]])
    assert (m.predict(st1)[1] <= m.predict(st0)[1] + 1e-12).all()
    assert list(st1.observed) == [0, 1, 2]
    assert np.isnan(m.misfit(st0, [0], [np.nan]))
    assert m.misfit(st0, [0, 1, 2], Y[85, [0, 1, 2]]) >= 0


def test_numpy_normal_cdf_matches_the_exact_one():
    x = np.linspace(-8, 8, 4001)
    approx = normal_cdf(x, exact=False)
    assert np.all(np.diff(approx) >= -1e-12)
    assert np.max(np.abs(approx - normal_cdf(x))) < 2e-7


def test_bridge_rules_return_distinct_unobserved_items():
    Y, X = _domain()
    m = _model(Y[:80], X[:80])
    order = hash_unit(np.arange(Y.shape[1]), "tie")
    st = m.posterior(m.prior(X[81]), [5], Y[81, [5]])
    for rule in BRIDGE_RULES:
        b = choose_bridge(rule, m, st, 4, 12, order, rng_order=hash_unit(np.arange(Y.shape[1]), "r"))
        assert len(b) == 4 and len(set(b.tolist())) == 4
        if rule != "panel":
            assert 5 not in b
    assert (fixed_panel(m, 4, order) == choose_bridge("panel", m, st, 4, 12, order)).all()
    with pytest.raises(ValueError):
        choose_bridge("oracle", m, st, 4, 12, order)
    with pytest.raises(ValueError):
        choose_bridge("exploit", m, st, 12, 12, order)


def test_corrected_lookahead_never_bridges_on_known_unavailable_items():
    # ``lookahead_v1`` (frozen in research/context_transfer_20261017) kept the prior baseline after
    # the first greedy pick; with heterogeneous measurement rates it preferred rarely measured items
    unavailable = {"lookahead": 0, "lookahead_v1": 0}
    for seed in range(6):
        Y, X = _domain(n=120, d=60, seed=seed, missing=0.0)
        m = _model(Y[:100], X[:100])
        order = hash_unit(np.arange(Y.shape[1]), "tie")
        m.measured_rate = (np.random.default_rng(seed).random(Y.shape[1]) < 0.5).astype(float)
        st = m.prior(X[110])
        for rule in unavailable:
            b = choose_bridge(rule, m, st, 4, 16, order)
            unavailable[rule] += int((m.measured_rate[b] == 0).sum())
    assert unavailable["lookahead"] == 0
    assert unavailable["lookahead_v1"] > 0


def test_campaign_spends_exactly_the_budget_and_counts_empty_wells():
    Y, X = _domain(missing=0.3)
    m = _model(Y[:80], X[:80])
    order = hash_unit(np.arange(Y.shape[1]), "tie")
    calls = []

    def measure(idx):
        calls.append(list(idx))
        return Y[85, idx]

    none = run_campaign(m, X[85], measure, 12, 0, None, order)
    assert none.rounds == 1 and len(none.wells) == 12 and len(calls) == 1
    calls.clear()
    bridged = run_campaign(m, X[85], measure, 12, 4, "lookahead", order)
    assert bridged.rounds == 2 and len(calls) == 2 and len(calls[0]) == 4 and len(calls[1]) == 8
    assert len(set(bridged.wells.tolist())) == 12 and (bridged.wells[:4] == bridged.bridge).all()
    assert bridged.wasted == int((~np.isfinite(Y[85, bridged.wells])).sum())
    assert (nominate(np.arange(5.0), 2, [4], np.zeros(5)) == [3, 2]).all()


def _inner(gains, base=1.0, n=40, seed=0, ranks=(5, 10)):
    rng = np.random.default_rng(seed)
    out = {}
    for r in ranks:
        v = base + rng.normal(scale=0.5, size=n)
        out[r] = [{"context": f"c{i}", "vc0": v[i], "b_exploit": v[i] + gains[0] + rng.normal(scale=0.5),
                   "b_lookahead": v[i] + gains[1] + rng.normal(scale=0.5)} for i in range(n)]
    return out


def test_a_bridge_is_adopted_only_on_evidence():
    strong = choose(_inner((0.0, 1.0)))
    assert strong.procedure == "b_lookahead" and strong.rounds == 2
    assert strong.bridge_gains["b_lookahead"]["z"] > Z_BRIDGE
    weak = choose(_inner((0.02, 0.02)))
    assert weak.procedure == "vc0" and weak.rounds == 1 and weak.basis == "no_bridge_evidence"
    assert choose(_inner((0.02, 0.05)), "max").procedure != "vc0"
    assert choose(_inner((0.02, 0.05)), "evidence").procedure == "vc0"
    with pytest.raises(ValueError):
        choose(_inner((0, 0)), "oracle")


def test_rank_follows_the_one_standard_error_rule():
    inner = _inner((0.0, 0.0), ranks=(5,))
    # rank 10 is better by 0.001 on average, well inside one standard error of the paired difference
    inner[10] = [{**x, "vc0": x["vc0"] + 0.001 + (0.05 if i % 2 else -0.05)} for i, x in enumerate(inner[5])]
    assert choose(inner, "evidence").rank == 5
    assert choose(inner, "max").rank == 10 and choose(inner).rank == 10


def test_without_inner_evidence_the_choice_is_no_bridge():
    ch = choose({5: [{"context": "a", "vc0": 0, "b_exploit": 3, "b_lookahead": 3}]})
    assert ch.procedure == "vc0" and ch.basis == NO_INNER_EVIDENCE


def test_source_replay_uses_source_contexts_only_and_is_deterministic():
    Y, X = _domain(n=75, d=30)
    contexts = np.array([f"s{i}" for i in range(75)])
    groups = np.array([f"p{i // 3}" for i in range(75)])
    kw = dict(abs_gate=None, min_measured=10, impute_iters=3, ranks=(2, 3), by_group=True, salt="t")
    a = source_replay(Y, X, contexts, groups, np.arange(30), 8, 2, **kw)
    b = source_replay(Y, X, contexts, groups, np.arange(30), 8, 2, **kw)
    assert a == b and set(a) == {2, 3}
    assert {x["context"] for x in a[2]} == set(contexts)
    assert all(set(PROCEDURES) <= set(x) for x in a[2])
    fid = hash_folds(groups, "t:inner", 3)
    assert all(len(set(fid[groups == g])) == 1 for g in set(groups))


def test_bridge_replay_tool_runs_end_to_end(tmp_path):
    from tools.evaluation import bridge_replay

    Y, X = _domain(n=70, d=25, seed=3)
    path = tmp_path / "domain.npz"
    np.savez(path, Y=Y, X=X, contexts=np.array([f"s{i}" for i in range(70)]),
             groups=np.array([f"p{i // 2}" for i in range(70)]), items=np.array([f"i{j}" for j in range(25)]))
    with np.load(path) as z:
        domain = {k: z[k] for k in ("Y", "X", "contexts", "groups", "items")}
    res = bridge_replay.replay(domain, 8, 2, min_measured=10, impute_iters=2, ranks=(2, 3))
    assert res["contexts"] == 70 and set(res["mean_hits"]) == set(bridge_replay.ARMS)
    assert all(r["selected"] == r[c["procedure"]] for r in res["records"]
               for k, c in res["choices"].items() if r["fold"] == k)
    assert res["mean_hits"]["oracle"] >= max(v for a, v in res["mean_hits"].items() if a != "oracle")
    assert 1.0 <= res["selected_rounds"] <= 2.0


def test_design_census_reads_only_declared_columns(tmp_path):
    pytest.importorskip("pandas")
    from tools.datasets.design_census import census

    table = tmp_path / "fits.tsv"
    table.write_text("subject\tsample\tdrug\tauc\np1\ts1\td1\t10\np1\ts1\td2\tbad\np2\ts2\td1\t12\n",
                     encoding="utf-8")
    out = census(table, ["subject", "sample", "drug"], "sample", "subject", "drug")
    assert out["read_columns"] == ["subject", "sample", "drug"] and "auc" not in json_keys(out)
    assert out["contexts"] == 2 and out["items"] == 2 and out["measured_pair_rate"] == pytest.approx(0.75)
    with pytest.raises(ValueError):
        census(table, ["subject", "drug"], "sample", "subject", "drug")


def json_keys(obj):
    return set(obj) | {k for v in obj.values() if isinstance(v, dict) for k in v}


def test_every_bridge_rule_states_its_evidence_grade():
    from agent.bridge_design import RULE_STATUS
    from agent.procedure_selection import SELECTION_STATUS

    assert set(RULE_STATUS) == set(BRIDGE_RULES)
    assert RULE_STATUS["lookahead"].startswith("development")
    assert "confirmed" in RULE_STATUS["exploit"]
    assert SELECTION_STATUS[("hybrid", "lookahead")].startswith("development")
