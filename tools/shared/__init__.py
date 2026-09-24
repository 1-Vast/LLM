"""Shared support code for tools, offline runners and tests.

File summary
- Path: tools/shared/__init__.py
- Purpose: make the support package importable from any working directory and
  re-export its two entry points, so a caller writes one import instead of three.
- Core points:
  - This package carries **no** `manifest.json`, so `LocalToolCatalog` never offers
    it to the controller. It is support code, not a selectable tool.
  - `StubClient` stands in for the language-model client with a fixed response, so
    an offline test exercises the caller rather than the provider.
  - `state_fixture` builds the smallest asset, registration and request the real
    virtual-cell entry point accepts, which is what makes an admission test a test
    of admission rather than of plumbing.
- Interfaces: `StubClient`, and the names re-exported from `tools.shared.state_fixture`
- Depends on: virtual_cell, numpy, pytest
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from .stub_client import StubClient  # noqa: E402
from .state_fixture import (  # noqa: E402
    CONTROL,
    DEFAULT_BASIS,
    DRUG_A,
    DRUG_B,
    SHIFT,
    adapter,
    asset_sha256,
    joined,
    registration,
    request,
    requires_asset_runtime,
    write_asset,
    write_model,
)

__all__ = [
    "CONTROL",
    "DEFAULT_BASIS",
    "DRUG_A",
    "DRUG_B",
    "SHIFT",
    "StubClient",
    "adapter",
    "asset_sha256",
    "joined",
    "registration",
    "request",
    "requires_asset_runtime",
    "write_asset",
    "write_model",
]
