"""Secondary same-posterior contrasts and independent supplementary ledger checks."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import campaign as C
import run as R
import supplement as S
import verify as V

HERE = Path(__file__).resolve().parent


def main():
    frozen = R.verify_execution()
    receipt = json.loads((HERE / "SUPPLEMENT_RECEIPT.json").read_text(encoding="utf-8"))
    for name, key in (("SUPPLEMENT_ROWS.csv", "rows_sha256"), ("SUPPLEMENT_LEDGER.jsonl", "ledger_sha256")):
        assert C.sha256(HERE / name) == receipt[key]
    extra = pd.read_csv(HERE / "SUPPLEMENT_ROWS.csv")
    base = pd.read_csv(HERE / "TEST_ROWS.csv")
    combined = pd.concat([base, extra[extra.role == "confirmation"]], ignore_index=True)
    results = []
    for budget in (2, 4, 8, 16):
        group = combined[combined.budget == budget]
        clusters = group.drop_duplicates("drug").set_index("drug").moa
        for comparator in ("batch_particle_kg", "fixed_library"):
            for metric in ("utility", "precision", "selective_r", "secondary_utility", "secondary_precision", "secondary_r"):
                table = group.pivot(index="drug", columns="arm", values=metric)
                delta = table.adaptive_dual - table[comparator]
                stats = R.paired_statistics(delta, clusters.reindex(table.index), C.SEED + 61)
                results.append({"a": "adaptive_dual", "b": comparator, "budget": budget, "metric": metric, **stats})
    summaries = []
    for (role, budget), group in extra.groupby(["role", "budget"]):
        summaries.append({"role": role, "budget": int(budget), "n": len(group),
                          **{metric: float(group[metric].mean()) for metric in ("utility", "precision", "selective_r")}})
    with threadpool_limits(limits=1):
        library, data = C.load_data()
        checked = V.verify_ledger("SUPPLEMENT", library, data)
        equivalence = 0
        for datum in [d for d in data if d[0].role == "development"][:8]:
            particle = C.ParticlePosterior(library, datum[0], **frozen["parameters"])
            plan, values = S.plan_batch(particle)
            first, value = particle.choose()
            assert plan[0] == first and abs(values[0] - value) < 1e-10
            equivalence += 1
    R.dump(HERE / "SUPPLEMENT_RESULTS.json", {"scope": "Frozen secondary comparison, not a changed primary gate.",
             "identical_initial_moments_cases": equivalence, "independent_ledger_verification": checked,
             "contrasts": results, "cost_curve": summaries, "llm_api_calls": 0})
    print(json.dumps({"budget16_utility": [r for r in results if r["budget"] == 16 and r["metric"] == "utility"],
                      "verification": checked, "identical_initial_moments_cases": equivalence}, indent=2))


if __name__ == "__main__":
    main()
