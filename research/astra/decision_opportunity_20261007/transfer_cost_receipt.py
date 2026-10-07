"""Expose common resource ceiling separately from frozen policy envelopes."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transfer_cost_study", HERE / "run.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def main():
    source = HERE / "transfer_run1"
    rows = [json.loads(line) for line in (source / "EPISODES.jsonl").read_text().splitlines()]
    entries = [dict(case_id=r["case_id"], policy_budget_cap=r["budget_cap"],
        actual_credits=r["actual_credits"], unused_policy_cap=r["unused_cap"],
        common_resource_ceiling=13, unused_common_ceiling=13-r["actual_credits"]) for r in rows]
    study.write(source / "COST_INTERPRETATION.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=study.digest(HERE / "TRANSFER_PROTOCOL.json"),
        episode_sha256=study.digest(source / "EPISODES.jsonl"),
        meaning="Frozen fixed5 policies reserve a narrower10credit envelope within a common13credit resource ceiling. Both measure5A+5B, so3commoncredits unused. KG8/fixed8 consume13. This cost-utility comparison is not samecost or samepolicy superiority.",
        same_actual_cost_control="M2fixed5 vs M0fixed5, both10credits; M2KG8 vs M0KG8, both13credits",
        primary="Registered lowercost utility transfer M2fixed5 vs M0KG8; unsuccessful raw mean condition retained",
        no_rerun="No frozen protocol or result modified; receipt only exposes shared ceiling separately", episodes=entries))
    print(json.dumps({"episodes": len(entries), "actual": sum(r["actual_credits"] for r in entries),
                      "common_ceiling": len(entries)*13, "common_unused": sum(r["unused_common_ceiling"] for r in entries)}))


if __name__ == "__main__":
    main()
