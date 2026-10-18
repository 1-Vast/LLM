"""Stage 1: generate every arm's edit for every eligible family from search-side evidence only; write EDITS.json once.

Requires FREEZE0. Reads no held-out cell (obs_core.search_view blanks held-out lineage columns and the family's held-out rows).
Agent calls: deepseek-flash, <= 3 per (episode, arm), 8 worker threads, each with its own client. Output is write-once.
"""
from __future__ import annotations

import json
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import obs_seal  # noqa: E402

warnings.filterwarnings("ignore")


def main():
    obs_seal.check(0)
    out = HERE / "EDITS.json"
    if out.exists():
        raise SystemExit("EDITS_EXIST (write-once)")
    import obs_arms as A
    import obs_core as O
    import research_edit as RE

    W = O.build_world()
    fams = list(W.episodes)
    stats = {f: O.search_stats(W, f) for f in fams}
    edits, none = [], []

    def add(f, rec, arm):
        if rec is None:
            none.append({"family": f, "arm": arm})
            return
        assert RE.validate(A.to_research_edit(W, f, rec)) == []
        edits.append(rec)

    for f in fams:
        for r in A.zero_edits(W, f):
            add(f, r, "zero")
        add(f, A.a2_edit(W, f, stats[f]), "a2")
        add(f, A.a2k_edit(W, f), "a2k")

    log = []

    def job(args):
        f, blind = args
        local = []
        r = A.agent_edit(W, f, A.make_client(), blind, stats[f], local)
        return f, blind, r, local

    with ThreadPoolExecutor(8) as ex:
        for f, blind, r, local in ex.map(job, [(f, b) for f in fams for b in (False, True)]):
            log += local
            add(f, r, "a3_blind" if blind else "a3")
    edits.sort(key=lambda r: (r["family"], r["arm"], r.get("meta", {}).get("draw", 0)))
    out.write_bytes((json.dumps({"edits": edits, "no_edit": none}, indent=1) + "\n").encode())
    (HERE / "LLM_LOG.json").write_bytes((json.dumps({"calls": log, "n_calls": len(log)}, indent=1) + "\n").encode())
    print("edits", len(edits), "no_edit", len(none), "llm calls", len(log))


if __name__ == "__main__":
    main()
