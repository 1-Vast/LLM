"""Build CLAIMS.json: every number README.md cites, recomputed from the result files.

File summary
- Path: research/orbit_contrast_20261013/claims.py
- Purpose: one formatted string per claim, derived only from RESULTS.json (S2), RESULTS_S1.json,
  RESULTS_S0.json, POWER.json and RESULTS_C.json (Task C, TASK_C.md), with the verdict applied by
  the frozen `verdict.decide` and the Task C decision as written by `taskc.py`.
  verify.py checks that CLAIMS.json recomputes and that each claim's text appears in README.md.
- Command: `python claims.py` writes CLAIMS.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from verdict import decide

HERE = Path(__file__).resolve().parent


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def fmt(c: dict) -> str:
    p = c["p_greater"]
    ptxt = "p < 0.0001" if p < 1e-4 + 1e-12 else f"p {p:.4f}"
    return f"{c['difference']:+.4f} [{c['ci95'][0]:+.4f}, {c['ci95'][1]:+.4f}], {ptxt}"


def build() -> dict:
    r, s1, s0, pw = _load("RESULTS.json"), _load("RESULTS_S1.json"), _load("RESULTS_S0.json"), _load("POWER.json")
    v = decide(r, pw)
    claims = []

    def add(cid: str, label: str, text: str) -> None:
        claims.append({"id": cid, "text": f"{label} {text}"})

    A, Bn, Bf = r["A"], r["B_nontrivial"], r["B_full"]
    pa, pb = A["primary_active"], Bn["primary_all"]
    add("S0", "S0 synthetic check:", "PASS" if s0["passed"] else "FAIL")
    add("units_A", "A′ primary population:", f"{pa['entities']} compounds, {pa['cells']} active cells")
    add("units_B", "B primary population:", f"{pb['entities']} genes, {pb['cells']} cells")
    add("V1", "V1 positive control (landmark self-knockdown), F − F₋self:", fmt(Bf["landmark"]["ablations"]["F-(F-self)"]))
    add("V1_sp", "V1 identity-gate Spearman with the realised self contrast:", f"{v['V1']['spearman_identity_gate_self']:.3f}")
    for t, key in (("A", "A"), ("B", "B_nontrivial")):
        rel = r["relabel_delta_id_F"][key]
        add(f"V2_{t}", f"V2 {t} relabelled Δ_id(F), 5 runs, mean and max:", f"{sum(rel) / len(rel):+.4f} / {max(rel):+.4f}")
    for t, blk in (("A", pa), ("B", pb)):
        c = blk["contrasts"]
        add(f"H1_{t}", f"H1-{t} Δ_id(F) = F − O:", fmt(c["F-O"]))
        add(f"H2a_{t}", f"H2a-{t} F − R:", fmt(c["F-R"]))
        add(f"H2b_{t}", f"H2b-{t} F − C′:", fmt(c["F-Cp"]))
        add(f"FC_{t}", f"{t} F − C (accuracy-certified full routes):", fmt(c["F-C"]))
        add(f"FN_{t}", f"{t} F − N (naive integration):", fmt(c["F-N"]))
        add(f"NO_{t}", f"{t} N − O (naive identity gain):", fmt(c["N-O"]))
        add(f"OB_{t}", f"{t} O − B0 (orbit means over base):", fmt(c["O-B0"]))
        add(f"arms_{t}", f"{t} mean centred cosine B0 / O / N / F:",
            " / ".join(f"{blk['arms'][k]:.4f}" for k in ("B0", "O", "N", "F")))
    add("abl_know", "A′ F − F₋know:", fmt(pa["ablations"]["F-(F-know)"]))
    add("abl_gen", "A′ F − F₋genetic:", fmt(pa["ablations"]["F-(F-genetic)"]))
    sn = A["strict_new_active"]
    add("strict_new", "A′ strict-new-mechanism stratum:", f"{sn['entities']} compounds, {sn['cells']} cells")
    if "ablations" in sn:
        add("H3", "H3 strict-new F − F₋genetic:", fmt(sn["ablations"]["F-(F-genetic)"]))
    kd = A["kd_covered_active"]
    add("kd_cov", "A′ knockdown-covered active cells, F − F₋genetic:", fmt(kd["ablations"]["F-(F-genetic)"]))
    for r_ in ("pharm", "cotarget", "esm"):
        add(f"abl_{r_}", f"B F − F₋{r_}:", fmt(pb["ablations"][f"F-(F-{r_})"]))
    pav = Bn["pharm_available"]
    add("pharm_av", "B pharm-available cells, F − F₋pharm:", fmt(pav["ablations"]["F-(F-pharm)"]))
    for task, blk in (("A", A), ("B", Bn), ("Bfull", Bf)):
        for rt, c in blk["certificates"].items():
            add(f"cert_{task}_{rt}", f"{task} {rt} gate Spearman with realised contrast, identity / accuracy:",
                f"{c['spearman_identity_gate']:.3f} / {c['spearman_accuracy_gate']:.3f} (mean contrast {c['mean_contrast']:+.4f}, admitted {c['admitted_fraction']:.2f})")
    ctl = r["controls"]
    sc = ctl["A_sign_contradiction"]
    add("ctl_sign", "Sign contradiction, mean genetic contrast real → flipped:",
        f"{sc['mean_contrast_genetic_real']:+.4f} → {sc['mean_contrast_genetic_flipped']:+.4f}")
    for k, label in (("A_context_permutation", "A′ context permutation"), ("A_evidence_withdrawal", "A′ evidence withdrawal"),
                     ("B_context_permutation", "B context permutation"), ("B_evidence_withdrawal", "B evidence withdrawal")):
        add(f"ctl_{k}", f"{label}, Δ_id(F) variant vs real:", f"{ctl[k]['delta_id_F']:+.4f} vs {ctl[k]['delta_id_F_real']:+.4f}")
    sn20 = ctl["A_source_snapshot_hub2020"]
    add("ctl_snapshot", "A′ Hub-2020 snapshot, Δ_id(F) variant vs real (same compounds):",
        f"{sn20['delta_id_F']:+.4f} vs {sn20['delta_id_F_real_same_compounds']:+.4f}")
    add("dev_A", "S1 development A′ Δ_id(F):", fmt(s1["A"]["primary_active"]["contrasts"]["F-O"]))
    add("power_A", "Power at MEI 0.01 (S1), A′ / B:", f"{pw['A']['power_at_mei']:.2f} / {pw['B']['power_at_mei']:.2f}")
    add("verdict", "Verdict:", v["verdict"])
    add("genetic_claim", "Functional-genetic-knowledge claim:", v["functional_genetic_claim"])
    rc = _load("RESULTS_C.json")
    for pop, label in (("primary_all", "all"), ("active", "active")):
        b = rc[pop]
        add(f"C_units_{label}", f"Task C units ({label}):", f"{b['units']} compounds, {b['mean_true_targets']:.2f} annotated targets each")
        add(f"C_hits_{label}", f"Task C hits@10 ({label}) Z0 / P / H / X / Zc / OC / F:",
            " / ".join(f"{b['hits_at_10'][a]:.4f}" for a in ("Z0", "P", "H", "X", "Zc", "OC", "F")))
        for k in ("C1 F-Zc", "C2 OC-X", "F-P", "F-H", "H-P", "X-Z0", "P-Z0"):
            add(f"C_{label}_{k.split()[-1]}", f"Task C ({label}) {k}:", fmt(b["contrasts"][k]))
        g = b["gate"]
        add(f"C_gate_{label}", f"Task C ({label}) admission gate Spearman with realised contrast, admitted fraction:",
            f"{g['spearman_chat_contrast']:.3f}, {g['admitted_fraction']:.2f}")
    add("C_decision", "Task C decision:", rc["decision"]["task_c"])
    add("C_orbit", "Task C orbit calibration helps:", "yes" if rc["decision"]["orbit_calibration_helps"] else "no")
    return {"source": ["RESULTS.json", "RESULTS_S1.json", "RESULTS_S0.json", "POWER.json", "RESULTS_C.json"], "decision": v,
            "task_c": rc["decision"], "claims": claims}


if __name__ == "__main__":
    out = build()
    (HERE / "CLAIMS.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for c in out["claims"]:
        print(c["text"])
