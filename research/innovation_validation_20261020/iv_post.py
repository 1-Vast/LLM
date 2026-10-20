"""Summaries from stored stream outputs only (no refit, no API, no re-evaluation). `build_summary(run_dir, cfg)` is deterministic; the verifier recomputes it."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import iv_stats as ST  # noqa: E402

MECH = ("alias", "compose")
CONTROLS = ("null", "lowrank")


def _contrasts(tab, sids_by_group, specs, level, delta, seed, primary_names=()):
    out = []
    for name, a, b in specs:
        for gname, sids in sids_by_group.items():
            d = ST.paired(tab, sids, a, b)
            row = ST.contrast_row(f"{name} [{gname}]", d, level, delta, seed, primary=(name in primary_names and gname == "mechanism(alias+compose)"))
            row.update({"name": name, "group": gname})
            out.append(row)
    return out


def build_summary(run_dir: Path, cfg: dict) -> dict:
    streams = ST.load_streams(run_dir)
    delta = cfg["margin"]["value"]
    gen_min = cfg["task"]["gen_min"]
    comp = cfg["comparators"]
    lvl_p, lvl_s = ST.LEVEL_PRIMARY, ST.LEVEL_SECONDARY
    E = ST.task_table(streams, "E", gen_min)
    T = ST.task_table(streams, "T", gen_min)
    FO = ST.task_table(streams, "FO", gen_min)
    orc = ST.oracle_table(streams, "E", gen_min)
    groups = {"mechanism(alias+compose)": ST.sids_of(E, MECH), "alias": ST.sids_of(E, ("alias",)), "compose": ST.sids_of(E, ("compose",)),
              "null": ST.sids_of(E, ("null",)), "lowrank": ST.sids_of(E, ("lowrank",)), "all_kinds": ST.sids_of(E, ("null", "lowrank", "alias", "compose"))}
    dec_groups = {"mechanism_decoupled": ST.sids_of(E, MECH, dec=True), "alias_decoupled": ST.sids_of(E, ("alias",), dec=True), "compose_decoupled": ST.sids_of(E, ("compose",), dec=True)}
    out = {"config_margin": delta, "n_streams": len(streams)}
    # ---- arm means
    out["arm_means_E"] = {g: ST.arm_means(E, s) for g, s in {**groups, **dec_groups}.items() if s}
    out["arm_means_T"] = {g: ST.arm_means(T, s) for g, s in {**groups, **dec_groups}.items() if s}
    out["arm_means_FO"] = {g: ST.arm_means(FO, s) for g, s in groups.items() if s}
    out["oracle_E_mean"] = {g: float(np.nanmean([orc[s] for s in sids])) for g, sids in {**groups, **dec_groups}.items() if sids}
    # ---- primary contrasts (contract E), pre-specified comparators
    prim = [("H1 diagnostic acquisition: inh_kg - strongest conventional", "inh_kg", comp["H1_primary"]),
            ("H2 inheritance: inh_kg - rst_kg", "inh_kg", "rst_kg"),
            ("H3 joint: inh_pol - best single adaptation", "inh_pol", comp["H3_comparator"])]
    names = [p[0] for p in prim]
    out["primary_E"] = _contrasts(E, groups, prim, lvl_p, delta, 11, primary_names=names)
    # ---- secondary contrasts
    sec = [("H1a acquisition rule on the same library: inh_kg - " + comp["H1a_policy_arm"], "inh_kg", comp["H1a_policy_arm"]),
           ("H1 vs direct measurement: inh_kg - direct", "inh_kg", "direct"),
           ("H1 vs latent+aopt: inh_kg - lat_aopt", "inh_kg", "lat_aopt"),
           ("H1 vs GBM+UCB: inh_kg - gbm_ucb", "inh_kg", "gbm_ucb"),
           ("H1 vs broad capacity: inh_kg - broadcap_bald", "inh_kg", "broadcap_bald"),
           ("H1 vs exploit on the same library: inh_kg - inh_exploit", "inh_kg", "inh_exploit"),
           ("H1 vs best-of conventional (post hoc, per stream)", "inh_kg", ["gbm_var", "gbm_ucb", "gbm_exploit", "lat_aopt", "lat_var", "broadcap_bald", "direct", "inh_bald", "inh_var", "inh_rand", "inh_exploit"]),
           ("no-probe prior: inh_kg - prior", "inh_kg", "prior"),
           ("policy adaptation only: fix_pol - fix_kg", "fix_pol", "fix_kg"),
           ("library evolution only: inh_kg - fix_kg", "inh_kg", "fix_kg"),
           ("joint vs neither: inh_pol - fix_kg", "inh_pol", "fix_kg"),
           ("deletion ablation: inh_kg - inh_del_all", "inh_kg", "inh_del_all"),
           ("delete older gates: inh_kg - inh_del_old", "inh_kg", "inh_del_old"),
           ("transplant into broad-capacity baseline: broadcap_transplant - broadcap_bald", "broadcap_transplant", "broadcap_bald"),
           ("inheritance vs param-only: inh_kg - fix_kg", "inh_kg", "fix_kg")]
    out["secondary_E"] = _contrasts(E, groups, sec, lvl_s, delta, 21)
    # ---- witness-to-target break: the same contrasts on decoupled streams and the difference of differences
    dd = []
    for name, a, b in prim[:2] + sec[:1] + sec[11:12]:
        for kd in ("alias", "compose", "mechanism"):
            s_norm = ST.sids_of(E, MECH if kd == "mechanism" else (kd,))
            s_dec = ST.sids_of(E, MECH if kd == "mechanism" else (kd,), dec=True)
            if not s_dec:
                continue
            d_norm = {s: ST.paired(E, [s], a, b) for s in s_norm}
            d_dec = {s.replace("_dec", ""): ST.paired(E, [s], a, b) for s in s_dec}
            common = [s for s in d_norm if s in d_dec and len(d_norm[s]) and len(d_dec[s])]
            if len(common) < 3:
                continue
            x = np.array([d_norm[s][0] for s in common])
            y = np.array([d_dec[s][0] for s in common])
            lo, hi = ST.boot_ci(x - y, lvl_s, 31)
            dd.append({"contrast": name, "kind": kd, "n_pairs": len(common), "gain_normal": float(x.mean()), "gain_decoupled": float(y.mean()),
                       "difference_of_differences": float((x - y).mean()), "ci95": [lo, hi]})
    out["witness_break"] = dd
    # ---- other contracts
    out["transfer_T"] = _contrasts(T, groups, [("H1 T: inh_kg - lat_aopt", "inh_kg", "lat_aopt"), ("H1 T: inh_kg - gbm_ucb", "inh_kg", "gbm_ucb"),
                                               ("H1 T: inh_kg - broadcap_bald", "inh_kg", "broadcap_bald"), ("H1 T: inh_kg - inh_var", "inh_kg", "inh_var"),
                                               ("H2 T: inh_kg - rst_kg", "inh_kg", "rst_kg"), ("T: inh_kg - prior", "inh_kg", "prior")], lvl_s, delta, 41)
    out["fixed_observation_FO"] = _contrasts(FO, groups, [("FO: inh_kg - lat_aopt", "inh_kg", "lat_aopt"), ("FO: inh_kg - broadcap_bald", "inh_kg", "broadcap_bald"),
                                                         ("FO: inh_kg - rst_kg", "inh_kg", "rst_kg"), ("FO: inh_kg - prior", "inh_kg", "prior")], lvl_s, delta, 51)
    # ---- headroom (paired per stream; oracle and method taken from the same cells, pools and streams)
    head = {}
    for g, sids in groups.items():
        if not sids:
            continue
        o = np.array([orc[s] for s in sids])
        head[g] = {a: float(np.mean(o - np.array([E[s][a] for s in sids]))) for a in ("prior", "direct", "inh_kg", "lat_aopt", "gbm_ucb") if all(a in E[s] for s in sids)}
    out["paired_headroom_E"] = head
    # ---- budget-utility curves and measurements to a fixed target
    curves = {}
    for g, sids in groups.items():
        if not sids:
            continue
        cur = {}
        for arm in ("inh_kg", "rst_kg", "lat_aopt", "direct"):
            pts = {}
            for bud, key in ((0, "prior"), (2, f"{arm}@B2"), (4, arm), (8, f"{arm}@B8")):
                vals = [E[s][key] for s in sids if key in E[s]]
                if vals:
                    pts[str(bud)] = float(np.mean(vals))
            cur[arm] = pts
        gap = np.mean([orc[s] - E[s]["prior"] for s in sids])
        target = float(np.mean([E[s]["prior"] for s in sids]) + 0.5 * gap)
        cur["target_utility_half_gap"] = target
        cur["budget_to_target"] = {arm: next((int(b) for b, v in sorted(cur[arm].items(), key=lambda kv: int(kv[0])) if v >= target), None) for arm in ("inh_kg", "rst_kg", "lat_aopt", "direct")}
        curves[g] = cur
    out["budget_curves_E"] = curves
    # ---- H5: marginal value of the deployed library on never-released anchors across checkpoints
    A = ST.anchor_table(streams)
    h5 = {}
    for g, sids in groups.items():
        if g not in ("alias", "compose", "mechanism(alias+compose)"):
            continue

        def V(role, gen):
            return np.array([A[s][(role, "inh_kg", gen)] - A[s][(role, "inh_del_all", gen)] for s in sids if (role, "inh_kg", gen) in A[s] and (role, "inh_del_all", gen) in A[s]])

        def U(role, arm, gen):
            return np.array([A[s][(role, arm, gen)] for s in sids if (role, arm, gen) in A[s]])
        growth = V("A_new", 4) - V("A_new", 1)
        retention = V("A_old", 4) - V("A_old", 2)
        vs_restart_new = U("A_new", "inh_kg", 4) - U("A_new", "rst_kg", 4)
        vs_restart_old = U("A_old", "inh_kg", 4) - U("A_old", "rst_kg", 4)
        row = {"value_of_library_A_new_by_checkpoint": {str(gk): float(V("A_new", gk).mean()) for gk in (1, 2, 3, 4)},
               "value_of_library_A_old_by_checkpoint": {str(gk): float(V("A_old", gk).mean()) for gk in (1, 2, 3, 4)},
               "growth_A_new_cp4_minus_cp1": ST.contrast_row("growth", growth, lvl_s, delta, 61, primary=False),
               "retention_A_old_cp4_minus_cp2": ST.contrast_row("retention", retention, lvl_s, delta, 62, primary=False),
               "inh_minus_restart_A_new_cp4": ST.contrast_row("A_new inh-rst", vs_restart_new, lvl_s, delta, 63),
               "inh_minus_restart_A_old_cp4": ST.contrast_row("A_old inh-rst", vs_restart_old, lvl_s, delta, 64),
               "bounded": True}
        h5[g] = row
    out["H5_anchors"] = h5
    # ---- library lifecycle statistics (what was deployed, how often, what was proposed)
    life = {}
    for arm in ("inh_kg", "inh_pol", "rst_kg", "fix_kg", "fix_pol"):
        dep = prop = demo = nonin = ret = 0
        for s, d in streams.items():
            if ST.is_dec(s):
                continue
            for g in d["generation_records"][arm]:
                prop += g["n_candidates"]
                dep += int(g["deployed_at_checkpoint"] is not None)
                for c in g["candidates"]:
                    if c.get("fit"):
                        demo += c["status"] == "demonstrated"
                        nonin += c["status"] == "noninferior"
                        ret += c["status"] == "retired"
        n_gen = sum(len(d["generation_records"][arm]) for s, d in streams.items() if not ST.is_dec(s))
        life[arm] = {"candidates_proposed": prop, "validated_demonstrated": int(demo), "noninferior": int(nonin), "retired": int(ret),
                     "generation_checkpoints_with_deployed_program": int(dep), "generation_checkpoints": n_gen}
    out["lifecycle"] = life
    # ---- resources
    res = {}
    for s, d in streams.items():
        for arm, sec_ in d["resources"]["seconds_by_arm"].items():
            res.setdefault(arm, 0.0)
            res[arm] += sec_
    out["resources_cpu_seconds_by_arm"] = {k: round(v, 1) for k, v in sorted(res.items())}
    out["resources_totals"] = {"stream_cpu_seconds": round(sum(d["resources"]["wall_seconds"] for d in streams.values()), 1),
                               "released_wells_per_stream": next(iter(streams.values()))["resources"]["released_wells"],
                               "deployment_probes_per_task": cfg["task"]["budget"],
                               "validation_replays": {a: int(sum(d["resources"]["validation_replays"][a] for d in streams.values())) for a in ("inh_kg", "inh_pol", "rst_kg", "fix_kg", "fix_pol")},
                               "candidate_evaluations": {a: int(sum(d["resources"]["candidate_evals"][a] for d in streams.values())) for a in ("inh_kg", "inh_pol", "rst_kg", "fix_kg", "fix_pol")}}
    return out


def _flat(prefix, v, out):
    if isinstance(v, dict):
        for k, x in v.items():
            _flat(f"{prefix}/{k}", x, out)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            _flat(f"{prefix}[{i}]", x, out)
    else:
        out[prefix] = v


def diff_summaries(a: dict, b: dict, tol: float = 1e-9):
    fa, fb = {}, {}
    _flat("", a, fa)
    _flat("", b, fb)
    bad = []
    for k in sorted(set(fa) | set(fb)):
        x, y = fa.get(k), fb.get(k)
        if isinstance(x, float) or isinstance(y, float):
            try:
                if not (abs(float(x) - float(y)) <= tol or (np.isnan(x) and np.isnan(y))):
                    bad.append(k)
            except (TypeError, ValueError):
                bad.append(k)
        elif x != y:
            bad.append(k)
    return bad


if __name__ == "__main__":
    run_dir = Path(sys.argv[1])
    cfg = json.loads((HERE / "CONFIG.json").read_text(encoding="utf-8"))
    summ = build_summary(run_dir, cfg)
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "SUMMARY.json"
    target.write_text(json.dumps(summ, indent=1, default=float) + "\n", encoding="utf-8")
    print("wrote", target)
