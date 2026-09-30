"""Policy view and evaluator view: what a planner may see, and what only the scorer may see.

File summary
- Path: research/maestro_vc_v1/views.py
- Purpose: write the two views of every replay episode and audit that the policy view holds nothing a
  held-out truth could have shaped.
- Core points:
  - The policy view is built by a pure function over a whitelist (`POLICY_KEYS`): episode identity,
    the compound's public structure and independent unit, the two competing hypotheses, the study
    design's menu with its assay days, the budget, the digest of the case-memory snapshot the planner
    retrieves from, and the number of training references. It has no truth, no class label, no reading,
    no elimination and no arm result.
  - The evaluator view is the full episode: truth, every condition's exact reading, and each arm's
    choice and terminal decision.
  - `policy_view` ignores every field outside the whitelist, so a change to any truth, label or outcome
    leaves the policy view byte-identical; `audit_policy_records` checks the same property from the
    outside (unknown keys, forbidden tokens as keys, a hypothesis pair not containing... nothing, since
    a truth-free pair cannot be checked against a truth) and the digest of each record.
  - The menu of a policy view is the design's planned conditions: it does not move with an outcome
    (protocol v2.1). The evaluator's `available_actions` equals it.
- Interfaces: `POLICY_KEYS`, `FORBIDDEN_KEYS`, `policy_view`, `evaluator_view`, `audit_policy_records`,
  `view_digest`
- Depends on: standard library only
"""
from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping

POLICY_KEYS = ("episode_id", "dataset", "tier", "fold", "compound", "smiles", "unit", "initial_hypotheses", "menu",
               "menu_days", "max_measurements", "budget_days", "snapshot_digest", "training_references")
FORBIDDEN_KEYS = ("truth", "klass", "label", "hypothesis_class", "nn_class", "outcome", "outcomes", "observed_outcome",
                  "remaining", "terminal_decision", "score", "final", "history_by_arm", "eliminated", "readout", "state",
                  "validator", "detected", "qc", "agreement")


def policy_view(episode: Mapping, setting: Mapping, *, smiles: Mapping[str, str | None], snapshot_digest: str,
                training_references: int) -> dict:
    """The only representation of an episode a planner is given. Pure over the whitelist."""
    dataset, tier = episode["dataset"], episode["tier"]
    days = setting["days"]
    menu = sorted(episode["available_actions"])
    return {
        "episode_id": episode["episode_id"], "dataset": dataset, "tier": tier,
        "fold": int(str(episode["evaluation_split"]).replace("fold_", "")), "compound": episode["compound"],
        "smiles": smiles.get(episode["compound"]), "unit": episode["unit"],
        "initial_hypotheses": sorted(episode["initial_hypotheses"]), "menu": menu,
        "menu_days": {a: days[a] for a in menu if a in days}, "max_measurements": setting["max_measurements"],
        "budget_days": setting["budget_days"], "snapshot_digest": snapshot_digest,
        "training_references": int(training_references)}


def evaluator_view(episode: Mapping) -> dict:
    """Everything, including truth and exact outcomes. Held by the scorer and never passed to an arm."""
    return dict(episode)


def view_digest(record: Mapping) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _keys(value, path=""):
    if isinstance(value, Mapping):
        for k, v in value.items():
            yield f"{path}.{k}" if path else str(k), str(k)
            yield from _keys(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _keys(v, path)


def audit_policy_records(records: Iterable[Mapping]) -> list[str]:
    """Named problems: unknown top-level keys, forbidden keys at any depth, a truth-shaped field, empty menus."""
    problems: list[str] = []
    seen = set()
    for r in records:
        eid = r.get("episode_id", "?")
        if eid in seen:
            problems.append(f"duplicate_episode:{eid}")
        seen.add(eid)
        extra = set(r) - set(POLICY_KEYS)
        if extra:
            problems.append(f"unknown_keys:{eid}:{sorted(extra)}")
        for full, leaf in _keys(r):
            if leaf in FORBIDDEN_KEYS:
                problems.append(f"forbidden_key:{eid}:{full}")
        if not r.get("menu"):
            problems.append(f"empty_menu:{eid}")
        if len(r.get("initial_hypotheses", ())) != 2:
            problems.append(f"contrast_not_two_hypotheses:{eid}")
    return problems
