"""Reference-only descriptives for block M (writes development/describe.json).

Signature strength per option, how many reference classes respond at all, the time split of
response strength, and the EMH component audit on reference drugs (classes with >= 2 reference
drugs). Development and confirmation drugs are not read here.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import components as CO
import knowledge as KN
import study as S

HERE = Path(__file__).resolve().parent


def main() -> dict:
    data = S.load_tier("open")
    X, moa, role, options, genes = data["x"], data["moa"], data["role"], data["options"], data["genes"]
    ref = role == "reference"
    norms = np.linalg.norm(X, axis=2)  # (n, opt)
    res = {"n_reference": int(ref.sum()), "options": options}
    res["norm_by_option"] = {o: [float(np.nanpercentile(norms[ref, j], q)) for q in (10, 50, 90)] for j, o in enumerate(options)}
    allref = norms[ref][np.isfinite(norms[ref])]
    res["norm_reference_quantiles"] = {q: float(np.percentile(allref, q)) for q in (10, 25, 50, 75, 90, 95, 99)}
    # class response strength from the class mean (averaging cancels noise; strength survives)
    means = CO.class_means(X, moa, ref, 2)
    cls_norm = {c: float(np.nanmean([np.linalg.norm(np.nan_to_num(m[j])) for j in range(len(options)) if not np.isnan(m[j]).all()])) for c, m in means.items()}
    res["class_mean_norm_quantiles"] = {q: float(np.percentile(list(cls_norm.values()), q)) for q in (10, 25, 50, 75, 90)}
    res["n_classes_2plus_reference"] = len(means)
    res["top_classes_by_norm"] = sorted(cls_norm.items(), key=lambda kv: -kv[1])[:25]
    six = [j for j, o in enumerate(options) if o.endswith("6 h")]
    tw = [j for j, o in enumerate(options) if o.endswith("24 h")]
    res["median_norm_6h_vs_24h"] = [float(np.nanmedian(norms[ref][:, six])), float(np.nanmedian(norms[ref][:, tw]))]
    for v in ("nolit", "lit", "lit_critic"):
        emhs = KN.load_emhs(HERE, v, sorted(means))
        res[f"components_{v}"] = CO.audit(emhs, means, genes, options)
    out = HERE / "development" / "describe.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ("norm_by_option", "options", "top_classes_by_norm")}, indent=1))
    print(r["top_classes_by_norm"][:15])
