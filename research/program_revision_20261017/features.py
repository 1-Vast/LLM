"""Pre-treatment features for lines and drugs, with their measurement programs and costs.

File summary
- Path: research/program_revision_20261017/features.py
- Purpose: build every legal decision-time input once, and say what each costs to obtain.
- Line features (pre-treatment; none is a drug response):
  - ``lineage``: primary tissue one-hot. Free: known when a sample is received.
  - ``panel``: status of the 50 genes of the Ion AmpliSeq Cancer Hotspot Panel v2 (a fixed,
    commercially defined DNA panel, chosen from prior knowledge, not from these data). Status = any
    DepMap 19Q4 mutation flagged TCGA/COSMIC hotspot or deleterious. Genes with < 5 mutated
    eligible lines are dropped (metadata-only rule). Cost: one targeted DNA assay per line.
  - ``expr``: log2(TPM+1) of the 2,000 genes with the largest variance over SOURCE lines,
    standardised with source-line mean/SD. A marker panel of <= 20 genes is one targeted RNA
    assay; the full transcriptome is one RNA-seq assay. Both are costed acquisitions.
  - ``rna_pcs``: 30 principal components of ``expr`` fitted on source lines (needs RNA-seq).
- Drug features (legal for unseen drugs): Morgan radius-2 2048-bit fingerprint, MoA tokens and
  target tokens from the Repurposing Hub annotation (vocabularies from SOURCE drugs only).
  No drug identifier, response loading or outcome-derived quantity is a feature.
- Interfaces: `MEASUREMENT_COSTS`, `line_features()`, `drug_features()`, `tokens`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import CACHE, EXPR, HERE, MUT, sha256

AMPLISEQ_V2 = [
    "ABL1", "AKT1", "ALK", "APC", "ATM", "BRAF", "CDH1", "CDKN2A", "CSF1R", "CTNNB1", "EGFR",
    "ERBB2", "ERBB4", "EZH2", "FBXW7", "FGFR1", "FGFR2", "FGFR3", "FLT3", "GNA11", "GNAS", "GNAQ",
    "HNF1A", "HRAS", "IDH1", "IDH2", "JAK2", "JAK3", "KDR", "KIT", "KRAS", "MET", "MLH1", "MPL",
    "NOTCH1", "NPM1", "NRAS", "PDGFRA", "PIK3CA", "PTEN", "PTPN11", "RB1", "RET", "SMAD4",
    "SMARCB1", "SMO", "SRC", "STK11", "TP53", "VHL",
]

# Declared resource units per line. They are kept as separate resources; no conversion into
# wells is claimed. "round" is one 5-day assay cycle before a later decision can use a readout.
MEASUREMENT_COSTS = {
    "lineage": {"assay": "none", "units": 0},
    "panel": {"assay": "targeted_dna_panel", "units": 1},
    "marker_panel": {"assay": "targeted_rna_panel_<=20_genes", "units": 1},
    "rna_seq": {"assay": "rna_seq", "units": 1},
    "probe": {"assay": "single_line_well_2.5uM", "units_per_probe": 1, "rounds": 1},
    "confirmation": {"assay": "two_replicate_wells_2.5uM", "units": 2},
}


def tokens(v) -> list[str]:
    if not isinstance(v, str):
        return []
    return sorted({t.strip() for t in v.split(",") if t.strip()})


def line_features(lines: pd.DataFrame) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "line_features.npz"
    key = "|".join(lines.depmap_id) + sha256(EXPR) + sha256(MUT)
    if path.exists():
        z = np.load(path, allow_pickle=False)
        if z["key"].item() == key:
            return {k: z[k] for k in z.files if k != "key"}
    ids = lines.depmap_id.tolist()
    src = (lines.line_split == "source").to_numpy()
    lin_names = sorted(set(lines.primary_tissue))
    lineage = np.array([[t == n for n in lin_names] for t in lines.primary_tissue], float)
    mut = pd.read_csv(MUT, usecols=["Hugo_Symbol", "DepMap_ID", "isDeleterious", "isTCGAhotspot",
                                    "isCOSMIChotspot", "Variant_Classification"], low_memory=False)
    mut = mut[mut.DepMap_ID.isin(set(ids)) & mut.Hugo_Symbol.isin(AMPLISEQ_V2)
              & (mut.Variant_Classification != "Silent")]
    flag = (mut.isTCGAhotspot.astype(str) == "True") | (mut.isCOSMIChotspot.astype(str) == "True") \
        | (mut.isDeleterious.astype(str) == "True")
    mut = mut[flag]
    pos = {i: k for k, i in enumerate(ids)}
    panel_all = np.zeros((len(ids), len(AMPLISEQ_V2)))
    for g, i in zip(mut.Hugo_Symbol, mut.DepMap_ID):
        panel_all[pos[i], AMPLISEQ_V2.index(g)] = 1.0
    keep = panel_all.sum(0) >= 5
    panel = panel_all[:, keep]
    panel_genes = [g for g, k in zip(AMPLISEQ_V2, keep) if k]
    ex = pd.read_csv(EXPR, index_col=0)
    ex = ex.reindex(ids)
    genes = np.array([c.split(" (")[0] for c in ex.columns])
    E = ex.to_numpy(float)
    var = np.nanvar(E[src], axis=0)
    top = np.argsort(-var)[:2000]
    E = E[:, top]
    mu, sd = np.nanmean(E[src], 0), np.nanstd(E[src], 0) + 1e-6
    Z = np.nan_to_num((E - mu) / sd)
    _, _, Wt = np.linalg.svd(Z[src] - Z[src].mean(0), full_matrices=False)
    pcs = (Z - Z[src].mean(0)) @ Wt[:30].T
    pcs = pcs / (pcs[src].std(0) + 1e-9)
    out = dict(lineage=lineage, lineage_names=np.array(lin_names), panel=panel,
               panel_genes=np.array(panel_genes), expr=Z, expr_genes=genes[top], rna_pcs=pcs)
    np.savez_compressed(path, key=np.array(key), **out)
    return out


def drug_features(drugs: pd.DataFrame) -> dict:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator

    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fp = np.zeros((len(drugs), 2048))
    for i, s in enumerate(drugs.smiles):
        mol = Chem.MolFromSmiles(str(s).split(",")[0].strip())
        fp[i] = gen.GetFingerprintAsNumPy(mol)
    src = (drugs.drug_split == "source").to_numpy()
    moa = [tokens(v) for v in drugs.moa]
    tgt = [tokens(v) for v in drugs.target]
    moa_vocab = sorted({t for r, s in zip(moa, src) if s for t in r})
    tgt_vocab = sorted({t for r, s in zip(tgt, src) if s for t in r})
    M = np.array([[t in r for t in moa_vocab] for r in moa], float)
    T = np.array([[t in r for t in tgt_vocab] for r in tgt], float)
    return dict(fp=fp, moa=M, moa_vocab=np.array(moa_vocab), target=T,
                target_vocab=np.array(tgt_vocab), moa_tokens=moa, target_tokens=tgt)
