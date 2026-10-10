"""Compile executable mechanism hypotheses (EMH) into per-option predicted signatures.

An EMH states directions and ordinal levels only. The compiler turns it into a gene-space vector
per option (line x time):

* program at 6 h: +1 on ``proximal_up``, -1 on ``proximal_down``;
* program at 24 h: the 6 h program plus +1 ``late_up`` / -1 ``late_down`` (clipped to [-1, 1]);
* each program is scaled to unit length; an empty program predicts no response;
* level(line, time) = rank(line_response[line]) * rank(magnitude[time]) / 3, ranks none=0 ..
  strong=3, so strong x strong = 3;
* amplitude = beta_t * level, with one slope per time fitted by least squares on **reference
  drugs only**: the projection of each reference signature onto its own class's unit program,
  regressed on the level (through the origin).

The numbers therefore come from reference measurements, the directions and gates from the agent.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from literature import slug

RANK = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}
TIMES = ("6 h", "24 h")


def load_emhs(here: Path, variant: str, classes: list[str]) -> dict[str, dict]:
    out = {}
    for c in classes:
        p = here / "emh" / variant / f"{slug(c)}.json"
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            if rec.get("status") == "ok":
                out[c] = rec["hypothesis"]
    return out


def programs(emh: dict, genes: list[str]) -> dict[str, np.ndarray]:
    pos = {g: i for i, g in enumerate(genes)}
    g6 = np.zeros(len(genes))
    for g in emh.get("proximal_up", []):
        if g in pos:
            g6[pos[g]] += 1
    for g in emh.get("proximal_down", []):
        if g in pos:
            g6[pos[g]] -= 1
    g24 = g6.copy()
    for g in emh.get("late_up", []):
        if g in pos:
            g24[pos[g]] += 1
    for g in emh.get("late_down", []):
        if g in pos:
            g24[pos[g]] -= 1
    out = {}
    for t, v in (("6 h", g6), ("24 h", g24)):
        v = np.clip(v, -1, 1)
        n = np.linalg.norm(v)
        out[t] = v / n if n > 0 else v
    return out


def levels(emh: dict, options: list[str]) -> np.ndarray:
    lv = np.zeros(len(options))
    mag = emh.get("magnitude", {})
    for j, o in enumerate(options):
        line, t = o.split("|")
        m = RANK.get(mag.get("6h" if t == "6 h" else "24h", "none"), 0)
        l_ = RANK.get(emh.get("line_response", {}).get(line, "none"), 0)
        lv[j] = l_ * m / 3.0
    return lv


def unit_programs(emhs: dict[str, dict], genes: list[str], options: list[str]) -> dict[str, np.ndarray]:
    """{class: (n_opt, G) unit program per option (by the option's time)}."""
    out = {}
    for c, e in emhs.items():
        pr = programs(e, genes)
        out[c] = np.stack([pr[o.split("|")[1]] for o in options])
    return out


def fit_slopes(X: np.ndarray, labels: np.ndarray, ref: np.ndarray, emhs: dict[str, dict], genes: list[str],
               options: list[str]) -> dict[str, float]:
    """Least-squares slope (through origin) of observed program projection on level, per time."""
    up = unit_programs(emhs, genes, options)
    num = {t: 0.0 for t in TIMES}
    den = {t: 0.0 for t in TIMES}
    for i in np.where(ref)[0]:
        c = labels[i]
        if c not in emhs:
            continue
        lv = levels(emhs[c], options)
        for j, o in enumerate(options):
            x = X[i, j]
            if np.isnan(x[0]) or lv[j] == 0 or not np.any(up[c][j]):
                continue
            t = o.split("|")[1]
            proj = float(up[c][j] @ x)
            num[t] += lv[j] * proj
            den[t] += lv[j] ** 2
    return {t: (num[t] / den[t] if den[t] > 0 else 0.0) for t in TIMES}


def compile_gene_space(emhs: dict[str, dict], genes: list[str], options: list[str], slopes: dict[str, float]) -> dict[str, np.ndarray]:
    """{class: (n_opt, G) predicted mean signature}."""
    up = unit_programs(emhs, genes, options)
    out = {}
    for c, e in emhs.items():
        lv = levels(e, options)
        beta = np.array([slopes[o.split("|")[1]] for o in options])
        out[c] = up[c] * (beta * lv)[:, None]
    return out


SIM_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}


def load_analogies(here: Path, classes: list[str]) -> dict[str, list[tuple[str, str]]]:
    """{class: [(analog class, similarity), ...]} from ``analogy/<slug>.json`` (agent output, no data)."""
    out = {}
    for c in classes:
        p = here / "analogy" / f"{slug(c)}.json"
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            if rec.get("status") == "ok":
                out[c] = [(a["class"], a["similarity"]) for a in rec["analogy"]["analogs"]]
    return out


def compile_analogies(analogies: dict[str, list[tuple[str, str]]], class_means: dict[str, tuple[np.ndarray, int]],
                      generic: np.ndarray) -> dict[str, np.ndarray]:
    """Prototype of a class = similarity-weighted mean of its analog classes' reference-drug means,
    per option (analogs not measured at an option are skipped there; no analog -> generic)."""
    out = {}
    for c, lst in analogies.items():
        acc = np.zeros_like(generic)
        wsum = np.zeros(generic.shape[0])
        for name, sim in lst:
            if name == c or name not in class_means:
                continue
            m, _ = class_means[name]
            ok = ~np.isnan(m[:, 0])
            w = SIM_WEIGHT.get(sim, 1.0)
            acc[ok] += w * m[ok]
            wsum[ok] += w
        out[c] = np.where(wsum[:, None] > 0, acc / np.maximum(wsum, 1e-12)[:, None], generic)
    return out
