"""Shared paths, endpoint and campaign rules for the indication-triage study.

File summary
- Path: research/indication_triage_20261016/common.py
- Purpose: one place for every rule the arms and the grader must share, so the development run
  on PRISM 19Q4 and the sealed run on PRISM 24Q2 apply the same code.
- Core points:
  - The endpoint is inherited unchanged from `research/knowledge_reality_20261013` (PROTOCOL.md
    section 5): selective residual on the generic profile G, robust z, event = z <= -3 and
    log2 FC <= -1, active = at least 5 events.
  - Campaign size (64 compounds), follow-up list size (32 pairs) and the per-compound cap (3) are
    inherited from the same protocol's H2 and `confirm.py`.
  - Tie-breaks and campaign membership come from salted hashes of the Broad core, so they are
    identical for every arm and independent of any outcome.
- Interfaces: paths, `write_json`, `sha256`, `h`, `residualise`, `robust_z`, `events`,
  `tie_break`, `nominate`, `campaigns`, `sign_flip`, `tanimoto`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / "tmp/indication_triage_20261016"
PRISM = ROOT / "data/external/prism_19q4/raw"
PRISM_LFC = PRISM / "primary-screen-replicate-collapsed-logfold-change.csv"
PRISM_TREATMENTS = PRISM / "primary-screen-replicate-collapsed-treatment-info.csv"
PRISM_SECONDARY_REPLICATES = PRISM / "secondary-screen-logfold-change.csv"
PRISM_SECONDARY_REPLICATE_INFO = PRISM / "secondary-screen-replicate-treatment-info.csv"
DEPMAP_INFO = ROOT / "data/external/depmap_19q4/sample_info.csv"
KNOWLEDGE_STUDY = ROOT / "research/knowledge_reality_20261013"
DEV_COMPOUNDS = KNOWLEDGE_STUDY / "compounds.csv"          # 4,528 cores with MoA-family folds 0-4
SEALED_CENSUS = KNOWLEDGE_STUDY / "SEALED_CENSUS.json"      # 545 panel lines, 1,229 eligible cores
SEALED_COMPOUNDS = KNOWLEDGE_STUDY / "sealed_compounds.csv"
SEALED_OUTCOME_NAME = "Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv"
SEALED_OUTCOME_MD5 = "042b15d3ebcc138a80a571b9286451ae"

SEED = 20261016
CAMPAIGN = 64          # compounds per campaign (knowledge_reality confirm.CAMPAIGN)
FOLLOW_UP = 32         # (compound, line) pairs per campaign follow-up list (confirm.BUDGET)
CAP = 3                # follow-up pairs per compound (develop.CAP)
Z_EVENT = -3.0         # robust z of the selective residual (knowledge_reality section 5)
LFC_EVENT = -1.0       # log2 fold change
MIN_EVENTS_ACTIVE = 5
MIN_MEASURED_LINES = 100


def write_json(path: Path, data) -> None:
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def h(key: str, salt: str) -> int:
    return int(hashlib.sha256(f"{salt}:{key}".encode()).hexdigest(), 16)


def residualise(M: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Remove each row's intercept and slope on G over its finite entries (NaN stays NaN)."""

    out = np.full(M.shape, np.nan)
    for i, y in enumerate(M):
        f = np.isfinite(y) & np.isfinite(G)
        if f.sum() < 10:
            continue
        X = np.column_stack([np.ones(f.sum()), G[f]])
        beta, *_ = np.linalg.lstsq(X, y[f], rcond=None)
        out[i, f] = y[f] - X @ beta
    return out


def robust_z(S: np.ndarray) -> np.ndarray:
    med = np.nanmedian(S, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(S - med), axis=1, keepdims=True) * 1.4826
    return (S - med) / np.maximum(mad, 1e-6)


def events(Y: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Selective events of measured profiles: the registered endpoint, identical for every arm."""

    with np.errstate(invalid="ignore"):
        return (robust_z(residualise(Y, G)) <= Z_EVENT) & (Y <= LFC_EVENT)


def tie_break(cores, L: int) -> np.ndarray:
    """A fixed pseudo-random order of (compound, line) pairs from a salted hash of the core."""

    return np.stack([np.random.default_rng(h(str(c), "tie") % (2 ** 32)).random(L) for c in cores])


def nominate(score: np.ndarray, cores, budget: int = FOLLOW_UP, cap: int = CAP) -> list[tuple[int, int]]:
    """Top `budget` (compound, line) pairs by score, at most `cap` per compound; higher is better."""

    n, L = score.shape
    flat = np.where(np.isfinite(score), score, -np.inf) + tie_break(cores, L) * 1e-9
    order = np.argsort(-flat, axis=None)
    picked, per = [], {}
    for k in order:
        i, l = divmod(int(k), L)
        if not np.isfinite(flat[i, l]):
            break
        if per.get(i, 0) >= cap:
            continue
        picked.append((i, l))
        per[i] = per.get(i, 0) + 1
        if len(picked) == budget:
            break
    return picked


def campaigns(cores, size: int = CAMPAIGN) -> list[np.ndarray]:
    """Index groups of up to `size` compounds, ordered by a salted hash of the core."""

    order = sorted(range(len(cores)), key=lambda i: h(str(cores[i]), "campaign"))
    return [np.array(order[s:s + size]) for s in range(0, len(order), size)]


def sign_flip(diff: np.ndarray, draws: int = 20000, seed: int = SEED) -> dict:
    """One-sided paired sign-flip test of mean(diff) > 0 (exact when 2^n <= draws)."""

    d = np.asarray(diff, dtype=float)
    n = len(d)
    if n == 0:
        return {"n": 0, "mean": None, "p": None}
    obs = d.mean()
    if 2 ** n <= draws:
        signs = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1) * 2 - 1
    else:
        signs = np.random.default_rng(seed).choice([-1, 1], size=(draws, n))
    null = (signs * d).mean(1)
    p = float((1 + (null >= obs - 1e-12).sum()) / (len(null) + 1))
    return {"n": n, "mean": float(obs), "sd": float(d.std(ddof=1)) if n > 1 else None, "p": p}


def tanimoto(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    A = A.astype(np.float32)
    B = B.astype(np.float32)
    inter = A @ B.T
    union = A.sum(1)[:, None] + B.sum(1)[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1.0), 0.0)
