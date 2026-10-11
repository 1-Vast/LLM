"""Export production reporting contracts and declare turnaround-price scenarios.

This is independent arithmetic over frozen research outputs. It neither changes
the research policy nor estimates authenticated laboratory or monetary costs.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.evaluation.decision_report import CampaignResult, paired_campaign_report


def main():
    import run as R
    frozen = R.verify_execution()
    frame = pd.read_csv(HERE / "TEST_ROWS.csv")
    if (HERE / "SUPPLEMENT_ROWS.csv").exists():
        supplement = pd.read_csv(HERE / "SUPPLEMENT_ROWS.csv")
        frame = pd.concat([frame, supplement[supplement.role == "confirmation"]], ignore_index=True)
    terminal = frame[frame.budget == 16]
    ledgers = {}
    with (HERE / "TEST_LEDGER.jsonl").open(encoding="utf-8") as stream:
        for raw in stream:
            record = json.loads(raw)
            ledgers.setdefault(record["drug"], record)
    protocol_hash = hashlib.sha256((HERE / "PROTOCOL_FREEZE.json").read_bytes()).hexdigest()
    library, data = R.C.load_data()
    menus = {d[0].drug: [str(library.lines[i]) for i in d[0].menu] for d in data}
    campaigns = []
    for row in terminal.itertuples():
        ledger = ledgers[row.drug]
        problem = {"source_protocol_sha256": protocol_hash, "campaign_id": row.drug,
                   "endpoint": "negative_mean_primary_selective_residual_of_terminal_top10",
                   "targets": ledger["target_lines"], "reference_class_exclusion": row.moa,
                   "measurement_budget": 16,
                   "menu": menus[row.drug], "input_l1000": "all_available_shared_input"}
        identity = hashlib.sha256(json.dumps(problem, sort_keys=True).encode()).hexdigest()
        campaigns.append(CampaignResult(campaign_id=row.drug, cluster_id=row.moa, arm=row.arm,
                         endpoint=problem["endpoint"], problem_sha256=identity, measurement_budget=16,
                         terminal_utility=float(row.utility), measurements=int(row.spent), turnarounds=int(row.rounds)))
    R.dump(HERE / "CAMPAIGN_RESULTS.json", [asdict(row) for row in campaigns])
    scenarios = []
    references = [frozen["best_fixed"]]
    if "batch_particle_kg" in frame.arm.unique():
        references.append("batch_particle_kg")
    for reference in references:
        for price in (0, 0.001, 0.01):
            scenarios.append(paired_campaign_report(campaigns, reference=reference, candidate="adaptive_dual",
                                                   measurement_price=0, turnaround_price=price,
                                                   resamples=4000, seed=20261011))
    R.dump(HERE / "COST_SCENARIOS.json", {
        "scope": "Utility-unit price sensitivities for simulated sequential turnarounds; no actual wet-lab cost or procurement claim.",
        "report_helper_sha256": hashlib.sha256((ROOT / "tools/evaluation/decision_report.py").read_bytes()).hexdigest(),
        "scenarios": scenarios})
    print(json.dumps({"records": len(campaigns), "scenarios": [
        {"reference": value["reference"], "turnaround_price": value["prices"]["turnaround"], "raw": value["raw_utility_increment"],
         "net": value["net_utility_increment"], "cluster_ci95": value["cluster_bootstrap_95"]} for value in scenarios]}, indent=2))


if __name__ == "__main__":
    main()
