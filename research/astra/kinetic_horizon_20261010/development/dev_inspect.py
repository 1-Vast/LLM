"""Development: raw rows for a few drugs on dev lines (sanity of signs)."""
import sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import horizon_data as H
A, P = H.A, H.P
sp = H.split(); dev = sp["development"]
keep, info = A.qualified_reference()
E = H.early_panel(keep)
L = H.load_late("development"); ld = list(L["drugs"])
table = info["table"]
for drug in ("Trametinib", "Gemcitabine", "vincristine", "Docetaxel"):
    j = E.drugs.index(drug); jl = ld.index(drug)
    print("\n", drug, "line | n_treat | G1frac_dmso G1frac_trt | g24 k24 s24 | PRISM_lfc2.5 sec_mean")
    lab = [l for (f, l, p) in table if f == dev[0] and A.drug_of(l) == drug and A.dose_of(l) == 5.0][0]
    for i, f in enumerate(dev):
        e = keep.index(f)
        rows = [(table[(f, lab, p)], table[(f, P.DMSO, p)]) for (ff, l, p) in table if ff == f and l == lab]
        t = {k: sum(r[0][k] for r in rows) for k in ("n", "G1", "S", "G2M")}
        b = {k: sum(r[1][k] for r in rows) for k in ("n", "G1", "S", "G2M")}
        print(f"{E.names[f]:>12} | {t['n']:5d} | {b['G1']/b['n']:.2f} {t['G1']/max(t['n'],1):.2f} | {E.g24[e,j]:+.2f} {E.k24[e,j]:+.2f} {E.s24[e,j]:+.2f} | {L['primary_2p5'][i,jl]:+.2f} {L['secondary_mean'][i,jl]:+.2f}")
