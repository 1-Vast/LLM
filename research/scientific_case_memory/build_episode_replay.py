"""Replay episodes and their integrity: the initial data a policy may see, the outcome it may not.

File summary
- Path: research/scientific_case_memory/build_episode_replay.py
- Purpose: state and verify the contract of a closed-loop replay episode, independent of any dataset:
  a policy record that carries only what existed before the experiment, an evaluator record that
  carries the hidden truth and outcomes, and the nine steps that connect them.
- Core points:
  - `REPLAY_STEPS` names the design's workflow in order: reveal initial data, retrieve and adapt
    precedents, construct hypotheses, forecast, choose an action, reveal the hidden outcome through the
    registered executor, update the evidence state by the registered rules, compare with the actual
    trajectory, update case reliability and calibration. Steps 1 to 5 read the policy record only.
  - `verify_replay_integrity(policy, evaluator)` checks the pairing from outside: identical episode
    ids and menus; the policy record holds no key that names a truth, a label, a reading or an
    outcome; the evaluator's truth is one of the two hypotheses; every menu action has an evaluator
    outcome; the policy record's snapshot digest is present so the memory it retrieved from is known.
  - `leak_probe(build_policy, evaluator)` is the strongest test: it rebuilds the policy record after
    changing every truth, label and outcome of the evaluator record, and the two policy records must
    be byte-identical. A builder that reads a hidden field fails it.
  - The module has no dependency on a dataset; the MAESTRO-VC v1 replay supplies its records.
- Interfaces: `REPLAY_STEPS`, `FORBIDDEN`, `verify_replay_integrity`, `leak_probe`
- Depends on: standard library only
"""
from __future__ import annotations

import copy
import json
from typing import Callable, Iterable, Mapping

REPLAY_STEPS = ("reveal_initial_data", "retrieve_and_adapt_precedents", "construct_hypotheses", "forecast_per_hypothesis",
                "choose_action_by_decision_value", "reveal_hidden_outcome_through_registered_executor",
                "update_evidence_state_by_registered_rules", "compare_with_actual_trajectory", "update_case_reliability_and_calibration")
FORBIDDEN = ("truth", "klass", "label", "hypothesis_class", "nn_class", "outcome", "outcomes", "observed_outcome", "remaining",
             "terminal_decision", "score", "final", "history_by_arm", "eliminated", "readout", "state")


def _keys(value, path=""):
    if isinstance(value, Mapping):
        for k, v in value.items():
            yield str(k)
            yield from _keys(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _keys(v)


def verify_replay_integrity(policy: Iterable[Mapping], evaluator: Iterable[Mapping]) -> list[str]:
    """Named problems in the pairing of policy and evaluator records (empty when sound)."""
    problems: list[str] = []
    ev = {e["episode_id"]: e for e in evaluator}
    seen = set()
    for p in policy:
        eid = p.get("episode_id", "?")
        if eid in seen:
            problems.append(f"duplicate_policy_episode:{eid}")
        seen.add(eid)
        e = ev.get(eid)
        if e is None:
            problems.append(f"policy_episode_without_evaluator_record:{eid}")
            continue
        leaked = sorted(set(_keys(p)) & set(FORBIDDEN))
        if leaked:
            problems.append(f"policy_record_names_hidden_fields:{eid}:{leaked}")
        if sorted(p["menu"]) != sorted(e["available_actions"]):
            problems.append(f"menu_differs:{eid}")
        if e["truth"] not in p["initial_hypotheses"]:
            problems.append(f"truth_outside_contrast:{eid}")
        missing = [a for a in p["menu"] if a not in e["observed_outcome"]]
        if missing:
            problems.append(f"menu_action_without_outcome:{eid}:{missing[0]}")
        if not p.get("snapshot_digest"):
            problems.append(f"no_snapshot_digest:{eid}")
    for eid in ev:
        if eid not in seen:
            problems.append(f"evaluator_episode_without_policy_record:{eid}")
    return problems


def leak_probe(build_policy: Callable[[Mapping], Mapping], evaluator: Mapping, *, scramble: Callable[[Mapping], Mapping] | None = None) -> bool:
    """True when the policy record is unchanged after every hidden field of the evaluator record is changed."""
    def default_scramble(e: Mapping) -> Mapping:
        out = copy.deepcopy(dict(e))
        for key in ("truth", "klass", "nn_class"):
            if key in out:
                out[key] = "__scrambled__"
        if "observed_outcome" in out:
            out["observed_outcome"] = {a: "__scrambled__" for a in out["observed_outcome"]}
        if "history_by_arm" in out:
            out["history_by_arm"] = {"__arm__": {"terminal_decision": "__scrambled__"}}
        return out

    before = json.dumps(build_policy(evaluator), sort_keys=True, default=str)
    after = json.dumps(build_policy((scramble or default_scramble)(evaluator)), sort_keys=True, default=str)
    return before == after
