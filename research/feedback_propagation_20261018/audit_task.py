"""Task qualification audit: unseen compound batch, limited budget, subsequent compound/context nominations.

File summary
- Path: research/feedback_propagation_20261018/audit_task.py
- Purpose: qualify (or refuse) the indication-triage task as a development task for the question "can observed
  feedback identify and repair a failure in how responses propagate to unmeasured pairs?". It reads only the
  exposed PRISM 19Q4 tables and the saved indication-triage outputs; no PRISM 24Q2 value exists locally.
- Sections (each writes its part of AUDIT.json):
  - `provenance`: checkout equals commit 5d713d5c; cached-table digests.
  - `chemistry`: ECFP4 separation between the MoA-family folds before and after the purge, Murcko-scaffold
    overlap, connectivity-unit and family leakage.
  - `masking`: the oracle interface hides every unqueried cell. A run is repeated with all cells that run never
    queried scrambled; trajectories, scores and lists must be identical. A deliberately leaky score function
    proves the test can fail.
  - `missingness`: cell, line and compound missingness, screen/dose composition, missingness versus activity,
    and the events that no admissible nomination can reach.
  - `granularity`: pool structure from the shipped pooling table, what the collapsed primary data lack
    (plate, well, replicate count), dose mixing, and what a logical 16-line design implies in pools.
  - `oldloop`: the saved indication-triage totals are reproduced for the loop and the conventional adaptive
    screen at w = 16 on its estimation folds, and the share of their hits that are pairs the arm itself probed
    is measured. A probed pair is a noisy copy of the pair that is graded.
- Interfaces: ``python -B audit_task.py [section ...]``; writes/merges AUDIT.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import bench
import loop as L
import rules as R
from bench import ROOT, TRIAGE, tc

HERE = Path(__file__).resolve().parent
OUT = HERE / "AUDIT.json"
TARGET_COMMIT = "5d713d5ca3194fbd131ce45835355538d10a4b66"


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()


def q(v, qs=(0.05, 0.25, 0.5, 0.75, 0.95)):
    return {str(x): float(np.quantile(v, x)) for x in qs}


# ---------------------------------------------------------------- provenance
def provenance(T) -> dict:
    head = git("rev-parse", "HEAD")
    tracked_diff = git("diff", "--name-only", TARGET_COMMIT, "HEAD").splitlines()
    status = [l for l in git("status", "--porcelain").splitlines()]
    new_only = all(l.startswith("??") or "feedback_propagation_20261018" in l or "seed_attribution_20261017" in l
                   or "STUDIES.json" in l or l.strip().endswith(("EVIDENCE.md", "REPORT.md", "DIRECTIONS.md", "RESEARCH_PROGRAM.md"))
                   for l in status)
    build = json.loads((TRIAGE / "BUILD.json").read_text(encoding="utf-8"))
    return {"head": head, "head_equals_target_commit": head == TARGET_COMMIT, "files_differing_from_target_commit": tracked_diff,
            "working_tree_entries_at_audit": status, "working_tree_changes_limited_to_this_task": new_only,
            "tables_sha256": tc.sha256(bench.CACHE / "tables.npz"), "tables_sha256_matches_BUILD": tc.sha256(bench.CACHE / "tables.npz") == build["tables_sha256"],
            "compounds": int(len(T["cores"])), "lines": int(len(T["lines"])), "python": sys.version.split()[0]}


# ---------------------------------------------------------------- chemistry
def murcko_scaffolds(cores) -> dict:
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold
    RDLogger.DisableLog("rdApp.*")
    info = pd.read_csv(tc.PRISM_TREATMENTS, usecols=["broad_id", "screen_id", "smiles"])
    info["core"] = info["broad_id"].str[:13]
    smiles = info.sort_values(["core", "screen_id"]).groupby("core")["smiles"].first()
    out = {}
    for c in cores:
        scaf = ""
        for part in str(smiles.get(c, "")).split(","):
            mol = Chem.MolFromSmiles(part.strip())
            if mol is not None:
                scaf = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
                break
        out[c] = scaf
    return out


def chemistry(T) -> dict:
    comp = pd.read_csv(tc.DEV_COMPOUNDS)
    folds = T["fold"]
    scaf = murcko_scaffolds(T["cores"])
    scaf_arr = np.array([scaf[c] for c in T["cores"]])
    rows = {}
    for f in range(5):
        fold = bench.make_fold(T, f)
        test = np.where(folds == f)[0]
        other = np.where(folds != f)[0]
        has = scaf_arr[test] != ""
        before = np.isin(scaf_arr[test], scaf_arr[other]) & has
        after = np.isin(scaf_arr[test], scaf_arr[fold.train_idx]) & has
        rows[str(f)] = {
            "evaluation_compounds": int(len(test)), "training_candidates": int(len(other)),
            "max_tanimoto_before_purge": q(fold.max_sim_before),
            "share_with_analogue_ge_0.5_before": float((fold.max_sim_before >= 0.5).mean()),
            "share_with_analogue_ge_0.7_before": float((fold.max_sim_before >= 0.7).mean()),
            "share_with_analogue_ge_0.85_before": float((fold.max_sim_before >= 0.85).mean()),
            "purged_training_compounds": fold.n_purged, "training_after_purge": fold.n_train,
            "max_tanimoto_after_purge": q(fold.max_sim_after), "max_tanimoto_after_purge_overall": float(fold.max_sim_after.max()),
            "share_with_analogue_ge_boundary_after": float((fold.max_sim_after >= bench.SEPARATION).mean()),
            "murcko_scaffold_shared_with_a_training_candidate_before": float(before.mean()),
            "murcko_scaffold_shared_with_a_training_compound_after": float(after.mean()),
            "evaluation_compounds_without_parsable_scaffold": int((~has).sum()),
        }
    fam_span = comp.groupby("family")["fold"].nunique()
    unit_span = comp.groupby("unit")["fold"].nunique()
    return {"separation_boundary": bench.SEPARATION, "boundary_rule": "training compounds with ECFP4 (Morgan r2, 2048) Tanimoto >= boundary to any evaluation compound are removed from that fold's training set",
            "folds": rows, "families": int(comp["family"].nunique()), "families_spanning_folds": int((fam_span > 1).sum()),
            "connectivity_units_spanning_folds": int((unit_span > 1).sum()),
            "reading": "folds are MoA-family folds: no family or connectivity unit crosses a fold, but "
                       "about a third of evaluation compounds had a >= 0.5 analogue in other folds; the purge removes that route"}


# ---------------------------------------------------------------- masking
def _run_closed(fold, hidden, rule, rows, **params):
    saved = fold.hidden
    fold.hidden = hidden
    try:
        hist, queried, _ = L.closed_loop(fold, rule, B=3, params=params, rows=rows)
    finally:
        fold.hidden = saved
    return hist, queried


def masking(T) -> dict:
    fold = bench.make_fold(T, 0, (1,))
    rows = list(range(64))
    rng = np.random.default_rng(20261018)
    out = {}
    for rule in ("ridge", "knn", "mixture_event", "empcov"):
        h1, q1 = _run_closed(fold, fold.hidden, rule, rows)
        hid = fold.hidden
        Y2 = hid.Y.copy()
        unq = ~q1
        # scramble every cell the first run never queried: random draws from the fold's own value range
        Y2[unq] = rng.normal(np.nanmean(hid.Y), np.nanstd(hid.Y), size=int(unq.sum()))
        hid2 = bench.Hidden(Y=Y2, truth=hid.truth, sd=hid.sd, z=hid.z)
        h2, q2 = _run_closed(fold, hid2, rule, rows)
        same_q = bool(np.array_equal(q1, q2))
        same_y = all(np.array_equal(h1[i][0], h2[i][0]) and np.array_equal(h1[i][1], h2[i][1], equal_nan=True) for i in rows)
        s1 = np.stack([R.score(rule, fold, i, *h1[i]) for i in rows])
        s2 = np.stack([R.score(rule, fold, i, *h2[i]) for i in rows])
        out[rule] = {"same_queries": same_q, "same_observations": same_y, "same_scores": bool(np.array_equal(s1, s2)),
                     "scrambled_cells": int(unq[rows].sum())}
    # control: a leaky policy that reads the hidden matrix must be detected
    def leaky_run(hidden):
        sc = np.where(fold.avail[None, :], hidden.Y[:64], -np.inf)
        return np.argsort(sc, axis=1)[:, :4]
    h = fold.hidden
    Y2 = h.Y.copy()
    Y2[:64] = rng.normal(np.nanmean(h.Y), np.nanstd(h.Y), size=Y2[:64].shape)
    leak = bool(not np.array_equal(leaky_run(h), leaky_run(bench.Hidden(Y=Y2, truth=h.truth, sd=h.sd, z=h.z))))
    out["leaky_control_detected"] = leak
    out["verdict"] = "PASS" if (all(v["same_queries"] and v["same_observations"] and v["same_scores"] for k, v in out.items() if isinstance(v, dict)) and leak) else "FAIL"
    out["reading"] = ("arms see only oracle answers; scrambling every cell a run did not query changes no query, observation, score or list. "
                      "The grader alone reads the hidden side. This does not make a probe independent of the cell it grades.")
    return out


# ---------------------------------------------------------------- missingness
def missingness(T) -> dict:
    Y = T["Y"].astype(np.float64)
    fin = np.isfinite(Y)
    info = pd.read_csv(tc.PRISM_TREATMENTS, usecols=["broad_id", "screen_id"])
    info["core"] = info["broad_id"].str[:13]
    screens = info.groupby("core")["screen_id"].agg(lambda s: "+".join(sorted(set(s)))).reindex(T["cores"]).to_numpy()
    by_screen = {s: {"compounds": int((screens == s).sum()), "finite_fraction": float(fin[screens == s].mean()),
                     "median_missing_lines": float(np.median((~fin[screens == s]).sum(1)))} for s in sorted(set(screens))}
    lo = np.where(fin.mean(0) < 0.9)[0]
    strong = np.nanmin(Y, axis=1) <= -3.0
    miss_per = (~fin).sum(1)
    admiss = {}
    reach = {}
    for f in range(5):
        tr = np.where(T["fold"] != f)[0]
        te = np.where(T["fold"] == f)[0]
        av = fin[tr].mean(0) >= bench.MIN_TRAIN_FINITE
        G = np.nanmedian(Y[tr], axis=0)
        ev = tc.events(Y[te], G)
        admiss[str(f)] = int(av.sum())
        reach[str(f)] = {"events": int(ev.sum()), "events_on_inadmissible_lines": int(ev[:, ~av].sum()),
                         "share_unreachable": float(ev[:, ~av].sum() / max(ev.sum(), 1)),
                         "missing_cells_on_admissible_lines": float((~fin[te][:, av]).mean())}
    return {"cell_finite_fraction": float(fin.mean()), "compound_finite_lines": q(fin.sum(1)), "line_finite_fraction": q(fin.mean(0), (0, 0.05, 0.25, 0.5, 1)),
            "lines_below_0.9_finite_overall": int(len(lo)), "by_screen": by_screen,
            "missing_lines_per_compound_strong_killers": float(miss_per[strong].mean()), "missing_lines_per_compound_other": float(miss_per[~strong].mean()),
            "strong_killers_min_lfc_le_-3": int(strong.sum()),
            "admissible_lines_per_fold_train_rule": admiss, "events_unreachable_by_nomination": reach,
            "treatment_of_missing": "a missing scoring-matrix cell is a failed unit when probed and a non-hit when nominated; nominated-unknown counts are reported with every utility",
            "reading": "missingness is concentrated in a few lines and one screen; it is not shown to be random with respect to activity (see strong-killer contrast), so unknown outcomes are bounded, not imputed"}


# ---------------------------------------------------------------- granularity
def granularity(T) -> dict:
    raw = tc.PRISM
    pool = pd.read_csv(raw / "secondary-screen-pooling-info.csv")
    lines = list(T["lines"])
    hts = pool[pool["screen_id"] == "HTS"].set_index("row_name")["pool_id"].reindex(lines)
    mts = pool[pool["screen_id"] == "MTS004"].set_index("row_name")["pool_id"].reindex(lines)
    sizes = hts.value_counts()
    hcodes = {p: k for k, p in enumerate(sorted(hts.dropna().unique()))}
    pid = np.array([hcodes[p] for p in hts])
    ct = pd.crosstab(hts.fillna("NA"), mts.fillna("NA"))
    concord = float(ct.max(1).sum() / ct.to_numpy().sum())
    cols = list(pd.read_csv(tc.PRISM_TREATMENTS, nrows=0).columns)
    ti = pd.read_csv(tc.PRISM_TREATMENTS, usecols=["broad_id", "screen_id", "dose"])
    ti["core"] = ti["broad_id"].str[:13]
    off = ti[(ti["dose"] - 2.5).abs() > 0.05]
    runs = ti.groupby("core").size()
    multi_dose = ti.groupby("core")["dose"].nunique()
    f0 = bench.make_fold(T, 0)
    touched = {str(k): int(len(set(pid[f0.design[:k]]))) for k in (4, 8, 16, 32, 64)}
    return {"pool_source": "data/external/prism_19q4/raw/secondary-screen-pooling-info.csv (screens HTS and MTS004 only supply the primary-screen pools)",
            "panel_lines": len(lines), "pools_HTS": int(hts.nunique()), "lines_per_pool": {"min": int(sizes.min()), "mean": float(sizes.mean()), "max": int(sizes.max())},
            "panel_lines_in_MTS004_pools": int(mts.notna().sum()), "pool_composition_concordance_HTS_vs_MTS004": concord,
            "collapsed_primary_treatment_columns": cols,
            "plate_well_replicate_mapping_available": False,
            "reading_of_mapping": "line -> pool membership is established; compound plate, well, detection plate and replicate count are not available for the replicate-collapsed primary data, so a well count, a price per well and the number of wells that bought a value are NOT established",
            "treatments_off_2.5uM": int(len(off)), "treatments": int(len(ti)), "cores_with_any_off_dose_treatment": int(off["core"].nunique()),
            "cores_with_multiple_runs": int((runs > 1).sum()), "cores_with_multiple_distinct_doses": int((multi_dose > 1).sum()),
            "logical_design_pools_touched": touched,
            "reading": "a PRISM well reads a pool of about 24 lines; a logical single-line unit is therefore not a physical purchase. "
                       "Costs here are hypothetical logical units; the pool-well grain is a sensitivity, not a priced design. "
                       "The probe is the scoring-matrix value plus synthetic noise (replicate spread from the secondary screen), "
                       "not an independent assay of the graded cell."}


# ---------------------------------------------------------------- old loop
def oldloop(T) -> dict:
    """Reproduce the saved indication-triage totals at w = 16 and split hits into probed and unprobed pairs."""

    import develop as D
    import policy as P

    dev = json.loads((TRIAGE / "DEVELOPMENT.json").read_text(encoding="utf-8"))
    chosen = dev["tuning"]["chosen"]
    out = {}
    t0 = time.time()
    totals = {"maestro_loop": [0, 0, 0], "two_stage": [0, 0, 0]}
    for f in (2, 3, 4):
        ctx, camps = D.context(D.load(), f, 1.0, False)
        for arm in totals:
            for c, idx in enumerate(camps):
                probed = set()
                raw = ctx.observe

                def logged(i, lines, _raw=raw, _probed=probed):
                    for l in np.asarray(lines, dtype=int):
                        _probed.add((int(i), int(l)))
                    return _raw(i, lines)

                ctx.observe = logged
                res = P.run_arm(arm, ctx, idx, D.PRIMARY_W, chosen.get(arm))
                ctx.observe = raw
                # picks carry campaign-local compound positions; the probe log carries global compound indices
                picks = [(int(idx[i]), int(l)) for i, l in res["picks"]]
                hits = [(i, l) for i, l in picks if ctx.truth[i, l]]
                n_probed_hits = sum(1 for p in hits if p in probed)
                totals[arm][0] += len(hits)
                totals[arm][1] += n_probed_hits
                totals[arm][2] += len(picks) - sum(1 for p in picks if p in probed)
        print("old loop fold", f, {a: v for a, v in totals.items()}, round(time.time() - t0), flush=True)
    saved = {a: dev["estimation"]["16"][a]["hits"] for a in totals}
    for arm, (hits, probed_hits, unprobed_slots) in totals.items():
        out[arm] = {"hits": hits, "saved_hits": saved[arm], "reproduces_saved_total": hits == saved[arm],
                    "hits_on_pairs_the_arm_probed": probed_hits, "hits_on_unprobed_pairs": hits - probed_hits,
                    "share_of_hits_on_probed_pairs": probed_hits / max(hits, 1), "unprobed_pairs_listed": unprobed_slots}
    out["reading"] = "the saved totals reproduce exactly; the share of listed hits that are pairs the arm itself probed is the part that is a noisy re-read of the graded cell"
    return out


SECTIONS = {"provenance": provenance, "chemistry": chemistry, "masking": masking, "missingness": missingness,
            "granularity": granularity, "oldloop": oldloop}


def main() -> None:
    want = sys.argv[1:] or list(SECTIONS)
    T = bench.load_tables()
    cur = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for name in want:
        t0 = time.time()
        cur[name] = SECTIONS[name](T)
        tc.write_json(OUT, cur)
        print("section", name, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
