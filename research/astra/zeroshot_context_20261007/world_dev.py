"""Development-only analysis: signal audit, ladder selection, controls, leakage diagnostic, delta_min.

Reads the two development held-out lines and the training panel only; writes world_dev/DEV_RESULTS.json.
Every error is depth-corrected (see world_models). Evaluation lines are never loaded here.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402

OUT = HERE / "world_dev"
M0_VARIANTS = ("equal", "precision")


def panel_keys():
    """(label, plate) groups of the held-out contexts, from the metadata census only."""
    keys = set()
    for name, file in wm.HELDOUT.items():
        census = json.loads((HERE / "census" / f"{file}.json").read_text(encoding="utf-8"))
        keys |= {(label, plate) for label, plate, n in census["condition_plate_counts"] if label != wm.CONTROL}
    return sorted(keys)


def components(panel, t, lam):
    """Forecast pieces and their sampling-noise algebra for one held-out line's eligible groups."""
    e = t["eligible"]
    cols = t["panel_index"][e]
    out = {"cols": cols, "obs": t["delta"][e], "noise_L": t["noise"][e], "devS": t["devS"][e], "S": t["S"][e],
           "S_raw": t["S_raw"][e], "keys": [k for k, ok in zip(t["keys"], e) if ok],
           "state_mean": panel.state_mean[cols]}
    dev_weights = {"knn": panel.w_knn_dev(t["basal"]), "krr": panel.w_krr_dev(t["basal"], lam)}
    for v in M0_VARIANTS:
        W0 = panel.w_m0(v)
        out[f"P0_{v}"] = panel.apply(W0, cols)
        out[f"n00_{v}"] = panel.noise_of(W0, cols)
        for d, Wd in dev_weights.items():
            out[f"n0d_{v}_{d}"] = (W0[:, cols] * Wd[:, cols] * panel.noise0[:, cols]).sum(0)
        # Gene-gated panel mean: per-coordinate response regressed on that coordinate's basal level.
        g, g0d, gdd = panel.gate(t["basal"], W0, cols, 0.0)
        out[f"D_gate_{v}"], out[f"n0d_{v}_gate"], out[f"ndd_gate_{v}"] = g, g0d, gdd
    for d, Wd in dev_weights.items():
        out[f"D_{d}"] = panel.apply(Wd, cols)
        out[f"ndd_{d}"] = panel.noise_of(Wd, cols)
    return out


def se_model(c, v, dev=None, gk=0.0, gs=0.0, state_term=None):
    pred = c[f"P0_{v}"].copy()
    noise = c[f"n00_{v}"].copy()
    if dev is not None and gk:
        D = c[f"D_{dev}_{v}"] if f"D_{dev}_{v}" in c else c[f"D_{dev}"]
        ndd = c[f"ndd_{dev}_{v}"] if f"ndd_{dev}_{v}" in c else c[f"ndd_{dev}"]
        pred += gk * D
        noise += 2 * gk * c[f"n0d_{v}_{dev}"] + gk * gk * ndd
    if gs:
        pred += gs * (c["devS"] if state_term is None else state_term)
    return wm.corrected_se(pred, c["obs"], noise, c["noise_L"])


def pooled(dev, fn):
    values, clusters, lines = [], [], []
    for name, c in dev.items():
        v = fn(c)
        values.append(v)
        clusters += [wm.drug_of(k) for k in c["keys"]]
        lines += [name] * len(v)
    return np.concatenate(values), np.array(clusters), np.array(lines)


def contrast(dev, fa, fb):
    a, cl, ln = pooled(dev, fa)
    b, _, _ = pooled(dev, fb)
    diff = a - b
    lo, hi = wm.cluster_bootstrap(diff, cl)
    return {"mean": float(diff.mean()), "ci95_drug_clustered": [lo, hi],
            "per_line": {n: float(diff[ln == n].mean()) for n in dev}, "groups": int(len(diff)), "drugs": int(len(set(cl)))}


def audit(c, v):
    """Noise-aware signal decomposition on one development line (eligible groups, infinite-depth M0)."""
    obs, nL = c["obs"], c["noise_L"]
    m0, n0 = c[f"P0_{v}"], c[f"n00_{v}"]
    total = np.mean(obs ** 2, 1) - nL
    deviation = np.mean((obs - m0) ** 2, 1) - nL - n0
    scale = float(np.sum((obs - m0) * m0) / np.sum(m0 * m0))
    dose = np.array([wm.dose_of(k) for k in c["keys"]])
    by_dose = {d: {"groups": int((dose == d).sum()), "mean_total": float(total[dose == d].mean()),
                   "mean_deviation": float(deviation[dose == d].mean()), "mean_noise_L": float(nL[dose == d].mean())}
               for d in sorted(set(dose))}
    return {"groups": int(len(obs)), "mean_noise_L": float(nL.mean()), "median_noise_L": float(np.median(nL)),
            "mean_M0_sampling_noise": float(n0.mean()),
            "mean_total_energy": float(total.mean()), "median_total_energy": float(np.median(total)),
            "mean_deviation_energy": float(deviation.mean()), "median_deviation_energy": float(np.median(deviation)),
            "deviation_fraction_of_total": float(deviation.mean() / total.mean()),
            "line_scaling_of_M0": scale, "by_dose": by_dose}


def split_half(t, c, v):
    """Disjoint treated halves against disjoint control halves: unbiased reproducible energies."""
    e = t["eligible"]
    a, b = t["deltaA"][e], t["deltaB"][e]
    ok = np.isfinite(a).all(1) & np.isfinite(b).all(1)
    m0, n0 = c[f"P0_{v}"][ok], c[f"n00_{v}"][ok]
    return {"groups": int(ok.sum()), "reproducible_total_energy": float(np.mean(np.mean(a[ok] * b[ok], 1))),
            "reproducible_deviation_energy": float(np.mean(np.mean((a[ok] - m0) * (b[ok] - m0), 1) - n0)),
            "reproducible_devS_alignment": float(np.mean(np.mean(c["devS"][ok] * ((a[ok] + b[ok]) / 2 - m0), 1)))}


def replicate_wells(c, v):
    """Same label in two plates: cross-well reproducibility of the deviation (independent wells)."""
    index = {}
    for i, k in enumerate(c["keys"]):
        index.setdefault(k[0], []).append(i)
    pairs = [v2[:2] for v2 in index.values() if len(v2) >= 2]
    if not pairs:
        return {"pairs": 0}
    m0, n0 = c[f"P0_{v}"], c[f"n00_{v}"]
    cross, within, dev_align = [], [], []
    for i, j in pairs:
        ei, ej = c["obs"][i] - m0[i], c["obs"][j] - m0[j]
        cross.append(np.mean(ei * ej))  # panel noise is independent across wells (different plates)
        within.append((np.mean(ei ** 2) - c["noise_L"][i] - n0[i] + np.mean(ej ** 2) - c["noise_L"][j] - n0[j]) / 2)
        dev_align.append((np.mean(c["devS"][i] * ej) + np.mean(c["devS"][j] * ei)) / 2)
    return {"pairs": len(pairs), "cross_well_deviation_energy": float(np.mean(cross)),
            "within_well_deviation_energy": float(np.mean(within)),
            "reproducible_fraction": float(np.mean(cross) / np.mean(within)),
            "devS_alignment_with_other_well_deviation": float(np.mean(dev_align))}


def leakage_diagnostic(panel, chunk=150):
    """STATE vs leave-one-out panel mean on the TRAINING contexts it was fitted to (in-sample)."""
    rows = []
    for li in range(len(panel.files)):
        Wm = panel.avail.copy()
        Wm[li] = False
        Wm = Wm / np.maximum(Wm.sum(0), 1)
        cols = np.flatnonzero(panel.avail[li] & (panel.coverage >= wm.MIN_PANEL_LINES))
        s_state, s_m0, s_zero = [], [], []
        for a in range(0, len(cols), chunk):
            cc = cols[a:a + chunk]
            obs = panel.delta[li, cc].astype(np.float64)
            pred = np.einsum("lk,lkd->kd", Wm[:, cc], panel.delta[:, cc], optimize=True)
            nm = (Wm[:, cc] ** 2 * panel.noise0[:, cc]).sum(0)
            nl = panel.noise0[li, cc]
            s_m0.append(np.mean((pred - obs) ** 2, 1) - nm - nl)
            s_state.append(np.mean((panel.state[li, cc] - obs) ** 2, 1) - nl)
            s_zero.append(np.mean(obs ** 2, 1) - nl)
        s_state, s_m0, s_zero = map(np.concatenate, (s_state, s_m0, s_zero))
        rows.append({"file": panel.files[li], "groups": int(len(cols)), "STATE_in_sample": float(s_state.mean()),
                     "M0_leave_one_out": float(s_m0.mean()), "no_change": float(s_zero.mean())})
    ratio = [r["STATE_in_sample"] / r["M0_leave_one_out"] for r in rows if r["M0_leave_one_out"] > 0]
    return {"per_context": rows, "median_ratio_STATE_over_M0": float(np.median(ratio)),
            "interpretation": "In-sample: STATE was trained on these contexts' full-depth cells. A held-out ratio near the in-sample ratio would be consistent with leakage or with perfect transfer; a clearly worse held-out ratio is what genuine holdout predicts."}


def main():
    OUT.mkdir(exist_ok=True)
    started = time.perf_counter()
    panel = wm.Panel(panel_keys())
    lam, lam_errors = panel.select_krr_lambda()
    raw = {name: wm.target(name, panel) for name in wm.SPLIT["development"]}
    dev = {name: components(panel, t, lam) for name, t in raw.items()}
    R = {"created_utc": datetime.now(timezone.utc).isoformat(), "development_lines": list(dev),
         "training_contexts": len(panel.files), "panel_keys": len(panel.keys),
         "panel_coverage_median": float(np.median(panel.coverage)),
         "eligible_groups": {n: int(len(c["obs"])) for n, c in dev.items()},
         "krr_lambda": {"selected": lam, "leave_one_context_out_errors": lam_errors, "data": "training contexts only"},
         "error_scale": "depth-corrected mean squared error per group, averaged over the 2,000 native coordinates"}
    m0_scores = {v: float(pooled(dev, lambda c, v=v: se_model(c, v))[0].mean()) for v in M0_VARIANTS}
    v = min(m0_scores, key=m0_scores.get)
    R["M0"] = {"scores": m0_scores, "selected": v,
               "no_change": float(pooled(dev, lambda c: np.mean(c["obs"] ** 2, 1) - c["noise_L"])[0].mean())}
    m1_scores = {f"{d}:{g}": float(pooled(dev, lambda c, d=d, g=g: se_model(c, v, d, gk=g))[0].mean())
                 for d in ("knn", "krr", "gate") for g in wm.GAMMAS}
    best = min(m1_scores, key=m1_scores.get)
    dk, gk = best.split(":")[0], float(best.split(":")[1])
    R["M1"] = {"scores": m1_scores, "selected_family": dk, "selected_gamma_K": gk}
    m2_scores = {str(g): float(pooled(dev, lambda c, g=g: se_model(c, v, gs=g))[0].mean()) for g in wm.GAMMAS}
    gs = float(min(m2_scores, key=m2_scores.get))
    m21_scores = {str(g): float(pooled(dev, lambda c, g=g: se_model(c, v, dk, gk=gk, gs=g))[0].mean()) for g in wm.GAMMAS}
    gs21 = float(min(m21_scores, key=m21_scores.get))
    R["M2"] = {"scores": m2_scores, "selected_gamma_S": gs}
    R["M21"] = {"scores": m21_scores, "selected_gamma_S": gs21}
    names = list(dev)
    for i, n in enumerate(names):
        other = dev[names[(i + 1) % len(names)]]
        okeys = {k: j for j, k in enumerate(other["keys"])}
        dev[n]["devS_swap"] = np.array([other["devS"][okeys[k]] if k in okeys else np.zeros(2000) for k in dev[n]["keys"]])
        rng = np.random.default_rng(20261007)
        strata = {}
        for j, k in enumerate(dev[n]["keys"]):
            strata.setdefault((wm.dose_of(k), k[1]), []).append(j)
        perm = np.arange(len(dev[n]["keys"]))
        for members in strata.values():
            perm[members] = rng.permutation(members)
        dev[n]["devS_perm"] = dev[n]["devS"][perm]
    gsel = gs if gs > 0 else 1.0
    M0 = lambda c: se_model(c, v)
    C = {"gamma_used_for_controls": gsel}
    C["M2_selected_minus_M0"] = contrast(dev, lambda c: se_model(c, v, gs=gs), M0)
    C["M2g_minus_M0"] = contrast(dev, lambda c: se_model(c, v, gs=gsel), M0)
    C["M1_selected_minus_M0"] = contrast(dev, lambda c: se_model(c, v, dk, gk=gk), M0)
    C["M21_minus_M1"] = contrast(dev, lambda c: se_model(c, v, dk, gk=gk, gs=gs21), lambda c: se_model(c, v, dk, gk=gk))
    C["M2g_minus_lineswap"] = contrast(dev, lambda c: se_model(c, v, gs=gsel), lambda c: se_model(c, v, gs=gsel, state_term=c["devS_swap"]))
    C["M2g_minus_permuted"] = contrast(dev, lambda c: se_model(c, v, gs=gsel), lambda c: se_model(c, v, gs=gsel, state_term=c["devS_perm"]))
    C["STATE_direct_minus_M0"] = contrast(dev, lambda c: np.mean((c["S"] - c["obs"]) ** 2, 1) - c["noise_L"], M0)
    C["STATE_raw_direct_minus_M0"] = contrast(dev, lambda c: np.mean((c["S_raw"] - c["obs"]) ** 2, 1) - c["noise_L"], M0)
    C["STATE_panel_mean_minus_M0"] = contrast(dev, lambda c: np.mean((c["state_mean"] - c["obs"]) ** 2, 1) - c["noise_L"], M0)
    C["M0_minus_no_change"] = contrast(dev, M0, lambda c: np.mean(c["obs"] ** 2, 1) - c["noise_L"])
    for n, c in dev.items():
        m0 = c[f"P0_{v}"]
        coef = np.sum(c["devS"] * m0, 1) / np.maximum(np.sum(m0 * m0, 1), 1e-12)
        c["devS_scale"] = coef[:, None] * m0
        c["devS_orth"] = c["devS"] - c["devS_scale"]
    C["M2g_scale_part_minus_M0"] = contrast(dev, lambda c: se_model(c, v, gs=gsel, state_term=c["devS_scale"]), M0)
    C["M2g_orthogonal_part_minus_M0"] = contrast(dev, lambda c: se_model(c, v, gs=gsel, state_term=c["devS_orth"]), M0)
    C["M2g_on_gate_minus_gate"] = contrast(dev, lambda c: se_model(c, v, "gate", gk=1.0, gs=gsel), lambda c: se_model(c, v, "gate", gk=1.0))
    R["development_contrasts"] = C
    R["per_line"] = {}
    for n, c in dev.items():
        R["per_line"][n] = {"audit": audit(c, v), "split_half": split_half(raw[n], c, v),
                            "replicate_wells": replicate_wells(c, v),
                            "mean_corrected_se": {"no_change": float(np.mean(np.mean(c["obs"] ** 2, 1) - c["noise_L"])),
                                                  "M0": float(se_model(c, v).mean()),
                                                  **{f"M2_g{g}": float(se_model(c, v, gs=g).mean()) for g in wm.GAMMAS},
                                                  **{f"M1_{dk}_g{g}": float(se_model(c, v, dk, gk=g).mean()) for g in wm.GAMMAS},
                                                  "STATE_direct": float(np.mean(np.mean((c["S"] - c["obs"]) ** 2, 1) - c["noise_L"]))}}
    R["leakage_diagnostic_training_contexts"] = leakage_diagnostic(panel)
    held = {n: R["per_line"][n]["mean_corrected_se"]["STATE_direct"] / R["per_line"][n]["mean_corrected_se"]["M0"] for n in dev}
    R["leakage_diagnostic_training_contexts"]["heldout_development_ratio_STATE_over_M0"] = held
    fw = np.concatenate([raw[n]["full_well_noise"][raw[n]["eligible"]] for n in dev])
    R["delta_min"] = {"value": float(np.median(fw)), "groups": int(len(fw)),
                      "formula": "median over development eligible groups of mean_g var_T/N_T(full well) + mean_g var_C/N_C(full plate)"}
    R["seconds"] = round(time.perf_counter() - started, 2)
    (OUT / "DEV_RESULTS.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
    print(json.dumps(R, indent=1))


if __name__ == "__main__":
    main()
