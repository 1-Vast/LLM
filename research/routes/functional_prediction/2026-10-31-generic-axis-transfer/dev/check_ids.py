import sys
import pandas as pd
cl = pd.read_csv(sys.argv[1], dtype=str)
print(cl.screen.value_counts().to_string())
cl["core"] = cl.IDs.str.extract(r"(BRD-[A-Z]\d{8})")[0]
sealed = pd.read_csv(sys.argv[2], dtype=str)
keys = pd.read_csv(sys.argv[3], sep="\t", dtype=str)
print("keys_24q2 columns:", list(keys.columns)[:8], len(keys))
cores = set(sealed.core)
sub = cl[cl.core.isin(cores)]
print("sealed cores in list:", sub.core.nunique(), "of", len(cores))
print(sub.groupby("core").screen.apply(lambda s: "+".join(sorted(set(s)))).value_counts().to_string())
print("rows per sealed core:", sub.groupby("core").size().value_counts().sort_index().to_string())
print("IDs with no BRD core:", int(cl.core.isna().sum()))
