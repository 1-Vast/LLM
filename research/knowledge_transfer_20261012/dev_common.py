"""Shared loading for block Q development on the phase-1 tier (GSE92742)."""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np

import knowledge as K

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PHASE1 = ROOT / "data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz"
CACHE = HERE / "cache"
N_FOLDS = 5


def fold_of(key: str, n: int = N_FOLDS) -> int:
    return int(hashlib.sha256(("blockq-dev:" + key).encode()).hexdigest(), 16) % n


@lru_cache(maxsize=1)
def load_phase1():
    z = np.load(PHASE1, allow_pickle=True)
    return {k: z[k] for k in z.files}


def knowledge_tokens(records, *, include_binding: bool = False):
    vocab: dict[str, int] = {}
    rows = []
    for r in records:
        toks = {"t:" + g for g in r.signed_targets(include_binding=include_binding)}
        toks |= {"m:" + m for m in r.hub_moa}
        rows.append(toks)
        for t in toks:
            vocab.setdefault(t, len(vocab))
    M = np.zeros((len(records), len(vocab)), dtype=bool)
    for i, toks in enumerate(rows):
        for t in toks:
            M[i, vocab[t]] = True
    return M, vocab


@lru_cache(maxsize=1)
def phase1_knowledge():
    CACHE.mkdir(exist_ok=True)
    path = CACHE / "phase1_knowledge.npz"
    z = load_phase1()
    records = K.phase1_records(z)
    if path.exists():
        fps = np.load(path)["fps"]
    else:
        fps = K.morgan_matrix([r.smiles for r in records])
        np.savez_compressed(path, fps=fps)
    know, vocab = knowledge_tokens(records)
    targets = [r.signed_targets() for r in records]
    return records, fps, know, vocab, targets


def vehicle_thresholds(z, q: float = 0.95) -> np.ndarray:
    """Per-line norm threshold above which a response counts as active (vehicle quantile)."""
    lines = list(z["line"])
    norms = np.linalg.norm(z["vehicle"].astype(np.float64), axis=1)
    return np.array([np.quantile(norms[z["vehicle_line"] == l], q) for l in lines])
