"""Trace of every path by which development QUERY outcomes enter the program-revision loop (real data).

File summary
- Path: research/seed_attribution_20261017/audit_access.py
- Purpose: Part 2 of the brief. Which fits, residuals, normalisations, thresholds, proposals and
  selections of the frozen development `revise.Bench` use the outcomes of the development query lines
  that the distinguishing experiment later "buys", and what changes when they are masked.
- Method (no frozen file is edited):
  1. Structural trace: for each fold of the frozen `Bench`, how many of its TRAINING lines are query
     lines of some project, and of the fold's own project. The same count for `replay.MaskedBench`.
  2. Perturbation trace: replace ONE project's query-line outcomes (drug-axis permutation of the
     non-probe drugs, per line, X1-X3 together) and rebuild every quantity from fresh caches. A quantity
     "depends on" the reserved outcomes iff it changes. Run on the frozen bench and on the masked bench
     (which must not change at all).
  3. Consequence: seed-library nominations and hits on the query lines, and the residual-association
     clusters that the proposer sees, with reserved outcomes visible (frozen) versus masked.
  4. Stale cache: the frozen fit cache is keyed by training lines, not by data. Changing labels in the
     same domain object returns the old fit; shown on one fold.
- Information conditions: I1 (no probes) and I2 (8 fixed probes; their readouts on the target lines are
  paid wells and stay visible in the masked domain).
- Output: AUDIT_ACCESS.json (write-once). Run: python audit_access.py
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corrected as C  # noqa: E402
import replay  # noqa: E402
import contract  # noqa: E402  (frozen modules are on sys.path through corrected)
import engine  # noqa: E402
import revise  # noqa: E402

OUT = HERE / "AUDIT_ACCESS.json"
N_PROBES = 8


def perturb(dom, project, protect_rows, seed=0):
    """A copy of ``dom`` in which one project's query-line outcomes are scrambled (frozen derivation)."""

    L = dom.lines
    q = np.flatnonzero((L.project.to_numpy() == project) & (L.role.to_numpy() == "query") & dom.src_line)
    rows = np.setdiff1d(np.flatnonzero(dom.src_drug), np.asarray(protect_rows, int))
    rng = np.random.default_rng(seed)
    out = copy.copy(dom)
    out.X1, out.X2, out.X3 = dom.X1.copy(), dom.X2.copy(), dom.X3.copy()
    for c in q:
        perm = rng.permutation(rows)
        for X, X0 in ((out.X1, dom.X1), (out.X2, dom.X2), (out.X3, dom.X3)):
            X[rows, c] = X0[perm, c]
    return replay.rederive(out), q


def train_overlap(bench):
    """Per fold: training lines that are query lines of any project / of the fold's own project."""

    L = bench.dom.lines
    proj, role = L.project.to_numpy(), L.role.to_numpy()
    is_query = (role == "query") & bench.dom.src_line
    rows = []
    for kind, folds in (("query", bench.query), ("support", bench.support)):
        for p in bench.projects:
            tr = folds[p].train
            rows.append({"fold": kind, "project": p, "n_train": int(len(tr)),
                         "train_query_lines_any_project": int(is_query[tr].sum()),
                         "train_query_lines_own_project": int((is_query[tr] & (proj[tr] == p)).sum()),
                         "n_target": int(len(folds[p].target))})
    return rows


def nomination_change(nom_a, nom_b):
    """Share of nominated (drug, line) pairs that differ between two nomination matrices."""

    diff = tot = 0
    for j in range(nom_a.shape[1]):
        a, b = set(nom_a[:, j].tolist()), set(nom_b[:, j].tolist())
        diff += len(a ^ b) // 2
        tot += len(a)
    return diff / max(tot, 1)


def compare(a: dict, b: dict, projects):
    """Which quantities changed between two snapshots, and by how much."""

    out = {"base_mean_changed": {}, "R_train_changed": {}, "oos_var_changed": {}, "nominations_changed": {},
           "commit_digest_equal": a["digest"] == b["digest"], "proposals_equal": a["proposals"] == b["proposals"],
           "diagnosis_equal": a["diagnosis"] == b["diagnosis"]}
    for p in projects:
        for kind in ("query", "support"):
            for name, tag in (("base_mean", "base_mean_changed"), ("R_train", "R_train_changed"), ("oos_var", "oos_var_changed")):
                x, y = a[f"{kind}|{p}|{name}"], b[f"{kind}|{p}|{name}"]
                same = np.array_equal(x, y, equal_nan=True)
                out[tag][f"{kind}|{p}"] = 0.0 if same else float(np.nanmax(np.abs(x - y))) if x.shape == y.shape else None
        out["nominations_changed"][p] = round(nomination_change(a[f"commit|{p}|nom"], b[f"commit|{p}|nom"]), 4)
    return out


def snapshot_light(bench, lib, projects):
    """Folds' arrays and commits plus the diagnosis/proposals text (the quantities `replay.snapshot` records)."""

    return replay.snapshot(bench, lib, projects[0])


def top_clusters(bench, lib, project, k=10):
    diag = revise.diagnose(bench, lib, project)
    return [(c["scope"], c["state"]) for c in diag["clusters"][:k]]


def overlap(a, b):
    return len(set(a) & set(b)) / max(len(a), 1)


def query_hits(bench, lib, truth):
    """Nominated hits per query line (truth domain), for the library's committed nominations."""

    commit, _ = bench.commit(lib)
    out = {}
    for p in bench.projects:
        f = bench.query[p]
        nom = commit[p][0]
        h, u = engine.score_nominations(truth, nom, f.drows, f.target)
        out[p] = {"lines": int(len(f.target)), "hits": int(h.sum()), "unknown": int(u.sum())}
    return out, commit


def main():
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; the audit is write-once")
    t0 = time.time()
    truth = C.CorrectedDomain()
    L = truth.lines
    src = np.flatnonzero(truth.src_line)
    proj, role = L.project.to_numpy(), L.role.to_numpy()
    projects = sorted(set(proj[src]))
    reserved = replay.reserved_lines(truth)
    result = {"lines": {"source": int(len(src)), "reserved_query": int(len(reserved)),
                        "historical": int(len(src) - len(reserved)),
                        "per_project": {p: {"query": int(((proj == p) & (role == "query") & truth.src_line).sum()),
                                            "support": int(((proj == p) & (role == "support") & truth.src_line).sum())}
                                        for p in projects}},
              "conditions": {}}
    print("projects", projects, result["lines"]["source"], "reserved", len(reserved), flush=True)
    perturbed = [projects[0], projects[len(projects) // 2], projects[-1]]  # a bench build is ~1 min; three suffice
    result["perturbed_projects"] = perturbed

    design_frozen = {"I1": [], "I2": engine.fixed_probe_design(truth, N_PROBES, "I2")}
    hist = np.setdiff1d(src, reserved)
    probe_rows = np.array([truth.drug_index[c] for c in design_frozen["I2"]], int)
    vis_i1 = replay.mask_cells(truth, reserved)
    design_masked_i2 = engine.fixed_probe_design(vis_i1, N_PROBES, "I2", train_rows=hist)
    masked_rows = np.array([truth.drug_index[c] for c in design_masked_i2], int)
    # the paid probe readouts of the masked design stay visible on the reserved lines; nothing else does
    vis_all = {"I1": vis_i1, "I2": replay.mask_cells(truth, reserved, keep_x1_rows=masked_rows)}
    protect = {"I1": [], "I2": np.union1d(probe_rows, masked_rows)}
    result["probe_design"] = {"frozen_all_source_lines": design_frozen["I2"], "masked_historical_only": design_masked_i2,
                              "same_set": sorted(design_frozen["I2"]) == sorted(design_masked_i2),
                              "overlap": len(set(design_frozen["I2"]) & set(design_masked_i2))}
    print("design", result["probe_design"], round(time.time() - t0, 1), flush=True)

    for info in ("I1", "I2"):
        cond = {}
        probes = design_frozen[info]
        frozen = revise.Bench(truth, info, probes)
        lib, dropped_f = revise.seed_library(frozen)
        masked = replay.MaskedBench(vis_all[info], truth, info, probes if info == "I1" else design_masked_i2)
        libm, dropped_m = revise.seed_library(masked)
        cond["structure"] = {"frozen_bench": train_overlap(frozen), "masked_bench": train_overlap(masked)}
        cond["seed_library"] = {"frozen_kept": lib.keys(), "masked_kept": libm.keys(),
                                "frozen_dropped": dropped_f, "masked_dropped": dropped_m}
        base_f = replay.snapshot(frozen, lib, projects[0])
        base_m = replay.snapshot(masked, libm, projects[0])
        cond["perturbation"] = {}
        for p in perturbed:
            pt, q = perturb(truth, p, protect[info])
            fb = revise.Bench(pt, info, probes)
            snap_f = replay.snapshot(fb, lib, projects[0])
            ptm = replay.mask_cells(pt, reserved, keep_x1_rows=masked_rows if info == "I2" else ())
            mb = replay.MaskedBench(ptm, pt, info, probes if info == "I1" else design_masked_i2)
            snap_m = replay.snapshot(mb, libm, projects[0])
            same_design = (engine.fixed_probe_design(pt, N_PROBES, info) == design_frozen["I2"]) if info == "I2" else None
            own = frozen.query[p]
            dom_tr = copy.copy(truth)
            dom_tr.thr, dom_tr.rep_var = pt.thr, pt.rep_var
            own_tr = copy.copy(own)
            own_tr.dom = dom_tr
            _, _, sc0 = C.decide(own, lib, truth.thr[own.drows], "lib", "frozen")
            _, _, sc1 = C.decide(own_tr, lib, pt.thr[own.drows], "lib", "frozen")
            nom0 = engine.nominate(sc0, truth.tie_drug[own.drows])
            nom1 = engine.nominate(sc1, truth.tie_drug[own.drows])
            threshold_path_only = round(nomination_change(nom0, nom1), 4)
            cond["perturbation"][p] = {
                "own_fold_nominations_changed_by_threshold_and_replicate_variance_only": threshold_path_only,
                "scrambled_query_lines": int(len(q)),
                "reference_median_changed_drugs": int(np.sum(~np.isclose(pt.med[truth.src_drug], truth.med[truth.src_drug], equal_nan=True))),
                "rep_var_max_change": float(np.nanmax(np.abs(pt.rep_var - truth.rep_var))),
                "probe_design_unchanged": same_design,
                "frozen_bench": compare(base_f, snap_f, projects),
                "masked_bench": compare(base_m, snap_m, projects),
                "masked_bench_invariant": replay.differences(base_m, snap_m) == []}
            print(info, p, "masked invariant", cond["perturbation"][p]["masked_bench_invariant"],
                  "frozen nominations changed", cond["perturbation"][p]["frozen_bench"]["nominations_changed"],
                  round(time.time() - t0, 1), flush=True)
        # consequence on the quoted development quantities
        hits_f, _ = query_hits(frozen, lib, truth)
        hits_m, _ = query_hits(masked, libm, truth)
        empty_f, _ = query_hits(frozen, type(lib)(), truth)
        empty_m, _ = query_hits(masked, type(libm)(), truth)
        cond["query_hits"] = {"frozen_seed": hits_f, "masked_seed": hits_m, "frozen_empty": empty_f, "masked_empty": empty_m}
        cond["diagnosis_clusters"] = {}
        for p in projects:
            cf, cm = top_clusters(frozen, lib, p), top_clusters(masked, libm, p)
            cond["diagnosis_clusters"][p] = {"frozen_top10": cf, "masked_top10": cm, "overlap": overlap(cf, cm)}
        cond["proposals"] = {"frozen": base_f["proposals"], "masked": base_m["proposals"]}
        result["conditions"][info] = cond

    # stale cache: same domain object, labels changed, caches kept
    d1 = copy.copy(truth)
    d1.X1, d1.X2, d1.X3 = truth.X1.copy(), truth.X2.copy(), truth.X3.copy()
    d1._model_cache, d1._safe_model_cache = {}, {}
    f1 = revise.Bench(d1, "I1", [])
    before = f1.support[projects[0]].base_mean.copy()
    pt2, _ = perturb(truth, projects[0], [])
    d1.X1[:], d1.X2[:], d1.X3[:] = pt2.X1, pt2.X2, pt2.X3
    d1.Ymean = pt2.Ymean
    f2_stale = revise.Bench(d1, "I1", [])
    d1._model_cache = {}
    f2_fresh = revise.Bench(d1, "I1", [])
    result["stale_cache"] = {
        "labels_changed": True,
        "support_base_mean_equal_with_stale_cache": bool(np.array_equal(before, f2_stale.support[projects[0]].base_mean, equal_nan=True)),
        "support_base_mean_equal_with_fresh_cache": bool(np.array_equal(before, f2_fresh.support[projects[0]].base_mean, equal_nan=True))}
    result["seconds"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(result, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)) + "\n",
                   encoding="utf-8", newline="\n")
    print("written", OUT.name, result["seconds"], "s")


if __name__ == "__main__":
    main()
