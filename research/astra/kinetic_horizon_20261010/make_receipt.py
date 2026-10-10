"""Assemble the dated machine receipt log/20261010/KINETIC_HORIZON.json from the study's records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main() -> dict:
    R, G, V = load("RESULTS.json"), load("GATE.json"), load("VERIFIED.json")
    M, T, K = R["M"], R["T"], R["K"]
    rec = {
        "study": "research/astra/kinetic_horizon_20261010",
        "frozen_utc": load("FREEZE.json")["frozen_utc"],
        "question": "Can a virtual cell's forecast of the early (24 h) state replace measuring it for a later-fate (5-day) decision; is any failure a ceiling, a transport or a timing problem?",
        "gate_development": {k: {x: G[k][x] for x in ("B_mean", "oracle_mean", "ceiling", "forecast_increment", "decision", "reasons") if x in G[k]}
                             for k in ("mix_24h_to_5d", "tahoe_24h_to_5d")},
        "confirmatory": {
            "M1_measurement_complements_prior": {k: M["M1_measurement_complements_prior"][k] for k in ("mean_increment", "ci95", "drugs_improved", "pass")},
            "M2_state_forecast_transport": {k: M["M2_state_forecast_transport"][k] for k in ("mean_increment", "ci95", "transport_refused")},
            "M2_rna_context_r": {d: {k: v[k] for k in ("S", "B_tahoe", "B_mix", "ceiling", "n_lines")} for d, v in M["M2_rna"].items()},
            "M2_cross_platform_same_line": M["M2_cross_platform_same_line"],
            "M2_cross_experiment_replicate": M["M2_cross_experiment_replicate"],
            "M3_decisions": {k: M["M3_decisions"][k] for k in ("P2_minus_P0", "P1_minus_P0", "pass", "gate_decision", "policy_by_gate", "costs")},
            "T1_when_to_observe": T["T1_when_to_observe"],
            "T2_temporal_fingerprint": T["T2_temporal_fingerprint"],
            "T3_kinetic_rate": {k: T["T3_kinetic_rate"][k] for k in ("pooled_kinetic_r", "pooled_kinetic_ci95", "pooled_g1_r", "pooled_abundance_so_far_r")},
            "K1_selectivity_ceiling": K["K1_selectivity_ceiling"],
            "K2_potency_kinetic_vs_share": K["K2_potency_kinetic_vs_share"],
            "K3_g1_sign_top_drugs": K["K3_g1_sign_top_drugs"],
        },
        "posthoc": {"paired_reanalysis": {k: {x: v[x] for x in ("mean_increment", "ci95", "drugs_improved", "top10_difference", "top10_difference_ci95", "top10_drugs_better")}
                                          for k, v in load("posthoc/paired_reanalysis.json").items() if k.startswith("M")},
                    "gate_uncertainty": load("posthoc/gate_uncertainty.json")},
        "verification": {k: (v.get("pass") if isinstance(v, dict) else v) for k, v in V.items()},
        "deviations": [d["id"] + ": " + d["what"][:160] for d in load("DEVIATIONS.json")],
        "units": {"tahoe_confirmation_lines": K["n_lines"], "mixseq_confirmation_lines": M["n_lines"], "mixseq_timecourse_lines": len(T["lines"]),
                  "tahoe_zeroshot_prism": "sealed (not extracted)"},
        "resources": {
            "downloads_bytes": {"prism_19q4": 391_472_595, "mixseq_scperturb_h5ad": 1_459_410_830, "ccle_19q4_expression_and_sample_info": 300_834_016},
            "state_forward_sets": 5421, "state_gpu_seconds": 142.8, "llm_calls": 0, "llm_spend_usd": 0.0,
            "lab_units_simulated": "P2 = 2 pooled treated wells per drug + 2 shared control wells, 1 day; P3 = one pooled 5-day screen, 5 days",
        },
        "promoted": ["src/maestro/world_model_value.py: IncrementEstimate, MeasureOrPredict, plan_measure_or_predict",
                     "tools/evaluation/increment.py: paired_increment", "tools/analysis/platform_identity.py: identity_test"],
        "not_promoted": ["kinetic readout (T3 rate hypothesis unsupported; K2 CI includes 0)", "STATE use on MIX-Seq (transport refused)",
                         "measurement-first policy (M1/M3 failed)"],
    }
    out = ROOT / "log/20261010/KINETIC_HORIZON.json"
    out.write_text(json.dumps(rec, indent=1, default=float), encoding="utf-8")
    rec["sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    return rec


if __name__ == "__main__":
    print(main()["sha256"])
