"""Run the baselines and both budget-matched searches on the development cells (writes the traces and INCUMBENTS.json).

File summary
- Path: research/acquisition_program_20261018/run_search.py
- Purpose: development only. Requires FREEZE1. Write-once outputs: SEARCH_TRACE_conventional.json,
  SEARCH_TRACE_agent.json, INCUMBENTS.json, DEV_BASELINES.json.
- Usage: ``python -B run_search.py``
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ap_analyse as AN  # noqa: E402
import ap_search as S  # noqa: E402
import seal  # noqa: E402


def main():
    seal.check(1)
    for f in ("SEARCH_TRACE_conventional.json", "SEARCH_TRACE_agent.json", "INCUMBENTS.json"):
        if (HERE / f).exists():
            raise SystemExit(f"{f} exists; write-once")
    t0 = time.time()
    dev = S.Dev()
    arms = {"fixed": ("program", None), "la": ("program", S.START),
            **{n: ("comparator", n) for n in ["prior", "mixture_mean", "empcov_0.1", "knn10", "knn20", "knn40", "forest", "R1", "gated"]}}
    base = {}
    fixed_cells = AN.arm_cells(dev.data, arms["fixed"])
    fixed_pc = AN.per_compound(dev.data, fixed_cells)
    for k, a in arms.items():
        c = AN.arm_cells(dev.data, a)
        base[k] = {"total": AN.totals(dev.data, c)["total"], "vs_fixed": AN.contrast(dev.data, AN.per_compound(dev.data, c), fixed_pc) if k != "fixed" else None}
        print(k, base[k]["total"], flush=True)
    base["hindsight_acquisition_choice_total_UNAVAILABLE"] = AN.hindsight_total(dev.data)
    S.write_trace(HERE / "DEV_BASELINES.json", base)
    conv = S.conventional_search(dev)
    S.write_trace(HERE / "SEARCH_TRACE_conventional.json", conv)
    print("conventional incumbent", conv["incumbent"], f"{time.time() - t0:.0f}s", flush=True)
    client = S.make_client()
    agent = S.agent_search(dev, client, log=lambda *a: print(*a, flush=True))
    agent["provider_usage"] = client.provider_usage
    S.write_trace(HERE / "SEARCH_TRACE_agent.json", agent)
    inc = {"fixed": None, "handwritten_lookahead": S.START, "conventional_search": conv["incumbent"], "agent_search": agent["incumbent"],
           "development_totals": {k: dev.summary(dev.result(e), dev.result(S.START)) for k, e in
                                  (("fixed", None), ("handwritten_lookahead", S.START), ("conventional_search", conv["incumbent"]), ("agent_search", agent["incumbent"]))}}
    S.write_trace(HERE / "INCUMBENTS.json", inc)
    print(json.dumps(inc["development_totals"], indent=1))


if __name__ == "__main__":
    main()
