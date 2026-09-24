"""Priced accounting for paid provider calls, against a declared ceiling.

File summary
- Path: src/evaluation/provider_spend.py
- Purpose: make every paid call in a run appear in one ledger with its price, so provider
  spend is reported separately from laboratory cost and a ceiling is enforced before a call
  rather than discovered after it.
- Core points:
  - Rates are recorded with their source and the date they were verified, and a price is
    computed from the provider's own usage fields: cache-miss input, cache-hit input and
    output tokens are billed differently and are kept apart.
  - A call is reserved before it is made and charged after it returns. A call that fails
    after the provider processed tokens is charged at its reservation rather than at zero,
    because the conservative direction for spend is upward.
  - The ledger carries a declared prior total, so a session that continues a campaign states
    what it inherited instead of restarting the count at zero.
  - Exceeding the ceiling is refused by name (`provider_ceiling_exceeded`) before the call.
- Interfaces: `RATES`, `price_usage`, `SpendEntry`, `SpendLedger`
- Depends on: (standard library only)
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

# Verified on 2026-09-12 against the provider's published pricing and recorded in the campaign
# ledger of that day; US dollars per million tokens.
RATES: Mapping[str, object] = {
    "model": "deepseek-flash",
    "input_cache_miss": 0.3,
    "input_cache_hit": 0.006,
    "output": 1.2,
    "verified_on": "2026-09-12",
    "source": "https://api-docs.deepseek.com/quick_start/pricing",
}


def price_usage(usage: Mapping[str, object]) -> float:
    """Price one call from the provider's own usage fields, in US dollars."""

    def value(name: str, fallback: int = 0) -> int:
        raw = usage.get(name, fallback)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)) or raw < 0:
            return fallback
        return int(raw)

    miss = value("prompt_cache_miss_tokens", value("prompt_tokens"))
    hit = value("prompt_cache_hit_tokens")
    output = value("completion_tokens")
    return (
        miss * float(RATES["input_cache_miss"])
        + hit * float(RATES["input_cache_hit"])
        + output * float(RATES["output"])
    ) / 1_000_000


@dataclass(frozen=True)
class SpendEntry:
    """One provider call: what it was for, what it cost, and whether it returned."""

    at: str
    label: str
    status: str
    reserved_usd: float
    charged_usd: float
    usage: Mapping[str, object]
    note: str = ""

    def payload(self) -> Mapping[str, object]:
        return {
            "at": self.at,
            "label": self.label,
            "status": self.status,
            "reserved_usd": round(self.reserved_usd, 8),
            "charged_usd": round(self.charged_usd, 8),
            "usage": dict(self.usage),
            "note": self.note,
        }


@dataclass
class SpendLedger:
    """An append-only priced ledger for one run, with a declared prior total and a ceiling."""

    path: Path
    ceiling_usd: float = 5.0
    prior_total_usd: float = 0.0
    prior_note: str = ""
    entries: list[SpendEntry] = field(default_factory=list)

    @property
    def session_total_usd(self) -> float:
        return sum(entry.charged_usd for entry in self.entries)

    @property
    def total_usd(self) -> float:
        return self.prior_total_usd + self.session_total_usd

    @property
    def remaining_usd(self) -> float:
        return self.ceiling_usd - self.total_usd

    def reserve(self, label: str, estimate_usd: float) -> None:
        """Refuse by name before a call that would exceed the declared ceiling."""

        if self.total_usd + estimate_usd > self.ceiling_usd:
            raise ValueError(
                "provider_ceiling_exceeded:"
                f"{label}:total={self.total_usd:.6f}+estimate={estimate_usd:.6f}>ceiling={self.ceiling_usd:.2f}"
            )

    def charge(
        self,
        label: str,
        usage: Mapping[str, object] | None,
        *,
        status: str = "ok",
        reserved_usd: float = 0.0,
        note: str = "",
    ) -> SpendEntry:
        """Record one call. A failure after token processing is charged at its reservation."""

        charged = price_usage(usage) if usage else (reserved_usd if status != "refused" else 0.0)
        entry = SpendEntry(
            at=datetime.now(timezone.utc).isoformat(),
            label=label,
            status=status,
            reserved_usd=reserved_usd,
            charged_usd=charged,
            usage=dict(usage or {}),
            note=note,
        )
        self.entries.append(entry)
        return entry

    def payload(self) -> Mapping[str, object]:
        return {
            "rates": dict(RATES),
            "ceiling_usd": self.ceiling_usd,
            "prior_total_usd": round(self.prior_total_usd, 8),
            "prior_note": self.prior_note,
            "session_total_usd": round(self.session_total_usd, 8),
            "total_usd": round(self.total_usd, 8),
            "remaining_usd": round(self.remaining_usd, 8),
            "calls": len(self.entries),
            "entries": [entry.payload() for entry in self.entries],
        }

    def write(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self.path

    @classmethod
    def load(cls, path: Path, *, ceiling_usd: float = 5.0, prior_total_usd: float = 0.0, prior_note: str = "") -> "SpendLedger":
        """Continue an existing ledger, or start one with a declared prior total."""

        if Path(path).is_file():
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            ledger = cls(
                path=Path(path),
                ceiling_usd=float(payload.get("ceiling_usd", ceiling_usd)),
                prior_total_usd=float(payload.get("prior_total_usd", prior_total_usd)),
                prior_note=str(payload.get("prior_note", prior_note)),
            )
            for entry in payload.get("entries", ()):
                ledger.entries.append(
                    SpendEntry(
                        at=str(entry.get("at", "")),
                        label=str(entry.get("label", "")),
                        status=str(entry.get("status", "ok")),
                        reserved_usd=float(entry.get("reserved_usd", 0.0)),
                        charged_usd=float(entry.get("charged_usd", 0.0)),
                        usage=dict(entry.get("usage", {})),
                        note=str(entry.get("note", "")),
                    )
                )
            return ledger
        return cls(path=Path(path), ceiling_usd=ceiling_usd, prior_total_usd=prior_total_usd, prior_note=prior_note)


def summarise(ledgers: Sequence[SpendLedger]) -> Mapping[str, object]:
    """Totals across several ledgers, for a record that reports one campaign figure."""

    return {
        "ledgers": len(ledgers),
        "calls": sum(len(ledger.entries) for ledger in ledgers),
        "session_total_usd": round(sum(ledger.session_total_usd for ledger in ledgers), 8),
        "total_usd": round(max((ledger.total_usd for ledger in ledgers), default=0.0), 8),
    }
