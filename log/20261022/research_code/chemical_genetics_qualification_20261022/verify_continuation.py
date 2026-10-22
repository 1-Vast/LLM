"""Verify this continuation's receipts, with no new source values or requests."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/chemical_genetics_qualification"
target = BASE / "ROOT_VERIFICATION.json"
if target.exists():
    raise FileExistsError(target)


def read(relative):
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks = []
kernel = read("mechanism_review/KERNEL_AUDIT_RESULT.json")
checks.append({"name": "kernel_audit_pass_and_scope", "passed": kernel["passed"] is True and
               kernel["source_response_values_used"] is False and len(kernel["cases"]) == 12})
checks.append({"name": "kernel_code_unchanged", "passed": kernel["code_sha256"] == sha(
    ROOT / "research/chemical_genetics_qualification_20261022/kernel_equivalence_audit.py")})
checks.append({"name": "kernel_protocol_unchanged", "passed": kernel["protocol_sha256"] == sha(
    BASE / "mechanism_review/KERNEL_AUDIT_PROTOCOL.md")})
inventory = read("graphics/INVENTORY.json")
network = read("workbook_identity/NETWORK.json")
checks.append({"name": "same_official_archive", "passed": inventory["archive_sha256"] ==
               network["sha256"] == sha(BASE / "workbook_identity/supplementaryFiles.raw.zip")})
for figure in inventory["figures"]:
    selected = figure["selected"]
    checks.append({"name": "image_" + figure["id"],
                   "passed": sha(Path(selected["path"])) == selected["sha256"]})
census = read("numeric_identity/CENSUS.json")
checks.append({"name": "day_only_census", "passed": census["status"] == "SEALED_IDENTITY_ONLY"
               and census["rows_verified"] == census["unique_keys"] == 60
               and census["numeric_day_string_all_rows_match"] is True
               and census["other_numeric_values_accessed"] is False
               and census["response_F_G_values_accessed"] is False
               and not census["duplicate_keys"] and not census["missing_expected_keys"]
               and not census["unexpected_keys"]})
checks.append({"name": "numeric_census_source_unchanged", "passed": census["source_sha256_before"] ==
               census["source_sha256_after"] == sha(Path(census["source_path"]))})
for relative in ("workbook_identity/VERIFICATION.json", "identity_followup/VERIFICATION.json"):
    checks.append({"name": relative, "passed": read(relative)["all_passed"] is True})
records = ["DECISION.md", "NARRATIVE_REVIEW.md", "identity_followup/EXPOSURE_CORRECTION.md",
           "graphics/INDEPENDENT_REVIEW.md", "mechanism_review/ADVOCATE.md",
           "mechanism_review/SKEPTIC.md", "mechanism_review/CROSS_ADVOCATE.md",
           "mechanism_review/CROSS_SKEPTIC.md"]
for relative in records:
    path = BASE / relative
    checks.append({"name": "record_" + relative, "passed": path.is_file(), "sha256": sha(path)})
for path in sorted((ROOT / "research/chemical_genetics_qualification_20261022").glob("*.py")):
    ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    checks.append({"name": "syntax_" + path.name, "passed": True})
result = {"all_passed": all(c["passed"] for c in checks), "checks": checks,
          "http_requests": 0, "new_response_values_read": False,
          "scope": "RECEIPT_AND_IMPLEMENTATION_VERIFICATION_ONLY"}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"all_passed": result["all_passed"], "checks": len(checks)}))
raise SystemExit(0 if result["all_passed"] else 1)
