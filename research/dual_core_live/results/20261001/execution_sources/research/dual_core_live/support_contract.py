"""Optional research policy support checks; never create forecasts or evidence.

The contract declares a defer fallback for forecast-required planning. It does
not require forecasts for fixed/no-forecast policies or rank alternative actions.
"""
from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from research.dual_core_live.live_api import validate_proposal


FORECAST_SUPPORT_CONTRACT = {"forecast_required": True, "fallback": "defer"}


def support_violations(
    card: Mapping[str, Any], proposal: Any, contract: Mapping[str, Any] | None = None
) -> tuple[str, ...]:
    """Report violations without selecting a replacement or mutating inputs.

    Public action fields are ``forecast_available`` (explicitly true) and
    ``one_step_net_utility`` (finite numeric and strictly positive). These values
    remain planning forecasts; passing this check grants no evidence authority.
    """
    if contract is not None and (
        not isinstance(contract, Mapping) or set(contract) != {"forecast_required", "fallback"}
        or contract.get("forecast_required") is not True or contract.get("fallback") != "defer"
    ):
        return ("invalid_support_contract",)
    checked = validate_proposal(card, proposal)
    if not checked["accepted"]:
        return (checked["reason"],)
    if contract is None or checked["action"] == "defer":
        return ()
    action = next(a for a in card["actions"] if a["id"] == checked["action"])
    violations = []
    if action.get("forecast_available") is not True:
        violations.append("forecast_unavailable")
    if "one_step_net_utility" not in action:
        violations.append("forecast_utility_missing")
    else:
        value = action["one_step_net_utility"]
        if type(value) not in (int, float):
            violations.append("forecast_utility_invalid")
        else:
            try:
                finite = isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                violations.append("forecast_utility_nonfinite")
            elif value <= 0:
                violations.append("forecast_utility_nonpositive")
    return tuple(violations)


def gate_supported_proposal(
    card: Mapping[str, Any], proposal: Any, contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Apply only the declared defer fallback; never choose an optimal action."""
    violations = support_violations(card, proposal, contract)
    if contract is None:
        return {**validate_proposal(card, proposal), "violations": violations}
    if violations:
        invalid = "invalid_support_contract" in violations
        return {"accepted": False, "action": None if invalid else "defer",
                "reason": "invalid_support_contract" if invalid else "forecast_support_refusal",
                "violations": violations}
    return {"accepted": True, "action": proposal["action"],
            "reason": "forecast_support_checked", "violations": ()}
