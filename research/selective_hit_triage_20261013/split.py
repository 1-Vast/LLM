"""Development/test split and evaluability, from metadata and identifier columns only.

File summary
- Path: research/selective_hit_triage_20261013/split.py
- Purpose: fix which compounds are development (outcomes opened for design) and which are test
  (outcomes sealed until the protocol is frozen), before any CTRP response value is read.
- Core points:
  - Mechanism families are connected components of compounds sharing a Repurposing Hub MoA string.
    Shared target genes are not used: they chain most kinase inhibitors into one component.
  - Families are taken in sha256 order and each goes to the smaller split, so no family crosses.
  - A compound is evaluable when CTRP holds at least 100 post-QC curves for it (any line). Only the
    identifier columns (experiment_id, master_cpd_id) of the curve table are read for this count.
  - Test compounds are dealt into eight campaigns in sha256 order for the sequential analyses.
- Output: SPLIT.json.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from collections import Counter

import pandas as pd

from census import CTRP_SHA256, CTRP_ZIP, HERE, SPLIT_SALT, sha256

MIN_CTRP_LINES = 100
CAMPAIGNS = 8


def h(text: str) -> str:
    return hashlib.sha256((SPLIT_SALT + ":" + text).encode()).hexdigest()


def moa_families(rows: list[dict]) -> list[str]:
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict = {}
    for i, r in enumerate(rows):
        for m in r["moas"] or ["NO_MOA:" + r["core"]]:
            if m in owner:
                a, b = find(i), find(owner[m])
                if a != b:
                    parent[a] = b
            else:
                owner[m] = i
    groups: dict = {}
    for i in range(len(rows)):
        groups.setdefault(find(i), []).append(rows[i]["core"])
    key = {root: "F" + h(",".join(sorted(cores)))[:10] for root, cores in groups.items()}
    return [key[find(i)] for i in range(len(rows))]


def main() -> None:
    if sha256(CTRP_ZIP) != CTRP_SHA256:
        raise SystemExit("CTRP_ARCHIVE_MISMATCH")
    census = json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))
    rows = census["compounds"]
    z = zipfile.ZipFile(CTRP_ZIP)
    ids = pd.read_csv(io.BytesIO(z.read("v20.data.curves_post_qc.txt")), sep="\t", encoding="latin-1",
                      usecols=["experiment_id", "master_cpd_id"])
    curves_per_cpd = Counter(int(k) for k in ids["master_cpd_id"])
    for r in rows:
        r["ctrp_post_qc_curves"] = curves_per_cpd.get(int(r["ctrp_master_cpd_id"]), 0)
    evaluable = [r for r in rows if r["ctrp_post_qc_curves"] >= MIN_CTRP_LINES]
    fam = moa_families(evaluable)
    for r, f in zip(evaluable, fam):
        r["family"] = f
    members: dict = {}
    for r in evaluable:
        members.setdefault(r["family"], []).append(r["core"])
    split = {"development": [], "test": []}
    for f in sorted(members, key=h):
        target = "test" if len(split["test"]) <= len(split["development"]) else "development"
        split[target] += sorted(members[f])
    test_order = sorted(split["test"], key=lambda c: h("campaign:" + c))
    campaigns = [test_order[k::CAMPAIGNS] for k in range(CAMPAIGNS)]
    family_of = {r["core"]: r["family"] for r in evaluable}
    out = {
        "label": "metadata and identifier columns only; no CTRP response value read",
        "rule": {"families": "connected components over shared Repurposing Hub MoA strings",
                 "assignment": "families in sha256 order, each to the smaller split",
                 "min_ctrp_post_qc_curves": MIN_CTRP_LINES, "campaigns": CAMPAIGNS, "salt": SPLIT_SALT},
        "excluded_not_evaluable": sorted(r["core"] for r in rows if r["ctrp_post_qc_curves"] < MIN_CTRP_LINES),
        "development": sorted(split["development"]), "test": sorted(split["test"]),
        "test_campaigns": campaigns, "family": family_of,
        "counts": {"evaluable": len(evaluable), "development": len(split["development"]), "test": len(split["test"]),
                   "families": len(members), "largest_family": max(len(v) for v in members.values()),
                   "largest_family_split": next(s for s in split if members[max(members, key=lambda k: len(members[k]))][0] in split[s])},
    }
    (HERE / "SPLIT.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"]), len(out["excluded_not_evaluable"]), "not evaluable")


if __name__ == "__main__":
    main()
