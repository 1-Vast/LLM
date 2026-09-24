"""Vision-model inspection of local scientific images with explicit interpretation limits.

File summary
- Path: src/agent/vision.py
- Purpose: Inspect supplied figures while marking them as non-measured observations.
- Core points:
  - `VisualInspector` reads figures only when supplied, never a plot into biological truth.
  - A visual reading is an observation, not a real measurement result.
- Interfaces: `VisualInspector`, `inspect`, `VisualInspection`, `VisionCompleter`
- Depends on: (standard library only)
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
_MAX_INLINE_BYTES = 32 * 1024 * 1024


class VisionCompleter(Protocol):
    def complete_json(self, messages: list[dict[str, Any]], **kwargs: Any) -> tuple[dict[str, Any], Any]: ...


@dataclass(frozen=True)
class VisualInspection:
    """A vision-model reading of one image, kept distinct from measured evidence."""

    path: Path
    observations: tuple[str, ...]
    quality_concerns: tuple[str, ...]
    decision_relevance: str
    limitations: tuple[str, ...]


class VisualInspector:
    """Reads figures only when supplied, and never converts a plot into biological truth."""

    def __init__(self, client: VisionCompleter, vision_model: str):
        self._client = client
        self._vision_model = vision_model

    def inspect(self, paths: tuple[Path, ...], *, question: str) -> tuple[VisualInspection, ...]:
        return tuple(self._inspect_one(path, question=question) for path in paths)

    def _inspect_one(self, path: Path, *, question: str) -> VisualInspection:
        mime_type = _MIME_TYPES.get(path.suffix.lower())
        if mime_type is None:
            raise ValueError(f"Unsupported visual asset type: {path.suffix}")
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size > _MAX_INLINE_BYTES:
            raise ValueError("Visual asset exceeds the inline vision request size limit.")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        prompt = """You are MAESTRO's scientific figure-inspection component. Return JSON only.
Describe only what is visible in the image: axes, labels, groups, annotations, visible
patterns, and image-quality concerns. Do not claim causality, target engagement, or
mechanistic truth from an image alone. State how the figure can inform the next evidence
question and what source data or controls are still needed.
Return {\"observations\":[\"...\"],\"quality_concerns\":[\"...\"],
\"decision_relevance\":\"...\",\"limitations\":[\"...\"]}."""
        data, _ = self._client.complete_json(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Research question: " + question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            model=self._vision_model,
        )
        return VisualInspection(
            path=path,
            observations=_text_items(data.get("observations")),
            quality_concerns=_text_items(data.get("quality_concerns")),
            decision_relevance=str(data.get("decision_relevance") or "No relevance stated."),
            limitations=_text_items(data.get("limitations")),
        )


def _text_items(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip()) if isinstance(value, list) else ()
