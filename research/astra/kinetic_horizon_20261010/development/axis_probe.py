"""Feasibility probe (development): is the candidate 2,000-gene order usable as STATE's input axis
for MIX-Seq cells?  Uses only DMSO/basal cells (no treated MIX-Seq cell is read).

A. Tahoe biology on the candidate order: Tirosh S / G2M marker columns vs Tahoe's own phase codes.
B. Cross-platform identity: MIX-Seq 24 h control profiles of the 21 shared lines, projected on the
   candidate order, must pick their own line among 50 Tahoe basal profiles; null = permuted order.
"""
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
GENES = json.loads((ROOT / "research/decision_value/axis_recovery_20261010/authority/sources/RHAISTER_splits__tahoe__static_2k_genes.json").read_text())
EXPR = ROOT / "data/external/tahoe_phenotype_20261010/expression"
G2M = "HMGB2 CDK1 NUSAP1 UBE2C BIRC5 TPX2 TOP2A NDC80 CKS2 NUF2 CKS1B MKI67 TMPO CENPF TACC3 FAM64A SMC4 CCNB2 CKAP2L CKAP2 AURKB BUB1 KIF11 ANP32E TUBB4B GTSE1 KIF20B HJURP CDCA3 HN1 CDC20 TTK CDC25C KIF2C RANGAP1 NCAPD2 DLGAP5 CDCA2 CDCA8 ECT2 KIF23 HMMR AURKA PSRC1 ANLN LBR CKAP5 CENPE CTCF NEK2 G2E3 GAS2L3 CBX5 CENPA".split()
SG = "MCM5 PCNA TYMS FEN1 MCM2 MCM4 RRM1 UNG GINS2 MCM6 CDCA7 DTL PRIM1 UHRF1 MLF1IP HELLS RFC2 RPA2 NASP RAD51AP1 GMNN WDR76 SLBP CCNE2 UBR7 POLD3 MSH2 ATAD2 RAD51 RRM2 CDC45 CDC6 EXO1 TIPIN DSCC1 BLM CASP8AP2 USP1 CLSPN POLA1 CHAF1B BRIP1 E2F8".split()
split = json.loads((HERE.parent / "SPLIT.json").read_text())
out = {}
# A. phase-marker columns in Tahoe basal cells (pooled over 50 lines, within-line centred)
X, ph = [], []
tahoe_mean = {}
for f in split["lines"]:
    z = np.load(EXPR / f / "basal.npz")
    x = z["x"].astype(np.float32)
    tahoe_mean[f] = x.mean(0)
    X.append(x - x.mean(0)); ph.append(z["phase"])
X = np.concatenate(X); ph = np.concatenate(ph)
cats = json.loads((ROOT / "research/astra/phenotype_anchor_20261010/obs/c0.h5ad.json").read_text())["categories"]["phase"]
code = {p: cats.index(p) for p in ("G1", "S", "G2M")}
def score(cols, a, b):
    m = X[:, cols].mean(1)
    return float(m[ph == code[a]].mean() - m[ph == code[b]].mean())
gidx = {g: i for i, g in enumerate(GENES)}
g2m_cols = [gidx[g] for g in G2M if g in gidx]; s_cols = [gidx[g] for g in SG if g in gidx]
rng = np.random.default_rng(0)
null = [score(rng.choice(2000, len(g2m_cols), replace=False), "G2M", "G1") for _ in range(200)]
out["A_n_g2m_markers_in_list"] = len(g2m_cols); out["A_n_s_markers_in_list"] = len(s_cols)
out["A_g2m_markers_G2M_minus_G1"] = score(g2m_cols, "G2M", "G1")
out["A_s_markers_S_minus_G1"] = score(s_cols, "S", "G1")
out["A_null_random_cols_mean_sd"] = [float(np.mean(null)), float(np.std(null))]
# B. cross-platform identity of the 21 shared lines
a = ad.read_h5ad(ROOT / "data/external/mixseq_scperturb/mcfarland_2020.h5ad", backed="r")
o = a.obs
dep2file = {v["depmap_id"]: f for f, v in split["lines"].items() if v["depmap_id"]}
mask = (o.perturbation.astype(str) == "control") & (o.time.astype(str) == "24") & (o.cell_quality.astype(str) == "normal") & o.DepMap_ID.astype(str).isin(dep2file)
idx = np.flatnonzero(mask.to_numpy())
var = list(a.var.index.astype(str))
vpos = {g: i for i, g in enumerate(var)}
shared = [g for g in GENES if g in vpos]
cols_t = np.array([gidx[g] for g in shared]); cols_m = np.array([vpos[g] for g in shared])
sub = a[idx].to_memory()
Xm = sub.X
tot = np.asarray(Xm.sum(1)).ravel()
Xm = Xm[:, cols_m].toarray() if hasattr(Xm, "toarray") else Xm[:, cols_m]
target = float(np.median(tot))
Xm = np.log1p(Xm / tot[:, None] * target)
lines_m = sub.obs.DepMap_ID.astype(str).to_numpy()
mix_mean = {d: Xm[lines_m == d].mean(0) for d in np.unique(lines_m)}
out["B_cells_per_line"] = {split["lines"][dep2file[d]]["name"]: int((lines_m == d).sum()) for d in mix_mean}
files = list(split["lines"]); T = np.array([tahoe_mean[f][cols_t] for f in files]); T = T - T.mean(0)
def identity(perm=None):
    ranks = []
    Mc = np.array([mix_mean[d] for d in mix_mean]); Mc = Mc - Mc.mean(0)
    Tc = T if perm is None else T[:, perm]
    for k, d in enumerate(mix_mean):
        r = np.array([np.corrcoef(Mc[k], Tc[j])[0, 1] for j in range(len(files))])
        ranks.append(int((r > r[files.index(dep2file[d])]).sum()) + 1)
    return ranks
ranks = identity()
out["B_target_sum_used"] = target
out["B_identity_ranks"] = ranks
out["B_top1"] = float(np.mean(np.array(ranks) == 1))
nulls = [float(np.mean(np.array(identity(rng.permutation(len(shared)))) == 1)) for _ in range(20)]
out["B_null_top1_mean"] = float(np.mean(nulls))
out["n_shared_genes"] = len(shared)
print(json.dumps(out, indent=1))
(HERE / "axis_probe.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
