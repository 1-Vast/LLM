"""Cost units of the program-revision study, separated, from the frozen records (no new fit).

File summary
- Path: research/seed_attribution_20261017/cost_units.py
- Purpose: Part 2 of the brief. `program_revision_20261017` reports one number, "wells", for things that
  are different. This script reads the frozen LIBRARIES.json and RESULTS.json and writes COST_UNITS.json
  with six separate accounts per arm, plus the definitions, so that a claim can say which account it
  spends.
- Accounts:
  1. shared_historical: outcomes of the source screen that every arm receives for free.
  2. incremental_research: development knowledge acquisition charged to one arm (frozen convention:
     2 wells per newly revealed pair, 1 well per development query line for a measurement edit, 2 wells
     per outcome read by the conventional search).
  3. deployment: what a campaign on a new line spends (probe 1 well, confirmation 2 wells, panel 1 assay
     unit, 28 wells per line in Stage C).
  4. bundles_rounds: batches and rounds (turnaround), not wells.
  5. compute_api_curation: seconds, LLM USD upper bound, and authoring effort (not measured).
  6. logical_queries: calls through the outcome-access interface (a pair is one query; it is not a well).
- What it does NOT recover: the physical (drug x PRISM pool) well count of the development experiments.
  A PRISM well measures every line of one pool at once (a pool holds 6-21 source lines), so per-pair wells
  are a logical charge. The retained trajectories keep the number of revealed pairs, not the pairs, so only
  bounds are given.
- Output: COST_UNITS.json (write-once). Run: python cost_units.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "program_revision_20261017"
OUT = HERE / "COST_UNITS.json"


def main():
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; write-once")
    lib = json.loads((FROZEN / "LIBRARIES.json").read_text(encoding="utf-8"))
    res = json.loads((FROZEN / "RESULTS.json").read_text(encoding="utf-8"))
    lines = pd.read_csv(FROZEN / "lines.csv", keep_default_na=False)
    drugs = pd.read_csv(FROZEN / "drugs.csv")
    src = lines[lines.line_split == "source"]
    q = src[src.role == "query"]
    pool_sizes = src.groupby("pool_id").size()
    q_pool_sizes = q.groupby("pool_id").size()
    n_src_drugs = int((drugs.drug_split == "source").sum())

    def deploy(arm):
        c = res["C_policies"].get(arm)
        return None if c is None else {"wells_per_line": c["wells"], "rounds_per_line": c["rounds"],
                                       "hits_per_line": round(c["hits_per_line"], 3), "unknown_per_line": round(c["unknown"], 3)}

    arms = {}
    for name, dev_name, policy in (("seed_fixed", "seed_fixed", "seed_fixed|exploit_first_feedback"),
                                   ("stepwise", "stepwise", "stepwise|exploit_first_feedback"),
                                   ("maestro_enum", "maestro_enum", "maestro_enum|exploit_first_feedback"),
                                   ("maestro_llm", "maestro_llm", "maestro_llm|exploit_first_feedback"),
                                   ("maestro_llm_joint", "maestro_llm_joint", "maestro_llm_joint|fixed_probes_feedback")):
        rec = lib[dev_name]
        acc = rec["accounting"]
        pairs = acc.get("revealed_pairs", acc.get("query_outcomes_read", 0))
        arms[name] = {
            "shared_historical": "inherited (source screen)",
            "incremental_research": {
                "wells_charged": acc.get("distinguishing_wells", acc.get("wells_charged", 0)),
                "convention": "2 wells per newly revealed pair" if name != "stepwise" else "2 wells per query outcome read",
                "candidates_evaluated": acc.get("evaluated", 0)},
            "logical_queries": {"pairs": int(pairs), "kind": "revealed (drug, line) pairs" if name != "stepwise" else "query outcomes read"},
            "physical_pool_wells_bounds": None if not pairs else {
                "upper_bound": int(pairs),
                "lower_bound": int(np.ceil(pairs / int(q_pool_sizes.max()))),
                "note": "a (drug, pool) well covers every line of the pool; the retained trajectories do not keep the pairs"},
            "deployment_stage_c": deploy(policy),
            "compute_api_curation": {"seconds": rec.get("seconds"), "llm": rec.get("llm_spend"),
                                     "curation": "10 textbook programs written before any result (authoring effort not measured)"
                                     if name == "seed_fixed" else "none beyond the proposer"}}
    out = {
        "definitions": {
            "shared_historical": "outcomes of the source screen: identical for every arm, not charged to any",
            "incremental_research": "development outcomes bought after committing predictions; charged to the arm that buys them",
            "deployment": "wells and assay units a campaign on a new line spends",
            "bundles_rounds": "batches in one round; turnaround, not wells",
            "compute_api_curation": "seconds, LLM USD upper bound at 0.30/1.20 per million tokens, authoring effort",
            "logical_queries": "calls through the access interface; one pair = one query = one query-unit, never one plate well"},
        "screen": {"source_drugs": n_src_drugs, "source_lines": int(len(src)), "dev_query_lines": int(len(q)),
                   "source_pools": int(len(pool_sizes)), "lines_per_source_pool": [int(pool_sizes.min()), float(pool_sizes.mean()), int(pool_sizes.max())],
                   "dev_query_pools": int(len(q_pool_sizes)), "dev_query_lines_per_pool": [int(q_pool_sizes.min()), float(q_pool_sizes.mean()), int(q_pool_sizes.max())]},
        "information_conditions": {
            "I0": {"wells_per_line": 0, "assay_units": 0, "inputs": "lineage"},
            "I1": {"wells_per_line": 0, "assay_units": 1, "inputs": "lineage + DNA hotspot panel"},
            "I2": {"wells_per_line": 8, "assay_units": 1, "inputs": "I1 + 8 fixed probes"},
            "I3": {"wells_per_line": 8, "assay_units": 2, "inputs": "I2 + RNA-seq"}},
        "arms": arms,
        "frozen_payback": res["C_knowledge_payback"],
        "what_the_frozen_numbers_mean": [
            "'wells' for the development arms are logical per-pair charges, not plate wells",
            "the conventional search's 167,722 wells are the cost of reading every known query outcome once for each candidate batch; "
            "it is a data-access convention, not a recommended experimental design",
            "deployment wells (28 per line) are identical across arms; arms differ only in how they spend them",
            "the 10-program seed library has zero incremental wells and no compute; its cost is authoring effort, not measured",
            "development outcomes read for the distinguishing experiment were also inside the training of the frozen bench's folds "
            "(AUDIT_ACCESS.json): the wells charged measure the pairs revealed after commitment, not the query information the loop used"]}
    OUT.write_text(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n",
                   encoding="utf-8", newline="\n")
    print("written", OUT.name)


if __name__ == "__main__":
    main()
