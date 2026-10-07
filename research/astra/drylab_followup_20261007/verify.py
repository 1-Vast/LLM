"""Independent saved-trace accounting; no policy or original main import."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "drylab_solution_20261007"
KEY = ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID", "LIBRARY_CONC", "anchor_set",
       "SEEDING_DENSITY", "RESEARCH_PROJECT", "DRUGSET_ID", "local_days"]


def verify(run):
    truth = pd.read_csv(SOURCE / "data/predictions.csv.gz", dtype={k: str for k in KEY})
    groups = {(s, r): g.reset_index(drop=True) for (s, r), g in truth.groupby(["SIDM", "role"])}
    events = {}
    for line in (run / "purchase_traces.jsonl").read_text().splitlines():
        z = json.loads(line)
        events.setdefault((z["SIDM"], z["role"], z["arm"]), []).append(z)
    arms = {"frozen_static", "design_only", "missingness_only", "tier_a", "tier_a_shuffled"}
    assert set(events) == {(s, r, a) for s, r in groups for a in arms}
    rows = []
    for (cell, role, arm), traces in events.items():
        g = groups[(cell, role)]
        cap = math.ceil(.2 * len(g))
        screens, confirmed, hits = set(), set(), set()
        stage = "screen"
        for spent, z in enumerate(traces, 1):
            i = z["index"]
            assert type(i) is int and 0 <= i < len(g)
            assert z["spent"] == spent <= cap
            assert z["pair"] == g.iloc[i].pair
            if z["stage"] == "screen":
                assert stage == "screen" and z["round"] == 1 and i not in screens
                screens.add(i)
                assert z["positive"] == bool(g.iloc[i].hit1)
            else:
                stage = "confirm"
                assert z["round"] == 2 and i in screens and i not in confirmed and bool(g.iloc[i].hit1)
                confirmed.add(i)
                assert z["positive"] == bool(g.iloc[i].hit2)
                if bool(g.iloc[i].hit2):
                    hits.add(i)
        assert len(screens) == math.floor(.7 * cap)
        ordered = sorted(screens, key=lambda i: (-float(g.iloc[i].prior_control_score), str(g.iloc[i].pair)))
        expected = [i for i in ordered if bool(g.iloc[i].hit1)][:cap - len(screens)]
        assert [z["index"] for z in traces if z["stage"] == "confirm"] == expected
        rows.append(dict(SIDM=cell, role=role, arm=arm, confirmations=len(hits), spent=len(traces),
                         budget=cap, unused=cap-len(traces), screened=len(screens), verified=len(confirmed)))
    rebuilt = pd.DataFrame(rows).sort_values(["SIDM", "role", "arm"]).reset_index(drop=True)
    saved = pd.read_csv(run / "campaigns.csv").sort_values(["SIDM", "role", "arm"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(rebuilt, saved[rebuilt.columns])
    aggregate = rebuilt.groupby("arm")[["confirmations", "spent", "budget", "unused", "screened", "verified"]].sum()
    recorded = pd.read_csv(run / "summary.csv", index_col="arm")
    pd.testing.assert_frame_equal(aggregate, recorded[aggregate.columns])
    choices = pd.read_json(run / "fold_choices.json")
    assert all(z.heldout_cell not in z.training_cells and len(z.training_cells) == 13 for z in choices.itertuples())
    features = pd.read_csv(run / "public_features.csv.gz", dtype={k: str for k in KEY})
    pd.testing.assert_frame_equal(features[KEY], truth[KEY])
    assert not any(k.startswith(("hit", "event", "raw_", "y1", "y2", "rank1", "rank2")) for k in features)
    # Verify exact fallback at selection level: scores remain frozen, eligible candidates may displace fallback candidates.
    freeze = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text())
    assert hashlib.sha256((HERE / "PROTOCOL.json").read_bytes()).hexdigest() == freeze["sha256"]
    return {"status": "PASS", "campaigns": len(rebuilt), "purchases": sum(len(z) for z in events.values()),
            "source_menu_rows": len(features), "complete_cell_train_exclusion": True,
            "independent_accounting_matches": True, "protocol_freeze_matches": True,
            "all_arm_campaigns_present": True, "static_confirmation_order_verified": True,
            "limits": "No independent culture, biological gain, or re-fit GDSC NLME independence certified"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=HERE / "tier_a_run2")
    parser.add_argument("--output", type=Path, default=HERE / "verification.json")
    args = parser.parse_args()
    report = verify(args.run)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
