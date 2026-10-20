"""Reload stored fitted programs and reproduce a nomination from the stored probe sequence WITHOUT refitting, API calls or hidden outcomes.

Inputs are the per-stream model file (the actual fitted programs deployed for a batch), the stored prior, the public monotherapy features of the cell
and the stored probe/value sequence. Used by the verifier and by the reload-equality test.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import iv_core as C  # noqa: E402


def unpack_fits(z, prefix: str):
    """z: npz mapping; prefix like 'inh_kg|b2'. Returns the list of Fitted exactly as deployed."""
    pids = sorted({k[len(prefix) + 1:].split("|")[0] for k in z.files if k.startswith(prefix + "|") and k.endswith("|meta")})
    order = {"N": 0, "U": 1, "C": 2}
    pids.sort(key=lambda p: (order.get(p, 3), p))
    fits = []
    for pid in pids:
        meta = json.loads(str(z[f"{prefix}|{pid}|meta"]))
        prog = C.Program(pid, meta["kind"], gates=tuple(meta["gates"]), k=meta["k"], conj=tuple(tuple(c) for c in meta["conj"]))
        f = C.Fitted(prog, np.asarray(z[f"{prefix}|{pid}|sigma"]), version=meta["version"])
        if f"{prefix}|{pid}|states" in z.files:
            f.states = np.asarray(z[f"{prefix}|{pid}|states"])
            f.logprior = np.asarray(z[f"{prefix}|{pid}|logprior"])
            f.mu = np.asarray(z[f"{prefix}|{pid}|mu"])
        if f"{prefix}|{pid}|V" in z.files:
            f.V = np.asarray(z[f"{prefix}|{pid}|V"])
        fits.append(f)
    return fits


def stored_z1(z, b: int, aref, amin, amax):
    pm, w, fbar = (np.asarray(z[f"prior|b{b}|{k}"]) for k in ("pm", "w", "fbar"))
    F = np.stack([aref, amin, amax], -1)
    return pm + (F - fbar) @ w


def replay_nomination(z, arm: str, b: int, aref, amin, amax, probes, values, pool: np.ndarray):
    """Rebuild the belief from stored programs, apply the stored observations in order, return (nominated list, program weights)."""
    fits = unpack_fits(z, f"{arm}|b{b}")
    z1 = stored_z1(z, b, aref, amin, amax)
    base = aref + z1
    bel = C.make_belief(fits, base)
    recorded = {}
    for p, v in zip(probes, values):
        bel.observe(int(p), v - base[int(p)])
        if pool[int(p)]:
            recorded[int(p)] = v
    score = C.shortlist_scores(bel, pool, recorded)
    return [int(q) for q in C.top_k(score)], bel.program_weights()
