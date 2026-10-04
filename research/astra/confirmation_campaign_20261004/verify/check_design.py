"""Checks of the design and resources workstreams' records and code against the independent implementation.

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/check_design.py
- Purpose: after `independent_check.py` has run (its own frozen code, no design import), compare its
  per-campaign records with the design workstream's records exactly; check budget, stopping and
  legality invariants on every design record file; compare the development table and the primary
  bootstrap; compare the resources workstream's two-round P2 records; then, with one more logged
  exposed read, (a) check that every outcome the design records say was revealed equals the builder
  panel value of the same line, role and menu row (condition identity: verification = the other
  orientation of the same pair), (b) rerun the design code (imported read-only) for R, C* and S_both
  at fp* and compare with its files (reproducibility), and (c) poison every outcome a design campaign
  did not buy (target line, the other role assignment of the target line, every other E line) and
  require identical purchases from the design code (legality).
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.check_design`;
  writes verify/receipts/design_check.json (refuses to overwrite).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
OUT = HERE / "receipts/design_check.json"
MINE = HERE / "receipts/verify_campaigns.jsonl"
MY_RECEIPT = HERE / "receipts/verification.json"
FIELDS = (("n_menu", "n_menu"), ("M", "M"), ("n1", "n1"), ("screens", "screens"), ("screen_hits", "screen_hits"),
          ("verifies", "verifies"), ("verify_hits", "verification_hits"), ("confirmed", "confirmed"),
          ("spent", "spent"), ("rounds_used", "rounds_used"))
DEADLINE = {"P2": 2, "P3": 3}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def latest(folder: Path, prefix: str) -> Path:
    cands = sorted(p for p in folder.iterdir() if p.is_dir() and p.name.startswith(prefix))
    if not cands:
        raise SystemExit(f"no {prefix}* results in {folder}")
    return cands[-1]


def invariants(rec: dict) -> list[str]:
    """Budget, stopping and legality on one design record, from its own round logs."""
    bad = []
    pol = rec.get("policy")
    deadline = DEADLINE.get(pol)
    if rec["spent"] > rec["cap"]:
        bad.append("spent>cap")
    screened_round, hit = {}, {}
    verified = set()
    for entry in rec.get("rounds", []):
        r = entry["round"]
        if deadline is not None and r > deadline:
            bad.append(f"round {r} beyond deadline")
        if deadline is not None and r == deadline and entry["screens"]:
            bad.append("screen in final round")
        rev = entry.get("reveals") or {"screens": [], "verifies": []}
        if [x[0] for x in rev["screens"]] != entry["screens"] or [x[0] for x in rev["verifies"]] != entry["verifies"]:
            bad.append("reveals differ from purchases")
        for i, _, h in rev["screens"]:
            if i in screened_round:
                bad.append("re-screen")
            screened_round[i], hit[i] = r, bool(h)
        for i, _, _ in rev["verifies"]:
            if i not in screened_round or screened_round[i] >= r:
                bad.append("verify without earlier screen")
            elif not hit[i]:
                bad.append("verify of a non-hit")
            if i in verified:
                bad.append("re-verify")
            verified.add(i)
    if sorted(screened_round) != sorted(rec["screens"]) or sorted(verified) != sorted(rec["verifies"]):
        bad.append("round logs differ from the record lists")
    if rec.get("unit", "measurement") == "measurement" and rec["spent"] != len(rec["screens"]) + len(rec["verifies"]):
        bad.append("spent != purchases")
    return bad


def main() -> int:          # pragma: no cover - needs the exposed release
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    sys.path.insert(0, str(ROOT))
    out: dict = {"owner": "verify", "evidence_status": "EXPLORATORY (Jaaks 2022 exposed)",
                 "code_sha256": sha(Path(__file__)), "independent_records_sha256": sha(MINE)}
    mine = {(r["predictor"], r["fp"], r["sidm"], r["role"]): r for r in read_jsonl(MINE)}
    myrec = json.loads(MY_RECEIPT.read_text(encoding="utf-8"))
    sel = json.loads((STUDY / "design/selection.json").read_text(encoding="utf-8"))
    fp_star, c_star = int(sel["fp_star"]), sel["C_star"]
    ev_dir = latest(STUDY / "design/results", "eval_")
    dev_dir = latest(STUDY / "design/results", "dev_")
    out["design_files"] = {}

    # 1. per-campaign comparison: design primary and own-fp records vs the independent records
    comp = {}
    for fname in ("campaigns_primary.jsonl.gz", "campaigns_own_fp.jsonl.gz"):
        path = ev_dir / fname
        out["design_files"][str(path.relative_to(ROOT)).replace("\\", "/")] = sha(path)
        recs = read_jsonl(path)
        mism, n = [], 0
        for d in recs:
            if d.get("unit", "measurement") != "measurement" or d.get("policy") != "P2":
                continue
            key = (d["arm"], int(d["fp"]), d["line"], d["role"])
            if key not in mine:
                continue
            n += 1
            m = mine[key]
            for a, b in FIELDS:
                if m[a] != d[b]:
                    mism.append({"campaign": list(key), "field": a, "verify": m[a], "design": d[b]})
        comp[fname] = {"campaigns_compared": n, "mismatches": mism[:50], "n_mismatches": len(mism),
                       "arms": dict(Counter(d["arm"] for d in recs))}
    out["per_campaign_comparison"] = comp
    prim = read_jsonl(ev_dir / "campaigns_primary.jsonl.gz")

    def total(recs, arm):
        return sum(r["confirmed"] for r in recs if r["arm"] == arm and int(r["fp"]) == fp_star) / 2.0

    out["e_totals_design"] = {a: total(prim, a) for a in sorted({r["arm"] for r in prim})}
    out["e_totals_verify"] = myrec["e_totals_at_fp_star"]
    out["e_totals_equal"] = all(out["e_totals_design"].get(a) == v for a, v in out["e_totals_verify"].items())

    # per-line confirmed counts (line value) for R and C*
    def line_vals(recs, arm, key_line, key_pred):
        acc = {}
        for r in recs:
            if r[key_pred] == arm and int(r["fp"]) == fp_star:
                acc.setdefault(r[key_line], []).append(r["confirmed"])
        return {k: sum(v) / 2.0 for k, v in acc.items() if len(v) == 2}

    lv = {}
    for arm in ("R", c_star, "S_both"):
        dv = line_vals(prim, arm, "line", "arm")
        mv = line_vals(list(mine.values()), arm, "sidm", "predictor")
        lv[arm] = {"lines": len(mv), "equal": dv == mv,
                   "differing_lines": sorted(k for k in set(dv) | set(mv) if dv.get(k) != mv.get(k))}
    out["per_line_values_equal"] = lv

    # 2. invariants on every design record file
    inv = {}
    for folder in (ev_dir, dev_dir, *sorted((STUDY / "design/results").glob("feedback_*"))):
        for path in sorted(folder.glob("campaigns_*.jsonl.gz")):
            recs = read_jsonl(path)
            out["design_files"][str(path.relative_to(ROOT)).replace("\\", "/")] = sha(path)
            viol = Counter()
            examples = []
            checked = 0
            for d in recs:
                if "rounds" not in d or "cap" not in d:
                    continue
                checked += 1
                for v in invariants(d):
                    viol[v] += 1
                    if len(examples) < 5:
                        examples.append({"arm": d.get("arm"), "line": d.get("line"), "role": d.get("role"),
                                         "policy": d.get("policy"), "violation": v})
            inv[str(path.relative_to(STUDY)).replace("\\", "/")] = {"records": len(recs), "checked": checked,
                                                                     "violations": dict(viol), "examples": examples,
                                                                     "policies": dict(Counter(d.get("policy") for d in recs))}
    out["design_record_invariants"] = inv

    # 3. development table and selection
    mine_dev = myrec["development_selection_independent"]
    dev_mism = []
    for p_, row in mine_dev["table"].items():
        for fp_, val in row.items():
            if float(sel["dev_yield"][p_][str(fp_)]) != float(val):
                dev_mism.append({"predictor": p_, "fp": fp_, "verify": val, "design": sel["dev_yield"][p_][str(fp_)]})
    out["development_table"] = {"cells_compared": sum(len(v) for v in mine_dev["table"].values()), "mismatches": dev_mism,
                                "selection_match": myrec["selection_match"]}

    # 4. primary bootstrap and verdict
    es = json.loads((ev_dir / "eval_summary.json").read_text(encoding="utf-8"))
    pr, mp = es["primary"]["result"], myrec["primary_independent"]
    out["primary_bootstrap"] = {
        "design": {"sum_R": pr["sum_x"], "sum_C": pr["sum_y"], "mean_diff": pr["mean_diff"], "mean_diff_ci": pr["mean_diff_ci"],
                   "relative": pr["relative_gain"], "relative_ci": pr["relative_gain_ci"], "verdict": es["primary"]["verdict"]["verdict"]},
        "verify": {"sum_R": mp["sum_R"], "sum_C": mp["sum_C"], "mean_diff": mp["point_absolute_per_line"],
                   "mean_diff_ci": mp["absolute_95"], "relative": mp["point_relative"], "relative_ci": mp["relative_95"],
                   "verdict": mp["verdict"]}}
    d_, v_ = out["primary_bootstrap"]["design"], out["primary_bootstrap"]["verify"]
    out["primary_bootstrap"]["equal_to_1e-12"] = bool(
        d_["sum_R"] == v_["sum_R"] and d_["sum_C"] == v_["sum_C"] and d_["verdict"] == v_["verdict"]
        and all(abs(a - b) <= 1e-12 for a, b in zip(d_["mean_diff_ci"] + d_["relative_ci"] + [d_["mean_diff"], d_["relative"]],
                                                     v_["mean_diff_ci"] + v_["relative_ci"] + [v_["mean_diff"], v_["relative"]])))
    sec = es.get("secondary_descriptive", {}).get("R_minus_S_both", {})
    out["R_minus_S_both_design"] = {k: sec.get(k) for k in ("sum_x", "sum_y", "relative_gain", "relative_gain_ci")}

    # 5. resources two-round P2 records vs design primary
    res_dir = STUDY / "resources/results"
    if res_dir.is_dir():
        rdir = latest(res_dir, "eval_")
        rpath = rdir / "campaigns_custom_p_cp20.jsonl"
        if rpath.is_file():
            out["design_files"][str(rpath.relative_to(ROOT)).replace("\\", "/")] = sha(rpath)
            rrecs = read_jsonl(rpath)
            dmap = {(d["arm"], d["line"], d["role"]): d for d in prim}
            rc = {"compared": 0, "mismatches": [], "preds": dict(Counter(r["pred"] for r in rrecs if r["rounds"] == 2))}
            tot = Counter()
            for r in rrecs:
                if r["rounds"] != 2 or r.get("fp") != fp_star:
                    continue
                d = dmap.get((r["pred"], r["line"], r["role"]))
                if d is None:
                    continue
                rc["compared"] += 1
                tot[r["pred"]] += r["confirmed"] / 2.0
                for a, b in (("screens_ordered", "screens"), ("verifies_ordered", "verifies"), ("confirmed", "confirmed"),
                             ("spent", "spent"), ("n1", "n1"), ("M", "M")):
                    if r[a] != d[b]:
                        rc["mismatches"].append({"campaign": [r["pred"], r["line"], r["role"]], "field": a})
            rc["n_mismatches"] = len(rc["mismatches"])
            rc["mismatches"] = rc["mismatches"][:20]
            rc["resources_totals_fp_star"] = dict(tot)
            out["resources_two_round_vs_design"] = rc

    # 6. one more logged exposed read: condition identity of design reveals; design-code rerun and poisoning
    from research.astra.confirmation_campaign_20261004 import common
    from research.astra.feedback_validation_20261003 import jaaks
    from research.astra.confirmation_campaign_20261004.design import campaign as cp      # read-only use

    ticket = common.exposed_ticket("check design records (reveal identity) and design code (rerun, poisoning)", "verify")
    out["second_access"] = {k: ticket.get(k) for k in ("purpose", "data_sha256", "freeze_sha256")}
    panels, _, candidates = jaaks.build_panels(ticket)
    part = common.partition()
    ident = Counter()
    for d in prim:
        sv, vs = panels[f"{d['tissue']}_SV"], panels[f"{d['tissue']}_VS"]
        mine_p = sv if d["role"] == "SV" else vs
        other = vs if d["role"] == "SV" else sv
        li = list(mine_p.library.lines).index(d["line"])
        rows = np.flatnonzero(mine_p.library.c == li)
        for entry in d["rounds"]:
            rev = entry.get("reveals") or {"screens": [], "verifies": []}
            for i, y, h in rev["screens"]:
                row = rows[i]
                ok = (float(mine_p.library.y[row]) == y and bool(mine_p.screen_hit[row]) == h)
                ident["screen_ok" if ok else "screen_bad"] += 1
            for i, y, h in rev["verifies"]:
                row = rows[i]
                ok = (float(mine_p.valid_y[row]) == y and bool(mine_p.valid_hit[row]) == h
                      and float(other.library.y[row]) == y and bool(other.screen_hit[row]) == h)
                ident["verify_ok" if ok else "verify_bad"] += 1
    out["reveal_condition_identity"] = dict(ident)

    tissues = cp.build_tissues(panels, candidates)
    arms = ("R", c_star, "S_both")
    rerun_bad, poison_bad, n = [], [], 0
    rng = np.random.default_rng(20261004)
    dmap = {(d["arm"], d["line"], d["role"]): d for d in prim}
    for t, T in tissues.items():
        HD, E = set(part[t]["HD"]), set(part[t]["E"])
        H = cp.restrict(T, HD)
        for sidm in sorted(E):
            for role in cp.ROLES:
                tg = cp.make_target(T, H, sidm, role, allowed_history=HD, forbidden=E)
                truth = cp.truth_of(T, tg)
                for arm in arms:
                    rec = cp.run_p2(tg, truth, arm, fp_star)
                    ref = dmap[(arm, sidm, role)]
                    if any(rec[k] != ref[k] for k in ("screens", "verifies", "confirmed", "spent", "n1")):
                        rerun_bad.append([arm, sidm, role])
                    # poison everything this campaign did not buy
                    P = cp.TissueData(T.tissue, T.code, T.lines, T.c, T.pid, T.pairs,
                                      {r: {k: v.copy() for k, v in a.items()} for r, a in T.arrays.items()},
                                      None, None, T.present_lines)
                    li = T.lines.index(sidm)
                    trow = np.flatnonzero(T.c == li)
                    bought_s, bought_v = set(rec["screens"]), set(rec["verifies"])
                    A = P.arrays[role]
                    for k, row in enumerate(trow):
                        if k not in bought_s:
                            A["h_s"][row] = ~A["h_s"][row]
                            A["y_s"][row] = rng.normal(0, 50)
                        if k not in bought_v:
                            A["h_v"][row] = ~A["h_v"][row]
                            A["y_v"][row] = rng.normal(0, 50)
                    other_role = "VS" if role == "SV" else "SV"
                    B = P.arrays[other_role]
                    for key in ("h_s", "h_v"):
                        B[key][trow] = rng.random(trow.size) < 0.5
                    for key in ("y_s", "y_v"):
                        B[key][trow] = rng.normal(0, 50, trow.size)
                    others = np.flatnonzero(np.isin(T.c, [T.lines.index(s) for s in E if s != sidm]))
                    for r_ in cp.ROLES:
                        for key in ("h_s", "h_v"):
                            P.arrays[r_][key][others] = rng.random(others.size) < 0.5
                        for key in ("y_s", "y_v"):
                            P.arrays[r_][key][others] = rng.normal(0, 50, others.size)
                    H2 = cp.restrict(P, HD)
                    tg2 = cp.make_target(P, H2, sidm, role, allowed_history=HD, forbidden=E)
                    rec2 = cp.run_p2(tg2, cp.truth_of(P, tg2), arm, fp_star)
                    n += 1
                    if (rec2["screens"], rec2["verifies"], rec2["confirmed"]) != (rec["screens"], rec["verifies"], rec["confirmed"]):
                        poison_bad.append([arm, sidm, role])
    out["design_code_rerun"] = {"campaigns": n, "differs_from_design_files": rerun_bad}
    out["design_code_poisoning"] = {"campaigns": n, "purchases_changed": poison_bad,
                                    "poisoned": "target line: every unpurchased screen and verification outcome of the "
                                                "campaign's role flipped / randomised; the other role assignment's rows of "
                                                "the target line randomised; every other E line randomised in both roles"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    summary = {k: out[k] for k in ("e_totals_equal", "per_line_values_equal", "development_table", "primary_bootstrap",
                                   "reveal_condition_identity", "design_code_rerun", "design_code_poisoning")}
    summary["per_campaign"] = {k: {"n": v["campaigns_compared"], "mismatches": v["n_mismatches"]} for k, v in comp.items()}
    summary["invariants"] = {k: v["violations"] for k, v in inv.items()}
    summary["resources"] = {k: v for k, v in out.get("resources_two_round_vs_design", {}).items() if k != "mismatches"}
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
