"""Parity of the promoted source modules with the study code they were copied from.

File summary
- Path: research/context_transfer_20261017/parity.py
- Purpose: show that `virtual_cell.bridged_transfer`, `agent.bridge_design` and
  `agent.procedure_selection` reproduce this study's `vc.py`, `agent.py` and `procedure.py`
  on a PRISM 19Q4 development subset (exposed data; no confirmation outcome is read).
- Core points:
  - The same source fit at rank 10: maximum absolute difference of the predictive mean,
    variance, event probability and expected hits on held-out lines.
  - The same bridges (exploit, info, panel, lookahead) and the same final nominations.
  - The same inner records and the same choice from the procedure selector, and the same
    choice under every rule on every cached development menu.
  - Writes PARITY.json. Repair and model averaging were not promoted, so they are not compared.
- Interfaces: `python -B parity.py`.
"""
from __future__ import annotations

import importlib
import sys

import numpy as np

import agent as study_agent
import data_prism
import procedure as study_procedure
import vc as study_vc
from common import HERE, ROOT, folds, tie_order, write_json

# the study's agent.py shadows the source package of the same name; load the source package now
sys.modules.pop("agent", None)
sys.path.insert(0, str(ROOT / "src"))
bt = importlib.import_module("virtual_cell.bridged_transfer")
bd = importlib.import_module("agent.bridge_design")
ps = importlib.import_module("agent.procedure_selection")


def subset():
    d = data_prism.load()
    rows = np.sort(np.argsort(tie_order(d["contexts"], "parity-lines"))[:240])
    cols = np.sort(np.argsort(tie_order(d["items"], "parity-items"))[:400])
    Y = d["Y"][rows][:, cols].astype(float)
    ev, G = bt.selective_events(Y, data_prism.ABS_GATE, 100)
    ev_study, _ = __import__("common").selective_events(Y, data_prism.ABS_GATE, 100)
    return {"Y": Y, "X": d["X"][rows].astype(float), "events": ev, "events_study": ev_study, "G": G,
            "contexts": d["contexts"][rows], "groups": d["groups"][rows], "items": d["items"][cols]}


def main():
    d = subset()
    out = {"lines": len(d["contexts"]), "items": len(d["items"]),
           "endpoint_identical": bool((d["events"] == d["events_study"]).all())}
    fid = folds(d["contexts"], "context-transfer")
    src, tgt = np.flatnonzero(fid != 0), np.flatnonzero(fid == 0)[:12]
    kw = dict(rank=10, abs_gate=data_prism.ABS_GATE, min_measured=100, impute_iters=15)
    a = study_vc.ContextModel(**kw).fit(d["Y"][src], d["X"][src])
    b = bt.BridgedTransferModel(**kw).fit(d["Y"][src], d["X"][src])
    order = tie_order(d["items"], "tie")
    diffs = {"mean": 0.0, "var": 0.0, "event_prob": 0.0, "expected_hit": 0.0}
    same = {"exploit": True, "info": True, "panel": True, "lookahead": True, "final": True}
    pa, pb = study_agent.fixed_panel(a, 4, order), bd.fixed_panel(b, 4, order)
    same["panel"] = bool((pa == pb).all())
    for c in tgt:
        sa, sb = a.prior(d["X"][c]), b.prior(d["X"][c])
        for name, (u, v) in {"mean": (a.predict(sa)[0], b.predict(sb)[0]),
                             "var": (a.predict(sa)[1], b.predict(sb)[1]),
                             "event_prob": (a.event_prob(sa), b.event_prob(sb)),
                             "expected_hit": (a.expected_hit(sa), b.expected_hit(sb))}.items():
            diffs[name] = max(diffs[name], float(np.nanmax(np.abs(u - v))))
        for rule in ("exploit", "info", "lookahead"):
            ba = study_agent.choose_bridge(rule, a, sa, 4, 16, order)
            bb = bd.choose_bridge(rule, b, sb, 4, 16, order)
            same[rule] &= bool((ba == bb).all())
            if rule == "lookahead":
                fa = study_agent.nominate(a.expected_hit(a.posterior(sa, ba, d["Y"][c, ba])), 12, ba, order)
                camp = bd.run_campaign(b, d["X"][c], lambda idx: d["Y"][c, idx], 16, 4, "lookahead", order)
                same["final"] &= bool((np.concatenate([ba, fa]) == camp.wells).all())
    out["max_abs_diff"] = diffs
    out["identical_choices"] = same
    dom = {k: d[k] for k in ("Y", "X", "contexts", "groups", "items")}
    dom["events"], dom["G"] = d["events"], d["G"]
    menu = study_procedure.menu_records(dom, fid, 16, 4, data_prism.ABS_GATE, 100, 15, outer=False,
                                        only_folds={0}, ranks=(5, 10))
    inner = ps.source_replay(d["Y"][src], d["X"][src], d["contexts"][src], d["groups"][src], d["items"], 16, 4,
                             abs_gate=data_prism.ABS_GATE, min_measured=100, impute_iters=15, ranks=(5, 10),
                             salt="procedure:0")
    rec_same = all([{k: x[k] for k in ("context",) + ps.PROCEDURES} for x in menu[0]["inner"][r]] == inner[r]
                   for r in (5, 10))
    ca, cb = study_procedure.choose(menu[0]["inner"], "evidence"), ps.choose(inner, "evidence")
    out["selector"] = {"inner_records_identical": bool(rec_same), "study_choice": [ca["rank"], ca["procedure"]],
                       "source_choice": [cb.rank, cb.procedure],
                       "choice_identical": (ca["rank"], ca["procedure"]) == (cb.rank, cb.procedure)}
    # every rule on every cached development menu: identical choices
    from common import CACHE
    import json
    rule_same = True
    for path in [CACHE / "dev" / "menu_v2_line_w32_b8.json", CACHE / "dev" / "menu_v2_lineage_w32_b8.json",
                 CACHE / "power" / "v2_menu_w16_b4.json", CACHE / "power" / "s_v2_menu_w16_b4.json"]:
        menu = json.loads(path.read_text(encoding="utf-8"))["menu"]
        for entry in menu.values():
            for rule in ps.RULES:
                x, y = study_procedure.choose(entry["inner"], rule), ps.choose(entry["inner"], rule)
                rule_same &= (x["rank"], x["procedure"]) == (y.rank, y.procedure)
    out["selector"]["all_rules_all_menus_identical"] = bool(rule_same)
    out["numpy_fallback_max_abs_cdf_error"] = float(np.max(np.abs(
        bt.normal_cdf(np.linspace(-8, 8, 20001), exact=False) - bt.normal_cdf(np.linspace(-8, 8, 20001)))))
    out["parity"] = bool(out["endpoint_identical"] and max(diffs.values()) < 1e-9 and all(same.values())
                         and rec_same and out["selector"]["choice_identical"] and rule_same)
    write_json(HERE / "PARITY.json", out)
    print(out)


if __name__ == "__main__":
    main()
