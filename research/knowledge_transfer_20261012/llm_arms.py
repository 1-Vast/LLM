"""Block Q LLM arms: whole agent systems that plan the same equal-budget campaign (deepseek-flash).

Every arm keeps a persistent campaign state (library, profiled cells and their results, its own
notes from earlier rounds), plans a batch each round, has its output validated, recovers once from
an invalid reply by re-prompting with the named error, and replans after every round's results.

* ``llm_no_vc``: the agent without the virtual cell. It sees compound identities, mechanisms and
  targets, line identities, the reference atlas activity rates and its own results; unprofiled
  cells are filled by the naive rule (``campaign.naive_fill``).
* ``llm_conv_vc``: a conventional ReAct agent given the virtual cell as tools (certificates per
  cell, the line-to-line transfer table, its results) and a ``submit`` action; up to four steps
  per round. Unprofiled cells are filled by the virtual cell.
* ``maestro_llm``: MAESTRO's certificate value-of-information batch with a bounded LLM override:
  the model may swap at most 20% of the batch, each swap with a declared reason code.

Responses are cached by a sha256 of the request, so re-scoring never re-spends; spend goes to a
``SpendLedger`` with a ceiling and is reported apart from wells.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from pathlib import Path

import numpy as np

import campaign as C

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
os.environ.setdefault("MAESTRO_LOG_DIRECTORY", str(ROOT / "tmp" / "blockq_llm_logs"))

from agent.llm import DeepSeekChatClient, LLMError, MAESTROSettings  # noqa: E402
from tools.evaluation.costs import SpendLedger  # noqa: E402

LLM_ARMS = ("llm_no_vc", "llm_conv_vc", "maestro_llm")
MAX_STEPS = 4
SWAP_FRACTION = 0.2
SWAP_CODES = ("MECHANISM_PRIOR", "CERTIFICATE_DOUBT", "COVERAGE")
LINE_TISSUE = {"A375": "melanoma", "A549": "lung adenocarcinoma", "HA1E": "immortalised kidney epithelium",
               "HCC515": "lung adenocarcinoma", "HEPG2": "hepatocellular carcinoma", "HT29": "colorectal adenocarcinoma",
               "MCF7": "breast adenocarcinoma (ER+)", "PC3": "prostate adenocarcinoma (AR-)",
               "VCAP": "prostate cancer (AR+)", "HELA": "cervical adenocarcinoma", "YAPC": "pancreatic adenocarcinoma"}


class Agent:
    """deepseek-flash with a response cache and a spend ledger shared by all campaigns of a run."""

    def __init__(self, cache_path: Path, ledger_path: Path, ceiling_usd: float, offline: bool = False):
        self.cache_path = cache_path
        self.cache: dict[str, dict] = {}
        if cache_path.exists():
            for line in cache_path.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                self.cache[rec["key"]] = rec
        self.ledger = SpendLedger.load(ledger_path, ceiling_usd=ceiling_usd)
        self.offline = offline
        self.client = None if offline else DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
        self.lock = threading.Lock()

    def ask(self, label: str, messages: list[dict], max_tokens: int = 3000) -> tuple[dict | None, str]:
        """Return (object, error code); the code is "" on success."""
        key = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        with self.lock:
            if key in self.cache:
                rec = self.cache[key]
                return rec["object"], rec["error"]
        if self.offline:
            return None, "OFFLINE_CACHE_MISS"
        with self.lock:
            self.ledger.reserve(label, 0.01)
        obj, err, usage, detail = None, "", {}, ""
        try:
            obj, resp = self.client.complete_json(messages, max_tokens=max_tokens)
            usage = dict(resp.usage)
        except LLMError as e:
            err = getattr(e, "code", type(e).__name__)
            detail = str(e)[:400]
        with self.lock:
            self.ledger.charge(label, usage, status="ok" if not err else "failed", reserved_usd=0.01, note=detail)
            self.ledger.write()
            rec = {"key": key, "label": label, "object": obj, "error": err, "usage": usage}
            if not err:  # failures are not cached: a re-run asks again (and is charged again)
                self.cache[key] = rec
                with self.cache_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
        return obj, err


# ----------------------------------------------------------------------------- campaign view

def cell_ids(c: C.Campaign) -> list[str]:
    return [f"C{i + 1:02d}" for i in range(c.grid.shape[0])]


def library_table(c: C.Campaign, meta: dict, measured: np.ndarray) -> str:
    ids = cell_ids(c)
    rows = []
    for i, cid in enumerate(ids):
        open_lines = [meta["lines"][t] for t in np.flatnonzero(c.grid[i] & ~measured[i])]
        moa = "; ".join(meta["moa"][i]) or "unknown"
        tg = ", ".join(meta["targets"][i][:6]) or "unknown"
        rows.append(f"{cid} | {meta['names'][i]} | MOA: {moa} | targets: {tg} | unprofiled lines: {' '.join(open_lines) or '-'}")
    return "\n".join(rows)


def results_table(c: C.Campaign, meta: dict, measured: np.ndarray) -> str:
    ids = cell_ids(c)
    raw = np.nan_to_num(c.atlas.Yc[c.library] + c.atlas.mu[None])
    ratio = np.linalg.norm(raw, axis=2) / c.thr[None]
    out = []
    for i, t in zip(*np.nonzero(measured)):
        line = f"{ids[i]} in {meta['lines'][t]}: response/noise {ratio[i, t]:.2f} ({'RESPONSIVE' if ratio[i, t] > 1 else 'not responsive'})"
        if ratio[i, t] > 1:
            o = np.argsort(raw[i, t])
            line += f"; up {','.join(meta['genes'][j] for j in o[-3:][::-1])}; down {','.join(meta['genes'][j] for j in o[:3])}"
        out.append(line)
    return "\n".join(out) or "(nothing profiled yet)"


def certificate_table(c: C.Campaign, meta: dict, st: dict, measured: np.ndarray, rows=None) -> str:
    ids = cell_ids(c)
    out = []
    for i in (range(c.grid.shape[0]) if rows is None else rows):
        cells = []
        for t in np.flatnonzero(c.grid[i] & ~measured[i]):
            flag = " REFUSED" if st["refusal"][i, t] else ""
            cells.append(f"{meta['lines'][t]} p={st['p'][i, t]:.2f} e={st['ecos'][i, t]:.2f}{flag}")
        if cells:
            out.append(f"{ids[i]}: " + "; ".join(cells))
    return "\n".join(out)


def transfer_table(c: C.Campaign, meta: dict) -> str:
    head = "from\\to " + " ".join(f"{l:>6}" for l in meta["lines"])
    return "\n".join([head] + [f"{meta['lines'][s]:>7} " + " ".join(f"{c.kappa[s, t]:6.2f}" for t in range(c.L))
                               for s in range(c.L)])


def task_text(c: C.Campaign, meta: dict, fill: str) -> str:
    lines = ", ".join(f"{l} ({LINE_TISSUE.get(l, 'cell line')}, {100 * meta['ref_rate'][t]:.0f}% of reference compounds responsive)"
                      for t, l in enumerate(meta["lines"]))
    fill_text = {"naive": "the compound's mean profile in lines where it was profiled and responsive, otherwise the "
                          "average drug response of that line (you have no predictive model)",
                 "vc": "the virtual cell's prediction for that cell"}[fill]
    return (
        "You are the planning component of an autonomous laboratory agent. Goal: complete a compound x "
        "cell-line transcriptional response map (L1000 landmark genes, 10 uM, 24 h) for a library of "
        f"{c.grid.shape[0]} compounds never profiled before. Lines: {lines}. Each well profiles one "
        "(compound, line) cell. At the end every unprofiled cell is filled with " + fill_text + ". The score "
        "counts only cells where the compound truly changes expression beyond vehicle noise: a profiled "
        "responsive cell scores 1, an unprofiled responsive cell scores the cosine similarity between its fill "
        "and the true response, non-responsive cells do not count. Compounds that respond in one line often "
        "respond in others, and responses share a common component across compounds.")


def parse_cells(obj, key: str, ids: list[str], meta: dict, allowed: np.ndarray, rejected: list | None = None) -> tuple[list, str]:
    """Valid distinct open cells from obj[key]; each rejected item is appended to ``rejected`` with its reason."""
    rejected = [] if rejected is None else rejected
    if not isinstance(obj, dict) or not isinstance(obj.get(key), list):
        return [], f"MISSING_{key.upper()}"
    out = []
    for item in obj[key]:
        try:
            cid, line = str(item[0]).strip().upper(), str(item[1]).strip().upper()
            i, t = ids.index(cid), [l.upper() for l in meta["lines"]].index(line)
        except (ValueError, IndexError, TypeError, KeyError):
            rejected.append(f"{item}: not a [compound id, line] pair from the table")
            continue
        if (i, t) in out:
            rejected.append(f"{cid} {line}: duplicate")
        elif not allowed[i, t]:
            rejected.append(f"{cid} {line}: not an unprofiled line of this compound")
        else:
            out.append((i, t))
    return out, ("INVALID_CELLS" if rejected else "")


# ----------------------------------------------------------------------------- arms

def run_llm_arm(c: C.Campaign, arm: str, W: int, meta: dict, agent: Agent) -> dict:
    rng = np.random.default_rng(C.seed_of(c.cid, arm, W))
    n, L = c.grid.shape
    ids = cell_ids(c)
    measured = np.zeros((n, L), bool)
    batch = int(np.ceil(W / C.ROUNDS))
    notes: list[str] = []
    log = {"errors": [], "fallback_cells": 0, "steps": 0, "swaps": 0, "invalid_swaps": 0}
    fill = "naive" if arm == "llm_no_vc" else "vc"
    rounds = 0
    for r in range(C.ROUNDS):
        k = min(batch, W - int(measured.sum()))
        if k <= 0:
            break
        allowed = c.grid & ~measured
        label = f"{c.cid}:{arm}:W{W}:r{r}"
        state = (f"Round {r + 1} of {C.ROUNDS}. Wells left in the campaign: {W - int(measured.sum())}; this round "
                 f"choose exactly {k} unprofiled cells.\n\nLIBRARY\n{library_table(c, meta, measured)}\n\nRESULTS SO FAR\n"
                 f"{results_table(c, meta, measured)}\n\nYOUR NOTES FROM EARLIER ROUNDS\n{chr(10).join(notes) or '(none)'}")
        if arm == "llm_no_vc":
            picks, note = _plan_simple(agent, label, c, meta, state, k, ids, allowed, log)
        elif arm == "llm_conv_vc":
            picks, note = _plan_react(agent, label, c, meta, state, k, ids, allowed, measured, log)
        elif arm == "maestro_llm":
            picks, note = _plan_override(agent, label, c, meta, state, k, ids, allowed, measured, rng, log)
        else:
            raise ValueError(arm)
        if len(picks) < k:  # recovery of last resort: named, counted, random among open cells
            free = [tuple(x) for x in np.argwhere(allowed) if tuple(x) not in set(picks)]
            for j in rng.permutation(len(free))[: k - len(picks)]:
                picks.append(free[j])
        for i, t in picks[:k]:
            measured[i, t] = True
        notes.append(f"round {r + 1}: {note[:300]}")
        rounds += 1
    out = C.finish(c, arm, measured, rounds, fill=fill)
    out.update(log)
    return out


def _plan_simple(agent, label, c, meta, state, k, ids, allowed, log):
    msgs = [{"role": "system", "content": task_text(c, meta, "naive")},
            {"role": "user", "content": state + '\n\nReply with JSON {"picks": [["C07", "MCF7"], ...], "note": "one '
             'sentence on your strategy for later rounds"} listing exactly ' + str(k) + " distinct unprofiled cells."}]
    return _ask_cells(agent, label, msgs, "picks", k, ids, meta, allowed, log)


def _ask_cells(agent, label, msgs, key, k, ids, meta, allowed, log):
    """Ask for k cells; on a partly invalid reply keep the valid cells and ask once for the rest."""
    obj, err = agent.ask(label, msgs)
    rejected: list = []
    picks, perr = parse_cells(obj, key, ids, meta, allowed, rejected) if not err else ([], err)
    picks = picks[:k]
    if len(picks) < k:
        log["errors"].append(err or perr or f"WRONG_COUNT_{len(picks)}")
        kept = ", ".join(f"[{ids[i]}, {meta['lines'][t]}]" for i, t in picks) or "none"
        why = "; ".join(rejected[:10]) or (err or "too few cells")
        retry = msgs + [{"role": "assistant", "content": json.dumps(obj) if obj else ""},
                        {"role": "user", "content": f"Rejected: {why}. Kept: {kept}. Give exactly {k - len(picks)} more distinct "
                         f'cells, each an unprofiled [compound id, line] pair from the library table, as JSON {{"{key}": [...]}}.'}]
        obj2, err2 = agent.ask(label + ":retry", retry)
        allowed2 = allowed.copy()
        for i, t in picks:
            allowed2[i, t] = False
        more, perr2 = parse_cells(obj2, key, ids, meta, allowed2) if not err2 else ([], err2)
        if err2 or perr2 or len(more) < k - len(picks):
            log["errors"].append(err2 or perr2 or f"WRONG_COUNT_{len(more)}")
        picks += more[: k - len(picks)]
    log["fallback_cells"] += max(0, k - len(picks))
    note = str(obj.get("note", "")) if isinstance(obj, dict) else ""
    return picks, note


def _plan_react(agent, label, c, meta, state, k, ids, allowed, measured, log):
    st = c.vc_state(measured)
    tools = ("TOOLS (call one per step):\n"
             "- certificates {\"compounds\": [\"C01\", ...] or \"all\"}: for each unprofiled cell, the virtual cell's "
             "p = P(responsive) and e = expected cosine of its prediction if responsive; REFUSED means no supported "
             "specific prediction (the fill is then the line's average response).\n"
             "- transfer_table {}: how well a profile in one line predicts the specific response in another.\n"
             "- submit {\"picks\": [[\"C07\", \"MCF7\"], ...], \"note\": \"...\"}: exactly " + str(k) + " cells; ends the round.\n"
             'Reply each step with JSON {"thought": "at most two sentences", "action": "<tool>", "args": {...}}.')
    msgs = [{"role": "system", "content": task_text(c, meta, "vc")}, {"role": "user", "content": state + "\n\n" + tools}]
    kept: list = []
    for step in range(MAX_STEPS):
        log["steps"] += 1
        final = step == MAX_STEPS - 1
        if final:
            msgs.append({"role": "user", "content": f"Last step: you must now call submit with exactly {k - len(kept)} cells."})
        obj, err = agent.ask(f"{label}:s{step}", msgs, max_tokens=6000)
        if err or not isinstance(obj, dict):
            log["errors"].append(err or "NOT_AN_OBJECT")
            msgs.append({"role": "user", "content": f"Your reply was rejected ({err or 'NOT_AN_OBJECT'}). Reply with one JSON action."})
            continue
        action = str(obj.get("action", "")).strip().lower()
        action = next((a for a in ("submit", "certificates", "transfer_table") if a.split("_")[0][:7] in action), action)
        args = obj.get("args") if isinstance(obj.get("args"), dict) else {}
        msgs.append({"role": "assistant", "content": json.dumps(obj)})
        if action == "submit":
            rejected: list = []
            line_names = meta["lines"]
            open_now = allowed.copy()
            for i, t in kept:
                open_now[i, t] = False
            more, perr = parse_cells(args, "picks", ids, meta, open_now, rejected)
            kept += more[: k - len(kept)]
            if len(kept) == k:
                return kept, str(args.get("note", obj.get("thought", "")))
            log["errors"].append(perr or f"WRONG_COUNT_{len(more)}")
            if final:
                log["fallback_cells"] += k - len(kept)
                return kept, str(args.get("note", ""))
            msgs.append({"role": "user", "content": f"submit partly rejected: {'; '.join(rejected[:10]) or 'too few cells'}. "
                         f"Kept {len(kept)} cells: {', '.join(f'[{ids[i]}, {line_names[t]}]' for i, t in kept)}. "
                         f"Submit exactly {k - len(kept)} more distinct unprofiled cells."})
        elif action == "certificates":
            want = args.get("compounds", "all")
            rows = None if want == "all" or not isinstance(want, list) else [ids.index(x) for x in map(str, want) if x in ids]
            msgs.append({"role": "user", "content": "OBSERVATION\n" + certificate_table(c, meta, st, measured, rows)})
        elif action == "transfer_table":
            msgs.append({"role": "user", "content": "OBSERVATION\n" + transfer_table(c, meta)})
        else:
            log["errors"].append("UNKNOWN_ACTION")
            msgs.append({"role": "user", "content": "Unknown action. Use certificates, transfer_table or submit."})
    log["fallback_cells"] += k - len(kept)
    return kept, ""


def _plan_override(agent, label, c, meta, state, k, ids, allowed, measured, rng, log):
    st = c.vc_state(measured)
    proposal = C.maestro_batch(c, st, measured, k, rng)
    prop = [tuple(x) for x in np.argwhere(proposal)]
    v = C.maestro_value(c, st, measured)
    v[proposal] = -np.inf
    reserve = [tuple(np.unravel_index(j, v.shape)) for j in np.argsort(-v, axis=None)[: 2 * k] if np.isfinite(v.flat[j])]
    max_swaps = max(1, int(SWAP_FRACTION * k))
    fmt = lambda cells: "\n".join(f"{ids[i]} {meta['lines'][t]} ({meta['names'][i]}): p={st['p'][i, t]:.2f} "
                                  f"e={st['ecos'][i, t]:.2f} value={C.maestro_value(c, st, measured)[i, t]:.2f}" for i, t in cells)
    msgs = [{"role": "system", "content": task_text(c, meta, "vc")},
            {"role": "user", "content": state + "\n\nThe certificate planner proposes this batch (p = P(responsive), e = "
             "expected cosine of the virtual cell's fill if responsive, value = expected score gain including transfer to "
             f"the compound's other lines):\n{fmt(prop)}\n\nNext-best cells:\n{fmt(reserve)}\n\nYou may replace at most "
             f"{max_swaps} proposed cells with other unprofiled cells, each with a reason code from {list(SWAP_CODES)} "
             "(MECHANISM_PRIOR: your knowledge of the compound or line says the planner is wrong; CERTIFICATE_DOUBT: the "
             "certificate looks unreliable; COVERAGE: a line or mechanism is under-sampled). Replace nothing unless you "
             'have a specific reason. Reply with JSON {"swaps": [{"out": ["C03", "A375"], "in": ["C10", "MCF7"], '
             '"code": "...", "reason": "..."}], "note": "..."}.'}]
    obj, err = agent.ask(label, msgs)
    picks = list(prop)
    if err or not isinstance(obj, dict) or not isinstance(obj.get("swaps", []), list):
        log["errors"].append(err or "MISSING_SWAPS")
        return picks, ""
    for sw in obj.get("swaps", [])[:max_swaps]:
        try:
            o = (ids.index(str(sw["out"][0]).upper()), [l.upper() for l in meta["lines"]].index(str(sw["out"][1]).upper()))
            i = (ids.index(str(sw["in"][0]).upper()), [l.upper() for l in meta["lines"]].index(str(sw["in"][1]).upper()))
            ok = o in picks and i not in picks and allowed[i] and sw.get("code") in SWAP_CODES
        except (ValueError, KeyError, IndexError, TypeError):
            ok = False
        if ok:
            picks[picks.index(o)] = i
            log["swaps"] += 1
        else:
            log["invalid_swaps"] += 1
    return picks, str(obj.get("note", ""))
