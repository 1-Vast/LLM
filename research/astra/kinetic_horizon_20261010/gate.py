"""Development-only gate: measurement ceiling, forecaster transport and the measure-or-predict
decision per domain.  Writes GATE.json before freeze; reads no confirmation or held-out value.

For a decision endpoint E and a cheap prior B (best development comparator):
* ceiling  = r(B + perfect early state) - r(B)          (perfect = observed early state)
* forecast = r(B + world-model forecast of early state) - r(B)
* decision: ADMIT_WORLD_MODEL if forecast >= MUB; else MEASURE_EARLY if ceiling >= MUB;
            else USE_PRIOR (reason WM_CEILING_BELOW_MUB).
Combinations are equal-weight sums of z-scores (no fitted weight).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ccle as C  # noqa: E402
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402

MUB = 0.05
MIX_DRUGS_LATE = ["Trametinib", "Afatinib", "Everolimus", "Gemcitabine", "Taselisib", "JQ1"]
STATE_DRUGS = MIX_DRUGS_LATE[:4]
CONFIG = {
    "mix_late_endpoint": "secondary_mean",
    "mix_prior": {"kind": "ridge", "n_pc": 50, "alpha": 100.0},
    "tahoe_late_endpoint": "primary_2p5",
    "tahoe_prior": {"kind": "kernel", "tau": 0.1, "top_m": 20},
    "tahoe_bridge_coef_s24_k24": [-0.1575, -0.1965],
    "projection_variant": "v1",
    "top_k": 10,
    "mub": MUB,
}


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 6 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


def z(x):
    return (x - np.nanmean(x)) / np.nanstd(x)


def mix_prior(target: str, refs: list, y: np.ndarray) -> float:
    p = CONFIG["mix_prior"]
    return float(C.ridge([target], refs, y, p["n_pc"], p["alpha"])[0])


def decide(ceiling: float, forecast: float) -> tuple[str, list]:
    if np.isfinite(forecast) and forecast >= MUB:
        return "ADMIT_WORLD_MODEL", []
    reasons = ["WM_TRANSPORT_UNQUALIFIED"] if np.isfinite(forecast) else ["WM_FORECAST_NOT_EVALUATED"]
    if np.isfinite(ceiling) and ceiling >= MUB:
        return "MEASURE_EARLY", reasons
    return "USE_PRIOR", reasons + ["WM_CEILING_BELOW_MUB"]


def mix_domain() -> dict:
    sp = MP.split(); dev = sp["pool_A_development"]
    ext = H.load_late("external_mix"); mixd = H.load_late("mix_development")
    ed, md = list(ext["drugs"]), list(mixd["drugs"])
    mp = MP.pool_a_panel(dev, ["A_treated_dev"], CONFIG["projection_variant"], MIX_DRUGS_LATE)
    st = MP.state_forecast("A", CONFIG["projection_variant"], dev, STATE_DRUGS)
    yk = CONFIG["mix_late_endpoint"]
    per = {}
    for j, drug in enumerate(MIX_DRUGS_LATE):
        y = mixd[yk][:, md.index(drug)]
        y_ext = ext[yk][:, ed.index(drug)]
        Bp = np.array([mix_prior(d, list(ext["depmap"]) + [x for x in dev if x != d], np.r_[y_ext, np.delete(y, i)]) for i, d in enumerate(dev)])
        mag = np.array([-np.linalg.norm(mp.obs[i, j]) if np.isfinite(mp.obs[i, j]).all() else np.nan for i in range(len(dev))])
        rec = {"B": r(Bp, y), "oracle_B_plus_Rmag": r(z(Bp) + z(mag), y), "R_mag": r(mag, y)}
        if drug in STATE_DRUGS:
            sm = -np.linalg.norm(st["paired"][:, j], axis=1)
            rec["wm_B_plus_Smag"] = r(z(Bp) + z(sm), y)
        per[drug] = rec
    mean = lambda k: float(np.nanmean([v[k] for v in per.values() if k in v]))  # noqa: E731
    ceiling = mean("oracle_B_plus_Rmag") - mean("B")
    forecast = float(np.nanmean([per[d]["wm_B_plus_Smag"] - per[d]["B"] for d in STATE_DRUGS]))
    # RNA-level transport of STATE (context deviation r), from dev_mixseq_rna.json (v1)
    rna = json.loads((HERE / "development/dev_mixseq_rna.json").read_text())["v1"]
    decision, reasons = decide(ceiling, forecast)
    return {"endpoint": f"PRISM {yk} (5 day), across lines per drug", "n_dev_lines": len(dev), "per_drug": per,
            "B_mean": mean("B"), "oracle_mean": mean("oracle_B_plus_Rmag"), "ceiling": ceiling, "forecast_increment": forecast,
            "state_rna_context_r_dev": {d: rna[d]["S"] for d in STATE_DRUGS},
            "state_rna_ceiling_dev": {d: rna[d]["ceiling"] for d in STATE_DRUGS},
            "decision": decision, "reasons": reasons}


def tahoe_domain() -> dict:
    split = H.split(); tdev = split["development"]
    keep, _ = H.A.qualified_reference()
    E = H.early_panel(keep)
    sel = lambda X: X - np.nanmean(X, 0, keepdims=True)  # noqa: E731
    ext = H.load_late("external_tahoe"); tl = H.load_late("development")
    yk = CONFIG["tahoe_late_endpoint"]
    Yd, Ye = tl[yk], ext[yk]
    drugs = list(tl["drugs"])
    dep = [split["lines"][f]["depmap_id"] for f in tdev]
    mu = np.nanmean(Ye, 0)
    ej = [E.drugs.index(d) if d in E.drugs else None for d in drugs]
    cs = CONFIG["tahoe_bridge_coef_s24_k24"]
    p = CONFIG["tahoe_prior"]
    rb, rc, rr = [], [], []
    for i, (f, d) in enumerate(zip(tdev, dep)):
        refs = list(ext["depmap"]) + [x for x in dep if x != d]
        Bp = np.array([C.kernel(d, refs, np.r_[Ye[:, j], np.delete(Yd[:, j], i)], p["tau"], p["top_m"]) for j in range(len(drugs))]) - mu
        e = keep.index(f)
        Rd = np.array([cs[0] * sel(E.s24)[e, k] + cs[1] * sel(E.k24)[e, k] if k is not None else np.nan for k in ej])
        y = Yd[i] - mu
        rb.append(r(Bp, y)); rr.append(r(Rd, y)); rc.append(r(z(Bp) + z(Rd), y))
    ceiling = float(np.nanmean(rc) - np.nanmean(rb))
    decision, reasons = decide(ceiling, np.nan)
    return {"endpoint": f"PRISM {yk} (5 day) within-line selectivity", "n_dev_lines": len(tdev), "B_mean": float(np.nanmean(rb)),
            "R_dyn_mean": float(np.nanmean(rr)), "oracle_mean": float(np.nanmean(rc)), "ceiling": ceiling,
            "forecast_increment": None, "decision": decision, "reasons": reasons,
            "note": "STATE forecasts of the Tahoe 24 h state exist only for the five zero-shot lines; with the ceiling below MUB no forecast can be admitted."}


def main() -> dict:
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("GATE.json is computed before freeze only")
    gate = {"config": CONFIG, "mix_24h_to_5d": mix_domain(), "tahoe_24h_to_5d": tahoe_domain(),
            "tahoe_24h_survival_same_unit": {"source": "research/astra/phenotype_anchor_20261010/GATE.json", "decision": "USE_PRIOR",
                                              "reasons": ["WM_CEILING_BELOW_MUB"], "ceiling": 0.003}}
    (HERE / "GATE.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    return gate


if __name__ == "__main__":
    g = main()
    for k in ("mix_24h_to_5d", "tahoe_24h_to_5d"):
        print(k, {x: g[k][x] for x in ("B_mean", "oracle_mean", "ceiling", "forecast_increment", "decision", "reasons")})
