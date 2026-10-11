"""Analytic sanity check: modest yield cannot justify many costly round trips."""
import json
from pathlib import Path
from .report_contract import CampaignResult, paired_campaign_report


rows = [CampaignResult(str(i), str(i), arm, "hit", "a" * 64, 16,
                       1.0 if arm == "batch" else 1.1, 16, 1 if arm == "batch" else 16)
        for i in range(4) for arm in ("batch", "adaptive")]
report = paired_campaign_report(rows, reference="batch", candidate="adaptive",
                                measurement_price=0.0, turnaround_price=0.01)
assert abs(report["net_utility_increment"] + 0.05) < 1e-12
assert report["independent_clusters"] == 4
report["evidence_scope"] = "VERIFIED_ENGINEERING_ONLY; analytic fixture, not biological measurements"
Path(__file__).with_name("prototype_result.json").write_text(json.dumps(report, indent=2) + "\n")
print(report["evidence_scope"])
