"""Post-hoc admission and receipt rendering, without provider calls or new sources."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "outputs/map_module_replacement_20261009/agent_trial/hard"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def admission(answer, evidence):
    """Fail closed on contract errors; never coerce missing evidence into truth."""
    reasons = []
    if not isinstance(answer, dict) or set(answer) != set(evidence) or any(type(answer.get(k)) is not type(v) for k, v in evidence.items()):
        return ["invalid_schema"]
    if answer["molecule_status"] not in {"exact", "blocked", "source_unavailable", "unverified"} or answer["target_scope"] not in {"none", "single_protein_annotation", "family_membership"} or answer["action_identifier"] not in {"verify_exact_identity", "measure_case_target_engagement"}:
        reasons.append("invalid_enum")
    for key in ("qualified_card_ids", "reported_modes"):
        value = answer[key]
        if any(not isinstance(v, str) for v in value) or value != sorted(set(value)):
            reasons.append("invalid_" + key)
        elif set(value) - set(evidence[key]):
            reasons.append("unauthorized_" + key)
    if answer["molecule_status"] != evidence["molecule_status"]:
        reasons.append("unauthorized_identity")
    if answer["action_identifier"] != evidence["action_identifier"]:
        reasons.append("unauthorized_action")
    for key in ("requested_mode_supported", "binding_assay_annotation", "direct_interaction_assertion", "source_conflict_detected", "case_measurement_supported", "independent_biological_confirmation"):
        if answer[key] and not evidence[key]:
            reasons.append("unauthorized_" + key)
    if answer["target_scope"] != "none" and answer["target_scope"] != evidence["target_scope"]:
        reasons.append("unauthorized_target_scope")
    return reasons


def main():
    frozen = read(HERE / "GUARD_FREEZE.json")
    for path, expected in frozen["files"].items():
        if sha(ROOT / path) != expected:
            raise AssertionError("Post-hoc guard freeze changed: " + path)
    spec = importlib.util.spec_from_file_location("independent_hard_reconstruction", HERE / "verify_hard.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    cases = {c["id"]: c for c in read(HERE / "CASES.json")}
    sources = {c["case_id"]: c for c in read(OUT.parent / "SOURCES.v3.json")["cases"]}
    inputs = {e["episode_id"]: e for e in read(OUT / "HARD_INPUTS.json")}
    truths = {c["case_id"]: c["expected"] for c in read(OUT / "HARD_REFERENCE.json")["cases"]}
    summaries, records = {}, []
    for original in read(OUT / "HARD_RESPONSES.json")["records"]:
        case = cases[original["case_id"]]
        prior = inputs[original["episode_id"]]["priors"][original["arm"]]
        identity = next((i["payload"] for i in original["inspections"] if i["tool_id"] == "exact_identity"), None)
        kinds = {"mechanism" if i["tool_id"] == "mechanism" else "activity" for i in original["inspections"] if i["tool_id"] in {"mechanism", "assay"}}
        selected = [c for c in sources[original["case_id"]]["cards"] if c["kind"] in kinds]
        evidence = verifier.raw_qualification(case, prior, identity["molecule_status"] if identity else "unverified", identity.get("exact_molecule_ids", []) if identity else [], selected)
        answer, truth = original["answer"], truths[original["case_id"]]
        reasons = admission(answer, evidence)
        group = "source_positive" if truth["qualified_card_ids"] else "null_or_blocked"
        key = f"{original['arm']}:{group}"
        summary = summaries.setdefault(key, {"episodes": 0, "original_exact": 0, "admitted": 0, "admitted_exact": 0, "rejected": 0, "admitted_positive_card_assertions": 0,
                                             "truth_positive_card_assertions": 0, "receipt_render_exact": 0, "receipt_render_card_recall_numerator": 0, "receipt_render_card_recall_denominator": 0,
                                             "missing_unpurchased_qualifying_card_episodes": 0, "rejection_reasons": {}})
        summary["episodes"] += 1
        summary["original_exact"] += int(answer == truth)
        summary["admitted"] += int(not reasons)
        summary["admitted_exact"] += int(not reasons and answer == truth)
        summary["rejected"] += int(bool(reasons))
        summary["truth_positive_card_assertions"] += len(truth["qualified_card_ids"])
        if not reasons:
            summary["admitted_positive_card_assertions"] += len(set(answer["qualified_card_ids"]) & set(truth["qualified_card_ids"]))
        summary["receipt_render_exact"] += int(evidence == truth)
        summary["receipt_render_card_recall_numerator"] += len(set(evidence["qualified_card_ids"]) & set(truth["qualified_card_ids"]))
        summary["receipt_render_card_recall_denominator"] += len(truth["qualified_card_ids"])
        summary["missing_unpurchased_qualifying_card_episodes"] += int(bool(set(truth["qualified_card_ids"]) - set(evidence["qualified_card_ids"])))
        for reason in reasons:
            summary["rejection_reasons"][reason] = summary["rejection_reasons"].get(reason, 0) + 1
        records.append({"episode_id": original["episode_id"], "arm": original["arm"], "group": group, "admitted": not reasons, "rejection_reasons": reasons,
                        "admitted_answer": answer if not reasons else None, "receipt_rendering": evidence, "receipt_rendering_full_source_exact": evidence == truth})
    result = {"post_hoc": True, "created_utc": datetime.now(timezone.utc).isoformat(), "no_new_provider_calls": True, "original_responses_unchanged": True,
              "scope": "Strict admission retains or abstains; it does not repair retrieval or reasoning. Separate receipt rendering deterministically reconstructs only already purchased source assertions, not null coercion or rescued LLM advantage. Omitted/unpurchased source records cannot be recovered. Explicit source flag false means no qualifying inspected annotation, never negative biology.",
              "summaries": summaries, "records": records}
    target = OUT / "OFFLINE_GUARD.json"
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
