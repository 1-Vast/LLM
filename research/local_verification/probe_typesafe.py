"""Probe the live TypeSafe Jev contract and report its response shape, never its key.

File summary
- Path: research/local_verification/probe_typesafe.py
- Purpose: the Jev field contract in `agent/typesafe.py` was written against documentation this
  environment could not reach, so every uncertain field is an alias that fails closed. This probe
  runs one small real evaluation from a machine that has the credentials and prints the response
  *structure*, so the aliases can be confirmed or corrected against fact rather than guess.
- Core points:
  - The key is read exactly as the application reads it and is never printed. Every line of output
    passes through a redactor that replaces the key, so even an echoing provider cannot leak it.
  - It calls the real client, then reaches past `evaluate()` for the unparsed body, because
    `evaluate()` deliberately converts failures into refusals and discards the payload.
  - An HTTP error body is captured too: that body usually names the field the provider rejected.
  - `--discover` is opt-in and asks the configured host which paths exist, for the case where the
    default evaluate path is wrong and everything returns 404.
- Interfaces: `main()`
- Depends on: agent.typesafe (standard library only otherwise)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agent.typesafe import (  # noqa: E402
    RESPONSE_ALIASES,
    JevEvaluation,
    TypeSafeJevClient,
    TypeSafeSettings,
    TypedAnswer,
    choice,
    noul,
    score,
    state_digest,
)

STATE = (
    "Case: a compound reduces viability in NCI-H596, while knockout of its nominated target "
    "does not. Two explanations remain live: (h1) the compound acts through an additional "
    "target; (h2) the knockout is incomplete so the target was never removed. "
    "Measured so far: viability for compound and knockout arms, 3 independent units each. "
    "Not measured: target engagement, residual protein, proximal pathway activity."
)

QUESTIONS = (
    noul("decision_separation", "Do the two explanations predict different outcomes for the proposed measurement?"),
    choice(
        "best_separating_action",
        "Which listed action best separates the two explanations? Answer with one listed identifier only.",
        ("rna_low", "engagement_shift", "proximal_activity", "orthogonal_rescue", "none_of_the_listed_options"),
    ),
    score("evidence_sufficiency", "How sufficient is the measured evidence for a development decision?", 5),
)

DISCOVERY_PATHS = ("/v1/systemone", "/v1/system-one", "/v1/evaluate", "/v1/jev", "/evaluate")
SCHEMA_PATHS = ("/openapi.json", "/v1/openapi.json", "/.well-known/openapi.json")


class Redactor:
    """Replace the credential with a placeholder in anything printed."""

    def __init__(self, secret: str):
        self._secret = secret or ""

    def __call__(self, text: str) -> str:
        if self._secret and len(self._secret) >= 8:
            return text.replace(self._secret, "<redacted>")
        return text


def shape(value: Any, depth: int = 0) -> Any:
    """Describe a payload by its keys and value types, not its content."""

    if depth > 3:
        return "..."
    if isinstance(value, Mapping):
        return {str(key): shape(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [shape(value[0], depth + 1), f"...x{len(value)}"] if value else []
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return type(value).__name__
    if isinstance(value, str):
        return f"str[{len(value)}]"
    return type(value).__name__


def describe_answer(answer: TypedAnswer) -> dict[str, Any]:
    return {
        "usable": answer.usable,
        "value": answer.value,
        "probability": answer.probability,
        "confidence": answer.confidence,
        "distribution": dict(answer.distribution or {}),
        "refusal": answer.refusal,
    }


def raw_request(url: str, key: str, body: Mapping[str, Any] | None, timeout: float) -> dict[str, Any]:
    """One request that reports the status and body of a failure instead of raising."""

    headers = {"Authorization": f"Bearer {key}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            return {"status": response.status, "body": response.read(2000).decode("utf-8", "replace")}
    except HTTPError as error:
        return {"status": error.code, "body": error.read(2000).decode("utf-8", "replace")}
    except (URLError, TimeoutError) as error:
        return {"status": None, "body": f"transport: {type(error).__name__}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Report the live Jev response shape without printing the key.")
    parser.add_argument("--workspace", type=Path, default=ROOT, help="Directory holding .env; defaults to the repository root.")
    parser.add_argument("--discover", action="store_true", help="On failure, ask the host which paths and schema exist.")
    parser.add_argument("--report", type=Path, help="Write the findings as JSON.")
    arguments = parser.parse_args()

    settings = TypeSafeSettings.from_workspace(arguments.workspace)
    if settings is None:
        print("typesafe: not configured in this workspace; the decision critic would simply not be built.")
        print("          set TYPESAFE_API_KEY, TYPESAFE_ENDPOINT and TYPESAFE_MODEL in .env to probe.")
        return 3

    redact = Redactor(settings.api_key)
    findings: dict[str, Any] = {
        "endpoint": settings.endpoint,
        "evaluate_url": settings.evaluate_url,
        "model": settings.model,
        "timeout_seconds": settings.timeout_seconds,
        "api_key_present": bool(settings.api_key),
        "api_key_length": len(settings.api_key),
        "state_digest": state_digest(STATE),
        "aliases_in_use": {name: list(names) for name, names in RESPONSE_ALIASES.items()},
    }
    print(f"endpoint      {settings.endpoint}")
    print(f"evaluate_url  {settings.evaluate_url}")
    print(f"model         {settings.model!r}")
    print(f"api key       present, {len(settings.api_key)} characters (value never printed)")
    print()

    client = TypeSafeJevClient(settings)
    body = {
        "model": settings.model,
        "state": STATE,
        "questions": {question.identifier: question.payload() for question in QUESTIONS},
    }
    findings["request_body_shape"] = shape(body)

    # `evaluate()` converts every failure into a refusal and keeps no payload, which is right for
    # production and useless for a probe. Go one level down for the unparsed response.
    raw: Any = None
    try:
        raw = client._send(body)  # noqa: SLF001 - deliberate: the probe needs the unparsed body.
        findings["transport"] = "ok"
        print("transport     ok")
        print("raw shape     " + redact(json.dumps(shape(raw), indent=1)))
        print()
        print("raw body      " + redact(json.dumps(raw, indent=1, ensure_ascii=False))[:4000])
        findings["raw_shape"] = shape(raw)
        findings["raw_body"] = json.loads(redact(json.dumps(raw, ensure_ascii=False)))
    except Exception as error:  # noqa: BLE001 - every failure mode is a finding here.
        cause = getattr(error, "__cause__", None)
        detail = ""
        if isinstance(cause, HTTPError):
            detail = cause.read(2000).decode("utf-8", "replace")
        findings["transport"] = redact(f"{type(error).__name__}: {error}")
        findings["error_body"] = redact(detail)
        print("transport     FAILED")
        print("  error       " + redact(f"{type(error).__name__}: {error}"))
        if detail:
            print("  body        " + redact(detail))

    if findings.get("transport") == "ok":
        evaluation = client.evaluate(STATE, QUESTIONS)
    else:
        # A second identical request would repeat the same retries and the same spend, and
        # `evaluate()` turns exactly this failure into exactly this refusal by construction.
        evaluation = JevEvaluation(
            settings.model, state_digest(STATE), {}, refusal=str(findings.get("transport"))
        )
    findings["evaluation"] = {
        "model_served": evaluation.model,
        "refusal": redact(evaluation.refusal) if evaluation.refusal else None,
        "usage": dict(evaluation.usage),
        "answers": {name: describe_answer(answer) for name, answer in evaluation.answers.items()},
        "usable": sorted(evaluation.usable_answers),
        "refusals": [redact(item) for item in evaluation.refusals()],
    }
    print()
    print("=== as the agent would read it ===")
    print(f"model served  {evaluation.model!r}")
    if evaluation.refusal:
        print(f"refused       {redact(evaluation.refusal)}")
    for name, answer in evaluation.answers.items():
        if answer.usable:
            print(f"  {name}: value={answer.value!r} p={answer.probability} confidence={answer.confidence}")
        else:
            print(f"  {name}: REFUSED {redact(str(answer.refusal))}")
    print(f"usage         {dict(evaluation.usage)}")

    if arguments.discover and (findings.get("transport") != "ok" or evaluation.refusal):
        base = settings.endpoint.rstrip("/")
        print()
        print("=== discovery (opt-in) ===")
        probes: dict[str, Any] = {}
        for path in SCHEMA_PATHS:
            outcome = raw_request(base + path, settings.api_key, None, settings.timeout_seconds)
            probes[f"GET {path}"] = {"status": outcome["status"], "body": redact(outcome["body"])[:300]}
            print(f"  GET  {path:<28} {outcome['status']}  {redact(outcome['body'])[:120]!r}")
        for path in DISCOVERY_PATHS:
            outcome = raw_request(base + path, settings.api_key, body, settings.timeout_seconds)
            probes[f"POST {path}"] = {"status": outcome["status"], "body": redact(outcome["body"])[:300]}
            print(f"  POST {path:<28} {outcome['status']}  {redact(outcome['body'])[:120]!r}")
        findings["discovery"] = probes

    if arguments.report:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(
            redact(json.dumps(findings, indent=1, ensure_ascii=False)) + "\n", encoding="utf-8"
        )
        print()
        print(f"report written to {arguments.report}")

    return 0 if findings.get("transport") == "ok" and not evaluation.refusal else 1


if __name__ == "__main__":
    raise SystemExit(main())
