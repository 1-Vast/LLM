import sys
import numpy as np
import pandas as pd
cl = pd.read_csv(sys.argv[1], dtype=str)
cl["core"] = cl.IDs.str.extract(r"(BRD-[A-Z]\d{8})")[0]
sealed = pd.read_csv(sys.argv[2], dtype=str)
both = cl[cl.core.isin(set(sealed.core))].groupby("core").filter(lambda g: g.screen.nunique() > 1)
print(both[["screen", "IDs", "Drug.Name"]].to_string())
l1 = np.load(sys.argv[3], allow_pickle=True)
have = np.isfinite(l1["x"][:, :, 0]).any(axis=1)
withl1 = set(np.asarray(l1["key"])[have])
print("overlap cores with L1000:", sorted(set(both.core) & withl1))
o = np.load("D:/MAESTRO/data/external/prism_19q4/derived/block_n_prism_open.npz", allow_pickle=True)
s = np.load("D:/MAESTRO/data/external/prism_19q4/derived/block_n_prism_sealed.npz", allow_pickle=True)
pool = set(map(str, np.concatenate([o["drug"], s["drug"]])))
names = set(both["Drug.Name"].str.lower())
print("overlap names in dev pool:", sorted(n for n in names if n in {p.lower() for p in pool}))
print("l1 keys sample:", list(l1["key"][:3]))
