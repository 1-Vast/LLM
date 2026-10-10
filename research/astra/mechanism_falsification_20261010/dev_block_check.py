"""Direct test of the collection confound: rank the true class with and without same-collection members.

For each development query of a referenced class and each of its options, class prototypes are the
mean of reference members measured at that option, either over all members (open) or only over
members whose signature at that option came from a different plate collection than the query's
(blocked; sig_id prefix before the first underscore). Scorer: mean over options of cosine in gene
space between the query and the prototype; only options where the true class has a blocked member
count, and both arms use exactly those options. Writes development/block_check.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import dev_ceiling as DC
import dev_programs as DP
import study as S

HERE = Path(__file__).resolve().parent


def option_collections(split: dict, drugs: np.ndarray, options: list[str]) -> np.ndarray:
    import pandas as pd
    sig = pd.read_csv(S.ROOT / "data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t",
                      usecols=["sig_id", "cell_id", "pert_itime"], low_memory=False).set_index("sig_id")
    pos = {o: j for j, o in enumerate(options)}
    out = np.empty((len(drugs), len(options)), dtype=object)
    for i, d in enumerate(drugs):
        for s in split["drugs"][str(d)]["sig_ids"]:
            j = pos[f"{sig.at[s, 'cell_id']}|{sig.at[s, 'pert_itime']}"]
            cur = out[i, j] or set()
            cur.add(s.split("_")[0])
            out[i, j] = cur
    return out


def main() -> dict:
    data = S.load_tier("open")
    X, moa, role, options = data["x"], data["moa"], data["role"], data["options"]
    ref = role == "reference"
    act = DP.drug_activity(X, ref)
    coll = option_collections(data["split"], data["drug"], options)
    classes = sorted(set(moa[ref]))
    members = {c: np.where(ref & (moa == c))[0] for c in classes}
    Xu = DC.unit(np.nan_to_num(X))
    pos = {c: i for i, c in enumerate(classes)}
    q = [i for i in np.where(role == "development")[0] if moa[i] in pos]
    rows = []
    for qi in q:
        sc_open, sc_block, used = np.zeros(len(classes)), np.zeros(len(classes)), 0
        cnt_open, cnt_block = np.zeros(len(classes)), np.zeros(len(classes))
        for o in S.available(data, qi):
            qc = coll[qi, o] or set()
            tm = [j for j in members[moa[qi]] if not np.isnan(X[j, o, 0]) and not ((coll[j, o] or set()) & qc)]
            if not tm:
                continue  # the true class has no other-collection member here: option not used
            used += 1
            for c in classes:
                mo = [j for j in members[c] if not np.isnan(X[j, o, 0])]
                mb = [j for j in mo if not ((coll[j, o] or set()) & qc)]
                if mo:
                    sc_open[pos[c]] += float(DC.unit(np.mean(X[mo, o], axis=0)) @ Xu[qi, o]); cnt_open[pos[c]] += 1
                if mb:
                    sc_block[pos[c]] += float(DC.unit(np.mean(X[mb, o], axis=0)) @ Xu[qi, o]); cnt_block[pos[c]] += 1
        if used == 0:
            continue
        so = np.where(cnt_open > 0, sc_open / np.maximum(cnt_open, 1), np.nan)
        sb = np.where(cnt_block > 0, sc_block / np.maximum(cnt_block, 1), np.nan)
        ti = pos[moa[qi]]
        rows.append({"drug": str(data["drug"][qi]), "act": float(act[qi]), "options_used": used,
                     "rank_open": DC.rank_of(so, ti, True), "rank_blocked": DC.rank_of(sb, ti, True),
                     "n_ranked_blocked": int(np.isfinite(sb).sum())})
    res = {"n": len(rows), "n_classes": len(classes)}
    for lab, f in (("all", lambda r: True), ("act<0.5", lambda r: r["act"] < 0.5), ("act0.5-0.75", lambda r: 0.5 <= r["act"] < 0.75),
                   ("act>=0.75", lambda r: r["act"] >= 0.75)):
        rs = [r for r in rows if f(r)]
        if rs:
            ro, rb = np.array([r["rank_open"] for r in rs]), np.array([r["rank_blocked"] for r in rs])
            res[lab] = {"n": len(rs), "median_open": float(np.median(ro)), "median_blocked": float(np.median(rb)),
                        "top5_open": float(np.mean(ro <= 5)), "top5_blocked": float(np.mean(rb <= 5)),
                        "chance_median": float(np.median([r["n_ranked_blocked"] for r in rs]) / 2)}
    res["rows"] = rows
    (HERE / "development" / "block_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
