"""Library lifecycle: bounded program search, strict validation, retirement, restart control, checkpoints and invocation records.

Statuses (a program is useful only when `demonstrated`):
  valid        fits and runs (software correctness; says nothing about usefulness)
  provisional  proposed this generation, not yet validated
  noninferior  within the margin of the incumbent on unseen cells; NOT counted as capability, not deployed
  demonstrated deployed: strictly better than the incumbent on cells that were not used to fit it (gain >= EPS_VAL and wins > losses)
  retired      removed after a leave-one-out candidate beat it, or rejected by validation
Ties and zero gain never promote. Archive reuse is NOT_IMPLEMENTED in this repair;
counts report the actual empty archive, never hypothetical retained candidates.
"""
from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass, field

import numpy as np

import r1_core as C
from r1_gates import Gate, discover_gates, refit_gates
from svc_world import realized_utility

EPS_VAL = 0.004
ARCHIVE_MAX = 3
DEPLOY_MAX_GATES = 4
CAND_PER_GEN = 12
POLICIES = ("kg", "bald", "variance", "exploit")


def seed_of(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


@dataclass
class Library:
    gates: dict = field(default_factory=dict)         # gid -> Gate (latest fit; semantics fixed by b/scope)
    deployed: C.Program | None = None
    archive: list = field(default_factory=list)
    ref_basis: np.ndarray | None = None
    policy: str = "kg"
    rank: int = 2
    records: list = field(default_factory=list)        # generation records
    calls: list = field(default_factory=list)          # invocation records
    n_candidate_evals: int = 0
    n_val_replays: int = 0
    deployed_fit: C.Fitted | None = None

    def snapshot(self):
        return {"deployed": None if self.deployed is None else {"pid": self.deployed.pid, "gates": list(self.deployed.gates), "conj": [list(c) for c in self.deployed.conj],
                                                              "status": self.deployed.status, "gen": self.deployed.gen, "parents": list(self.deployed.parents)},
                "archive": [{"pid": p.pid, "gates": list(p.gates), "status": p.status} for p in self.archive], "policy": self.policy,
                "archive_reuse_status": "NOT_IMPLEMENTED",
                "deployment_history": None if self.deployed_fit is None else self.deployed_fit.version,
                "gates": {gid: {"scope": list(g.scope), "pi": g.pi, "gen": g.gen, "sep": g.sep, "evidence_cells": list(g.evidence_cells), "parents": list(g.parents)}
                          for gid, g in self.gates.items() if self.deployed is not None and gid in self.deployed.gates}}


def make_fits(lib: Library, M: C.Models, program: C.Program | None, gate_store: dict | None = None, rank: int = 2):
    """Fitted programs for one campaign: null + unexplained + continuous latent (basis aligned to the library reference) + optional gate program."""
    fits = [C.fit_program(C.Program("N", "null"), M, {}), C.fit_program(C.Program("U", "unexplained"), M, {})]
    cf = C.fit_program(C.Program("C", "cont", k=rank), M, {}, ref_basis=lib.ref_basis)
    fits.append(cf)
    if program is not None:
        store = gate_store if gate_store is not None else lib.gates
        if lib.deployed is not None and program.pid == lib.deployed.pid:
            gf = lib.deployed_fit
            if (gf is None or gf.version != M.version or gf.program.pid != program.pid
                    or program.key() != lib.deployed.key()
                    or gf.definition_key != program.key(store)):
                raise RuntimeError("Deployment snapshot absent or stale; explicitly refit at the release boundary")
        else:
            gf = C.fit_program(program, M, store)
        if gf is not None:
            fits.append(gf)
    return fits


def run_task(world, static, cell, M, fits, policy, B, contract, mask, seed, fixed_probes=None):
    camp0 = world.campaign(cell, 1)
    z1 = M.prior.z1(camp0.Aref, camp0.amin, camp0.amax)
    pool = np.ones(static.n, bool) if mask is None else ~mask
    rng = np.random.default_rng(seed)
    camp, nom, bel, tr = C.run_campaign(world, static, cell, fits, (z1,), policy, B, contract, mask, rng, fixed_probes=fixed_probes)
    r = realized_utility(world, camp, nom, pool)
    return r, camp, nom, bel, tr


def replay(world, static, cells, M, fits, policy, B, tag):
    return np.array([run_task(world, static, c, M, fits, policy, B, "E", None, seed_of("val", tag, c))[0]["utility"] for c in cells])


def compare(u_c: np.ndarray, u_i: np.ndarray):
    d = u_c - u_i
    wins, losses = int((d > 1e-9).sum()), int((d < -1e-9).sum())
    return {"gain": float(d.mean()), "wins": wins, "losses": losses, "n": len(d)}


def promote_rule(cmp: dict) -> str:
    if cmp["gain"] >= EPS_VAL and cmp["wins"] > cmp["losses"] and cmp["wins"] >= 2:
        return "demonstrated"
    if cmp["gain"] > -EPS_VAL:
        return "noninferior"
    return "retired"


# ----------------------------------------------------------------------------- candidate generation
def _prog(gate_ids, gen, parents, conj=(), tag=""):
    p = C.Program(f"P{gen}_{seed_of(tuple(gate_ids), tuple(conj), tag) % 10**6:06d}", "gate", gates=tuple(gate_ids), conj=tuple(conj), status="provisional", parents=tuple(parents), gen=gen)
    return p


def propose(arm: str, lib: Library, Mpre: C.Models, gen: int, stream_tag: str, n_max: int):
    """Return up to n_max candidate (Program, gate_store). `arm` is 'inherit' (uses the library) or 'restart' (fresh discovery only)."""
    cands, seen = [], set()

    def add(prog, store):
        k = prog.key(store)
        if k in seen or len(prog.gates) == 0 or len(prog.gates) > DEPLOY_MAX_GATES or len(cands) >= n_max:
            return
        seen.add(k)
        cands.append((prog, store))

    def fresh(seed_tag, Gmax, min_gain, restarts, existing=()):
        rng = np.random.default_rng(seed_of(stream_tag, gen, seed_tag))
        gl = discover_gates(Mpre, gen=gen, prefix="g", rng=rng, Gmax=Gmax, restarts=restarts, min_gain=min_gain, existing=existing)
        return gl

    if arm == "inherit":
        inc = lib.deployed
        if inc is not None:
            gs = [lib.gates[g] for g in inc.gates]
            add(_prog(inc.gates, gen, inc.gates, inc.conj, "reuse"), dict(lib.gates))               # reuse / adapt (refit on Hpre inside fit_program)
            for s in range(3):                                                                           # compose: new gates on the residual of the inherited ones
                new = fresh(f"c{s}", 2, 0.08, 6, existing=gs)
                for ng in new[:2]:
                    store = dict(lib.gates)
                    store[ng.gid] = ng
                    ids = tuple(inc.gates) + (ng.gid,)
                    add(_prog(ids, gen, inc.gates, inc.conj, f"c{s}"), store)
                    if len(ids) >= 2:
                        pairs = tuple(itertools.combinations(ids[-3:], 2))
                        add(_prog(ids, gen, inc.gates, tuple(pairs), f"cj{s}"), store)
            if len(inc.gates) >= 2:                                                                      # retirement candidates: leave one gate out
                for k in range(len(inc.gates)):
                    ids = tuple(g for i, g in enumerate(inc.gates) if i != k)
                    add(_prog(ids, gen, inc.gates, tuple(c for c in inc.conj if all(x in ids for x in c)), f"lo{k}"), dict(lib.gates))
        for j, (Gm, mg, rs) in enumerate([(2, 0.12, 6), (3, 0.12, 8), (4, 0.10, 12)]):                  # fresh proposals
            gl = fresh(f"f{j}", Gm, mg, rs)
            if gl:
                store = {g.gid: g for g in gl}
                add(_prog(tuple(g.gid for g in gl), gen, (), (), f"f{j}"), store)
                if len(gl) >= 2:
                    add(_prog(tuple(g.gid for g in gl), gen, (), tuple(itertools.combinations([g.gid for g in gl][:3], 2)), f"fj{j}"), store)
    else:
        grid = [(Gm, mg, rs) for Gm in (2, 3, 4, 1) for mg in (0.12, 0.08, 0.2) for rs in (4, 8, 12)]
        j = 0
        while len(cands) < n_max and j < n_max * 3:
            Gm, mg, rs = grid[j % len(grid)]
            gl = fresh(f"r{j}", Gm, mg, rs)
            if gl:
                store = {g.gid: g for g in gl}
                ids = tuple(g.gid for g in gl)
                add(_prog(ids, gen, (), (), f"r{j}"), store)
                if len(ids) >= 2:
                    add(_prog(ids, gen, (), tuple(itertools.combinations(ids[:3], 2)), f"rj{j}"), store)
            j += 1
    return cands


# ----------------------------------------------------------------------------- one generation
def evolve(arm: str, lib: Library, world, static, stream_tag: str, gen: int, H_pre: list, val_cells: list, H_rel: list, B: int, adapt_policy: bool, n_cands: int, search: bool = True):
    """Search on H_pre, validate on val_cells (not used by any candidate fit), refit the survivor on H_rel. Mutates lib; returns the generation record."""
    if arm == "restart":                                 # nothing inherited: the raw data are kept, the library is rebuilt from empty
        lib.deployed, lib.gates, lib.ref_basis, lib.archive = None, {}, None, []
        lib.deployed_fit = None
    Mpre = C.build_models(world, H_pre, static)
    inc_prog, inc_store = lib.deployed, lib.gates
    if search:
        base_fits = make_fits(lib, Mpre, inc_prog, inc_store, lib.rank) if inc_prog is not None else make_fits(lib, Mpre, None, None, lib.rank)
        u_inc = replay(world, static, val_cells, Mpre, base_fits, lib.policy, B, f"{stream_tag}|{gen}|inc")
    else:
        u_inc = np.zeros(0)
    cands = propose(arm, lib, Mpre, gen, stream_tag, n_cands) if search else []
    lib.n_candidate_evals += len(cands)
    rec = {"gen": gen, "arm": arm, "incumbent": None if inc_prog is None else inc_prog.pid, "n_candidates": len(cands), "val_cells": list(val_cells), "incumbent_val": u_inc.tolist(), "candidates": []}
    best = None
    for prog, store in cands:
        fits = make_fits(lib, Mpre, prog, store, lib.rank)
        has_gate = any(f.program.kind == "gate" for f in fits)
        if not has_gate:
            rec["candidates"].append({"pid": prog.pid, "gates": list(prog.gates), "conj": [list(c) for c in prog.conj], "fit": False})
            continue
        u_c = replay(world, static, val_cells, Mpre, fits, lib.policy, B, f"{stream_tag}|{gen}|cand|{prog.key(store)}")
        lib.n_val_replays += len(val_cells)
        cmp = compare(u_c, u_inc)
        st = promote_rule(cmp)
        rec["candidates"].append({"pid": prog.pid, "gates": list(prog.gates), "conj": [list(c) for c in prog.conj], "fit": True, "parents": list(prog.parents), "status": st, **cmp})
        prog.status, prog.evidence = st, cmp
        if st == "demonstrated" and (best is None or (cmp["gain"], -len(prog.gates)) > (best[2]["gain"], -len(best[0].gates))):
            best = (prog, store, cmp, next(f for f in fits if f.program.kind == "gate"))
    # archive of unproven stepping stones (bounded, never deployed, never counted)
    lib.archive = [p for p in lib.archive if p.status == "noninferior"][: ARCHIVE_MAX]
    rec["archive_size_after"] = len(lib.archive)
    rec["archive_reuse_status"] = "NOT_IMPLEMENTED"
    rolled_back = None
    if best is not None:
        prog, store, cmp, candidate_fit = best
        prog.status = "demonstrated"
        if inc_prog is not None:
            inc_prog.status = "retired"
        lib.gates.update(store)
        lib.deployed = prog
        lib.deployed_fit = candidate_fit
        lib.gates.update(candidate_fit.gates)
        rec["deployed_after"] = prog.pid
        rec["deployed_cmp"] = cmp
    else:
        rec["deployed_after"] = None if inc_prog is None else inc_prog.pid
    # policy adaptation (diagnostic-policy adaptation arm): only a strict win over the incumbent policy changes it
    rec["policy_before"] = lib.policy
    if adapt_policy:
        Mfit = Mpre
        fits = make_fits(lib, Mfit, lib.deployed, lib.gates, lib.rank)
        u0 = replay(world, static, val_cells, Mfit, fits, lib.policy, B, f"{stream_tag}|{gen}|pol|{lib.policy}")
        pol_rec = {}
        bestp = None
        for pol in POLICIES:
            if pol == lib.policy:
                continue
            u = replay(world, static, val_cells, Mfit, fits, pol, B, f"{stream_tag}|{gen}|pol|{pol}")
            cmp = compare(u, u0)
            pol_rec[pol] = cmp
            if cmp["gain"] >= EPS_VAL and cmp["wins"] > cmp["losses"] and cmp["wins"] >= 2 and (bestp is None or cmp["gain"] > bestp[1]["gain"]):
                bestp = (pol, cmp)
        rec["policy_candidates"] = pol_rec
        if bestp is not None:
            lib.policy = bestp[0]
    rec["policy_after"] = lib.policy
    # refit deployed program (inherited gates adapted within scope) on everything released; keep reference basis for the continuous program
    Mrel = C.build_models(world, H_rel, static)
    cf = C.fit_program(C.Program("C", "cont", k=lib.rank), Mrel, {}, ref_basis=lib.ref_basis)
    if lib.ref_basis is None:
        lib.ref_basis = cf.V
    if lib.deployed is not None:
        gf = C.fit_program(lib.deployed, Mrel, lib.gates)
        if gf is None:
            lib.deployed.status = "retired"          # no longer supported by the released history: rolled back to the base library
            rolled_back = lib.deployed.pid
            lib.deployed = None
            lib.deployed_fit = None
        else:
            lib.deployed_fit = gf
            lib.gates.update(gf.gates)
    else:
        lib.deployed_fit = None
    rec["rolled_back_on_refit"] = rolled_back
    rec["deployed_at_checkpoint"] = None if lib.deployed is None else lib.deployed.pid        # what is actually used afterwards
    rec["library_after"] = lib.snapshot()
    lib.records.append(rec)
    return rec
