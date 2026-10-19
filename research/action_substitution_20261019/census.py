"""Design-only eligibility census of conditional substitution units in Jaaks 2022 (reads no response column).

A substitution unit is (A, A', B, c, role): A and A' are plausible alternative implementations (shared annotated target
or shared pathway), B is a common partner in the other role, c a cell line, and both A+B and A'+B were measured.
Library-side swaps share the anchor drug and its concentration (dose-matched partner); anchor-side swaps use each
anchor at its own concentrations (not dose-matched). Writes CENSUS.json (overwrites; design only).
"""
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import cas_data as D

HERE = Path(__file__).resolve().parent


def drug_table(df):
    rows = {}
    for role in ("ANCHOR", "LIBRARY"):
        sub = df[[f"{role}_ID", f"{role}_NAME", f"{role}_TARGET", f"{role}_PATHWAY", f"{role}_DRUG_TYPE"]].drop_duplicates()
        for _, r in sub.iterrows():
            d = rows.setdefault(r[f"{role}_ID"], dict(name=r[f"{role}_NAME"], target=r[f"{role}_TARGET"],
                                                      pathway=r[f"{role}_PATHWAY"], type=r[f"{role}_DRUG_TYPE"], roles=set()))
            d["roles"].add(role.lower())
    return rows


def main():
    assert D.md5(D.ORIGINAL) == D.MD5_ORIGINAL, "original fitted file checksum mismatch"
    df = D.design("original")
    val = D.design("validation")
    drugs = drug_table(df)
    out = dict(source=dict(file=D.ORIGINAL.name, md5=D.MD5_ORIGINAL, sha256=D.sha256(D.ORIGINAL)),
               rows=int(len(df)), lines=int(df.CELL_LINE_NAME.nunique()), tissues=df.Tissue.value_counts().to_dict(),
               plates=int(df.BARCODE.nunique()), combinations=int(df.COMBI_ID.nunique()),
               anchors=int(df.ANCHOR_ID.nunique()), library=int(df.LIBRARY_ID.nunique()), drugs=len(drugs),
               drugs_in_both_roles=sum(1 for d in drugs.values() if len(d["roles"]) == 2))
    # replicate structure: same (line, anchor, anchor conc, library) on several plates
    key = ["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"]
    reps = df.groupby(key).BARCODE.nunique()
    out["measurements_per_key"] = {str(k): int(v) for k, v in reps.value_counts().sort_index().items()}
    out["lines_with_replicates"] = int(df.loc[df.set_index(key).index.isin(reps[reps > 1].index), "CELL_LINE_NAME"].nunique())
    # target families
    ts = {i: D.target_set(d["target"]) for i, d in drugs.items()}
    fam_exact = defaultdict(list)
    for i, t in ts.items():
        if t:
            fam_exact[t].append(i)
    out["exact_target_families_size_ge2"] = {", ".join(sorted(t)): [drugs[i]["name"] for i in ids]
                                             for t, ids in fam_exact.items() if len(ids) >= 2}
    pairs_overlap = [(a, b) for a, b in itertools.combinations(sorted(drugs), 2) if ts[a] & ts[b]]
    pairs_pathway = [(a, b) for a, b in itertools.combinations(sorted(drugs), 2)
                     if drugs[a]["pathway"] == drugs[b]["pathway"] and not (ts[a] & ts[b])]
    out["candidate_pairs"] = dict(target_overlap=len(pairs_overlap), same_pathway_no_target_overlap=len(pairs_pathway))
    # observed substitution units (library side: same anchor+conc+line; anchor side: same library+line)
    lib_obs = df.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC"]).LIBRARY_ID.agg(set)
    anc_obs = df.groupby(["CELL_LINE_NAME", "LIBRARY_ID"]).ANCHOR_ID.agg(set)
    units = Counter()
    per_pair = defaultdict(lambda: Counter())
    for kind, pairs in (("target_overlap", pairs_overlap), ("same_pathway", pairs_pathway)):
        for a, b in pairs:
            nl = sum(1 for s in lib_obs if a in s and b in s)
            na = sum(1 for s in anc_obs if a in s and b in s)
            units[(kind, "library_side")] += nl
            units[(kind, "anchor_side")] += na
            if nl + na:
                per_pair[kind][f"{drugs[a]['name']} | {drugs[b]['name']}"] = nl + na
    out["substitution_units"] = {f"{k[0]}/{k[1]}": int(v) for k, v in units.items()}
    out["target_overlap_pairs_with_units"] = dict(sorted(per_pair["target_overlap"].items(), key=lambda kv: -kv[1]))
    out["same_pathway_pairs_with_units_n"] = len(per_pair["same_pathway"])
    # validation screen coverage of the same units
    out["validation"] = dict(rows=int(len(val)), lines=int(val.CELL_LINE_NAME.nunique()), combinations=int(val.COMBI_ID.nunique()),
                             lines_shared_with_original=int(len(set(val.CELL_LINE_NAME) & set(df.CELL_LINE_NAME))))
    out["drugs"] = {i: dict(name=d["name"], target=d["target"], pathway=d["pathway"], type=d["type"], roles=sorted(d["roles"]))
                    for i, d in sorted(drugs.items(), key=lambda kv: kv[1]["name"])}
    (HERE / "CENSUS.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("drugs", "target_overlap_pairs_with_units", "exact_target_families_size_ge2")}, indent=1, default=str))
    print("exact-target families:", json.dumps(out["exact_target_families_size_ge2"], indent=0)[:3000])
    print("top target-overlap pairs:", list(out["target_overlap_pairs_with_units"].items())[:40])


if __name__ == "__main__":
    main()
