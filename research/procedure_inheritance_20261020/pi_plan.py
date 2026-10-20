"""Executable experimental procedure ("plan"), its search/validation lifecycle, and the amortised-policy (distillation) baseline.

A plan is a small program, not a stored loading matrix or an explanation:
    applicability  the plan applies only if the deployed library is the one it was validated under (fingerprint) AND the background's public reference is within
                   `zmax` standard deviations of the training references; otherwise the default one-step planner runs instead (exit INAPPLICABLE)
    first          read pair p1
    second         residual r1 = y1 - a[p1]; the second read is second[bin(r1)] where bins are cut by `edges`; second == -1 is STOP (hand over to the default planner)
    update         posterior over the library regimes (+ unexplained U) after every read; if U > 0.5 the shared UNKNOWN exit replaces every later read by a direct read
    shortlist      top-K posterior-mean scores with recorded values kept; reads 3.. use the same default one-step planner as the conventional arms
Identity: `exec_sha` hashes the executable content, `pid` additionally hashes the history (parents, library fingerprint, training and validation backgrounds).
"""
from __future__ import annotations

import hashlib
import json
import time

import numpy as np

import pi_factors as F
import pi_model as M

ZMAX = 6.0
BIN_MERGE = 0.08


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


class Plan:
    def __init__(self, p1, edges, second, B, aref_mu, aref_sd, lib_fp=None, parents=(), train=(), val=(), bin_mass=None, zmax=ZMAX, force=False):
        self.p1, self.edges, self.second, self.B = int(p1), [round(float(e), 6) for e in edges], [int(s) for s in second], int(B)
        self.aref_mu, self.aref_sd = np.round(np.asarray(aref_mu, float), 5), np.round(np.asarray(aref_sd, float), 5)
        self.lib_fp, self.parents, self.train, self.val = lib_fp, tuple(parents), tuple(train), tuple(val)
        self.bin_mass = None if bin_mass is None else [float(x) for x in bin_mass]
        self.zmax, self.force = float(zmax), force
        assert len(self.second) == len(self.edges) + 1

    # ---- identity
    def content(self):
        return {"schema": "pi_plan_v1", "B": self.B, "first": self.p1, "edges": self.edges, "second": self.second,
                "exits": {"unknown_posterior_u": M.UNKNOWN_W, "stop": -1, "inapplicable": "default_kg1"},
                "applicability": {"zmax": self.zmax, "aref_mu": self.aref_mu.tolist(), "aref_sd": self.aref_sd.tolist()}}

    @property
    def exec_sha(self):
        return _sha(self.content())

    def history(self):
        return {"parents": list(self.parents), "lib_fp": self.lib_fp, "train": list(self.train), "val": list(self.val), "bin_mass": self.bin_mass}

    @property
    def pid(self):
        return _sha({"exec": self.exec_sha, "history": self.history()})

    def to_json(self):
        return {"pid": self.pid, "exec_sha": self.exec_sha, "content": self.content(), "history": self.history()}

    @staticmethod
    def from_json(d, force=False):
        c, h = d["content"], d["history"]
        pl = Plan(c["first"], c["edges"], c["second"], c["B"], c["applicability"]["aref_mu"], c["applicability"]["aref_sd"], h["lib_fp"], h["parents"], h["train"], h["val"],
                  h.get("bin_mass"), c["applicability"]["zmax"], force)
        assert pl.exec_sha == d["exec_sha"] and pl.pid == d["pid"], "plan artifact identity mismatch"
        return pl

    def rebound(self, lib_fp, train, val):
        return Plan(self.p1, self.edges, self.second, self.B, self.aref_mu, self.aref_sd, lib_fp, (self.pid,), train, val, self.bin_mass, self.zmax, self.force)

    def collapsed(self):
        """Ablation: keep the first read, replace the observation-dependent second read by one fixed read (the heaviest training branch)."""
        j = int(np.argmax(self.bin_mass)) if self.bin_mass else 0
        return Plan(self.p1, [], [self.second[j]], self.B, self.aref_mu, self.aref_sd, self.lib_fp, (self.pid,), self.train, self.val, [1.0], self.zmax, self.force)

    # ---- execution
    def applicable(self, lib, a):
        if lib is None:
            return False
        if not self.force and self.lib_fp != lib.fingerprint():
            return False
        z = np.abs((a - self.aref_mu) / (self.aref_sd + 1e-9))
        return bool(z.max() <= self.zmax)

    name = "plan"

    def choose(self, c):
        if c.step == 1:
            ok = self.applicable(c.lib, c.a)
            c.log["plan_applicable"] = ok
            c.log["plan_id"] = self.pid
            return self.p1 if ok else None
        if c.step == 2 and c.log.get("plan_applicable") and c.seq and c.seq[0][0] == self.p1:
            r1 = c.seq[0][1] - c.a[self.p1]
            b = int(np.searchsorted(self.edges, r1))
            c.log["branch"] = b
            p2 = self.second[b]
            if p2 < 0:
                c.log["plan_stop"] = True
                return None
            return p2 if p2 not in c.obs else None
        return None


class Student:
    """Amortised policy distilled from the two-step teacher: a depth-limited decision tree on (step, posterior over library components). Serialised as arrays."""
    name = "distill"

    def __init__(self, tree, classes, n_feat, lib_fp, meta=None):
        self.t, self.classes, self.n_feat, self.lib_fp, self.meta = tree, np.asarray(classes, int), n_feat, lib_fp, meta or {}

    def arrays(self, prefix=""):
        t = self.t
        return {prefix + k: np.asarray(t[k]) for k in ("left", "right", "feat", "thr", "value")} | {prefix + "classes": self.classes,
                prefix + "meta": np.array([self.n_feat])}

    @staticmethod
    def from_arrays(z, prefix, lib_fp):
        t = {k: z[prefix + k] for k in ("left", "right", "feat", "thr", "value")}
        return Student(t, z[prefix + "classes"], int(z[prefix + "meta"][0]), lib_fp)

    @property
    def sha(self):
        h = hashlib.sha256()
        for k in ("left", "right", "feat", "thr", "value"):
            h.update(np.asarray(self.t[k]).tobytes())
        h.update(self.classes.tobytes())
        return h.hexdigest()

    def probs(self, f):
        t, n = self.t, 0
        while t["left"][n] != -1:
            n = t["left"][n] if f[t["feat"][n]] <= t["thr"][n] else t["right"][n]
        v = t["value"][n]
        return v / max(v.sum(), 1e-12)

    def choose(self, c):
        if c.step > 2 or c.lib is None or c.lib.fingerprint() != self.lib_fp:
            return None
        f = np.concatenate([[c.step], c.w])
        pr = self.probs(f)
        legal = set(int(x) for x in c.legal())
        best, bp = None, -1.0
        for cls, p in zip(self.classes, pr):
            if int(cls) in legal and p > bp + 1e-12:
                best, bp = int(cls), p
        c.log["student_id"] = self.sha
        return best


def train_student(lib, A, recs, ids, max_depth=4):
    """Distil the two-step teacher (Kg2) on the released backgrounds (reads come from the recorded vectors). Returns (student or None, teacher_rows, cpu_seconds, n_teacher_decisions)."""
    from sklearn.tree import DecisionTreeClassifier
    t0 = time.process_time()
    X, y, rows, ndec = [], [], [], 0
    for j in ids:
        camp = M.Camp(A[j], recs[j], T=recs[j])
        row = M.run_campaign(lib, camp, 4, _Rec(M.Kg2(), X, y), arm="teacher")
        rows.append({"bg": int(j), "queries": row["queries"][:2]})
        ndec += 2
    if not X:
        return None, rows, time.process_time() - t0, ndec
    X, y = np.array(X), np.array(y)
    if len(set(y)) < 1:
        return None, rows, time.process_time() - t0, ndec
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=0).fit(X, y)
    tr = clf.tree_
    tree = {"left": tr.children_left, "right": tr.children_right, "feat": tr.feature, "thr": tr.threshold, "value": tr.value[:, 0, :]}
    st = Student(tree, clf.classes_, X.shape[1], lib.fingerprint())
    return st, rows, time.process_time() - t0, ndec


class _Rec:
    """Teacher wrapper that records (features, action) for the first two reads."""
    name = "teacher"

    def __init__(self, agent, X, y):
        self.a, self.X, self.y = agent, X, y

    def choose(self, c):
        p = self.a.choose(c)
        if c.step <= 2 and p is not None:
            self.X.append(np.concatenate([[c.step], c.w]).tolist())
            self.y.append(int(p))
        return p


# ------------------------------------------------------------------ plan construction and search
def level_centres(lib, p1):
    lev = sorted(float(x) for x in lib.Lfull[:lib.m1, p1])
    groups = [[lev[0]]]
    for v in lev[1:]:
        if v - groups[-1][-1] < BIN_MERGE:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [float(np.mean(g)) for g in groups]


def build_plan(lib, a_mean, aref_mu, aref_sd, B, p1=None, alt_rank=None, mass=None):
    """Model-based construction (counted as ordinary planning cost): p1 from the two-step lookahead at the prior, bins from the library's levels at p1, one-step best second read per bin."""
    P = len(a_mean)
    legal = np.arange(P)
    w0 = M.posterior(lib, {})
    if p1 is None:
        rk, _ = M.kg2_rank(lib, a_mean, {}, w0, legal)
        if not rk or rk[0][1] <= M.EPS_STOP:
            return None
        p1 = rk[0][0]
    cent = level_centres(lib, p1)
    edges = [(cent[i] + cent[i + 1]) / 2 for i in range(len(cent) - 1)]
    second = []
    rest = legal[legal != p1]
    for ctr in cent:
        obs = {p1: ctr}
        w = M.posterior(lib, obs)
        kg, _ = M.kg1_all(lib, a_mean, obs, w, rest)
        second.append(int(rest[np.lexsort((rest, -kg))][0]) if kg.max() > M.EPS_STOP else -1)
    return Plan(p1, edges, second, B, aref_mu, aref_sd, bin_mass=mass)


def _second_alternatives(lib, a_mean, plan, n=2):
    P = len(a_mean)
    cent = level_centres(lib, plan.p1)
    rest = np.array([q for q in range(P) if q != plan.p1])
    out = []
    for ctr in cent:
        obs = {plan.p1: ctr}
        w = M.posterior(lib, obs)
        kg, _ = M.kg1_all(lib, a_mean, obs, w, rest)
        out.append([int(q) for q in rest[np.lexsort((rest, -kg))][:n + 1]])
    return out


def mutations(lib, a_mean, plan, first_alts):
    """Deterministic ordered neighbours of a plan: alternative second reads per branch, STOP toggles, alternative first reads."""
    out = []
    nb = len(plan.second)
    if nb == len(level_centres(lib, plan.p1)):
        alts = _second_alternatives(lib, a_mean, plan)
        for j in range(nb):
            for q in alts[j]:
                if q != plan.second[j]:
                    s = list(plan.second)
                    s[j] = q
                    out.append(Plan(plan.p1, plan.edges, s, plan.B, plan.aref_mu, plan.aref_sd, bin_mass=plan.bin_mass))
    for j in range(nb):
        if plan.second[j] != -1:
            s = list(plan.second)
            s[j] = -1
            out.append(Plan(plan.p1, plan.edges, s, plan.B, plan.aref_mu, plan.aref_sd, bin_mass=plan.bin_mass))
    for q in first_alts:
        if q != plan.p1:
            pl = build_plan(lib, a_mean, plan.aref_mu, plan.aref_sd, plan.B, p1=q, mass=None)
            if pl is not None:
                out.append(pl)
    return out


def replay_plan(plan, ids, loo_libs, A, recs, B, default=False):
    """Replay on released backgrounds with their leave-one-out libraries; the recorded vector is both read table and truth."""
    out = []
    for j in ids:
        camp = M.Camp(A[j], recs[j], T=recs[j])
        agent = M.Kg1() if default or plan is None else _Forced(plan)
        out.append(M.run_campaign(loo_libs[j], camp, B, agent)["utility"])
    return np.array(out)


class _Forced:
    """Replay uses leave-one-out libraries whose fingerprints differ from the deployed one; applicability by fingerprint is checked at deployment, not in replay."""
    name = "plan"

    def __init__(self, plan):
        self.p = Plan(plan.p1, plan.edges, plan.second, plan.B, plan.aref_mu, plan.aref_sd, plan.lib_fp, (), (), (), plan.bin_mass, plan.zmax, force=True)

    def choose(self, c):
        return self.p.choose(c)


def learn_plan(mode, lib, labels_arr, ids, E, A, recs, B, val_ids, incumbent, archive, cap=F.CAND_CAP):
    """One generation of plan learning for one budget. mode 'on' (inheritance) seeds the search with the incumbent and archive; 'restart' rebuilds from the model-based seed only.
    Candidates are scored on the training backgrounds (leave-one-out libraries); the winner is validated against the incumbent on `val_ids`. Returns the decision record."""
    t0 = time.process_time()
    pos = {int(i): r for r, i in enumerate(ids)}
    loo = {}
    for j in ids:
        loo[j], _ = F.lib_from_labels(E, labels_arr, exclude=pos[j], min_members=1)
    # positional access: loo libs / A / recs are indexed by background id through dictionaries
    Ad = {int(i): A[pos[i]] for i in ids}
    Rd = {int(i): A[pos[i]] + E[pos[i]] for i in ids}
    train_ids = [i for i in ids if i not in val_ids]
    a_mean = A[[pos[i] for i in train_ids]].mean(0)
    aref_mu, aref_sd = a_mean, A[[pos[i] for i in train_ids]].std(0) + 1e-6
    lib_fp = lib.fingerprint()
    replays = 0
    evals = []                                                   # (plan, train score, source)

    def evaluate(pl, src):
        nonlocal replays
        u = replay_plan(pl, train_ids, loo, Ad, Rd, B)
        replays += len(train_ids)
        evals.append((pl, float(u.mean()), src))
        return float(u.mean())

    seeds = []
    reuse = []
    if mode == "on":
        if incumbent is not None:
            seeds.append((incumbent.rebound(lib_fp, train_ids, val_ids), "incumbent"))
        for k, pl in enumerate(archive[:2]):
            seeds.append((pl.rebound(lib_fp, train_ids, val_ids), "archive"))
    built = build_plan(lib, a_mean, aref_mu, aref_sd, B)
    if built is not None:
        seeds.append((Plan(built.p1, built.edges, built.second, B, aref_mu, aref_sd, lib_fp, (), train_ids, val_ids), "model_built"))
    seen = set()
    best, best_s, best_src = None, -1e9, None
    for pl, src in seeds:
        if len(evals) >= cap or pl.exec_sha in seen:
            continue
        seen.add(pl.exec_sha)
        s = evaluate(pl, src)
        if s > best_s + 1e-9:
            best, best_s, best_src = pl, s, src
    if best is not None:
        w0 = M.posterior(lib, {})
        rk, _ = M.kg2_rank(lib, a_mean, {}, w0, np.arange(len(a_mean)))
        first_alts = [p for p, _ in rk[:3]]
        queue = mutations(lib, a_mean, best, first_alts)
        while len(evals) < cap and queue:
            cand = queue.pop(0)
            cand = Plan(cand.p1, cand.edges, cand.second, B, aref_mu, aref_sd, lib_fp, (best.pid,), train_ids, val_ids, cand.bin_mass)
            if cand.exec_sha in seen:
                continue
            seen.add(cand.exec_sha)
            s = evaluate(cand, "mutation")
            if s > best_s + 1e-9:
                best, best_s, best_src = cand, s, "mutation"
                queue = mutations(lib, a_mean, best, first_alts)
    # branch-mass for the collapse ablation (from training reads of the first pair)
    if best is not None:
        r1 = np.array([Rd[j][best.p1] - Ad[j][best.p1] for j in train_ids])
        mass = np.bincount(np.searchsorted(best.edges, r1), minlength=len(best.second)).astype(float)
        best = Plan(best.p1, best.edges, best.second, B, aref_mu, aref_sd, lib_fp, best.parents, train_ids, val_ids, (mass / max(mass.sum(), 1)).tolist())
    # validation against the incumbent / default on the newest batch
    ref_u = replay_plan(None, val_ids, loo, Ad, Rd, B, default=True)
    replays += len(val_ids)
    inc_rb = incumbent.rebound(lib_fp, train_ids, val_ids) if (mode == "on" and incumbent is not None) else None
    inc_u = replay_plan(inc_rb, val_ids, loo, Ad, Rd, B) if inc_rb is not None else ref_u
    replays += len(val_ids) if inc_rb is not None else 0
    deployed, status, cmp_new = None, "none", None
    if best is not None:
        v_best = replay_plan(best, val_ids, loo, Ad, Rd, B)
        replays += len(val_ids)
        cmp_new = F.compare(v_best, inc_u)
        cmp_new["strict_library_rule"] = F.promote_rule(cmp_new["gain"], cmp_new["wins"], cmp_new["losses"])
        if F.promote_rule_plan(cmp_new["gain"], cmp_new["wins"], cmp_new["losses"]):
            deployed, status = best, "demonstrated"
    if deployed is None and inc_rb is not None:
        cmp_inc = F.compare(inc_u, ref_u)
        if cmp_inc["gain"] >= -F.EPS_VAL:
            deployed, status = inc_rb, "incumbent_kept"
        else:
            status = "incumbent_retired"
    if status == "demonstrated" and best_src in ("archive",):
        reuse.append("archive")
    # the winner must not be worse than the default planner on the validation batch
    if deployed is not None:
        dv = replay_plan(deployed, val_ids, loo, Ad, Rd, B)
        c_def = F.compare(dv, ref_u)
        if c_def["gain"] < -F.EPS_VAL:
            deployed, status = None, "rolled_back_to_default"
    ranked = sorted([e for e in evals if deployed is None or e[0].exec_sha != deployed.exec_sha], key=lambda e: -e[1])
    new_archive, shas = [], set()
    for pl, s, src in ranked:
        if pl.exec_sha not in shas and len(new_archive) < 3:
            shas.add(pl.exec_sha)
            new_archive.append(pl)
    rec = {"B": B, "mode": mode, "n_candidates": len(evals), "n_replays": replays, "cpu_s": time.process_time() - t0, "status": status,
           "deployed": None if deployed is None else deployed.pid, "deployed_exec": None if deployed is None else deployed.exec_sha,
           "best_source": best_src, "candidates": [{"exec": p.exec_sha[:12], "train": round(s, 6), "source": src} for p, s, src in evals],
           "vs_incumbent": cmp_new, "reuse": reuse, "archive": [p.exec_sha[:12] for p in new_archive]}
    return deployed, new_archive, rec
