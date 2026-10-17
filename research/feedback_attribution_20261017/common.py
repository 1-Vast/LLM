"""Shared paths, data access, folds and paired statistics for the feedback-attribution study.

File summary
- Path: research/feedback_attribution_20261017/common.py
- Purpose: one place for what every script of this study must do identically.
- Core points:
  - The Beat AML 2.0 domain is the matrix built by `research/context_transfer_20261017/data_beataml.py`
    (520 RNA-seq samples from 479 patients x 166 inhibitors, probit AUC, frozen selective events).
    It is read from that study's cache and checked against the input digests recorded in its
    RESULTS.json. Beat AML is exposed: everything here is development evidence.
  - Outer folds are the confirmation's five patient-disjoint folds (salt
    ``context-transfer-subject``), and tie-breaks use the same hashed order, so records can be
    compared with the confirmation sample by sample.
  - The promoted modules are imported from ``src``. This folder must not contain a module named
    ``agent``, ``virtual_cell`` or ``maestro``.
  - `paired` is the confirmation's patient-cluster bootstrap and sign-flip test, copied unchanged.
  - `schedule_matrix` is design metadata: which inhibitors were on a panel each sample was run
    with (panel inventory = inhibitors ever recorded under that panel name in the raw file).
- Interfaces: paths, `load_domain`, `outer_folds`, `tie`, `paired`, `holm`, `write_json`, `sha256`,
  `basal_pcs`, `schedule_matrix`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.procedure_selection import hash_folds, hash_unit  # noqa: E402

CACHE = ROOT / "tmp" / "feedback_attribution_20261017"
SOURCE_STUDY = ROOT / "research" / "context_transfer_20261017"
DOMAIN_CACHE = ROOT / "tmp" / "context_transfer_20261017" / "beataml_domain.npz"
BEATAML = ROOT / "data" / "external" / "beataml2_20261017"
RAW = BEATAML / "beataml_wv1to4_raw_inhibitor_v4_dbgap.txt"
PROBIT = BEATAML / "beataml_probit_curve_fits_v4_dbgap.txt"
CLIN = BEATAML / "beataml_wv1to4_clinical.xlsx"
FAMILIES = BEATAML / "beataml_drug_families.xlsx"
MAPPING = BEATAML / "beataml_waves1to4_sample_mapping.xlsx"
FOLD_SALT = "context-transfer-subject"
N_FOLDS = 5
SEED = 20261017


def write_json(path, data) -> None:
    """LF bytes, so a digest does not depend on the platform."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes((json.dumps(data, indent=1, default=_plain) + "\n").encode("utf-8"))


def _plain(x):
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.bool_):
        return bool(x)
    raise TypeError(type(x))


def sha256(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def load_domain() -> dict:
    """The confirmation domain, refused if its inputs differ from the ones the confirmation used."""

    z = np.load(DOMAIN_CACHE, allow_pickle=False)
    d = {k: z[k] for k in z.files}
    recorded = json.loads((SOURCE_STUDY / "RESULTS.json").read_text(encoding="utf-8"))["input_sha256"]
    if d["input_sha256"].tolist() != recorded:
        raise SystemExit("DOMAIN_MISMATCH: cached Beat AML domain differs from the confirmation's inputs")
    d["Y"] = d["Y"].astype(float)
    return d


def schedule_matrix(d: dict) -> np.ndarray:
    """Sample x inhibitor: True if the inhibitor was on a panel the sample was run with (cached)."""

    path = CACHE / "schedule.npz"
    if path.exists():
        z = np.load(path, allow_pickle=False)
        if z["raw_sha256"].item() == sha256(RAW) and z["contexts"].tolist() == d["contexts"].tolist():
            return z["scheduled"]
    import pandas as pd
    raw = pd.read_csv(RAW, sep="	", usecols=["dbgap_rnaseq_sample", "inhibitor", "inhibitor_panel"], dtype=str)
    inv = raw.groupby("inhibitor_panel").inhibitor.agg(set).to_dict()
    si = {s: i for i, s in enumerate(d["contexts"])}
    ii = {s: j for j, s in enumerate(d["items"])}
    out = np.zeros((len(si), len(ii)), bool)
    for s, pans in raw[raw.dbgap_rnaseq_sample.isin(si)].groupby("dbgap_rnaseq_sample").inhibitor_panel.agg(set).items():
        for p in pans:
            for it in inv[p]:
                if it in ii:
                    out[si[s], ii[it]] = True
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, scheduled=out, contexts=d["contexts"], raw_sha256=np.array(sha256(RAW)))
    return out


def outer_folds(groups) -> np.ndarray:
    return hash_folds(groups, FOLD_SALT, N_FOLDS)


def tie(items) -> np.ndarray:
    return hash_unit(items, "tie")


def basal_pcs(X: np.ndarray, rows=None, n_genes: int = 2000, n_pcs: int = 30) -> np.ndarray:
    """Basal-expression PCs as the Virtual Cell computes them (top-variance genes, standardised).

    The projection is fitted on ``rows`` (default: all) and applied to every row.
    """

    rows = np.arange(len(X)) if rows is None else np.asarray(rows)
    Xs = X[rows].astype(float)
    genes = np.argsort(-Xs.var(0))[:n_genes]
    mu, sd = Xs[:, genes].mean(0), Xs[:, genes].std(0) + 1e-6
    Z = (X[:, genes] - mu) / sd
    _, _, Wt = np.linalg.svd((Xs[:, genes] - mu) / sd, full_matrices=False)
    return Z @ Wt[:n_pcs].T


def holm(ps: dict) -> dict:
    keys = sorted(ps, key=lambda k: ps[k])
    m = len(keys)
    adj, running = {}, 0.0
    for i, k in enumerate(keys):
        running = max(running, min(1.0, (m - i) * ps[k]))
        adj[k] = running
    return adj


def paired(diff: np.ndarray, groups, draws: int = 10000, boot: int = 2000, seed: int = SEED) -> dict:
    """Paired comparison over samples with patient clusters (copied from the confirmation's common.py).

    Mean of per-sample differences; cluster bootstrap 95% interval (patients resampled with
    replacement, samples kept intact); one-sided sign-flip p over cluster means (mean > 0).
    """

    d = np.asarray(diff, dtype=float)
    groups = np.asarray(groups)
    labels = sorted(set(groups.tolist()))
    index = [np.flatnonzero(groups == g) for g in labels]
    rng = np.random.default_rng(seed)
    sums = np.array([d[i].sum() for i in index])
    sizes = np.array([len(i) for i in index])
    picks = rng.integers(0, len(labels), size=(boot, len(labels)))
    boots = sums[picks].sum(1) / sizes[picks].sum(1)
    cm = sums / sizes
    signs = rng.choice([-1.0, 1.0], size=(draws, len(labels)))
    w = sizes / sizes.sum()
    obs = float((cm * w).sum())
    null = (signs * cm * w).sum(1)
    p = float((1 + (null >= obs - 1e-12).sum()) / (draws + 1))
    return {
        "n_contexts": int(len(d)),
        "n_clusters": int(len(labels)),
        "mean": float(d.mean()),
        "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
        "p_one_sided": p,
        "positive_contexts": int((d > 0).sum()),
        "negative_contexts": int((d < 0).sum()),
    }
