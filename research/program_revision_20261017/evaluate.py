"""Stage B (frozen decisions on future projects) and Stage C (complete policies), one entry point.

File summary
- Path: research/program_revision_20261017/evaluate.py
- Purpose: evaluate the frozen libraries of LIBRARIES.json on held-out lines (future lines of seen
  lineages; future lineages), novel drug structure groups, and their joint novelty, under the
  registered information conditions, then run complete equal-budget campaigns on future lines.
- Access: ``--dry`` exercises every code path on development query lines with future data
  masked (results go to tmp/, never RESULTS.json). Without ``--dry`` the evaluator refuses unless
  FREEZE.json matches and every registered library exists; the first opening of future data writes
  ACCESS.json (write-once: time, digests of LIBRARIES.json and FREEZE.json). A later run refuses
  if LIBRARIES.json changed after that opening.
- Outputs: RESULTS.json (registered analysis), tmp/.../units_*.json (per-line records),
  trajectories/stage_c_traces.jsonl (action traces of the first lines of each policy).
- Interfaces: ``python -B evaluate.py [--dry] [--stages B,C]``; `analyse(units)`.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from common import CACHE, HERE, hash_unit, holm, paired, sha256, write_json
from engine import (INFO, ContextFold, Domain, DrugFold, fixed_probe_design, legal_atoms, nominate, ridge_baseline,
                    score_nominations)
from freeze import check_freeze
from policy import POLICIES, LinePredictor, afa_select, probe_readout, run_campaign
from vc import Program, ProgramLibrary, atoms, hit_probability, parse_state

ARMS = ["seed_fixed", "stepwise", "maestro_enum", "maestro_llm", "maestro_enum_empty", "maestro_llm_empty",
        "maestro_enum_joint", "maestro_llm_joint"]
PRIMARY = "maestro_llm"
MIN_EFFECT = 0.10  # hits per line at K = 10 (one extra qualified hit per ten lines)


def load_libraries(path=None):
    rec = json.loads((path or HERE / "LIBRARIES.json").read_text(encoding="utf-8"))
    libs = {}
    for arm in ARMS:
        if arm not in rec:
            raise SystemExit(f"LIBRARY_MISSING: {arm}")
        libs[arm] = (ProgramLibrary([Program(p["scope"], p["state"], p["origin"]) for p in rec[arm]["programs"]]),
                     rec[arm]["design"])
    return libs, rec


def restrict(lib: ProgramLibrary, info: str, probe_cores) -> ProgramLibrary:
    """Programs whose measurement program is purchased under this condition."""

    legal = legal_atoms(info)
    keep = []
    for p in lib.programs:
        ats = atoms(parse_state(p.state))
        if all(a[0] in legal and (a[0] != "probe" or a[1] in probe_cores) for a in ats):
            keep.append(Program(p.scope, p.state, p.origin))
    return ProgramLibrary(keep)


def open_domain(dry: bool):
    if dry:
        return Domain(open_future=False)
    check_freeze()
    libs_digest = sha256(HERE / "LIBRARIES.json")
    access = HERE / "ACCESS.json"
    if access.exists():
        rec = json.loads(access.read_text(encoding="utf-8"))
        if rec["libraries_sha256"] != libs_digest:
            raise SystemExit("LIBRARIES_CHANGED_AFTER_EXPOSURE")
    else:
        write_json(access, {"opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "libraries_sha256": libs_digest, "freeze_sha256": sha256(HERE / "FREEZE.json"),
                            "note": "first opening of novel-drug and held-out-line outcomes"})
    return Domain(open_future=True)


def targets(dom, dry):
    L = dom.lines
    src = np.flatnonzero(dom.src_line)
    if dry:
        q = np.flatnonzero(dom.src_line & (L.role.to_numpy() == "query"))
        return np.setdiff1d(src, q), q, np.array(["dry_query"] * len(q))
    split = L.line_split.to_numpy()
    T = np.flatnonzero((split == "future_line") | (split == "future_lineage"))
    return src, T, split[T]


def score_block(dom, score, drug_rows, line_rows):
    nom = nominate(score, dom.tie_drug[drug_rows])
    h, u = score_nominations(dom, nom, drug_rows, line_rows)
    return h.tolist(), u.tolist()


def stage_b(dom, libs, probes, train, T):
    out = {}
    folds = {}
    for info in ("I0", "I1", "I2", "I3"):
        f = ContextFold(dom, train, T, info, probes)
        folds[info] = f
        out[f"strong|{info}"] = score_block(dom, f.apply(None)[2], f.drows, T)
        if info in ("I1", "I2", "I3"):
            for arm, (lib, design) in libs.items():
                if arm.endswith("_joint"):
                    continue
                r = restrict(lib, info, f.probe_cores)
                out[f"{arm}|{info}"] = score_block(dom, f.apply(r)[2], f.drows, T)
    for info in ("I1", "I2"):
        drows = folds[info].drows
        mean, var = ridge_baseline(dom, train, T, info, probes)
        sc = hit_probability(mean, var[:, None] + dom.rep_var[drows][:, None] / 6, dom.thr[drows][:, None])
        out[f"drug_ridge|{info}"] = score_block(dom, sc, drows, T)
    # leave-one-program-out on future lines (I2): each program's effect on the frozen decisions
    for arm in (PRIMARY, "maestro_enum", "stepwise"):
        full = restrict(libs[arm][0], "I2", folds["I2"].probe_cores)
        for k, p in enumerate(full.programs):
            ablated = ProgramLibrary([q for i, q in enumerate(full.programs) if i != k])
            out[f"ablate[{arm}]-{p.key}|I2"] = score_block(dom, folds["I2"].apply(ablated)[2], folds["I2"].drows, T)
    # joint arms: each library with its own measurement program (8 wells, same budget)
    for arm, (lib, design) in libs.items():
        if not arm.endswith("_joint"):
            continue
        f = ContextFold(dom, train, T, "I2", design)
        out[f"{arm}|I2"] = score_block(dom, f.apply(restrict(lib, "I2", f.probe_cores))[2], f.drows, T)
        out[f"strong_own_design[{arm}]|I2"] = score_block(dom, f.apply(None)[2], f.drows, T)
    # conventional adaptive acquisition (8 wells, one per round) with and without the primary library
    fI2 = folds["I2"]
    for name, lib in (("afa", None), (f"afa+{PRIMARY}", restrict(libs[PRIMARY][0], "I2", fI2.probe_cores))):
        pred = LinePredictor(fI2, lib)
        S = np.zeros((len(fI2.drows), len(T)))
        for j, c in enumerate(T):
            readouts, used = [], set()
            for _ in range(8):
                d = afa_select(pred, j, readouts, used)
                used.add(d)
                r = probe_readout(dom, d, c)
                if r:
                    readouts.append(r)
            S[:, j] = pred.score(j, readouts)[0]
        out[f"{name}|I2"] = score_block(dom, S, fI2.drows, T)
    return out, folds


def novel_drugs(dom, libs, probes, train, T, folds):
    """Unseen structure groups on known lines and on future lines, zero- and few-observation."""

    nov = np.flatnonzero(~dom.src_drug)
    L = dom.lines
    pools = L.pool_id.to_numpy()
    src = np.flatnonzero(dom.src_line)
    counts = {p: int((pools[src] == p).sum()) for p in set(pools[src])}
    best = max(counts.values())
    pool = sorted([p for p, n in counts.items() if n == best], key=lambda p: hash_unit([str(p)], "pool")[0])[0]
    in_pool = set(src[pools[src] == pool].tolist())
    out = {"_probe_pool": {"pool_id": str(pool), "source_lines": len(in_pool)}}
    res = {}
    for info in ("I1", "I2"):
        f = folds[info]
        tpos = {c: i for i, c in enumerate(f.train)}
        pool_probes = [{tpos[c]: float(dom.X1[d, c]) for c in in_pool if np.isfinite(dom.X1[d, c])} for d in nov]
        known_sub = np.array([i for i, c in enumerate(f.train) if c not in in_pool])
        tgt_sub = np.array([j for j, c in enumerate(f.target) if c not in in_pool])
        settings = [("known_lines", "train", known_sub)] if info == "I2" else []
        settings.append((f"future_lines_{info}", "target", tgt_sub))
        for where, on, sub in settings:
            for dobs, pp in (("zero", None), ("few", pool_probes)):
                df = DrugFold(f, nov, on=on, pool_probes=pp, line_subset=sub)
                lines = df.lines
                res[f"strong|{where}|{dobs}"] = score_block(dom, df.apply(None)[2], nov, lines)
                pot = hit_probability(df.additive, df.base_var, df.thr[:, None])
                res[f"potency_only|{where}|{dobs}"] = score_block(dom, pot, nov, lines)
                for arm, (lib, design) in libs.items():
                    if arm.endswith("_joint"):
                        continue
                    r = restrict(lib, info, f.probe_cores)
                    res[f"{arm}|{where}|{dobs}"] = score_block(dom, df.apply(r)[2], nov, lines)
                res[f"_lines|{where}|{dobs}"] = [int(c) for c in lines]
    out.update(res)
    return out


def stage_c(dom, libs, probes, folds, T, trace_path):
    f = folds["I2"]
    out = {}
    plan = [("strong", None, list(POLICIES))]
    for arm in ("seed_fixed", "stepwise", "maestro_enum", "maestro_llm"):
        plan.append((arm, restrict(libs[arm][0], "I2", f.probe_cores), ["fixed_probes_feedback", "exploit_first_feedback"]))
    plan.append((PRIMARY + "@afa", restrict(libs[PRIMARY][0], "I2", f.probe_cores), ["afa_probes_feedback"]))
    with trace_path.open("w", encoding="utf-8", newline="\n") as tr:
        for name, lib, pols in plan:
            pred = LinePredictor(f, lib)
            for pol in pols:
                rows = []
                for j in range(len(T)):
                    r = run_campaign(pred, j, POLICIES[pol], fixed_probes=probes)
                    if j < 3:
                        tr.write(json.dumps({"arm": name, "policy": pol, "line": dom.lines.depmap_id[T[j]], **r}) + "\n")
                    rows.append({k: r[k] for k in ("hits", "wells", "rounds", "confirmed", "unknown", "wells_to_3_hits")})
                out[f"{name}|{pol}"] = rows
        for arm in ("maestro_enum_joint", "maestro_llm_joint"):
            lib, design = libs[arm]
            fj = ContextFold(dom, f.train, T, "I2", design)
            pred = LinePredictor(fj, restrict(lib, "I2", fj.probe_cores))
            out[f"{arm}|fixed_probes_feedback"] = [
                {k: v for k, v in run_campaign(pred, j, POLICIES["fixed_probes_feedback"], fixed_probes=design).items()
                 if k != "trace"} for j in range(len(T))]
    return out


# ---------------------------------------------------------------- registered analysis

def contrast(units, a, b, groups, mask=None, key=0):
    x, y = np.array(units[a][key], float), np.array(units[b][key], float)
    g = np.asarray(groups)
    if mask is not None:
        x, y, g = x[mask], y[mask], g[mask]
    r = paired(x - y, g)
    r.update(a=a, b=b, mean_a=float(x.mean()), mean_b=float(y.mean()))
    return r


def verdict(r, p_adj=None):
    lo, hi = r["ci95"]
    if hi < 0:
        return "HARMFUL"
    if r["mean"] >= MIN_EFFECT and lo > 0 and (p_adj is None or p_adj < 0.05):
        return "CONFIRMED"
    return "NOT_CONFIRMED"


def analyse(units: dict, dry: bool = False) -> dict:
    meta = units["_meta"]
    groups = np.array(meta["cluster"])
    strata = np.array(meta["stratum"])
    B = units["B"]
    res = {"meta": {k: v for k, v in meta.items() if k not in ("cluster", "stratum", "lines")}}
    # Stage B summary table
    table = {}
    for k, (h, u) in B.items():
        h, u = np.array(h), np.array(u)
        row = {"all": [float(h.mean()), float(u.mean())]}
        for s in sorted(set(strata)):
            m = strata == s
            row[s] = [float(h[m].mean()), float(u[m].mean())]
        table[k] = row
    res["B_table_hits_unknown_per_line"] = table
    fam = {"H1_method_vs_strong": (f"{PRIMARY}|I2", "strong|I2"),
           "H2_method_vs_conventional_search": (f"{PRIMARY}|I2", "stepwise|I2"),
           "H3_llm_value": (f"{PRIMARY}|I2", "maestro_enum|I2"),
           "H4_editable_vs_fixed": (f"{PRIMARY}|I2", "seed_fixed|I2")}
    prim = {k: contrast(B, a, b, groups) for k, (a, b) in fam.items()}
    adj = holm({k: v["p_one_sided"] for k, v in prim.items()})
    for k in prim:
        prim[k]["p_holm"] = adj[k]
        prim[k]["verdict"] = verdict(prim[k], adj[k])
        prim[k]["by_stratum"] = {s: contrast(B, *fam[k], groups, strata == s) for s in sorted(set(strata))}
    res["B_primary_few_observation"] = prim
    sec = {}
    pairs = {
        "zero_obs_method_vs_strong": (f"{PRIMARY}|I1", "strong|I1"),
        "zero_obs_llm_value": (f"{PRIMARY}|I1", "maestro_enum|I1"),
        "zero_obs_seed_vs_strong": ("seed_fixed|I1", "strong|I1"),
        "few_obs_enum_vs_strong": ("maestro_enum|I2", "strong|I2"),
        "few_obs_stepwise_vs_strong": ("stepwise|I2", "strong|I2"),
        "few_obs_seed_vs_strong": ("seed_fixed|I2", "strong|I2"),
        "empty_start_llm_vs_strong": ("maestro_llm_empty|I2", "strong|I2"),
        "empty_start_enum_vs_strong": ("maestro_enum_empty|I2", "strong|I2"),
        "joint_vs_sequential_llm": ("maestro_llm_joint|I2", f"{PRIMARY}|I2"),
        "joint_vs_sequential_enum": ("maestro_enum_joint|I2", "maestro_enum|I2"),
        "joint_llm_vs_strong": ("maestro_llm_joint|I2", "strong|I2"),
        "afa_vs_fixed_design": ("afa|I2", "strong|I2"),
        "library_on_afa": (f"afa+{PRIMARY}|I2", "afa|I2"),
        "rna_vs_probes": ("strong|I3", "strong|I2"),
        "rna_method_vs_strong": (f"{PRIMARY}|I3", "strong|I3"),
        "probes_vs_panel": ("strong|I2", "strong|I1"),
        "strong_vs_ridge_I2": ("strong|I2", "drug_ridge|I2"),
    }
    for k, (a, b) in pairs.items():
        if a in B and b in B:
            sec[k] = contrast(B, a, b, groups)
            sec[k]["by_stratum"] = {s: contrast(B, a, b, groups, strata == s) for s in sorted(set(strata))}
    res["B_secondary"] = sec
    abl = {}
    for k in B:
        if k.startswith("ablate["):
            arm = k[len("ablate["):k.index("]")]
            prog = k[k.index("]-") + 2:-len("|I2")]
            r = contrast(B, f"{arm}|I2", k, groups)
            abl.setdefault(arm, {})[prog] = {"full_minus_ablated": r["mean"], "ci95": r["ci95"]}
    res["B_program_ablation_I2"] = abl
    # novel drugs: per-line nominations among novel drugs; clusters = line lineage
    N = units.get("N", {})
    nres = {}
    for key in [k for k in N if k.startswith("strong|")]:
        _, where, dobs = key.split("|")
        lines = np.array(N[f"_lines|{where}|{dobs}"])
        g = units["_line_lineage"]
        gl = np.array([g[str(c)] for c in lines])
        row = {"strong": float(np.mean(N[key][0])), "unknown_strong": float(np.mean(N[key][1])),
               "potency_only": float(np.mean(N[f"potency_only|{where}|{dobs}"][0]))}
        for arm in ("seed_fixed", "stepwise", "maestro_enum", PRIMARY):
            row[arm] = float(np.mean(N[f"{arm}|{where}|{dobs}"][0]))
        row["method_vs_strong"] = contrast(N, f"{PRIMARY}|{where}|{dobs}", key, gl)
        row["strong_vs_potency"] = contrast(N, key, f"potency_only|{where}|{dobs}", gl)
        nres[f"{where}|{dobs}"] = row
    res["N_novel_drugs"] = nres
    res["N_probe_pool"] = N.get("_probe_pool")
    # Stage C
    C = units.get("C", {})
    cres = {}
    for k, rows in C.items():
        hits = np.array([r["hits"] for r in rows], float)
        cres[k] = {"hits_per_line": float(hits.mean()), "wells": float(np.mean([r["wells"] for r in rows])),
                   "rounds": float(np.mean([r["rounds"] for r in rows])),
                   "unknown": float(np.mean([r["unknown"] for r in rows])),
                   "lines_reaching_3_hits": int(sum(r["wells_to_3_hits"] is not None for r in rows)),
                   "median_wells_to_3_hits": (float(np.median([r["wells_to_3_hits"] for r in rows if r["wells_to_3_hits"] is not None]))
                                              if any(r["wells_to_3_hits"] is not None for r in rows) else None)}
    res["C_policies"] = cres

    def ch(a, b):
        x = np.array([r["hits"] for r in C[a]], float)
        y = np.array([r["hits"] for r in C[b]], float)
        r = paired(x - y, groups)
        r.update(a=a, b=b)
        return r

    if C:
        cc = {"structural_fixed_feedback": ch(f"{PRIMARY}|fixed_probes_feedback", "strong|fixed_probes_feedback"),
              "structural_exploit_first": ch(f"{PRIMARY}|exploit_first_feedback", "strong|exploit_first_feedback"),
              "total_vs_exploit_first": ch(f"{PRIMARY}|fixed_probes_feedback", "strong|exploit_first_feedback"),
              "total_vs_fixed_feedback": ch(f"{PRIMARY}|fixed_probes_feedback", "strong|fixed_probes_feedback"),
              "total_vs_afa": ch(f"{PRIMARY}|fixed_probes_feedback", "strong|afa_probes_feedback"),
              "feedback_vs_one_shot": ch("strong|fixed_probes_feedback", "strong|fixed_probes_then_confirm"),
              "probes_vs_exploit_first": ch("strong|fixed_probes_feedback", "strong|exploit_first_feedback"),
              "afa_vs_fixed": ch("strong|afa_probes_feedback", "strong|fixed_probes_feedback"),
              "joint_llm_vs_strong_fixed_feedback": ch("maestro_llm_joint|fixed_probes_feedback", "strong|fixed_probes_feedback"),
              "enum_structural_fixed_feedback": ch("maestro_enum|fixed_probes_feedback", "strong|fixed_probes_feedback"),
              "stepwise_structural_fixed_feedback": ch("stepwise|fixed_probes_feedback", "strong|fixed_probes_feedback")}
        for k in cc:
            cc[k]["verdict"] = verdict(cc[k])
        res["C_contrasts"] = cc
        # knowledge acquisition cost and payback (lines needed for the gain to repay the wells)
        libs = units["_libraries"]
        base = cres["strong|fixed_probes_feedback"]["hits_per_line"] / 28.0
        pay = {}
        for arm in ("stepwise", "maestro_enum", PRIMARY, "maestro_llm_joint"):
            k = f"{arm}|fixed_probes_feedback"
            gain = cres[k]["hits_per_line"] - cres["strong|fixed_probes_feedback"]["hits_per_line"]
            wells = libs[arm]["accounting"].get("distinguishing_wells", libs[arm]["accounting"].get("wells_charged", 0))
            pay[arm] = {"development_wells": wells, "gain_hits_per_line": gain,
                        "hits_those_wells_buy_at_baseline_yield": wells * base,
                        "lines_to_repay": (wells * base / gain) if gain > 0 else None}
        res["C_knowledge_payback"] = pay
    res["dry_run"] = dry
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--stages", default="B,N,C")
    ap.add_argument("--libraries", default=None, help="dry runs only: another LIBRARIES file")
    args = ap.parse_args()
    if args.libraries and not args.dry:
        raise SystemExit("LIBRARIES_OVERRIDE_DRY_ONLY")
    t0 = time.time()
    from pathlib import Path
    libs, librec = load_libraries(Path(args.libraries) if args.libraries else None)
    dom = open_domain(args.dry)
    probes = librec["_bench"]["probes"]
    if probes != fixed_probe_design(dom, 8):
        raise SystemExit("DESIGN_MISMATCH: the frozen design does not reproduce")
    train, T, strata = targets(dom, args.dry)
    units = {"_meta": {"lines": [str(dom.lines.depmap_id[c]) for c in T], "stratum": strata.tolist(),
                       "cluster": [str(dom.lines.primary_tissue[c]) for c in T], "n_train_lines": int(len(train)),
                       "probes": probes, "K": 10},
             "_line_lineage": {str(c): str(dom.lines.primary_tissue[c]) for c in range(len(dom.lines))},
             "_libraries": {a: librec[a] for a in ARMS}}
    stages = args.stages.split(",")
    units["B"], folds = stage_b(dom, libs, probes, train, T)
    print("B", round(time.time() - t0), flush=True)
    if "N" in stages and not args.dry:
        units["N"] = novel_drugs(dom, libs, probes, train, T, folds)
        print("N", round(time.time() - t0), flush=True)
    if "C" in stages:
        tp = (CACHE if args.dry else HERE / "trajectories") / "stage_c_traces.jsonl"
        units["C"] = stage_c(dom, libs, probes, folds, T, tp)
        print("C", round(time.time() - t0), flush=True)
    tag = "dry" if args.dry else "future"
    write_json(CACHE / f"units_{tag}.json", units)
    res = analyse(units, args.dry)
    res["seconds"] = round(time.time() - t0, 1)
    res["units_sha256"] = sha256(CACHE / f"units_{tag}.json")
    write_json((CACHE / "RESULTS_dry.json") if args.dry else (HERE / "RESULTS.json"), res)
    print(json.dumps(res["B_primary_few_observation"], indent=1)[:3000])


if __name__ == "__main__":
    main()
