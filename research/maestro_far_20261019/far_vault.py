"""One reused-vault evaluation (block-N sealed drug names: opened once by block N, so NOT independent). Frozen code/model only.
Q = vault drugs (fold 9); references = all dev folds, Tanimoto-purged. Same policies and primary repair (gate) as the test stage."""
import json, pickle, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import far_core as fc
import far_data
from far_run import sha, pairs, boot_auc, POLICIES, REPAIRS

out = HERE / "records_vault.npz"
if out.exists():
    raise SystemExit("write-once: vault records exist")
fz = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
for f, h in fz["hashes"].items():
    if sha(HERE / f) != h:
        raise SystemExit(f"FREEZE_MISMATCH {f}")
src = (HERE / "far_data.py").read_text(encoding="utf-8").replace('if (nm in sealed) == (tier == "vault"):', "if True:")
src = src.replace("fold=np.array([fold_of(m) for m in fam])", "fold=np.array([9 if d in sealed else fold_of(m) for d, m in zip(drug, fam)])")
ns = {"__name__": "far_data_all", "__file__": str(HERE / "far_data.py")}
exec(compile(src, "far_data_all", "exec"), ns)
D = ns["load"]("both")
print("combined", len(D["drug"]), "vault", int((D["fold"] == 9).sum()))
fam_ids = {f: i for i, f in enumerate(np.unique(D["family"]))}
D["famid"] = np.array([fam_ids[f] for f in D["family"]])
m = json.loads((HERE / "MODEL.json").read_text(encoding="utf-8")); beta, b0, tau = np.array(m["coef"]), m["intercept"], m["tau"]
vm = pickle.load(open(HERE / "VALUE_MODEL.pkl", "rb"))
fmodel = lambda c, j: 1 / (1 + np.exp(-(fc.false_prog_features(c, j) @ beta + b0)))
vmodel = lambda c, j: np.clip(vm.predict(fc.value_features(c, j)), 0, None)
c = fc.Campaign(D, 9, (0, 1, 2, 3, 4)); c.famid = D["famid"][c.q]
print("|Q|", len(c.q), "|R|", len(c.r), "lines", len(c.lines), "sig", c.has_sig.mean())
rng = np.random.default_rng(20261019)
X, y, fam = pairs(c, rng)
atlas = {"n_pairs": int(len(y)), "signatures": {n: dict(zip(("auroc", "lcb90", "ucb90"), boot_auc(X[:, k], y, fam))) for k, n in enumerate(["domain_distance", "neighbour_dispersion", "model_disagreement"])}}
rec = {}
runs = [(p, "gate") for p in POLICIES] + [(p, r) for p in ("exploit", "far") for r in REPAIRS if r != "gate"]
for p, r in runs:
    contrib, hits, frac = fc.run_policy(c, p, r, tau, vmodel if p == "far2" else fmodel, 20261019 + 9)
    rec[f"9|{p}|{r}"] = contrib; rec[f"9|{p}|{r}|hits"] = hits
rec["9|fam"] = c.famid
np.savez(out, **rec)
(HERE / "ATLAS_vault.json").write_text(json.dumps(atlas, indent=1) + "\n", encoding="utf-8")
print(json.dumps(atlas, indent=1))
