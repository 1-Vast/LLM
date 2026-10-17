"""Post-hoc diagnostics of the revision failure (exploratory; development data only).

File summary
- Path: research/program_revision_20261017/diagnostics.py
- Purpose: explain why revision accepted almost nothing although the textbook seed library helped
  on future lineages. Not part of the registered analysis; written after RESULTS.json and labelled
  as such in REPORT.md. Reads only `Domain(open_future=False)` (source drugs x source lines) for
  the power check, and the cached per-line records (units_future.json) for stratum breakdowns.
- Checks:
  - D1 power of the frozen acceptance rule on the development arena: each seed program offered as
    an add edit to an empty library, and each seed program offered for retirement from the full
    seed library (does the arena have evidence either way?);
  - D2 the same for the seed programs judged on lineage-disjoint arenas would need a new design;
    instead D2 reports how many development query lines carry each seed program's gate
    (BRAF/KRAS/NRAS/PIK3CA/TP53/...) versus the future strata;
  - D3 Stage C per stratum (descriptive).
- Interfaces: ``python -B diagnostics.py`` writes DIAGNOSTICS.json.
"""
from __future__ import annotations

import json

import numpy as np

from common import CACHE, HERE, write_json
from engine import Domain, fixed_probe_design
from revise import SEED_LIBRARY, Bench, Edit, evaluate_edit, seed_library
from vc import LineContext, ProgramLibrary, parse_state


def main():
    dom = Domain(open_future=False)
    probes = fixed_probe_design(dom, 8)
    bench = Bench(dom, "I2", probes)
    out = {"_note": "post hoc, exploratory; development data only for D1"}
    d1 = []
    empty = ProgramLibrary()
    cur = bench.commit(empty)
    for scope, state in SEED_LIBRARY:
        rec, _ = evaluate_edit(bench, empty, cur, Edit("add", scope=scope, state=state, origin="seed-power"))
        d1.append({k: rec.get(k) for k in ("edit", "decision", "reason", "llr", "hits_new_only", "hits_cur_only",
                                           "distinguishing_pairs")})
    seed, _ = seed_library(bench)
    cur_s = bench.commit(seed)
    d1r = []
    for p in seed.programs:
        rec, _ = evaluate_edit(bench, seed, cur_s, Edit("retire", key=p.key, origin="seed-retire-power"))
        d1r.append({k: rec.get(k) for k in ("edit", "decision", "reason", "llr", "hits_new_only", "hits_cur_only")})
    out["D1_seed_add_from_empty"] = d1
    out["D1_seed_retire_from_seed"] = d1r
    # D2 gate prevalence: development query lines vs future strata (line features only, no outcome)
    L = dom.lines
    ctx = LineContext(dom.lf, np.arange(len(L)), {}, np.zeros(len(L)))
    split, role = L.line_split.to_numpy(), L.role.to_numpy()
    groups = {"dev_query": (split == "source") & (role == "query"), "dev_support": (split == "source") & (role == "support"),
              "future_line": split == "future_line", "future_lineage": split == "future_lineage"}
    d2 = {}
    for scope, state in SEED_LIBRARY:
        v = ctx.state(parse_state(state)) > 0.5
        d2[f"{scope}|{state}"] = {g: int(v[m].sum()) for g, m in groups.items()}
    d2["_lines"] = {g: int(m.sum()) for g, m in groups.items()}
    out["D2_gate_counts"] = d2
    # D3 Stage C per stratum from the cached per-line records
    kept = HERE / "records" / "units_future.json"
    units = json.loads((kept if kept.exists() else CACHE / "units_future.json").read_text(encoding="utf-8"))
    strata = np.array(units["_meta"]["stratum"])
    d3 = {}
    for k, rows in units["C"].items():
        h = np.array([r["hits"] for r in rows], float)
        d3[k] = {s: float(h[strata == s].mean()) for s in sorted(set(strata))}
    out["D3_stage_c_by_stratum"] = d3
    write_json(HERE / "DIAGNOSTICS.json", out)
    for r in d1:
        print("add", r["edit"]["scope"], r["edit"]["state"], r["decision"], r.get("reason"), r["llr"], r["hits_new_only"], r["hits_cur_only"])
    for r in d1r:
        print("retire", r["edit"]["key"], r["decision"], r.get("reason"), r["llr"], r["hits_new_only"], r["hits_cur_only"])
    print(json.dumps(d2))


if __name__ == "__main__":
    main()
