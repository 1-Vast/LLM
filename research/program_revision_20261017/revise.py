"""Agent core: counterexample diagnosis, edit proposal, distinguishing experiments and revision.

File summary
- Path: research/program_revision_20261017/revise.py
- Purpose: the evaluated MAESTRO revision process over an editable program library, plus the
  conventional search that uses the same language, acceptance rule and evaluation budget.
- Development bench (`Bench`): for every source development project p, a `ContextFold` that
  predicts p's QUERY lines from all other source lines (the distinguishing-experiment arena)
  and one that predicts p's SUPPORT lines (the diagnosis arena). Support and query lines of a
  project are disjoint. Query outcomes are revealed only through `reveal`, after the candidate's
  predictions and nominations are committed (digest written first). Query outcomes reused for
  many candidates are development data, never confirmation.
- Edits (`Edit`): add(scope, state) | retire(key) | split(key, gate) -> two programs gated by
  gate and not-gate | replace_state(key, state) | narrow(key, scope) | measure(key=design probe
  to drop, gate=new probe, optional scope/state): a joint response-and-measurement edit that is
  evaluated on the bench rebuilt under the new design. Textual variants with identical semantics
  are refused (SEMANTIC_DUPLICATE, NO_SEMANTIC_CHANGE), as are interactions aliased with drug and
  line offsets on the source observation pattern (INTERACTION_NOT_IDENTIFIABLE). Capacity: <= 12 programs,
  <= 3 atoms per program; a scope needs >= 5 source drugs from >= 2 structure groups; a binary
  state needs >= 5 positive source lines from >= 2 lineages (a lineage atom: >= 5 lines). No
  drug or line identifier exists in the language, so a program cannot be a lookup table.
- Distinguishing experiment: the pairs nominated by exactly one of (current, edited) library on
  all development query lines. Its cost is 2 wells per newly revealed pair. Acceptance (frozen):
  log-likelihood ratio of the edited over the current predictive on the revealed pairs >= 3.0
  (likelihood ratio 20) AND hits(edited-only) - hits(current-only) >= 1. At most one accepted
  edit per step: the largest hit gain, then the largest LLR.
- Proposers: `EnumerativeProposer` (residual-association screen; ``scope_of_screen`` "project"
  emphasises the current project's support lines, "global" pools all support lines) and
  `llm_proposer.LLMProposer` (same diagnosis packet, same number of candidates per step).
- Interfaces: `SEED_LIBRARY`, `Bench`, `Edit`, `diagnose`, `EnumerativeProposer`, `run_revision`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

import numpy as np

from engine import INFO, ContextFold, Domain, legal_atoms, nominate
from vc import Program, ProgramLibrary, atoms, is_binary, parse_state, scope_mask, state_text

# Pre-specified from textbook pharmacogenomics (written before any program result was inspected).
SEED_LIBRARY = [
    ("moa:MEK inhibitor", "mut:BRAF"), ("moa:RAF inhibitor", "mut:BRAF"),
    ("moa:MEK inhibitor", "mut:KRAS"), ("moa:MEK inhibitor", "mut:NRAS"),
    ("moa:EGFR inhibitor", "mut:EGFR"), ("moa:PI3K inhibitor", "mut:PIK3CA"),
    ("moa:MDM inhibitor", "mut:TP53"), ("moa:mTOR inhibitor", "mut:PTEN"),
    ("moa:CDK inhibitor", "mut:RB1"), ("moa:AKT inhibitor", "mut:PTEN"),
]
MAX_PROGRAMS = 12
MAX_ATOMS = 3
N_COMPOSE = None  # binary atoms entering the composition screen (None = every binary atom; no hierarchy)
LLR_ACCEPT = 3.0
WELLS_PER_PAIR = 2


@dataclass
class Edit:
    op: str
    scope: str = ""
    state: str = ""
    key: str = ""
    gate: str = ""
    origin: str = ""
    rationale: str = ""
    direction: str = ""   # "sensitising" | "protective" | "" (committed sign of the effect)

    def label(self) -> str:
        return json.dumps({k: v for k, v in asdict(self).items() if v and k != "rationale"}, sort_keys=True)


class Bench:
    def __init__(self, dom: Domain, info: str, probe_cores, strong=None):
        self.dom, self.info = dom, info
        self.probes, self.strong = list(probe_cores), strong
        L = dom.lines
        src = np.flatnonzero(dom.src_line)
        self.projects = sorted(set(L.project.to_numpy()[src]))
        proj, role = L.project.to_numpy(), L.role.to_numpy()
        self.query, self.support = {}, {}
        for p in self.projects:
            q = np.flatnonzero((proj == p) & (role == "query"))
            s = np.flatnonzero((proj == p) & (role == "support"))
            self.query[p] = ContextFold(dom, np.setdiff1d(src, q), q, info, probe_cores, strong=strong)
            self.support[p] = ContextFold(dom, np.setdiff1d(src, s), s, info, probe_cores, strong=strong)
        self.drows = self.query[self.projects[0]].drows
        self.structure = dom.drugs.structure_group.to_numpy()
        self.revealed = set()
        # observation pattern of the source training data (drugs x source lines)
        self.observed = np.isfinite(dom.Ymean[np.ix_(self.drows, src)])

    def with_design(self, probe_cores):
        """The same bench under another probe design (cached fits; shares the revealed set)."""

        nb = Bench(self.dom, self.info, probe_cores, self.strong)
        nb.revealed = self.revealed
        return nb

    def query_lines(self) -> int:
        return int(sum(len(self.query[p].target) for p in self.projects))

    # ---------------------------------------------------------- validation
    def validate(self, lib: ProgramLibrary, edit: Edit):
        """Return (new_library, None) or (None, refusal_code)."""

        dom = self.dom
        legal = legal_atoms(self.info)
        new = lib.copy()
        keys = new.keys()
        try:
            if edit.op == "add":
                prog = Program(edit.scope, edit.state, edit.origin, edit.rationale[:200])
                new.programs.append(prog)
            elif edit.op == "retire":
                if edit.key not in keys:
                    return None, "UNKNOWN_PROGRAM"
                new.programs = [p for p in new.programs if p.key != edit.key]
            elif edit.op == "split":
                if edit.key not in keys:
                    return None, "UNKNOWN_PROGRAM"
                old = next(p for p in new.programs if p.key == edit.key)
                g = state_text(parse_state(edit.gate))
                if not is_binary(parse_state(g)):
                    return None, "GATE_NOT_BINARY"
                st = state_text(parse_state(old.state))
                if is_binary(parse_state(st)):
                    a = Program(old.scope, f"and({st},{g})", edit.origin, edit.rationale[:200])
                    b = Program(old.scope, f"andnot({st},{g})", edit.origin, edit.rationale[:200])
                else:
                    # continuous state: one program per gate arm, each gated by mul
                    a = Program(old.scope, f"mul({st},{g})", edit.origin, edit.rationale[:200])
                    b = Program(old.scope, st, edit.origin, edit.rationale[:200])
                new.programs = [p for p in new.programs if p.key != edit.key] + [a, b]
            elif edit.op == "replace_state":
                if edit.key not in keys:
                    return None, "UNKNOWN_PROGRAM"
                old = next(p for p in new.programs if p.key == edit.key)
                new.programs = [p for p in new.programs if p.key != edit.key] + [Program(old.scope, edit.state, edit.origin, edit.rationale[:200])]
            elif edit.op == "narrow":
                if edit.key not in keys:
                    return None, "UNKNOWN_PROGRAM"
                old = next(p for p in new.programs if p.key == edit.key)
                new.programs = [p for p in new.programs if p.key != edit.key] + [Program(edit.scope, old.state, edit.origin, edit.rationale[:200])]
            else:
                return None, "UNKNOWN_OPERATION"
        except (ValueError, StopIteration):
            return None, "UNPARSABLE_EDIT"
        if len(new.programs) > MAX_PROGRAMS:
            return None, "LIBRARY_CAPACITY"
        if len(set(new.keys())) != len(new.keys()):
            return None, "DUPLICATE_PROGRAM"
        if new.digest() == lib.digest():
            return None, "NO_STRUCTURAL_CHANGE"
        src_lines = np.flatnonzero(dom.src_line)
        for p in new.programs:
            if p.key in keys:
                continue
            try:
                tree = parse_state(p.state)
            except ValueError:
                return None, "UNPARSABLE_STATE"
            ats = atoms(tree)
            if len(ats) > MAX_ATOMS:
                return None, "PROGRAM_TOO_COMPLEX"
            for at in ats:
                if at[0] not in legal:
                    return None, "MEASUREMENT_NOT_IN_CONDITION"
                if at[0] == "probe" and at[1] not in self.query[self.projects[0]].probe_cores:
                    return None, "PROBE_NOT_IN_DESIGN"
            try:
                sm = scope_mask(p.scope, dom.df, self.drows)
            except ValueError:
                return None, "UNKNOWN_SCOPE"
            if sm.sum() < 5 or len(set(self.structure[self.drows[sm]])) < 2:
                return None, "SCOPE_TOO_NARROW"
            from vc import LineContext
            ctx = LineContext(dom.lf, src_lines, {}, np.zeros(len(src_lines)))
            if is_binary(tree):
                try:
                    v = ctx.state(tree)
                except KeyError as e:
                    return None, "UNKNOWN_ATOM"
                pos = v > 0.5
                if not identifiable(self.observed, sm, v):
                    return None, "INTERACTION_NOT_IDENTIFIABLE"
                lin = dom.lines.primary_tissue.to_numpy()[src_lines]
                only_lin = all(a[0] == "lin" for a in ats)
                if pos.sum() < 5 or (not only_lin and len(set(lin[pos])) < 2):
                    return None, "GATE_TOO_RARE"
                if (~pos).sum() < 5:
                    return None, "GATE_TOO_COMMON"
            else:
                for at in ats:
                    if at[0] in ("mut", "lin", "expr"):
                        try:
                            ctx.atom(at)
                        except KeyError:
                            return None, "UNKNOWN_ATOM"
        sig_new = self.semantics(new)
        if len(set(sig_new)) != len(sig_new):
            return None, "SEMANTIC_DUPLICATE"
        if sorted(sig_new) == sorted(self.semantics(lib)):
            return None, "NO_SEMANTIC_CHANGE"
        return new, None

    def semantics(self, lib: ProgramLibrary):
        """Programs as (drug set, state values on source lines); textual variants collapse."""

        from vc import LineContext
        src_lines = np.flatnonzero(self.dom.src_line)
        ctx = LineContext(self.dom.lf, src_lines, {}, np.zeros(len(src_lines)))
        out = []
        for p in lib.programs:
            sm = scope_mask(p.scope, self.dom.df, self.drows)
            tree = parse_state(p.state)
            try:
                st = ctx.state(tree).astype(np.float32).tobytes() if is_binary(tree) else p.state.encode()
            except KeyError:
                st = p.state.encode()
            out.append(hashlib.sha256(sm.tobytes() + b"|" + st).hexdigest()[:16])
        return out

    # ---------------------------------------------------------- committed predictions
    def commit(self, lib: ProgramLibrary):
        """Nominations and predictive moments on every development query line (cross-fitted)."""

        out = {}
        for p in self.projects:
            f = self.query[p]
            mean, var, score = f.apply(lib)
            nom = nominate(score, self.dom.tie_drug[f.drows])
            out[p] = (nom, mean, var)
        blob = json.dumps({p: out[p][0].tolist() for p in self.projects}).encode()
        return out, hashlib.sha256(blob).hexdigest()[:16]

    def reveal(self, pairs):
        """Outcomes of the distinguishing experiment: (hit, known, m23) per (drug_row, line_row)."""

        dom = self.dom
        res = {}
        for d, c in pairs:
            known = bool(dom.known[d, c])
            m = np.nanmean([dom.X2[d, c], dom.X3[d, c]]) if known else np.nan
            res[(d, c)] = (bool(dom.hit[d, c]), known, float(m) if known else None)
        new = len(set(pairs) - self.revealed)
        self.revealed |= set(pairs)
        return res, new

    def distinguish(self, cur, new, designed: int = 30):
        """Distinguishing experiment: nomination flips plus the ``designed`` pairs with the largest
        standardised predicted disagreement, with their predictive moments under both libraries."""

        pairs, info = [], {}
        cand = []
        for p in self.projects:
            f = self.query[p]
            pos = {d: i for i, d in enumerate(f.drows)}
            z = np.abs(new[p][1] - cur[p][1]) / np.sqrt(cur[p][2])
            for j, c in enumerate(f.target):
                a = set(f.drows[cur[p][0][:, j]])
                b = set(f.drows[new[p][0][:, j]])
                for d in a ^ b:
                    i = pos[d]
                    pairs.append((int(d), int(c)))
                    info[(int(d), int(c))] = dict(only="new" if d in b else "cur",
                                                  mc=float(cur[p][1][i, j]), vc=float(cur[p][2][i, j]),
                                                  mn=float(new[p][1][i, j]), vn=float(new[p][2][i, j]))
            top = np.argsort(-z, axis=None)[:designed]
            for t in top:
                i, j = np.unravel_index(t, z.shape)
                if z[i, j] <= 1e-9:
                    continue
                cand.append((float(z[i, j]), int(f.drows[i]), int(f.target[j]), p, i, j))
        cand.sort(key=lambda x: -x[0])
        for _, d, c, p, i, j in cand[:designed]:
            if (d, c) in info:
                continue
            pairs.append((d, c))
            info[(d, c)] = dict(only="neither", mc=float(cur[p][1][i, j]), vc=float(cur[p][2][i, j]),
                                mn=float(new[p][1][i, j]), vn=float(new[p][2][i, j]))
        return pairs, info


def identifiable(observed: np.ndarray, scope: np.ndarray, state: np.ndarray, iters: int = 60) -> bool:
    """Is a scope x state interaction separable from drug and line offsets on this observation
    pattern? Alternating projections remove row and column means over observed cells; an
    interaction that vanishes is aliased with main effects (e.g. a crossed design)."""

    x = np.where(observed, np.outer(scope.astype(float), state.astype(float)), 0.0)
    n0 = np.sqrt((x ** 2).sum())
    if n0 == 0:
        return False
    rc = np.maximum(observed.sum(1, keepdims=True), 1)
    cc = np.maximum(observed.sum(0, keepdims=True), 1)
    for _ in range(iters):
        x = np.where(observed, x - x.sum(1, keepdims=True) / rc, 0.0)
        x = np.where(observed, x - x.sum(0, keepdims=True) / cc, 0.0)
    return bool(np.sqrt((x ** 2).sum()) / n0 > 1e-3)


def loglik(y, m, v):
    return -0.5 * (np.log(2 * np.pi * v) + (y - m) ** 2 / v)


def evaluate_edit(bench: Bench, lib: ProgramLibrary, cur_commit, edit: Edit):
    """Validate, commit, run the distinguishing experiment, and apply the frozen acceptance rule."""

    rec = {"edit": json.loads(edit.label()), "rationale": edit.rationale[:300]}
    nb, probe_wells = bench, 0
    if edit.op == "measure":
        nb, refusal = measurement_bench(bench, lib, edit)
        if refusal is None:
            new_lib, refusal = (nb.validate(lib, Edit("add", scope=edit.scope, state=edit.state, origin=edit.origin,
                                                      rationale=edit.rationale)) if edit.scope else (lib.copy(), None))
            probe_wells = nb.query_lines()  # the new probe measured once on every development query line
    else:
        new_lib, refusal = bench.validate(lib, edit)
    if refusal:
        rec.update(decision="refused", reason=refusal)
        return rec, None
    new_commit, digest = nb.commit(new_lib)
    pairs, info = bench.distinguish(cur_commit[0], new_commit)
    rec["committed_digest"] = digest
    rec["distinguishing_pairs"] = len(pairs)
    outcomes, newly = bench.reveal(pairs)  # revealed only after the digest above is recorded
    rec["wells_new"] = WELLS_PER_PAIR * newly + probe_wells
    if probe_wells:
        rec["design_after"] = nb.probes
    n_plus = sum(1 for k in pairs if outcomes[k][0] and info[k]["only"] == "new")
    n_minus = sum(1 for k in pairs if outcomes[k][0] and info[k]["only"] == "cur")
    unknown = sum(1 for k in pairs if not outcomes[k][1])
    llr = 0.0
    for k in pairs:
        y = outcomes[k][2]
        if y is None:
            continue
        llr += loglik(y, info[k]["mn"], info[k]["vn"]) - loglik(y, info[k]["mc"], info[k]["vc"])
    rec.update(hits_new_only=n_plus, hits_cur_only=n_minus, unknown=unknown, llr=round(float(llr), 3))
    # committed direction check (the LLM may state a sign; magnitudes always come from fitting)
    direction_ok = True
    if edit.op == "add" and edit.direction in ("sensitising", "protective"):
        betas = []
        for p in nb.projects:
            f = nb.query[p]
            ctx_tr, _ = f.contexts()
            tmp = new_lib.copy()
            tmp.fit(f.R_train, tmp.states(ctx_tr), bench.dom.df, f.drows)
            k = [q.key for q in tmp.programs].index(new_lib.programs[-1].key)
            betas.append(tmp.beta[k])
        sign = float(np.mean(betas))
        rec["fitted_shared_loading"] = round(sign, 4)
        direction_ok = (sign < 0) if edit.direction == "sensitising" else (sign > 0)
        rec["direction_committed"] = edit.direction
    ok = llr >= LLR_ACCEPT and (n_plus - n_minus) >= 1 and direction_ok
    rec["decision"] = "accept_candidate" if ok else "reject"
    if not ok:
        rec["reason"] = ("DIRECTION_CONTRADICTED" if not direction_ok else
                         "INSUFFICIENT_EVIDENCE" if llr < LLR_ACCEPT else "NO_DECISION_GAIN")
    return rec, (new_lib, (new_commit, digest), nb) if ok else None


def measurement_bench(bench: Bench, lib: ProgramLibrary, edit: Edit):
    """A measurement edit swaps one design probe (``key``) for a source drug (``gate``)."""

    dom = bench.dom
    if edit.key not in bench.probes:
        return None, "PROBE_NOT_IN_DESIGN"
    if edit.gate not in dom.drug_index or not dom.src_drug[dom.drug_index[edit.gate]]:
        return None, "UNKNOWN_PROBE"
    if edit.gate in bench.probes:
        return None, "PROBE_ALREADY_IN_DESIGN"
    if any(edit.key in p.state for p in lib.programs):
        return None, "PROBE_IN_USE"
    return bench.with_design([edit.gate if c == edit.key else c for c in bench.probes]), None


# ---------------------------------------------------------------- diagnosis

def candidate_scopes(bench: Bench):
    dom = bench.dom
    out = []
    for kind, vocab in (("moa", dom.df["moa_vocab"]), ("target", dom.df["target_vocab"])):
        for t in vocab:
            m = scope_mask(f"{kind}:{t}", dom.df, bench.drows)
            if m.sum() >= 5 and len(set(bench.structure[bench.drows[m]])) >= 2:
                out.append((f"{kind}:{t}", m))
    return out


def candidate_attributes(bench: Bench, rows, ctx):
    dom = bench.dom
    legal = legal_atoms(bench.info)
    attrs = []
    if "mut" in legal:
        for g in dom.lf["panel_genes"]:
            attrs.append((f"mut:{g}", ctx.atom(("mut", g))))
    for t in dom.lf["lineage_names"]:
        v = ctx.atom(("lin", t))
        if v.sum() >= 2:
            attrs.append((f"lin:{t}", v))
    if "probe" in legal:
        for c in ctx.probe_values:
            attrs.append((f"probe:{c}", ctx.atom(("probe", c))))
    attrs.append(("b", ctx.atom(("b",))))
    if "expr" in legal:
        for g in dom.lf["expr_genes"][:500]:
            attrs.append((f"expr:{g}", ctx.atom(("expr", g))))
    return attrs


def diagnose(bench: Bench, lib: ProgramLibrary, project: str | None, top: int = 30):
    """Counterexample clusters: drug scopes whose residuals on support lines track a line attribute.

    Residuals are observed minus committed predictions for SUPPORT lines predicted as new lines
    (cross-fitted). With ``project``, the statistic is computed on that project's support lines
    and reported alongside its value over all support lines.
    """

    dom = bench.dom
    E_all, rows_all, attr_all = [], [], {}
    per_project = {}
    for p in bench.projects:
        f = bench.support[p]
        mean, var, score = f.apply(lib)
        Y = dom.Ymean[np.ix_(f.drows, f.target)]
        E = (Y - mean) / np.sqrt(var)
        E_all.append(E)
        _, ctx = f.contexts()
        for name, v in candidate_attributes(bench, f.target, ctx):
            attr_all.setdefault(name, []).append(v)
        per_project[p] = len(f.target)
        rows_all.append(np.full(len(f.target), p))
        # decision counterexamples: missed hits and false nominations on this project's lines
    E = np.column_stack(E_all)
    proj = np.concatenate(rows_all)
    attrs = {k: np.concatenate(v) for k, v in attr_all.items() if len(v) == len(bench.projects)}
    scopes = candidate_scopes(bench)
    names = list(attrs)
    A = np.column_stack([attrs[n] for n in names])
    A = (A - A.mean(0)) / (A.std(0) + 1e-9)
    S = np.column_stack([np.nanmean(np.where(np.isfinite(E[m]), E[m], np.nan), 0) for _, m in scopes])
    S = np.nan_to_num(S)
    out = []
    sel = np.ones(len(proj), bool) if project is None else (proj == project)

    def tstats(mask):
        n = mask.sum()
        Sm = S[mask] - S[mask].mean(0)
        Am = A[mask] - A[mask].mean(0)
        cov = Am.T @ Sm / max(n - 1, 1)
        sa = Am.std(0, ddof=1)[:, None] + 1e-9
        ss = Sm.std(0, ddof=1)[None, :] + 1e-9
        r = cov / (sa * ss)
        return r * np.sqrt(max(n - 2, 1) / np.maximum(1 - r ** 2, 1e-9)), r

    # compositions over the same language: conjunctions of binary atoms and continuous atoms gated by
    # them (the conventional search sees every state form the agent can use). No main-effect hierarchy:
    # Stage A S4c showed a hierarchical screen misses a pure interaction that the rule would accept.
    t0, _ = tstats(np.ones(len(proj), bool))
    strength = np.abs(t0).max(1)
    raw = {n: attrs[n] for n in names}
    binary = [n for n in names if n.split(":")[0] in ("mut", "lin")]
    cont = [n for n in names if n.split(":")[0] in ("probe", "b")]
    cont += sorted([n for n in names if n.startswith("expr:")], key=lambda n: -strength[names.index(n)])[:5]
    binary = [n for n in binary if 5 <= (raw[n] > 0.5).sum() <= len(raw[n]) - 5]
    top_bin = sorted(binary, key=lambda n: -strength[names.index(n)])[:N_COMPOSE]
    comp = {}
    for i, a in enumerate(top_bin):
        for b in top_bin[i + 1:]:
            comp[f"and({a},{b})"] = raw[a] * raw[b]
            comp[f"andnot({a},{b})"] = raw[a] * (1 - raw[b])
            comp[f"andnot({b},{a})"] = raw[b] * (1 - raw[a])
        for c in cont:
            comp[f"mul({c},{a})"] = raw[c] * raw[a]
    comp = {k: v for k, v in comp.items() if (v != 0).sum() >= 5 and (v == 0).sum() >= 5}

    def _corr(x, y):
        sx, sy = x.std(), y.std()
        return 0.0 if sx == 0 or sy == 0 else float(np.mean((x - x.mean()) * (y - y.mean())) / (sx * sy))

    # a composition indistinguishable from one of its parents on the support lines is redundant
    parents = {k: [n for n in names if n in k] for k in comp}
    comp = {k: v for k, v in comp.items() if all(abs(_corr(v, raw[n])) < 0.95 for n in parents[k])}
    if comp:
        names = names + list(comp)
        C = np.column_stack(list(comp.values()))
        A = np.column_stack([A, (C - C.mean(0)) / (C.std(0) + 1e-9)])
    t_all, r_all = tstats(np.ones(len(proj), bool))
    t_loc, r_loc = tstats(sel) if project is not None and sel.sum() >= 5 else (t_all, r_all)
    key = np.abs(t_loc) + 0.5 * np.abs(t_all)
    existing = set(lib.keys())
    flat = np.argsort(-key, axis=None)
    kept = []  # (scope mask, state column) of listed clusters, for a diversity filter
    for idx in flat:
        i, j = np.unravel_index(idx, key.shape)
        if any(k.startswith(scopes[j][0] + "|") and names[i] in k for k in existing):
            continue
        m = scopes[j][1]
        redundant = False
        for m2, i2 in kept:
            jac = (m & m2).sum() / max((m | m2).sum(), 1)
            if jac >= 0.8 and abs(_corr(A[:, i], A[:, i2])) >= 0.7:
                redundant = True
                break
        if redundant:
            continue
        kept.append((m, i))
        out.append({"scope": scopes[j][0], "state": names[i], "n_drugs": int(scopes[j][1].sum()),
                    "t_project": round(float(t_loc[i, j]), 2), "t_all_support": round(float(t_all[i, j]), 2),
                    "r_all_support": round(float(r_all[i, j]), 3),
                    "residual_direction": "more sensitive where state high" if r_all[i, j] < 0 else "less sensitive where state high"})
        if len(out) >= top:
            break
    # measurement candidates: unmeasured source drugs whose readout on support lines tracks a scope
    # residual (drugs inside the scope are excluded: their own readout is not a state measurement)
    lines_all = np.concatenate([bench.support[p].target for p in bench.projects])
    design = set(bench.probes)
    cand = [d for d in bench.drows if dom.drugs.core[d] not in design]
    P = dom.X1[np.ix_(cand, lines_all)].T
    with np.errstate(all="ignore"):
        P = np.where(np.isfinite(P), P, np.nanmean(P, 0, keepdims=True))
    P = np.nan_to_num(P)
    Pz = (P - P.mean(0)) / (P.std(0) + 1e-9)
    Sz = (S - S.mean(0)) / (S.std(0) + 1e-9)
    n = len(lines_all)
    rr = Pz.T @ Sz / n
    tm = rr * np.sqrt((n - 2) / np.maximum(1 - rr ** 2, 1e-9))
    pos = {d: i for i, d in enumerate(bench.drows)}
    for j, (_, m) in enumerate(scopes):
        inside = np.array([m[pos[d]] for d in cand])
        tm[inside, j] = 0.0
    meas = []
    for idx in np.argsort(-np.abs(tm), axis=None)[:15]:
        i, j = np.unravel_index(idx, tm.shape)
        d = cand[i]
        meas.append({"scope": scopes[j][0], "probe": dom.drugs.core[d], "probe_name": str(dom.drugs.name[d]),
                     "probe_moa": str(dom.drugs.moa[d]), "t_all_support": round(float(tm[i, j]), 2)})
    return {"project": project, "support_lines": int(sel.sum()), "clusters": out, "measurement_candidates": meas,
            "library": [{"key": p.key, "origin": p.origin} for p in lib.programs]}


class EnumerativeProposer:
    """Conventional search: the top residual-association clusters become add edits; the weakest
    program (smallest |shared loading|) is offered for retirement once the library is non-empty."""

    name = "enumerative"

    def __init__(self, n: int = 6, joint: bool = False):
        self.n = n
        self.joint = joint
        self.tried = set()

    def propose(self, diagnosis, lib: ProgramLibrary, bench: Bench):
        edits = []
        if self.joint:
            # measurement edits: swap the last-designed probe the library does not use for an unmeasured
            # source drug whose readout tracks a scope residual, and add the program that reads it
            free = [c for c in reversed(bench.probes) if not any(c in p.state for p in lib.programs)]
            for m in diagnosis.get("measurement_candidates", []):
                if len(edits) >= 2 or not free:
                    break
                sig = ("measure", m["scope"], m["probe"])
                if sig in self.tried:
                    continue
                self.tried.add(sig)
                edits.append(Edit("measure", key=free[0], gate=m["probe"], scope=m["scope"], state=f"probe:{m['probe']}",
                                  origin=self.name, rationale=f"unmeasured readout tracks scope residual t={m['t_all_support']}"))
        # refinements of existing programs: a cluster in an existing program's scope becomes a split
        # (binary state) or a state replacement (continuous state); at most two per step
        by_scope = {p.scope: p for p in lib.programs}
        for c in diagnosis["clusters"]:
            if len(edits) >= 2 or c["scope"] not in by_scope:
                continue
            old = by_scope[c["scope"]]
            op = "split" if is_binary(parse_state(c["state"])) and is_binary(parse_state(old.state)) else "replace_state"
            sig = (op, old.key, c["state"])
            if sig in self.tried:
                continue
            self.tried.add(sig)
            edits.append(Edit(op, key=old.key, gate=c["state"] if op == "split" else "",
                              state=c["state"] if op == "replace_state" else "", origin=self.name,
                              rationale=f"residual association within an existing scope t={c['t_project']}"))
        for c in diagnosis["clusters"]:
            if len(edits) >= self.n - (1 if lib.programs else 0):
                break
            sig = (c["scope"], c["state"])
            if sig in self.tried:
                continue
            self.tried.add(sig)
            edits.append(Edit("add", scope=c["scope"], state=c["state"], origin=self.name,
                              rationale=f"residual association t={c['t_project']} (all support {c['t_all_support']})"))
        if lib.programs:
            f = bench.query[bench.projects[0]]
            ctx_tr, _ = f.contexts()
            tmp = lib.copy()
            tmp.fit(f.R_train, tmp.states(ctx_tr), bench.dom.df, f.drows)
            k = int(np.argmin(np.abs(tmp.beta)))
            key = lib.programs[k].key
            if ("retire", key) not in self.tried:
                self.tried.add(("retire", key))
                edits.append(Edit("retire", key=key, origin=self.name, rationale="smallest shared loading"))
        return edits, {}


def run_revision(bench: Bench, lib: ProgramLibrary, proposer, rounds: int = 2, project_mode: bool = True,
                 log=None, budget_candidates: int | None = None):
    """Sequential revision. Returns (final library, trajectory list, accounting)."""

    traj = []
    cur_commit = bench.commit(lib)
    evaluated = 0
    wells = 0
    order = list(bench.projects)
    step = 0
    for r in range(rounds):
        for p in order:
            step += 1
            diag = diagnose(bench, lib, p if project_mode else None)
            edits, meta = proposer.propose(diag, lib, bench)
            recs, best = [], None
            for e in edits:
                if budget_candidates is not None and evaluated >= budget_candidates:
                    break
                rec, ok = evaluate_edit(bench, lib, cur_commit, e)
                if rec.get("decision") != "refused":
                    evaluated += 1
                wells += rec.get("wells_new", 0)
                recs.append(rec)
                if ok is not None:
                    gain = (rec["hits_new_only"] - rec["hits_cur_only"], rec["llr"])
                    if best is None or gain > best[0]:
                        best = (gain, ok, len(recs) - 1)
            if best is not None:
                lib, cur_commit, bench = best[1][0], best[1][1], best[1][2]
                recs[best[2]]["decision"] = "accepted"
            for rec in recs:
                if rec.get("decision") == "accept_candidate":
                    rec["decision"] = "acceptable_not_chosen"
            if hasattr(proposer, "feedback"):
                proposer.feedback(recs)
            entry = {"step": step, "round": r, "project": p, "proposer": proposer.name,
                     "counterexamples": diag["clusters"][:8], "proposer_meta": meta,
                     "candidates": recs, "library_after": lib.keys(),
                     "library_digest": lib.digest(), "design": list(bench.probes),
                     "evaluated_so_far": evaluated, "wells_so_far": wells}
            traj.append(entry)
            if log is not None:
                log.write(json.dumps(entry) + "\n")
                log.flush()
    return lib, traj, {"evaluated": evaluated, "distinguishing_wells": wells,
                       "revealed_pairs": len(bench.revealed), "design": list(bench.probes)}


def seed_library(bench: Bench):
    lib = ProgramLibrary()
    dropped = []
    for scope, state in SEED_LIBRARY:
        new, refusal = bench.validate(lib, Edit("add", scope=scope, state=state, origin="seed"))
        if refusal:
            dropped.append({"scope": scope, "state": state, "reason": refusal})
        else:
            lib = new
    return lib, dropped


def full_query_score(bench: Bench, lib: ProgramLibrary):
    """Log-likelihood of every known development query outcome and the nominated hits (all lines)."""

    dom = bench.dom
    ll, hits = 0.0, 0
    for p in bench.projects:
        f = bench.query[p]
        mean, var, score = f.apply(lib)
        nom = nominate(score, dom.tie_drug[f.drows])
        for j, c in enumerate(f.target):
            hits += int(dom.hit[f.drows[nom[:, j]], c].sum())
        Y = np.where(dom.known[np.ix_(f.drows, f.target)],
                     np.nanmean(np.stack([dom.X2[np.ix_(f.drows, f.target)], dom.X3[np.ix_(f.drows, f.target)]]), 0), np.nan)
        ok = np.isfinite(Y)
        ll += float(loglik(Y[ok], mean[ok], var[ok]).sum())
    return ll, hits


def stepwise_search(bench: Bench, lib: ProgramLibrary, n_screen: int = 100, budget: int = 120, log=None):
    """Conventional model selection over the same language: a marginal screen of the top global
    residual clusters on ALL development query outcomes, then greedy forward additions in screen
    order, each kept under the same thresholds (log-likelihood gain >= 3.0 and >= 1 more hit).
    It reads every query outcome (charged as such), not a distinguishing experiment."""

    diag = diagnose(bench, lib, None, top=n_screen)
    base_ll, base_hits = full_query_score(bench, lib)
    evaluated, traj, screen = 0, [], []
    for c in diag["clusters"]:
        if evaluated >= budget:
            break
        new, refusal = bench.validate(lib, Edit("add", scope=c["scope"], state=c["state"], origin="stepwise"))
        if refusal:
            traj.append({"phase": "screen", "edit": [c["scope"], c["state"]], "decision": "refused", "reason": refusal})
            continue
        ll, h = full_query_score(bench, new)
        evaluated += 1
        screen.append((ll - base_ll, h - base_hits, c["scope"], c["state"]))
        traj.append({"phase": "screen", "edit": [c["scope"], c["state"]], "dll": round(ll - base_ll, 3), "dhits": h - base_hits})
    screen.sort(key=lambda x: (-x[1], -x[0]))
    cur_ll, cur_hits = base_ll, base_hits
    for dll, dh, scope, state in screen:
        if evaluated >= budget or dll < LLR_ACCEPT or dh < 1:
            continue
        new, refusal = bench.validate(lib, Edit("add", scope=scope, state=state, origin="stepwise"))
        if refusal:
            continue
        ll, h = full_query_score(bench, new)
        evaluated += 1
        ok = ll - cur_ll >= LLR_ACCEPT and h - cur_hits >= 1
        traj.append({"phase": "forward", "edit": [scope, state], "dll": round(ll - cur_ll, 3), "dhits": h - cur_hits,
                     "decision": "accepted" if ok else "reject"})
        if ok:
            lib, cur_ll, cur_hits = new, ll, h
    if log is not None:
        for t in traj:
            log.write(json.dumps(t) + "\n")
    n_known = sum(int(bench.dom.known[np.ix_(bench.query[p].drows, bench.query[p].target)].sum()) for p in bench.projects)
    return lib, traj, {"evaluated": evaluated, "query_outcomes_read": n_known, "wells_charged": WELLS_PER_PAIR * n_known}
