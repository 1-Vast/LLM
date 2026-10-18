"""Registered analysis of the Phase E records -> RESULTS.json (write-once) and the continue/stop decision.

File summary
- Path: research/feedback_propagation_20261018/analyse.py
- Purpose: apply PROTOCOL.md section 9 to records/E_fold{2,3,4}.json. Unit of analysis: mean difference per 64
  compounds from per-compound paired differences; interval: family-cluster bootstrap (4,000 draws, seed 20261018);
  one-sided p: family sign-flip; the confirmatory family {P1, P2} is Holm-adjusted. The practical threshold delta* is
  read from THRESHOLDS.json (derived from development data before this analysis ran).
- Contrasts (B = 3 pools, identical histories, unmeasured-pair nominations unless stated):
  - P1 update attribution: R1 - ridge-plus-feedback;
  - P2 conventional explanation: R1 - C* (kNN, K = 10);
  - P3 diagnosis: gated repair - ungated R1.
- Decision (PROTOCOL.md section 10): CONTINUE only if P1 is practically meaningful (Holm p < .05 and the lower
  95% bound >= delta*), P2 holds (Holm p < .05, lower bound > 0, point >= delta*) and P3 holds (p < .05, lower bound > 0,
  point >= delta*). Otherwise STOP, with the first failed condition named.
- Usage: ``python -B analyse.py`` (write-once).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import metrics as M
import seal
from bench import tc

HERE = Path(__file__).resolve().parent
REC = HERE / "records"
OUT = HERE / "RESULTS.json"
FOLDS = (2, 3, 4)
CONVENTIONAL = ("ridge", "mixture_mean", "empcov_0.1", "C_star_knn10", "knn20", "knn40", "forest")


def load() -> dict:
    return {f: json.loads((REC / f"E_fold{f}.json").read_text(encoding="utf-8")) for f in FOLDS}


def arrays(recs: dict, section: str, arm: str, kind: str, util: str) -> np.ndarray:
    """Concatenated per-compound utility (folds 2, 3, 4) of one arm."""

    out = []
    for f in FOLDS:
        node = recs[f]
        for part in section.split("/"):
            node = node[part]
        c = node[arm][kind]
        h = np.asarray(c["hits_c"], dtype=float)
        out.append((h > 0).astype(float) if util == "unique" else (np.asarray(c["measured_hits_c"], dtype=float) if util == "measured" else h))
    return np.concatenate(out)


def frame(recs: dict) -> tuple[np.ndarray, np.ndarray]:
    fam, keep = [], []
    for f in FOLDS:
        r = recs[f]
        fam += list(r["family"])
        keep.append(M.complete_mask(r["campaign_sizes"], r["campaign_index"]))
    return np.array(fam), np.concatenate(keep)


def contrast(recs, fr, a, b, kind="unmeasured", util="hits") -> dict:
    """a, b = (section, arm). Returns the paired family analysis and the campaign sign-flip."""

    d = arrays(recs, *a, kind, util) - arrays(recs, *b, kind, util)
    fam, keep = fr
    out = M.paired_family(d, fam, keep)
    camp = []
    off = 0
    for f in FOLDS:
        r = recs[f]
        for ix in r["campaign_index"]:
            if len(ix) == M.CAMPAIGN:
                camp.append(float(d[off:off + r["compounds"]][ix].sum()))
        off += r["compounds"]
    out["campaign"] = M.campaign_sign_flip(np.array(camp))
    return out


def rate(recs, fr, section, arm, kind="unmeasured", util="hits") -> float:
    a = arrays(recs, section, arm, kind, util)
    fam, keep = fr
    return float(a[keep].sum() / (keep.sum() / M.CAMPAIGN))


def analyse(recs: dict) -> dict:
    fr = frame(recs)
    thr = json.loads((HERE / "THRESHOLDS.json").read_text(encoding="utf-8"))
    delta = float(thr["delta_star_hits_per_64_compounds"])
    res: dict = {"delta_star": delta, "n_compounds": int(sum(recs[f]["compounds"] for f in FOLDS)),
                 "complete_campaign_compounds": int(fr[1].sum()), "complete_campaigns": int(fr[1].sum() // M.CAMPAIGN),
                 "data_status": "PRISM 19Q4 folds 2-4: exposed (opened by indication_triage_20261016 and by this study's audit); not an independent confirmation"}
    A = "A_B3"
    arm = lambda s, a: (s, a)

    # ---- rates per 64 compounds -------------------------------------------------------------
    arms_A = [a for a in recs[2][A] if not a.startswith("_") and a not in ("oracle",)]
    res["rates_B3"] = {a: {"unmeasured_hits": rate(recs, fr, A, a), "unmeasured_unique": rate(recs, fr, A, a, util="unique"),
                           "any_hits": rate(recs, fr, A, a, "any"), "any_measured_hits": rate(recs, fr, A, a, "any", "measured")}
                       for a in arms_A}
    res["rates_B3"]["oracle"] = {"unmeasured_hits": rate(recs, fr, A, "oracle"), "any_hits": rate(recs, fr, A, "oracle", "any")}
    res["unknown_nominations_B3"] = {a: int(sum(recs[f][A][a]["unmeasured"]["unknown"] for f in FOLDS)) for a in arms_A}

    # ---- confirmatory family ----------------------------------------------------------------
    P = {"P1_R1_vs_ridge": (arm(A, "R1"), arm(A, "ridge")), "P2_R1_vs_Cstar": (arm(A, "R1"), arm(A, "C_star_knn10")),
         "P3_gated_vs_R1": (arm(A, "gated"), arm(A, "R1"))}
    primary = {k: {"unmeasured_hits": contrast(recs, fr, *v), "unique_candidates": contrast(recs, fr, *v, util="unique"),
                   "any_hits": contrast(recs, fr, *v, kind="any")} for k, v in P.items()}
    holm = M.holm({"P1": primary["P1_R1_vs_ridge"]["unmeasured_hits"]["p_one_sided"], "P2": primary["P2_R1_vs_Cstar"]["unmeasured_hits"]["p_one_sided"]})
    res["primary"] = primary
    res["holm_P1_P2"] = holm

    # ---- secondary contrasts ----------------------------------------------------------------
    sec = {}
    for nm, (a, b) in {"ridge_vs_prior": ("ridge", "prior"), "R1_vs_prior": ("R1", "prior"), "Cstar_vs_ridge": ("C_star_knn10", "ridge"),
                       "R1_vs_mixture_mean": ("R1", "mixture_mean"), "R1_vs_empcov_0.1": ("R1", "empcov_0.1"), "R1_vs_forest": ("R1", "forest"),
                       "R1_vs_knn20": ("R1", "knn20"), "R1_vs_knn40": ("R1", "knn40"), "gated_vs_ridge": ("gated", "ridge"),
                       "mixture_vs_ridge": ("mixture_mean", "ridge")}.items():
        sec[nm] = {"unmeasured_hits": contrast(recs, fr, (A, a), (A, b)), "unique_candidates": contrast(recs, fr, (A, a), (A, b), util="unique")}
    best_conv = max(CONVENTIONAL, key=lambda c: rate(recs, fr, A, c))
    sec["R1_vs_best_conventional_on_E"] = {"comparator": best_conv, "unmeasured_hits": contrast(recs, fr, (A, "R1"), (A, best_conv)),
                                           "reading": "the comparator is chosen on the estimation folds (selection favours it)"}
    res["secondary"] = sec

    # ---- sensitivities ----------------------------------------------------------------------
    sens = {}
    for B in (2, 4):
        s = f"A_B{B}"
        sens[f"B{B}"] = {"R1_vs_ridge": contrast(recs, fr, (s, "R1"), (s, "ridge")), "R1_vs_Cstar": contrast(recs, fr, (s, "R1"), (s, "C_star_knn10")),
                         "Cstar_vs_ridge": contrast(recs, fr, (s, "C_star_knn10"), (s, "ridge")),
                         "rates": {a: rate(recs, fr, s, a) for a in ("prior", "ridge", "C_star_knn10", "R1")}}
    s = "C_logical16"
    sens["logical16"] = {"ridge_vs_prior": contrast(recs, fr, (s, "ridge"), (s, "prior")), "R1_vs_ridge": contrast(recs, fr, (s, "R1"), (s, "ridge")),
                         "R1_vs_prior": contrast(recs, fr, (s, "R1"), (s, "prior")),
                         "rates": {a: rate(recs, fr, s, a) for a in ("prior", "ridge", "C_star_knn10", "R1")}}
    s = "C_noise_seed2"
    sens["noise_seed2"] = {"R1_vs_ridge": contrast(recs, fr, (s, "R1"), (s, "ridge")), "R1_vs_Cstar": contrast(recs, fr, (s, "R1"), (s, "C_star_knn10")),
                           "rates": {a: rate(recs, fr, s, a) for a in ("prior", "ridge", "C_star_knn10", "R1")}}
    s = "C_deranged"
    sens["deranged"] = {"R1_real_vs_R1_deranged": contrast(recs, fr, (A, "R1"), (s, "R1")), "ridge_real_vs_ridge_deranged": contrast(recs, fr, (A, "ridge"), (s, "ridge")),
                        "R1_deranged_vs_prior": contrast(recs, fr, (s, "R1"), (A, "prior")),
                        "rates": {a: rate(recs, fr, s, a) for a in ("ridge", "C_star_knn10", "R1")}}
    curve = {}
    keep = fr[1]
    for b in ("1", "2", "3", "4"):
        curve[b] = {}
        for a in ("ridge", "C_star_knn10", "R1"):
            vals = np.concatenate([np.asarray(recs[f]["C_budget_curve"][b][a]["unmeasured"]["hits_c"], dtype=float) for f in FOLDS])
            curve[b][a] = float(vals[keep].sum() / (keep.sum() / M.CAMPAIGN))
    sens["budget_curve_common_target"] = curve
    res["sensitivity"] = sens

    # ---- closed loops (total decision utility) ----------------------------------------------
    cl = "B_closed_loops"
    loops = [a for a in recs[2][cl]]
    res["closed_loop_rates"] = {a: {"unmeasured_hits": rate(recs, fr, cl, a), "unmeasured_unique": rate(recs, fr, cl, a, util="unique"),
                                    "any_hits": rate(recs, fr, cl, a, "any"), "any_measured_hits": rate(recs, fr, cl, a, "any", "measured"),
                                    "lines_per_compound": float(np.mean([recs[f][cl][a]["_cost"]["lines_per_compound"] for f in FOLDS])),
                                    "pools_per_compound": float(np.mean([recs[f][cl][a]["_cost"]["pools_per_compound"] for f in FOLDS]))} for a in loops}
    res["closed_loop_rates"]["fixed_design_ridge"] = {"unmeasured_hits": rate(recs, fr, A, "ridge"), "any_hits": rate(recs, fr, A, "ridge", "any"),
                                                      "lines_per_compound": float(np.mean([recs[f][A]["_cost"]["lines_per_compound"] for f in FOLDS]))}
    res["closed_loop_rates"]["fixed_design_R1"] = {"unmeasured_hits": rate(recs, fr, A, "R1"), "any_hits": rate(recs, fr, A, "R1", "any")}
    pairs = {"loop_R1_vs_loop_ridge": ((cl, "loop_R1"), (cl, "loop_ridge")), "loop_R1_vs_loop_Cstar": ((cl, "loop_R1"), (cl, "loop_C_star_knn10")),
             "loop_Cstar_vs_loop_ridge": ((cl, "loop_C_star_knn10"), (cl, "loop_ridge")), "loop_gated_vs_loop_R1": ((cl, "loop_gated"), (cl, "loop_R1")),
             "loop_ridge_vs_two_stage": ((cl, "loop_ridge"), (cl, "two_stage_ridge")), "loop_R1_vs_fixed_R1": ((cl, "loop_R1"), (A, "R1")),
             "loop_ridge_vs_fixed_ridge": ((cl, "loop_ridge"), (A, "ridge"))}
    res["closed_loop_contrasts"] = {k: {"unmeasured_hits": contrast(recs, fr, *v), "any_hits": contrast(recs, fr, *v, kind="any")} for k, v in pairs.items()}

    # ---- hindsight diagnostics ----------------------------------------------------------------
    hs = {"gate_auc_by_fold": {str(f): recs[f]["D_hindsight"]["gate_auc_loss_difference_vs_truly_better"] for f in FOLDS},
          "share_R1_truly_better_than_ridge": {str(f): recs[f]["D_hindsight"]["share_R1_truly_better_than_ridge"] for f in FOLDS},
          "true_mse_mean": {str(f): recs[f]["D_hindsight"]["true_mse_mean"] for f in FOLDS},
          "best_of_rule_share": {str(f): recs[f]["D_hindsight"]["best_of_rule_share"] for f in FOLDS}}
    d = "D_hindsight"
    hs["hindsight_gate_vs_R1"] = contrast(recs, fr, (d, "hindsight_gate_R1_or_ridge"), (A, "R1"))
    hs["hindsight_best_of_rules_vs_R1"] = contrast(recs, fr, (d, "hindsight_best_of_rules"), (A, "R1"))
    hs["rates"] = {k: rate(recs, fr, d, k) for k in ("hindsight_gate_R1_or_ridge", "hindsight_best_of_rules")}
    res["hindsight"] = hs

    # ---- decision ---------------------------------------------------------------------------
    p1 = primary["P1_R1_vs_ridge"]["unmeasured_hits"]
    p2 = primary["P2_R1_vs_Cstar"]["unmeasured_hits"]
    p3 = primary["P3_gated_vs_R1"]["unmeasured_hits"]
    c = {"P1_direction": bool(holm["P1"] < 0.05 and p1["mean"] > 0),
         "P1_practical": bool(holm["P1"] < 0.05 and p1["ci95"][0] >= delta),
         "P2_beats_conventional": bool(holm["P2"] < 0.05 and p2["ci95"][0] > 0 and p2["mean"] >= delta),
         "P3_diagnosis_adds": bool(p3["p_one_sided"] < 0.05 and p3["ci95"][0] > 0 and p3["mean"] >= delta),
         "unique_yield_direction_consistent": bool(primary["P1_R1_vs_ridge"]["unique_candidates"]["mean"] > 0)}
    if not c["P1_practical"]:
        stop = "P1_NOT_PRACTICAL" if not c["P1_direction"] else "P1_DIRECTION_ONLY_BELOW_DELTA_STAR"
    elif not c["P2_beats_conventional"]:
        stop = "CONVENTIONAL_METHODS_EXPLAIN_THE_GAIN"
    elif not c["P3_diagnosis_adds"]:
        stop = "NO_FEEDBACK_IDENTIFIABLE_RESIDUAL_FOR_A_DIAGNOSIS_PROGRAM"
    elif not c["unique_yield_direction_consistent"]:
        stop = "UNIQUE_YIELD_CONTRADICTS"
    else:
        stop = None
    res["decision"] = {"conditions": c, "delta_star": delta, "decision": "CONTINUE_TO_PROGRAM_SEARCH_DESIGN" if stop is None else "STOP", "first_failed_condition": stop,
                       "reading": "STOP means no agent-generated program search is launched; the repair is reported with its attribution"}
    return json.loads(json.dumps(res, allow_nan=False, default=tc._plain))


def main() -> None:
    seal.check()
    if OUT.exists():
        raise SystemExit("RESULTS.json exists; write-once")
    res = analyse(load())
    tc.write_json(OUT, res)
    print(json.dumps({"rates_B3": res["rates_B3"], "decision": res["decision"]}, indent=1))
    for k, v in res["primary"].items():
        u = v["unmeasured_hits"]
        print(k, round(u["mean"], 3), [round(x, 3) for x in u["ci95"]], "p", round(u["p_one_sided"], 4))


if __name__ == "__main__":
    main()
