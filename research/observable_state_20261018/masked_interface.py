"""Role-gated masked outcome interface for D_search -> D_select -> D_transfer.

File summary
- Path: research/observable_state_20261018/masked_interface.py
- Purpose: the only way a study arm may learn anything about hidden campaign outcomes. The hidden evaluator is a callable
  supplied by the study (never imported here); this module enforces who may ask, how often, and in what form:
  * `search`   : returns one scalar utility per call for a submitted decision set; capped number of calls.
  * `select`   : returns only a boolean pass/fail against a threshold fixed at construction; smaller cap; the number of
                 bits released is recorded.
  * `transfer` : callable once, and only if the freeze check passes; returns the full result record.
  Every call is appended to a write-once ledger (jsonl) with role, units, digest of the request and what was released.
- Interfaces: `MaskedOutcomeInterface.query(role, decisions)`, `.ledger()`.
- Not a security boundary against a determined caller of the hidden callable; it is the accounting and refusal layer the
  repository's other studies use, with refusal reasons named.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROLES = ("search", "select", "transfer")


class AccessRefused(RuntimeError):
    pass


class MaskedOutcomeInterface:
    def __init__(self, hidden_utility, ledger_path, *, caps=None, select_threshold=None, freeze_check=None):
        """hidden_utility(role, decisions) -> float (search/select) or dict (transfer).

        caps: {"search": n, "select": m}; transfer is always one call. select_threshold: pass/fail line for `select`.
        freeze_check: callable raising SystemExit/Exception if the freeze does not hold (gates `transfer`).
        """

        self._f = hidden_utility
        self._path = Path(ledger_path)
        self._caps = {"search": 40, "select": 8, **(caps or {})}
        self._thr = select_threshold
        self._freeze = freeze_check
        self._n = {r: 0 for r in ROLES}
        if self._path.exists():
            for line in self._path.read_text(encoding="utf-8").splitlines():
                self._n[json.loads(line)["role"]] += 1

    def _log(self, role, decisions, released):
        rec = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "role": role, "n_decisions": len(decisions),
               "request_sha256": hashlib.sha256(json.dumps(decisions, sort_keys=True, default=str).encode()).hexdigest(),
               "released": released}
        with open(self._path, "ab") as fh:  # append-only
            fh.write((json.dumps(rec) + "\n").encode("utf-8"))

    def query(self, role, decisions):
        if role not in ROLES:
            raise AccessRefused("UNKNOWN_ROLE")
        if role == "transfer":
            if self._n["transfer"] >= 1:
                raise AccessRefused("TRANSFER_ALREADY_USED")
            if self._freeze is None:
                raise AccessRefused("TRANSFER_NEEDS_FREEZE_CHECK")
            try:
                self._freeze()
            except BaseException as e:  # noqa: BLE001 - any failure of the freeze check refuses the call
                raise AccessRefused(f"FREEZE_NOT_HOLDING: {e}") from None
            out = self._f("transfer", decisions)
            self._n["transfer"] += 1
            self._log(role, decisions, {"kind": "full_record"})
            return out
        if self._n[role] >= self._caps[role]:
            raise AccessRefused(f"{role.upper()}_CAP_REACHED")
        u = float(self._f(role, decisions))
        self._n[role] += 1
        if role == "search":
            self._log(role, decisions, {"kind": "scalar_utility"})
            return u
        if self._thr is None:
            raise AccessRefused("SELECT_NEEDS_THRESHOLD")
        passed = bool(u >= self._thr)
        self._log(role, decisions, {"kind": "pass_fail", "bits": 1})
        return passed

    def ledger(self):
        return [json.loads(x) for x in self._path.read_text(encoding="utf-8").splitlines()] if self._path.exists() else []
