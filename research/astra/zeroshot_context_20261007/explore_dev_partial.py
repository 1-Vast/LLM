"""PRELIMINARY development exploration with the training contexts extracted so far.

Purpose: see noise, signal and replicate-well structure on the two development lines while the
remaining training contexts download, to size the acquisition task. Nothing here selects a model
or a gamma; world_dev.py repeats every number on the complete panel. Evaluation lines are not read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402
from agent_data import menu_labels  # noqa: E402
from remote import CACHE  # noqa: E402
from world_dev import panel_keys  # noqa: E402


def main():
    files = [f for f in wm.TRAIN_FILES if (CACHE / "observations" / f"{f}.npz").exists() and (CACHE / "state_forecasts" / f"{f}.npz").exists()]
    panel = wm.Panel(panel_keys(), files=files)
    wm.MIN_PANEL_LINES = len(files) - 3  # partial panel only; world_dev uses the registered 30
    base = panel.m0("equal")
    wells = menu_labels()
    out = {"status": "PRELIMINARY exploration, partial panel; superseded by world_dev.py", "training_contexts_used": files}
    for name in wm.SPLIT["development"]:
        t = wm.target(name, panel)
        e = t["eligible"]
        d, noise = t["delta"][e], t["noise"][e]
        m0 = base[t["panel_index"]][e]
        eta = d - m0
        total = np.mean(d ** 2, 1) - noise
        dev = np.mean(eta ** 2, 1) - noise
        s = t["S"][e]
        cor_s = [np.corrcoef(a, b)[0, 1] for a, b in zip(s, d)]
        cor_m0 = [np.corrcoef(a, b)[0, 1] for a, b in zip(m0, d)]
        cor_dev = [np.corrcoef(a, b)[0, 1] for a, b in zip(t["devS"][e], eta)]
        cor_knn = [np.corrcoef(a, b)[0, 1] for a, b in zip(t["devK"][e], eta)]
        row = {"groups": int(e.sum()), "noise_median": float(np.median(noise)), "noise_mean": float(noise.mean()),
               "total_energy_quantiles": np.percentile(total, [10, 25, 50, 75, 90, 99]).tolist(),
               "deviation_energy_quantiles": np.percentile(dev, [10, 25, 50, 75, 90, 99]).tolist(),
               "deviation_over_total_mean": float(dev.mean() / total.mean()),
               "mse": {"no_change": float(np.mean(np.mean(d ** 2, 1))), "M0_equal_partial": float(np.mean(np.mean(eta ** 2, 1))),
                       "STATE_direct": float(np.mean(np.mean((s - d) ** 2, 1))),
                       "M0_plus_devS": float(np.mean(np.mean((m0 + t["devS"][e] - d) ** 2, 1))),
                       "M0_plus_half_devS": float(np.mean(np.mean((m0 + 0.5 * t["devS"][e] - d) ** 2, 1))),
                       "M0_plus_devK": float(np.mean(np.mean((m0 + t["devK"][e] - d) ** 2, 1))),
                       "noise": float(noise.mean())},
               "median_corr_STATE_vs_observed": float(np.nanmedian(cor_s)), "median_corr_M0_vs_observed": float(np.nanmedian(cor_m0)),
               "median_corr_devS_vs_eta": float(np.nanmedian(cor_dev)), "median_corr_devK_vs_eta": float(np.nanmedian(cor_knn))}
        # Top-decile total energy subset (strong responders), still all eligible-defined.
        strong = total >= np.percentile(total, 90)
        row["strong_decile"] = {"groups": int(strong.sum()),
                                "median_corr_devS_vs_eta": float(np.nanmedian(np.array(cor_dev)[strong])),
                                "median_corr_devK_vs_eta": float(np.nanmedian(np.array(cor_knn)[strong])),
                                "mse_M0": float(np.mean(np.mean(eta[strong] ** 2, 1))),
                                "mse_M0_plus_devS": float(np.mean(np.mean((m0[strong] + t["devS"][e][strong] - d[strong]) ** 2, 1))),
                                "mse_M0_plus_devK": float(np.mean(np.mean((m0[strong] + t["devK"][e][strong] - d[strong]) ** 2, 1)))}
        # Replicate wells on the agent menu: deviation-energy reproducibility across independent wells.
        keys = {k: i for i, k in enumerate(t["keys"])}
        za, zb = [], []
        for label, (pa, pb) in wells.items():
            if (label, pa) in keys and (label, pb) in keys:
                ia, ib = keys[(label, pa)], keys[(label, pb)]
                ea = t["delta"][ia] - base[t["panel_index"][ia]]
                eb = t["delta"][ib] - base[t["panel_index"][ib]]
                za.append(np.mean(ea ** 2) - t["noise"][ia]); zb.append(np.mean(eb ** 2) - t["noise"][ib])
        za, zb = np.array(za), np.array(zb)
        rank = lambda x: np.argsort(np.argsort(x))
        row["replicate_wells"] = {"labels": int(len(za)), "pearson_zA_zB": float(np.corrcoef(za, zb)[0, 1]),
                                  "spearman_zA_zB": float(np.corrcoef(rank(za), rank(zb))[0, 1]),
                                  "zB_quantiles": np.percentile(zb, [10, 50, 85, 90, 99]).tolist()}
        out[name] = row
    (HERE / "world_dev").mkdir(exist_ok=True)
    (HERE / "world_dev" / "PRELIMINARY_partial_panel.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
