"""Prospective-style replay: mask the reserved pool before every fit; reveal only through an interface.

File summary
- Path: research/seed_attribution_20261017/replay.py
- Purpose: the information contract that a prospective-style replay of the program-revision loop
  needs, as code, plus a synthetic world to test it. Nothing frozen is edited.
- Why it exists (measured in `audit_access.py`): in the frozen `revise.Bench`, the support fold of a
  project is trained on every source line except the project's support lines, so it is trained on the
  project's own QUERY lines. The query lines are the distinguishing-experiment arena whose outcomes the
  loop is said to buy only after committing predictions. The reference median, the replicate variance,
  the probe design and the other projects' folds also use them. Distinguishing-experiment wells
  therefore do not measure how much of the query outcomes the loop used.
- Contract implemented here:
  - `mask_cells` removes the outcomes of the reserved lines from X1-X3 and re-derives everything that
    depends on them (training means, endpoint, reference median, threshold, replicate variance) with the
    reference restricted to the historical (non-reserved) lines.
  - `MaskedBench` trains every fold on historical lines only. Its truth is held privately and can only be
    read through `reveal`, which is the one costed acquisition call.
  - `synthetic_world` builds a small PRISM-shaped world (planted gated interaction, one-replicate and
    missing pairs) so the invariance can be tested by changing the reserved labels.
- Interfaces: `rederive`, `mask_cells`, `MaskedBench`, `synthetic_world`, `snapshot`, `reserved_lines`.
"""
from __future__ import annotations

import copy
import warnings

import numpy as np
import pandas as pd

import corrected as C
import contract
import revise


def rederive(dom, ref_lines=None):
    """Recompute every quantity derived from X1-X3 (training means, endpoint, replicate variance)."""

    stack = np.stack([dom.X1, dom.X2, dom.X3])
    n = np.isfinite(stack).sum(0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        dom.Ymean = np.where(n > 0, np.nansum(stack, 0) / np.maximum(n, 1), np.nan)
        ref = dom.src_line if ref_lines is None else np.asarray(ref_lines, bool)
        dom.endpoint = contract.endpoint(dom.X2, dom.X3, ref)
        dom.med, dom.thr = dom.endpoint.med, dom.endpoint.thr
        dom.hit, dom.known = dom.endpoint.hit, dom.endpoint.known
        dev = stack - np.nanmean(stack, 0, keepdims=True)
        rv = np.nansum(dev ** 2, 0) / np.maximum(n - 1, 1)
        rv = np.where(n >= 2, rv, np.nan)
        rep = np.nanmean(rv[:, ref], axis=1)
        dom.rep_var = np.where(np.isfinite(rep), rep, np.nanmedian(rep))
    dom._model_cache = {}
    dom._safe_model_cache = {}
    return dom


def reserved_lines(dom) -> np.ndarray:
    """Development query lines of every project: the pool whose outcomes are bought, not given."""

    role = dom.lines.role.to_numpy()
    return np.flatnonzero(dom.src_line & (role == "query"))


def mask_cells(dom, lines, keep_x1_rows=()):
    """A copy of ``dom`` in which the outcomes of ``lines`` are unknown to every fit.

    ``keep_x1_rows``: drug rows whose X1 readout on ``lines`` stays visible. Those are the paid probe
    wells of an information condition (I1/I2): a probe is a purchased measurement on a target line,
    so it is legal input and is charged as wells; every other cell of the reserved lines is masked.
    """

    out = copy.copy(dom)
    out.X1, out.X2, out.X3 = dom.X1.copy(), dom.X2.copy(), dom.X3.copy()
    cols = np.asarray(lines, int)
    keep = np.asarray(list(keep_x1_rows), int)
    saved = dom.X1[np.ix_(keep, cols)].copy() if len(keep) else None
    for X in (out.X1, out.X2, out.X3):
        X[:, cols] = np.nan
    if saved is not None:
        out.X1[np.ix_(keep, cols)] = saved
    ref = dom.src_line.copy()
    ref[cols] = False
    return rederive(out, ref)


class MaskedBench(revise.Bench):
    """`revise.Bench` whose folds are trained on historical lines only and whose truth is private."""

    def __init__(self, visible, truth, info, probe_cores, strong=None):
        self.dom, self.info, self.truth = visible, info, truth
        self.probes, self.strong = list(probe_cores), strong
        L = visible.lines
        src = np.flatnonzero(visible.src_line)
        proj, role = L.project.to_numpy(), L.role.to_numpy()
        self.projects = sorted(set(proj[src]))
        reserved = reserved_lines(visible)
        self.hist = np.setdiff1d(src, reserved)
        self.query, self.support = {}, {}
        for p in self.projects:
            q = np.flatnonzero((proj == p) & (role == "query") & visible.src_line)
            s = np.flatnonzero((proj == p) & (role == "support") & visible.src_line)
            self.query[p] = C.SafeContextFold(visible, self.hist, q, info, probe_cores, strong=strong)
            self.support[p] = C.SafeContextFold(visible, np.setdiff1d(self.hist, s), s, info, probe_cores, strong=strong)
        self.drows = self.query[self.projects[0]].drows
        self.structure = visible.drugs.structure_group.to_numpy()
        self.revealed = set()
        self.observed = np.isfinite(visible.Ymean[np.ix_(self.drows, src)])

    def with_design(self, probe_cores):
        raise NotImplementedError("MEASURE_EDIT_NEEDS_PURCHASE: a new probe's readouts on the reserved lines must be bought")

    def reveal(self, pairs):
        t = self.truth
        res = {}
        for d, c in pairs:
            known = bool(t.known[d, c])
            res[(d, c)] = (bool(t.hit[d, c]), known, float(t.endpoint.m[d, c]) if known else None)
        new = len(set(pairs) - self.revealed)
        self.revealed |= set(pairs)
        return res, new


def synthetic_world(seed: int = 0, label_seed: int = 0, n_drugs: int = 130, n_lines: int = 96):
    """A small PRISM-shaped world. ``label_seed`` redraws ONLY the outcomes of the development query lines.

    Returns (truth, reserved): an `engine.Domain`-compatible object with outcomes in the frozen layout
    and the indices of the reserved lines. Planted effect: MEK inhibitors are 1.2 log2
    units more sensitive on lines with BRAF mutation (panel column 0).
    """

    import engine

    rng = np.random.default_rng(seed)
    n_src_d = int(n_drugs * 0.8)
    n_src_l = int(n_lines * 0.8)
    moa_vocab = ["MEK inhibitor", "EGFR inhibitor", "PI3K inhibitor", "CDK inhibitor", "HDAC inhibitor"]
    moa = rng.integers(0, len(moa_vocab), n_drugs)
    drugs = pd.DataFrame({
        "core": [f"D{i:04d}" for i in range(n_drugs)], "name": [f"drug{i}" for i in range(n_drugs)],
        "moa": [moa_vocab[k] for k in moa], "target": ["" for _ in range(n_drugs)],
        "structure_group": [f"g{i // 2}" for i in range(n_drugs)],
        "drug_split": ["source"] * n_src_d + ["novel"] * (n_drugs - n_src_d)})
    tissues = ["lung", "breast", "skin", "colon", "ovary", "kidney"]
    tissue = rng.integers(0, len(tissues), n_lines)
    project = np.array([f"p{t % 3}" for t in tissue])
    role = np.where(rng.random(n_lines) < 0.5, "support", "query")
    line_split = np.array(["source"] * n_src_l + ["future_line"] * (n_lines - n_src_l))
    lines = pd.DataFrame({"row_name": [f"L{i}" for i in range(n_lines)], "depmap_id": [f"ACH-{i:05d}" for i in range(n_lines)],
                          "primary_tissue": [tissues[t] for t in tissue], "project": project, "role": role,
                          "line_split": line_split, "pool_id": [1] * n_lines})
    panel_genes = np.array(["BRAF", "KRAS", "NRAS", "EGFR", "PIK3CA", "TP53", "PTEN", "RB1"])
    panel = (rng.random((n_lines, len(panel_genes))) < 0.3).astype(float)
    lf = dict(lineage=np.eye(len(tissues))[tissue], lineage_names=np.array(tissues), panel=panel,
              panel_genes=panel_genes, expr=rng.normal(size=(n_lines, 12)), expr_genes=np.array([f"E{i}" for i in range(12)]),
              rna_pcs=rng.normal(size=(n_lines, 4)))
    moa_mat = np.eye(len(moa_vocab))[moa]
    df = dict(fp=(rng.random((n_drugs, 64)) < 0.2).astype(float), moa=moa_mat, moa_vocab=np.array(moa_vocab),
              target=np.zeros((n_drugs, 0)), target_vocab=np.array([]),
              moa_tokens=[[moa_vocab[k]] for k in moa], target_tokens=[[] for _ in range(n_drugs)])
    a = rng.normal(-0.3, 0.6, n_drugs)
    b = rng.normal(0, 0.3, n_lines) + 0.25 * lf["lineage"][:, 0]
    U, V = rng.normal(size=(n_drugs, 3)) * 0.35, rng.normal(size=(n_lines, 3)) * 0.5
    mean = a[:, None] + b[None, :] + U @ V.T
    mean = mean - 1.2 * np.outer(moa == 0, panel[:, 0])

    def draw(local_rng, shape, cols=slice(None)):
        return mean[:, cols] + local_rng.normal(0, 0.45, shape)

    X = [draw(rng, mean.shape) for _ in range(3)]
    for k, p in zip((0, 1, 2), (0.15, 0.18, 0.16)):
        X[k][rng.random(mean.shape) < p] = np.nan
    lab = np.random.default_rng(1_000_003 + label_seed)
    res = reserved_set = np.flatnonzero((line_split == "source") & (role == "query"))
    for k in range(3):
        fresh = draw(lab, (n_drugs, len(res)), res)
        fresh[lab.random(fresh.shape) < 0.17] = np.nan
        X[k][:, res] = fresh
    dom = C.CorrectedDomain.__new__(C.CorrectedDomain)
    dom.drugs, dom.lines, dom.open_future = drugs, lines, True
    dom.src_drug = (drugs.drug_split == "source").to_numpy()
    dom.src_line = (lines.line_split == "source").to_numpy()
    dom.X1, dom.X2, dom.X3 = X
    dom.lf, dom.df = lf, df
    from common import hash_unit
    dom.tie_drug = hash_unit(drugs.core, "tie-drug")
    dom.tie_line = hash_unit(lines.depmap_id, "tie-line")
    dom.drug_index = {c: i for i, c in enumerate(drugs.core)}
    for X_ in (dom.X1, dom.X2, dom.X3):
        X_[~dom.src_drug, :] = np.nan
    rederive(dom)
    return dom, reserved_set


def snapshot(bench, lib, project, rounds_of_edits: bool = True):
    """Everything a revision step computes BEFORE it buys an outcome, as plain comparable values."""

    out = {}
    for p in bench.projects:
        for tag, fold in (("query", bench.query[p]), ("support", bench.support[p])):
            out[f"{tag}|{p}|base_mean"] = fold.base_mean.copy()
            out[f"{tag}|{p}|R_train"] = fold.R_train.copy()
            out[f"{tag}|{p}|oos_var"] = fold.oos_var.copy()
    commit, digest = bench.commit(lib)
    for p in bench.projects:
        nom, mean, var = commit[p]
        out[f"commit|{p}|nom"], out[f"commit|{p}|mean"], out[f"commit|{p}|var"] = nom, mean, var
    out["digest"] = digest
    diag = revise.diagnose(bench, lib, project)
    out["diagnosis"] = repr(diag)
    prop = revise.EnumerativeProposer(n=6)
    edits, _ = prop.propose(diag, lib, bench)
    out["proposals"] = repr([e.label() for e in edits])
    if edits:
        new, refusal = bench.validate(lib, edits[0])
        if new is not None:
            nc, _ = bench.commit(new)
            pairs, info = bench.distinguish(commit, nc)
            out["distinguishing_pairs"] = repr(sorted(pairs))
    return out


def differences(a: dict, b: dict) -> list:
    """Keys whose values differ between two snapshots (exact comparison)."""

    bad = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
            same = x is not None and y is not None and x.shape == y.shape and np.array_equal(x, y, equal_nan=True)
        else:
            same = x == y
        if not same:
            bad.append(k)
    return bad
