"""Research-scope checks for block K: promotion parity with the study's records and sealing.

Data-dependent tests skip when the local data packets are absent.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "data/external/kinetic_horizon_20261010"
sys.path[:0] = [str(HERE), str(ROOT / "src"), str(ROOT)]
needs_data = pytest.mark.skipif(not (DATA / "prism_mix_sealed.npz").exists(), reason="block K data packet absent")


def test_duration_shares_partition_the_cycle_and_slowdown_is_one_without_change():
    import horizon_data as Hd
    u = Hd.duration_shares(50, 30, 20)
    assert np.isclose(u.sum(), 1.0) and (u > 0).all()
    same = {"G1": 5000, "S": 3000, "G2M": 2000}
    assert np.isclose(Hd.kinetic(same, same), 0.0)
    arrest = {"G1": 9000, "S": 500, "G2M": 500}
    assert Hd.kinetic(arrest, same) < -1.0  # a G1 arrest is a slowdown
    mitotic = {"G1": 3000, "S": 2000, "G2M": 5000}
    assert Hd.kinetic(mitotic, same) < 0  # a G2/M arrest is also a slowdown (direction-agnostic)
    f = lambda c: np.array([c["G1"], c["S"], c["G2M"]], float) / sum(c.values())  # noqa: E731
    assert np.isclose(Hd.log_rho_from_fractions(f(arrest), f(same)), Hd.kinetic(arrest, same), atol=0.01)


def test_the_planner_abstains_on_the_development_intervals_of_this_block():
    from maestro.world_model_value import IncrementEstimate, plan_measure_or_predict
    g = json.loads((HERE / "posthoc/gate_uncertainty.json").read_text())
    plan = plan_measure_or_predict(IncrementEstimate(g["ceiling_point"], *g["ceiling_ci95"], 24, "mixseq_dev"),
                                   IncrementEstimate(g["forecast_point"], *g["forecast_ci95"], 24, "mixseq_dev"),
                                   minimum_useful_benefit=0.05)
    assert plan.action == "ABSTAIN"
    gate = json.loads((HERE / "GATE.json").read_text())
    assert gate["mix_24h_to_5d"]["decision"] == "MEASURE_EARLY"  # the frozen point-estimate decision, kept as recorded


@needs_data
def test_paired_increment_tool_reproduces_the_posthoc_paired_reanalysis():
    import pandas as pd
    from tools.evaluation.increment import paired_increment
    with np.load(HERE / "PREDICTIONS.npz", allow_pickle=False) as z:
        pr = {k: z[k].copy() for k in z.files}
    with np.load(DATA / "prism_mix_sealed.npz", allow_pickle=False) as z:
        tab = pd.DataFrame(z["secondary_mean"], index=z["files"], columns=z["drugs"])
    drugs = list(json.loads((HERE / "RESULTS.json").read_text())["M"]["M1_measurement_complements_prior"]["per_drug"])
    Y = np.column_stack([tab.loc[list(pr["M_lines"]), d].to_numpy() for d in drugs])
    out = paired_increment(pr["M_B"], pr["M_Rmag"], Y, tasks=drugs, n_boot=2000, seed=20261010)
    ref = json.loads((HERE / "posthoc/paired_reanalysis.json").read_text())["M1_measurement"]
    assert out["point"] == pytest.approx(ref["mean_increment"], abs=1e-12)
    assert [out["lower"], out["upper"]] == pytest.approx(ref["ci95"], abs=1e-12)
    assert out["tasks_improved"] == ref["drugs_improved"]


@needs_data
def test_identity_tool_reproduces_the_axis_probe():
    import mixseq_panel as MP
    import mixseq_state as MS
    from tools.analysis.platform_identity import identity_test
    sp = MP.split()
    cal = MS.calibration(sp)
    c = MP.load_units(["A_control", "C_control", "D_control"])
    present = c["present"]
    query, reference = {}, {}
    for d in np.unique(c["depmap"]):
        f = sp["lines"][d]["tahoe_file"]
        if f:
            query[d] = MS.project(c["frac"][c["depmap"] == d], cal, "v1")[:, present].mean(0)
    split = json.loads((HERE / "SPLIT.json").read_text())
    for f, v in split["lines"].items():
        x = np.load(ROOT / "data/external/tahoe_phenotype_20261010/expression" / f / "basal.npz")["x"]
        reference[v["depmap_id"] or f] = x.mean(0)[present]
    out = identity_test(reference, query, n_null=100, seed=0)
    assert out["passed"] and out["top1"] == 1.0 and out["shared"] >= 18


def test_sealed_tiers_refuse_without_the_explicit_flag():
    py = sys.executable
    for cmd in ([py, str(HERE / "prism_extract.py"), "heldout"], [py, str(HERE / "mixseq_extract.py"), "D_treated"]):
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        assert done.returncode != 0 and "TIER_SEALED" in (done.stdout + done.stderr)
