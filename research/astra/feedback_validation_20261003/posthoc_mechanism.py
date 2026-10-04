"""POST HOC (after the verdict): do in-context drug-in-line effects replicate across orientations?

File summary
- Path: research/astra/feedback_validation_20261003/posthoc_mechanism.py
- Purpose: explain the registered Jaaks result. Feedback can only help validated discovery if
  the drug-in-line effects it learns from screen measurements reappear in the independent
  validation measurements of the same line. For every line, fit the frozen in-context posterior
  on ALL screen measurements of the SV replicate and, separately, on all screen measurements of
  the VS replicate (which are the SV validation measurements on disjoint plates), then compare
  the two sets of drug effects, split by the drug's role in SV (S = anchored, V = titrated).
  Also report how much of each orientation's within-line residual variance the effects explain.
- Core points:
  - Not part of the frozen protocol; written and run after `results/jaaks_primary/verdict.json`.
    The vault entry for this run is logged with purpose "post hoc".
  - Uses the frozen TransferWorld (context off) and its fitted variances.
- Interfaces: `python -m research.astra.feedback_validation_20261003.posthoc_mechanism OUT_JSON`.
- Depends on: numpy; study modules; tools.datasets.combination_screens.open_vault.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from research.certified_discovery.world import TransferWorld

from .jaaks import RELEASE, build_panels
from .run import FREEZE, ROOT, VAULT_LOG
from .study import WORLD


def effects(world: TransferWorld) -> tuple[np.ndarray, np.ndarray, float]:
    """Posterior drug effects from all target measurements; residual R2 explained in-sample."""
    rows = world.rows
    resid = world.lib.y[rows] - world.prior_target
    Z = world.Z_target
    cov = np.linalg.inv(world.A_inv + Z.T @ Z / world.s_noise)
    eff = cov @ (Z.T @ resid) / world.s_noise
    fitted = Z @ eff
    r2 = 1.0 - np.var(resid - fitted) / np.var(resid) if np.var(resid) > 0 else np.nan
    return eff[1:], resid, float(r2)


def main(argv: list[str] | None = None) -> int:
    from tools.datasets.combination_screens import open_vault

    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0])
    ticket = open_vault(FREEZE, VAULT_LOG, purpose="POST HOC exploratory mechanism diagnostic (after verdict)",
                        source=RELEASE, root=ROOT)
    panels, _, candidates = build_panels(ticket, RELEASE)
    report: dict = {"status": "POST HOC exploratory; not part of the frozen protocol", "ticket": ticket, "tissues": {}}
    for tissue in ("Breast", "Colon", "Pancreas"):
        sv, vs = panels[f"{tissue}_SV"], panels[f"{tissue}_VS"]
        S = set(candidates[tissue]["S"])
        drugs = sv.library.drugs
        role_s = np.array([d in S for d in drugs])
        pairs = {"anchor_role_in_SV": ([], []), "library_role_in_SV": ([], [])}
        r2_sv, r2_vs, cross = [], [], []
        for line in range(len(sv.library.lines)):
            w1, w2 = TransferWorld(sv.library, line, WORLD), TransferWorld(vs.library, line, WORLD)
            e1, res1, a = effects(w1)
            e2, res2, b = effects(w2)
            r2_sv.append(a)
            r2_vs.append(b)
            present = np.zeros(len(drugs), bool)
            present[np.unique(np.r_[sv.library.a[w1.rows], sv.library.b[w1.rows]])] = True
            for key, mask in (("anchor_role_in_SV", role_s & present), ("library_role_in_SV", ~role_s & present)):
                pairs[key][0].extend(e1[mask].tolist())
                pairs[key][1].extend(e2[mask].tolist())
            # out-of-orientation R2: SV drug effects predicting the VS (validation) residuals
            fitted_cross = w2.Z_target[:, 1:] @ e1
            cross.append(1.0 - np.var(res2 - fitted_cross) / np.var(res2) if np.var(res2) > 0 else np.nan)
        report["tissues"][tissue] = {
            "lines": len(sv.library.lines),
            "corr_drug_effects_SV_vs_VS": {k: float(np.corrcoef(x, y)[0, 1]) for k, (x, y) in pairs.items()},
            "sd_drug_effects_SV": {k: float(np.std(x)) for k, (x, _) in pairs.items()},
            "sd_drug_effects_VS": {k: float(np.std(y)) for k, (_, y) in pairs.items()},
            "median_in_sample_r2_SV": float(np.nanmedian(r2_sv)), "median_in_sample_r2_VS": float(np.nanmedian(r2_vs)),
            "median_cross_orientation_r2": float(np.nanmedian(cross))}
    out.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    print(json.dumps(report["tissues"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
