"""Held-out internal development assessment of the frozen incumbents (writes records/held.json and RESULTS.json).

File summary
- Path: research/acquisition_program_20261018/evaluate.py
- Purpose: after FREEZE1 and FREEZE2, evaluate the fixed design, the handwritten lookahead, the two searched incumbents and the
  predecessor comparators on the held-out task groups (folds 2-4, target groups 2 and 3, five fresh paired noise scenarios).
  This is an internal development assessment on exposed data, not independent biological confirmation.
- Pure part: `contrasts_from_records(records)` recomputes every contrast from records/held.json (used by verify.py).
- Usage: ``python -B evaluate.py`` (write-once; the held-out cache is built by ``python -B ap_build.py held`` after FREEZE2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ap_analyse as AN  # noqa: E402
import ap_task as A  # noqa: E402
import metrics as M  # noqa: E402
import seal  # noqa: E402

PAIRS = (("lookahead_vs_fixed", "handwritten_lookahead", "fixed"), ("conventional_vs_fixed", "conventional_search", "fixed"),
         ("agent_vs_fixed", "agent_search", "fixed"), ("conventional_vs_lookahead", "conventional_search", "handwritten_lookahead"),
         ("agent_vs_lookahead", "agent_search", "handwritten_lookahead"), ("agent_vs_conventional", "agent_search", "conventional_search"),
         ("R1_vs_fixed", "R1", "fixed"), ("knn20_vs_fixed", "knn20", "fixed"), ("prior_vs_fixed", "prior", "fixed"),
         ("agent_vs_R1", "agent_search", "R1"), ("lookahead_vs_R1", "handwritten_lookahead", "R1"))
COMPARATORS = ("prior", "mixture_mean", "empcov_0.1", "knn10", "knn20", "knn40", "forest", "R1", "gated")


def contrasts_from_records(rec: dict) -> dict:
    folds = sorted(rec["family"], key=int)
    fam = np.concatenate([np.asarray(rec["family"][f]) for f in folds])

    def vec(arm):
        return np.concatenate([np.asarray(rec["per_compound"][arm][f], float) for f in folds])

    out = {}
    for name, a, b in PAIRS:
        r = M.paired_family(vec(a) - vec(b), fam, np.ones(len(fam), dtype=bool))
        out[name] = {k: r[k] for k in ("mean", "ci95", "p_one_sided", "n_families", "n_compounds")}
    out["rates_per_64_compounds"] = {a: float(vec(a).sum() / (len(fam) / M.CAMPAIGN)) for a in rec["per_compound"]}
    return out


def main() -> None:
    seal.check(1)
    seal.check(2)
    if (HERE / "RESULTS.json").exists():
        raise SystemExit("RESULTS.json exists; write-once")
    import ap_build as B
    inc = json.loads((HERE / "INCUMBENTS.json").read_text(encoding="utf-8"))
    data = B.load_all("held")
    programs = {"fixed": None, "handwritten_lookahead": inc["handwritten_lookahead"], "conventional_search": inc["conventional_search"],
                "agent_search": inc["agent_search"]}
    arms = {k: ("program", v) for k, v in programs.items()}
    arms.update({c: ("comparator", c) for c in COMPARATORS})
    cells, per_compound, totals = {}, {}, {}
    for k, a in arms.items():
        cells[k] = AN.arm_cells(data, a)
        pc = AN.per_compound(data, cells[k])
        per_compound[k] = {str(f): v.tolist() for f, v in pc.items()}
        totals[k] = AN.totals(data, cells[k])
        if a[0] == "program":
            totals[k]["lines_per_compound"] = float(np.mean([g["lines"] for v in cells[k].values() for g in v]))
        print(k, totals[k]["total"], flush=True)
    family = {}
    for task, _ in data:
        family[str(task.fold.fold)] = [str(x) for x in np.asarray(task.fold.hidden.family)[task.rows]]
    rec = {"per_compound": per_compound, "family": family}
    (HERE / "records").mkdir(exist_ok=True)
    (HERE / "records" / "held.json").write_bytes((json.dumps(rec) + "\n").encode())
    res = {"status": "internal development assessment on exposed folds 2-4; noise scenarios are paired draws, not biological samples",
           "incumbents": {k: v for k, v in inc.items() if k != "development_totals"}, "totals": totals,
           "contrasts": contrasts_from_records(rec), "practical_floor_events_per_64_compounds": 0.1875}
    diag = {}
    for k in ("handwritten_lookahead", "conventional_search", "agent_search"):
        diag[k] = AN.decision_diagnostics(data, programs[k])
    res["decision_diagnostics"] = diag
    res["hindsight_acquisition_choice_total_UNAVAILABLE"] = AN.hindsight_total(data)
    agree = {}
    for a, b in (("agent_search", "handwritten_lookahead"), ("conventional_search", "handwritten_lookahead"), ("agent_search", "conventional_search")):
        ra, rb = A.compile_program(programs[a]), A.compile_program(programs[b])
        same = n = 0
        for task, scs in data:
            for sc in scs:
                ca, cb = A.choose(sc["features"], ra), A.choose(sc["features"], rb)
                same += int((ca == cb).sum())
                n += len(ca)
        agree[f"{a}_vs_{b}"] = same / n
    res["choice_agreement"] = agree
    (HERE / "RESULTS.json").write_bytes((json.dumps(res, indent=1) + "\n").encode())
    for k, v in res["contrasts"].items():
        if k != "rates_per_64_compounds":
            print(k, round(v["mean"], 3), [round(x, 3) for x in v["ci95"]], round(v["p_one_sided"], 3))


if __name__ == "__main__":
    main()
