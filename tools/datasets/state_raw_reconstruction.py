"""Strict axis-bound raw-UMI conversion; external input remains uncertified."""
import numpy as np


def convert_counts(counts, ensembl_ids, contract, *, research_reconstruction=False):
    if not research_reconstruction:
        raise ValueError("external RNA not certified: provider preprocessing provenance remains unknown")
    if list(ensembl_ids)!=contract['raw_ensembl_axis']:
        raise ValueError("raw Ensembl axis/version mismatch; missing or duplicate genes forbidden")
    values=np.asarray(counts,dtype=np.float64)
    if values.ndim!=2 or values.shape[1]!=len(ensembl_ids):
        raise ValueError('raw count matrix shape mismatch')
    if not np.isfinite(values).all() or (values<0).any() or not np.equal(values,np.floor(values)).all():
        raise ValueError('finite nonnegative integer UMI counts required')
    totals=values.sum(axis=1)
    if (totals<=0).any():raise ValueError('empty RNA library')
    # Normalize BEFORE selecting the fixed official model axis.
    return np.log1p(values[:,contract['source_indices']]*10000/totals[:,None]).astype(np.float32)
