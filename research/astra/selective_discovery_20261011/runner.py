"""Block P runner: execute registered arms over campaigns and persist one ledger per campaign x arm.

``tier='dev'``: the 1,403 exposed block-N compounds. Each sub-library is 60% of the 542 compounds with
GSE70138 signatures (seeded), treated as new; the reference is every other block-N compound.
``tier='confirm'``: the reference is all 1,403 block-N compounds. The 975 new compounds are split
into three disjoint sub-libraries (seeded). Outcomes come from the sealed tier, which ``extract`` refuses
until FREEZE.json exists.

Ledgers: ``<out>/<library>/<lineage>/<arm>.json`` holding the screened order, pre-reveal
predictions, refusals, LLM records (CONV) and the true hit flags of the screened compounds. They are
written atomically, and an existing ledger is reused, so an interrupted run resumes without
re-buying anything.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import campaign as CA  # noqa: E402
import world as WM  # noqa: E402

N_LIBRARIES = 3
DEV_POOL_SHARE = 0.6


def libraries(U, tier: str, seed: int = 20261011):
    """[(name, ref, pool)] for the tier."""
    rng = np.random.default_rng(seed)
    if tier == "dev":
        p2 = np.where(U.has_p2 & (U.group == "blockn"))[0]
        out = []
        for s in range(N_LIBRARIES):
            r = np.random.default_rng(seed + s)
            pool = np.sort(r.choice(p2, size=int(DEV_POOL_SHARE * len(p2)), replace=False))
            out.append((f"dev{s}", np.setdiff1d(np.where(U.group == "blockn")[0], pool), pool))
        return out
    new = np.where(U.group == "new")[0]
    perm = rng.permutation(new)
    ref = np.where(U.group == "blockn")[0]
    return [(f"lib{s}", ref, np.sort(perm[s::N_LIBRARIES])) for s in range(N_LIBRARIES)]


def mask_cross(U, pool):
    """Pool compounds never serve as GSE92742 references (true for new compounds; imposed in dev)."""
    U.sims["vc_cross"][:, pool] = np.nan


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def ledger(U, H, st: CA.State, arm: str, extra=None):
    sel = [c for _, c in st.screened]
    return {"arm": arm, "lineage": U.lineages[st.t], "budget": st.budget, "batch": st.batch,
            "screened": [{"round": r, "brd": str(U.brd[c]), "name": str(U.name[c]), "idx": int(c),
                          "hit": bool(H[c, st.t])} for r, c in st.screened],
            "predictions": [{"idx": c, "p": p} for c, p in st.predictions],
            "refusals": st.refusals, "hits": int(H[sel, st.t].sum()) if sel else 0,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **(extra or {})}
