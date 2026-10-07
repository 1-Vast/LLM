"""Independent checks of acquired features, response errors and paid accounting."""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pandas as pd

from research.astra.functional_data_20261007.acquire import HERE, ROOT
from research.astra.drylab_followup_20261007.reproduce import preservation


def main():
    out = HERE / "verification_complete.json"
    if out.exists():
        raise FileExistsError(out)
    d = HERE / "data_run3"
    source = ROOT / "research/astra/drylab_solution_20261007/data/predictions.csv.gz"
    target = pd.read_csv(source, dtype={"ANCHOR_ID": str, "LIBRARY_ID": str, "SIDM": str, "LIBRARY_CONC": str})
    points = pd.read_csv(d / "mono_plate_points.csv.gz", dtype={"sidm": str, "drug_id": str, "BARCODE": str})
    event = pd.read_csv(d / "mono_event_points.csv.gz", dtype={"sidm": str, "drug_id": str})
    features = pd.read_csv(d / "candidate_features.csv.gz", dtype={"ANCHOR_ID": str, "LIBRARY_ID": str, "SIDM": str, "LIBRARY_CONC": str})
    assert not set(points.sidm) & set(target.SIDM)
    assert not set(event.sidm) & set(target.SIDM)
    assert not points.duplicated(["BARCODE", "drug_id", "role", "dose_uM"]).any()
    assert points.nc_cv.le(.18).all() and points.zfactor.ge(.3).all()
    assert np.isfinite(points.viability).all()
    for k in ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID", "LIBRARY_CONC", "anchor_set"]:
        assert features[k].astype(str).tolist() == target[k].astype(str).tolist(), k
    assert features.exact_eligible.sum() == 4424
    assert not features.loc[features.composite, "exact_eligible"].any()
    assert not any(k.startswith(("hit", "event", "raw_", "y1", "y2")) for k in features)
    # Rebuild response error tables without using the forecasting implementation.
    prediction = pd.read_csv(HERE / "world_results/heldout_predictions.csv.gz")
    assert not set(prediction.sidm) & set(target.SIDM)
    assert prediction.groupby("sidm").fold.nunique().eq(1).all()
    prediction["absolute"] = abs(prediction.prediction - prediction.viability)
    prediction["square"] = (prediction.prediction - prediction.viability) ** 2
    summary = prediction.groupby(["arm", "sidm"])[["absolute", "square"]].mean().groupby("arm").mean()
    saved = pd.read_csv(HERE / "world_results/summary.csv", index_col="arm")
    np.testing.assert_allclose(summary.absolute, saved.mae, rtol=1e-12)
    np.testing.assert_allclose(np.sqrt(summary.square), saved.rmse, rtol=1e-12)
    # PRISM has its own task. Identity, STR and target exclusions are mandatory.
    prism = pd.read_csv(HERE / "prism_qualified/reference_observations.csv.gz")
    assert not set(prism.sidm) & set(target.SIDM)
    assert prism.structure_agreement.eq(True).all()
    assert prism.jaaks_exact_match.eq(False).all()
    assert prism.time_h.eq(120).all()
    receipt = json.loads((HERE / "acquisition/prism/receipts.json").read_text())
    for z in receipt:
        assert z["status"] == "VERIFIED"
        p = HERE / "acquisition/prism" / z["name"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == z["sha256"]
    # Reconstruct all screen/confirm purchases independently of the replay/model.
    groups = {(s, r): g.reset_index(drop=True) for (s, r), g in target.groupby(["SIDM", "role"])}
    traces = {}
    for line in (HERE / "ranking_results/purchase_traces.jsonl").read_text().splitlines():
        z = json.loads(line);traces.setdefault((z["SIDM"], z["role"], z["arm"]), []).append(z)
    arms = {"frozen_static", "raw_reference", "raw_shuffled"}
    assert set(traces) == {(s, r, a) for s, r in groups for a in arms}
    records = []
    for (cell, role, arm), trace in traces.items():
        truth = groups[(cell, role)]
        budget = math.ceil(.2 * len(truth))
        screens, verified, hits = set(), set(), set()
        for spent, z in enumerate(trace, 1):
            i = z["index"]
            assert type(i) is int and 0 <= i < len(truth) and z["spent"] == spent <= budget
            assert z["pair"] == truth.iloc[i].pair
            if z["stage"] == "screen":
                assert z["round"] == 1 and not verified and i not in screens
                assert z["positive"] == bool(truth.iloc[i].hit1)
                screens.add(i)
            else:
                assert z["round"] == 2 and i in screens and i not in verified and bool(truth.iloc[i].hit1)
                assert z["positive"] == bool(truth.iloc[i].hit2)
                verified.add(i)
                if z["positive"]:
                    hits.add(i)
        assert len(screens) == math.floor(.7 * budget)
        expected = sorted([i for i in screens if bool(truth.iloc[i].hit1)], key=lambda i: (-truth.iloc[i].prior_control_score, truth.iloc[i].pair))[:budget-len(screens)]
        assert [z["index"] for z in trace if z["stage"] == "confirm"] == expected
        records.append(dict(arm=arm, confirmations=len(hits), spent=len(trace), budget=budget, unused=budget-len(trace)))
    rebuild = pd.DataFrame(records).groupby("arm")[["confirmations", "spent", "budget", "unused"]].sum()
    pd.testing.assert_frame_equal(rebuild, pd.read_csv(HERE / "ranking_results/summary.csv", index_col="arm"))
    for protocol, freeze in [("PROTOCOL.json", "PROTOCOL_FREEZE.json"), ("WORLD_PROTOCOL.json", "WORLD_FREEZE.json")]:
        f = json.loads((HERE / freeze).read_text())
        assert hashlib.sha256((HERE / protocol).read_bytes()).hexdigest() == f["sha256"]
    recipe = pd.read_csv(HERE / "composite_recipes_verified/physical_well_component_doses.csv", dtype={"BARCODE": str})
    patterns = pd.read_csv(HERE / "composite_recipes_verified/observed_top_recipes.csv", dtype=str)
    assert not set(recipe.sidm) & set(target.SIDM)
    for _, g in recipe.groupby("BARCODE"):
        values = np.array([[float(v) for v in x.split("|")] for x in g.component_doses_uM])
        maxima = "|".join(format(v, ".12g") for v in values.max(axis=0))
        assert maxima in set(patterns.component_doses_uM)
    projected = json.loads((HERE / "composite_recipes_verified/core_intervention_projection.json").read_text())
    assert [z["dose"] for z in projected[0]["intervention"]["components"]] == [10., 1.]
    report = {"status": "PASS", "prior_supplied_files_unchanged": len(preservation()),
              "qualified_raw_reference_rows": len(points), "candidate_coverage": int(features.exact_eligible.sum()),
              "target_raw_mono_excluded": True, "prism_response_rows": len(prism), "prism_source_hashes_match": True,
              "world_errors_independently_rebuilt": True, "ranking_campaigns": len(traces),
              "purchases_independently_checked": sum(map(len, traces.values())), "frozen_contracts_unchanged": True,
              "composite_recipe_wells_checked": len(recipe), "existing_core_type_projection_checked": True,
              "claim": "Data and accounting checks, not biological or agent decision-value certification"}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
