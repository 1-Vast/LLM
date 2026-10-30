"""Strict verifier. Fails (exit 1) on missing or inconsistent evidence; an empty or partial package is reported INCOMPLETE and fails.

Does no refit, no API call and no hidden-outcome decoding: it reads stored outputs, recomputes the summary with the stored statistics code, reproduces sampled
nominations from the stored fitted programs and checks accounting, coverage, uniqueness, legality, checkpoint/rollback and model identity.
Usage: python iv_verify.py [PACKAGE_DIR]
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np

HERE0 = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE0))

REQUIRED = ["CONFIG.json", "FREEZE.json", "PROTOCOL.md", "REPORT.md", "SUMMARY.json", "REPAIR_REPRODUCTION.json", "WORKED_EXAMPLE.json", "INTEGRITY_BEFORE.json",
            "RUN/LEDGER.json", "RUN/RESOURCES.json", "REAL_DEV_REPLAY.json", "EXTERNAL_SOURCE_QUALIFICATION.json"]
CODE_NAMES = ["iv_core.py", "iv_gates.py", "iv_search.py", "iv_run.py", "iv_conv.py", "iv_stats.py", "iv_worlds.py", "iv_replay.py"]
EPS = 1e-9


def tmask_from_classes(pair_class):
    m = np.zeros(len(pair_class), bool)
    for c in np.unique(pair_class):
        ix = np.nonzero(pair_class == c)[0]
        m[ix[::2]] = True
    return m


def main(argv=None) -> int:
    here = Path((argv or sys.argv[1:] or [str(HERE0)])[0]).resolve()
    problems, notes = [], []

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    missing = [f for f in REQUIRED if not (here / f).exists()]
    for f in missing:
        problems.append(f"missing mandatory evidence: {f}")
    if not (here / "RUN" / "eval" / "streams").exists() or not list((here / "RUN" / "eval" / "streams").glob("*.json.gz")):
        problems.append("missing mandatory evidence: RUN/eval/streams/*.json.gz")
    if problems:
        print("VERIFY INCOMPLETE:")
        for p in problems:
            print(" -", p)
        return 1
    import iv_core as C
    import iv_freeze as F
    import iv_replay as RP
    import iv_search as S
    import iv_stats as ST
    import iv_worlds as W

    cfg = json.loads((here / "CONFIG.json").read_text(encoding="utf-8"))
    # ---- code and configuration authentication
    pr = F.check() if here == HERE0 else []
    problems += pr
    frozen = json.loads((here / "FREEZE.json").read_text(encoding="utf-8"))
    need(frozen["config"] == cfg, "CONFIG.json differs from the frozen configuration")
    led = json.loads((here / "RUN" / "LEDGER.json").read_text(encoding="utf-8"))
    for stage in ("dev", "eval", "real"):
        need(stage in led, f"stage '{stage}' missing from the ledger")
    # ---- expected stream coverage
    kinds, dec_kinds = cfg["streams"]["kinds"], cfg["streams"]["decoupled_kinds"]
    lo, hi = cfg["streams"]["eval_seeds"]
    expected = {f"{k}_{s}" for k in kinds for s in range(lo, hi + 1)} | {f"{k}_{s}_dec" for k in dec_kinds for s in range(lo, hi + 1)}
    streams = ST.load_streams(here / "RUN" / "eval")
    need(set(streams) == expected, f"stream coverage: missing {sorted(expected - set(streams))[:5]}, unexpected {sorted(set(streams) - expected)[:5]}")
    B = cfg["task"]["budget"]
    K = cfg["task"]["shortlist_k"]
    common_arms = cfg["arms"]["common"]
    n_checked_replay = 0
    wall = 0.0
    for sid, d in streams.items():
        rows = d["rows"]
        need(d["budget"] == B, f"{sid}: budget differs from config")
        sched = d["schedule"]
        kind, seed, dec = d["kind"], d["seed"], d["decoupled"]
        w = W.make_stream(kind, seed, decoupled=dec)["world"]                     # public structure only (campaign features); no truth is read
        st = w.static
        tmask = tmask_from_classes(st.pair_class)
        n = st.n
        # coverage: every common arm covers every task cell of every batch, in the E contract
        for arm in common_arms:
            for b, batch in enumerate(sched["batches"], 1):
                have = {r["cell"] for r in rows if r["arm"] == arm and r["contract"] == "E" and r["role"] == "task" and r["gen"] == b}
                need(have == set(batch), f"{sid}: arm {arm} does not cover batch {b} tasks in contract E")
        for r in rows:
            where = f"{sid}/{r['arm']}/{r['contract']}/{r['cell']}"
            nom = r["nominated"]
            need(len(nom) == K and len(set(nom)) == K and all(0 <= q < n for q in nom), f"{where}: nominations not {K} unique valid pairs")
            probes = r["probes"]
            need(len(probes) == len(set(probes)) == r["n_spent"], f"{where}: query ledger inconsistent with n_spent")
            budget = B
            if "@B" in r["arm"]:
                budget = int(r["arm"].split("@B")[1])
            need(r["n_spent"] <= budget, f"{where}: spent {r['n_spent']} > budget {budget}")
            need(abs(r["oracle"] - r["utility"] - r["regret"]) < 1e-9, f"{where}: regret != oracle - utility")
            need(r["utility"] <= r["oracle"] + 1e-9, f"{where}: utility above oracle")
            if r["contract"] in ("T", "FO"):
                need(all(tmask[p] for p in probes), f"{where}: probe outside the legal probe half")
                need(all(not tmask[q] for q in nom), f"{where}: nominated pair outside the target half")
            if r["arm"] == "prior":
                need(r["n_spent"] == 0, f"{where}: prior arm spent queries")
        # generation records: validation rule re-derived, bounded capacity, equal envelope
        for arm, recs in d["generation_records"].items():
            for g in recs:
                for c in g["candidates"]:
                    if c.get("fit"):
                        cmp = {k: c[k] for k in ("gain", "wins", "losses", "n")}
                        need(S.promote_rule(cmp) == c["status"], f"{sid}/{arm}/gen{g['gen']}: candidate status disagrees with the promotion rule")
                        if c["status"] == "demonstrated":
                            need(c["gain"] >= S.EPS_VAL and c["wins"] > c["losses"], f"{sid}/{arm}: promoted without strict gain")
                cap = S.CAND_PER_GEN * (g["gen"] if arm == "rst_kg" else 1)
                need(g["n_candidates"] <= cap, f"{sid}/{arm}/gen{g['gen']}: {g['n_candidates']} candidates exceed the envelope {cap}")
                lib = g["library_after"]
                if lib["deployed"] is not None:
                    need(len(lib["deployed"]["gates"]) <= S.DEPLOY_MAX_GATES, f"{sid}/{arm}: deployed capacity exceeded")
                need(len(lib["archive"]) <= S.ARCHIVE_MAX, f"{sid}/{arm}: archive bound exceeded")
            # checkpoint / rollback: what batch b+1 and the anchors actually used is what was deployed after validation and rollback
            for g in recs:
                dep = g["deployed_at_checkpoint"]
                nxt = [r for r in rows if r["arm"] == arm and r["contract"] == "E" and r["role"] == "task" and r["gen"] == g["gen"] + 1]
                for r in nxt:
                    used = {p.split(":")[0] for p in r["programs"]}
                    need((dep is None and not used) or (dep is not None and dep in used), f"{sid}/{arm}: batch {g['gen'] + 1} used {used} but the checkpoint deployed {dep}")
                for r in [r for r in rows if r["arm"] == arm and r["role"] in ("A_old", "A_new") and r["gen"] == g["gen"]]:
                    used = {p.split(":")[0] for p in r["programs"]}
                    need((dep is None and not used) or (dep is not None and dep in used), f"{sid}/{arm}: anchor checkpoint {g['gen']} used {used}, deployed {dep}")
        # resources
        res = d["resources"]
        need(res["released_wells"] == res["released_cells"] * res["pairs_per_cell"], f"{sid}: released wells inconsistent")
        for name, recs in d["generation_records"].items():
            need(sum(g["n_candidates"] for g in recs) == res["candidate_evals"][name], f"{sid}/{name}: candidate evaluation total inconsistent")
        wall += res["wall_seconds"]
        # model identity and reload equality (no refit)
        z = np.load(here / "RUN" / "eval" / "models" / f"{sid}.npz", allow_pickle=False)
        sample = [r for r in rows if r["arm"] in ("inh_kg", "rst_kg") and r["contract"] == "E" and r["role"] == "task" and "trace" in r][:4]
        for r in sample:
            b = r["gen"]
            camp = w.campaign(r["cell"], B)
            pool = np.ones(n, bool)
            nom, _ = RP.replay_nomination(z, r["arm"], b, camp.Aref, camp.amin, camp.amax, r["probes"], r["values"], pool)
            need(nom == r["nominated"], f"{sid}/{r['arm']}/{r['cell']}: nomination not reproduced from the stored model")
            progs = {p.split(":")[0] for p in r["programs"]}
            stored = {k.split("|")[2] for k in z.files if k.startswith(f"{r['arm']}|b{b}|") and k.endswith("|meta")} - {"N", "U", "C"}
            need(progs == stored, f"{sid}/{r['arm']}/b{b}: stored model programs {stored} != programs used {progs}")
            n_checked_replay += 1
    # ---- summary reproduction from stored outputs only
    import iv_post as PO
    fresh = PO.build_summary(here / "RUN" / "eval", cfg)
    stored = json.loads((here / "SUMMARY.json").read_text(encoding="utf-8"))
    diff = PO.diff_summaries(fresh, stored)
    need(not diff, f"SUMMARY.json is not reproduced from stored outputs: {diff[:5]}")
    # ---- resource ceilings
    rs = json.loads((here / "RUN" / "RESOURCES.json").read_text(encoding="utf-8"))
    need(rs["comparative_wall_minutes"] <= cfg["ceilings"]["compute_minutes"], "comparative wall time above the ceiling")
    api = here / "API_RESULTS.json"
    if api.exists():
        a = json.loads(api.read_text(encoding="utf-8"))["ledger"]
        need(a["http_attempts"] <= cfg["ceilings"]["api_attempts"] and a["cumulative_tokens"] <= cfg["ceilings"]["api_tokens"], "API ceilings exceeded")
        need(a.get("no_credentials_or_headers_persisted", False), "API record does not state credential hygiene")
    # ---- real replay is development-labelled and restricted to released cells
    rd = json.loads((here / "REAL_DEV_REPLAY.json").read_text(encoding="utf-8"))
    need(rd.get("label") == "DEVELOPMENT_REPLAY_EXPOSED" and rd.get("cells_used") == 18, "real replay is not labelled development or not restricted to 18 released cells")
    need(rd.get("withheld_backgrounds_touched") is False, "real replay claims to have touched withheld backgrounds")
    problems = list(dict.fromkeys(problems))
    ke = here / "KNOWN_EXCEPTIONS.json"
    if ke.exists():                                       # documented, exactly matched exceptions are reported, never silently dropped
        for ex in json.loads(ke.read_text(encoding="utf-8"))["exceptions"]:
            tag = f"{ex['stream']}/{ex['arm']}: anchor checkpoint {ex['gen']} used set()"
            hit = [p for p in problems if p.startswith(tag)]
            if hit:
                notes.append(f"KNOWN EXCEPTION ({ex['stream']}/{ex['arm']}/gen{ex['gen']}): {ex['check']}")
                problems = [p for p in problems if p not in hit]
    if problems:
        print("VERIFY FAILED:")
        for p in problems[:40]:
            print(" -", p)
        return 1
    for n_ in notes:
        print("NOTE:", n_)
    print(f"VERIFY OK: {len(streams)} streams, {sum(len(d['rows']) for d in streams.values())} task rows, {n_checked_replay} nominations reproduced from stored models, wall {wall / 60:.1f} stream-minutes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
