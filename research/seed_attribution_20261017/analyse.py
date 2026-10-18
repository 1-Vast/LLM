"""Registered analysis of the fixed-seed attribution study: per-line records -> RESULTS.json.

File summary
- Path: research/seed_attribution_20261017/analyse.py
- Purpose: every contrast, interval, classification and sensitivity named in PROTOCOL.md, computed from
  the per-line records of `run.py` only (no PRISM data are read, so `verify.py` can recompute it).
- Statistics: hits per line (known qualified hits among the nominated or confirmed drugs; unknown is a
  non-hit). Paired differences over lines; the 21 lineages are the clusters (repeated lines of one
  lineage are not independent domains). Interval: cluster bootstrap 95%; one-sided sign-flip p over
  cluster means; Holm within each registered family. Both are the frozen `common.paired`/`holm`.
- Verdict vocabulary: for a contrast X - Y, "X_BETTER" iff mean >= MIN_EFFECT and the lower bound > 0;
  "Y_BETTER" iff mean <= -MIN_EFFECT and the upper bound < 0; "EQUIVALENT_WITHIN_MARGIN" iff the whole
  interval lies inside (-MIN_EFFECT, MIN_EFFECT); otherwise "NOT_DISTINGUISHABLE". The primary family
  also uses the frozen CONFIRMED / NOT_CONFIRMED / HARMFUL words with the Holm rule.
- Interfaces: `analyse(units) -> dict`, `main()` (writes RESULTS.json once).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corrected  # noqa: F401,E402  (puts the frozen study folder on sys.path)
from common import holm, paired  # noqa: E402  (frozen)

MIN_EFFECT = 0.10
LAYERS = ("policy", "I2", "I1")
CONVENTIONAL = ("C0_additive", "C1_global_ridge", "C1x_global_ridge_cross", "C2_per_drug_ridge", "C3_pooled_gbm")
VARIANT_ARMS = ("B_seed", "D_shared_only", "C1_global_ridge", "C3_pooled_gbm")
DRAWS, BOOT = 10000, 2000


# ---------------------------------------------------------------- helpers


def hits(units, layer, arm):
    return np.array(units["arms"][arm][layer]["hits"], float)


def unknown(units, layer, arm):
    return np.array(units["arms"][arm][layer]["unknown"], float)


def variant(units, key, field="hits"):
    return np.array(units["variants"][key][field], float)


def null_names(units):
    return sorted(k for k in units["arms"] if k.startswith("E") and k[1:].isdigit())


def null_mean(units, layer, field="hits"):
    names = null_names(units)
    return np.mean([np.array(units["arms"][n][layer][field], float) for n in names], axis=0)


def contrast(x, y, groups, mask=None):
    x, y, g = np.asarray(x, float), np.asarray(y, float), np.asarray(groups)
    if mask is not None:
        x, y, g = x[mask], y[mask], g[mask]
    r = paired(x - y, g, draws=DRAWS, boot=BOOT)
    r.update(mean_x=float(x.mean()), mean_y=float(y.mean()))
    lo, hi = r["ci95"]
    r["verdict"] = ("X_BETTER" if r["mean"] >= MIN_EFFECT and lo > 0 else "Y_BETTER" if r["mean"] <= -MIN_EFFECT and hi < 0
                    else "EQUIVALENT_WITHIN_MARGIN" if lo > -MIN_EFFECT and hi < MIN_EFFECT else "NOT_DISTINGUISHABLE")
    return r


def frozen_verdict(r, p_adj=None):
    lo, hi = r["ci95"]
    if hi < 0:
        return "HARMFUL"
    if r["mean"] >= MIN_EFFECT and lo > 0 and (p_adj is None or p_adj < 0.05):
        return "CONFIRMED"
    return "NOT_CONFIRMED"


def cluster_boot(diff, groups, stat, draws=BOOT, seed=20261017):
    """Cluster bootstrap interval of an arbitrary statistic of the per-line differences."""

    d, g = np.asarray(diff, float), np.asarray(groups)
    labels = sorted(set(g.tolist()))
    idx = {l: np.flatnonzero(g == l) for l in labels}
    rng = np.random.default_rng(seed)
    est = stat(d, g)
    vals = []
    for _ in range(draws):
        pick = rng.integers(0, len(labels), len(labels))
        sel = np.concatenate([idx[labels[i]] for i in pick])
        vals.append(stat(d[sel], g[sel]))
    vals = np.array([v for v in vals if np.isfinite(v)])
    return {"estimate": float(est), "ci95": [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if len(vals) else None}


def equal_cluster_mean(d, g):
    labels = sorted(set(g.tolist()))
    return float(np.mean([d[g == l].mean() for l in labels]))


# ---------------------------------------------------------------- sections


def means_table(units):
    out = {}
    for layer in LAYERS:
        out[layer] = {}
        for arm, rec in units["arms"].items():
            row = {"hits": float(np.mean(rec[layer]["hits"])), "unknown": float(np.mean(rec[layer]["unknown"]))}
            if layer == "policy":
                row.update(wells=float(np.mean(rec[layer]["wells"])), rounds=float(np.mean(rec[layer]["rounds"])))
            out[layer][arm] = row
    return out


def primary_family(units, groups):
    tests = {"P1_policy_B_vs_A": "policy", "P2_I2_B_vs_A": "I2", "P3_I1_B_vs_A": "I1"}
    res = {k: contrast(hits(units, L, "B_seed"), hits(units, L, "A_S"), groups) for k, L in tests.items()}
    adj = holm({k: v["p_one_sided"] for k, v in res.items()})
    for k, v in res.items():
        v["p_holm"] = adj[k]
        v["frozen_verdict"] = frozen_verdict(v, adj[k])
        v["layer"] = tests[k]
    survives = res["P1_policy_B_vs_A"]["frozen_verdict"] == "CONFIRMED"
    signal_remains = any(v["mean"] >= MIN_EFFECT and v["ci95"][0] > 0 for v in res.values())
    return {"tests": res, "seed_signal_survives_primary_layer": survives, "meaningful_signal_remains_any_layer": signal_remains}


def attribution(units, groups):
    out = {}
    for layer in LAYERS:
        A, B, D = (hits(units, layer, a) for a in ("A_S", "B_seed", "D_shared_only"))
        En = null_mean(units, layer)
        decomposition = {
            "correspondence_B_minus_null_mean": contrast(B, En, groups),
            "per_drug_calibration_B_minus_shared_only": contrast(B, D, groups),
            "shared_structure_shared_only_minus_A": contrast(D, A, groups),
            "capacity_null_mean_minus_A": contrast(En, A, groups),
            "seed_total_B_minus_A": contrast(B, A, groups)}
        adj = holm({k: v["p_one_sided"] for k, v in decomposition.items()})
        for k, v in decomposition.items():
            v["p_holm"] = adj[k]
        conventional = {}
        for c in CONVENTIONAL:
            x = hits(units, layer, c)
            conventional[c] = {"B_minus_C": contrast(B, x, groups), "C_minus_A": contrast(x, A, groups)}
        adj_c = holm({c: conventional[c]["B_minus_C"]["p_one_sided"] for c in CONVENTIONAL})
        for c in CONVENTIONAL:
            conventional[c]["B_minus_C"]["p_holm"] = adj_c[c]
        # null collection: library-level means and the exact permutation rank
        names = null_names(units)
        seed_mean = float(B.mean())
        null_means = {n: float(hits(units, layer, n).mean()) for n in names}
        ge = sum(1 for v in null_means.values() if v >= seed_mean)
        rank = {"seed_mean": seed_mean, "null_means": null_means, "null_mean_of_means": float(np.mean(list(null_means.values()))),
                "null_sd": float(np.std(list(null_means.values()), ddof=1)), "n_nulls": len(names),
                "n_nulls_at_least_seed": ge, "p_permutation": (1 + ge) / (1 + len(names)),
                "seed_exceeds_every_null": ge == 0,
                "null_libraries_above_A_by_margin": int(sum(1 for v in null_means.values() if v - float(A.mean()) >= MIN_EFFECT))}
        out[layer] = {"decomposition": decomposition, "conventional": conventional, "null_collection": rank}
    return out


def variance_decomposition(units, groups):
    out = {}
    for layer in ("I2", "I1"):
        A = hits(units, layer, "A_S")
        block = {}
        for arm in VARIANT_ARMS:
            full = hits(units, layer, arm)
            mean_only = variant(units, f"{arm}|{layer}|mean_only")
            var_only = variant(units, f"{arm}|{layer}|variance_only_oos")
            frozen_var = variant(units, f"{arm}|{layer}|full_frozen_variance")
            row = {"mean_only_minus_A": contrast(mean_only, A, groups), "variance_only_oos_minus_A": contrast(var_only, A, groups),
                   "full_minus_A": contrast(full, A, groups), "full_minus_mean_only": contrast(full, mean_only, groups),
                   "full_frozen_in_sample_variance_minus_A": contrast(frozen_var, A, groups),
                   "interaction": float(full.mean() - A.mean() - (mean_only.mean() - A.mean()) - (var_only.mean() - A.mean()))}
            if arm == "B_seed":
                row["variance_only_in_sample_minus_A"] = contrast(variant(units, f"{arm}|{layer}|variance_only_in_sample"), A, groups)
            block[arm] = row
        out[layer] = block
    return out


def gate_strata(units, groups):
    gates = {g: np.array(v, float) > 0.5 for g, v in units["_meta"]["gates"].items()}
    any_pos = np.any(np.column_stack(list(gates.values())), axis=1)
    prevalence = units["_meta"]["source_any_gate_prevalence"]
    out = {"lines_any_gate_positive": int(any_pos.sum()), "lines_all_gates_negative": int((~any_pos).sum())}
    for layer in LAYERS:
        A, B = hits(units, layer, "A_S"), hits(units, layer, "B_seed")
        diff = B - A
        block = {}
        for name, mask in (("gate_positive_lines", any_pos), ("gate_negative_lines", ~any_pos)):
            if mask.sum() >= 3 and len(set(np.asarray(groups)[mask].tolist())) >= 2:
                block[name] = contrast(B, A, groups, mask)
                block[name]["share_of_total_gain"] = float(diff[mask].sum() / diff.sum()) if diff.sum() != 0 else None
            else:
                block[name] = "UNSUPPORTED: fewer than 3 lines or 2 lineages"
        block["per_gene"] = {}
        for g, pos in gates.items():
            cell = {}
            for name, mask in (("positive", pos), ("negative", ~pos)):
                if mask.sum() >= 5 and len(set(np.asarray(groups)[mask].tolist())) >= 2:
                    r = contrast(B, A, groups, mask)
                    cell[name] = {"n_lines": int(mask.sum()), "mean": r["mean"], "ci95": r["ci95"]}
                else:
                    cell[name] = {"n_lines": int(mask.sum()), "mean": None, "ci95": None}
            block["per_gene"][g] = cell
        # mixture standardised to the source prevalence of "any seed gate positive"
        if any_pos.sum() >= 10 and (~any_pos).sum() >= 10:
            block["standardised_to_source_gate_mixture"] = _gate_standardised(diff, any_pos, groups, prevalence)
        else:
            block["standardised_to_source_gate_mixture"] = "UNSUPPORTED: a gate cell has fewer than 10 lines"
        out[layer] = block
    return out


def _gate_standardised(diff, any_pos, groups, prevalence):
    labels = np.asarray(groups)
    idx = np.arange(len(diff))

    def one(sel):
        dd, mm = diff[sel], any_pos[sel]
        if mm.sum() == 0 or (~mm).sum() == 0:
            return np.nan
        return prevalence * dd[mm].mean() + (1 - prevalence) * dd[~mm].mean()

    rng = np.random.default_rng(20261017)
    ls = sorted(set(labels.tolist()))
    members = {l: idx[labels == l] for l in ls}
    est = one(idx)
    vals = []
    for _ in range(BOOT):
        pick = rng.integers(0, len(ls), len(ls))
        sel = np.concatenate([members[ls[i]] for i in pick])
        vals.append(one(sel))
    vals = np.array([v for v in vals if np.isfinite(v)])
    return {"weights": {"gate_positive": prevalence, "gate_negative": 1 - prevalence}, "estimate": float(est),
            "ci95": [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]}


def disagreement(units, groups):
    """A vs B nominated (or confirmed) sets: how many differ, what the differing ones returned."""

    out = {}
    K = None
    for layer in LAYERS:
        if layer == "policy":
            sa = units["arms"]["A_S"]["policy"]["confirmed_drugs"]
            ta = units["arms"]["A_S"]["policy"]["status"]
            sb = units["arms"]["B_seed"]["policy"]["confirmed_drugs"]
            tb = units["arms"]["B_seed"]["policy"]["status"]
        else:
            sa, ta = units["arms"]["A_S"][layer]["nominated"], units["arms"]["A_S"][layer]["status"]
            sb, tb = units["arms"]["B_seed"][layer]["nominated"], units["arms"]["B_seed"][layer]["status"]
        groups_arr = np.asarray(groups)
        rows = []
        b_only_hit_groups = {}
        structure = units["_meta"]["structure_group"]
        for j in range(len(sa)):
            a_map, b_map = dict(zip(sa[j], ta[j])), dict(zip(sb[j], tb[j]))
            a_only = [d for d in a_map if d not in b_map]
            b_only = [d for d in b_map if d not in a_map]
            ha = sum(1 for d in a_only if a_map[d] == 1)
            hb = sum(1 for d in b_only if b_map[d] == 1)
            ua = sum(1 for d in a_only if a_map[d] == -1)
            ub = sum(1 for d in b_only if b_map[d] == -1)
            rows.append((len(a_only), len(b_only), ha, hb, ua, ub))
            for d in b_only:
                if b_map[d] == 1:
                    b_only_hit_groups[structure[d]] = b_only_hit_groups.get(structure[d], 0) + 1
        arr = np.array(rows, float)
        net = arr[:, 3] - arr[:, 2]
        diff = hits(units, layer, "B_seed") - hits(units, layer, "A_S")
        total_b_only = arr[:, 1].sum()
        total_a_only = arr[:, 0].sum()
        top_group = max(b_only_hit_groups.values()) if b_only_hit_groups else 0
        out[layer] = {
            "differing_nominations_per_line_A_only": float(arr[:, 0].mean()), "differing_nominations_per_line_B_only": float(arr[:, 1].mean()),
            "lines_with_any_difference": int((arr[:, 1] > 0).sum()),
            "hits_per_B_only_nomination": float(arr[:, 3].sum() / total_b_only) if total_b_only else None,
            "hits_per_A_only_nomination": float(arr[:, 2].sum() / total_a_only) if total_a_only else None,
            "unknown_per_B_only_nomination": float(arr[:, 5].sum() / total_b_only) if total_b_only else None,
            "unknown_per_A_only_nomination": float(arr[:, 4].sum() / total_a_only) if total_a_only else None,
            "net_hits_from_differing_nominations": float(net.mean()),
            "net_equals_B_minus_A_contrast": bool(np.allclose(net, diff)),
            "b_only_hit_scaffold_groups": len(b_only_hit_groups), "b_only_hits": int(arr[:, 3].sum()),
            "largest_scaffold_group_share_of_b_only_hits": float(top_group / arr[:, 3].sum()) if arr[:, 3].sum() else None}
    return out


def lineage_support(units, groups):
    out = {}
    g = np.asarray(groups)
    labels = sorted(set(g.tolist()))
    strata = np.asarray(units["_meta"]["stratum"])
    for layer in LAYERS:
        diff = hits(units, layer, "B_seed") - hits(units, layer, "A_S")
        per = {l: {"lines": int((g == l).sum()), "mean": float(diff[g == l].mean())} for l in labels}
        loo = [equal_cluster_mean(diff[g != l], g[g != l]) for l in labels]
        loo_pooled = [float(diff[g != l].mean()) for l in labels]
        positive = sum(1 for v in per.values() if v["mean"] > 0)
        negative = sum(1 for v in per.values() if v["mean"] < 0)
        contributions = sorted(((l, float(diff[g == l].sum())) for l in labels), key=lambda t: -abs(t[1]))
        total = float(diff.sum())
        out[layer] = {
            "per_lineage": per, "lineages_positive": positive, "lineages_negative": negative, "n_lineages": len(labels),
            "leave_one_lineage_out_pooled_mean_range": [min(loo_pooled), max(loo_pooled)],
            "leave_one_lineage_out_equal_lineage_mean_range": [min(loo), max(loo)],
            "largest_lineage_contribution": {"lineage": contributions[0][0], "share_of_total": contributions[0][1] / total if total else None},
            "by_stratum": {s: contrast(hits(units, layer, "B_seed"), hits(units, layer, "A_S"), groups, strata == s)
                           for s in sorted(set(strata.tolist()))},
        }
    return out


def standardised(units, groups):
    out = {}
    strata = np.asarray(units["_meta"]["stratum"])
    for layer in LAYERS:
        diff = hits(units, layer, "B_seed") - hits(units, layer, "A_S")
        g = np.asarray(groups)
        by_stratum = {s: float(diff[strata == s].mean()) for s in sorted(set(strata.tolist())) if (strata == s).sum() >= 10}
        out[layer] = {
            "pooled_lines": float(diff.mean()),
            "equal_lineage_weights": cluster_boot(diff, g, equal_cluster_mean),
            "equal_stratum_weights": ({"estimate": float(np.mean(list(by_stratum.values()))), "strata": by_stratum}
                                      if len(by_stratum) == 2 else "UNSUPPORTED")}
    return out


def unknown_sensitivity(units, groups):
    out = {}
    for layer in LAYERS:
        A, B = hits(units, layer, "A_S"), hits(units, layer, "B_seed")
        uA, uB = unknown(units, layer, "A_S"), unknown(units, layer, "B_seed")
        if layer == "policy":
            nA = np.array(units["arms"]["A_S"]["policy"]["confirmed"], float)
            nB = np.array(units["arms"]["B_seed"]["policy"]["confirmed"], float)
        else:
            nA = nB = np.full(len(A), 10.0)
        rateA, rateB = A / np.maximum(nA - uA, 1), B / np.maximum(nB - uB, 1)
        optimistic_A = A + uA * (A.sum() / np.maximum((nA - uA).sum(), 1))
        optimistic_B = B + uB * (B.sum() / np.maximum((nB - uB).sum(), 1))
        entry = {"unknown_per_line_B_minus_A": contrast(uB, uA, groups),
                 "hit_rate_among_known_B_minus_A": contrast(rateB, rateA, groups),
                 "lower_bound_unknown_as_miss_B_minus_A": contrast(B, A, groups),
                 "upper_bound_unknown_at_pooled_hit_rate_B_minus_A": contrast(optimistic_B, optimistic_A, groups)}
        key = "policy" if layer == "policy" else layer
        a_key, b_key = f"A_S|{key}|availability_weighted", f"B_seed|{key}|availability_weighted"
        if a_key in units["variants"] and b_key in units["variants"]:
            entry["availability_weighted_B_minus_A"] = contrast(variant(units, b_key), variant(units, a_key), groups)
            entry["availability_weighted_unknown_B_minus_A"] = contrast(variant(units, b_key, "unknown"), variant(units, a_key, "unknown"), groups)
        out[layer] = entry
    return out


def costs(units):
    out = {"wells_per_line": {}, "rounds_per_line": {}, "compute_seconds": units["seconds"]}
    pol = units["arms"]
    for arm, rec in pol.items():
        out["wells_per_line"][arm] = float(np.mean(rec["policy"]["wells"]))
        out["rounds_per_line"][arm] = float(np.mean(rec["policy"]["rounds"]))
    out["note"] = ("deployment wells and rounds are equal across arms by construction (28 wells, exploit-first batches); "
                   "arms differ in compute and in what must be curated: B and D need ten authored programs, E needs none beyond the "
                   "permutation rule, C needs a tuning grid; no LLM spend; the DNA panel is one assay unit per line in every arm")
    return out


def classify(primary, attr):
    """The registered reading of the attribution contrasts at the primary layer (and at every layer)."""

    out = {}
    for layer in LAYERS:
        d = attr[layer]["decomposition"]
        n = attr[layer]["null_collection"]
        total = d["seed_total_B_minus_A"]["mean"]
        statements = []
        corr = d["correspondence_B_minus_null_mean"]
        if corr["verdict"] == "X_BETTER" and n["seed_exceeds_every_null"]:
            statements.append("CORRESPONDENCE_SUPPORTED: the seed pairing beats the matched permutations and every single null")
        elif corr["verdict"] in ("NOT_DISTINGUISHABLE", "EQUIVALENT_WITHIN_MARGIN"):
            statements.append("CORRESPONDENCE_NOT_ESTABLISHED: the seed pairing is not distinguishable from matched permutations")
        elif corr["verdict"] == "Y_BETTER":
            statements.append("PERMUTED_PAIRINGS_BETTER: the seed pairing loses to matched permutations")
        else:
            statements.append("CORRESPONDENCE_PARTIAL: the mean contrast passes but the seed does not exceed every null")
        cap = d["capacity_null_mean_minus_A"]
        statements.append("CAPACITY_ALONE_GAINS" if cap["verdict"] == "X_BETTER" else "CAPACITY_ALONE_DOES_NOT_GAIN"
                          if cap["verdict"] in ("NOT_DISTINGUISHABLE", "EQUIVALENT_WITHIN_MARGIN") else "CAPACITY_ALONE_HURTS")
        pdc = d["per_drug_calibration_B_minus_shared_only"]
        statements.append({"X_BETTER": "PER_DRUG_LOADINGS_HELP", "Y_BETTER": "PER_DRUG_LOADINGS_HURT"}.get(pdc["verdict"], "PER_DRUG_LOADINGS_NOT_DISTINGUISHABLE"))
        shared = d["shared_structure_shared_only_minus_A"]
        statements.append("SHARED_STRUCTURE_GAINS" if shared["verdict"] == "X_BETTER" else "SHARED_STRUCTURE_NOT_DISTINGUISHABLE")
        conv = {c: attr[layer]["conventional"][c]["B_minus_C"]["verdict"] for c in CONVENTIONAL}
        out[layer] = {"seed_total_B_minus_A": total, "statements": statements, "B_vs_conventional": conv}
    return out


def analyse(units: dict) -> dict:
    groups = np.array(units["_meta"]["cluster"])
    res = {"meta": {"n_lines": len(groups), "n_clusters": len(set(groups.tolist())), "strata": {s: int((np.array(units["_meta"]["stratum"]) == s).sum())
                                                                                       for s in sorted(set(units["_meta"]["stratum"]))},
                    "undefined_reference_drugs": units["_meta"]["undefined_reference_drugs"], "n_nulls": len(null_names(units)),
                    "parity_with_frozen_implementation": units["parity"], "min_effect": MIN_EFFECT,
                    "data_status": "EXPOSED future strata (opened by program_revision_20261017); attribution, not confirmation"}}
    res["means"] = means_table(units)
    res["primary"] = primary_family(units, groups)
    res["attribution"] = attribution(units, groups)
    res["variance_decomposition"] = variance_decomposition(units, groups)
    res["gate_strata"] = gate_strata(units, groups)
    res["disagreement"] = disagreement(units, groups)
    res["lineage_support"] = lineage_support(units, groups)
    res["standardised"] = standardised(units, groups)
    res["unknown_sensitivity"] = unknown_sensitivity(units, groups)
    res["secondary_policy_on_I1_fold"] = {
        "B_minus_A": contrast(np.array(units["arms"]["B_seed"]["policy_I1fold"]["hits"], float),
                              np.array(units["arms"]["A_S"]["policy_I1fold"]["hits"], float), groups)}
    res["cost"] = costs(units)
    res["classification"] = classify(res["primary"], res["attribution"])
    return res


def main():
    records = HERE / "records" / "units.json"
    out = HERE / "RESULTS.json"
    if out.exists():
        raise SystemExit("RESULTS.json exists; the registered analysis is write-once")
    units = json.loads(records.read_text(encoding="utf-8"))
    res = analyse(units)
    import hashlib
    res["units_sha256"] = hashlib.sha256(records.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    out.write_bytes((json.dumps(res, indent=1, allow_nan=False) + "\n").encode("utf-8"))
    p = res["primary"]
    print(json.dumps({k: [round(v["mean"], 3), [round(x, 3) for x in v["ci95"]], v["frozen_verdict"]] for k, v in p["tests"].items()}, indent=1))
    print("seed signal survives:", p["seed_signal_survives_primary_layer"], "| signal remains:", p["meaningful_signal_remains_any_layer"])


if __name__ == "__main__":
    main()
