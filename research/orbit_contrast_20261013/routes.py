"""Routes and relabelling orbits for Task A' (cold-start compounds) and Task B (unseen-gene knockdowns).

File summary
- Path: research/orbit_contrast_20261013/routes.py
- Purpose: compute, for one setting (query cells, reference entities, knowledge variant), every route's
  real prediction f, its orbit mean g-bar over M stratum-preserving relabellings, the orbit spread,
  label-free descriptors, and (when the truth is supplied) cos(f, y) and the mean orbit cos(f_m, y).
- Settings never let a query entity be its own reference; centring and the generic direction come
  from the setting's reference entities only (PROTOCOL.md section 3).
- Interfaces: `RouteOut`, `TaskA`, `TaskB`, `unit`, `cos_rows`, `stratum_donors`.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

M_ORBIT = 16


def unit(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return np.where(n > 1e-12, x / np.maximum(n, 1e-12), 0.0)


def cos_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    num = (a * b).sum(-1)
    den = np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1)
    return np.where(den > 1e-12, num / np.maximum(den, 1e-12), 0.0)


def rng_for(*parts) -> np.random.Generator:
    h = hashlib.sha256(("orbit-contrast-rng:" + "|".join(map(str, parts))).encode()).hexdigest()
    return np.random.default_rng(int(h[:16], 16))


def stratum_groups(keys: np.ndarray, members: np.ndarray, min_size: int = 5, fallbacks=()) -> list[np.ndarray]:
    """Partition `members` into strata of at least `min_size` where possible.

    `keys` is (n, k) integer strata. Members whose full-key stratum is too small are regrouped,
    among the still-unassigned members only, by each column subset in `fallbacks` (finest first), and
    finally all together.
    """
    levels = [tuple(range(keys.shape[1]))] + [tuple(c) for c in fallbacks] + [()]
    left = np.asarray(members)
    groups = []
    for li, cols in enumerate(levels):
        if not len(left):
            break
        by: dict = {}
        for i in left:
            by.setdefault(tuple(keys[i, list(cols)]) if cols else (), []).append(i)
        keep = []
        for v in by.values():
            if len(v) >= min_size or li == len(levels) - 1:
                groups.append(np.array(v))
            else:
                keep.extend(v)
        left = np.array(keep, int)
    return groups


def stratum_donors(keys: np.ndarray, members: np.ndarray, min_size: int = 5, fallbacks=()) -> dict:
    """Map each member to the other members of its stratum (see `stratum_groups`); never to itself."""
    out = {}
    for g in stratum_groups(keys, members, min_size, fallbacks):
        for i in g:
            out[int(i)] = g[g != i]
    return out


def permutation_from(donors: dict, n: int, rng: np.random.Generator) -> np.ndarray:
    """A global relabelling: permute uniformly within each stratum (a stratum = a member plus its donors)."""
    perm = np.arange(n)
    done = set()
    for i in sorted(donors):
        if i in done:
            continue
        pool = np.sort(np.append(donors[i], i))
        done.update(pool.tolist())
        perm[pool] = pool[rng.permutation(len(pool))]
    return perm


@dataclass
class RouteOut:
    f: np.ndarray                  # nq x p real prediction (0 where unavailable)
    avail: np.ndarray              # nq bool
    gbar: np.ndarray               # nq x p orbit mean (0 where unavailable or no orbit)
    spread: np.ndarray             # nq orbit spread sqrt(mean ||f_m - gbar||^2)
    desc: np.ndarray               # nq x d route-specific label-free descriptors
    desc_names: tuple
    cos_f: np.ndarray | None = None        # cos(f, y)
    cos_orbit: np.ndarray | None = None    # mean_m cos(f_m, y)
    has_orbit: bool = True


class OrbitAccumulator:
    def __init__(self, nq: int, p: int, y: np.ndarray | None):
        self.s = np.zeros((nq, p))
        self.ss = np.zeros(nq)
        self.c = np.zeros(nq)
        self.n = 0
        self.y = y

    def add(self, fm: np.ndarray) -> None:
        self.s += fm
        self.ss += (fm * fm).sum(1)
        if self.y is not None:
            self.c += cos_rows(fm, self.y)
        self.n += 1

    def result(self):
        g = self.s / self.n
        spread = np.sqrt(np.maximum(self.ss / self.n - (g * g).sum(1), 0.0))
        return g, spread, (self.c / self.n if self.y is not None else None)


def knn_mean(sim: np.ndarray, R: np.ndarray, k: int, power: float, floor: float):
    """Similarity-weighted mean of the top-k reference rows; (pred, avail, top, mean_k, n_used)."""
    nq, nr = sim.shape
    if nr == 0:
        return np.zeros((nq, R.shape[1])), np.zeros(nq, bool), np.zeros(nq), np.zeros(nq), np.zeros(nq)
    kk = min(k, nr)
    idx = np.argpartition(-sim, kk - 1, axis=1)[:, :kk]
    s = np.take_along_axis(sim, idx, 1)
    w = np.where(s >= max(floor, 1e-12), np.power(np.maximum(s, 0.0), power), 0.0)
    tot = w.sum(1)
    pred = np.einsum("qk,qkp->qp", w, R[idx]) / np.maximum(tot, 1e-12)[:, None]
    avail = tot > 0
    pred[~avail] = 0.0
    used = (w > 0).sum(1)
    return pred, avail, s.max(1), np.where(used > 0, (s * (w > 0)).sum(1) / np.maximum(used, 1), 0.0), used


def jaccard(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    a = A.astype(np.float32)
    b = B.astype(np.float32)
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


def tanimoto(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return jaccard(A, B)


# --------------------------------------------------------------------------------------------- Task A'

@dataclass
class KnowledgeA:
    """Compound knowledge variant: token matrix rows, signed targets, and per-line KD-row maps."""

    tok: np.ndarray                    # n_cp x V bool
    signed: list                       # per compound: list of (kd_row, sign) for targets with a KD row
    n_signed: np.ndarray               # all signed targets, KD-covered or not
    gene_map: np.ndarray               # n_line x n_kd: KD row used for a target's KD row in line T
    kd_line: np.ndarray                # n_line: line whose KD is read for line T (context permutation)


class TaskA:
    ROUTES = ("chem", "know", "genetic")
    ORBIT_ROUTES = ("know", "genetic")

    def __init__(self, z: dict, ck, fps: np.ndarray, kd_degree: np.ndarray):
        self.z = z
        self.Y = z["cp"].astype(np.float32)                      # n_cp x L x p (NaN missing)
        self.has = np.isfinite(self.Y[..., 0])
        self.L, self.p = self.Y.shape[1], self.Y.shape[2]
        self.fps = fps
        kd = z["kd"].astype(np.float64)
        self.kd_has = np.isfinite(kd[..., 0])
        mu = np.array([np.nanmean(kd[:, T][self.kd_has[:, T]], 0) for T in range(self.L)])
        self.KDc = np.where(self.kd_has[..., None], kd - mu[None], 0.0).astype(np.float32)
        self.kd_index = {g: i for i, g in enumerate(z["kd_gene"])}
        self.lm = set(map(str, z["gene_symbol"]))
        self.ck = ck
        self.kd_degree = kd_degree
        # gene strata per line: landmark x degree bin {0,1,2-4,>=5} x KD-norm tercile in T
        lm = np.array([g in self.lm for g in z["kd_gene"]], int)
        dbin = np.digitize(kd_degree, [1, 2, 5])
        self.gene_donors = []
        for T in range(self.L):
            members = np.flatnonzero(self.kd_has[:, T])
            nrm = np.linalg.norm(self.KDc[:, T], axis=1)
            terc = np.zeros(len(nrm), int)
            q = np.quantile(nrm[members], [1 / 3, 2 / 3])
            terc[members] = np.digitize(nrm[members], q)
            keys = np.stack([lm, dbin, terc], 1)
            self.gene_donors.append(stratum_donors(keys, members, fallbacks=[(0, 1), (0,)]))
        # compound strata: token-count bin x has-Hub-target, among annotated compounds
        ntok = np.array([len(t) for t in ck.tokens])
        self.annotated = ntok > 0
        ckeys = np.stack([np.digitize(ntok, [2, 4, 8]), ck.has_hub_target.astype(int)], 1)
        self.cp_donors = stratum_donors(ckeys, np.flatnonzero(self.annotated), fallbacks=[(0,)])
        vocab: dict = {}
        for t in ck.tokens:
            for x in t:
                vocab.setdefault(x, len(vocab))
        self.vocab = vocab

    def knowledge(self, ck, gene_map=None, kd_line=None, cp_perm=None) -> KnowledgeA:
        n = len(ck.tokens)
        src = np.arange(n) if cp_perm is None else cp_perm
        tok = np.zeros((n, len(self.vocab)), bool)
        signed, nsig = [], np.zeros(n, int)
        for i in range(n):
            for x in ck.tokens[src[i]]:
                if x in self.vocab:
                    tok[i, self.vocab[x]] = True
        for i in range(n):
            s = ck.signed[i]
            nsig[i] = len(s)
            signed.append([(self.kd_index[g], v) for g, v in s.items() if g in self.kd_index])
        gm = np.tile(np.arange(len(self.kd_index)), (self.L, 1)) if gene_map is None else gene_map
        kl = np.arange(self.L) if kd_line is None else kd_line
        return KnowledgeA(tok, signed, nsig, gm, kl)

    def global_gene_perm(self, seed) -> np.ndarray:
        """Per-line stratum-preserving permutation of KD rows (a global relabelling of gene identity)."""
        n = len(self.kd_index)
        return np.stack([permutation_from(self.gene_donors[T], n, rng_for("gperm", seed, T)) for T in range(self.L)])

    def global_compound_perm(self, seed) -> np.ndarray:
        return permutation_from(self.cp_donors, len(self.ck.tokens), rng_for("cperm", seed))

    def genetic_vec(self, K: KnowledgeA, d: int, T: int, rows=None):
        tl = K.kd_line[T]
        tg = K.signed[d] if rows is None else rows
        vecs = []
        for r, s in tg:
            r2 = K.gene_map[T, r]
            if self.kd_has[r2, tl]:
                vecs.append(s * self.KDc[r2, tl])
        if not vecs:
            return None, 0, 0.0
        V = np.stack(vecs)
        if len(vecs) > 1:
            U = unit(V)
            g = U @ U.T
            coh = (g.sum() - len(vecs)) / (len(vecs) * (len(vecs) - 1))
        else:
            coh = 1.0
        return V.mean(0), len(vecs), coh

    def setting(self, K: KnowledgeA, q_cp: np.ndarray, q_line: np.ndarray, ref_mask: np.ndarray, active_ref: np.ndarray,
                salt: str, with_truth: bool = True):
        """Route outputs for query cells (q_cp[i], q_line[i]); references are compounds with ref_mask True."""
        nq, p = len(q_cp), self.p
        out_y = np.zeros((nq, p))
        gen = np.zeros((nq, p))
        outs = {r: dict(f=np.zeros((nq, p)), avail=np.zeros(nq, bool), gbar=np.zeros((nq, p)), spread=np.zeros(nq),
                        desc=None, cf=np.zeros(nq), co=np.zeros(nq)) for r in self.ROUTES}
        descs = {"chem": np.zeros((nq, 3)), "know": np.zeros((nq, 3)), "genetic": np.zeros((nq, 3))}
        for T in range(self.L):
            qi = np.flatnonzero(q_line == T)
            if not len(qi):
                continue
            refs = np.flatnonzero(ref_mask & self.has[:, T])
            mu = self.Y[refs, T].astype(np.float64).mean(0)
            Rc = self.Y[refs, T].astype(np.float64) - mu
            act = active_ref[refs, T]
            gT = unit(unit(Rc[act]).mean(0)) if act.any() else unit(unit(Rc).mean(0))
            gen[qi] = gT
            d = q_cp[qi]
            y = self.Y[d, T].astype(np.float64) - mu
            out_y[qi] = y
            yy = y if with_truth else None
            # chem (base route, no orbit)
            sim = tanimoto(self.fps[d], self.fps[refs])
            sim[np.equal.outer(d, refs)] = -1.0
            pred, av, top, meank, used = knn_mean(sim, Rc, 10, 2.0, 0.3)
            o = outs["chem"]; o["f"][qi] = pred; o["avail"][qi] = av
            descs["chem"][qi] = np.stack([top, meank, np.log1p(used)], 1)
            if yy is not None:
                o["cf"][qi] = np.where(av, cos_rows(pred, y), 0.0)
            # know: Jaccard kNN over tokens; orbit replaces the query's tokens by a stratum donor's
            kr = refs[K.tok[refs].any(1)]
            Rk = self.Y[kr, T].astype(np.float64) - mu
            sim = jaccard(K.tok[d], K.tok[kr])
            sim[np.equal.outer(d, kr)] = -1.0
            pred, av, top, meank, used = knn_mean(sim, Rk, 10, 1.0, 0.0)
            o = outs["know"]; o["f"][qi] = pred; o["avail"][qi] = av
            descs["know"][qi] = np.stack([top, meank, np.log1p(used)], 1)
            acc = OrbitAccumulator(len(qi), p, yy)
            rng = rng_for("know", salt, T)
            for m in range(M_ORBIT):
                donors = np.array([rng.choice(self.cp_donors[x]) if x in self.cp_donors and len(self.cp_donors[x]) else x for x in d])
                sm = jaccard(K.tok[donors], K.tok[kr])
                sm[np.equal.outer(d, kr)] = -1.0
                pm, _, _, _, _ = knn_mean(sm, Rk, 10, 1.0, 0.0)
                acc.add(pm)
            g, s, c = acc.result()
            o["gbar"][qi] = np.where(av[:, None], g, 0.0); o["spread"][qi] = s
            if yy is not None:
                o["cf"][qi] = np.where(av, cos_rows(pred, y), 0.0); o["co"][qi] = np.where(av, c, 0.0)
            # genetic: signed KD of the compound's targets in T; orbit relabels each target within its gene stratum
            o = outs["genetic"]
            rng = rng_for("genetic", salt, T)
            fm_all = np.zeros((M_ORBIT, len(qi), p))
            tl = K.kd_line[T]
            for a, x in enumerate(d):
                v, n, coh = self.genetic_vec(K, x, T)
                if v is None:
                    continue
                o["f"][qi[a]] = v; o["avail"][qi[a]] = True
                descs["genetic"][qi[a]] = [np.log1p(n), np.log1p(K.n_signed[x]), coh]
                rows = [(K.gene_map[T, r], s) for r, s in K.signed[x] if self.kd_has[K.gene_map[T, r], tl]]
                donor_tl = self.gene_donors[tl]
                for m in range(M_ORBIT):
                    vec = np.zeros(p)
                    for r, s in rows:
                        pool = donor_tl.get(r)
                        rr = rng.choice(pool) if pool is not None and len(pool) else r
                        vec += s * self.KDc[rr, tl]
                    fm_all[m, a] = vec / len(rows)
            acc = OrbitAccumulator(len(qi), p, yy)
            for m in range(M_ORBIT):
                acc.add(fm_all[m])
            g, s, c = acc.result()
            av = o["avail"][qi]
            o["gbar"][qi] = np.where(av[:, None], g, 0.0); o["spread"][qi] = np.where(av, s, 0.0)
            if yy is not None:
                o["cf"][qi] = np.where(av, cos_rows(o["f"][qi], y), 0.0); o["co"][qi] = np.where(av, c, 0.0)
        res = {}
        names = {"chem": ("top_sim", "mean_k_sim", "log_used"), "know": ("top_sim", "mean_k_sim", "log_used"),
                 "genetic": ("log_kd_targets", "log_targets", "kd_coherence")}
        for r in self.ROUTES:
            o = outs[r]
            res[r] = RouteOut(o["f"], o["avail"], o["gbar"], o["spread"], descs[r], names[r],
                              o["cf"] if with_truth else None, o["co"] if with_truth else None, r in self.ORBIT_ROUTES)
        return res, gen, out_y


# --------------------------------------------------------------------------------------------- Task B

@dataclass
class KnowledgeB:
    self_idx: np.ndarray        # n_gene: landmark readout index used by the self route (-1 if none)
    pharm_src: np.ndarray       # n_gene: gene whose pharmacology vector is used (-1 none)
    pharm_line: np.ndarray      # n_line: line whose pharmacology is read for line T
    cmp_sets: np.ndarray        # n_gene x n_ann bool compound sets used by the cotarget route
    esm_src: np.ndarray         # n_gene: gene whose ESM vector is used (-1 none)
    pharm: np.ndarray           # n_gene x L x p pharmacology vectors (0 where none)
    pharm_has: np.ndarray       # n_gene x L
    pharm_n: np.ndarray         # n_gene x L number of compounds behind each pharmacology vector


class TaskB:
    ROUTES = ("self", "pharm", "cotarget", "esm")

    def __init__(self, z: dict, ck, esm: np.ndarray, esm_has: np.ndarray):
        self.z = z
        self.genes = [str(g) for g in z["kd_gene"]]
        self.Y = z["kd"].astype(np.float32)
        self.has = np.isfinite(self.Y[..., 0])
        self.L, self.p = self.Y.shape[1], self.Y.shape[2]
        sym = [str(s) for s in z["gene_symbol"]]
        lm_pos = {s: i for i, s in enumerate(sym)}
        self.lm_idx = np.array([lm_pos.get(g, -1) for g in self.genes])
        self.is_lm = self.lm_idx >= 0
        self.esm, self.esm_has = esm, esm_has
        gpos = {g: i for i, g in enumerate(self.genes)}
        ann = np.flatnonzero([len(s) > 0 for s in ck.signed])
        self.ann = ann
        self.cp_signed = ck.signed
        S = np.zeros((len(self.genes), len(ann)), bool)
        sign = np.zeros((len(self.genes), len(ann)), np.int8)
        for a, d in enumerate(ann):
            for g, v in ck.signed[d].items():
                if g in gpos:
                    S[gpos[g], a] = True
                    sign[gpos[g], a] = v
        self.S, self.sign = S, sign
        self.degree = S.sum(1)
        cp = z["cp"].astype(np.float64)
        cp_has = np.isfinite(cp[..., 0])
        self.cp, self.cp_has = cp, cp_has
        nsig = np.array([len(ck.signed[d]) for d in ann])
        self.cp_w = 1.0 / np.maximum(nsig, 1)
        mu = np.array([cp[cp_has[:, T], T].mean(0) for T in range(self.L)])
        self.cpc = np.where(cp_has[..., None], cp - mu[None], 0.0)
        self.pharm, self.pharm_has, self.pharm_n = self._pharm(np.ones(len(ann), bool))
        lm = self.is_lm.astype(int)
        dbin = np.digitize(self.degree, [2, 5])
        # strata
        self.self_donors = {i: np.flatnonzero(self.is_lm)[np.flatnonzero(self.is_lm) != i] for i in np.flatnonzero(self.is_lm)}
        self.pharm_donors = []
        for T in range(self.L):
            members = np.flatnonzero(self.pharm_has[:, T])
            self.pharm_donors.append(stratum_donors(np.stack([dbin, lm], 1), members, fallbacks=[(0,)]))
        self.cot_donors = stratum_donors(np.stack([dbin, lm], 1), np.flatnonzero(self.degree > 0), fallbacks=[(0,)])
        self.esm_donors = stratum_donors(lm[:, None], np.flatnonzero(self.esm_has))

    def _pharm(self, keep: np.ndarray):
        """n_gene x L x p mean of sign x centred compound signature, weighted 1/n_signed; `keep` masks (gene, compound) pairs."""
        G, L, p = len(self.genes), self.L, self.p
        P = np.zeros((G, L, p))
        has = np.zeros((G, L), bool)
        cnt = np.zeros((G, L))
        Sk = self.S & keep if keep.ndim == 2 else self.S & keep[None]
        for T in range(L):
            m = self.cp_has[self.ann, T]
            W = (Sk[:, m] * self.sign[:, m]) * self.cp_w[m][None]
            tot = (Sk[:, m] * self.cp_w[m][None]).sum(1)
            P[:, T] = (W @ self.cpc[self.ann[m], T]) / np.maximum(tot, 1e-12)[:, None]
            has[:, T] = Sk[:, m].any(1)
            cnt[:, T] = Sk[:, m].sum(1)
        P[~has] = 0.0
        return P, has, cnt

    def knowledge(self, self_perm=None, pharm_perm=None, cot_perm=None, esm_perm=None, pharm_line=None,
                  withdraw=None) -> KnowledgeB:
        G = len(self.genes)
        ident = np.arange(G)
        sp = ident if self_perm is None else self_perm
        P, Ph, Pn = (self.pharm, self.pharm_has, self.pharm_n) if withdraw is None else self._pharm(withdraw)
        if pharm_perm is not None:
            P2, H2, N2 = np.zeros_like(P), np.zeros_like(Ph), np.zeros_like(Pn)
            for T in range(self.L):
                P2[:, T] = P[pharm_perm[T], T]
                H2[:, T] = Ph[pharm_perm[T], T]
                N2[:, T] = Pn[pharm_perm[T], T]
            P, Ph, Pn = P2, H2, N2
        if pharm_line is not None:
            P, Ph, Pn = P[:, pharm_line], Ph[:, pharm_line], Pn[:, pharm_line]
        cs = self.S if cot_perm is None else self.S[cot_perm]
        es = np.where(self.esm_has, ident, -1) if esm_perm is None else np.where(self.esm_has[esm_perm], esm_perm, -1)
        return KnowledgeB(self.lm_idx[sp], ident, np.arange(self.L) if pharm_line is None else pharm_line, cs, es, P, Ph, Pn)

    def global_perms(self, seed):
        G = len(self.genes)
        return dict(self_perm=permutation_from(self.self_donors, G, rng_for("self", seed)),
                    pharm_perm=[permutation_from(self.pharm_donors[T], G, rng_for(f"pharm{T}", seed)) for T in range(self.L)],
                    cot_perm=permutation_from(self.cot_donors, G, rng_for("cot", seed)),
                    esm_perm=permutation_from(self.esm_donors, G, rng_for("esm", seed)))

    def setting(self, K: KnowledgeB, q_g: np.ndarray, q_line: np.ndarray, ref_mask: np.ndarray, salt: str,
                with_truth: bool = True, routes=None):
        routes = routes or self.ROUTES
        nq, p = len(q_g), self.p
        out_y = np.zeros((nq, p))
        gen = np.zeros((nq, p))
        outs = {r: dict(f=np.zeros((nq, p)), avail=np.zeros(nq, bool), gbar=np.zeros((nq, p)), spread=np.zeros(nq),
                        cf=np.zeros(nq), co=np.zeros(nq), desc=np.zeros((nq, 3))) for r in routes}
        for T in range(self.L):
            qi = np.flatnonzero(q_line == T)
            if not len(qi):
                continue
            refs = np.flatnonzero(ref_mask & self.has[:, T])
            mu = self.Y[refs, T].astype(np.float64).mean(0)
            Rc = self.Y[refs, T].astype(np.float64) - mu
            gT = unit(unit(Rc).mean(0))
            gen[qi] = gT
            g = q_g[qi]
            y = self.Y[g, T].astype(np.float64) - mu
            out_y[qi] = y
            yy = y if with_truth else None

            def finish(r, pred, av, desc, draws):
                o = outs[r]
                o["f"][qi] = np.where(av[:, None], pred, 0.0); o["avail"][qi] = av; o["desc"][qi] = desc
                acc = OrbitAccumulator(len(qi), p, yy)
                for fm in draws:
                    acc.add(fm)
                gb, s, c = acc.result()
                o["gbar"][qi] = np.where(av[:, None], gb, 0.0); o["spread"][qi] = np.where(av, s, 0.0)
                if yy is not None:
                    o["cf"][qi] = np.where(av, cos_rows(pred, y), 0.0); o["co"][qi] = np.where(av, c, 0.0)

            if "self" in routes:
                idx = K.self_idx[g]
                av = (idx >= 0) & self.is_lm[g]
                pred = np.zeros((len(qi), p))
                pred[av, idx[av]] = -1.0
                rng = rng_for("self", salt, T)
                draws = []
                for m in range(M_ORBIT):
                    fm = np.zeros((len(qi), p))
                    for a in np.flatnonzero(av):
                        dn = rng.choice(self.self_donors[g[a]])
                        fm[a, K.self_idx[dn]] = -1.0
                    draws.append(fm)
                finish("self", pred, av, np.zeros((len(qi), 3)), draws)
            if "pharm" in routes:
                av = K.pharm_has[g, T]
                pred = K.pharm[g, T]
                rng = rng_for("pharm", salt, T)
                draws = []
                for m in range(M_ORBIT):
                    dn = np.array([rng.choice(self.pharm_donors[K.pharm_line[T]][x]) if x in self.pharm_donors[K.pharm_line[T]]
                                   and len(self.pharm_donors[K.pharm_line[T]][x]) else x for x in g])
                    draws.append(K.pharm[dn, T])
                desc = np.stack([np.log1p(K.pharm_n[g, T]), np.zeros(len(qi)), np.zeros(len(qi))], 1)
                finish("pharm", pred, av, desc, draws)
            if "cotarget" in routes:
                kr = refs[K.cmp_sets[refs].any(1)]
                Rk = self.Y[kr, T].astype(np.float64) - mu
                sim = jaccard(K.cmp_sets[g], K.cmp_sets[kr])
                sim[np.equal.outer(g, kr)] = -1.0
                pred, av, top, meank, used = knn_mean(sim, Rk, 10, 1.0, 0.0)
                rng = rng_for("cot", salt, T)
                draws = []
                for m in range(M_ORBIT):
                    dn = np.array([rng.choice(self.cot_donors[x]) if x in self.cot_donors and len(self.cot_donors[x]) else x for x in g])
                    sm = jaccard(K.cmp_sets[dn], K.cmp_sets[kr])
                    sm[np.equal.outer(g, kr)] = -1.0
                    draws.append(knn_mean(sm, Rk, 10, 1.0, 0.0)[0])
                finish("cotarget", pred, av, np.stack([top, meank, np.log1p(used)], 1), draws)
            if "esm" in routes:
                kr = refs[self.esm_has[refs]]
                Rk = self.Y[kr, T].astype(np.float64) - mu
                src = K.esm_src[g]
                avq = src >= 0
                E = np.where(avq[:, None], self.esm[np.maximum(src, 0)], 0.0)
                sim = E @ self.esm[kr].T
                sim[np.equal.outer(g, kr)] = -1.0
                sim[~avq] = -1.0
                pred, av, top, meank, used = knn_mean(sim, Rk, 10, 1.0, 0.0)
                av &= avq
                rng = rng_for("esm", salt, T)
                draws = []
                for m in range(M_ORBIT):
                    dn = np.array([rng.choice(self.esm_donors[x]) if x in self.esm_donors and len(self.esm_donors[x]) else x for x in np.maximum(src, 0)])
                    sm = self.esm[dn] @ self.esm[kr].T
                    sm[np.equal.outer(g, kr)] = -1.0
                    sm[~avq] = -1.0
                    draws.append(knn_mean(sm, Rk, 10, 1.0, 0.0)[0])
                finish("esm", pred, av, np.stack([top, meank, np.log1p(used)], 1), draws)
        names = {"self": ("none0", "none1", "none2"), "pharm": ("log_compounds", "none1", "none2"),
                 "cotarget": ("top_sim", "mean_k_sim", "log_used"), "esm": ("top_sim", "mean_k_sim", "log_used")}
        res = {r: RouteOut(outs[r]["f"], outs[r]["avail"], outs[r]["gbar"], outs[r]["spread"], outs[r]["desc"], names[r],
                           outs[r]["cf"] if with_truth else None, outs[r]["co"] if with_truth else None) for r in routes}
        return res, gen, out_y
