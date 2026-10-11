"""Parity tests between this block's frozen statistics and the promotion candidate in tools/.

`stats.cluster_signflip` decides every registered verdict in block P. If it is promoted to
`tools.evaluation.scoring`, the promoted copy must agree with the frozen one exactly, on the
block's own campaign differences as well as on constructed cases. These tests skip when the
promotion has not happened, so they are meaningful before and after.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import stats as ST  # noqa: E402

promoted = pytest.importorskip("tools.evaluation.scoring", reason="promotion not performed")
if not hasattr(promoted, "cluster_signflip_test"):
    pytest.skip("tools.evaluation.scoring has no cluster_signflip_test yet", allow_module_level=True)


def _cases():
    rng = np.random.default_rng(11)
    clusters = np.array([f"L{i % 14}" for i in range(42)])
    yield "null", rng.normal(0, 1, 42), clusters
    yield "shift", rng.normal(0.7, 1, 42), clusters
    yield "sparse", np.where(np.arange(42) < 6, 1.0, 0.0), clusters
    yield "all_zero", np.zeros(42), clusters
    yield "one_cluster_only", np.where(clusters == "L3", 2.0, 0.0), clusters


@pytest.mark.parametrize("name,diff,clusters", list(_cases()), ids=[c[0] for c in _cases()])
def test_promoted_signflip_matches_frozen(name, diff, clusters):
    a = ST.cluster_signflip(diff, clusters)
    b = promoted.cluster_signflip_test(diff, clusters)
    for key in ("estimate", "p_greater", "p_less", "p_two_sided"):
        assert a[key] == pytest.approx(b[key], abs=1e-12), f"{name}:{key}"
    assert a["exact"] == b["exact"] and a["n_clusters"] == b["n_clusters"]


def test_promoted_signflip_matches_on_the_registered_contrasts():
    rows = ROOT / "research/astra/selective_discovery_20261011/results/confirm/ROWS.csv"
    if not rows.exists():
        pytest.skip("confirmation rows absent")
    import pandas as pd
    df = pd.read_csv(rows)
    clusters = df["T"].to_numpy()
    for a, b, metric in (("maestro", "agent_novc", "unexpected"), ("maestro", "vc_only", "hits")):
        diff = (df[f"{a}|{metric}"] - df[f"{b}|{metric}"]).to_numpy(float)
        x = ST.cluster_signflip(diff, clusters)
        y = promoted.cluster_signflip_test(diff, clusters)
        assert x["p_greater"] == pytest.approx(y["p_greater"], abs=1e-12)
        assert x["estimate"] == pytest.approx(y["estimate"], abs=1e-12)


def test_registered_verdicts_reproduce_from_the_rows():
    """The verdicts in RESULTS.json must follow from ROWS.csv alone, with the frozen rule."""
    res = ROOT / "research/astra/selective_discovery_20261011/results/confirm/RESULTS.json"
    rows = res.parent / "ROWS.csv"
    if not (res.exists() and rows.exists()):
        pytest.skip("confirmation results absent")
    import pandas as pd
    claimed = json.loads(res.read_text(encoding="utf-8"))
    df = pd.read_csv(rows)
    g = df["T"].to_numpy()
    primary = {"H1_vc_contribution_unexpected": (df["maestro|unexpected"] - df["agent_novc|unexpected"]).to_numpy(float),
               "H2_agent_contribution_hits": (df["maestro|hits"] - df["vc_only|hits"]).to_numpy(float)}
    fam = ST.family({k: (v, g) for k, v in primary.items()}, alpha=0.05)
    for k, v in fam.items():
        assert v["verdict"] == claimed["primary"][k]["verdict"]
        assert v["estimate"] == pytest.approx(claimed["primary"][k]["estimate"])
