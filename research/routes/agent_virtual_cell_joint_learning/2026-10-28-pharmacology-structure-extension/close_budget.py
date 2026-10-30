"""Summarize actual bounded source receipts; this does not validate science."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
read = lambda path: json.loads((root / path).read_text(encoding="utf-8"))
p7 = read("sources/evidence_p7/manifest.json")
punzi = read("sources/punzi/receipt.json")
official = read("sources/bcl11b_official_supplement/receipt.json")
timeout = read("sources/bcl11b_supplement/receipt.json")
version_query = read("sources/public_version_check/receipt.json")
preprint = read("sources/public_version_check/preprint_receipt.json")
usage = json.loads((root.parent / "deepseek/tasks/DS012/usage.json").read_text(encoding="utf-8"))
for file in p7["files"]:
    raw = (root / "sources/evidence_p7" / file["file"]).read_bytes()
    assert len(raw) == file["bytes"] and hashlib.sha256(raw).hexdigest() == file["sha256"]
raw = (root / "sources/punzi/41467_2024_54728_MOESM8_ESM.zip").read_bytes()
assert len(raw) == punzi["bytes"] and hashlib.sha256(raw).hexdigest() == punzi["sha256"]
result = {
    "scope": "receipt/provenance/budget accounting only; not biological or algorithmic validation",
    "search_passes": {"previous": 6, "extension": 3, "cumulative": 9, "ceiling": 9},
    "http": {"extension_calls": p7["http_calls"] + 5, "ceiling": 18,
             "extension_queries": p7["queries"] + 1, "query_ceiling": 10,
             "saved_response_bytes": p7["raw_response_bytes"] + punzi["bytes"] + official["error_body_bytes"] + version_query["bytes"] + preprint["bytes"],
             "download_cap_bytes": 100000000,
             "timeout_partial_bytes": None, "timeout_partial_upper_bound": timeout["byte_cap"] + 1,
             "failure_statuses": ["EPMC supplementaryFiles read timeout", "Science SI HTTP403", "bioRxiv lookup HTTP403 error1010"],
             "automatic_retries": 0},
    "harness": {"previous_invocations": 3, "extension_invocations": 1, "cumulative_invocations": 4,
                "extension_ceiling": 2, "cumulative_ceiling": 5, "task_id": "DS012", "stdin_bytes": usage["stdin_bytes"],
                "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
                "cache_read_tokens": usage["cache_read_tokens"], "seconds": usage["seconds"],
                "extension_declared_cost_cap_usd": 0.05, "actual_cost_usd": None, "effective_model": None,
                "provider_request_count": None, "automatic_retries": 0, "backend_changes": 0},
    "scientific_execution": {"effect_experiments": 0, "training": 0, "gpu": 0, "wet_lab": 0,
                             "note": "metadata extraction and algebraic counterexamples only; no endpoint values consumed for effect"},
    "terra": {"requested": "gpt-6.1-terra/high", "effective_model": None, "status": "503_no_deliverable", "retries": 0},
    "goal_status": "ACTIVE / NOT_ACHIEVED"
}
(root / "budget_usage.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
