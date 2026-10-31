"""Aggregate measured receipts and record the scientific no-fit decision."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

EP = Path(__file__).resolve().parent.parent
ROOT = EP.parents[3]


def save(name, value):
    (EP / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


roles = {}
for role, attempts, byte_limit in [("root", 24, 64 << 20), ("investigator", 12, 16 << 20),
                                   ("scout", 8, 8 << 20), ("challenge", 8, 8 << 20)]:
    records = [json.loads(line) for line in (EP / role / "http_receipts.jsonl").read_text().splitlines()]
    complete = sum(row.get("completed_decoded_body_bytes", 0) for row in records)
    partial = sum(row.get("known_partial_decoded_body_bytes", 0) for row in records)
    roles[role] = {"attempts": len(records), "attempt_limit": attempts,
                   "completed_decoded_body_bytes": complete, "known_partial_decoded_body_bytes": partial,
                   "known_decoded_body_bytes": complete + partial, "byte_limit": byte_limit,
                   "receipt": role + "/http_receipts.jsonl"}
    assert len(records) <= attempts and complete + partial <= byte_limit

total_attempts = sum(role["attempts"] for role in roles.values())
total_bytes = sum(role["known_decoded_body_bytes"] for role in roles.values())
assert (total_attempts, total_bytes) == (44, 27000904)
save("usage.json", {
    "measured_utc": datetime.now(timezone.utc).isoformat(), "scope": "Current bounded episode; not program-wide",
    "roles": roles, "http_attempts": total_attempts, "http_attempt_limit": 52,
    "known_decoded_body_bytes": total_bytes, "known_decoded_body_byte_limit": 96 << 20,
    "inherited_three_episode_attempts": 137, "inherited_three_episode_bytes": 399366548,
    "four_episode_attempts": total_attempts + 137, "four_episode_attempt_limit": 252,
    "four_episode_known_decoded_body_bytes": total_bytes + 399366548,
    "four_episode_byte_limit": 704643072, "wire_bytes": None, "paid_cost": None,
    "input_tokens": None, "output_tokens": None, "cached_tokens": None,
    "requested_configurations": {"investigator": "gpt-6.1-sol/medium", "scout": "gpt-6.1-sol/high",
                                 "development": "gpt-6-astra/max (platform content flag; partial only)",
                                 "challenge": "gpt-6.1-sol/high"},
    "effective_configurations": None, "source_of_model_measurements": "Requested handles only; no effective native telemetry",
    "cpu_matrix_count": 0, "cpu_matrix_limit": 1, "implementation_repairs": 0,
    "substantive_revisions_after_v1": 0, "substantive_revision_limit": 2,
    "stop_reason": "Evidence sufficient to park transport question before fit; remaining shares unused",
})

jats = EP / "root/sources/peyre-transition-original.xml"
canonical = ROOT / "reference/papers/doi-10.1038-s44320-025-00150-0/supp-Fig_5C.xlsx"
with zipfile.ZipFile(EP / "root/sources/peyre-fig5-source.zip") as archive:
    member = archive.read("SD_Figure_5/Fig_5C.xlsx")
save("root/ancestry_check.json", {
    "existing_identity": "doi-10.1038-s44320-025-00150-0",
    "original_episode": "research/routes/observation_acquisition/2026-10-29-functional-rule-revision",
    "jats_sha256": hashlib.sha256(jats.read_bytes()).hexdigest(),
    "canonical_workbook": canonical.relative_to(ROOT).as_posix(),
    "canonical_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
    "new_zip_member_sha256": hashlib.sha256(member).hexdigest(),
    "identical": member == canonical.read_bytes(),
    "current_added_header_exposure": ["T2", "TBQ2", "T3", "T3TBQsurv2"],
    "response_values_projected": False, "library_duplicate_created": False,
})
save("root/scientific_decision.json", {
    "candidate": "probe_question_v1.md", "disposition": "PARK_BEFORE_FIT", "evidence_status": "UNTESTED",
    "contribution": "Conditional pre-next-challenge state sufficiency across histories/preparations; not a new algorithm",
    "scientific_claim_supported": False, "functional_benefit_demonstrated": False, "numerical_protocol_admitted": False,
    "reason": "Prospective observation/outcome contract, preparation/history support and discriminating precision are not authenticated",
    "not_disqualifying_in_itself": ["Outcome-labeled reporter columns without individual IDs",
                                  "Independent destructive endpoint cultures for a valid population-mean task"],
    "primary_rivals": ["Common conditional regression", "History interactions", "Survival/compartment/state-space models"],
    "source_owned_results": ["Peyre reporter and alternation findings", "Roux shared thresholds and three-agent predictions"],
    "restart": "One declared probe/endpoint with prospectively timed state, response encoding, survivor/replating policy, independent cultures, history support/overlap; then freeze numerical comparison and review",
    "initial_review": "challenge/initial_review.md", "initial_review_sha256": "3d6319126f7cd14f488e0f6430502f67354eed6c3898d57c5e04eb002ec8529d",
    "cpu_matrix_executed": False, "agent_or_core_promotion": False, "goal": "ACTIVE / NOT_ACHIEVED",
})
print("Receipt totals44attempts/27000904B; ancestry and no-fit decision recorded.")
