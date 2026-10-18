"""Edit proposers for the per-family bets: Zero, A2 (enumerator), A2k (knowledge rule), A3 (agent), A3-blind.

File summary
- Path: research/observable_state_20261018/obs_arms.py
- Every proposer sees only `obs_core.search_stats` outputs (held-out lineage columns and the family's held-out rows are blank)
  and label-level metadata (family name, PRISM target genes, DepMap state counts). None reads a held-out cell.
- Each proposal is converted to a typed `ResearchEdit` and must pass `research_edit.validate` before it is accepted.
- Agent: deepseek-flash through `src/agent/llm.py` only; at most MAX_CALLS calls per (episode, arm); every call is logged.
- Edit record: {"family","arm","variable","sign","magnitude","p","meta"}; sign = -1 means the family is MORE sensitive
  (lower log2 fold change) when the state is on.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import obs_core as O  # noqa: E402
import research_edit as RE  # noqa: E402

MAX_CALLS = 3
N_SHORT = 12
N_ZERO = 20
BOOT = 200
SEED = 20261018


def _h(*a) -> int:
    return int(hashlib.sha256("|".join(map(str, a)).encode()).hexdigest()[:8], 16)


def to_research_edit(W, fam, rec, registered="pending-freeze") -> RE.ResearchEdit:
    sign, mag = rec["sign"], max(float(rec["magnitude"]), O.MAG_FLOOR)
    direction = "down" if sign < 0 else "up"
    return RE.ResearchEdit(
        edit_id=f"{fam}:{rec['arm']}:{rec['variable']}", primitive="interaction",
        observed_failure=f"family {fam}: search-side residual structure across state {rec['variable']}",
        competing_explanations=[{"name": "main_effects", "description": "family response independent of the state", "is_strong_simple_baseline": True},
                                {"name": "family_x_state", "description": f"family response differs by {rec['variable']}", "is_strong_simple_baseline": False}],
        virtual_cell_edit={"drug_family": fam, "state_variable": rec["variable"]},
        applicability_scope={"drugs": [fam], "contexts": ["held-out lineages"], "assay": "PRISM primary single dose log2FC"},
        discriminating_assay={"bundle": "held-out family compounds x held-out lineage lines (existing published values)", "cost": {"logical_queries": 1}},
        predicted_outcomes={"main_effects": {"quantity": "crossed_contrast", "direction": "none", "min_magnitude": 0.0},
                            "family_x_state": {"quantity": "crossed_contrast", "direction": direction, "min_magnitude": mag}},
        expected_decision_change={"nomination_change": f"family compounds nominated on lines with {rec['variable']} {'on' if sign < 0 else 'off'}",
                                  "direction_of_qualified_hits": "up"},
        rejection_condition={"quantity": "crossed_contrast", "op": ">=" if sign < 0 else "<=", "threshold": -mag if sign < 0 else mag},
        registered_before_outcome=registered, dependence_group=fam)


# ---------------------------------------------------------------- non-LLM arms
def zero_edits(W, fam, n=N_ZERO):
    adm = np.where(W.admissible)[0]
    rng = np.random.default_rng([SEED, _h(fam, "zero")])
    return [{"family": fam, "arm": "zero", "variable": W.names[int(rng.choice(adm))], "sign": int(rng.choice([-1, 1])), "magnitude": O.MAG_FLOOR, "p": 0.5, "meta": {"draw": k}}
            for k in range(n)]


def a2_edit(W, fam, stats=None):
    est, t, nF, nC, dF, dC = O.search_stats(W, fam) if stats is None else stats
    ok = np.isfinite(t)
    if not ok.any():
        return None
    v = int(np.nanargmax(np.where(ok, np.abs(t), -np.inf)))
    sign = int(np.sign(est[v])) or -1
    rng = np.random.default_rng([SEED, _h(fam, "a2boot")])
    same = 0
    for _ in range(BOOT):
        rows = rng.integers(0, len(dF), len(dF))
        e_b, t_b, *_ = O.welch(dF[rows], dC)
        if np.isfinite(t_b).any():
            vb = int(np.nanargmax(np.where(np.isfinite(t_b), np.abs(t_b), -np.inf)))
            same += int(vb == v and int(np.sign(e_b[v])) == sign)
    return {"family": fam, "arm": "a2", "variable": W.names[v], "sign": sign, "magnitude": max(O.MAG_FLOOR, 0.5 * abs(float(est[v]))),
            "p": same / BOOT, "meta": {"t": float(t[v]), "est": float(est[v])}}


def a2k_edit(W, fam):
    name_idx = {n: i for i, n in enumerate(W.names)}
    for g, _ in W.fam_targets.get(fam, [])[:3]:
        for pre in ("expr", "mut"):
            n = f"{pre}:{g}"
            if n in name_idx and W.admissible[name_idx[n]]:
                return {"family": fam, "arm": "a2k", "variable": n, "sign": -1, "magnitude": O.MAG_FLOOR, "p": 0.5, "meta": {"target": g}}
    return None


# ---------------------------------------------------------------- agent arms
SYSTEM = ("You are the Scientific Agent of MAESTRO. You propose ONE falsifiable response-state bet for a drug family from search-side "
          "evidence only. Reply with exactly one JSON object and nothing else.")


def _view(W, fam, stats, blind):
    est, t, nF, nC, *_ = stats
    ok = np.where(np.isfinite(t))[0]
    short = ok[np.argsort(-np.abs(t[ok]))][:N_SHORT]
    adm = np.where(W.admissible)[0]
    alias = {}
    if blind:
        perm = np.random.default_rng([SEED, _h(fam, "alias")]).permutation(adm)
        alias = {int(v): f"V{k:04d}" for k, v in enumerate(perm)}
    nm = (lambda v: alias[int(v)]) if blind else (lambda v: W.names[int(v)])
    rows = [{"variable": nm(v), "contrast_est_log2FC": round(float(est[v]), 3), "welch_t": round(float(t[v]), 2),
             "family_compounds": int(nF[v]), "comparator_compounds": int(nC[v])} for v in short]
    ep = W.episodes[fam]
    d = {"episode": "anonymous family" if blind else fam,
         "search_compounds": int(len(ep["S"])),
         "comparator_compounds": int(len(ep["Fp"])),
         "shortlist_by_search_side_abs_t": rows,
         "note_on_shortlist": f"{len(adm)} admissible state variables were screened; the top {N_SHORT} by |t| are shown. Large |t| values are expected by chance."}
    if not blind:
        d["family_target_genes"] = [g for g, _ in W.fam_targets.get(fam, [])[:6]]
        genes = sorted({n.split(":", 1)[1] for n in (W.names[i] for i in adm) if n.startswith("expr:")})
        muts = sorted({n.split(":", 1)[1] for n in (W.names[i] for i in adm) if n.startswith("mut:")})
        d["vocabulary"] = {"expr:<gene> (expression above panel median)": genes, "mut:<gene> (damaging or hotspot mutation)": muts}
    else:
        d["vocabulary"] = f"anonymous codes V0000..V{len(adm) - 1:04d}"
    return d, alias


def _prompt(view, attempt_note=""):
    return json.dumps({
        "task": ("Propose ONE bet: a cell-state variable z such that this drug family's response (log2 fold change, lower = more killing) "
                 "differs by z more than other families' response does. The bet is tested later on held-out compounds of this family "
                 "in held-out tissue lineages against other families' compounds. Registered sign: -1 = the family is MORE sensitive "
                 "(more negative log2FC) when z is on relative to other families; +1 = less sensitive."),
        "rules": ["variable must be exactly one name from the vocabulary", "magnitude = minimum |crossed contrast| in log2FC units you commit to (floor 0.10)",
                  "p = your probability the bet is confirmed (sign right, magnitude reached, one-sided permutation p < 0.05)",
                  "refusing is not allowed; weak evidence should show in a low p"],
        "evidence": view, "attempt_note": attempt_note,
        "respond_with": {"variable": "name", "sign": "-1 or 1", "magnitude": "number", "p": "number 0-1", "rationale": "one sentence"}}, indent=0)


def agent_edit(W, fam, client, blind=False, stats=None, log=None):
    stats = O.search_stats(W, fam) if stats is None else stats
    view, alias = _view(W, fam, stats, blind)
    inv = {a: v for v, a in alias.items()}
    name_idx = {n: i for i, n in enumerate(W.names)}
    note = ""
    for attempt in range(1, MAX_CALLS + 1):
        msg = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": _prompt(view, note)}]
        try:
            obj, resp = client.complete_json(msg, max_tokens=4000)
            var = str(obj.get("variable", "")).strip()
            v = inv.get(var) if blind else name_idx.get(var)
            if v is None or not W.admissible[v]:
                raise ValueError(f"variable {var!r} not in vocabulary")
            sign = int(float(obj.get("sign")))
            if sign not in (-1, 1):
                raise ValueError("sign must be -1 or 1")
            mag, p = float(obj.get("magnitude")), float(obj.get("p"))
            if not (0 <= p <= 1) or not np.isfinite(mag) or mag < 0:
                raise ValueError("bad magnitude or p")
            rec = {"family": fam, "arm": "a3_blind" if blind else "a3", "variable": W.names[v], "sign": sign, "magnitude": mag, "p": p,
                   "meta": {"attempt": attempt, "rationale": str(obj.get("rationale", ""))[:300]}}
            ed = to_research_edit(W, fam, rec)
            bad = RE.validate(ed)
            if bad:
                raise ValueError("; ".join(bad)[:200])
            if log is not None:
                log.append({"family": fam, "arm": rec["arm"], "attempt": attempt, "ok": True})
            return rec
        except Exception as e:  # noqa: BLE001 - a failed attempt consumes a call and is reported back
            note = f"previous attempt invalid: {type(e).__name__}: {str(e)[:150]}"
            if log is not None:
                log.append({"family": fam, "arm": "a3_blind" if blind else "a3", "attempt": attempt, "ok": False, "error": note})
    return None


def make_client():
    root = HERE.parents[1]
    sys.path.insert(0, str(root / "src"))
    from agent.llm import DeepSeekChatClient, MAESTROSettings

    return DeepSeekChatClient(MAESTROSettings.from_workspace(root))
