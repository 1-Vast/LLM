"""Deterministic evidence-channel routing; never buys or infers causal noise."""
ALLOWED_CHANNELS = ("axis", "control_noise", "treated_repeats", "transfer", "P2_certificate", "price")
ALLOWED_RECORD_KEYS = ("status", "source_verified", "receipt", "matched", "time_match", "independent_units", "registered")
STATUSES = ("missing", "blocked", "conflict", "failed", "verified", "qualified")
FORBIDDEN_FIELDS = ("train_B", "outcomes", "privatearrays", "private_arrays", "evaluator_private", "B_values", "B_outcome", "B_outcomes")
HYPOTHESES = dict(H1="Conditional control-cell sampling variability may be misrepresented.",
    H2="Source/sample/plate matching may limit transfer; causality is unresolved.",
    H3="The scalar RNA compression may omit response directions useful for decisions.",
    H4="A-to-B residual transfer may be weak after conditioning on admissible inputs.")


def _reject_private(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_FIELDS:
                raise ValueError("evaluation_B_or_private_arrays_forbidden")
            _reject_private(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_private(child)


def route(evidence):
    """Accept authenticated receipt statuses, not model claims or outcome arrays."""
    if not isinstance(evidence, dict):
        raise ValueError("strict_evidence_channel_records_required")
    _reject_private(evidence)
    if set(evidence) - set(ALLOWED_CHANNELS):
        raise ValueError("unknown_evidence_channel")
    for record in evidence.values():
        if not isinstance(record, dict) or set(record) - set(ALLOWED_RECORD_KEYS):
            raise ValueError("strict_source_receipt_record_required")
        if record.get("status", "missing") not in STATUSES:
            raise ValueError("unknown_source_receipt_status")
        for key in ("source_verified", "matched", "time_match", "independent_units", "registered"):
            if key in record and type(record[key]) is not bool:
                raise ValueError("source_receipt_flag_must_be_boolean")
        if "receipt" in record and not isinstance(record["receipt"], str):
            raise ValueError("source_receipt_identifier_must_be_text")

    def qualified(channel, required=()):
        record = evidence.get(channel, {})
        return (record.get("status") in ("verified", "qualified") and record.get("source_verified") is True
                and bool(record.get("receipt", "").strip()) and all(record.get(flag) is True for flag in required))

    def failure(channel):
        record = evidence.get(channel, {})
        return record.get("status") in ("failed", "conflict") and record.get("source_verified") is True and bool(record.get("receipt", "").strip())

    if not qualified("axis"):
        step, blockers = "authenticate_axis", ["Authenticated endpoint gene-coordinate axis is missing, failed or conflicted."]
    elif not qualified("control_noise"):
        step, blockers = "audit_controls", ["Authenticated weighted39gene control sampling audit is unavailable."]
    elif failure("treated_repeats") or failure("transfer") or failure("P2_certificate"):
        step, blockers = "direct_B_or_stop", ["An authenticated downstream qualification failed or conflicted; no acquisition is authorized."]
    elif not qualified("treated_repeats", ("matched", "time_match", "independent_units")):
        step, blockers = "request_matched_treated_repeats", ["Matched treated repeats with authenticated time and independent units are not available."]
    elif not qualified("transfer"):
        step, blockers = "paired_information_trial", ["Reliable paired A-to-B information transfer has not been certified."]
    elif not qualified("P2_certificate") or evidence["P2_certificate"].get("status") != "qualified":
        step, blockers = "paired_information_trial", ["An explicit qualified P2 release certificate is absent."]
    else:
        step, blockers = "consider_acquisition", []
        if not qualified("price", ("registered",)):
            blockers.append("Matched registered information prices are unavailable; monetary EVSI is undefined.")
    return dict(proposed_step=step, shadow=True, purchase_count=0, predicted_benefit=None,
        blocking_evidence=blockers, available_hypotheses=HYPOTHESES.copy(), hypotheses_status="Unresolved alternatives, not causal findings.",
        limitations="A control-cell full/diagonal variance ratio cannot establish the cause of A/B disagreement. Recommendations are referrals only; no fabricated outcomes, prices, net value or calibrated-risk certificate.")
