"""Feasibility F13 (exploratory; exposed block-N compounds): is the "unexpected hit" definition sound?

The registered definition calls a hit *unexpected* when no reference compound of the **same
annotated mechanism string** is a selective hit for that lineage. Repurposing Hub strings are
comma-separated token lists, so string equality is a strict notion of "same class": a hit annotated
"dopamine receptor antagonist, serotonin receptor antagonist" counts as unexpected even when a known
hit is annotated "dopamine receptor antagonist". That would overstate novelty.

Three nested definitions are compared on the development campaigns already recorded by F3:

* ``string``  (registered): no reference hit shares the exact mechanism string;
* ``token``   stricter: no reference hit shares **any** mechanism token;
* ``token_target`` strictest: no reference hit shares a mechanism token **or** an annotated target;
* ``token_target_chem`` adds: and no reference hit is within Morgan Tanimoto 0.4.

For each definition it reports how many reachable hits qualify and the virtual cell's contribution
(full stack minus the no-virtual-cell stack, at a 10% budget), so the registered definition can be
replaced before the freeze if it is the loose one that carries the effect.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import stats as ST  # noqa: E402
import world as WM  # noqa: E402

CHEM_T = 0.4


def tokens(s):
    return {x.strip() for x in str(s).split(",") if x.strip() and x.strip() != "nan"}


def masks(U, ref, t):
    """{definition: boolean mask over all compounds} marking a hit as unexpected under that definition."""
    H = U.hits()
    known = ref[H[ref, t]]
    ktok = set().union(*[tokens(U.moa[j]) for j in known]) if len(known) else set()
    ktgt = set().union(*[U.targets[j] for j in known]) if len(known) else set()
    kstr = set(U.moa[known]) - {"nan"}
    n = len(U.brd)
    same_string = np.isin(U.moa, list(kstr))
    share_token = np.array([bool(tokens(U.moa[i]) & ktok) for i in range(n)])
    share_target = np.array([bool(U.targets[i] & ktgt) for i in range(n)])
    if len(known):
        chem = U.sims["chem"][:, known]
        close = np.nan_to_num(chem, nan=0.0).max(1) >= CHEM_T
    else:
        close = np.zeros(n, bool)
    return {"string": H[:, t] & ~same_string,
            "token": H[:, t] & ~share_token,
            "token_target": H[:, t] & ~share_token & ~share_target,
            "token_target_chem": H[:, t] & ~share_token & ~share_target & ~close}


def main():
    U = WM.build(include_new=False)
    H = U.hits()
    f3 = pd.read_csv(HERE / "f3_rows.csv")
    f3 = f3[f3.frac == 0.10]
    p2 = np.where(U.has_p2)[0]
    defs = ["string", "token", "token_target", "token_target_chem"]
    rows = []
    for seed in sorted(f3.seed.unique()):
        rng0 = np.random.default_rng(20261011 + seed)
        pool = np.sort(rng0.choice(p2, size=int(0.6 * len(p2)), replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        for t, T in enumerate(U.lineages):
            sub = f3[(f3.seed == seed) & (f3["T"] == T)]
            if not len(sub):
                continue
            m = masks(U, ref, t)
            row = {"seed": seed, "T": T}
            for d in defs:
                row[f"reachable|{d}"] = int(m[d][pool].sum())
            rows.append(row)
    pool_df = pd.DataFrame(rows)
    print(pool_df[[f"reachable|{d}" for d in defs]].sum().to_string())
    # recount each arm's qualifying hits from the recorded selection orders
    orders = HERE / "f3_orders_selections.json"
    if not orders.exists():
        print("\nf3 did not store selection ids; recounting needs the orders. Reporting reachable counts only.")
        out = {"reachable": {d: int(pool_df[f"reachable|{d}"].sum()) for d in defs},
               "note": "arm-level recount unavailable: f3_orders.py recorded aggregate counts, not ids"}
        (HERE / "f13_novelty_definition.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        return
    sel = json.loads(orders.read_text(encoding="utf-8"))
    res = {}
    for d in defs:
        diffs, clusters = [], []
        for seed in sorted(f3.seed.unique()):
            rng0 = np.random.default_rng(20261011 + seed)
            pool = np.sort(rng0.choice(p2, size=int(0.6 * len(p2)), replace=False))
            ref = np.setdiff1d(np.arange(len(U.brd)), pool)
            for t, T in enumerate(U.lineages):
                key_a, key_b = f"{seed}|{T}|refit_all", f"{seed}|{T}|refit_novc"
                if key_a not in sel:
                    continue
                m = masks(U, ref, t)[d]
                diffs.append(int(m[sel[key_a]].sum()) - int(m[sel[key_b]].sum()))
                clusters.append(T)
        res[d] = ST.family({"vc": (np.array(diffs, float), np.array(clusters))}, alpha=0.05)["vc"]
        print(d, round(res[d]["estimate"], 1), "p_greater", round(res[d]["p_greater"], 4), res[d]["verdict"])
    out = {"reachable": {d: int(pool_df[f"reachable|{d}"].sum()) for d in defs},
           "vc_contribution": {d: {k: res[d][k] for k in ("estimate", "lower", "upper", "p_greater", "verdict")}
                               for d in defs}}
    (HERE / "f13_novelty_definition.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
