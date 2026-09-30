"""Post-hoc diagnostics prompted by the audit: NOT pre-registered, reported as such.

File summary
- Path: research/biological_depth/posthoc.py
- Purpose: examine what the pre-registered audit exposed: the zero arm scoring B1 = 0.130, a
  vehicle null that calls 78% of conditions responsive, and anchors that fail in the data.
- Core points:
  - `B1_perp` removes the systematic axis from both vectors before correlating, so predicting
    "less (or more) than the average drug" scores exactly zero; only direction information
    orthogonal to the shared response remains.
  - Every comparison here is paired by compound with a compound-bootstrap interval.
  - Nothing here changes a registered verdict; it says how much each verdict is worth.
- Run: python research/biological_depth/posthoc.py --prepared <dir> --cv <dir> --output <dir>
- Depends on: audit.py, common.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import common
from audit import Audit, pearson

LINES = ("A549", "K562", "MCF7")


def perp(vector: np.ndarray, axis: np.ndarray) -> np.ndarray:
    norm = float(axis @ axis)
    return vector - (vector @ axis) / norm * axis if norm > 0 else vector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--cv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    a = Audit(args.prepared, args.cv)
    rows = np.flatnonzero(a.responsive)
    compound = a.conditions.compound.to_numpy()
    out: dict = {"status": "post hoc; not pre-registered"}

    def per_compound(fn, subset=rows) -> dict[str, float]:
        values: dict[str, list[float]] = {}
        for i in subset:
            v = fn(i)
            if v is not None and np.isfinite(v):
                values.setdefault(compound[i], []).append(v)
        return {k: float(np.mean(v)) for k, v in values.items()}

    # 1. direction orthogonal to the systematic response
    b1_perp, b1 = {}, {}
    for arm in a.pred:
        b1_perp[arm] = per_compound(lambda i: pearson(perp(a.pred[arm][i] - a.m[i], a.m[i]), perp(a.y[i] - a.m[i], a.m[i])))
        b1[arm] = per_compound(lambda i: pearson(a.pred[arm][i] - a.m[i], a.y[i] - a.m[i]))
    ceiling_perp = per_compound(lambda i: None if np.isnan(a.rep1[i]).any() or np.isnan(a.rep2[i]).any() else
                                pearson(perp(a.rep1[i] - a.m[i], a.m[i]), perp(a.rep2[i] - a.m[i], a.m[i])))
    out["B1_perp"] = {arm: common.cluster_bootstrap(v) for arm, v in b1_perp.items()}
    out["B1_perp_replicate_ceiling"] = common.cluster_bootstrap(ceiling_perp)
    raw = out["B1_perp_replicate_ceiling"]["mean"]
    out["B1_perp_replicate_ceiling_spearman_brown"] = 2 * raw / (1 + raw) if raw is not None else None
    out["B1_minus_zero"] = {arm: common.paired_bootstrap(b1[arm], b1["zero"]) for arm in a.pred if arm != "zero"}
    out["B1_perp_minus_knn"] = {arm: common.paired_bootstrap(b1_perp[arm], b1_perp["knn_chem"])
                                for arm in a.pred if arm != "knn_chem"}
    out["annotation_control"] = {
        "B1_moa_minus_shuffled": common.paired_bootstrap(b1["latent_jepa_moa"], b1["latent_jepa_moa_shuffled"]),
        "B1_perp_moa_minus_shuffled": common.paired_bootstrap(b1_perp["latent_jepa_moa"], b1_perp["latent_jepa_moa_shuffled"]),
        "B1_moa_minus_jepa": common.paired_bootstrap(b1["latent_jepa_moa"], b1["latent_jepa"])}

    # 2. how permissive the vehicle null is: replicate agreement among "responsive" conditions
    agreement = np.array([np.nan if np.isnan(a.rep1[i]).any() or np.isnan(a.rep2[i]).any()
                          else pearson(a.rep1[i], a.rep2[i]) for i in range(len(a.y))])
    doses = a.conditions.dose.to_numpy()
    out["null_check"] = {
        "responsive_fraction_by_dose": {str(d): float(a.responsive[doses == d].mean()) for d in (10.0, 100.0, 1000.0, 10000.0)},
        "uncentered_replicate_r_median_by_dose": {str(d): float(np.nanmedian(agreement[doses == d])) for d in (10.0, 100.0, 1000.0, 10000.0)},
        "fraction_replicate_r_above_0.3_by_dose": {str(d): float(np.nanmean(agreement[doses == d] > 0.3)) for d in (10.0, 100.0, 1000.0, 10000.0)}}

    # 2b. the same direction metric on conditions whose two replicates agree (r > 0.3). Selection
    # uses only the measurements, so comparisons between arms stay fair; the ceiling on this
    # subset is inflated by the selection and is reported for orientation only.
    reproducible = np.flatnonzero(np.nan_to_num(agreement, nan=-1.0) > 0.3)
    out["reproducible_population"] = {"conditions": int(len(reproducible)),
                                      "compounds": int(len(set(compound[reproducible])))}
    b1_perp_rep = {arm: per_compound(lambda i: pearson(perp(a.pred[arm][i] - a.m[i], a.m[i]),
                                                       perp(a.y[i] - a.m[i], a.m[i])), reproducible) for arm in a.pred}
    out["B1_perp_reproducible"] = {arm: common.cluster_bootstrap(v) for arm, v in b1_perp_rep.items()}
    out["B1_perp_reproducible_minus_knn"] = {arm: common.paired_bootstrap(b1_perp_rep[arm], b1_perp_rep["knn_chem"])
                                             for arm in a.pred if arm != "knn_chem"}

    # 2c. which mechanism classes carry predictable direction at all (classes with >= 3 compounds)
    classes = a.compounds.pathway_level_2
    counts = classes.value_counts()
    by_class = {}
    for arm in ("knn_chem", "ridge_chem", "mlp_existing", "latent_jepa", "latent_jepa_moa"):
        for label in counts[counts >= 3].index:
            members = {c: v for c, v in b1_perp[arm].items() if classes.get(c) == label}
            by_class.setdefault(label, {"compounds": len(members)})[arm] = (
                float(np.mean(list(members.values()))) if members else None)
    out["B1_perp_by_class"] = dict(sorted(by_class.items(), key=lambda kv: -(kv[1].get("knn_chem") or 0)))

    # 3. anchors that failed in the observed data, and the unreproduced ones, in detail
    spec = common.load_anchors()
    observed = a.anchors(a.y, spec)
    out["observed_anchor_detail"] = {k: observed[k]["detail"] for k in
                                     ("A4_mek_mpas", "A6_bet_hexim1", "A10_no_functional_target", "A2_glucocorticoid_gr", "A7_p53_context")}
    for arm in ("knn_chem", "latent_jepa", "latent_jepa_moa", "mlp_existing", "ridge_chem"):
        detail = a.anchors(a.pred[arm], spec)
        out.setdefault("model_anchor_detail", {})[arm] = {k: detail[k]["detail"] for k in ("A2_glucocorticoid_gr", "A7_p53_context", "A3_estrogen_receptor_mcf7")}
    # 4. what a held-out glucocorticoid's structure neighbours are (prodrug question)
    from models import morgan, tanimoto
    fps = morgan(a.compounds.smiles.tolist(), 2048)
    names = list(a.compounds.index)
    target = names.index("Triamcinolone Acetonide")
    sims = tanimoto(fps[[target]], fps)[0]
    folds = a.compounds.fold.to_numpy()
    order = [j for j in np.argsort(-sims) if folds[j] != folds[target]][:5]
    out["triamcinolone_training_neighbours"] = [(names[j], round(float(sims[j]), 3)) for j in order]
    common.write_json(args.output / "posthoc.json", out)
    summary = {"B1_perp": {k: v["mean"] for k, v in out["B1_perp"].items()},
               "B1_perp_ceiling": out["B1_perp_replicate_ceiling"], "spearman_brown": out["B1_perp_replicate_ceiling_spearman_brown"],
               "annotation_control": out["annotation_control"], "null_check": out["null_check"],
               "triamcinolone_neighbours": out["triamcinolone_training_neighbours"]}
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
