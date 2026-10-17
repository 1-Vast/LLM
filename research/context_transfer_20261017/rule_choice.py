"""Apply the pre-declared selection-rule criterion of RULE_CHOICE.md to the development menus.

File summary
- Path: research/context_transfer_20261017/rule_choice.py
- Purpose: choose the frozen selection rule among "evidence", "max" and "hybrid" by minimax
  relative regret against the best fixed (rank, procedure) pipeline in each of the four
  development settings, exactly as RULE_CHOICE.md declares.
- Core points:
  - Reads only cached menus (no replay). Each rule is applied with `procedure.apply`, a pure
    function of the inner records.
  - Hindsight comparator per setting: the single (rank, procedure) with the highest mean outer
    hits over all contexts.
  - Writes RULE_CHOICE.json with every setting's table and the chosen rule.
- Interfaces: `python -B rule_choice.py`.
"""
from __future__ import annotations

import json

import numpy as np

import procedure
from common import CACHE, HERE, write_json

SETTINGS = {"prism_line": CACHE / "dev" / "menu_v2_line_w32_b8.json",
            "prism_lineage": CACHE / "dev" / "menu_v2_lineage_w32_b8.json",
            "proxy_random": CACHE / "power" / "v2_menu_w16_b4.json",
            "proxy_structured": CACHE / "power" / "s_v2_menu_w16_b4.json"}
RULES = ("evidence", "max", "hybrid")
TIE = 0.005
PREFERENCE = ("evidence", "hybrid", "max")


def evaluate(menu: dict) -> dict:
    fixed = {}
    for r in procedure.RANKS:
        rows = [x for entry in menu.values() for x in entry["outer"][str(r)]]
        for p in procedure.PROCEDURES:
            fixed[f"{p}@{r}"] = float(np.mean([x[p] for x in rows]))
    best_key = max(fixed, key=fixed.get)
    out = {"fixed": fixed, "best_fixed": best_key, "best_fixed_hits": fixed[best_key], "rules": {}}
    for rule in RULES:
        auto, choices = procedure.apply(menu, rule)
        hits = float(np.mean([v["auto"] for v in auto.values()]))
        out["rules"][rule] = {"hits": hits, "relative_regret": (fixed[best_key] - hits) / fixed[best_key],
                              "choices": {k: [v["rank"], v["procedure"]] for k, v in choices.items()},
                              "rounds": float(np.mean([v["auto_rounds"] for v in auto.values()]))}
    return out


def main():
    res = {"criterion": "RULE_CHOICE.md", "settings": {}}
    missing = [s for s, p in SETTINGS.items() if not p.exists()]
    if missing:
        raise SystemExit(f"MENU_MISSING: {missing}")
    for name, path in SETTINGS.items():
        menu = json.loads(path.read_text(encoding="utf-8"))["menu"]
        res["settings"][name] = evaluate(menu)
    worst = {rule: max(s["rules"][rule]["relative_regret"] for s in res["settings"].values()) for rule in RULES}
    low = min(worst.values())
    tied = [rule for rule in PREFERENCE if worst[rule] - low < TIE]
    res["max_relative_regret"] = worst
    res["chosen"] = tied[0]
    write_json(HERE / "RULE_CHOICE.json", res)
    for name, s in res["settings"].items():
        print(name, s["best_fixed"], round(s["best_fixed_hits"], 3),
              {r: (round(v["hits"], 3), round(v["relative_regret"], 3), v["rounds"]) for r, v in s["rules"].items()})
    print("max relative regret", {r: round(v, 4) for r, v in worst.items()}, "chosen", res["chosen"])


if __name__ == "__main__":
    main()
