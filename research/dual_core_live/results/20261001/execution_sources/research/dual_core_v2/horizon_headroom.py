"""DIAGNOSTIC headroom for a third measurement: could any untried condition decide an undecided episode?

File summary
- Path: research/dual_core_v2/horizon_headroom.py
- Purpose: before defining any longer-horizon task, bound what a third measurement could add on the
  registered protocol-v2.1 tasks. For every block 7 reference episode that ended undecided after two
  measurements, the registered validator reads every untried design-available condition (the block 7
  fold context, executor `episodes.execute`). An episode "could be decided" if any such reading
  eliminates a hypothesis; "correctly" if the first eliminating reading in menu order removes the decoy.
- Core points: it reads outcomes, so it is an oracle ceiling, never a policy. Costs are the registered
  assay days of one extra condition. Nothing here changes a task.
- Interfaces: `headroom`; CLI `python -m research.dual_core_v2.horizon_headroom TRACES.pkl OUT.json`
- Depends on: research/protocol_v2 (tasks_v21, runner), research/belief_planning (world labels)
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def headroom(traces) -> dict:
    from research.protocol_v2 import runner as RN
    from research.protocol_v2 import tasks_v21 as TV
    E = TV.E
    out = {}
    groups = {}
    for t in traces:
        if t["arm"] == "reference" and t["measurements"] == 2 and not t["steps"][-1]["eliminated"]:
            groups.setdefault((t["dataset"], t["tier"], t["fold"]), []).append(t)
    for (ds, tier, fold), ts in sorted(groups.items()):
        data, ctx, setting, design = TV.load(ds, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        avail = TV.K.design_availability(design, setting.keys, sorted({t["compound"] for t in ts}))
        for t in ts:
            done = {tuple(s["key"]) for s in t["steps"]}
            local = RN.local_setting(setting, avail[t["compound"]])
            untried = [k for k in local.keys if k not in done]
            truth = comp.klass[t["compound"]]
            first, any_elim, extra_days, any_right, any_wrong = None, False, None, False, False
            for k in untried:
                r = E.execute(ctx, t["compound"], k, t["h1"], t["h2"])
                outcome = r.get("outcome")
                if outcome in ("eliminate_a", "eliminate_b") and r.get("qc", True):
                    any_elim = True
                    removed = t["h1"] if outcome == "eliminate_a" else t["h2"]
                    any_right |= removed != truth
                    any_wrong |= removed == truth
                    if first is None:
                        first = removed == truth
                        extra_days = setting.days(k)
            key = f"{ds}|{tier}"
            e = out.setdefault(key, {"undecided_after_two": 0, "with_untried_condition": 0, "some_reading_decides": 0,
                                     "first_decision_correct": 0, "first_decision_wrong": 0,
                                     "some_correct_reading": 0, "some_wrong_reading": 0, "only_correct_readings": 0,
                                     "units": set()})
            e["undecided_after_two"] += 1
            e["with_untried_condition"] += bool(untried)
            if any_elim:
                e["some_reading_decides"] += 1
                e["first_decision_correct"] += first is False
                e["first_decision_wrong"] += first is True
                e["some_correct_reading"] += any_right
                e["some_wrong_reading"] += any_wrong
                e["only_correct_readings"] += any_right and not any_wrong
                e["units"].add(t["unit"])
    for e in out.values():
        e["units_that_could_decide"] = len(e.pop("units"))
    return out


if __name__ == "__main__":
    sys.path[:0] = [str(ROOT), str(ROOT / "src")]
    res = {"status": "diagnostic oracle headroom (reads outcomes); block 7 reference traces",
           "result": headroom(pickle.load(open(sys.argv[1], "rb")))}
    Path(sys.argv[2]).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))
