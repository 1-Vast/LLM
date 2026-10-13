"""Run S1 (development, outer fold 0) or S2 (validation, outer folds 1-4, once) of PROTOCOL.md.

File summary
- Path: research/orbit_contrast_20261013/run.py
- Purpose: build both tasks from local exposed assets, run the nested pipeline per outer fold for the
  real knowledge and its variants, aggregate per-entity scores, and write RESULTS_S1.json or the
  write-once RESULTS.json.
- Core points:
  - Populations are fixed by the real knowledge and the truth's activity, identically for every arm
    and every knowledge variant.
  - S2 refuses unless FREEZE.json authenticates (freeze.check) and RESULTS.json does not exist.
  - No network access, no provider call.
- Commands (repository root or study folder): `python run.py s0`, `python run.py s1`,
  `python run.py s2`.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sources as S  # noqa: E402
from ocea import compress, concat, entity_means, fit_predict, paired, spearman  # noqa: E402
from routes import TaskA, TaskB, rng_for  # noqa: E402

MEI = 0.01
Z_ALPHA, Z_POWER = 1.959964, 0.841621
N_RELABEL = 5
A_BASE, A_ORBIT = ("chem",), ("know", "genetic")
B_FULL, B_NT = ("self", "pharm", "cotarget", "esm"), ("pharm", "cotarget", "esm")


def build():
    z = S.load_phase1()
    store, ents, smiles = S.compound_store(z)
    ck = S.compile_compounds(store, ents)
    fps = S.morgan(smiles)
    deg = Counter(g for s in ck.signed for g in s)
    kd_genes = [str(g) for g in z["kd_gene"]]
    A = TaskA(z, ck, fps, np.array([deg[g] for g in kd_genes]))
    E, Eh = S.esm_features(kd_genes)
    B = TaskB(z, ck, E, Eh)
    return {"z": z, "store": store, "ents": ents, "ck": ck, "fps": fps, "deg": deg, "A": A, "B": B}


# ------------------------------------------------------------------------------------------- Task A'

def a_masks(A: TaskA):
    z = A.z
    fold = np.array([S.fold_of(str(k)) for k in z["compound"]])
    thr = S.vehicle_thresholds(z)
    nrm = np.linalg.norm(np.nan_to_num(A.Y.astype(np.float64)), axis=2)
    act = A.has & (nrm > thr[None])
    return fold, act


def run_a(A: TaskA, K, outer: list, salt: str, ablate=A_ORBIT) -> dict:
    fold, act = a_masks(A)
    ann = A.annotated
    cells = []
    for k in outer:
        inner = []
        for j in range(5):
            if j == k:
                continue
            cm = ((fold == j) & ann)[:, None] & act
            qc, ql = np.nonzero(cm)
            res, gen, y = A.setting(K, qc, ql, (fold != j) & (fold != k), act, f"{salt}|k{k}|j{j}")
            inner.append(compress(res, gen, y, A_BASE, A_ORBIT, ql, qc, j))
        cm = ((fold == k) & ann)[:, None] & A.has
        qc, ql = np.nonzero(cm)
        res, gen, y = A.setting(K, qc, ql, fold != k, act, f"{salt}|k{k}|test")
        te = compress(res, gen, y, A_BASE, A_ORBIT, ql, qc, -1)
        out = fit_predict(concat(inner), te, A_BASE, A_ORBIT, A.L, ablate)
        others = np.flatnonzero((fold != k) & ann)
        shared = (A.knowledge_tok[qc].astype(np.float32) @ A.knowledge_tok[others].T.astype(np.float32)).max(1) > 0
        cells.append({"entity": qc, "line": ql, "active": act[qc, ql], "strict_new": ~shared,
                      "n_signed": np.array([len(A.ck.signed[d]) for d in qc]),
                      "scores": out["scores"], "gates": out["gates_test"], "avail": te.avail,
                      "contrast": {r: te.cos_f[r] - te.cos_orbit[r] for r in A_ORBIT}, "accuracy": dict(te.cos_f),
                      "gate_info": out["gate_info"], "betas": out["betas"], "fold": k})
    return merge(cells)


# ------------------------------------------------------------------------------------------- Task B

def run_b(B: TaskB, K, outer: list, salt: str, pipelines=(("full", B_FULL, ("self",)), ("nontrivial", B_NT, B_NT))) -> dict:
    fold = np.array([S.fold_of(g) for g in B.genes])
    routes = tuple(sorted({r for _, rs, _ in pipelines for r in rs}, key=B_FULL.index))
    by = {name: [] for name, _, _ in pipelines}
    for k in outer:
        inner = {name: [] for name, _, _ in pipelines}
        for j in range(5):
            if j == k:
                continue
            cm = (fold == j)[:, None] & B.has
            qg, ql = np.nonzero(cm)
            res, gen, y = B.setting(K, qg, ql, (fold != j) & (fold != k), f"{salt}|k{k}|j{j}", routes=routes)
            for name, rs, _ in pipelines:
                inner[name].append(compress(res, gen, y, (), rs, ql, qg, j))
        cm = (fold == k)[:, None] & B.has
        qg, ql = np.nonzero(cm)
        res, gen, y = B.setting(K, qg, ql, fold != k, f"{salt}|k{k}|test", routes=routes)
        for name, rs, abl in pipelines:
            te = compress(res, gen, y, (), rs, ql, qg, -1)
            out = fit_predict(concat(inner[name]), te, (), rs, B.L, abl)
            by[name].append({"entity": qg, "line": ql, "landmark": B.is_lm[qg], "scores": out["scores"],
                             "gates": out["gates_test"], "avail": te.avail,
                             "contrast": {r: te.cos_f[r] - te.cos_orbit[r] for r in rs}, "accuracy": dict(te.cos_f),
                             "gate_info": out["gate_info"], "betas": out["betas"], "fold": k})
    return {name: merge(v) for name, v in by.items()}


# ------------------------------------------------------------------------------------------- summaries

def merge(cells: list) -> dict:
    out = {}
    for key in cells[0]:
        v0 = cells[0][key]
        if isinstance(v0, np.ndarray):
            out[key] = np.concatenate([c[key] for c in cells])
        elif key in ("scores", "avail", "contrast", "accuracy"):
            out[key] = {r: np.concatenate([c[key][r] for c in cells]) for r in v0}
        elif key == "gates":
            out[key] = {f"{g}:{r}": np.concatenate([c[key][(g, r)] for c in cells]) for (g, r) in v0}
        else:
            out[key] = [c[key] for c in cells]
    return out


def contrast(res: dict, mask: np.ndarray, a: str, b: str) -> dict:
    ue, va = entity_means(res["scores"][a], res["entity"], mask)
    _, vb = entity_means(res["scores"][b], res["entity"], mask)
    return paired(va - vb)


def arm_means(res: dict, mask: np.ndarray) -> dict:
    return {a: float(entity_means(s, res["entity"], mask)[1].mean()) for a, s in res["scores"].items()} if mask.any() else {}


CONTRASTS = (("F", "O"), ("F", "R"), ("F", "Cp"), ("F", "C"), ("F", "N"), ("N", "O"), ("R", "O"), ("Cp", "O"),
             ("C", "O"), ("O", "B0"), ("B0", "Z0"))


def summarise(res: dict, populations: dict, routes: tuple) -> dict:
    out = {}
    res = dict(res)
    res["scores"] = dict(res["scores"], Z0=np.zeros_like(res["scores"]["F"]))
    for name, mask in populations.items():
        block = {"cells": int(mask.sum()), "entities": int(len(np.unique(res["entity"][mask]))), "arms": arm_means(res, mask)}
        if block["entities"] >= 5:
            block["contrasts"] = {f"{a}-{b}": contrast(res, mask, a, b) for a, b in CONTRASTS}
            block["ablations"] = {f"F-(F-{r})": contrast(res, mask, "F", f"F-{r}") for r in routes if f"F-{r}" in res["scores"]}
        out[name] = block
    cert = {}
    for r in routes:
        m = res["avail"][r]
        if m.sum() >= 10:
            c = res["contrast"][r][m]
            cert[r] = {"cells": int(m.sum()), "mean_contrast": float(c.mean()),
                       "spearman_identity_gate": spearman(res["gates"][f"id:{r}"][m], c),
                       "spearman_accuracy_gate": spearman(res["gates"][f"acc:{r}"][m], c),
                       "admitted_fraction": float((res["gates"][f"id:{r}"][m] > 0).mean())}
    out["certificates"] = cert
    return out


def power(diff: dict, units_validation: int) -> dict:
    sd = diff.get("sd")
    if sd is None:
        return {"note": "too few units"}
    n_needed = int(np.ceil(((Z_ALPHA + Z_POWER) * sd / MEI) ** 2))
    from math import erf, sqrt
    z = MEI / (sd / np.sqrt(units_validation)) - Z_ALPHA
    pw = 0.5 * (1 + erf(z / sqrt(2)))
    return {"sd_entity_diff": sd, "mei": MEI, "units_needed_80pct": n_needed, "units_expected_validation": units_validation,
            "power_at_mei": float(pw)}


def a_populations(A: TaskA, res: dict) -> dict:
    act = res["active"]
    return {"primary_active": act, "all_cells": np.ones_like(act), "kd_covered_active": act & res["avail"]["genetic"],
            "strict_new_active": act & res["strict_new"], "exclude_promiscuous_active": act & (res["n_signed"] <= 16)}


def b_populations(res: dict) -> dict:
    allc = np.ones(len(res["entity"]), bool)
    return {"primary_all": allc, "landmark": res["landmark"], "pharm_available": res["avail"]["pharm"]}


def relabel_delta(res: dict, mask: np.ndarray) -> float:
    return float(entity_means(res["scores"]["F"] - res["scores"]["O"], res["entity"], mask)[1].mean())


# ------------------------------------------------------------------------------------------- stages

def knowledge_tok(A: TaskA, K) -> None:
    A.knowledge_tok = K.tok


def stage(outer: list, label: str, controls: bool, n_relabel: int) -> dict:
    t0 = time.time()
    W = build()
    A, B, ck = W["A"], W["B"], W["ck"]
    KA = A.knowledge(ck)
    knowledge_tok(A, KA)
    out = {"stage": label, "outer_folds": outer, "python": platform.python_version(), "numpy": np.__version__}

    ra = run_a(A, KA, outer, "real")
    pa = a_populations(A, ra)
    out["A"] = summarise(ra, pa, A_ORBIT)
    out["A"]["gate_info"] = ra["gate_info"]
    rb = run_b(B, B.knowledge(), outer, "real")
    pb_full, pb_nt = b_populations(rb["full"]), b_populations(rb["nontrivial"])
    out["B_full"] = summarise(rb["full"], pb_full, B_FULL)
    out["B_nontrivial"] = summarise(rb["nontrivial"], pb_nt, B_NT)
    out["B_full"]["gate_info"] = rb["full"]["gate_info"]
    out["B_nontrivial"]["gate_info"] = rb["nontrivial"]["gate_info"]
    print(f"[{label}] real done {time.time() - t0:.0f}s", flush=True)

    rel = {"A": [], "B_full": [], "B_nontrivial": []}
    for s in range(n_relabel):
        Kr = A.knowledge(ck, gene_map=A.global_gene_perm(s), cp_perm=A.global_compound_perm(s))
        rr = run_a(A, Kr, outer, f"relabel{s}", ablate=())
        rel["A"].append(relabel_delta(rr, pa["primary_active"]))
        rbr = run_b(B, B.knowledge(**B.global_perms(s)), outer, f"relabel{s}",
                    pipelines=(("full", B_FULL, ()), ("nontrivial", B_NT, ())))
        rel["B_full"].append(relabel_delta(rbr["full"], pb_full["primary_all"]))
        rel["B_nontrivial"].append(relabel_delta(rbr["nontrivial"], pb_nt["primary_all"]))
        print(f"[{label}] relabel {s} done {time.time() - t0:.0f}s", flush=True)
    out["relabel_delta_id_F"] = rel

    if controls:
        out["controls"] = run_controls(W, ra, pa, rb, pb_nt, outer)
        print(f"[{label}] controls done {time.time() - t0:.0f}s", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    return out


def run_controls(W: dict, ra: dict, pa: dict, rb: dict, pb: dict, outer: list) -> dict:
    A, B, ck = W["A"], W["B"], W["ck"]
    L = A.L
    rng = rng_for("context-derangement")
    der = np.roll(np.arange(L), 1 + int(rng.integers(0, L - 1)))
    res = {}
    real_a = relabel_delta(ra, pa["primary_active"])
    # sign contradiction (A' genetic)
    K = A.knowledge(ck)
    K.signed = [[(r, -s) for r, s in x] for x in K.signed]
    r = run_a(A, K, outer, "signflip", ablate=())
    m = pa["primary_active"] & r["avail"]["genetic"]
    res["A_sign_contradiction"] = {"mean_contrast_genetic_real": float(ra["contrast"]["genetic"][m].mean()),
                                   "mean_contrast_genetic_flipped": float(r["contrast"]["genetic"][m].mean()),
                                   "delta_id_F": relabel_delta(r, pa["primary_active"]), "delta_id_F_real": real_a}
    # context permutation (A' genetic reads KD from another line)
    r = run_a(A, A.knowledge(ck, kd_line=der), outer, "context", ablate=())
    res["A_context_permutation"] = {"delta_id_F": relabel_delta(r, pa["primary_active"]), "delta_id_F_real": real_a,
                                    "derangement": der.tolist()}
    # evidence withdrawal (50% of each compound's targets and MoA tokens)
    wr = rng_for("withdraw-A")
    signed = [{g: s for g, s in x.items() if wr.random() < 0.5} for x in ck.signed]
    tokens = [frozenset(t for t in ts if not t.startswith("t:") and wr.random() < 0.5) | {"t:" + g for g in sg}
              for ts, sg in zip(ck.tokens, signed)]
    ckw = replace(ck, signed=signed, tokens=tokens)
    Aw = TaskA(A.z, ckw, A.fps, A.kd_degree)
    Kw = Aw.knowledge(ckw)
    Aw.knowledge_tok = A.knowledge_tok           # strict-new flags stay defined by the real knowledge
    Aw.annotated = A.annotated                   # population fixed by the real knowledge
    r = run_a(Aw, Kw, outer, "withdraw", ablate=())
    res["A_evidence_withdrawal"] = {"delta_id_F": relabel_delta(r, pa["primary_active"]), "delta_id_F_real": real_a}
    # source snapshot: Hub 2020 only (MAP-KG excluded by availability date)
    ck20 = S.compile_compounds(W["store"], W["ents"], as_of="2020-12-31")
    A20 = TaskA(A.z, ck20, A.fps, A.kd_degree)
    K20 = A20.knowledge(ck20)
    A20.knowledge_tok = A.knowledge_tok
    keep = A20.annotated.copy()
    A20.annotated = A.annotated & keep
    r = run_a(A20, K20, outer, "snapshot", ablate=())
    both = pa["primary_active"] & keep[ra["entity"]]
    both_r = r["active"] & keep[r["entity"]]
    res["A_source_snapshot_hub2020"] = {"delta_id_F": relabel_delta(r, both_r), "delta_id_F_real_same_compounds": relabel_delta(ra, both)}
    # B: context permutation and withdrawal on the pharm route
    real_b = relabel_delta(rb, pb["primary_all"])
    r = run_b(B, B.knowledge(pharm_line=der), outer, "context", pipelines=(("nontrivial", B_NT, ()),))["nontrivial"]
    res["B_context_permutation"] = {"delta_id_F": relabel_delta(r, pb["primary_all"]), "delta_id_F_real": real_b}
    keepm = rng_for("withdraw-B").random(B.S.shape) < 0.5
    r = run_b(B, B.knowledge(withdraw=keepm), outer, "withdraw", pipelines=(("nontrivial", B_NT, ()),))["nontrivial"]
    res["B_evidence_withdrawal"] = {"delta_id_F": relabel_delta(r, pb["primary_all"]), "delta_id_F_real": real_b}
    return res


def gates_s1(out: dict) -> dict:
    a = out["A"]["primary_active"]["contrasts"]["F-O"]
    v1 = out["B_full"]["landmark"]["ablations"]["F-(F-self)"]
    sp = out["B_full"]["certificates"]["self"]["spearman_identity_gate"]
    units_a = out["A"]["primary_active"]["entities"] * 4
    units_b = out["B_nontrivial"]["primary_all"]["entities"] * 4
    return {"V1_dev": {"landmark_F_minus_F_without_self": v1, "spearman_identity_gate_self": sp,
                       "pass": bool(v1.get("difference", 0) > 0 and v1.get("p_greater", 1) < 0.001 and sp > 0)},
            "power": {"A": power(a, units_a), "B": power(out["B_nontrivial"]["primary_all"]["contrasts"]["F-O"], units_b)}}


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("s0", "s1", "s2"))
    args = ap.parse_args()
    if args.stage == "s0":
        import synthetic
        res = synthetic.run()
        (HERE / "RESULTS_S0.json").write_text(json.dumps(jsonable(res), indent=1) + "\n", encoding="utf-8", newline="\n")
        print("S0", "PASS" if res["passed"] else "FAIL")
        return 0 if res["passed"] else 1
    if args.stage == "s1":
        out = stage([0], "S1 development", controls=False, n_relabel=1)
        out.update(gates_s1(out))
        (HERE / "RESULTS_S1.json").write_text(json.dumps(jsonable(out), indent=1) + "\n", encoding="utf-8", newline="\n")
        power_out = {"stage": "S1", "A": out["power"]["A"], "B": out["power"]["B"], "mei": MEI}
        (HERE / "POWER.json").write_text(json.dumps(jsonable(power_out), indent=1) + "\n", encoding="utf-8", newline="\n")
        print("S1 V1", "PASS" if out["V1_dev"]["pass"] else "FAIL")
        return 0
    import freeze
    freeze.require_freeze()
    target = HERE / "RESULTS.json"
    if target.exists():
        raise SystemExit("RESULTS_ALREADY_WRITTEN: S2 is write-once")
    out = stage([1, 2, 3, 4], "S2 validation", controls=True, n_relabel=N_RELABEL)
    target.write_text(json.dumps(jsonable(out), indent=1) + "\n", encoding="utf-8", newline="\n")
    print("S2 written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
