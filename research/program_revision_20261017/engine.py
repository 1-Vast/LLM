"""Evaluation engine: data access policy, cross-fitted strong model, program application, decisions.

File summary
- Path: research/program_revision_20261017/engine.py
- Purpose: everything that turns (training lines, target lines, information condition, library)
  into committed predictions, nominations and scored outcomes, identically for every arm.
- Access policy (`Domain`):
  - ``open_future=False`` (Stage A, development, revision): every response of a NOVEL drug or a
    non-SOURCE line is replaced by NaN at load time. Only the frozen Stage B/C evaluators pass
    ``open_future=True``, and they refuse unless FREEZE.json exists and its digests match.
  - Training responses are the mean of the available replicates X1-X3. A probe readout is X1 of
    that pair. A confirmation outcome is X2 and X3 of that pair (`common.qualified_hits`). The
    reference median of the endpoint uses SOURCE lines only.
- Information conditions for a new line (`INFO`): which legal features enter the line-state
  prior, whether the fixed probe design is measured, and which program atoms are legal.
  I0 lineage; I1 lineage + DNA panel; I2 I1 + fixed probes; I3 I2 + RNA-seq.
- Cross-fitting (`ContextFold`): the strong model is fitted on the training lines; their
  out-of-sample residuals come from 5 inner folds in which each inner line is predicted as a new
  line from the same legal information. Programs are fitted only on those residuals.
- Decisions: per target line, nominate the k candidates with the largest hit probability;
  ties by a fixed hashed order. Utility = qualified hits among nominations with known outcome;
  unknown outcomes are counted separately and never treated as inactive.
- Strong-model ALS fits are cached per (domain, training lines, settings) (`fitted_model`); they
  do not depend on the information condition or probe design, so a design change only recomputes
  posteriors.
- Interfaces: `Domain`, `INFO`, `ContextFold`, `DrugFold`, `nominate`, `score_nominations`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import HERE, hash_unit, load_responses, qualified_hits
from features import drug_features, line_features
from vc import LineContext, ProgramLibrary, StrongModel, hit_probability, ridge_prior, top_k

INFO = {
    "I0": {"lineage": True, "panel": False, "probes": False, "rna": False},
    "I1": {"lineage": True, "panel": True, "probes": False, "rna": False},
    "I2": {"lineage": True, "panel": True, "probes": True, "rna": False},
    "I3": {"lineage": True, "panel": True, "probes": True, "rna": True},
}

K_NOMINATE = 10
STRONG = {"rank": 20, "lam": 2.0, "iters": 12}  # selected on development query lines (select_strong*.log)


class Domain:
    def __init__(self, open_future: bool = False):
        self.drugs = pd.read_csv(HERE / "drugs.csv")
        self.lines = pd.read_csv(HERE / "lines.csv", keep_default_na=False)
        self.open_future = open_future
        X1, X2, X3 = load_responses(self.drugs, self.lines)
        self.src_drug = (self.drugs.drug_split == "source").to_numpy()
        self.src_line = (self.lines.line_split == "source").to_numpy()
        if not open_future:
            for X in (X1, X2, X3):
                X[~self.src_drug, :] = np.nan
                X[:, ~self.src_line] = np.nan
        self.X1, self.X2, self.X3 = X1, X2, X3
        stack = np.stack([X1, X2, X3])
        n = np.isfinite(stack).sum(0)
        self.Ymean = np.where(n > 0, np.nansum(stack, 0) / np.maximum(n, 1), np.nan)
        self.hit, self.known = qualified_hits(X2, X3, line_mask=self.src_line)
        m23 = np.where(self.known, (X2 + X3) / 2, np.nan)
        with np.errstate(all="ignore"):
            self.med = np.nanmedian(m23[:, self.src_line], axis=1)
        self.thr = np.minimum(-1.0, self.med - 1.0)
        dev = stack - np.nanmean(stack, 0, keepdims=True)
        with np.errstate(all="ignore"):
            rv = np.nansum(dev ** 2, 0) / np.maximum(n - 1, 1)
            rv = np.where(n >= 2, rv, np.nan)
            self.rep_var = np.nanmean(rv[:, self.src_line], axis=1)
        self.rep_var = np.where(np.isfinite(self.rep_var), self.rep_var, np.nanmedian(self.rep_var))
        self.lf = line_features(self.lines)
        self.df = drug_features(self.drugs)
        self.tie_drug = hash_unit(self.drugs.core, "tie-drug")
        self.tie_line = hash_unit(self.lines.depmap_id, "tie-line")
        self.drug_index = {c: i for i, c in enumerate(self.drugs.core)}

    def line_Z(self, rows, info: str, lineage_cols=None):
        """Line-state prior features for the given rows under an information condition."""

        spec = INFO[info]
        parts = []
        if spec["lineage"]:
            L = self.lf["lineage"][rows]
            if lineage_cols is not None:
                L = L[:, lineage_cols]
            parts.append(L)
        if spec["panel"]:
            parts.append(self.lf["panel"][rows])
        if spec["rna"]:
            parts.append(self.lf["rna_pcs"][rows])
        return np.column_stack(parts) if parts else np.zeros((len(rows), 0))

    def drug_F(self, rows):
        fp = self.df["fp"][rows]
        fp = fp / np.maximum(np.sqrt(fp.sum(1, keepdims=True)), 1.0)
        return np.column_stack([fp, self.df["moa"][rows], self.df["target"][rows]])


def legal_atoms(info: str) -> set:
    spec = INFO[info]
    out = {"lin", "b"}
    if spec["panel"]:
        out.add("mut")
    if spec["probes"]:
        out.add("probe")
    if spec["rna"]:
        out.add("expr")
    return out


def fitted_model(dom: Domain, train_rows, Ytr, strong) -> StrongModel:
    """ALS fit of the strong model, cached per (domain, training lines, settings).

    The fit does not depend on the information condition or the probe design, so a design change
    only recomputes posteriors. A shallow copy is returned so priors set on it are not shared.
    """

    import copy
    cache = dom.__dict__.setdefault("_model_cache", {})
    key = (np.asarray(train_rows).tobytes(), tuple(sorted(strong.items())), Ytr.shape)
    if key not in cache:
        cache[key] = StrongModel(**strong).fit(Ytr)
    return copy.copy(cache[key])


class ContextFold:
    """Training lines -> target lines (new contexts), for source drugs or novel drugs."""

    def __init__(self, dom: Domain, train_rows, target_rows, info: str, probe_cores,
                 inner_folds: int = 5, strong=None):
        self.dom, self.info = dom, info
        self.train = np.asarray(train_rows)
        self.target = np.asarray(target_rows)
        self.drows = np.flatnonzero(dom.src_drug)
        self.probe_cores = list(probe_cores) if INFO[info]["probes"] else []
        self.probe_idx = np.array([dom.drug_index[c] for c in self.probe_cores], int)
        # probe positions on the source-drug axis
        pos = {d: i for i, d in enumerate(self.drows)}
        self.probe_pos = np.array([pos[d] for d in self.probe_idx], int)
        self.strong = strong or STRONG
        lin_cols = np.flatnonzero(dom.lf["lineage"][self.train].sum(0) > 0)
        self.lin_cols = lin_cols
        Y = dom.Ymean[np.ix_(self.drows, self.train)]
        # inner cross-fitting for out-of-sample residuals on training lines
        h = hash_unit(dom.lines.depmap_id.to_numpy()[self.train], "inner-fold")
        fold = np.minimum((h * inner_folds).astype(int), inner_folds - 1)
        R = np.full(Y.shape, np.nan)
        Pm = np.full(Y.shape, np.nan)
        b_oos = np.zeros(len(self.train))
        for f in range(inner_folds):
            tr, te = np.flatnonzero(fold != f), np.flatnonzero(fold == f)
            mean, S, _ = self._predict(Y[:, tr], self.train[tr], self.train[te])
            Pm[:, te] = mean
            b_oos[te] = S[:, 0]
        R = Y - Pm
        self.Y, self.R_train, self.P_train, self.b_train = Y, R, Pm, b_oos
        mean, S, C = self._predict(Y, self.train, self.target)
        self.model = self._last_model
        self.base_mean, self.S_target, self.C_target = mean, S, C
        self.b_target = S[:, 0]
        self.oos_var = np.nanmean(R ** 2, axis=1)
        self.probe_train = self._probe_values(self.train)
        self.probe_target = self._probe_values(self.target)

    def _probe_values(self, rows):
        out = {}
        for core, d in zip(self.probe_cores, self.probe_idx):
            v = self.dom.X1[d, rows]
            out[core] = np.where(np.isfinite(v), v, np.nan)
        return out

    def _predict(self, Ytr, train_rows, new_rows):
        dom = self.dom
        m = fitted_model(dom, train_rows, Ytr, self.strong)
        m.line_prior(dom.line_Z(train_rows, self.info, self.lin_cols))
        Znew = dom.line_Z(new_rows, self.info, self.lin_cols)
        probes = None
        noise = None
        if self.probe_cores:
            noise = m.resid_var + 0.67 * dom.rep_var[self.drows]
            probes = []
            for c in new_rows:
                obs = {}
                for p, d in zip(self.probe_pos, self.probe_idx):
                    v = dom.X1[d, c]
                    if np.isfinite(v):
                        obs[int(p)] = float(v)
                probes.append(obs)
        mean, S, C = m.predict_lines(Znew, probes, noise)
        self._last_model = m
        return mean, S, C

    def contexts(self):
        """LineContext for training lines (OOS b) and targets; missing probes become 0 (= mean)."""

        def fill(vals, ref):
            out = {}
            for k, v in vals.items():
                mu = np.nanmean(ref[k])
                out[k] = np.where(np.isfinite(v), v, mu)
            return out
        tr = LineContext(self.dom.lf, self.train, fill(self.probe_train, self.probe_train), self.b_train)
        te = LineContext(self.dom.lf, self.target, fill(self.probe_target, self.probe_train), self.b_target)
        return tr, te

    def apply(self, lib: ProgramLibrary | None):
        """Committed predictions for source drugs on target lines: (mean, var, score)."""

        dom = self.dom
        mean = self.base_mean.copy()
        var = self.oos_var.copy()
        if lib is not None and lib.programs:
            ctx_tr, ctx_te = self.contexts()
            lib.fit(self.R_train, lib.states(ctx_tr), dom.df, self.drows)
            mean = mean + lib.correction(lib.states(ctx_te), dom.df, self.drows, novel=False)
            var = np.where(np.isfinite(lib.resid_var), lib.resid_var, var)
        var = var + dom.rep_var[self.drows] / 6.0
        mean, var = self._own_probe(mean, var)
        thr = dom.thr[self.drows]
        score = hit_probability(mean, var, thr[:, None])
        return mean, var, score

    def _own_probe(self, mean, var):
        """A probed drug's own X1 readout on the target sharpens its prediction (Gaussian fusion)."""

        if not self.probe_cores:
            return mean, np.repeat(var[:, None], mean.shape[1], 1)
        V = np.repeat(var[:, None], mean.shape[1], 1)
        for core, p, d in zip(self.probe_cores, self.probe_pos, self.probe_idx):
            x = self.probe_target[core]
            ok = np.isfinite(x)
            vr = 0.67 * self.dom.rep_var[d]
            post_v = 1.0 / (1.0 / V[p, ok] + 1.0 / vr)
            mean[p, ok] = post_v * (mean[p, ok] / V[p, ok] + x[ok] / vr)
            V[p, ok] = post_v
        return mean, V


class DrugFold:
    """Novel drugs (never measured in training) on known lines or on the fold's new lines.

    Uses the strong model of a `ContextFold` (fitted on source drugs x its training lines). The
    drug state [a_d, U_d] of a novel drug has a ridge prior from fingerprint, MoA and target
    tokens fitted on source drugs. Few-observation: ``pool_probes`` (one dict per novel drug,
    {training-line position: X1 readout}) are one pooled well on source lines; they update the
    drug state by Bayesian linear regression. ``on``: "train" predicts the fold's training lines
    (fitted line states), "target" its target lines (posterior line states).
    """

    def __init__(self, fold: ContextFold, novel_rows, on: str = "target", pool_probes=None, line_subset=None):
        dom = fold.dom
        self.fold, self.dom, self.on = fold, dom, on
        self.rows = np.asarray(novel_rows)
        m = fold.model
        m.drug_prior(dom.drug_F(fold.drows))
        noise = float(np.nanmean(m.resid_var) + 0.67 * np.nanmean(dom.rep_var[fold.drows]))
        # drug-state posterior from the pooled readouts on training lines
        ref, tm, tc = m.predict_drugs(dom.drug_F(self.rows), m.line_state, pool_probes, noise)
        if on == "target":
            S, lines, Cl = fold.S_target, fold.target, fold.C_target
        else:
            S, lines, Cl = m.line_state, fold.train, None
        sel = np.arange(len(lines)) if line_subset is None else np.asarray(line_subset)
        self.sel = sel
        S = S[sel]
        self.lines = lines[sel]
        G = np.column_stack([np.ones(len(S)), S[:, 1:]])
        self.base_mean = tm @ G.T + S[:, 0][None, :]
        dv = np.einsum("li,dij,lj->dl", G, tc, G)
        if Cl is not None:
            T = np.column_stack([np.ones(len(tm)), tm[:, 1:]])
            lv = np.einsum("di,lij,dj->dl", T, Cl[sel], T)
        else:
            lv = 0.0
        self.base_var = dv + lv + float(np.nanmean(fold.oos_var))
        # generic potency + overall line sensitivity control: the additive part a_d + b_c alone
        self.additive = tm[:, 0][:, None] + S[:, 0][None, :]
        # predicted reference median over source training lines (the endpoint median is unknown)
        self.thr = np.minimum(-1.0, np.median(ref, axis=1) - 1.0)

    def apply(self, lib: ProgramLibrary | None):
        dom, fold = self.dom, self.fold
        mean = self.base_mean.copy()
        if lib is not None and lib.programs:
            ctx_tr, ctx_te = fold.contexts()
            lib.fit(fold.R_train, lib.states(ctx_tr), dom.df, fold.drows)
            ctx = ctx_te if self.on == "target" else ctx_tr
            mean = mean + lib.correction(lib.states(ctx)[self.sel], dom.df, self.rows, novel=True)
        var = self.base_var + dom.rep_var[fold.drows].mean() / 6.0
        score = hit_probability(mean, var, self.thr[:, None])
        return mean, var, score


def ridge_baseline(dom: Domain, train, target, info: str, probe_cores, alphas=(1.0, 10.0, 100.0, 1000.0)):
    """Drug-specific ridge on the legal line features plus probe readouts (S_ridge comparator).

    Returns (mean (drugs, targets), loo_var (drugs,)). Missing probe readouts are mean-filled.
    """

    drows = np.flatnonzero(dom.src_drug)
    lin_cols = np.flatnonzero(dom.lf["lineage"][train].sum(0) > 0)

    def Z(rows):
        parts = [dom.line_Z(rows, info, lin_cols)]
        if INFO[info]["probes"]:
            P = np.column_stack([dom.X1[dom.drug_index[c], rows] for c in probe_cores])
            ref = np.column_stack([dom.X1[dom.drug_index[c], train] for c in probe_cores])
            mu = np.nanmean(ref, 0)
            parts.append(np.where(np.isfinite(P), P, mu))
        return np.column_stack(parts)

    Ztr, Zte = Z(train), Z(target)
    mu, sd = Ztr.mean(0), Ztr.std(0) + 1e-9
    Ztr, Zte = (Ztr - mu) / sd, (Zte - mu) / sd
    Y = dom.Ymean[np.ix_(drows, train)]
    mean = np.zeros((len(drows), len(target)))
    var = np.zeros(len(drows))
    for i in range(len(drows)):
        o = np.isfinite(Y[i])
        if o.sum() < 5:
            mean[i] = np.nanmean(Y[i]) if o.any() else 0.0
            var[i] = np.nanvar(Y[i]) if o.sum() > 1 else 1.0
            continue
        y = Y[i, o]
        ym = y.mean()
        U, s, Vt = np.linalg.svd(Ztr[o], full_matrices=False)
        Uy = U.T @ (y - ym)
        best = None
        for a in alphas:
            f = s ** 2 / (s ** 2 + a)
            h = (U ** 2 * f).sum(1) + 1.0 / o.sum()
            res = (y - ym) - U @ (f * Uy)
            loo = res / np.maximum(1 - h, 1e-6)
            e = (loo ** 2).mean()
            if best is None or e < best[0]:
                best = (e, a)
        a = best[1]
        w = Vt.T @ ((s / (s ** 2 + a)) * Uy)
        mean[i] = ym + Zte @ w
        var[i] = best[0]
    return mean, var


def fixed_probe_design(dom: Domain, k: int = 8, info: str = "I1", train_rows=None) -> list:
    """Greedy A-optimal probes: minimise mean predictive variance of all source drugs on a new line.

    Uses only source drugs x training lines (default: all source lines). Deterministic.
    """

    drows = np.flatnonzero(dom.src_drug)
    train = np.flatnonzero(dom.src_line) if train_rows is None else np.asarray(train_rows)
    m = StrongModel(**STRONG).fit(dom.Ymean[np.ix_(drows, train)])
    lin_cols = np.flatnonzero(dom.lf["lineage"][train].sum(0) > 0)
    m.line_prior(dom.line_Z(train, info, lin_cols))
    C = m._lp[3].copy()
    H = np.column_stack([np.ones(len(drows)), m.U])
    noise = m.resid_var + 0.67 * dom.rep_var[drows]
    chosen = []
    for _ in range(k):
        HC = H @ C
        q = np.einsum("ij,ij->i", HC, H)
        red = np.array([(HC @ H[j]) @ (HC @ H[j]) for j in range(len(drows))]) / (q + noise)
        red[chosen] = -np.inf
        j = int(np.argmax(red))
        chosen.append(j)
        h = H[j]
        Ch = C @ h
        C = C - np.outer(Ch, Ch) / (h @ Ch + noise[j])
    return [dom.drugs.core[drows[j]] for j in chosen]


def nominate(score: np.ndarray, tie: np.ndarray, k: int = K_NOMINATE) -> np.ndarray:
    return top_k(score, k, tie)


def score_nominations(dom: Domain, nom: np.ndarray, drug_rows: np.ndarray, line_rows: np.ndarray):
    """Per target line: (known hits, unknown outcomes, nominations)."""

    hits = np.zeros(nom.shape[1])
    unknown = np.zeros(nom.shape[1])
    for j, c in enumerate(line_rows):
        d = drug_rows[nom[:, j]]
        hits[j] = dom.hit[d, c].sum()
        unknown[j] = (~dom.known[d, c]).sum()
    return hits, unknown


def nomination_sets(nom: np.ndarray, drug_rows: np.ndarray, line_rows: np.ndarray) -> set:
    return {(int(drug_rows[i]), int(c)) for j, c in enumerate(line_rows) for i in nom[:, j]}
