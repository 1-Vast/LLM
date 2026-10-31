"""Check 3: re-derive the NCI-60 key set, folds, profiles and activity flags from the two CellMiner workbooks
(verifier caches made by v02_parse_xlsx.py) plus l1000_nci.npz. Writes derived_nci.npz and check3_nci.json.
"""
import hashlib
import json
from collections import Counter, defaultdict

import numpy as np
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

ROOT = "D:/MAESTRO/"
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"
STUDY = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/"
VER = STUDY + "VERIFY/"


def ik14_from_smiles(smi):
    if not smi or smi in ("-", "na"):
        return None
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    k = Chem.MolToInchiKey(m)
    return k[:14] if k else None


def fold_variants(key):
    d = hashlib.sha256(key.encode("utf-8")).digest()
    h = d.hex()
    return {"int_full_mod10": int(h, 16) % 10, "first_byte_mod10": d[0] % 10, "first8hex_mod10": int(h[:8], 16) % 10,
            "last8hex_mod10": int(h[-8:], 16) % 10, "first16hex_mod10": int(h[:16], 16) % 10}


def main():
    out = {}
    Z = np.load(VER + "cache_zscore.npz")
    nsc, smiles, z, zline = [str(s) for s in Z["nsc"]], [str(s) for s in Z["smiles"]], Z["z"], [str(s) for s in Z["line"]]
    out["z_rows"] = len(nsc)
    out["z_duplicate_nsc"] = sum(1 for v in Counter(nsc).values() if v > 1)
    ik = [ik14_from_smiles(s) for s in smiles]
    out["z_rows_without_key"] = sum(k is None for k in ik)
    out["z_rows_smiles_missing"] = sum((not s) or s in ("-", "na") for s in smiles)

    # compare my NSC -> ik14 with the built map nci_ik14.tsv (diagnostic only)
    built = {}
    with open(PROC + "nci_ik14.tsv", encoding="utf-8", newline="") as f:
        hdr = f.readline().rstrip("\r\n").split("\t")
        for line in f:
            p = line.rstrip("\r\n").split("\t")
            built[p[0]] = p
    out["nci_ik14_tsv_header"] = hdr
    out["nci_ik14_tsv_rows"] = len(built)

    groups = defaultdict(list)
    for i, k in enumerate(ik):
        if k is not None:
            groups[k].append(i)
    out["n_keys_from_z"] = len(groups)
    out["n_keys_multi_nsc"] = sum(1 for v in groups.values() if len(v) > 1)

    L = np.load(PROC + "l1000_nci.npz", allow_pickle=True)
    lkey = [str(k) for k in L["key"]]
    lx = L["x"]
    meas = np.isfinite(lx[..., 0])
    out["l1000_measured_def_agree_with_n_sig"] = bool(np.array_equal(meas, L["n_sig"] > 0))
    lmeasured = {k for k, m in zip(lkey, meas) if m.any()}
    out["l1000_keys"] = len(lkey)
    out["l1000_keys_with_measured_option"] = len(lmeasured)
    out["l1000_keys_not_from_z_table"] = sorted(set(lkey) - set(groups))
    out["l1000_key_equals_ik14"] = all(str(a) == str(b) for a, b in zip(L["key"], L["ik14"]))

    prof = {}
    nfin = {}
    max_single = {}
    for k, idx in groups.items():
        with np.errstate(all="ignore"):
            prof[k] = np.nanmean(z[idx], axis=0)
        nfin[k] = int(np.isfinite(prof[k]).sum())
        max_single[k] = int(np.isfinite(z[idx]).sum(axis=1).max())
    included = sorted(k for k in groups if k in lmeasured and nfin[k] >= 50)
    alt_any_single = sorted(k for k in groups if k in lmeasured and max_single[k] >= 50)
    out["n_included"] = len(included)
    out["n_included_alt_single_nsc_ge50"] = len(alt_any_single)
    out["excluded_l1000_keys_lines_lt50"] = sorted(k for k in lmeasured if k in groups and nfin[k] < 50)

    # ---- activity from the raw workbook
    Rw = np.load(VER + "cache_raw.npz")
    rnsc, fail, rx, rline = [str(s) for s in Rw["nsc"]], [str(s) for s in Rw["fail"]], Rw["x"], [str(s) for s in Rw["line"]]
    assert rline == zline
    fc = Counter(fail)
    out["raw_rows"] = len(rnsc)
    out["raw_failure_values_top"] = fc.most_common(8)
    nofail = np.array([f.strip() in ("-", "", "<None>") for f in fail])
    out["raw_rows_without_failure"] = int(nofail.sum())
    rows_by_nsc = defaultdict(list)
    for i, s in enumerate(rnsc):
        rows_by_nsc[s].append(i)
    killed = {}
    killed_alt_all_rows = {}
    n_exp = {}
    for k in included:
        rows = [r for i in groups[k] for r in rows_by_nsc.get(nsc[i], [])]
        good = [r for r in rows if nofail[r]]
        n_exp[k] = len(good)
        with np.errstate(all="ignore"):
            m = np.nanmean(rx[good], axis=0) if good else np.full(60, np.nan)
            m_all = np.nanmean(rx[rows], axis=0) if rows else np.full(60, np.nan)
        killed[k] = int(np.sum(np.isfinite(m) & (m >= 5.60)))
        killed_alt_all_rows[k] = int(np.sum(np.isfinite(m_all) & (m_all >= 5.60)))
    out["included_without_raw_rows"] = sorted(k for k in included if n_exp[k] == 0)
    active = np.array([killed[k] >= 3 for k in included])
    out["n_active"] = int(active.sum())

    # ---- folds
    fv = {k: fold_variants(k) for k in included}

    # ---- compare with nci60.npz
    N = np.load(PROC + "nci60.npz")
    nkey = [str(s) for s in N["key"]]
    cmp = {"keys_equal": nkey == included, "lines_equal": [str(s) for s in N["line"]] == zline,
           "n_npz": len(nkey), "only_in_npz": sorted(set(nkey) - set(included)),
           "only_in_verifier": sorted(set(included) - set(nkey))}
    if cmp["keys_equal"]:
        P = np.vstack([prof[k] for k in included])
        cmp["profile_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(P), np.isfinite(N["profile"])))
        cmp["profile_max_abs_diff"] = float(np.nanmax(np.abs(P - N["profile"])))
        cmp["active_equal"] = bool(np.array_equal(active, N["active"]))
        kl = np.array([killed[k] for k in included])
        cmp["killed_lines_equal"] = bool(np.array_equal(kl, N["killed_lines"]))
        cmp["killed_lines_n_differ"] = int((kl != N["killed_lines"]).sum())
        kl_alt = np.array([killed_alt_all_rows[k] for k in included])
        cmp["killed_lines_alt_all_rows_n_differ"] = int((kl_alt != N["killed_lines"]).sum())
        cmp["active_alt_all_rows_n_differ"] = int(((kl_alt >= 3) != N["active"]).sum())
        for name in fold_variants("X"):
            f = np.array([fv[k][name] for k in included])
            cmp[f"fold_{name}_equal"] = bool(np.array_equal(f, N["fold"]))
        cmp["fold_counts"] = np.bincount(N["fold"], minlength=10).tolist()
        sig = lx[[lkey.index(k) for k in included]]
        cmp["signature_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(sig), np.isfinite(N["signature"])))
        cmp["signature_max_abs_diff"] = float(np.nanmax(np.abs(sig.astype(float) - N["signature"].astype(float))))
        # my ik14 vs the built map, for included keys
        mism = []
        for k in included:
            for i in groups[k]:
                b = built.get(nsc[i])
                if b is not None and k not in b:
                    mism.append((nsc[i], k, b))
        cmp["nci_ik14_tsv_mismatch_for_included"] = mism[:20]
        cmp["nci_ik14_tsv_mismatch_count"] = len(mism)
        fold = np.array([fv[k]["int_full_mod10"] for k in included])
        # generic per fold = mean of reference profiles (other nine folds)
        G = np.zeros((len(included), 60))
        for f in range(10):
            ref = fold != f
            with np.errstate(all="ignore"):
                g = np.nanmean(P[ref], axis=0)
            G[fold == f] = g
        R = np.load(STUDY + "RUN/predictions_nci60.npz")
        cmp["pred_file_keys_equal"] = [str(s) for s in R["key"]] == included
        cmp["pred_file_lines_equal"] = [str(s) for s in R["line"]] == zline
        cmp["pred_file_observed_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(R["observed"]), np.isfinite(P)))
        cmp["pred_file_observed_max_abs_diff"] = float(np.nanmax(np.abs(R["observed"] - P)))
        cmp["pred_file_generic_max_abs_diff"] = float(np.max(np.abs(R["generic"] - G)))
        cmp["pred_file_active_equal"] = bool(np.array_equal(R["active"], active))
        # fingerprints: Morgan r2 2048 of the first NSC's SMILES (diagnostic; the protocol does not say which SMILES)
        from rdkit.Chem import AllChem
        fp_first = np.zeros((len(included), 2048), np.uint8)
        fp_union = np.zeros((len(included), 2048), np.uint8)
        for qi, k in enumerate(included):
            bits = []
            for i in groups[k]:
                m = Chem.MolFromSmiles(smiles[i])
                bits.append(np.array(list(AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)), np.uint8))
            fp_first[qi] = bits[0]
            fp_union[qi] = np.max(bits, axis=0)
        cmp["fingerprint_first_smiles_rows_differ"] = int((fp_first != N["fingerprint"]).any(axis=1).sum())
        cmp["fingerprint_union_rows_differ"] = int((fp_union != N["fingerprint"]).any(axis=1).sum())
        np.savez(VER + "derived_nci.npz", key=np.array(included), line=np.array(zline), observed=P, generic=G,
                 active=active, killed_lines=kl, fold=fold, n_nsc=np.array([len(groups[k]) for k in included]),
                 n_raw_experiments=np.array([n_exp[k] for k in included]))
    out["compare"] = cmp
    json.dump(out, open(VER + "check3_nci.json", "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
