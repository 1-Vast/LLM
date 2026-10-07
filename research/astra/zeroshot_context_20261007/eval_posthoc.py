"""POST-HOC descriptive analysis after the frozen evaluation (not a test; nothing here was registered).

On the evaluation lines with the frozen choices: dose breakdown of M2 - M0, the coordinates that
carry STATE's improvement (named genes only), and how the improvement splits between coordinates the
gene-gated comparator already handles and the rest.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402
from world_dev import components, panel_keys  # noqa: E402


def main():
    protocol = json.loads((HERE / "WORLD_PROTOCOL.json").read_text(encoding="utf-8"))
    wm.guard(wm.SPLIT["evaluation"])
    ch = protocol["choices"]
    v, gs, gk, lam = ch["M0_variant"], ch["gamma_S"], ch["gamma_K"], ch["krr_lambda"]
    names = json.loads((HERE.parents[2] / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json").read_text(encoding="utf-8"))["names"]
    panel = wm.Panel(panel_keys())
    out = {"status": "post-hoc descriptive, after the frozen evaluation; not a hypothesis test", "lines": {}}
    gene_gain = np.zeros(2000)
    gate_gain = np.zeros(2000)
    for name in wm.SPLIT["evaluation"]:
        t = wm.target(name, panel)
        c = components(panel, t, lam)
        m0 = c[f"P0_{v}"]
        m2 = m0 + gs * c["devS"]
        m1 = m0 + gk * c[f"D_gate_{v}"]
        e0 = (m0 - c["obs"]) ** 2
        e2 = (m2 - c["obs"]) ** 2
        e1 = (m1 - c["obs"]) ** 2
        gene_gain += (e0 - e2).sum(0)
        gate_gain += (e0 - e1).sum(0)
        dose = np.array([wm.dose_of(k) for k in c["keys"]])
        row = {}
        for d in sorted(set(dose)):
            m = dose == d
            row[str(d)] = {"groups": int(m.sum()), "M2_minus_M0_raw_squared_error": float((e2[m] - e0[m]).mean()),
                           "M0_raw_squared_error": float(e0[m].mean())}
        out["lines"][name] = {"by_dose": row}
    order = np.argsort(-gene_gain)
    total = gene_gain.sum()
    out["share_of_STATE_gain_in_top_coordinates"] = {str(k): float(gene_gain[order[:k]].sum() / total) for k in (20, 100, 500)}
    out["top_coordinates_STATE_gain"] = [{"coordinate": int(j), "gene": names[j], "gain_share": float(gene_gain[j] / total),
                                          "gate_gain_share_same_coordinate": float(gate_gain[j] / gate_gain.sum())} for j in order[:30]]
    corr = float(np.corrcoef(gene_gain, gate_gain)[0, 1])
    out["correlation_per_coordinate_STATE_gain_vs_gate_gain"] = corr
    out["note"] = ("Raw squared errors are used for the per-coordinate split because the depth correction is per group; "
                   "panel sampling noise is identical for M0 and M2, so their difference is unaffected.")
    (HERE / "world_eval" / "POSTHOC_DESCRIPTIVE.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("share_of_STATE_gain_in_top_coordinates", "correlation_per_coordinate_STATE_gain_vs_gate_gain")}, indent=1))
    print([(x["gene"], round(x["gain_share"], 4), round(x["gate_gain_share_same_coordinate"], 4)) for x in out["top_coordinates_STATE_gain"][:30]])
    print(json.dumps(out["lines"], indent=1)[:2500])


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


def common_vs_specific(split_name):
    """Split devS into its (plate, dose) stratum mean and the drug-specific remainder (descriptive)."""
    protocol = json.loads((HERE / "WORLD_PROTOCOL.json").read_text(encoding="utf-8"))
    ch = protocol["choices"]
    v, gs, lam = ch["M0_variant"], ch["gamma_S"], ch["krr_lambda"]
    names = wm.SPLIT[split_name]
    wm.guard(names)
    panel = wm.Panel(panel_keys())
    res = {}
    for name in names:
        t = wm.target(name, panel)
        c = components(panel, t, lam)
        strata = {}
        for j, k in enumerate(c["keys"]):
            strata.setdefault((wm.dose_of(k), k[1]), []).append(j)
        common = np.zeros_like(c["devS"])
        for members in strata.values():
            common[members] = c["devS"][members].mean(0)
        specific = c["devS"] - common
        m0, n0 = c[f"P0_{v}"], c[f"n00_{v}"]
        se = lambda pred: float((np.mean((pred - c["obs"]) ** 2, 1) - n0 - c["noise_L"]).mean())
        base = se(m0)
        res[name] = {"M0": base, "M2_full_minus_M0": se(m0 + gs * c["devS"]) - base,
                     "M2_common_part_minus_M0": se(m0 + gs * common) - base,
                     "M2_drug_specific_part_minus_M0": se(m0 + gs * specific) - base}
    return res


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--split-common":
    out = {"status": "post-hoc descriptive decomposition of devS into (plate, dose) stratum mean and drug-specific remainder",
           "development": common_vs_specific("development"), "evaluation": common_vs_specific("evaluation")}
    (HERE / "world_eval" / "POSTHOC_COMMON_VS_SPECIFIC.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
