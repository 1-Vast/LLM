"""Post-outcome all-fixed-policy and measured-rank diagnostics, not a new primary."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from research.astra.gdsc_transport import digest, save
from research.astra.gdsc_layout_validation import PAIR

OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "research/astra/results/20261002_gdsc_layout_evaluation_v1/policy_evaluation.csv"
if (OUT / "summary.json").exists():
    raise FileExistsError("use a new directory")
panel = pd.read_csv(SOURCE)
rows = []
for label,g in [("all",panel),*[(str(k),v) for k,v in panel.groupby("DRUGSET_ID")]]:
    w = 1. / g.groupby("unit").unit.transform("size").to_numpy()
    values = g[PAIR].to_numpy()
    q = g[["q_PLX","q_PD"]].to_numpy()
    selected = g.C2_action.to_numpy(dtype=int)
    measured_contrast = values[:,1] - values[:,0]
    forecast_contrast = q[:,1] - q[:,0]
    tied = np.abs(measured_contrast) <= 1e-12
    correct = ((selected == 1) == (measured_contrast > 0)) & ~tied
    rows.append(dict(layout=label,scans=len(g),
        fixed_PLX_value=float(np.average(values[:,0],weights=w)),
        fixed_PD_value=float(np.average(values[:,1],weights=w)),
        C2_minus_fixed_PLX_pp=float(np.average(g.C2_utility-values[:,0],weights=w)*100),
        C2_minus_fixed_PD_pp=float(np.average(g.C2_utility-values[:,1],weights=w)*100),
        measured_rank_correct=int(correct.sum()),measured_rank_wrong=int((~correct & ~tied).sum()),
        measured_rank_numeric_tie=int(tied.sum()),
        measured_winner_PLX=int((measured_contrast < -1e-12).sum()),
        measured_winner_PD=int((measured_contrast > 1e-12).sum()),
        predicted_contrast_mean_pp=float(np.average(forecast_contrast,weights=w)*100),
        observed_contrast_mean_pp=float(np.average(measured_contrast,weights=w)*100),
        contrast_mean_error_pp=float(np.average(forecast_contrast-measured_contrast,weights=w)*100),
        all_action_RMSE=float(np.sqrt(np.average(np.mean((q-values)**2,axis=1),weights=w))),
        measured_rank_scope="single published paired readout, not a certified true or mechanism ranking"))
save(OUT / "summary.json",dict(status="post-outcome diagnostics; no change to frozen model/primary/menu",
    source_sha256=digest(SOURCE),analysis_sha256=digest(__file__),comparisons=rows,
    no_target_selected_replacement_policy=True,physical_CI=None,
    conclusion="positive development-fixed contrast does not establish superiority to both fixed actions"))
save(OUT / "manifest.json",{p.name:digest(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"})
print((OUT / "summary.json").read_text())
