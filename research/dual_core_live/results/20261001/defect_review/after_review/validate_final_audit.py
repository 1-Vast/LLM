"""Verify final report-only auditor input containment and preserve all prior receipts."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from agent.model_audit import ModelAuditAgent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


normal = {"remaining_budget": 2, "actions": [{"id": "legal", "cost": 1}], "evidence": []}
valid_proposal = {"action": "legal", "terminal_authorized": False}
cases = {}
for name, value in (("nan_budget", float("nan")), ("oversized_budget", 10**1000)):
    card = deepcopy(normal); card["remaining_budget"] = value
    cases[name] = (card, deepcopy(valid_proposal), "invalid_task_contract")
card = deepcopy(normal); card["actions"][0]["id"] = "\ud800"
cases["unicode_encoding_failure"] = (card, deepcopy(valid_proposal), "invalid_task_contract")
cases["set_proposal"] = (deepcopy(normal), dict(valid_proposal, extra=set()), "malformed_proposal")
cases["nonobject_card"] = ([], deepcopy(valid_proposal), "invalid_task_contract")

auditor, results = ModelAuditAgent(), {}
for name, (card, proposal, expected) in cases.items():
    before = deepcopy((card, proposal, vars(auditor)))
    report = auditor.review(card, proposal)
    results[name] = {"finding_codes": [f.code for f in report.findings], "input_sha256": report.input_sha256,
                    "proposal_sha256": report.proposal_sha256,
                    "caller_state_unchanged": (card, proposal, vars(auditor)) == before,
                    "no_action_or_repair_authority": not hasattr(report, "action") and not hasattr(report, "repair")}
    assert expected in results[name]["finding_codes"] and results[name]["caller_state_unchanged"]
    assert results[name]["no_action_or_repair_authority"]
assert results["nan_budget"]["input_sha256"] is None
assert results["unicode_encoding_failure"]["input_sha256"] is None
assert results["set_proposal"]["proposal_sha256"] is None
assert results["oversized_budget"]["input_sha256"] is not None

first = json.loads((OUT / "independent_validation.json").read_text())
core_unchanged = {p: sha(ROOT / p) == old for p, old in first["source_sha256"].items()
                  if not p.endswith("model_audit.py")}
assert first["all_six_original_cases_resolved"] and all(core_unchanged.values())
record = {"date": "2026-10-01", "passed": True, "command": [sys.executable, *sys.argv],
    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "environment": {"interpreter": sys.executable, "python": sys.version, "platform": platform.platform()},
    "source_sha256": {p: sha(ROOT / p) for p in first["source_sha256"]}, "code_sha256": sha(Path(__file__)),
    "six_case_receipt_sha256": sha(OUT / "independent_validation.json"),
    "original_frozen_receipt_sha256": sha(OUT.parent / "reproduction_receipt.json"),
    "original_core_fix_sources_unchanged": core_unchanged, "results": results,
    "clarification": "The earlier receipt's new_open_cases field tracks review candidates, not proven remaining failures: those inputs already returned reports during that run. This final receipt verifies their exact findings and the root's later numeric/Unicode corrections.",
    "authority": "Report-only: no input mutation, replacement action, repair, execution, provider call or training."}
with (OUT / "final_audit_validation.json").open("x") as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
print(json.dumps({"passed": True, "original_core_fix_sources_unchanged": core_unchanged,
                  "case_findings": {k: v["finding_codes"] for k, v in results.items()}}, indent=2))
