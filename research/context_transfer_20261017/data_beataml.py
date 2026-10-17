"""Confirmation domain: Beat AML 2.0 primary patient samples x single-agent inhibitors.

File summary
- Path: research/context_transfer_20261017/data_beataml.py
- Purpose: build the confirmation domain in the same shape as the PRISM development domain.
  It reads the inhibitor AUC column, so only `confirm.py` may call `load()`, after the freeze.
- Core points:
  - Y: probit-fit AUC (lower = more sensitive) for every single-agent inhibitor in the release's
    own paper-inclusion set, for RNA-seq samples that have basal expression.
  - Contexts: RNA-seq samples. Groups: dbGaP subject, so a patient's samples share a fold and a
    dependence cluster.
  - X: the release's normalised basal expression (genes x samples, transposed). Pre-treatment.
  - Endpoint: the registered selective event with no absolute gate (AUC has no constant that
    matches log2 FC <= -1) and >= 100 measured samples per inhibitor.
  - Mutations (WES calls) are kept as gene-symbol lists for the secondary agent arm only.
- Interfaces: `load()` -> dict like data_prism.load(); `mutations()` -> {rnaseq sample: [genes]}.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import BEATAML, CACHE, selective_events, sha256

PROBIT = BEATAML / "beataml_probit_curve_fits_v4_dbgap.txt"
EXPR = BEATAML / "beataml_waves1to4_norm_exp_dbgap.txt"
MUT = BEATAML / "beataml_wes_wv1to4_mutations_dbgap.txt"
CLIN = BEATAML / "beataml_wv1to4_clinical.xlsx"
ABS_GATE = None
MIN_MEASURED = 100
CACHE_FILE = CACHE / "beataml_domain.npz"


def build() -> dict:
    fits = pd.read_csv(PROBIT, sep="\t", usecols=["dbgap_subject_id", "dbgap_rnaseq_sample",
                                                 "inhibitor", "paper_inclusion", "auc"],
                       dtype={"dbgap_subject_id": str, "dbgap_rnaseq_sample": str, "inhibitor": str})
    fits = fits[fits.paper_inclusion.astype(str).str.upper() == "TRUE"]
    expr = pd.read_csv(EXPR, sep="\t", index_col=0)
    samples = sorted(set(fits.dbgap_rnaseq_sample.dropna()) & set(expr.columns))
    fits = fits[fits.dbgap_rnaseq_sample.isin(samples)]
    Ydf = fits.pivot_table(index="dbgap_rnaseq_sample", columns="inhibitor", values="auc", aggfunc="mean")
    Ydf = Ydf.reindex(index=samples)
    subj = fits.groupby("dbgap_rnaseq_sample").dbgap_subject_id.first().reindex(samples)
    genes = expr.index.to_numpy()
    X = expr[samples].T.to_numpy(dtype=np.float32)
    Y = Ydf.to_numpy(dtype=float)
    events, G = selective_events(Y, ABS_GATE, MIN_MEASURED)
    out = {
        "Y": Y.astype(np.float32), "X": X, "genes": genes.astype(str), "events": events, "G": G,
        "contexts": np.array(samples, dtype=str), "groups": subj.to_numpy().astype(str),
        "items": Ydf.columns.to_numpy().astype(str),
        "input_sha256": np.array([sha256(PROBIT), sha256(EXPR)], dtype=str),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE_FILE, **out)
    return out


def load() -> dict:
    if not CACHE_FILE.exists():
        return build()
    z = np.load(CACHE_FILE, allow_pickle=False)
    return {k: z[k] for k in z.files}


def mutations() -> dict:
    """Protein-altering WES calls per RNA-seq sample, through the clinical sample mapping."""

    m = pd.read_csv(MUT, sep="\t", usecols=["dbgap_sample_id", "symbol", "variant_classification"], dtype=str)
    keep = {"missense_variant", "frameshift_variant", "stop_gained", "inframe_insertion",
            "inframe_deletion", "splice_acceptor_variant", "splice_donor_variant", "start_lost",
            "stop_lost", "protein_altering_variant"}
    m = m[m.variant_classification.apply(lambda v: any(k in str(v) for k in keep))]
    clin = pd.read_excel(CLIN, usecols=["dbgap_dnaseq_sample", "dbgap_rnaseq_sample"], dtype=str)
    dmap = clin.dropna().drop_duplicates().set_index("dbgap_dnaseq_sample").dbgap_rnaseq_sample.to_dict()
    out: dict[str, list[str]] = {}
    for dna, genes in m.groupby("dbgap_sample_id").symbol:
        rna = dmap.get(dna)
        if rna:
            out.setdefault(rna, [])
            out[rna] = sorted(set(out[rna]) | set(genes.dropna()))
    return out
