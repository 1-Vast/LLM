"""Recompute frozen policies without overwriting the retained experiment artifacts."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import campaign as C
import run as R
import supplement as S

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Recompute all 421 test compounds, rather than 8.")
    args = parser.parse_args()
    frozen = R.verify_execution()
    expected = pd.read_csv(HERE / "TEST_ROWS.csv")
    extra = pd.read_csv(HERE / "SUPPLEMENT_ROWS.csv")
    expected = pd.concat([expected, extra[extra.role == "confirmation"]], ignore_index=True)
    expected = expected.set_index(["drug", "arm", "budget"])
    metrics = ("utility", "precision", "selective_r", "max_error", "secondary_utility",
               "secondary_precision", "secondary_r", "spent", "rounds")
    start = time.perf_counter()
    maximum = 0.0
    count = 0
    with threadpool_limits(limits=1):
        library, data = C.load_data()
        units = [d for d in data if d[0].role == "confirmation"]
        if not args.all:
            units = units[:8]
        signature_map = R.signature_permutation(data)
        for index, datum in enumerate(units):
            for arm in list(R.ARMS) + ["batch_particle_kg"]:
                if arm == "batch_particle_kg":
                    rows, _ = S.run_one(library, datum, frozen["parameters"])
                else:
                    rows, _ = R.run_one(library, datum, arm, frozen["parameters"], signature_map)
                for row in rows:
                    truth = expected.loc[(row["drug"], row["arm"], row["budget"])]
                    for metric in metrics:
                        value = np.nan if row[metric] is None else row[metric]
                        actual = truth[metric]
                        if np.isnan(value) or np.isnan(actual):
                            assert np.isnan(value) and np.isnan(actual)
                        else:
                            difference = abs(value - actual)
                            assert difference < 1e-10, (row["drug"], arm, metric, difference)
                            maximum = max(maximum, difference)
                    count += 1
            if index % 20 == 0:
                print(f"recompute {index}/{len(units)} seconds={time.perf_counter() - start:.1f}", flush=True)
    report = {"n_drugs": len(units), "n_campaign_cost_rows": count,
              "max_metric_error": maximum, "seconds": time.perf_counter() - start,
              "scope": "Algorithm-output reconstruction from frozen sources and parameters; no tuning or overwrite.",
              "calibration_freeze_sha256": C.sha256(R.CONFIG)}
    R.dump(HERE / ("REPLAY_ALL_VERIFIED.json" if args.all else "REPLAY_SAMPLE_VERIFIED.json"), report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
