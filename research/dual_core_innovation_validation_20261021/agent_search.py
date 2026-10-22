"""Bounded program search on DEVELOPMENT evidence only (dev + sel backgrounds; final outcomes are never read here).
Arms: A0 static fixed procedure | A1 inherited LLM chain (3 generations, tasks T1 dev/W1 -> T2 dev+sel/W1 -> T3 dev+sel/W0+W1) |
A2 restart (3 independent LLM requests from A0 on the T3 evidence, no inherited program) | Aconv conventional menu optimiser (8 candidates, no LLM).
Acceptance for every arm: strictly greater mean validation yield than the incumbent, plus source check and identity audit.  Ties are rejected.
usage: python agent_search.py {conv|a1|a2}"""
from __future__ import annotations
import hashlib, json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from sklearn.metrics import roc_auc_score
import agent_data as AD, ptv_env as ENV, ptv_audit as AU, agent_llm as LLM

HERE = Path(__file__).parent
OUT = HERE / "RUN" / "programs"; OUT.mkdir(parents=True, exist_ok=True)

A0_SRC = '''def run(env):
    drugs = list(env.drugs)
    order = sorted(drugs, key=lambda d: (-env.W[d], d))
    for d in order:
        if env.left() < 1.0:
            break
        env.query_f(d)
'''
MENU_T = '''def run(env):
    kappa = {kappa}
    beta = {beta}
    drugs = list(env.drugs)
    adj = {{d: 0.0 for d in drugs}}
    done = {{}}
{mol}    while env.left() >= 1.0 and len(done) < len(drugs):
        best = None
        bs = -1e9
        for d in drugs:
            if d in done:
                continue
            s = (1.0 - beta) * env.W[d] + beta * env.prior[d] + adj[d]
            if s > bs:
                bs = s
                best = d
        y = env.query_f(best)
        done[best] = y
        resid = y - env.W[best]
        for d in drugs:
            if d not in done:
                w = env.sim(d, best)
                if w > 0:
                    adj[d] = adj[d] + kappa * w * w * resid
'''
MOL_BLOCK = '''    top = sorted(drugs, key=lambda d: (-env.W[d], d))[:2]
    for d in top:
        m = env.query_m(d)
        adj[d] = adj[d] + 0.5 * (m['score'] - env.W[d])
'''


def menu():
    c = []
    for kappa in (0.0, 1.0):
        for beta in (0.0, 0.5, 1.0):
            c.append(MENU_T.format(kappa=kappa, beta=beta, mol=""))
    for beta in (0.0, 0.5):
        c.append(MENU_T.format(kappa=0.0, beta=beta, mol=MOL_BLOCK))
    return c


def evaluate(src, eps):
    ENV.check_source(src)
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda e: ENV.run_program(src, e["kwargs"]), eps))
    return res


def mean_yield(src, eps):
    r = evaluate(src, eps)
    bad = [x["error"] for x in r if str(x.get("error", "")).startswith("runner")]
    if bad:
        raise RuntimeError(f"runner fault in {len(bad)} episode(s): {bad[0]}")
    return float(np.mean([x["yield"] for x in r])), r


def sets():
    d, s = AD.load("dev", "m1"), AD.load("sel", "m1")
    return {"T1": d["W1"], "T2": d["W1"] + s["W1"], "T3": d["W1"] + s["W1"] + d["W0"] + s["W0"]}, d, s


def evidence(src, eps, names):
    lines = []
    for e, nm in zip(eps, names):
        k = e["kwargs"]; ds = k["drugs"]; y = np.array([k["labels"][d] for d in ds])
        def au(f):
            return round(float(roc_auc_score(y, [f(d) for d in ds])), 2) if len(set(y)) > 1 else None
        r = ENV.run_program(src, k)
        order = sorted(ds, key=lambda d: (-k["W"][d], d))
        rank = {d: i for i, d in enumerate(order)}
        mol_au = au(lambda d: k["mol"][d]["score"]) if all(d in k["mol"] for d in ds) else None
        lines.append(f"{nm}: n={len(ds)} pos={int(y.sum())} AUROC(W)={au(lambda d: k['W'][d])} prior={au(lambda d: k['prior'][d])} nn={au(lambda d: k['nn'][d])} mol={mol_au}; "
                     f"incumbent yield={r['yield']} queried(rank_by_W,label)={[(rank[t[1]], t[2]) for t in r['trace'] if t[0]=='f']}; "
                     f"labels in W-rank order (first 12)={[int(k['labels'][d]) for d in order[:12]]}")
    return "\n".join(lines)


def accept(cand_src, incumbent_src, val_eps, log, tag):
    rec = {"tag": tag}
    try:
        ENV.check_source(cand_src)
    except Exception as e:
        rec.update(accepted=False, reason=f"source check: {e}"); log.append(rec); return False
    a = AU.audit_program(cand_src); rec["audit"] = a
    rec["structure_changed_vs_incumbent"] = AU.structure_signature(cand_src) != AU.structure_signature(incumbent_src)
    yi, ri = mean_yield(incumbent_src, val_eps); yc, rc = mean_yield(cand_src, val_eps)
    rec["runner_faults"] = sum(str(x.get("error", "")).startswith("runner") for x in ri + rc)
    rec.update(val_yield_candidate=yc, val_yield_incumbent=yi, errors=[x.get("error") for x in rc if x.get("error")])
    ok = yc > yi + 1e-9 and rec["structure_changed_vs_incumbent"] and not a["embedded_data_suspected"] and not rec["errors"] and rec["runner_faults"] == 0
    rec["accepted"] = bool(ok); log.append(rec); return ok


def main(arm):
    S, dev, sel = sets()
    names = {"T1": [e["cell"] for e in dev["W1"]], "T2": [e["cell"] for e in dev["W1"] + sel["W1"]],
             "T3": [e["cell"] + "/W1" for e in dev["W1"] + sel["W1"]] + [e["cell"] + "/W0" for e in dev["W0"] + sel["W0"]]}
    log = []; budget = LLM.Budget()
    if arm == "conv":
        best, by = A0_SRC, mean_yield(A0_SRC, S["T3"])[0]
        for i, c in enumerate(menu()):
            y = mean_yield(c, S["T3"])[0]
            log.append({"candidate": i, "val_yield": y, "audit": AU.audit_program(c)})
            if y > by + 1e-9:
                best, by = c, y
        (OUT / "Aconv.py").write_text(best); json.dump({"a0_val": mean_yield(A0_SRC, S["T3"])[0], "chosen_val": by, "log": log}, open(OUT / "Aconv_log.json", "w"), indent=1)
        print("conv", by, mean_yield(A0_SRC, S["T3"])[0]); return
    if arm == "a1":
        inc = A0_SRC
        for g, T in enumerate(("T1", "T2", "T3"), 1):
            cf = OUT / f"A1_g{g}_candidate.py"
            if cf.exists():       # resume after an infrastructure fault: reuse the recorded candidate, no new request
                src, rec = cf.read_text(), {"tag": f"A1_g{g}", "outcome": "REUSED_RECORDED_CANDIDATE"}
            else:
                src, rec = LLM.propose(f"A1_g{g}", evidence(inc, S[T], names[T]), inc, budget)
            entry = {"generation": g, "task": T, "request": rec}
            if src is not None:
                (OUT / f"A1_g{g}_candidate.py").write_text(src)
                ok = accept(src, inc, S[T], log, f"A1_g{g}")
                entry["accepted"] = ok
                if ok: inc = src
            (OUT / f"A1_g{g}_incumbent.py").write_text(inc)
            log.append(entry)
        (OUT / "A1.py").write_text(inc); json.dump(log, open(OUT / "A1_log.json", "w"), indent=1); return
    if arm == "a2":
        cands = []
        for r in range(3):
            cf = OUT / f"A2_r{r+1}_candidate.py"
            if cf.exists():
                src, rec = cf.read_text(), {"tag": f"A2_r{r+1}", "outcome": "REUSED_RECORDED_CANDIDATE"}
            else:
                src, rec = LLM.propose(f"A2_r{r+1}", evidence(A0_SRC, S["T3"], names["T3"]), A0_SRC, budget)
            log.append({"request": rec})
            if src is not None:
                (OUT / f"A2_r{r+1}_candidate.py").write_text(src); cands.append(src)
        best = A0_SRC
        by = mean_yield(A0_SRC, S["T3"])[0]
        for i, c in enumerate(cands):
            tmp = []
            ok = accept(c, A0_SRC, S["T3"], tmp, f"A2_r{i+1}"); log += tmp
            if ok and tmp[0]["val_yield_candidate"] > by + 1e-9:
                best, by = c, tmp[0]["val_yield_candidate"]
        (OUT / "A2.py").write_text(best); json.dump(log, open(OUT / "A2_log.json", "w"), indent=1); return


if __name__ == "__main__":
    main(sys.argv[1])
