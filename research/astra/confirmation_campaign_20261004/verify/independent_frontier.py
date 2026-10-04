"""Independent P1 / P2-grid / P3 re-implementation and comparison with the resources and design records.

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/independent_frontier.py
- Purpose: extend the verify workstream's own implementation (`independent_check.py`; no design or
  resources code imported) with the contract-v2 P1 (one round, both orientations of the first M // 2
  pairs) and P3 (three-round verify-hits with the exact reserve rule), run P1, P2 at every fp of the
  grid and P3 for every predictor (and the oracle for P3) on HD (history = other HD lines) and E
  (history = all HD lines), and compare per campaign with
  - resources/results/{hd,eval}_*/campaigns_custom_p_cp20.jsonl (1, 2 and 3 rounds),
  - design/results/dev_*/campaigns_p2_grid.jsonl.gz and campaigns_p3.jsonl.gz (HD),
  - design/results/eval_*/campaigns_p3.jsonl.gz (E) and the R arm of the feedback P3 files,
  and check budget / stopping / legality invariants on the design feedback campaign files.
- Core points: P3 round 2 accepts candidate j iff (k + 1) + ceil(round(sum p_s, 12)) <= B2 with
  p_s = the role's shrunk screen-call rate, stopping at the first failure; round 3 verifies round-2
  hits only; outcomes only through `independent_check.Market`.
- Interfaces: `run_p3`, `p1_confirmed`, `main()`; writes verify/receipts/frontier_check.json.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from research.astra.confirmation_campaign_20261004.verify import independent_check as ic

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
OUT = HERE / "receipts/frontier_check.json"


def run_p3(screen_order, verify_order, p_s: np.ndarray, m: int, market: ic.Market) -> dict:
    n_r1 = (int(m) + 1) // 2
    r1 = [int(i) for i in screen_order[:n_r1]]
    rev1 = {i: market.screen(i, 1) for i in r1}
    hits1 = {i for i, h in rev1.items() if h}
    v2 = [int(i) for i in verify_order if int(i) in hits1][:max(0, m - n_r1)]
    b2 = m - n_r1 - len(v2)
    screened = set(r1)
    accepted, total = [], 0.0
    for j in screen_order:
        j = int(j)
        if j in screened:
            continue
        s = total + float(p_s[j])
        if (len(accepted) + 1) + math.ceil(round(s, 12)) <= b2:
            accepted.append(j)
            total = s
        else:
            break
    vcalls2 = [market.verify(i, 2) for i in v2]
    rev2 = {i: market.screen(i, 2) for i in accepted}
    spent = n_r1 + len(v2) + len(accepted)
    hits2 = {i for i, h in rev2.items() if h}
    v3 = [int(i) for i in verify_order if int(i) in hits2][:max(0, m - spent)]
    vcalls3 = [market.verify(i, 3) for i in v3]
    spent += len(v3)
    if spent > m:
        raise RuntimeError("CAP_EXCEEDED")
    screens = r1 + accepted
    verifies = v2 + v3
    calls = vcalls2 + vcalls3
    used = [r for r, ok in ((1, bool(r1)), (2, bool(v2 or accepted)), (3, bool(v3))) if ok]
    return {"screens": screens, "verifies": verifies, "n_r1": n_r1, "v2": len(v2), "B2": b2,
            "round2_screens": len(accepted), "confirmed": int(sum(calls)), "spent": spent,
            "screen_hits": [i for i in screens if (rev1.get(i) if i in rev1 else rev2.get(i))],
            "verify_hits": [i for i, c in zip(verifies, calls) if c], "rounds_used": len(used)}


def p1_confirmed(screen_order, joint: np.ndarray, m: int) -> dict:
    k = int(m) // 2
    first = [int(i) for i in screen_order[:k]]
    return {"screens": first, "verifies": first, "confirmed": int(joint[first].sum()) if first else 0,
            "spent": 2 * k, "n1": k}


def campaigns(rds: dict, part: dict, group: str, preds, fps) -> dict:
    out = {}
    for (tissue, role), rd in rds.items():
        e, hd = ic.line_split(rd, part)
        for t in (e if group == "E" else hd):
            rows = np.flatnonzero(rd.line == t)
            sc = ic.shrunk_scores(rd, ic.history_mask(rd, t, hd), rows)
            n = rows.size
            m = ic.cap_m(n)
            rank = ic.tie_rank(rd.tissue, int(t), role, n)
            joint = (rd.screen_hit[rows] & rd.valid_hit[rows])
            sid = rd.lines[t]
            for p in preds:
                s_sc, v_sc = (joint.astype(float), joint.astype(float)) if p == "oracle" else sc[p]
                so, vo = ic.order(s_sc, rank), ic.order(v_sc, rank)
                new = {}
                for fp in fps:
                    mk = ic.Market(rd.screen_hit[rows], rd.valid_hit[rows])
                    new[("P2", p, fp, sid, role)] = ic.run_p2(so, vo, m, ic.n_screen(fp, m), mk)
                mk = ic.Market(rd.screen_hit[rows], rd.valid_hit[rows])
                new[("P3", p, None, sid, role)] = run_p3(so, vo, sc["_p_s"][0], m, mk)
                new[("P1", p, None, sid, role)] = p1_confirmed(so, joint, m)
                for v in new.values():
                    v["M"], v["n_menu"] = m, n
                out.update(new)
    return out


def read_jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def latest(folder: Path, prefix: str) -> Path:
    return sorted(p for p in folder.iterdir() if p.is_dir() and p.name.startswith(prefix))[-1]


def compare(mine: dict, recs: list[dict], keyf, fields) -> dict:
    n, mism, missing = 0, [], 0
    for r in recs:
        key = keyf(r)
        if key is None:
            continue
        if key not in mine:
            missing += 1
            continue
        n += 1
        m = mine[key]
        for a, b, conv in fields:
            if conv(m[a]) != r[b]:
                mism.append({"campaign": [str(x) for x in key], "field": b, "verify": conv(m[a]), "other": r[b]})
    return {"compared": n, "not_in_verify": missing, "n_mismatches": len(mism), "mismatches": mism[:20]}


def main() -> int:          # pragma: no cover - needs the exposed release
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    sys.path.insert(0, str(ROOT))
    from research.astra.confirmation_campaign_20261004 import common
    from research.astra.feedback_validation_20261003 import jaaks
    from research.astra.confirmation_campaign_20261004.verify.check_design import invariants

    ticket = common.exposed_ticket("independent P1/P2-grid/P3 frontier vs resources and design records", "verify")
    panels, _, _ = jaaks.build_panels(ticket)
    part = common.partition()
    rds = {(t, r): ic.role_data(panels[f"{t}_{r}"], t, r) for t in ic.TISSUES for r in ic.ROLES}
    preds = ic.PREDICTORS + ("oracle",)
    out = {"owner": "verify", "evidence_status": "EXPLORATORY (Jaaks 2022 exposed)",
           "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "independent_check_sha256": hashlib.sha256((HERE / "independent_check.py").read_bytes()).hexdigest(),
           "access": {k: ticket.get(k) for k in ("purpose", "data_sha256", "freeze_sha256")}, "files": {}}
    mine = {}
    for group in ("HD", "E"):
        for k, v in campaigns(rds, part, group, preds, ic.FP_GRID).items():
            mine[(group,) + k] = v
    ident = lambda x: x                                       # noqa: E731
    count = len

    # resources: custom per-pair layout records at cp20 (= the contract's M)
    res = {}
    for group, prefix in (("HD", "hd_"), ("E", "eval_")):
        path = latest(STUDY / "resources/results", prefix) / "campaigns_custom_p_cp20.jsonl"
        out["files"][str(path.relative_to(ROOT)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
        recs = read_jsonl(path)
        pol = {1: "P1", 2: "P2", 3: "P3"}

        def keyf(r, group=group):
            return (group, pol[r["rounds"]], r["pred"], r["fp"] if r["rounds"] == 2 else None, r["line"], r["role"])

        res[group] = {}
        for rounds in (1, 2, 3):
            sub = [r for r in recs if r["rounds"] == rounds]
            fields = [("M", "M", ident), ("n_menu", "n_menu", ident), ("screens", "screens_ordered", ident),
                      ("verifies", "verifies_ordered", ident), ("confirmed", "confirmed", ident), ("spent", "spent", ident)]
            if rounds != 1:
                fields += [("screen_hits", "screen_hits", count), ("verify_hits", "verification_hits", count)]
            if rounds == 2:
                fields += [("n1", "n1", ident)]
            res[group][f"rounds_{rounds}"] = compare(mine, sub, keyf, fields)
            tot = defaultdict(float)
            for r in sub:
                tot[(r["pred"], r["fp"])] += r["confirmed"] / 2.0
            mt = defaultdict(float)
            for r in sub:
                mt[(r["pred"], r["fp"])] += mine[keyf(r)]["confirmed"] / 2.0 if keyf(r) in mine else float("nan")
            res[group][f"rounds_{rounds}"]["totals_resources"] = {f"{p}|{fp}": v for (p, fp), v in sorted(tot.items(), key=str)}
            res[group][f"rounds_{rounds}"]["totals_equal"] = all(mt[k] == tot[k] for k in tot)
    out["resources_vs_verify"] = res

    # design: dev P2 grid, dev P3, eval P3, feedback R arm (P3)
    dz = {}
    dev, ev = latest(STUDY / "design/results", "dev_"), latest(STUDY / "design/results", "eval_")
    fdev, fev = latest(STUDY / "design/results", "feedback_dev_"), latest(STUDY / "design/results", "feedback_eval_")
    p3_fields = [("screens", "screens", ident), ("verifies", "verifies", ident), ("confirmed", "confirmed", ident),
                 ("spent", "spent", ident), ("n_r1", "n_r1", ident), ("v2", "v2", ident), ("B2", "B2", ident),
                 ("round2_screens", "round2_screens", ident), ("rounds_used", "rounds_used", ident)]
    p2_fields = [("screens", "screens", ident), ("verifies", "verifies", ident), ("confirmed", "confirmed", ident),
                 ("spent", "spent", ident), ("n1", "n1", ident), ("rounds_used", "rounds_used", ident)]
    for name, path, group, fields, only_r in (
            ("dev_p2_grid", dev / "campaigns_p2_grid.jsonl.gz", "HD", p2_fields, False),
            ("dev_p3", dev / "campaigns_p3.jsonl.gz", "HD", p3_fields, False),
            ("eval_p3", ev / "campaigns_p3.jsonl.gz", "E", p3_fields, False),
            ("feedback_dev_R_p3", fdev / "feedback_campaigns_hd.jsonl.gz", "HD", p3_fields, True),
            ("feedback_eval_R_p3", fev / "feedback_campaigns_e.jsonl.gz", "E", p3_fields, True)):
        out["files"][str(path.relative_to(ROOT)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
        recs = read_jsonl(path)
        if only_r:
            inv = Counter(v for r in recs for v in invariants(r))
            dz[name.replace("_R_p3", "_invariants_all_arms")] = {"records": len(recs), "violations": dict(inv),
                                                                 "arms": dict(Counter(r["arm"] for r in recs))}
            recs = [r for r in recs if r["arm"] == "R"]

        def keyf(r, group=group):
            if r.get("unit", "measurement") != "measurement":
                return None
            return (group, r["policy"], r["arm"], int(r["fp"]) if r["policy"] == "P2" else None, r["line"], r["role"])

        dz[name] = compare(mine, recs, keyf, fields)
    out["design_vs_verify"] = dz

    # verify-side totals (HD and E) for the record
    tot = defaultdict(float)
    for (group, pol, p, fp, sid, role), v in mine.items():
        tot[f"{group}|{pol}|{p}|{fp}"] += v["confirmed"] / 2.0
    out["verify_totals"] = dict(sorted(tot.items()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    brief = {"resources": {g: {k: {x: v[x] for x in ("compared", "not_in_verify", "n_mismatches", "totals_equal")}
                               for k, v in d.items()} for g, d in res.items()},
             "design": {k: ({x: v[x] for x in ("compared", "not_in_verify", "n_mismatches")} if "compared" in v else v)
                        for k, v in dz.items()},
             "E_P3": {k: v for k, v in tot.items() if k.startswith("E|P3|")}}
    print(json.dumps(brief, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
