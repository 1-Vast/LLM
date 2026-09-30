"""One locked replay of the registered arms on one (study, tier, fold): sealed view, shared runner.

File summary
- Path: research/belief_planning/replay.py
- Purpose: run the registered comparator ladder and the belief-planning agent (with its
  attribution controls) on identical episodes. Every arm goes through `policies.run_matched` with
  the same menu, budget, QC rule and stopping. Write one record per (episode, arm), with the
  menus offered and any integrity problem.
- Core points:
  - Arms receive `firewall.seal(ctx)`: no held-out row, annotation or detection flag. The
    executor runs on the real context and reveals only what an arm buys (reading to the runner,
    profile to `Visible`).
  - The oracle is built on the real context and is flagged `reads_hidden_outcomes`. The
    permuted-feedback control is flagged `reads_other_episode_outcomes`. Neither is a candidate.
  - The ladder arms are the 2026-09-27 implementations (`external_validation/arms.py`), including
    the non-agent `myopic_edv`, measured-profile `retrieval`, `marginal_only` and the fixed
    expert order.
- Interfaces: `LADDER`, `AGENT`, `arm_table`, `run`
- Depends on: arms.py, tasks.py, research/external_validation/{arms,firewall}.py
"""
from __future__ import annotations

import time

from research.external_validation import arms as A
from research.external_validation import firewall as F

from . import arms as BA
from . import tasks as T
from . import world as W

P, C, E = T.P, T.C, T.E
LADDER = ("defer_floor", "random_legal", "fixed", "cost_only", "marginal_only", "retrieval", "magnitude",
          "magnitude_permuted", "ridge", "info_gain", "myopic_edv", "maestro_masked", "maestro_vc",
          "maestro_vc_permuted", "production_default", "sparse_two_step", "oracle")
AGENT = {
    "belief": {"build": lambda: BA.belief_arm(), "role": "primary_candidate"},
    "belief_vc_masked": {"build": lambda: BA.belief_arm(vc="masked"), "role": "control"},
    "belief_vc_permuted": {"build": lambda: BA.belief_arm(vc="permuted"), "role": "control"},
    "belief_feedback_withheld": {"build": lambda: BA.belief_arm(feedback="withheld"), "role": "control"},
    "belief_feedback_permuted": {"build": lambda: BA.belief_arm(feedback="permuted"), "role": "control",
                                 "reads_other_episode_outcomes": True},
    "belief_h1": {"build": lambda: BA.belief_arm(horizon=1), "role": "ablation"},
    "anchored": {"build": lambda: BA.belief_arm(anchor=True), "role": "secondary_candidate"},
}


def arm_table(real_ctx, execute, names) -> dict:
    table = {}
    for name in names:
        if name == "oracle":
            table[name] = A.make_oracle(real_ctx, execute)
        elif name in AGENT:
            table[name] = AGENT[name]["build"]()
        else:
            table[name] = A.REGISTRY[name]["build"]()
    return table


def executor(real_ctx, visible_of):
    def run_one(_ctx, compound, key, h1, h2):
        result = E.execute(real_ctx, compound, key, h1, h2)
        row = result.get("row")
        visible_of().reveal(key, real_ctx.data.shift[row] if result["qc"] and row is not None else None)
        return result
    return run_one


def run(meta: dict, real_ctx, fold: int, tier: str, setting, names, unit_of, *, episodes=None, limit=None) -> dict:
    """Seal, prepare and run `names` on the fold's episodes; returns records and integrity problems."""
    comp = real_ctx.data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == fold])
    sealed = F.seal(real_ctx, heldout, vc_factory=lambda d, det: A.StructureVC(d, det))
    sealed.extra["structure_vc"] = sealed.magnitude
    listed = T.prepare(sealed, fold, tier, real_ctx=real_ctx)
    episodes = listed if episodes is None else episodes
    if limit:
        episodes = episodes[:limit]
    problems = list(F.sealed_view_problems(sealed, heldout))
    if "ridge" in names:
        A.prepare(sealed)
    state = {"visible": None}
    run_one = executor(real_ctx, lambda: state["visible"])
    table = arm_table(real_ctx, E.execute, names)
    records = []
    for compound, truth, decoy, h1, h2 in episodes:
        for name, arm in table.items():
            state["visible"] = F.Visible()
            sealed.extra["visible"] = state["visible"]
            offered, clock = [], [0.0]

            def wrapped(c_, compound_, h1_, h2_, executed, menu, remaining, setting_, state_, arm=arm):
                offered.append([C.action_id(k) for k in menu])
                start = time.perf_counter()
                try:
                    return arm(c_, compound_, h1_, h2_, executed, menu, remaining, setting_, state_)
                finally:
                    clock[0] += time.perf_counter() - start

            row = P.run_matched(name, wrapped, sealed, compound, truth, h1, h2, setting, qc_rule="continue",
                                execute=run_one)
            violations = P.audit_record(row, setting)
            steps = row["steps"]
            notes = [(s.get("note") or {}) for s in steps]
            if name != "oracle" and any(n.get("reads_hidden_outcomes") for n in notes):
                violations.append("non_oracle_read_hidden_outcomes")
            if name in ("belief_vc_masked", "maestro_masked") and any(n.get("used_vc") for n in notes):
                violations.append("masked_arm_used_vc")
            problems += [f"{name}:{compound}:{v}" for v in violations]
            keys = [tuple(s["key"]) for s in steps]
            spec = AGENT.get(name) or A.REGISTRY.get(name, {})
            row.update({**meta, "fold": fold, "tier": tier, "decoy": decoy, "arm": name,
                        "role": spec.get("role", "comparator" if name != "oracle" else "bound"),
                        "reads_hidden_outcomes": name == "oracle",
                        "reads_other_episode_outcomes": bool(spec.get("reads_other_episode_outcomes")),
                        "offered": offered, "wells": 2 * len(keys) + 4 * len({(k[0], k[1]) for k in keys}),
                        "compute_seconds": clock[0], "provider_usd": 0.0,
                        "used_vc": any(n.get("used_vc") for n in notes),
                        "unit": str(unit_of.get(compound, compound))})
            records.append(C.clean(row))
    hyper = sealed.extra.get("world_hyperparameters")
    vc = sealed.extra["structure_vc"]
    features = [{"tier": tier, "fold": fold, "compound": c, "max_train_tanimoto": vc.max_similarity(c)}
                for c in sorted({e[0] for e in episodes})]
    return {"records": records, "problems": problems, "episodes": len(episodes), "features": features,
            "world_hyperparameters": hyper, "validator": {k: v for k, v in real_ctx.params.items() if k != "grid"}}


def forecasts_for_calibration(records) -> list[dict]:
    """Per executed step of the belief arms: the forecast for the truth branch and what was read."""
    out = []
    for r in records:
        if not r["arm"].startswith(("belief", "anchored", "maestro", "myopic_edv", "marginal_only", "sparse_two_step",
                                    "retrieval", "info_gain")):
            continue
        truth, other = r["truth"], (r["h2"] if r["truth"] == r["h1"] else r["h1"])
        for i, step in enumerate(r["steps"]):
            note = step.get("note") or {}
            pred = (note.get("prediction_by_hypothesis") or {}).get(truth)
            if not pred or not step["qc"]:
                continue
            outcome = step["outcome"]
            correct = (outcome == "eliminate_b" and truth == r["h1"]) or (outcome == "eliminate_a" and truth == r["h2"])
            wrong = (outcome == "eliminate_a" and truth == r["h1"]) or (outcome == "eliminate_b" and truth == r["h2"])
            out.append({"arm": r["arm"], "dataset": r.get("dataset"), "tier": r["tier"], "fold": r["fold"],
                        "compound": r["compound"], "unit": r["unit"], "step": i, "action": step["action"],
                        "line": step["key"][0], "time": step["key"][1], "dose": step["key"][2],
                        "p_correct": float(pred.get("p_correct", float("nan"))),
                        "p_wrong": float(pred.get("p_wrong", float("nan"))),
                        "support": pred.get("support", pred.get("local_support")),
                        "basis": note.get("basis", pred.get("basis")),
                        "y_correct": float(correct), "y_wrong": float(wrong), "other": other,
                        "detected": outcome not in ("undetected",)})
    return out
