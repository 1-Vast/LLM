"""Assemble VERIFICATION.json from the verifier's check outputs (check1..check5 and the extra checks)."""
import json

VER = "D:/MAESTRO/research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"


def load(name):
    return json.load(open(VER + name, encoding="utf-8"))


def main():
    c1, c2, c3, c4, c5 = (load(f) for f in ("check1_stats.json", "check2_arms.json", "check3_nci.json",
                                             "check4_prism.json", "check5_freeze.json"))
    xm, xl, xa, xd, xq = (load(f) for f in ("check_extra_maintained.json", "check_extra_l1000_meta.json",
                                             "check_extra_alternatives.json", "check_extra_devpool.json",
                                             "check_extra_query_matching.json"))
    checks = []

    def add(group, name, expected, recomputed, diff, tol, ok, scope="required"):
        checks.append({"group": group, "scope": scope, "name": name, "expected": expected, "recomputed": recomputed,
                       "max_abs_diff": diff, "tolerance": tol, "pass": bool(ok)})

    # ---- check 1 (statistics)
    for c in c1["checks"]:
        add("1 statistics", c["name"], c["expected"], c["recomputed"], c["max_abs_diff"], c["tolerance"], c["pass"])

    # ---- check 2 (arms)
    for s, arms in (("nci60", ("B0", "C1")), ):
        for a in arms:
            r = c2[s][a]
            add("2 arms", f"{s}: re-implemented {a} predictions vs saved pred_{a} (419 x 60; NaN pattern equal: "
                f"{r['nan_pattern_equal']})", "saved pred_" + a, "verifier implementation", r["max_abs_diff"], 1e-6,
                r["nan_pattern_equal"] and r["max_abs_diff"] <= 1e-6)
    extra_arms = [("nci60", "B1", c2["nci60"]["B1"]), ("nci60", "B2", c2["nci60"]["B2"]),
                  ("nci60", "L", c2["nci60"]["L_variants"]["global_rng_permutation_per_fold"]),
                  ("prism24q2", "B0", c2["prism24q2"]["B0"]), ("prism24q2", "B1", c2["prism24q2"]["B1"]),
                  ("prism24q2", "B2", c2["prism24q2"]["B2"]), ("prism24q2", "C1", c2["prism24q2"]["C1"]),
                  ("prism24q2", "L", c2["prism24q2"]["L_variants"]["default_rng"])]
    for s, a, r in extra_arms:
        add("2 arms", f"{s}: re-implemented {a} predictions vs saved pred_{a} (NaN pattern equal: {r['nan_pattern_equal']})",
            "saved pred_" + a, "verifier implementation", r["max_abs_diff"], 1e-6,
            r["nan_pattern_equal"] and r["max_abs_diff"] <= 1e-6, scope="extra")

    # ---- check 3 (NCI-60 inclusion, folds, activity)
    cc = c3["compare"]
    add("3 nci60 inputs", "NCI-60 key set (>=50 of 60 z lines and >=1 measured L1000 option)", cc["n_npz"], c3["n_included"],
        0 if cc["keys_equal"] else None, 0, cc["keys_equal"])
    add("3 nci60 inputs", "NCI-60 fold = int(SHA-256(key)) mod 10", "nci60.npz fold", "recomputed",
        0 if cc["fold_int_full_mod10_equal"] else None, 0, cc["fold_int_full_mod10_equal"])
    add("3 nci60 inputs", "NCI-60 killed lines per key (mean -log10 GI50 over experiments without failure >= 5.60)",
        "nci60.npz killed_lines", "recomputed", cc["killed_lines_n_differ"], 0, cc["killed_lines_equal"])
    add("3 nci60 inputs", "NCI-60 activity flags (>=3 killed lines)", 293, c3["n_active"], 0 if cc["active_equal"] else None,
        0, cc["active_equal"])
    add("3 nci60 inputs", "NCI-60 key profiles (z averaged over NSCs sharing a key)", "nci60.npz profile", "recomputed",
        cc["profile_max_abs_diff"], 1e-6, cc["profile_nan_pattern_equal"] and cc["profile_max_abs_diff"] <= 1e-6)
    add("3 nci60 inputs", "NCI-60 signatures equal l1000_nci.npz for the included keys", "nci60.npz signature",
        "l1000_nci.npz x", cc["signature_max_abs_diff"], 1e-6, cc["signature_nan_pattern_equal"] and cc["signature_max_abs_diff"] <= 1e-6)
    add("3 nci60 inputs", "NCI-60 NSC->key by RDKit equals nci_ik14.tsv for all included NSCs", 0,
        cc["nci_ik14_tsv_mismatch_count"], cc["nci_ik14_tsv_mismatch_count"], 0, cc["nci_ik14_tsv_mismatch_count"] == 0, "extra")
    add("3 nci60 inputs", "NCI-60 fingerprints = Morgan r2 2048 of the first NSC's SMILES", 0,
        cc["fingerprint_first_smiles_rows_differ"], cc["fingerprint_first_smiles_rows_differ"], 0,
        cc["fingerprint_first_smiles_rows_differ"] == 0, "extra")

    # ---- check 4 (24Q2)
    m = c5["matrix"]
    p = c4["compare"]
    add("4 prism24q2 inputs", "24Q2 matrix MD5", m["expected_md5"], m["md5"], None, 0, m["md5_match"])
    add("4 prism24q2 inputs", "24Q2 query set (sealed REP.1M with >=1 measured option in l1000_24q2.npz, none in the pool)",
        101, c4["n_queries"], 0 if p["keys_equal_prism24q2"] else None, 0, p["keys_equal_prism24q2"] and c4["n_queries"] == 101)
    add("4 prism24q2 inputs", "No query ik14 equals a development-pool ik14 (also checked: RDKit and sealed conn keys)",
        [], c4["dropped_in_pool_any_ik_source"], None, 0, c4["dropped_in_pool_any_ik_source"] == [])
    add("4 prism24q2 inputs", "24Q2 parsed matrix rows (REP.1M rows with the query's Broad ID core)", 101, c4["parsed_rows"],
        None, 0, c4["parsed_rows"] == 101 and not c4["queries_without_matrix_row"])
    add("4 prism24q2 inputs", "REP.PRIMARY rows: 3 sealed compounds have one, none has L1000", 3,
        len(c4["sealed_with_REP.PRIMARY_row"]), None, 0,
        len(c4["sealed_with_REP.PRIMARY_row"]) == 3 and c4["sealed_with_REP.PRIMARY_row_and_l1000"] == [])
    add("4 prism24q2 inputs", "24Q2 line set (exact DepMap ID in both the 19Q4 pool and the 24Q2 matrix)", 568,
        c4["n_lines_exact"], None, 0, p["lines_equal_prism24q2"] and c4["n_lines_exact"] == 568)
    add("4 prism24q2 inputs", "24Q2 query profiles", "prism24q2.npz profile", "recomputed", p["profile_max_abs_diff"], 1e-6,
        p["profile_nan_pattern_equal"] and p["profile_max_abs_diff"] <= 1e-6)
    add("4 prism24q2 inputs", "24Q2 activity flags (>=5% of 568 lines with LFC <= -1; missing = not)", 32, p["n_active"],
        None, 0, p["active_equal_prism24q2"])
    add("4 prism24q2 inputs", "24Q2 query signatures equal l1000_24q2.npz", 0.0, p["signature_vs_l1000_max_abs_diff"],
        p["signature_vs_l1000_max_abs_diff"], 1e-6, p["signature_nan_pattern_equal"], "extra")
    add("4 prism24q2 inputs", "24Q2 fingerprints = Morgan r2 2048 of the sealed SMILES", 0, p["fingerprint_n_rows_differ"],
        p["fingerprint_n_rows_differ"], 0, p["fingerprint_equal_prism24q2"], "extra")
    add("4 prism24q2 inputs", "Development pool = block N 19Q4 primary profiles and block M signatures", 0.0,
        max(xd["profile_max_abs_diff"], xd["signature_max_abs_diff"]),
        max(xd["profile_max_abs_diff"], xd["signature_max_abs_diff"]), 1e-6,
        xd["profile_nan_equal"] and xd["signature_nan_equal"] and xd["n_dev"] == 1403, "extra")

    # ---- check 5 (freeze)
    for r in c5["files"]:
        if r["section"] == "sources":
            continue
        add("5 freeze", f"FREEZE {r['section']}: {r['file']}", r["expected_sha256"], r.get("sha256"), None, 0, r["pass_"])
    src = [r for r in c5["files"] if r["section"] == "sources"]
    add("5 freeze", "FREEZE sources (21 hashed + GSE92742 gctx by size)", len(src), sum(r["pass_"] for r in src), None, 0,
        all(r["pass_"] for r in src), "extra")
    add("5 freeze", "24Q2 matrix modified after frozen_at_utc", c5["frozen_at_utc"], m["mtime_utc"], None, 0,
        m["mtime_after_freeze"])
    late = [r["file"] for r in c5["files"] if r.get("modified_after_freeze")]
    add("5 freeze", "No freeze-bound file modified after frozen_at_utc", [], late, None, 0, late == [], "extra")

    # ---- extra cross-checks
    mx = max(v for s in xm.values() for k, v in s.items() if k.endswith("max_abs_diff_maintained_vs_verifier") or k.endswith("_vs_saved"))
    add("extra", "Maintained selective_r and transfer_profile agree with the verifier and the saved B0/B1", 0.0, mx, mx, 1e-6,
        mx <= 1e-6 and all(v for s in xm.values() for k, v in s.items() if k.endswith("nan_equal")), "extra")
    for s in ("nci60", "prism24q2"):
        r = xl[s]["idose_10um_text"]
        add("extra", f"{s}: n_sig per key x option re-derived from GSE92742 metadata (trt_cp, inchi_key_prefix = key, "
            f"pert_idose '10 uM', 9 lines x 6/24 h)", "l1000 npz n_sig", "sig_info counts", r["n_cells_differ"], 0,
            r["n_sig_equal"], "extra")
    po = load("check_extra_pool_overlap.json")
    add("extra", "No 24Q2 query matches a development-pool compound by connectivity block, name or Broad ID",
        [], po["query_ik14_in_dev"] + po["query_name_in_dev"] + po["query_core_in_dev"], None, 0, po["pass"], "extra")

    discrepancies = [{
        "type": "input construction (non-numeric; not a section-9 1e-6 item)",
        "what": "24Q2 query set: 102 sealed REP.1M compounds have >=1 measured L1000 option under the run's own identity "
                "rule (LINCS trt_cp inchi_key_prefix = connectivity block, pert_idose '10 uM'); the frozen l1000_24q2.npz "
                "and the run use 101.",
        "missing_compound": "BRD-K57796080 (3,5-DHPG-(S)), connectivity block HOOWCUZPEFNHDT, shared with query "
                            "BRD-A20589515 (dihydroxyphenylglycine; 7 core-line 10 uM signatures)",
        "explanation": "keys_24q2.tsv / l1000_24q2.npz keep one Broad ID per connectivity block (first in the sealed file); the "
                       "de-duplication is not written in PROTOCOL.md, but the protocol's census count (101) matches it and "
                       "the file is hash-bound and dated 04:20Z, before the freeze and before the 24Q2 download, so the "
                       "choice cannot depend on outcomes. The other shared block (A-804598, two Broad IDs) has no L1000 data.",
        "impact": "Unknown without reading one more sealed 24Q2 row (not done, to keep the remaining sealed compounds "
                  "unread). Its enantiomer is inactive (17 of 568 killed lines; 29 needed). If it were active it would "
                  "carry the same predictions as BRD-A20589515; the 24Q2 point estimate turns negative only if its "
                  "per-compound difference is below -0.467 (H1) or -0.584 (H3); observed range over the 32 actives "
                  "is -0.154 to +0.134 (H1) and -0.133 to +0.183 (H3).",
        "affects_reported_numbers": False,
    }]
    ambiguities = [
        {"rule": "Secondary hit precision: number of hits ('the 10% of evaluated lines') and which lines are evaluated",
         "reading_used": "nearest integer to 0.1 x n, ties to even (Python round), n = lines where both residuals are finite",
         "result": "reproduces every per-compound hit precision exactly (0 difference)",
         "alternatives": "floor or ceil: per-compound differences up to 0.333 (NCI-60) and 0.034-0.036 (24Q2); round half up: "
                         "0.035 on 24Q2. Under floor, secondary C1-B0 = +0.0069 (p 0.27) and C1-B1 = +0.0105 (p 0.12) on "
                         "NCI-60 vs reported +0.0088 / +0.0152; 24Q2 +0.0041 / +0.0035 vs +0.0069 / +0.0067. No decision "
                         "depends on the secondary endpoint.",
         "disclosure": "the verifier's first implementation used floor and failed 16 checks; the reading was changed after "
                       "seeing that, because the protocol does not specify rounding"},
        {"rule": "24Q2 activity: denominator of '5% of the evaluated lines'",
         "reading_used": "all 568 lines (missing = not <= -1), as the protocol's parenthesis implies; reproduces 32 actives",
         "alternatives": "lines with a value: 33 actives (adds BRD-K00003381: 28 killed of 544 measured); H1 +0.0147 (p 0.104), "
                         "H3 +0.0208 (p 0.028): still not Holm-significant, point estimates positive, verdicts unchanged"},
        {"rule": "24Q2 lines 'present in both the 19Q4 pool and the 24Q2 matrix'",
         "reading_used": "exact DepMap ID match: 568 lines (reproduced)",
         "alternatives": "matching the base ID of 4 pool lines flagged _FAILED_STR (ACH-000010, -000511, -000925, -000992): "
                         "572 lines, same 32 actives, H1 +0.0146 (p 0.111), H3 +0.0186 (p 0.044); verdicts unchanged"},
        {"rule": "NCI-60 kill threshold: 'at least 5.60 (GI50 <= 2.5 uM)'",
         "reading_used": "5.60 as written (reproduced)",
         "alternatives": "-log10(2.5e-6) = 5.60206 changes 32 killed-line cells and no activity flag; 53 line means lie "
                         "exactly at 5.60, so summation order could matter, but the counts reproduced exactly"},
        {"rule": "L1000 'at 10 uM'",
         "reading_used": "the frozen inputs use the nominal LINCS label pert_idose '10 uM' (verified: n_sig equal for all "
                         "448 + 1227 keys)",
         "alternatives": "exact pert_dose == 10 uM would leave 7 NCI-60 keys (419 -> 412) and 2 24Q2 queries (101 -> 99) "
                         "without a measured option and change signatures of others; not testable without the 23 GB gctx"},
        {"rule": "24Q2 compound identity for L1000 matching (not stated for confirmation 2)",
         "reading_used": "connectivity block as for NCI-60 (the frozen input does this; 26 of the 101 queries match only "
                         "this way)",
         "alternatives": "Broad ID = pert_id: 77 queries; union of both: 104 (adds BMS-536924, whose LINCS inchi_key_prefix "
                         "differs from RDKit's for the same SMILES, and TC-H-106, which has no LINCS InChIKey); see also "
                         "the de-duplication discrepancy"},
        {"rule": "B2 fingerprint for NCI-60 keys with several NSC numbers (not stated)",
         "reading_used": "the stored fingerprints equal Morgan r2/2048 of the first NSC's SMILES in the z-score table",
         "alternatives": "union of the NSCs' fingerprints differs for 6 keys (B2 is context only)"},
        {"rule": "Leakage-control permutation scheme ('seed 20261031')",
         "reading_used": "one numpy default_rng(20261031); NCI-60: a permutation of the reference indices per fold in fold "
                         "order 0-9; 24Q2: one permutation of the 1,403 references (reproduced to 5e-15)",
         "alternatives": "a fresh generator per fold, seed+fold, or RandomState do not reproduce pred_L (not a protocol issue)"},
        {"rule": "Bootstrap resampling scheme",
         "reading_used": "verifier's own default_rng integer resampling, 10,000 resamples per contrast",
         "result": "all 12 reported intervals agree within 0.0016 (tolerance 0.005); the study's exact draws are not "
                   "reproduced with default_rng(20261031) integer draws (differences up to 0.00095)"},
    ]
    notes = [
        "C1 needs the query centred on the reference mean before the top-5 directions are removed; without that "
        "centring predictions differ by up to 1.03 (all 419 rows). The protocol's wording supports centring both.",
        "Closest neighbour-set call: the k-th vs (k+1)-th similarity gap reached 5.4e-7 (C1, NCI-60) and 2.2e-6 (C1, 24Q2); "
        "the verifier's float64 implementation still selected identical neighbours everywhere.",
        "The leakage arm L beats the zero arm on the secondary endpoint (hit precision on actives 0.121 NCI-60, 0.120 24Q2 "
        "vs 0.10; one-sided one-sample p 0.003 and 0.004), so 0.10 understates the chance level of hit precision; the primary "
        "leakage rule is unaffected (L mean r 0.0137, p 0.236; -0.0116, p 0.259).",
        "RESULTS.json omits contrasts the protocol lists: every arm vs Z (primary and secondary) and the secondary context "
        "contrasts (C1-B2, B1-B0). The verifier computed them (check1_stats.json, unreported_contrasts): every non-L arm "
        "is far above Z on both sets (primary one-sided p < 0.001); secondary C1-B2 +0.022 (p 0.056) NCI-60, +0.012 (p 0.16) 24Q2.",
        "NCI-60 rules that excluded nothing here: the >=50-line rule removed no L1000-measured key, and dropping the "
        "failure-reason filter changes no killed-line count for the 419 keys.",
        "No undefined selective r occurred in either set, so the 'undefined counts as 0' rule was never used.",
        "Twenty development-pool drugs have no connectivity block (no structure); no query matches the pool by name or by "
        "Broad ID either (19Q4 treatment info), so the pool-overlap rule is satisfied beyond the ik14 test.",
        "Sealing: the verifier read only the ID column of every 24Q2 matrix row and parsed values only for the 101 query "
        "rows the run used. BRD-K57796080's row was not read.",
        "Forbidden files (gat_*.py, DEV_LOG.md, dev/, run logs) were never opened for reading; gat_*.py and DEV_LOG.md "
        "were hashed as opaque bytes for check 5, and dev/ files were not hashed.",
        "No DEVIATIONS.md exists in the study folder; all freeze-bound files hash-match and none was modified after "
        "04:53:24Z. Timeline (UTC): matrix created 04:53:39Z, modified 04:53:48Z; prism24q2.npz 04:54:34Z; NCI-60 run outputs "
        "04:58:55Z; 24Q2 outputs 04:59:17Z.",
        "The maintained module (src/virtual_cell/transcriptional_transfer.py) was used only as a secondary cross-check; "
        "it agrees with the verifier's implementation to 6e-16.",
        "REPORT.md was not written: the agent harness refused a report .md file from a subagent, so the report text was "
        "returned to the caller. The xlsx caches made by v02_parse_xlsx.py (221 MB) were deleted after use; re-run v02 "
        "first to reproduce. All freeze-bound files and RUN outputs were re-hashed at the end and are unchanged.",
    ]
    req = [c for c in checks if c["scope"] == "required"]
    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    out = {"verdict": verdict,
           "summary": {"checks_total": len(checks), "checks_passed": sum(c["pass"] for c in checks),
                       "required_total": len(req), "required_passed": sum(c["pass"] for c in req),
                       "verified_study_verdict": c1["verdict"], "verified_promote_C1": c1["promote_C1"]},
           "checks": checks, "discrepancies": discrepancies, "ambiguities": ambiguities, "notes": notes}
    json.dump(out, open(VER + "VERIFICATION.json", "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    print(verdict, out["summary"])
    for c in checks:
        if not c["pass"]:
            print("FAILED:", c["name"])


if __name__ == "__main__":
    main()
