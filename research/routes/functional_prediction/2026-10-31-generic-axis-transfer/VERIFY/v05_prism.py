"""Check 4: re-derive the PRISM 24Q2 query set, line set, query profiles and activity flags.

Sealing discipline: only the ID column of every matrix row is read; values are parsed only for the rows
chosen for the queries (as the protocol does for the run).
Writes VERIFY/derived_prism.npz and VERIFY/check4_prism.json.
"""
import csv
import json
import re
from collections import Counter, defaultdict

import numpy as np
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

ROOT = "D:/MAESTRO/"
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"
STUDY = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/"
VER = STUDY + "VERIFY/"
MATRIX = ROOT + "data/external/prism_24q2_20261031/matrix/Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv"
CLIST = ROOT + "data/external/prism_24q2_20261031/meta/Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv"
SEALED = ROOT + "log/research_records/knowledge_reality_20261013/sealed_compounds.csv"


def ik14_from_smiles(smi):
    m = Chem.MolFromSmiles(smi) if smi else None
    if m is None:
        return None
    k = Chem.MolToInchiKey(m)
    return k[:14] if k else None


def core_of(identifier):
    s = identifier.strip()
    if s.startswith("BRD:"):
        s = s[4:]
    m = re.match(r"^(BRD-[A-Z]\d{8})", s)
    return m.group(1) if m else None


def main():
    out = {}
    # ---- sealed list
    sealed = list(csv.DictReader(open(SEALED, encoding="utf-8", newline="")))
    out["n_sealed"] = len(sealed)
    cores = [r["core"].strip() for r in sealed]
    out["n_sealed_unique_cores"] = len(set(cores))
    my_ik = {r["core"].strip(): ik14_from_smiles(r["smiles"].strip()) for r in sealed}
    conn = {r["core"].strip(): r["conn"].strip() for r in sealed}
    out["n_rdkit_fail"] = sum(v is None for v in my_ik.values())
    out["rdkit_vs_conn_mismatch"] = sorted(c for c in cores if my_ik[c] is not None and my_ik[c] != conn[c])

    # ---- L1000 measured options
    L = np.load(PROC + "l1000_24q2.npz", allow_pickle=True)
    lkey = [str(k) for k in L["key"]]
    lik = {str(k): str(i) for k, i in zip(L["key"], L["ik14"])}
    x = L["x"]
    measured = np.isfinite(x[..., 0])  # an option is measured when its signature is finite
    n_meas = measured.sum(axis=1)
    nsig_meas = (L["n_sig"] > 0).sum(axis=1)
    out["l1000_measured_def_agree_with_n_sig"] = bool(np.array_equal(measured, L["n_sig"] > 0))
    out["l1000_keys_not_in_sealed"] = sorted(set(lkey) - set(cores))
    out["sealed_not_in_l1000_keys"] = sorted(set(cores) - set(lkey))
    has_l1000 = {k for k, n in zip(lkey, n_meas) if n > 0}
    out["n_with_measured_option"] = len(has_l1000)
    # keys_24q2.tsv
    ktsv = {}
    with open(PROC + "keys_24q2.tsv", encoding="utf-8", newline="") as f:
        next(f)
        for line in f:
            k, i = line.rstrip("\r\n").split("\t")
            ktsv[k] = i
    out["keys_tsv_vs_l1000_ik14_mismatch"] = sorted(k for k in ktsv if lik.get(k) != ktsv[k])
    out["l1000_ik14_vs_rdkit_mismatch"] = sorted(k for k in lkey if my_ik.get(k) != lik[k])
    out["l1000_ik14_vs_conn_mismatch"] = sorted(k for k in lkey if conn.get(k) != lik[k])

    # ---- development pool
    dev = np.load(PROC + "dev_pool.npz")
    dev_ik = set(str(i) for i in dev["ik14"])
    dev_lines = [str(s) for s in dev["line"]]

    queries0 = [c for c in cores if c in has_l1000]  # sealed order
    dropped = [c for c in queries0 if (my_ik.get(c) in dev_ik) or (lik.get(c) in dev_ik) or (conn.get(c) in dev_ik)]
    out["dropped_in_pool_any_ik_source"] = dropped
    queries = sorted(c for c in queries0 if c not in dropped)
    out["n_queries"] = len(queries)

    # ---- compound list: REP.1M ids per core
    clist = list(csv.DictReader(open(CLIST, encoding="utf-8", newline="")))
    out["compound_list_rows"] = len(clist)
    out["compound_list_screens"] = dict(Counter(r["screen"] for r in clist))
    rep1m_ids = defaultdict(set)
    primary_cores = set()
    multi_id_rows = 0
    for r in clist:
        ids = [s for s in re.split(r"[;,|\s]+", r["IDs"]) if s]
        if len(ids) != 1:
            multi_id_rows += 1
        for i in ids:
            c = core_of(i)
            if r["screen"] == "REP.1M":
                rep1m_ids[c].add(i.strip())
            if r["screen"] == "REP.PRIMARY":
                primary_cores.add(c)
    out["compound_list_rows_with_multiple_ids"] = multi_id_rows
    out["sealed_with_REP.PRIMARY_row"] = sorted(set(cores) & primary_cores)
    out["sealed_with_REP.PRIMARY_row_and_l1000"] = sorted(set(cores) & primary_cores & has_l1000)
    out["sealed_without_REP.1M_id"] = sorted(c for c in cores if c not in rep1m_ids)

    # ---- matrix: read IDs of every row; parse values only for chosen rows
    want = {i: c for c in queries for i in rep1m_ids.get(c, ())}
    vals = defaultdict(list)
    n_rows = 0
    id_counts = Counter()
    with open(MATRIX, encoding="utf-8", newline="") as f:
        header = f.readline().rstrip("\r\n").split(",")
        mlines = header[1:]
        for line in f:
            n_rows += 1
            rid, rest = line.split(",", 1)
            rid = rid.strip().strip('"')
            id_counts[rid] += 1
            if rid in want:
                fields = rest.rstrip("\r\n").split(",")
                assert len(fields) == len(mlines)
                vals[want[rid]].append((rid, np.array([float(v) if v.strip() not in ("", "NA", "NaN", "nan") else np.nan
                                                       for v in fields])))
    out["matrix_rows"] = n_rows
    out["matrix_columns"] = len(mlines)
    out["matrix_duplicate_row_ids"] = sum(1 for v in id_counts.values() if v > 1)
    out["parsed_rows"] = sum(len(v) for v in vals.values())
    out["queries_without_matrix_row"] = sorted(c for c in queries if c not in vals)
    out["queries_with_several_rows"] = {c: [r for r, _ in v] for c, v in vals.items() if len(v) > 1}
    # wanted ids absent from the matrix
    out["rep1m_ids_of_queries_absent_from_matrix"] = sorted(i for i in want if id_counts[i] == 0)

    # ---- lines: present in both the 19Q4 pool and the 24Q2 matrix (exact id match)
    mset = set(mlines)
    lines = [s for s in dev_lines if s in mset]
    out["n_lines_exact"] = len(lines)
    stripped = [s for s in dev_lines if s.split("_")[0] in mset]
    out["n_lines_if_suffix_stripped"] = len(stripped)
    col = {s: j for j, s in enumerate(mlines)}
    idx = np.array([col[s] for s in lines])

    prof = np.full((len(queries), len(lines)), np.nan)
    prof_plainmean = np.full((len(queries), len(lines)), np.nan)
    for qi, c in enumerate(queries):
        if c not in vals:
            continue
        M = np.vstack([v for _, v in vals[c]])[:, idx]
        with np.errstate(all="ignore"):
            prof[qi] = np.nanmean(M, axis=0)
        prof_plainmean[qi] = M.mean(axis=0)
    n_lines = len(lines)
    killed = (np.nan_to_num(prof, nan=0.0) <= -1) & np.isfinite(prof)
    nk = killed.sum(axis=1)
    active_all = nk >= 0.05 * n_lines           # denominator = all evaluated lines (missing = not killed)
    n_fin = np.isfinite(prof).sum(axis=1)
    active_fin = nk >= 0.05 * n_fin             # alternative: denominator = lines with a value

    # generic: mean profile of the development pool over the evaluated lines
    dcol = {s: j for j, s in enumerate(dev_lines)}
    dprof = dev["profile"][:, [dcol[s] for s in lines]]
    with np.errstate(all="ignore"):
        generic = np.nanmean(dprof, axis=0)
    out["dev_pool_lines_all_nan"] = int((~np.isfinite(generic)).sum())

    np.savez(VER + "derived_prism.npz", key=np.array(queries), line=np.array(lines), observed=prof,
             observed_plainmean=prof_plainmean, generic=generic, active=active_all, active_finite_denominator=active_fin,
             killed_lines=nk, ik14=np.array([lik[c] for c in queries]))

    # ---- compare with prism24q2.npz and predictions file
    P = np.load(PROC + "prism24q2.npz")
    R = np.load(STUDY + "RUN/predictions_prism24q2.npz")
    cmp = {}
    cmp["keys_equal_prism24q2"] = [str(k) for k in P["key"]] == queries
    cmp["keys_equal_predictions"] = [str(k) for k in R["key"]] == queries
    cmp["lines_equal_prism24q2"] = [str(s) for s in P["line"]] == lines
    cmp["lines_equal_predictions"] = [str(s) for s in R["line"]] == lines
    if cmp["keys_equal_prism24q2"] and cmp["lines_equal_prism24q2"]:
        a, b = prof, P["profile"]
        cmp["profile_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(a), np.isfinite(b)))
        cmp["profile_max_abs_diff"] = float(np.nanmax(np.abs(a - b)))
        cmp["active_equal_prism24q2"] = bool(np.array_equal(active_all, P["active"]))
        cmp["active_alt_equal_prism24q2"] = bool(np.array_equal(active_fin, P["active"]))
        cmp["n_active"] = int(active_all.sum())
        cmp["n_active_alt"] = int(active_fin.sum())
        cmp["signature_vs_l1000_max_abs_diff"] = float(np.nanmax(np.abs(
            P["signature"].astype(float) - x[[lkey.index(c) for c in queries]].astype(float))))
        cmp["signature_nan_pattern_equal"] = bool(np.array_equal(
            np.isfinite(P["signature"]), np.isfinite(x[[lkey.index(c) for c in queries]])))
        cmp["parsed_treatments_npz"] = int(P["parsed_treatments"])
        cmp["dropped_in_pool_npz"] = [str(s) for s in P["dropped_in_pool"]]
        cmp["observed_pred_file_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(R["observed"]), np.isfinite(prof)))
        cmp["observed_pred_file_max_abs_diff"] = float(np.nanmax(np.abs(R["observed"] - prof)))
        cmp["generic_pred_file_rows_identical"] = bool(np.all(R["generic"] == R["generic"][0]))
        cmp["generic_pred_file_max_abs_diff"] = float(np.max(np.abs(R["generic"] - generic[None])))
        cmp["active_pred_file_equal"] = bool(np.array_equal(R["active"], active_all))
        cmp["plainmean_vs_nanmean_max_abs_diff"] = float(np.nanmax(np.abs(prof_plainmean - prof)))
        cmp["plainmean_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(prof_plainmean), np.isfinite(prof)))
        # fingerprint check (B2 input): Morgan r2 2048 from the sealed SMILES
        from rdkit.Chem import AllChem
        smi = {r["core"].strip(): r["smiles"].strip() for r in sealed}
        fp = np.zeros((len(queries), 2048), dtype=np.uint8)
        for qi, c in enumerate(queries):
            m = Chem.MolFromSmiles(smi[c])
            bv = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
            fp[qi] = np.array(list(bv), dtype=np.uint8)
        cmp["fingerprint_equal_prism24q2"] = bool(np.array_equal(fp, P["fingerprint"]))
        cmp["fingerprint_n_rows_differ"] = int((fp != P["fingerprint"]).any(axis=1).sum())
    out["compare"] = cmp
    json.dump(out, open(VER + "check4_prism.json", "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
