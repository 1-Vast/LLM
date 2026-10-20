"""POST HOC, EXPLORATORY diagnostics written AFTER the frozen evaluation was scored; they do not change the pre-registered label.
Reads the stored run (libraries, plans, worlds); no refit. Quantifies (1) how often the aref-range applicability exit fired for f1_plan and f1_plan_xplant and
(2) what the plan arm and the transplant arm would have done with the range check disabled (content-only transplant)."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pi_model as M  # noqa: E402
import pi_plan as PL  # noqa: E402
import pi_run as R  # noqa: E402
import pi_stats as ST  # noqa: E402
import pi_world as W  # noqa: E402

run = HERE / "RUN" / "eval"
streams, xp = ST.load(run)
out = {"label": "POST_HOC_EXPLORATORY_NOT_PREREGISTERED", "per_stream": {}, "pooled": {}}
acc = {}
for sid, d in streams.items():
    stream = W.make_stream(d["kind"], d["seed"])
    sc = stream["schedule"]
    z = np.load(run / "models" / f"{sid}.npz", allow_pickle=False)
    partner = next(o for o in streams.values() if o["kind"] == d["kind"] and o["seed"] != d["seed"])
    rec = {"f1_plan_rows_with_plan": 0, "f1_plan_inapplicable": 0, "xplant_rows_with_plan": 0, "xplant_inapplicable": 0}
    for r in d["rows"]:
        if r["arm"] == "f1_plan" and r["role"] == "task" and r.get("plan_applicable") is not None:
            rec["f1_plan_rows_with_plan"] += 1
            rec["f1_plan_inapplicable"] += int(r["plan_applicable"] is False)
    for r in xp[sid]["rows"]:
        if r.get("plan_applicable") is not None:
            rec["xplant_rows_with_plan"] += 1
            rec["xplant_inapplicable"] += int(r["plan_applicable"] is False)
    util = {}
    for c in range(4):
        lib = M.Lib.from_arrays(z, f"on|{c}|")
        for B in R.BUDGETS:
            for name, src in (("f1_plan_norange", d["plans"]), ("xplant_content_only", partner["plans"])):
                pj = src.get(f"f1_plan|{c}|{B}")
                pl = None if pj is None else PL.Plan.from_json(pj, force=True)
                if pl is not None:
                    pl.zmax = 1e12
                for bg in sc["batches"][c]:
                    if c + 1 < 2:
                        continue
                    b = stream["bgs"][bg]
                    camp = M.Camp(b["a"], b["y"], T=b["T"])
                    row = M.run_campaign(lib, camp, B, pl if pl is not None else M.Kg1(), arm=name)
                    util.setdefault((name, B), []).append(row["utility"])
    rec["utility"] = {f"{k[0]}@{k[1]}": float(np.mean(v)) for k, v in util.items()}
    out["per_stream"][sid] = rec
    for k, v in rec["utility"].items():
        acc.setdefault(k, []).append(v)
means, _, _, _ = ST.stream_means(streams, xp)
for k, v in acc.items():
    arm, B = k.split("@")
    ref = {s: means[s][("f1_kg1", int(B))] for s in means}
    out["pooled"][k] = {"mean": float(np.mean(v)), "minus_f1_kg1": float(np.mean(v) - np.mean(list(ref.values()))), "minus_f1_plan_prereg": float(np.mean(v) - np.mean([means[s][("f1_plan", int(B))] for s in means]))}
out["pooled"]["applicability_exit_totals"] = {k: int(sum(r[k] for r in out["per_stream"].values())) for k in ("f1_plan_rows_with_plan", "f1_plan_inapplicable", "xplant_rows_with_plan", "xplant_inapplicable")}
(HERE / "POSTHOC.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(out["pooled"], indent=1))
