"""Read-only verification of the decoupled calibration study.

python -B verify.py            # freeze hashes (study files, imported frozen RSD and heavy-tail files, read caches, data),
                               # stage order, decision identity, reproduction of the heavy-tail records, pooled statistics
                               # and verdicts recomputed from the per-unit records in DEV_RESULT.json
python -B verify.py --replay   # also re-runs every (dose, block) unit and compares the per-unit records (about 1.5 h)

Never writes (the replay reads the existing read caches only).
"""
import datetime
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dc_run as DC  # noqa: E402

D, HD = DC.D, DC.HD
FAIL = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        FAIL.append(msg)


def load(name):
    p = HERE / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def close(a, b, tol=1e-9):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        if a == b:
            return True
        return bool((np.isnan(a) and np.isnan(b)) or abs(a - b) <= tol * max(1.0, abs(a)))
    return a == b


def rt(x):
    return json.loads(json.dumps(x, default=float))


fz = load("FREEZE.json")
check(fz is not None, "FREEZE.json present")
if fz:
    for rel, h in fz["sha256_text"].items():
        check(D.sha256_text(HERE / rel) == h, f"frozen text hash {rel}")
    for rel, h in fz["imported_frozen_sha256_text"].items():
        check(D.sha256_text(HERE.parent / rel) == h, f"imported frozen file unchanged {rel}")
    for name, own in (("heavy_tail_rsd_20261019", ("ht_core.py", "ht_data.py", "ht_run.py")),
                      ("replicate_decisions_20261019", ("rsd_core.py", "rsd_data.py", "rsd_run.py"))):
        own_fz = json.loads((HERE.parent / name / "FREEZE.json").read_text(encoding="utf-8"))
        for f in own:
            check(D.sha256_text(HERE.parent / name / f) == own_fz["sha256_text"][f], f"{name}/{f} matches its own study's freeze")
    for rel, h in fz["read_cache_sha256"].items():
        check(D.sha256(HD.CACHE / rel) == h, f"read cache unchanged {rel}")
    for rel, h in fz["data_sha256"].items():
        check(D.sha256(D.ROOT / rel) == h, f"data hash {rel}")
    check(fz["confirmatory"]["status"] == "BLOCKED_NO_AUTHORISED_UNOPENED_ARENA", "confirmatory stage recorded as blocked")

res = load("DEV_RESULT.json")
check(res is not None, "DEV_RESULT.json present")
if res and fz:
    check(res["grade"] == "DEVELOPMENT_ONLY" and res["primary"]["verdict"]["grade"] == "DEVELOPMENT_ONLY",
          "result labelled development-only")
    t_fz = datetime.datetime.fromisoformat(fz["frozen_utc"])
    t_run = datetime.datetime.fromisoformat(res["started_utc"])
    check(t_run > t_fz, f"development readout started after the freeze ({res['started_utc']} > {fz['frozen_utc']})")
    check(close(res["code_sha256"], {"dc_run.py": fz["sha256_text"]["dc_run.py"]}), "readout ran the frozen dc_run.py")
    recs = res["records"]
    doses = fz["primary_doses"] + fz["secondary_doses"]
    check(sorted((r["dose"], r["block"]) for r in recs) == sorted((d, b) for d in doses for b in fz["blocks"]),
          "one record per (dose, block)")
    for r in recs:
        comp = fz["arena_composition"].get(str(r["dose"]))
        if comp:
            c = comp[r["block"]]
            check(r["n_queries"] == c["queries"] and r["n_reference"] == c["references"],
                  f"record {r['dose']} {r['block']}: query/reference counts match the frozen composition")
        check(r["checks"]["dec_picks_equal_rsd"], f"record {r['dose']} {r['block']}: decoupled D1/D2 picks equal rsd's")
        for a in DC.DECOUPLED:
            check(r["d1"][a] == r["d1"]["rsd"] and r["d2"][a] == r["d2"]["rsd"],
                  f"record {r['dose']} {r['block']}: {a} decision outcomes identical to rsd")
    rep = DC.reproduction(recs)
    check(close(rt(rep), res["reproduction_of_heavy_tail"]), "reproduction table recomputed")
    check(len(rep) == 6 and all(v["max_abs_diff"] <= 1e-9 and v["cfg_equal"] and v["nu_equal"] and v["s_abs_diff"] <= 1e-9
                                for v in rep.values()),
          "rsd and ht_compound reproduce the frozen heavy-tail records in all 6 units (max abs diff <= 1e-9)")
    prim = [r for r in recs if r["dose"] in fz["primary_doses"]]
    sec = [r for r in recs if r["dose"] in fz["secondary_doses"]]
    agg = DC.pool(prim, fz["n_boot"], fz["seed"], fz["thresholds"])
    check(close(rt(agg), res["primary"]["aggregate"]), "primary pooled aggregate recomputed from per-unit records")
    v = DC.verdict(agg, all(r["checks"]["dec_picks_equal_rsd"] for r in prim), fz["thresholds"])
    check(close(rt(v), res["primary"]["verdict"]), "primary verdict recomputed with the frozen thresholds")
    a2 = DC.pool(sec, fz["n_boot"], fz["seed"], fz["thresholds"])
    check(close(rt(a2), res["secondary_2p5uM"]["aggregate"]), "secondary 2.5 uM aggregate recomputed")
    for d in doses:
        a = DC.pool([r for r in recs if r["dose"] == d], fz["n_boot"], fz["seed"], fz["thresholds"])
        check(close(rt(a), res["per_dose"][str(d)]), f"per-dose aggregate {d} uM recomputed")
    check(res["confirmatory"]["status"] == "BLOCKED_NO_AUTHORISED_UNOPENED_ARENA", "no confirmatory read was made")
    print(f"  overall (development-only): {v['overall']}  not met: {v['not_met']}")
    for h, x in v["hypotheses"].items():
        print(f"  {h} {x['statistic']}: {x['label']}  est {x['estimate']:+.4f}  "
              f"CI {x['ci95'][0]:+.4f}..{x['ci95'][1]:+.4f}  p_holm {x['p_holm']:.4f}")
    if "--replay" in sys.argv:
        for r in recs:
            r2 = DC.run_block(r["block"], r["dose"])
            r2.pop("seconds"); r0 = dict(r); r0.pop("seconds")
            check(close(r0, rt(r2), 1e-6), f"replay {r['dose']} {r['block']}")

print("VERIFY", "FAILED: " + str(len(FAIL)) if FAIL else "OK")
sys.exit(1 if FAIL else 0)
