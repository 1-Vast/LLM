"""Recorded live-provider probes using the existing production API clients.

Provider output is a proposal or judgment. Contract validation and measured
evidence remain deterministic. The executable never changes provider settings.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping

from agent.decision_critic import TypeSafeJevClient, TypeSafeSettings, choice, noul
from agent.llm import DeepSeekChatClient, MAESTROSettings

ROOT = Path(__file__).resolve().parents[2]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, value: Any) -> None:
    """A run receipt is write-once, including its preregistration."""
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def safe_error(error: Exception) -> dict[str, Any]:
    """Record an error category/status without dumping provider request headers."""
    cause: BaseException | None = error
    status = None
    while cause is not None:
        if isinstance(getattr(cause, "code", None), int):
            status = cause.code
        cause = cause.__cause__
    return {"type": type(error).__name__, "http_status": status}


class RecordedDeepSeek(DeepSeekChatClient):
    """Capture safe request bodies and response envelopes; reuse provider transport."""

    def __init__(self, settings: MAESTROSettings):
        super().__init__(settings)
        self.exchanges: list[dict[str, Any]] = []

    def _send(self, request):
        body = json.loads(request.data)
        exchange = {"provider": "deepseek", "endpoint": request.full_url,
                    "request": body, "request_sha256": digest(body),
                    "transport_policy": "existing_client_bounded_transport_retries"}
        started = time.perf_counter()
        try:
            response = super()._send(request)
            exchange.update(response=response, response_sha256=digest(response),
                            served_model=response.get("model"), usage=response.get("usage", {}))
            return response
        except Exception as error:
            exchange["error"] = safe_error(error)
            raise
        finally:
            exchange["latency_seconds"] = time.perf_counter() - started
            self.exchanges.append(exchange)


class RecordedJev(TypeSafeJevClient):
    """The typed judgments are observable and never add measured evidence."""

    def __init__(self, settings: TypeSafeSettings):
        super().__init__(settings)
        self.exchanges: list[dict[str, Any]] = []

    def _send(self, body: Mapping[str, Any]):
        exchange = {"provider": "jev", "endpoint": self.settings.evaluate_url,
                    "request": body, "request_sha256": digest(body),
                    "transport_policy": "existing_client_bounded_transport_retries"}
        started = time.perf_counter()
        try:
            response = super()._send(body)
            exchange.update(response=response, response_sha256=digest(response),
                            served_model=response.get("model"), usage=response.get("usage", {}))
            return response
        except Exception as error:
            exchange["error"] = safe_error(error)
            raise
        finally:
            exchange["latency_seconds"] = time.perf_counter() - started
            self.exchanges.append(exchange)


def legal_actions(card: Mapping[str, Any]) -> list[str]:
    """Budget, authorized prerequisites, and attempted action history define legality."""
    qualified = set(card.get("qualified_prerequisites", []))
    attempted = set(card.get("attempted_actions", []))
    return [a["id"] for a in card["actions"]
            if a["cost"] <= card["remaining_budget"] and a["id"] not in attempted
            and set(a.get("prerequisites", [])).issubset(qualified)]


def validate_proposal(card: Mapping[str, Any], proposal: Any) -> dict[str, Any]:
    """Fail closed: free text can never execute a new action or create a terminal."""
    if not isinstance(proposal, dict):
        return {"accepted": False, "action": None, "reason": "proposal_not_object"}
    selected = proposal.get("action")
    legal = legal_actions(card)
    if selected != "defer" and selected not in legal:
        return {"accepted": False, "action": None, "reason": "action_not_currently_legal"}
    if proposal.get("terminal_authorized") is not False:
        return {"accepted": False, "action": None, "reason": "proposal_cannot_authorize_terminal"}
    return {"accepted": True, "action": selected, "reason": "contract_checked"}


SMOKE_CARDS = (
    {"id": "smoke_budget_prerequisite", "family": "generic_registered_measurement",
     "remaining_budget": 3, "qualified_prerequisites": [], "attempted_actions": [],
     "actions": [
         {"id": "m1", "cost": 2, "prerequisites": [], "description": "An available qualifying measurement."},
         {"id": "m2", "cost": 4, "prerequisites": ["target_activity"], "description": "A blocked measurement."}],
     "evidence": [], "forecasts": [], "objective": "Take an affordable unblocked measurement when one exists."},
    {"id": "smoke_prediction_boundary", "family": "generic_registered_measurement",
     "remaining_budget": 0, "qualified_prerequisites": [], "attempted_actions": [],
     "actions": [{"id": "m1", "cost": 2, "prerequisites": [], "description": "A registered measurement."}],
     "evidence": [], "forecasts": [{"reading": "target_activity", "kind": "model_prediction", "qc": "not_measured"}],
     "objective": "Select a legal action or defer. A forecast cannot supply a measurement or authorize a terminal."},
)

PROPOSER_PROMPT = (
    "You propose one next action under a registered experiment contract. Use only "
    "the supplied task state; do not assume external facts. Respect remaining_budget, "
    "qualified_prerequisites, and attempted_actions. A forecast is planning-only and "
    "cannot qualify evidence or authorize a terminal decision. Return JSON with "
    "exact keys action and terminal_authorized, e.g. "
    '{"action":"m1","terminal_authorized":false}. '
    "Use action defer if no legal useful action exists."
)


def provider_settings() -> tuple[MAESTROSettings, TypeSafeSettings]:
    deepseek = MAESTROSettings.from_workspace(ROOT)
    jev = TypeSafeSettings.from_workspace(ROOT)
    if jev is None:
        raise RuntimeError("TypeSafe settings are unavailable")
    return deepseek, jev


def assert_no_credentials(value: Any, secrets: tuple[str, ...]) -> None:
    encoded = canonical(value)
    if any(secret and secret in encoded for secret in secrets):
        raise RuntimeError("Credential detected in a run artifact; writing refused")


def smoke(out: Path) -> dict[str, Any]:
    deepseek_settings, jev_settings = provider_settings()
    # Exclusive directory creation makes an accidental repeated command harmless.
    out.mkdir(parents=True, exist_ok=False)
    sources = (Path(__file__), ROOT / "src/agent/llm.py", ROOT / "src/agent/decision_critic.py")
    predeclared = {
        "protocol": "dual-core-live-smoke-1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "logical_calls_per_provider": 2, "cards": SMOKE_CARDS, "cards_sha256": digest(SMOKE_CARDS),
        "proposer_prompt": PROPOSER_PROMPT, "expected_actions": ["m1", "defer"],
        "expected_prediction_is_measurement": False, "max_tokens": 160,
        "command": sys.argv, "python": sys.version, "platform": platform.platform(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_hashes": {p.relative_to(ROOT).as_posix(): file_digest(p) for p in sources},
        "provider_settings": {"deepseek": {"endpoint": deepseek_settings.base_url, "model": deepseek_settings.chat_model},
                              "jev": {"endpoint": jev_settings.evaluate_url, "model": jev_settings.model}},
        "limits": "Smoke only; no biological utility, calibration, or superiority claim. No training."
    }
    write_new(out / "predeclared.json", predeclared)
    deepseek, jev = RecordedDeepSeek(deepseek_settings), RecordedJev(jev_settings)
    rows = []
    for card in SMOKE_CARDS:
        messages = [{"role": "system", "content": PROPOSER_PROMPT},
                    {"role": "user", "content": canonical(card)}]
        try:
            proposal, response = deepseek.complete_json(messages, max_tokens=160)
            deepseek_result = {"proposal": proposal, "validation": validate_proposal(card, proposal),
                               "served_model": response.model, "usage": dict(response.usage)}
        except Exception as error:
            deepseek_result = {"error": safe_error(error), "validation": {"accepted": False, "action": None}}
        questions = (
            choice("legal_action", "Choose the affordable unblocked registered measurement, or defer if no action is legal.",
                   tuple(a["id"] for a in card["actions"]) + ("defer",)),
            noul("prediction_is_measurement", "Does this state include a qualified actual measurement, rather than only a model prediction?"),
        )
        evaluation = jev.evaluate(canonical(card), questions)
        jev_result = {"served_model": evaluation.model, "answers": {k: asdict(v) for k, v in evaluation.answers.items()},
                      "usage": dict(evaluation.usage), "refusals": evaluation.refusals()}
        rows.append({"card_id": card["id"], "deepseek": deepseek_result, "jev": jev_result,
                     "evidence_before_sha256": digest(card["evidence"]), "evidence_after_sha256": digest(card["evidence"])})
        artifacts = {"rows": rows, "exchanges": deepseek.exchanges + jev.exchanges}
        assert_no_credentials(artifacts, (deepseek_settings.api_key, jev_settings.api_key))
        write_new(out / f"card_{len(rows):02d}.json", {"result": rows[-1], "exchanges": [deepseek.exchanges[-1], jev.exchanges[-1]]})
    summary = {"protocol": predeclared["protocol"], "rows": rows,
               "logical_calls": {"deepseek": len(deepseek.exchanges), "jev": len(jev.exchanges)},
               "files": {p.name: file_digest(p) for p in out.iterdir() if p.is_file()}}
    write_new(out / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = smoke(args.out.resolve())
    print(json.dumps({"output": str(args.out), "logical_calls": result["logical_calls"], "rows": result["rows"]}, indent=2))


if __name__ == "__main__":
    main()
