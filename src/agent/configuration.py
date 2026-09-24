"""Runtime configuration for MAESTRO's OpenAI-compatible LLM endpoints.

File summary
- Path: src/agent/configuration.py
- Purpose: Load and hold the chat/vision model settings and secret API key.
- Core points:
  - `MAESTROSettings` carries the chat and vision model plus a secret API key.
  - The API key is never emitted in logs, exceptions, or `repr`.
- Interfaces: `MAESTROSettings`, `from_workspace`, `ConfigurationError`
- Depends on: (standard library only)
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when a required runtime setting is unavailable."""


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read simple dotenv assignments without exporting or logging secret values."""

    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


@dataclass(frozen=True)
class MAESTROSettings:
    """Settings required by the text and vision clients.

    The key is intentionally not represented in logs, exceptions, or ``repr``.
    """

    api_key: str
    base_url: str
    chat_model: str
    vision_model: str
    log_directory: Path
    timeout_seconds: float = 90.0
    max_tokens: int = 4_000

    def __repr__(self) -> str:
        return ("MAESTROSettings(api_key='<redacted>', base_url={!r}, chat_model={!r}, "
                "vision_model={!r}, log_directory={!r}, timeout_seconds={!r}, max_tokens={!r})").format(
                    self.base_url, self.chat_model, self.vision_model, self.log_directory,
                    self.timeout_seconds, self.max_tokens)

    @classmethod
    def from_workspace(cls, workspace: Path) -> "MAESTROSettings":
        """Load the existing DeepSeek configuration from the workspace dotenv file."""

        environment = _read_dotenv(workspace / ".env")
        required = (
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_BASE_URL",
            "DEEPSEEK_MODEL",
            "DEEPSEEK_VISION_MODEL",
        )
        missing = [name for name in required if not environment.get(name)]
        if missing:
            raise ConfigurationError(
                "Missing required MAESTRO provider settings: " + ", ".join(missing)
            )
        def setting(name: str) -> str:
            return os.environ.get(name) or environment[name]
        return cls(
            api_key=setting("DEEPSEEK_API_KEY"),
            base_url=setting("DEEPSEEK_BASE_URL").rstrip("/"),
            chat_model=setting("DEEPSEEK_MODEL"),
            vision_model=setting("DEEPSEEK_VISION_MODEL"),
            log_directory=workspace / "log" / "20260910",
        )
