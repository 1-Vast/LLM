"""A dropped or reset connection is a named transport failure for both provider clients.

On 2026-09-26 a Jev evaluation raised `http.client.RemoteDisconnected` straight out of
`TypeSafeJevClient.evaluate`, whose contract is that a provider failure becomes a refusal and never
ends a MAESTRO turn. Neither client caught connection-level errors, which are neither `HTTPError`
nor `URLError`. These tests pin the repaired behaviour: retried, then refused (Jev) or raised as
the client's own transport error (DeepSeek), with the key never in the message.
"""
from __future__ import annotations

from http.client import RemoteDisconnected

import pytest

from agent import llm as llm_module
from agent import typesafe as typesafe_module
from agent.configuration import MAESTROSettings
from agent.llm import DeepSeekChatClient, LLMTransportError
from agent.typesafe import TypeSafeJevClient, TypeSafeSettings, choice

FAILURES = (RemoteDisconnected("Remote end closed connection without response"),
            ConnectionResetError(10054, "An existing connection was forcibly closed"))


@pytest.mark.parametrize("failure", FAILURES, ids=("remote_disconnected", "connection_reset"))
def test_jev_dropped_connection_becomes_a_refused_evaluation(monkeypatch, failure):
    attempts = []

    def drop(request, timeout=None):
        attempts.append(request)
        raise failure

    monkeypatch.setattr(typesafe_module, "urlopen", drop)
    monkeypatch.setattr(typesafe_module, "sleep", lambda seconds: None)
    client = TypeSafeJevClient(TypeSafeSettings("secret-key", "https://example.org", "jev-1.13"))

    evaluation = client.evaluate("state", [choice("next_action", "Which action?", ["a", "b"])])

    assert evaluation.answers == {}
    assert evaluation.refusal.startswith("JevTransportError:the connection failed:")
    assert type(failure).__name__ in evaluation.refusal
    assert len(attempts) == typesafe_module._MAX_ATTEMPTS
    assert "secret-key" not in evaluation.refusal


@pytest.mark.parametrize("failure", FAILURES, ids=("remote_disconnected", "connection_reset"))
def test_deepseek_dropped_connection_is_a_transport_error_after_retries(monkeypatch, tmp_path, failure):
    attempts = []

    def drop(request, timeout=None):
        attempts.append(request)
        raise failure

    monkeypatch.setattr(llm_module, "urlopen", drop)
    monkeypatch.setattr(llm_module, "sleep", lambda seconds: None)
    client = DeepSeekChatClient(MAESTROSettings("secret-key", "https://example.org", "model", "vision", tmp_path))

    with pytest.raises(LLMTransportError) as raised:
        client.complete_json([{"role": "user", "content": "Return {}."}])

    assert "lost its connection" in str(raised.value)
    assert len(attempts) == llm_module._MAX_ATTEMPTS
    assert "secret-key" not in str(raised.value)
