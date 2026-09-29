"""Audit of a case memory: is every case reusable, honest about its status and free of the traps a memory hides?

File summary
- Path: research/scientific_case_memory/case_quality_audit.py
- Purpose: inspect a set of cases (a store, a snapshot file or a list) and report, per check, how many
  cases fail it and which, so a memory is accepted or refused on evidence rather than on its size.
- Core points:
  - Checks: schema validity (`validate_case`); provenance completeness (builder, sources with a
    checksum-like value, creation date); typed status (no value on a non-biological observation, no
    biological measurement without a status); reading-code consistency (each `codes` string has one
    character per pool class, characters in `0123-`, no scored reading against the case's own class);
    orphan references (a measurement or update naming an action the case does not list); duplicate
    content (two case ids with identical content apart from the id); kind sanity (a failure case names a
    major failure mode, a contrastive case a contrast partner, an adaptation case complete links);
    version chain (each version supersedes the previous digest).
  - Leakage checks against a held-out set: no case names a held-out compound, and no case shares an
    independent unit with one. The held-out sets are supplied by the caller from evaluator-side data.
  - `kind_balance` reports counts of case kinds and of reading kinds, so a memory of successes only is
    visible as such; `failure_share` is the share of scored readings that are misleading or negative.
  - The audit never repairs anything and never raises on a bad case: it returns the finding.
- Interfaces: `audit_cases`, `audit_store`, `kind_balance`, `CHECKS`
- Depends on: case_schema.py, case_index.py, case_store.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping, Sequence

from . import case_index as CI
from . import case_schema as S
from . import case_store as CS

CHECKS = ("schema", "provenance", "typed_status", "reading_codes", "orphan_references", "duplicate_content", "kind_sanity",
          "version_chain", "heldout_compound", "heldout_unit")


def _content_key(case: S.Case) -> str:
    d = S.to_dict(case)
    for k in ("case_id", "supersedes", "provenance"):
        d.pop(k, None)
    d["context_fingerprint"] = {k: v for k, v in d["context_fingerprint"].items() if k not in ("compound", "unit", "smiles")}
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def kind_balance(cases: Iterable[S.Case]) -> dict:
    kinds: dict[str, int] = {}
    readings = {k.value: 0 for k in S.ReadingKind}
    scored = 0
    for c in cases:
        kinds[c.case_kind.value] = kinds.get(c.case_kind.value, 0) + 1
        for u in c.hypothesis_updates:
            for ch in u.codes:
                if ch in "0123":  # a malformed character is reported by `audit_cases`, never allowed to stop the audit
                    readings[CI.KIND_OF_CODE[int(ch)].value] += 1
                    scored += 1
    failure = readings["misleading"] + readings["negative"]
    return {"case_kinds": dict(sorted(kinds.items())), "reading_kinds": readings, "scored_readings": scored,
            "failure_share": failure / scored if scored else 0.0}


def audit_cases(cases: Sequence[S.Case], *, pool: Sequence[str] | None = None, heldout_compounds: Iterable[str] = (),
                heldout_units: Iterable[str] = (), latest_only: bool = True) -> dict:
    heldout_compounds, heldout_units = set(heldout_compounds), set(heldout_units)
    findings: dict[str, list[str]] = {c: [] for c in CHECKS}
    seen: dict[str, str] = {}
    by_id: dict[str, list[S.Case]] = {}
    for case in cases:
        by_id.setdefault(case.case_id, []).append(case)
    for case in cases:
        cid = f"{case.case_id}@v{case.case_version}"
        for err in S.validate_case(case):
            findings["schema"].append(f"{cid}:{err}")
        prov = case.provenance
        if not prov.get("builder") or not prov.get("created_at") or not prov.get("sources"):
            findings["provenance"].append(cid)
        for ref in case.raw_data_references:
            if len(ref.sha256) != 64:
                findings["provenance"].append(f"{cid}:bad_checksum:{ref.uri}")
        for o in case.initial_observations:
            if not o.status.biological and (o.value is not None or o.readout is not None):
                findings["typed_status"].append(f"{cid}:{o.condition_id}:{o.status.value}_carries_a_value")
        for m in case.real_measurements:
            if not isinstance(m.status, S.MeasurementStatus):
                findings["typed_status"].append(f"{cid}:{m.action_id}:untyped")
        actions = {a.action_id for a in case.candidate_actions}
        for m in case.real_measurements:
            if m.action_id not in actions:
                findings["orphan_references"].append(f"{cid}:{m.action_id}")
        for u in case.hypothesis_updates:
            if u.action_id not in actions:
                findings["orphan_references"].append(f"{cid}:{u.action_id}")
            if u.codes:
                if pool is not None and len(u.codes) != len(pool):
                    findings["reading_codes"].append(f"{cid}:{u.action_id}:length")
                if set(u.codes) - set("0123-"):
                    findings["reading_codes"].append(f"{cid}:{u.action_id}:alphabet")
                if pool is not None and case.context_fingerprint.get("hypothesis_class") in pool:
                    own = list(pool).index(case.context_fingerprint["hypothesis_class"])
                    if own < len(u.codes) and u.codes[own] != "-":
                        findings["reading_codes"].append(f"{cid}:{u.action_id}:scored_against_its_own_class")
        if case.case_kind is S.CaseKind.FAILURE and not any(m.severity == "major" for m in case.failure_modes):
            findings["kind_sanity"].append(f"{cid}:failure_without_major_mode")
        if case.case_kind is S.CaseKind.CONTRASTIVE and not any(m.code.startswith("contrast") for m in case.failure_modes):
            findings["kind_sanity"].append(f"{cid}:contrastive_without_partner")
        if case.case_kind is S.CaseKind.ADAPTATION and any(l.success is None for l in case.adaptation_map):
            findings["kind_sanity"].append(f"{cid}:adaptation_link_unresolved")
        if case.case_kind is not S.CaseKind.ADAPTATION:
            key = _content_key(case)
            if key in seen and seen[key] != case.case_id:
                findings["duplicate_content"].append(f"{case.case_id}=={seen[key]}")
            seen.setdefault(key, case.case_id)
        name = case.context_fingerprint.get("compound")
        unit = case.context_fingerprint.get("unit")
        if name in heldout_compounds:
            findings["heldout_compound"].append(cid)
        if unit in heldout_units:
            findings["heldout_unit"].append(cid)
    for cid, versions in by_id.items():
        versions = sorted(versions, key=lambda c: c.case_version)
        for i, v in enumerate(versions):
            expected = S.digest(versions[i - 1]) if i else None
            if v.case_version != i + 1 or v.supersedes != expected:
                findings["version_chain"].append(f"{cid}@v{v.case_version}")
    latest = [sorted(vs, key=lambda c: c.case_version)[-1] for vs in by_id.values()]
    balance = kind_balance(latest)
    return {"cases": len(by_id), "versions": len(cases), "checks": {k: {"failures": len(v), "examples": v[:5]} for k, v in findings.items()},
            "passed": all(not v for v in findings.values()), "balance": balance}


def audit_store(store: CS.CaseStore, **kw) -> dict:
    result = audit_cases(store.all_versions(), **kw)
    result["store_verify"] = list(store.verify())
    result["snapshot_digest"] = store.snapshot_digest()
    return result
