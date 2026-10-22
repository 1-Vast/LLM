"""Train one world-model variant for one stage/fold and save held-out predictions at the requested epoch checkpoints.
usage: python run_models.py STAGE HELDOUT VARIANT SEED CKPTS HIDDEN OUTDIR       (CKPTS: comma list of epochs, e.g. 15,30,45; training stops at the last)
STAGE: dev | sel | final.  HELDOUT: a lineage/stock name (dev, sel) or 'ALL' (final).
Training backgrounds: dev -> dev minus held-out; sel -> dev + sel minus held-out; final -> dev + sel.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, torch
import ptv_data as D, ptv_tasks as T, ptv_models as M

stage, held, variant, seed, ckpts, hidden, outdir = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), [int(e) for e in sys.argv[5].split(",")], int(sys.argv[6]), Path(sys.argv[7])
torch.set_num_threads(4)
DEV = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
P = T.Prep(); ex = P.R.experiments()
train_parts = {"dev": ["dev"], "sel": ["dev", "sel"], "final": ["dev", "sel"]}[stage]
if stage == "final":
    D.require_stage("final")
    test = ex[ex.part == "final"]
else:
    test = ex[ex.lineage == D.lineage_of(held)]
train = ex[ex.part.isin(train_parts) & ~ex.lineage.isin(test.lineage.unique())]
items, train = P.items(train)
tens = M.make_tensors(items)
titems, test = P.items(test, with_outcome=True)
tt = M.make_tensors(titems)
m = M.PPODE(5585, 935, hidden=hidden, variant=variant).to(DEV)
outdir.mkdir(parents=True, exist_ok=True)
tag = f"{stage}_{held}_{variant}_s{seed}"
store = {}
t0 = time.time()


def log(ep, tot):
    if ep + 1 in ckpts:
        y, p = M.predict(m, tt)
        store[f"p_e{ep + 1}"] = p
        store[f"ypred_e{ep + 1}"] = y.astype("float16") if y is not None else np.zeros(1, "float16")
        store[f"loss_e{ep + 1}"] = np.array(tot)


M.train(m, tens, epochs=max(ckpts), seed=seed, log=log)
last = max(ckpts)
torch.save(m.state_dict(), outdir / f"{tag}.pt")
np.savez_compressed(outdir / f"{tag}.npz", perts=test.perts.values, cell=test.cell.values, lab=tt["lab"].numpy(), single=tt["single"].numpy(),
                    p=store[f"p_e{last}"], ypred=store[f"ypred_e{last}"], ytrue=tt["y"].numpy().astype("float16"), yobs=tt["yobs"].numpy().astype("uint8"),
                    x=tt["x"].numpy().squeeze(-1).astype("float16"), **store)
json.dump({"stage": stage, "held": held, "variant": variant, "seed": seed, "ckpts": ckpts, "hidden": hidden, "n_train": len(items), "n_test": len(titems),
           "device": str(DEV), "train_cells": sorted(train.cell.unique().tolist()), "seconds": time.time() - t0}, open(outdir / f"{tag}.json", "w"))
print(tag, "done", round(time.time() - t0))
