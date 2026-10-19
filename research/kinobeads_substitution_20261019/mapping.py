"""Map Jaaks 2022 drugs (action-substitution CENSUS.json) to Klaeger 2017 compounds (ChEMBL CHEMBL3991601). Design only.

Reads names and synonyms; no Jaaks response column and no Kd value is read. Writes MAPPING.json (overwrites).
Usage: python mapping.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AS = ROOT / "research/action_substitution_20261019"
KL = ROOT / "data/external/klaeger2017_chembl"

# Jaaks name -> ChEMBL molecule name, added only for drug-identity reasons (code name vs INN); see MAPPING.json
ALIASES = {}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def main():
    census = json.loads((AS / "CENSUS.json").read_text(encoding="utf-8"))
    lofo = json.loads((AS / "LOFO_SYNERGY_DELTA_AUC.json").read_text(encoding="utf-8"))
    evaluable = sorted(lofo["per_impl"])
    mols = json.loads((KL / "molecules.json").read_text(encoding="utf-8"))["molecules"]
    index = {}
    for mid, m in mols.items():
        for n in [m["pref_name"]] + m["synonyms"]:
            if n:
                index.setdefault(norm(n), set()).add(mid)
    out, ambiguous = {}, {}
    for did, d in census["drugs"].items():
        if "|" in d["name"]:
            continue
        name = ALIASES.get(d["name"], d["name"])
        hits = index.get(norm(name), set())
        if len(hits) == 1:
            mid = next(iter(hits))
            out[did] = dict(name=d["name"], chembl=mid, klaeger_name=mols[mid]["pref_name"], via="alias" if d["name"] in ALIASES else "name/synonym")
        elif len(hits) > 1:
            ambiguous[did] = dict(name=d["name"], candidates=sorted(hits))
    names = {did: d["name"] for did, d in census["drugs"].items() if "|" not in d["name"]}
    res = dict(source="CENSUS.json drug names vs ChEMBL pref_name + molecule_synonyms of CHEMBL3991601 molecules",
               aliases=ALIASES, n_jaaks_drugs=len(names), n_mapped=len(out),
               mapped=dict(sorted(out.items(), key=lambda kv: kv[1]["name"])), ambiguous=ambiguous,
               unmapped=sorted(n for did, n in names.items() if did not in out),
               evaluable_implementations=evaluable,
               evaluable_mapped=sorted(n for n in evaluable if n in {v["name"] for v in out.values()}),
               evaluable_unmapped=sorted(n for n in evaluable if n not in {v["name"] for v in out.values()}))
    res["n_evaluable_mapped"] = len(res["evaluable_mapped"])
    res["coverage_gate"] = "PASS" if len(out) >= 15 else "BLOCKED"
    (HERE / "MAPPING.json").write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("n_jaaks_drugs", "n_mapped", "ambiguous", "unmapped", "n_evaluable_mapped",
                                          "evaluable_unmapped", "coverage_gate")}, indent=1))
    for v in res["mapped"].values():
        print(f"  {v['name']:16s} -> {v['klaeger_name']} ({v['chembl']}, {v['via']})")


if __name__ == "__main__":
    main()
