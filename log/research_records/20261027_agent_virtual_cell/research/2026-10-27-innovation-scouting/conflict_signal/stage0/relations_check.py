"""relations_check.py - R198-A1 Stage 0 relation qualification audit (ENGINEERING IMPLEMENTATION ONLY).

This script implements the Stage 0 protocol in `../relations_check_design.md` / `../protocol_draft_v2.md`
(P0a). It is deterministic, response-aware only for the pre-declared reference cells, and it is
**gated**: by default it refuses to read real data. Real Stage 0 may run only with `--confirm-run`
AND `run_gate.real_run_enabled=true` in the config AND a frozen utility_range/delta_min.

This round (task-48) only writes the implementation; it was NOT run on real data. The synthetic
self-check (`synthetic_selfcheck.py`) exercises this module on pure synthetic data.

Usage (real run - BLOCKED until Lead approval):
    & D:\\anaconda\\envs\\maestro\\python.exe relations_check.py --confirm-run

Default (safe):
    & D:\\anaconda\\envs\\maestro\\python.exe relations_check.py
    -> prints refusal JSON, exits 3; no real file is opened.
"""
import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

STATUS_PASS = "pass"
STATUS_DATA = "data_unavailable"
STATUS_DESIGN = "design_invalid"
STATUS_BLOCKED = "blocked_by_utility_definition"
STATUS_REFUSED = "refused"

BASE = Path(__file__).resolve().parents[4]          # D:\MAESTRO
CONFIG_PATH = Path(__file__).resolve().parent / "relations_check_config.json"


# ------------------------------------------------------------------ small utils
def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest().upper()


def sha256_json(obj):
    return sha256_bytes(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf8"))


def sha256_cell_list(cells):
    return sha256_bytes("\n".join(sorted(cells)).encode("utf8"))


def normalize_cell(x):
    """NFKC -> casefold -> keep alnum only (frozen normalization)."""
    return "".join(ch for ch in unicodedata.normalize("NFKC", str(x)).casefold() if ch.isalnum())


def load_config(path=CONFIG_PATH):
    return json.loads(Path(path).read_text(encoding="utf8"))


def round_sig(x, digits=6):
    if x is None or isinstance(x, str):
        return x
    if abs(x) < 1e-300:
        return 0.0
    return round(float(x), digits)


# ------------------------------------------------------------------ gate
def check_run_gate(cfg, confirm_run, mode="relations_check"):
    """Return (status, reason) or (None, None) if a real run is permitted.

    Mode-aware gate (v4.1 fix):
      - both modes: default or --confirm-run alone -> refused (exit 3);
      - both modes: real_run_enabled must be true (exit 3 otherwise);
      - mode="p0a_metadata": only the two-key gate is required. P0d utility/delta_min
        (blocked_by_utility_definition) does NOT block the metadata-only precheck;
      - mode="relations_check": utility range is required only when
        utility.utility_gate_required_for_run is true; if false (v4 config), P0a
        relations_check is allowed before P0d, and a real utility block returns BLOCKED.
    """
    gate = cfg["run_gate"]
    utility = cfg["utility"]
    if not confirm_run:
        return STATUS_REFUSED, "refused: --confirm-run flag is required; default mode never reads real data"
    if gate.get("real_run_enabled", False) is not True:
        return STATUS_REFUSED, ("refused: run_gate.real_run_enabled=false in config; Lead must set it true "
                                "after (a) A1v4.1 review passes, (b) Lead approval, (c) two-key run approval")
    if mode == "relations_check" and bool(utility.get("utility_gate_required_for_run", True)):
        if (utility.get("utility_range") is None
                or utility.get("delta_min_state") == "blocked_by_utility_definition"):
            return STATUS_BLOCKED, ("blocked_by_utility_definition: utility_range/delta_min not frozen; the full "
                                    "relations_check requires the utility gate when utility_gate_required_for_run=true. "
                                    "Fill config.utility.utility_range (and delta_min_state) after P0d/A5, or run the "
                                    "metadata-only precheck with --p0a-metadata.")
    return None, None


# ------------------------------------------------------------------ cell allocation (metadata only)
def allocate_cells(cell_tissue, cfg):
    """Deterministic stratified allocation: reference (A/B) / feedback S / unqueried U, disjoint.

    cell_tissue: {cell_name: tissue_label}. Returns dict with sorted lists + sha + warnings.
    """
    alloc_cfg = cfg["cell_allocation"]
    seed = int(alloc_cfg["seed"])
    rng = random.Random(seed)
    by_tissue = defaultdict(list)
    for cell in sorted(cell_tissue):
        by_tissue[str(cell_tissue[cell])].append(cell)
    tissues = sorted(by_tissue)
    ref_target = int(alloc_cfg["reference_total"])
    min_per_tissue = int(alloc_cfg.get("min_reference_per_tissue", 0))
    A, B, S, U = [], [], [], []
    warnings = []
    ref_alloc = {t: min(min_per_tissue, len(by_tissue[t])) for t in tissues}
    total_ref = sum(ref_alloc.values())
    if total_ref > ref_target:
        # global cap: trim proportionally from the largest allocations
        while total_ref > ref_target:
            t = max(tissues, key=lambda x: (ref_alloc[x], x))
            if ref_alloc[t] == 0:
                break
            ref_alloc[t] -= 1
            total_ref -= 1
        warnings.append("reference_total_capped")
    elif total_ref < ref_target:
        remaining_cap = {t: len(by_tissue[t]) - ref_alloc[t] for t in tissues}
        need = ref_target - total_ref
        while need > 0:
            candidates = [t for t in tissues if remaining_cap[t] > 0]
            if not candidates:
                break
            t = max(candidates, key=lambda x: (remaining_cap[x], x))
            ref_alloc[t] += 1
            remaining_cap[t] -= 1
            need -= 1
        if sum(ref_alloc.values()) < ref_target:
            warnings.append("reference_below_target_due_to_cell_count")
    a_target = int(alloc_cfg["half_A"])
    b_target = int(alloc_cfg["half_B"])
    # A/B split within each tissue's reference pool (deterministic shuffle)
    for t in tissues:
        pool = list(by_tissue[t])
        rng.shuffle(pool)
        ref_pool = pool[:ref_alloc[t]]
        rng.shuffle(ref_pool)
        n_a = int(round(ref_alloc[t] * a_target / max(1, a_target + b_target)))
        A.extend(ref_pool[:n_a])
        B.extend(ref_pool[n_a:])
    remaining = {t: [c for c in by_tissue[t] if c not in set(A) | set(B)] for t in tissues}
    s_target = int(alloc_cfg["feedback_S"])
    s_alloc = {t: 0 for t in tissues}
    total_s = 0
    while total_s < s_target:
        candidates = [t for t in tissues if len(remaining[t]) - s_alloc[t] > 0]
        if not candidates:
            break
        t = max(candidates, key=lambda x: (len(remaining[t]) - s_alloc[t], x))
        s_alloc[t] += 1
        total_s += 1
    if total_s < s_target:
        warnings.append("feedback_S_below_target_due_to_cell_count")
    for t in tissues:
        S.extend(remaining[t][: s_alloc[t]])
        U.extend(remaining[t][s_alloc[t]:])
    A, B, S, U = sorted(set(A)), sorted(set(B)), sorted(set(S)), sorted(set(U))
    overlap = (set(A) & set(B)) | (set(A) & set(S)) | (set(A) & set(U)) | (set(B) & set(S)) | (set(B) & set(U)) | (set(S) & set(U))
    if overlap:
        raise RuntimeError(f"cell allocation overlap: {sorted(overlap)[:5]}")

    def tissue_counts(cells_):
        return {t: sum(1 for c in cells_ if str(cell_tissue[c]) == t) for t in tissues}

    if not alloc_cfg.get("record_cell_names", False):
        splits = {k: {"n": len(v), "sha256": sha256_cell_list(v),
                      "tissues": dict(sorted(tissue_counts(v).items()))}
                  for k, v in (("A", A), ("B", B), ("S", S), ("U", U))}
    else:
        splits = {k: {"n": len(v), "sha256": sha256_cell_list(v), "cells": v,
                      "tissues": dict(sorted(tissue_counts(v).items()))}
                  for k, v in (("A", A), ("B", B), ("S", S), ("U", U))}
    return {"A": A, "B": B, "S": S, "U": U, "splits": splits, "warnings": sorted(warnings),
            "seed": seed, "tissues": tissues}


# ------------------------------------------------------------------ v4 metadata-only P0a (plan A: per-tissue Breast/Colon)
def allocate_reference_v4(cell_tissue, matched_cells, cfg):
    """Explicit per-tissue A/B reference counts from the matched pool (v4 plan A)."""
    alloc = cfg["cell_allocation"]
    explicit = alloc.get("explicit_tissue_counts")
    if explicit is None:
        return None
    matched = set(matched_cells)
    by_tissue = defaultdict(list)
    for cell in sorted(cell_tissue):
        if cell in matched:
            by_tissue[str(cell_tissue[cell])].append(cell)
    A, B, warnings = [], [], []
    for tissue in sorted(set(list(explicit["A"]) + list(explicit["B"]))):
        na = int(explicit["A"].get(tissue, 0))
        nb = int(explicit["B"].get(tissue, 0))
        pool = by_tissue.get(tissue, [])
        if len(pool) < na + nb:
            warnings.append(f"insufficient_matched_cells:{tissue}")
        A.extend(pool[:na])
        B.extend(pool[na:na + nb])
    leftover = sorted(set(cell_tissue) - set(A) - set(B))
    return {"A": sorted(set(A)), "B": sorted(set(B)), "leftover": leftover, "warnings": sorted(warnings)}


def build_cell_conditions(matched_rows, cfg):
    """cell -> set((anchor, ac, lc, library)) from metadata-only matched_conditions rows."""
    dk = cfg["data"]
    conds = defaultdict(set)
    cells = set()
    for r in matched_rows:
        cell = normalize_cell(r[dk["cell_column"]] if dk["cell_column"] in r else r.get("cell"))
        anchor = str(r[dk["anchor_id_column"]] if dk["anchor_id_column"] in r else r["anchor_id"]).strip()
        ac = str(r[dk["anchor_conc_column"]] if dk["anchor_conc_column"] in r else r["anchor_conc"]).strip()
        lc = str(r[dk["library_conc_column"]] if dk["library_conc_column"] in r else r["library_conc"]).strip()
        lib = str(r[dk["library_id_column"]] if dk["library_id_column"] in r else r["library_id"]).strip()
        conds[cell].add((anchor, ac, lc, lib))
        cells.add(cell)
    return conds, cells


def canon_conc(x):
    """Canonicalize concentration labels across fitted/matched tables (float -> '.10g')."""
    try:
        return format(float(x), ".10g")
    except (TypeError, ValueError):
        return str(x).strip()


def _group_cell_conditions(cell_conditions, cells):
    """cell -> (anchor, canon_ac, canon_lc) -> set(libraries) for the given cells."""
    out = {}
    for cell in cells:
        groups = defaultdict(set)
        for (anchor, ac, lc, lib) in cell_conditions.get(cell, ()):
            groups[(str(anchor).strip(), canon_conc(ac), canon_conc(lc))].add(str(lib).strip())
        out[cell] = groups
    return out


def enumerate_candidate_universe(conds, cell_tissue, cell_subset, cfg, matched_conds=None):
    """Per-tissue candidate grid (same anchor / same two concentrations / same-direction library contrasts).

    Candidate keys are the UNION of per-cell (anchor, ac, lc, library-pair) groups over the matched
    cell_subset, matching the A0/challenge enumeration (229 total; Breast 134 + Colon 37 + Pancreas 58).
    `matched_conds` (keys from matched_conditions.csv) drives the key enumeration when provided; `conds`
    (all Original metadata) is used for candidate cells so the S-side Cond_r coverage can be evaluated on
    the leftover pool.
    """
    main_tissues = [str(t) for t in cfg["candidate_enumeration"]["main_family_tissues"]]
    key_conds = matched_conds if matched_conds is not None else conds
    per_cell = _group_cell_conditions(key_conds, sorted(cell_subset))
    keys = {}
    for cell in sorted(cell_subset):
        tissue = cell_tissue.get(cell)
        if tissue not in main_tissues:
            continue
        for (anchor, ac, lc), libs in per_cell[cell].items():
            ordered = sorted(libs)
            for i in range(len(ordered)):
                for j in range(i + 1, len(ordered)):
                    key = (tissue, anchor, ac, lc, ordered[i], ordered[j])
                    keys[key] = True
    out = []
    canon_conds = {c: {(str(a).strip(), canon_conc(x), canon_conc(y), str(l).strip())
                       for (a, x, y, l) in conds.get(c, ())} for c in conds}
    for (tissue, anchor, ac, lc, l1, l2) in sorted(keys):
        cells = sorted(c for c in canon_conds
                       if cell_tissue.get(c) == tissue
                       and (anchor, ac, lc, l1) in canon_conds[c]
                       and (anchor, ac, lc, l2) in canon_conds[c])
        if cells:
            out.append({"tissue": tissue, "anchor": anchor, "ac": ac, "lc": lc,
                        "library_1": l1, "library_2": l2, "cells": cells})
    return out


def select_s_cells(candidates, conds, cell_tissue, leftover, cfg):
    """Metadata-only S selection maximizing the number of candidates with >=n_ctx S cells in Cond_r.

    Primary: binary MILP via scipy.optimize.milp (deterministic HiGHS); fallback: deterministic greedy.
    Per-tissue S counts come from cell_allocation.explicit_tissue_counts["S"].
    """
    main_tissues = [str(t) for t in cfg["candidate_enumeration"]["main_family_tissues"]]
    n_ctx = int(cfg["statistics"]["n_ctx_min"])
    s_counts_cfg = cfg["cell_allocation"].get("explicit_tissue_counts", {}).get("S", {})
    s_target = int(cfg["cell_allocation"]["feedback_S"])
    eligible_cells = [c for c in leftover if cell_tissue.get(c) in main_tissues]
    # per-tissue caps (must sum to s_target; if not, fall back to proportional target)
    counts = {t: int(s_counts_cfg.get(t, 0)) for t in main_tissues}
    if sum(counts.values()) != s_target:
        # deterministic proportional allocation
        counts = {t: 0 for t in main_tissues}
        remaining = s_target
        pools = {t: [c for c in eligible_cells if cell_tissue.get(c) == t] for t in main_tissues}
        while remaining > 0:
            cand = [t for t in main_tissues if len(pools[t]) - counts[t] > 0]
            if not cand:
                break
            t = min(cand, key=lambda x: (-(len(pools[x]) - counts[x]), x))
            counts[t] += 1
            remaining -= 1
    rel_cells = [[c for c in eligible_cells
                  if cell_tissue.get(c) == rel["tissue"]
                  and all((rel["anchor"], rel["ac"], rel["lc"], lib) in conds.get(c, ())
                          for lib in (rel["library_1"], rel["library_2"]))]
                 for rel in candidates]

    def covered(sel):
        sel_set = set(sel)
        return [i for i, cells in enumerate(rel_cells) if len(sel_set & set(cells)) >= n_ctx]

    solver = "greedy"
    chosen = []
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        cell_idx = {c: i for i, c in enumerate(eligible_cells)}
        n_cells, n_rel = len(eligible_cells), len(candidates)
        n_var = n_cells + n_rel
        c_obj = np.zeros(n_var)
        c_obj[n_cells:] = -1.0                       # maximize covered relations
        c_obj[:n_cells] = 1e-9 * np.arange(n_cells)  # deterministic tie-break
        integrality = np.ones(n_var)
        bounds = Bounds(np.zeros(n_var), np.ones(n_var))
        rows = []
        lb = []
        ub = []
        # per-tissue S counts
        for t in main_tissues:
            row = np.zeros(n_var)
            for i, c in enumerate(eligible_cells):
                if cell_tissue.get(c) == t:
                    row[i] = 1.0
            rows.append(row); lb.append(counts.get(t, 0)); ub.append(counts.get(t, 0))
        # sum x == s_target (implied by per-tissue, but keep explicit for safety)
        row = np.zeros(n_var); row[:n_cells] = 1.0
        rows.append(row); lb.append(s_target); ub.append(s_target)
        # relation coverage: n_ctx*y_r - sum eligible x <= 0
        for r, cells in enumerate(rel_cells):
            row = np.zeros(n_var)
            row[n_cells + r] = n_ctx
            for c in cells:
                if c in cell_idx:
                    row[cell_idx[c]] = -1.0
            rows.append(row); lb.append(-np.inf); ub.append(0.0)
        cons = LinearConstraint(np.vstack(rows), np.array(lb), np.array(ub))
        res = milp(c=c_obj, integrality=integrality, bounds=bounds, constraints=cons,
                   options={"time_limit": 120, "disp": False})
        if res is not None and res.x is not None and res.status in (0,):
            x = np.round(res.x[:n_cells]).astype(int)
            chosen = [eligible_cells[i] for i in range(n_cells) if x[i] == 1]
            # deterministic check of counts
            ok = all(sum(1 for c in chosen if cell_tissue.get(c) == t) == counts.get(t, 0)
                     for t in main_tissues)
            if ok and len(chosen) == s_target:
                solver = "milp"
            else:
                chosen = []
    except Exception:
        chosen = []
    if not chosen:
        # deterministic greedy fallback
        chosen = []
        for t in main_tissues:
            t_cells = [c for c in eligible_cells if cell_tissue.get(c) == t]
            for _ in range(counts.get(t, 0)):
                best = None
                best_gain = -1
                for c in t_cells:
                    if c in chosen:
                        continue
                    gain = len(covered(chosen + [c]))
                    key = (-gain, c)
                    if best is None or key < best[0]:
                        best = (key, c)
                if best is not None:
                    chosen.append(best[1])
    covered_idx = covered(chosen)
    return {"S": sorted(chosen), "solver": solver, "covered_candidates": len(covered_idx),
            "per_tissue_counts": {t: sum(1 for c in chosen if cell_tissue.get(c) == t) for t in main_tissues},
            "s_target": s_target, "n_ctx_min": n_ctx}


def run_p0a_metadata(cell_tissue, matched_cells, conds, cfg, matched_conds=None):
    """P0a-metadata (metadata-only): allocation, candidate grid, S-side Cond_r precheck, gates."""
    main_tissues = [str(t) for t in cfg["candidate_enumeration"]["main_family_tissues"]]
    excluded = [str(t) for t in cfg["candidate_enumeration"].get("excluded_tissues", [])]
    result = {"schema": "r198-a1-stage0-p0a-metadata-v4", "status": None, "reasons": [], "gates": {},
              "counts": {}, "config_sha256": None, "synthetic": False}
    ref = allocate_reference_v4(cell_tissue, matched_cells, cfg)
    if ref is None:
        result["status"] = STATUS_DESIGN
        result["reasons"] = ["explicit_tissue_counts_missing"]
        return result
    A, B, leftover = ref["A"], ref["B"], ref["leftover"]
    ref_pool = set(A) | set(B)
    result["gates"]["reference_matched_subset"] = ref_pool <= set(matched_cells)
    result["gates"]["reference_size_ok"] = len(A) == int(cfg["cell_allocation"]["half_A"]) and \
        len(B) == int(cfg["cell_allocation"]["half_B"])
    universe = enumerate_candidate_universe(conds, cell_tissue, sorted(matched_cells), cfg,
                                            matched_conds=matched_conds)
    result["counts"]["candidate_grid_by_tissue"] = {t: sum(1 for r in universe if r["tissue"] == t)
                                                    for t in sorted({r["tissue"] for r in universe})}
    result["counts"]["candidate_grid_total"] = len(universe)
    result["_candidate_keys"] = [(r["tissue"], r["anchor"], r["ac"], r["lc"],
                                  r["library_1"], r["library_2"]) for r in universe]
    # A/B supply per candidate
    A_set, B_set = set(A), set(B)
    supply_ok = []
    for rel in universe:
        n_a = len([c for c in rel["cells"] if c in A_set])
        n_b = len([c for c in rel["cells"] if c in B_set])
        rel["n_A"] = n_a
        rel["n_B"] = n_b
        if n_a >= int(cfg["candidate_enumeration"]["min_cells_half_A"]) and \
           n_b >= int(cfg["candidate_enumeration"]["min_cells_half_B"]):
            supply_ok.append(rel)
    result["counts"]["ab_supply_candidates"] = len(supply_ok)
    # S-side metadata precheck via coverage maximization
    sel = select_s_cells(supply_ok, conds, cell_tissue, leftover, cfg)
    S = sel["S"]
    S_set = set(S)
    precheck_ok = []
    for rel in supply_ok:
        n_s = len([c for c in rel["cells"] if c in S_set])
        rel["n_S"] = n_s
        if n_s >= int(cfg["statistics"]["n_ctx_min"]):
            precheck_ok.append(rel)
    result["counts"]["s_selection"] = {k: v for k, v in sel.items() if k != "S"}
    result["_s_cells"] = sel["S"]
    result["_a_cells"] = A
    result["_b_cells"] = B
    result["counts"]["precheck_eligible"] = len(precheck_ok)
    result["counts"]["precheck_eligible_by_tissue"] = {t: sum(1 for r in precheck_ok if r["tissue"] == t)
                                                       for t in main_tissues}
    U = sorted(set(leftover) - S_set)
    splits = {k: {"n": len(v), "sha256": sha256_cell_list(v),
                  "tissues": {t: sum(1 for c in v if cell_tissue.get(c) == t) for t in sorted(set(cell_tissue.values()))}}
              for k, v in (("A", A), ("B", B), ("S", S), ("U", U))}
    overlap = (set(A) & set(B)) | (set(A) & set(S)) | (set(A) & set(U)) | (set(B) & set(S)) | (set(B) & set(U)) | (set(S) & set(U))
    result["gates"]["three_way_disjoint"] = not overlap
    result["gates"]["main_tissues_breast_colon"] = main_tissues == ["Breast", "Colon"]
    result["gates"]["pancreas_excluded"] = ("Pancreas" in excluded) and \
        not any(r["tissue"] == "Pancreas" for r in universe)
    span_bad = [r for r in universe if len({cell_tissue.get(c) for c in r["cells"]}) != 1]
    result["gates"]["tissue_span_non_vacuity"] = len(span_bad) == 0 and len(universe) > 0
    result["gates"]["s_side_cond_cov_ge_12"] = len(precheck_ok) > 0
    target = int(cfg["global_acceptance"].get("coverage_min_abs") or
                 math.ceil(float(cfg["global_acceptance"]["coverage_min"]) * float(cfg["global_acceptance"]["coverage_denominator"])))
    result["counts"]["coverage_denominator"] = int(cfg["global_acceptance"].get("coverage_denominator") or 0)
    result["counts"]["coverage_target"] = target
    # expected-passing count = actual metadata-only S-coverage optimum (the operational gate)
    result["counts"]["s_milp_optimum"] = int(sel["covered_candidates"])
    result["counts"]["expected_passing_count"] = int(sel["covered_candidates"])
    result["counts"]["s_solver"] = sel["solver"]
    result["counts"]["s_splits_sha256"] = sha256_cell_list(S)
    result["counts"]["reference_cells_note"] = (
        "reference 84 includes A9+B9=18 Pancreas cells that are NOT used by the per-tissue Breast/Colon "
        "main family (no tissue nuisance in the main model); retained only to keep the frozen 84/24/17 composition")
    result["counts"]["v3_reference_values_not_applicable"] = {
        "v3_upper_bound_all_candidates": 114,
        "v3_upper_bound_breast_colon": 112,
        "note": ("v3 MILP values under a DIFFERENT S composition (24 taken from the 41 leftover pool, possibly "
                 "cross-tissue); they are NOT a v4 bound, NOT a reachability proof, and are NOT used as a gate. "
                 "v4 uses the actual s_milp_optimum."),
    }
    result["gates"]["precheck_eligible_ge_target"] = len(precheck_ok) >= target
    result["gates"]["s_milp_optimum_ge_target"] = int(sel["covered_candidates"]) >= target
    result["gates"]["s_selection_solver"] = sel["solver"]
    result["allocation"] = {"A": len(A), "B": len(B), "S": len(S), "U": len(U),
                            "reference_warnings": ref["warnings"], "splits": splits,
                            "A_cells": A if cfg["cell_allocation"].get("record_cell_names") else None,
                            "B_cells": B if cfg["cell_allocation"].get("record_cell_names") else None,
                            "S_cells": S if cfg["cell_allocation"].get("record_cell_names") else None,
                            "U_cells": U if cfg["cell_allocation"].get("record_cell_names") else None}
    failed = [k for k, v in result["gates"].items() if isinstance(v, bool) and not v]
    if failed:
        result["status"] = STATUS_DATA if "reference_matched_subset" not in failed and "tissue_span_non_vacuity" not in failed else STATUS_DESIGN
        result["reasons"] = [f"gate_failed:{k}" for k in failed]
        return result
    result["status"] = STATUS_PASS
    result["reasons"] = []
    return result


def _json_safe(obj):
    """Recursively convert sets/tuples to sorted lists so outputs are deterministic JSON."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (set, frozenset)):
        return sorted(_json_safe(v) for v in obj)
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def write_p0a_outputs(result, cfg, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {k: result[k] for k in ("schema", "status", "reasons", "gates", "counts", "allocation")}
    payload["config_sha256"] = sha256_json(cfg)
    payload["notes"] = {
        "P0a-metadata PASS is NOT relations_check PASS and NOT Stage 1 / effect evidence.",
        "the only source of truth for the coverage gate is the actual s_milp_optimum (counts.s_milp_optimum), not the v3 114/112 reference values",
        "reference 84 contains 18 Pancreas cells (A9+B9) that are not used by the per-tissue Breast/Colon main family",
        "real_data_read: false for this metadata-only step; loader only reads the 6 metadata columns (no endpoint)",
    }
    path = outdir / cfg["p0a_metadata"]["output"]
    path.write_bytes(json.dumps(_json_safe(payload), indent=1, sort_keys=True,
                                ensure_ascii=False).encode("utf8"))
    (outdir / (path.name + ".sha256")).write_text(sha256_file(path) + "\n", encoding="utf8")
    return {path.name: sha256_file(path)}


def load_metadata_inputs(config):
    """Metadata-only loader for real P0a: matched_conditions + Original metadata columns (NO endpoint).

    Returns (cell_tissue, matched_cells, conds) or raises RuntimeError with reasons.
    """
    import pandas as pd
    data = config["data"]
    matched_path = BASE / data["matched_conditions_csv"]
    if data.get("require_sha_match") and sha256_file(matched_path) != data["matched_conditions_sha256_expected"].upper():
        raise RuntimeError("matched_conditions_sha256_mismatch")
    mdf = pd.read_csv(matched_path)
    # matched_conditions.csv (A0 deliverable) uses lower-case metadata columns; they are NOT the
    # fitted-table column names, so map them explicitly here (metadata-only fields).
    matched_alias = ["cell", "anchor_id", "anchor_conc", "library_conc", "library_id"]
    missing = [c for c in matched_alias if c not in mdf.columns]
    if missing:
        raise RuntimeError(f"matched_conditions_missing_columns:{missing}")
    matched_conds = defaultdict(set)
    for r in mdf[matched_alias].to_dict("records"):
        cell = normalize_cell(r["cell"])
        if not cell:
            continue
        matched_conds[cell].add((str(r["anchor_id"]).strip(), canon_conc(r["anchor_conc"]),
                                 canon_conc(r["library_conc"]), str(r["library_id"]).strip()))
    matched_cells = {normalize_cell(r["cell"]) for r in mdf[matched_alias].to_dict("records")}
    matched_cells = {c for c in matched_cells if c}
    matched_conds = dict(matched_conds)
    orig_path = BASE / data["original_fitted_csv"]
    if data.get("require_sha_match"):
        if orig_path.stat().st_size != int(data["original_fitted_bytes_expected"]):
            raise RuntimeError("original_fitted_size_mismatch")
        if sha256_file(orig_path) != data["original_fitted_sha256_expected"].upper():
            raise RuntimeError("original_fitted_sha256_mismatch")
    odf = pd.read_csv(orig_path, usecols=[data["cell_column"], data["tissue_column"],
                                          data["anchor_id_column"], data["anchor_conc_column"],
                                          data["library_conc_column"], data["library_id_column"]],
                      low_memory=False)
    # pandas returns usecols in FILE order; reorder explicitly before positional access
    odf = odf[[data["cell_column"], data["tissue_column"], data["anchor_id_column"],
               data["anchor_conc_column"], data["library_conc_column"], data["library_id_column"]]]
    cell_tissue = {}
    all_conds = defaultdict(set)
    for r in odf.itertuples(index=False, name=None):
        cell = normalize_cell(r[0]); tissue = str(r[1]).strip()
        if not cell or not tissue:
            continue
        cell_tissue.setdefault(cell, tissue)
        all_conds[cell].add((str(r[2]).strip(), canon_conc(r[3]), canon_conc(r[4]), str(r[5]).strip()))
    conds = dict(all_conds)
    matched_cells = {c for c in matched_cells if c in cell_tissue}
    return {"cell_tissue": cell_tissue, "matched_cells": matched_cells,
            "conds": conds, "matched_conds": matched_conds}



# ------------------------------------------------------------------ real-data loading (gated)
def load_original_cell_metadata(config):
    """Metadata-only pass: read CELL_LINE_NAME + Tissue from the Original fitted table (no response)."""
    import pandas as pd  # local import: only needed for the gated real path
    data = config["data"]
    path = BASE / data["original_fitted_csv"]
    if data.get("require_sha_match"):
        if not path.exists():
            return None, [f"missing_input:{data['original_fitted_csv']}"]
        if path.stat().st_size != int(data["original_fitted_bytes_expected"]):
            return None, ["input_size_mismatch"]
        if sha256_file(path) != data["original_fitted_sha256_expected"].upper():
            return None, ["input_sha256_mismatch"]
    df = pd.read_csv(path, usecols=[data["cell_column"], data["tissue_column"]], low_memory=False)
    cell_tissue = {}
    for cell, tissue in zip(df[data["cell_column"]], df[data["tissue_column"]]):
        if isinstance(cell, str) and isinstance(tissue, str):
            cell_tissue[normalize_cell(cell)] = tissue.strip()
    return cell_tissue, []


def stream_reference_observations(config, ref_cells):
    """Stream the fitted table and keep rows ONLY for reference cells; parse response only for them.

    This keeps S/U-cell responses out of memory: for non-reference cells the endpoint text is never
    converted to a number and the row is skipped.
    """
    data = config["data"]
    path = BASE / data["original_fitted_csv"]
    ref = set(ref_cells)
    cell_idx = tissue_idx = anchor_idx = library_idx = 0
    ac_idx = lc_idx = ep_idx = 0
    rows = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        idx = {name: i for i, name in enumerate(header)}
        cell_idx = idx[data["cell_column"]]
        tissue_idx = idx[data["tissue_column"]]
        anchor_idx = idx[data["anchor_id_column"]]
        library_idx = idx[data["library_id_column"]]
        ac_idx = idx[data["anchor_conc_column"]]
        lc_idx = idx[data["library_conc_column"]]
        ep_idx = idx[data["endpoint"]]
        for raw in reader:
            if len(raw) <= ep_idx:
                continue
            cell = normalize_cell(raw[cell_idx]) if cell_idx < len(raw) and isinstance(raw[cell_idx], str) else None
            if cell not in ref:
                continue  # do not parse endpoint for non-reference (S/U) cells
            try:
                y = float(raw[ep_idx])
            except (TypeError, ValueError):
                continue
            aid = str(raw[anchor_idx]).strip()
            lid = str(raw[library_idx]).strip()
            ac = raw[ac_idx].strip()
            lc = raw[lc_idx].strip()
            if "|" in aid or "|" in lid or "|" in ac:
                continue
            if not (aid and lid and ac and lc):
                continue
            rows.append({"cell": cell, "tissue": raw[tissue_idx].strip(),
                         "anchor": aid, "library": lid, "ac": ac, "lc": lc, "y": y})
    return rows


# ------------------------------------------------------------------ observations / candidates
def build_condition_table(rows, cfg):
    """Aggregate duplicate rows (same cell, anchor, ac, lc, library) by median; build lookup maps.

    ac/lc are canonicalized with canon_conc so that the table keys match the P0a-metadata candidate
    universe (matched_conditions canonical form). This keeps the relation stage restricted to the
    frozen P0a grid instead of re-enumerating all fitted-table condition unions.
    """
    grouped = defaultdict(list)
    cell_tissue = {}
    for r in rows:
        cell_tissue.setdefault(r["cell"], r["tissue"])
        grouped[(r["cell"], str(r["anchor"]).strip(), canon_conc(r["ac"]),
                 canon_conc(r["lc"]), str(r["library"]).strip())].append(r["y"])
    agg = cfg["data"].get("aggregate_duplicate_rows", "median")
    table = {}
    for key, vals in grouped.items():
        if agg == "median":
            table[key] = statistics.median(vals)
        elif agg == "mean":
            table[key] = statistics.fmean(vals)
        else:
            raise ValueError(f"unknown aggregate_duplicate_rows: {agg}")
    return table, cell_tissue


def enumerate_candidates(table, cell_tissue, splits, cfg, candidate_keys=None):
    """Enumerate same-anchor / same-two-concentrations / same-direction controlled library contrasts.

    candidate_keys (optional): when provided (full real run), restrict to the frozen P0a-metadata
    candidate grid keys (tissue, anchor, ac, lc, l1, l2). Without it (synthetic tests) the enumeration
    is the per-tissue library-pair grid of the supplied table.
    """
    enum = cfg["candidate_enumeration"]
    min_a = int(enum["min_cells_half_A"])
    min_b = int(enum["min_cells_half_B"])
    context_mode = enum.get("context_mode", "per_tissue")
    main_tissues = [str(t) for t in enum.get("main_family_tissues", [])]
    allowed = set(candidate_keys) if candidate_keys is not None else None
    A = set(splits["A"])
    B = set(splits["B"])
    groups = defaultdict(lambda: defaultdict(set))   # group_label -> (anchor,ac,lc) -> libraries
    for (cell, anchor, ac, lc, library) in table:
        tissue = cell_tissue.get(cell)
        if tissue is None:
            continue
        if context_mode == "per_tissue" and main_tissues and str(tissue) not in main_tissues:
            continue
        group_label = "ALL" if context_mode == "pooled_across_tissue" else str(tissue)
        groups[group_label][(anchor, ac, lc)].add(library)
    candidates = []
    for group_label in sorted(groups):
        # sorted(): set iteration order of strings depends on PYTHONHASHSEED; sorting keeps outputs
        # byte-identical across processes (bootstrap resampling maps indices to a fixed cell order).
        group_cells = sorted(c for c in (A | B) if (context_mode == "pooled_across_tissue"
                                                    or str(cell_tissue.get(c)) == group_label))
        for (anchor, ac, lc) in sorted(groups[group_label]):
            libs = sorted(groups[group_label][(anchor, ac, lc)])
            if len(libs) < int(enum["min_libraries_per_group"]):
                continue
            for i in range(len(libs)):
                for j in range(i + 1, len(libs)):
                    l1, l2 = libs[i], libs[j]
                    if allowed is not None and (group_label, anchor, ac, lc, l1, l2) not in allowed:
                        continue
                    dA, dB = {}, {}
                    for cell in group_cells:
                        v1 = table.get((cell, anchor, ac, lc, l1))
                        v2 = table.get((cell, anchor, ac, lc, l2))
                        if v1 is None or v2 is None:
                            continue
                        if cell in A:
                            dA[cell] = v1 - v2
                        elif cell in B:
                            dB[cell] = v1 - v2
                    if len(dA) < min_a or len(dB) < min_b:
                        continue
                    candidates.append({
                        "cell_group": group_label, "anchor": anchor, "ac": ac, "lc": lc,
                        "library_1": l1, "library_2": l2, "dA": dA, "dB": dB,
                    })
    return candidates


# ------------------------------------------------------------------ statistics
def bootstrap_sign_stability(values, sign_ref, n_boot, rng):
    vals = list(values)
    n = len(vals)
    if n == 0:
        return 0.0
    agree = 0
    for _ in range(n_boot):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        m = statistics.fmean(sample)
        if (m > 0 and sign_ref > 0) or (m < 0 and sign_ref < 0) or (m == 0 and sign_ref == 0):
            agree += 1
    return agree / n_boot


def bootstrap_interval(values, n_boot, rng):
    vals = list(values)
    n = len(vals)
    means = []
    for _ in range(n_boot):
        means.append(statistics.fmean([vals[rng.randrange(n)] for _ in range(n)]))
    means.sort()
    lo = means[int(round(0.025 * (len(means) - 1)))]
    hi = means[int(round(0.975 * (len(means) - 1)))]
    return lo, hi


def exact_one_sided_sign_p(k, n):
    if n <= 0:
        return 1.0
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return min(1.0, p)


def bh_significant(pvals, q):
    """Benjamini-Hochberg: return set of indices passing q."""
    m = len(pvals)
    if m == 0:
        return set()
    order = sorted(range(m), key=lambda i: (pvals[i], i))
    passed = set()
    threshold_rank = 0
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= q * rank / m:
            threshold_rank = rank
    if threshold_rank == 0:
        return set()
    cutoff_p = pvals[order[threshold_rank - 1]]
    for i in range(m):
        if pvals[i] <= cutoff_p:
            passed.add(i)
    return passed


def relation_id(c):
    key = "|".join([c["cell_group"], c["anchor"], c["ac"], c["lc"], c["library_1"], c["library_2"]])
    return "r_" + sha256_bytes(key.encode("utf8"))[:16].lower()


def evaluate_candidates(candidates, cfg):
    stats = cfg["statistics"]
    rng_boot = random.Random(int(stats["bootstrap_seed"]))
    n_boot_stab = int(stats["stability_bootstrap"])
    n_boot_int = int(stats["interval_bootstrap"])
    results = []
    for c in candidates:
        dA_vals = list(c["dA"].values())
        dB_vals = list(c["dB"].values())
        muA = statistics.fmean(dA_vals)
        muB = statistics.fmean(dB_vals)
        signA = 1 if muA > 0 else (-1 if muA < 0 else 0)
        signB = 1 if muB > 0 else (-1 if muB < 0 else 0)
        stability_A = bootstrap_sign_stability(dA_vals, signA, n_boot_stab, rng_boot)
        nz_B = [(v, (1 if v > 0 else -1)) for v in dB_vals if v != 0]
        n_B = len(nz_B)
        k_B = sum(1 for v, s in nz_B if s == signA)
        agree_B = (k_B / n_B) if n_B else 0.0
        p_B = exact_one_sided_sign_p(k_B, n_B)
        # swap: select direction on B, validate on A
        nz_A = [(v, (1 if v > 0 else -1)) for v in dA_vals if v != 0]
        n_A = len(nz_A)
        k_A = sum(1 for v, s in nz_A if s == signB)
        agree_A = (k_A / n_A) if n_A else 0.0
        swap_pass = (signA == signB and signA != 0 and agree_A >= float(stats["direction_agreement_min"]))
        lo, hi = bootstrap_interval(dB_vals, n_boot_int, rng_boot)
        sigma_B = statistics.stdev(dB_vals) if len(dB_vals) > 1 else 0.0
        results.append({
            "candidate": c, "relation_id": relation_id(c),
            "mu_A": muA, "mu_B": muB, "sign_A": signA, "sign_B": signB,
            "stability_A": stability_A, "direction_agreement_B": agree_B,
            "direction_agreement_A": agree_A, "sign_test_p_B": p_B,
            "n_A": len(dA_vals), "n_B": len(dB_vals), "swap_pass": swap_pass,
            "interval_lo": lo, "interval_hi": hi, "interval_width": hi - lo,
            "sigma_B": sigma_B,
            "mu_over_sigma": (abs(muB) / sigma_B) if sigma_B > 0 else 0.0,
        })
    # Two multiplicity layers (frozen protocol):
    #  - per-relation exact sign test alpha=0.01 (alpha_pass);
    #  - the old strict full-family BH over all tested relations is kept as a SENSITIVITY only;
    #    the decision layer applies BH q<=0.10 within the primary family (<=10) after ranking.
    pvals = [r["sign_test_p_B"] for r in results]
    passed_full = bh_significant(pvals, float(stats["bh_q"]))
    alpha = float(stats["alpha_per_relation"])
    for i, r in enumerate(results):
        r["bh_pass_full_family_sensitivity"] = i in passed_full
        r["alpha_pass"] = r["sign_test_p_B"] <= alpha
    return results


def accept_relations(results, cfg):
    stats = cfg["statistics"]
    utility_range = cfg["utility"]["utility_range"]
    utility_check_enabled = bool(stats.get("interval_utility_check_enabled", True))
    w_sigma = float(stats["interval_sigma_mult"])
    w_util = float(stats["interval_utility_frac"])
    accepted, rejected = [], defaultdict(int)
    for r in results:
        fail = []
        if not r.get("alpha_pass", False):
            fail.append("alpha_not_significant")
        if r["direction_agreement_B"] < float(stats["direction_agreement_min"]):
            fail.append("direction_agreement_B_low")
        if not r["swap_pass"]:
            fail.append("swap_check_failed")
        if r["n_A"] < int(stats["n_ctx_min"]) or r["n_B"] < int(stats["n_ctx_min"]):
            fail.append("n_ctx_low")
        width_limit = w_sigma * r["sigma_B"]
        if utility_check_enabled and utility_range is not None:
            width_limit = min(width_limit, w_util * float(utility_range))
        if r["interval_width"] > width_limit:
            fail.append("interval_too_wide")
        if r["mu_over_sigma"] < float(stats["mu_min_sigma_mult"]):
            fail.append("mu_too_close_to_zero")
        if fail:
            rejected[fail[0]] += 1
            r["reject_reasons"] = fail
        else:
            accepted.append(r)
    # rank accepted for the primary family: stable > |mu|/sigma > smaller p > id
    accepted.sort(key=lambda r: (-r["stability_A"], -r["mu_over_sigma"], r["sign_test_p_B"], r["relation_id"]))
    n_primary = min(int(stats["primary_family_max"]), len(accepted))
    primary = accepted[:n_primary]
    bh_primary = bh_significant([r["sign_test_p_B"] for r in primary], float(stats["bh_q"])) if primary else set()
    for idx_rank, r in enumerate(accepted):
        r["primary_bh_pass"] = (idx_rank < n_primary and idx_rank in bh_primary)
        if idx_rank < n_primary and r["primary_bh_pass"]:
            r["family"] = "primary"
        else:
            r["family"] = "exploratory"
    return accepted, dict(rejected)


# ------------------------------------------------------------------ main pipeline
def run_relations_check(observations_table, cell_tissue, cfg, synthetic=False, elapsed=None, splits_override=None,
                        candidate_keys=None):
    """Pure pipeline on an already-loaded condition table + cell metadata.

    observations_table: {(cell, anchor, ac, lc, library): y}; cell_tissue: {cell: tissue}
    splits_override: optional dict with A/B/S/U cell lists (e.g. from P0a-metadata); when given the
    pipeline does not re-allocate cells.
    Returns result dict with status/reasons/relations/gates/splits/hashes (no timestamps).
    """
    result = {"schema": "r198-a1-stage0-relations-check-result-v1", "synthetic": bool(synthetic),
              "status": None, "reasons": [], "relations": [], "gates": {}, "counts": {},
              "config_sha256": None}
    # utility gate: Stage 0 acceptance needs a frozen utility range only when the utility branch is enabled.
    # (Lead 2026-10-27 A1v3 decision: P0a uses only the 2.0*sigma_r width branch; utility moves to P0d.
    #  Until A1v3 is frozen the committed config keeps utility_gate_required_for_run=true, so a real run
    #  is refused with blocked_by_utility_definition; the v3 change is config-only.)
    utility_cfg = cfg["utility"]
    utility_check_enabled = bool(cfg["statistics"].get("interval_utility_check_enabled", True))
    utility_gate_required = bool(utility_cfg.get("utility_gate_required_for_run", True))
    if utility_gate_required and (utility_cfg.get("utility_range") is None
                                  or utility_cfg.get("delta_min_state") == "blocked_by_utility_definition"):
        result["status"] = STATUS_BLOCKED
        result["reasons"] = ["blocked_by_utility_definition: utility_range/delta_min not frozen"]
        return result
    if splits_override is not None:
        A_cells = sorted(splits_override["A"])
        B_cells = sorted(splits_override["B"])
        S_cells = sorted(splits_override.get("S", []))
        U_cells = sorted(splits_override.get("U", []))
        result["splits"] = {k: {"n": len(v), "sha256": sha256_cell_list(v),
                                "tissues": {t: sum(1 for c in v if cell_tissue.get(c) == t)
                                            for t in sorted(set(cell_tissue.values()))}}
                            for k, v in (("A", A_cells), ("B", B_cells), ("S", S_cells), ("U", U_cells))}
        splits = {"A": A_cells, "B": B_cells, "S": S_cells, "U": U_cells,
                  "warnings": ["splits_override"], "seed": int(cfg["cell_allocation"]["seed"])}
    else:
        splits = allocate_cells(cell_tissue, cfg)
        result["splits"] = splits["splits"]
    result["allocation"] = {"warnings": splits.get("warnings", []), "seed": splits.get("seed"),
                            "n_A": len(splits["A"]), "n_B": len(splits["B"]),
                            "n_S": len(splits["S"]), "n_U": len(splits["U"])}
    candidates = enumerate_candidates(observations_table, cell_tissue, splits, cfg, candidate_keys=candidate_keys)
    result["counts"]["candidates_evaluable"] = len(candidates)
    if len(candidates) == 0:
        result["status"] = STATUS_DATA
        result["reasons"] = ["insufficient_contexts: no candidate relation has >= n_ctx_min cells in both A and B halves"]
        return result
    max_tested = int(cfg["candidate_enumeration"]["max_candidates_tested"])
    if len(candidates) > max_tested:
        # deterministic pre-ranking by A-side stability proxy: |mean_A| relative to sd, then id
        def proxy(c):
            vals = list(c["dA"].values())
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            mu = statistics.fmean(vals)
            return (-(abs(mu) / sd if sd > 0 else 0.0), relation_id(c))
        candidates = sorted(candidates, key=proxy)[:max_tested]
        result["counts"]["candidates_truncated_to"] = max_tested
    results = evaluate_candidates(candidates, cfg)
    accepted, rejected = accept_relations(results, cfg)
    result["counts"].update({
        "candidates_tested": len(results),
        "alpha_pass_relations": sum(1 for r in results if r.get("alpha_pass")),
        "strict_full_family_bh_pass_sensitivity": sum(1 for r in results if r.get("bh_pass_full_family_sensitivity")),
        "accepted_relations": len(accepted),
        "rejected_reasons": rejected,
        "primary_relations": sum(1 for r in accepted if r.get("family") == "primary"),
        "exploratory_relations": sum(1 for r in accepted if r.get("family") == "exploratory"),
        "primary_bh_pass_relations": sum(1 for r in accepted if r.get("primary_bh_pass")),
    })
    universe = len(candidates)
    glob = cfg["global_acceptance"]
    coverage_denominator_cfg = glob.get("coverage_denominator")
    coverage = ((len(accepted) / float(coverage_denominator_cfg)) if coverage_denominator_cfg
                else (len(accepted) / universe if universe else 0.0))
    by_group = defaultdict(int)
    for r in accepted:
        by_group[r["candidate"]["cell_group"]] += 1
    coverage_min_val = float(glob.get("coverage_min", cfg.get("coverage", {}).get("coverage_min", 0.5)))
    context_mode = cfg["candidate_enumeration"].get("context_mode", "per_tissue")
    coverage_denominator = glob.get("coverage_denominator")
    coverage_min_abs = glob.get("coverage_min_abs")
    if coverage_min_abs is not None:
        coverage_target_count = int(coverage_min_abs)
        coverage_ok = len(accepted) >= coverage_target_count
    elif coverage_denominator:
        coverage_target_count = int(math.ceil(coverage_min_val * float(coverage_denominator)))
        coverage_ok = len(accepted) >= coverage_target_count
    else:
        coverage_target_count = None
        coverage_ok = coverage >= coverage_min_val
    gates = {
        "R_within_min_max": int(glob["R_min"]) <= len(accepted) <= int(glob["R_max"]),
        "coverage_ok": coverage_ok,
        "context_mode": context_mode,
        "primary_family_ok": sum(1 for r in accepted if r.get("family") == "primary") <= int(glob["primary_family_max"]),
    }
    result["gates"] = {"gates": gates, "coverage": round_sig(coverage),
                       "coverage_target_count": coverage_target_count,
                       "accepted_by_group": dict(sorted(by_group.items())),
                       "R_min": int(glob["R_min"]), "R_max": int(glob["R_max"]),
                       "coverage_min": coverage_min_val,
                       "coverage_denominator": coverage_denominator,
                       "utility_branch": ("enabled" if utility_check_enabled else "deferred_to_P0d")}
    reasons = []
    if len(accepted) < int(glob["R_min"]):
        reasons.append("R_below_min")
    if len(accepted) > int(glob["R_max"]):
        reasons.append("R_above_max")
    if not gates["coverage_ok"]:
        reasons.append("coverage_below_min")
    if not any(r.get("alpha_pass") for r in results):
        reasons.append("alpha_none_significant")
    if reasons:
        # R above max is a design/config bound violation; others are data-availability limits
        result["status"] = STATUS_DESIGN if "R_above_max" in reasons else STATUS_DATA
        result["reasons"] = reasons
        result["relations"] = accepted
        return result
    if elapsed is not None and elapsed > float(cfg["budget"]["max_seconds"]):
        result["status"] = STATUS_DESIGN
        result["reasons"] = ["budget_exceeded"]
        result["relations"] = accepted
        return result
    result["status"] = STATUS_PASS
    result["reasons"] = []
    result["relations"] = accepted
    return result


# ------------------------------------------------------------------ outputs
def relations_to_rows(relations):
    rows = []
    for r in relations:
        c = r["candidate"]
        rows.append({
            "relation_id": r["relation_id"], "family": r.get("family", ""),
            "cell_group": c["cell_group"], "anchor_id": c["anchor"], "anchor_conc": c["ac"],
            "library_conc": c["lc"], "library1_id": c["library_1"], "library2_id": c["library_2"],
            "direction": "anchor_to_library", "endpoint": "SYNERGY_DELTA_EMAX",
            "mu_A": round_sig(r["mu_A"]), "mu_B": round_sig(r["mu_B"]), "sign": r["sign_B"],
            "l_B": round_sig(r["interval_lo"]), "u_B": round_sig(r["interval_hi"]),
            "w_B": round_sig(r["interval_width"]), "sigma_r": round_sig(r["sigma_B"]),
            "n_ctx_A": r["n_A"], "n_ctx_B": r["n_B"],
            "stability_A": round_sig(r["stability_A"]), "direction_agreement_B": round_sig(r["direction_agreement_B"]),
            "direction_agreement_A": round_sig(r["direction_agreement_A"]),
            "sign_test_p_B": round_sig(r["sign_test_p_B"], 8), "swap_pass": int(bool(r["swap_pass"])),
        })
    rows.sort(key=lambda x: (x["family"] != "primary", x["cell_group"], x["anchor_id"], x["anchor_conc"],
                             x["library_conc"], x["library1_id"], x["library2_id"]))
    return rows


def write_outputs(result, cfg, outdir, input_shas=None):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    names = cfg["outputs"]
    rel_rows = relations_to_rows(result.get("relations", []))
    rel_path = outdir / names["relations_csv"]
    with rel_path.open("w", encoding="utf8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rel_rows[0].keys()) if rel_rows else
                                ["relation_id", "family", "cell_group", "anchor_id", "anchor_conc",
                                 "library_conc", "library1_id", "library2_id", "direction", "endpoint",
                                 "mu_A", "mu_B", "sign", "l_B", "u_B", "w_B", "sigma_r", "n_ctx_A",
                                 "n_ctx_B", "stability_A", "direction_agreement_B",
                                 "direction_agreement_A", "sign_test_p_B", "swap_pass"])
        writer.writeheader()
        writer.writerows(rel_rows)
    splits_path = outdir / names["relation_splits_json"]
    splits_payload = {"schema": "r198-a1-stage0-relation-splits-v1",
                      "seed": result.get("allocation", {}).get("seed"),
                      "splits": result.get("splits", {}),
                      "allocation": result.get("allocation", {}),
                      "note": "cell names omitted unless config.cell_allocation.record_cell_names=true; sha256 covers sorted normalized cell names"}
    splits_bytes = json.dumps(splits_payload, indent=1, sort_keys=True, ensure_ascii=False).encode("utf8")
    splits_path.write_bytes(splits_bytes)
    check = {
        "schema": "r198-a1-stage0-relations-check-v1",
        "synthetic": bool(result.get("synthetic", False)),
        "status": result["status"],
        "reasons": result["reasons"],
        "counts": result.get("counts", {}),
        "gates": result.get("gates", {}),
        "allocation": result.get("allocation", {}),
        "config_sha256": sha256_json(cfg),
        "input_sha256": input_shas or {},
        "outputs": {
            names["relations_csv"]: sha256_file(rel_path),
            names["relation_splits_json"]: sha256_bytes(splits_bytes),
        },
        "notes": [
            "no timestamps in outputs (deterministic)",
            "relations_check.json itself is not listed in its own hash set (self-reference)",
        ],
    }
    check_bytes = json.dumps(check, indent=1, sort_keys=True, ensure_ascii=False).encode("utf8")
    check_path = outdir / names["relations_check_json"]
    check_path.write_bytes(check_bytes)
    if cfg["outputs"].get("write_sha256_sidecar", False):
        for p in (rel_path, splits_path, check_path):
            (outdir / (p.name + ".sha256")).write_text(sha256_file(p) + "\n", encoding="utf8")
    return {"relations_csv": sha256_file(rel_path), "relation_splits_json": sha256_bytes(splits_bytes),
            "relations_check_json": sha256_bytes(check_bytes)}


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="R198-A1 Stage 0 relations_check (gated; implementation only)")
    ap.add_argument("--confirm-run", action="store_true",
                    help="required to read real data; default refuses (real run also needs run_gate.real_run_enabled=true)")
    ap.add_argument("--p0a-metadata", action="store_true",
                    help="run only the metadata-only P0a precheck (allocation/candidate grid/S-side coverage/non-vacuity); no response read")
    ap.add_argument("--config", default=str(CONFIG_PATH))
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    status, reason = check_run_gate(cfg, args.confirm_run,
                                    mode="p0a_metadata" if args.p0a_metadata else "relations_check")
    if status is not None:
        print(json.dumps({"status": status, "reason": reason, "real_data_read": False,
                          "mode": "p0a_metadata" if args.p0a_metadata else "relations_check"},
                         indent=1, sort_keys=True))
        return 3 if status == STATUS_REFUSED else 4
    t0 = __import__("time").time()
    if args.p0a_metadata:
        print(json.dumps({"status": "starting", "mode": "p0a_metadata",
                          "note": "metadata-only P0a (no response column is read)"}, indent=1, sort_keys=True))
        try:
            meta = load_metadata_inputs(cfg)
        except Exception as exc:  # noqa: BLE001 - report as data/design failure
            print(json.dumps({"status": STATUS_DATA, "reasons": [f"metadata_load_error:{exc}"]}, indent=1, sort_keys=True))
            return 1
        result = run_p0a_metadata(meta["cell_tissue"], meta["matched_cells"], meta["conds"], cfg,
                                  matched_conds=meta["matched_conds"])
        elapsed = __import__("time").time() - t0
        if elapsed > float(cfg["p0a_metadata"]["budget_max_seconds"]):
            result["status"] = STATUS_DESIGN
            result["reasons"] = list(result["reasons"]) + ["budget_exceeded"]
        outdir = args.outdir or (BASE / cfg["outputs"]["output_dir"])
        hashes = write_p0a_outputs(result, cfg, outdir)
        print(json.dumps({"mode": "p0a_metadata", "status": result["status"], "reasons": result["reasons"],
                          "counts": result["counts"], "gates": result["gates"], "outputs": hashes,
                          "elapsed_s": round(elapsed, 1)}, indent=1, sort_keys=True))
        return 0 if result["status"] == STATUS_PASS else 1
    print(json.dumps({"status": "starting", "note": "real Stage 0 run permitted by gate; loading metadata only"},
                     indent=1, sort_keys=True))
    # v4: P0a-metadata must run first and provide the frozen allocation
    try:
        meta = load_metadata_inputs(cfg)
        cell_tissue = meta["cell_tissue"]
        matched_cells = meta["matched_cells"]
        conds = meta["conds"]
        p0a = run_p0a_metadata(cell_tissue, matched_cells, conds, cfg,
                               matched_conds=meta["matched_conds"])
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": STATUS_DATA, "reasons": [f"p0a_metadata_error:{exc}"]}, indent=1, sort_keys=True))
        return 1
    if p0a["status"] != STATUS_PASS:
        print(json.dumps({"status": p0a["status"], "reasons": ["p0a_metadata_failed"] + p0a["reasons"],
                          "counts": p0a.get("counts", {})}, indent=1, sort_keys=True))
        return 1
    splits = {k: p0a["allocation"]["splits"][k].get("cells") for k in ("A", "B", "S", "U")}
    if any(v is None for v in splits.values()):
        # split SHA-only outputs omit raw names; rebuild the deterministic pieces from the P0a result
        ref = allocate_reference_v4(cell_tissue, matched_cells, cfg)
        S_cells = list(p0a.get("_s_cells", []))
        U_cells = sorted(set(ref["leftover"]) - set(S_cells))
        splits = {"A": ref["A"], "B": ref["B"], "S": S_cells, "U": U_cells}
    rows = stream_reference_observations(cfg, splits["A"] + splits["B"])
    table, cell_tissue2 = build_condition_table(rows, cfg)
    elapsed = __import__("time").time() - t0
    result = run_relations_check(table, cell_tissue2, cfg, synthetic=False, elapsed=elapsed,
                                 splits_override=splits, candidate_keys=p0a.get("_candidate_keys"))
    outdir = args.outdir or (BASE / cfg["outputs"]["output_dir"])
    input_shas = {}
    if cfg["data"].get("require_sha_match"):
        input_shas[cfg["data"]["original_fitted_csv"]] = cfg["data"]["original_fitted_sha256_expected"].upper()
    hashes = write_outputs(result, cfg, outdir, input_shas=input_shas) if result["status"] != STATUS_BLOCKED else {}
    print(json.dumps({"status": result["status"], "reasons": result["reasons"], "counts": result.get("counts", {}),
                      "gates": result.get("gates", {}), "outputs": hashes}, indent=1, sort_keys=True))
    return 0 if result["status"] == STATUS_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
