"""Model profiles for the capability ablation of block N.

``flash`` reproduces every earlier MAESTRO call: deepseek-flash through ``complete_json``, which
disables thinking. ``flash_think`` is the same model with thinking enabled; ``pro`` is
deepseek-v4-pro with thinking (its default). Prices are the provider's peak rates
(https://api-docs.deepseek.com/quick_start/pricing, read 2026-10-11); off-peak is half, so peak is a
conservative upper bound. The spend ledger prices flash usage itself at peak; a pro call's usage carries
its model name, so the ledger books the price computed here (off-peak half rate when the call ends in
an off-peak window, by the provider's published rule) as the reservation.
"""
from __future__ import annotations

RATES = {  # USD per million tokens, peak
    "deepseek-flash": {"hit": 0.006, "miss": 0.3, "out": 1.2},
    "deepseek-v4-pro": {"hit": 0.044, "miss": 1.32, "out": 3.96},
}
PROFILES = {
    "flash": {"model": "deepseek-flash", "thinking": False, "max_tokens": 3000},
    "flash_think": {"model": "deepseek-flash", "thinking": True, "max_tokens": 32000},
    "pro": {"model": "deepseek-v4-pro", "thinking": True, "max_tokens": 32000},
}
JSON_ONLY = {"role": "system", "content": "Return exactly one JSON object and no prose. Do not use markdown fences."}


def off_peak(when=None) -> bool:
    """Provider rule: peak is 01:00-04:00 and 06:00-10:00 UTC Monday-Friday; weekends are off-peak.
    Chinese public holidays are not modelled, so a holiday weekday is priced at peak (conservative)."""
    import datetime as _dt
    t = when or _dt.datetime.now(_dt.timezone.utc)
    if t.weekday() >= 5:
        return True
    return not (1 <= t.hour < 4 or 6 <= t.hour < 10)


def price(usage: dict | None, model: str, when=None) -> float:
    if not usage:
        return 0.0
    r = RATES[model]
    scale = 0.5 if off_peak(when) else 1.0
    hit = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
    miss = int(usage.get("prompt_cache_miss_tokens", max(0, int(usage.get("prompt_tokens", 0) or 0) - hit)) or 0)
    out = int(usage.get("completion_tokens", 0) or 0)
    return scale * (hit * r["hit"] + miss * r["miss"] + out * r["out"]) / 1e6


def call_json(client, messages: list[dict], profile: str):
    """One JSON completion under ``profile``; returns (object, response)."""
    from agent.llm import LLMError, json_object_from_text  # noqa: E402
    p = PROFILES[profile]
    if profile == "flash":
        return client.complete_json(messages, max_tokens=p["max_tokens"])
    resp = client.complete(list(messages) + [JSON_ONLY], model=p["model"], max_tokens=p["max_tokens"],
                           json_output=p["model"] != "deepseek-flash", thinking_enabled=p["thinking"])
    try:
        obj = json_object_from_text(resp.content)
    except Exception as error:  # unparseable or empty content is a named failure, not a guess
        raise LLMError(f"unparseable_content:{type(error).__name__}") from error
    if not isinstance(obj, dict):
        raise LLMError("unparseable_content:not_an_object")
    return obj, resp


def ledger_usage(usage: dict | None, profile: str) -> tuple[dict | None, float]:
    """(usage to book, reservation): pro usage is marked unpriced and booked at its peak price."""
    model = PROFILES[profile]["model"]
    if usage is None or model == "deepseek-flash":
        return usage, 0.01
    return {**usage, "model": model}, price(usage, model)
