"""Read-only verification of the heavy-tail RSD study.

python -B verify.py            # freeze hashes (study, imported frozen RSD files, data), stage order, pooled statistics
                               # and verdict recomputed from the per-block records in RESULT.json
python -B verify.py --replay   # also re-runs every test (dose, block) and compares the per-block records (about 1 h)

Never writes into this folder (the replay reuses the read cache only if it already exists).
"""
import datetime
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ht_data as HD  # noqa: E402
import rsd_data as D  # noqa: E402

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


fz = load("FREEZE.json")
check(fz is not None, "FREEZE.json present")
if fz:
    for rel, h in fz["sha256_text"].items():
        check(D.sha256_text(HERE / rel) == h, f"frozen text hash {rel}")
    for rel, h in fz["rsd_frozen_sha256_text"].items():
        check(D.sha256_text(HD.RSD / rel) == h, f"imported RSD file unchanged {rel}")
    rsd_fz = json.loads((HD.RSD / "FREEZE.json").read_text(encoding="utf-8"))
    for f in ("rsd_core.py", "rsd_data.py", "rsd_run.py"):
        check(D.sha256_text(HD.RSD / f) == rsd_fz["sha256_text"][f], f"RSD {f} matches the RSD study's own freeze")
    for rel, h in fz["data_sha256"].items():
        check(D.sha256(D.ROOT / rel) == h, f"data hash {rel}")

res = load("RESULT.json")
check(res is not None, "RESULT.json present")
if res and fz:
    import ht_run as HR  # noqa: E402
    t_fz = datetime.datetime.fromisoformat(fz["frozen_utc"])
    t_open = datetime.datetime.fromisoformat(res["started_utc"])
    check(t_open > t_fz, f"test doses opened after the freeze ({res['started_utc']} > {fz['frozen_utc']})")
    for p in sorted((HERE / "cache").glob("reads_*.npz")):
        if not p.name.startswith("reads_2p5uM_"):
            mt = datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc)
            check(mt > t_fz, f"test-dose read cache {p.name} written after the freeze ({mt.isoformat(timespec='seconds')})")
    recs = res["records"]
    check(sorted((r["dose"], r["block"]) for r in recs) == sorted((d, b) for d in fz["test_doses"] for b in fz["blocks"]),
          "one record per (test dose, block)")
    for r in recs:
        comp = fz["test_arena_composition"][str(r["dose"])][r["block"]]
        check(r["n_queries"] == comp["queries"] and r["n_reference"] == comp["references"],
              f"record {r['dose']} {r['block']}: query/reference counts match the frozen metadata composition")
    agg = HR.pool(recs, fz["n_boot"], fz["seed"])
    check(close(agg, res["aggregate"]), "pooled aggregate recomputed from per-block records")
    for d in HD.TEST_DOSES:
        a = HR.pool([r for r in recs if r["dose"] == d], fz["n_boot"], fz["seed"])
        check(close(a, res["per_dose"][str(d)]), f"per-dose aggregate {d} uM recomputed")
    v = HR.verdict(agg, fz["thresholds"])
    check(close(v, res["verdict"]), "verdict recomputed with the frozen thresholds")
    print(f"  overall: {v['overall']}  not met: {v['not_met']}")
    for h, x in v["hypotheses"].items():
        print(f"  {h} {x['contrast']} {x['decision']}: {x['label']}  est {x['estimate']:+.4f}  "
              f"CI {x['ci95'][0]:+.4f}..{x['ci95'][1]:+.4f}  p_holm {x['p_holm']:.4f}")
    if "--replay" in sys.argv:
        for r in recs:
            r2 = HR.run_block(r["block"], r["dose"])
            r2.pop("seconds"); r0 = dict(r); r0.pop("seconds")
            check(close(r0, json.loads(json.dumps(r2, default=float)), 1e-6), f"replay {r['dose']} {r['block']}")

print("VERIFY", "FAILED: " + str(len(FAIL)) if FAIL else "OK")
sys.exit(1 if FAIL else 0)
