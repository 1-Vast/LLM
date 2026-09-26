"""Post hoc: what the validator's gates prevent, against a naive "nearest class wins" reading.

File summary
- Path: research/dynamic_world_model/naive_reader.py
- Purpose: quantify unsupported belief updates (a registered secondary metric) for two naive
  readers that MAESTRO would get from an unguarded analysis, on every held-out compound, contrast
  and menu condition:
  - `nearest_class`: eliminate the hypothesis whose best projected similarity is lower, with no
    detection gate, floor or margin;
  - `absence_as_failure`: additionally conclude "the perturbation failed" whenever nothing is
    detected, which is wrong whenever the same compound gives a detected, correctly matching
    response at another condition of the menu.
- Labelled post hoc: neither reader is a registered arm. The validator column is the registered rule.
- Run: python research/dynamic_world_model/naive_reader.py
- Depends on: common.py, episodes.py, analyze.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import analyze as A
import common as C
import episodes as E


def main() -> None:
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    rows = []
    for ctx, fold in E.contexts(data, protocol, detected, magnitude):
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, fold):
            outcomes = {}
            for key in ctx.tier.keys:
                result = E.execute(ctx, compound, key, h1, h2)
                if not result["qc"]:
                    continue
                t = ctx.ft.tables[key]
                scores = C.heldout_class_scores(t, data.shift[result["row"]], ctx.ft.classes)
                s1, s2 = scores[ctx.ft.classes.index(h1)], scores[ctx.ft.classes.index(h2)]
                naive = None if not (np.isfinite(s1) or np.isfinite(s2)) else (h2 if s1 >= s2 else h1)
                outcomes[key] = (result["outcome"], naive, bool(detected[result["row"]]))
            decisive_elsewhere = any(o == ("eliminate_b" if decoy == h2 else "eliminate_a") for o, _, _ in outcomes.values())
            for key, (outcome, naive, det) in outcomes.items():
                eliminated = {"eliminate_b": h2, "eliminate_a": h1}.get(outcome)
                rows.append({"tier": ctx.tier.name, "compound": compound, "skeleton": comp.skeleton[compound],
                             "validator_wrong": float(eliminated == truth), "validator_correct": float(eliminated == decoy),
                             "naive_wrong": float(naive == truth), "naive_correct": float(naive == decoy),
                             "undetected": float(not det),
                             "absence_misread": float((not det) and decisive_elsewhere)})
    frame = pd.DataFrame(rows)
    summary = {"label": "post hoc; readers other than the validator are not registered arms"}
    for tier, sub in frame.groupby("tier"):
        summary[tier] = {name: A.bootstrap_mean(sub[name], sub.skeleton) for name in
                         ("validator_wrong", "validator_correct", "naive_wrong", "naive_correct", "undetected", "absence_misread")}
        summary[tier]["n"] = int(len(sub))
    C.write_json(C.OUTPUTS / "analysis" / "naive_reader_posthoc.json", C.clean(summary))
    for tier in ("B", "A"):
        s = summary[tier]
        print(tier, "n", s["n"], {k: f"{v['mean']:.3f} [{v['low']:.3f},{v['high']:.3f}]" for k, v in s.items() if isinstance(v, dict)})


if __name__ == "__main__":
    main()
