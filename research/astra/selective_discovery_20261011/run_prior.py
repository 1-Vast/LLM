"""Generate the LLM lineage prior for every block-P compound (development and confirmation).

The model sees names and annotations only, never a viability value, so running it on confirmation
compounds before the freeze exposes no outcome; the outputs are hashed into FREEZE.json.
Arms:
* ``prior``: every compound (1,403 block-N + 975 new);
* ``prior_masked``: the name withheld, on the 542 development compounds that have phase-2
  signatures (a memorisation check: does the name add beyond annotation?).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import extract as EX  # noqa: E402
import llm_prior as LP  # noqa: E402

LINEAGES = ["lung", "skin", "central_nervous_system", "ovary", "pancreas", "colorectal", "upper_aerodigestive", "breast",
            "urinary_tract", "esophagus", "bone", "uterus", "liver", "gastric"]


def main(arms=("prior", "prior_masked")):
    info = pd.read_csv(ROOT / "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv")
    info["brd"] = info.broad_id.str[:13]
    meta = info.drop_duplicates("brd").set_index("brd")
    split = json.loads((ROOT / "research/astra/mechanism_routing_20261011/SPLIT.json").read_text(encoding="utf-8"))["units"]
    bn = sorted({u["prism_columns"][0].split("::")[0][:13] for u in split.values()})
    L = EX.load_l1000()
    new = [b for b, r in zip(L["brd"], L["role"]) if r == "new"]
    dev_p2 = [b for b, r in zip(L["brd"], L["role"]) if r == "blockn"]

    def task(arm, b):
        r = meta.loc[b]
        tg = [t.strip() for t in str(r["target"]).split(",") if t.strip() and t.strip() != "nan"]
        return (arm, b, str(r["name"]), str(r["moa"]), tg, str(r["phase"]), str(r["indication"]), LINEAGES)

    tasks = []
    if "prior" in arms:
        tasks += [task("prior", b) for b in bn + new]
    if "prior_masked" in arms:
        tasks += [task("prior_masked", b) for b in dev_p2]
    pr = LP.Prior(workers=12)
    out = pr.run(tasks)
    bad = [o for o in out if o["status"] != "ok" or o["n_missing"]]
    print(json.dumps({"n": len(out), "failed_or_incomplete": len(bad), "ledger_total_usd": pr.ledger.total_usd}, indent=1))


if __name__ == "__main__":
    main()
