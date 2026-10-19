"""Read-only verification of the RSD study.

python -B verify.py            # freeze hashes, stage decisions, verdict recomputed from the written records
python -B verify.py --replay   # also re-run the evaluation block with the recorded configuration and compare headlines

Never writes into this folder. The replay reads the evaluation block again (already opened) and is runtime-sensitive in
the last digits (BLAS); estimates are compared with an absolute tolerance of 1e-6.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rsd_data as D  # noqa: E402

FAIL = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        FAIL.append(msg)


def load(name):
    p = HERE / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


fz = load("FREEZE.json")
check(fz is not None, "FREEZE.json present")
if fz:
    for rel, h in fz["sha256_text"].items():
        check(D.sha256_text(HERE / rel) == h, f"frozen text hash {rel}")
    for rel, h in fz["data_sha256"].items():
        check(D.sha256(D.ROOT / rel) == h, f"data hash {rel}")

search = load("SEARCH.json")
check(search is not None and search["decision"] == "CONTINUE_TO_FREEZE", "search headroom gate recorded as passed")
if search and fz:
    head = search["headroom"]
    check(any(head[d]["ci95"][0] > 0 for d in ("D1", "D2")), "headroom lower bound > 0 for at least one decision")
    check(all(abs(fz["practical_threshold"][d] - 0.5 * head[d]["estimate"]) < 1e-12 for d in ("D1", "D2")),
          "practical threshold = 0.5 x search raw2 - raw")

sel = load("SELECTION.json")
if sel is not None:
    c = sel["run"]["truth_T"]["contrasts"]["rsd-raw"]
    go = c["D1"]["estimate"] > 0 or c["D2"]["estimate"] > 0
    check(sel["decision"] == ("GO" if go else "STOP_SELECTION_NONPOSITIVE"), f"selection decision {sel['decision']} matches its rule")

ev = load("EVALUATION.json")
if ev is not None:
    check(sel is not None and sel["decision"] == "GO", "evaluation ran only after a GO")
    import rsd_run as R  # noqa: E402
    v = R.verdict(ev, fz["practical_threshold"])
    check(v == ev["verdict"], "verdict recomputed from contrasts and frozen thresholds")
    for d in ("D1", "D2"):
        print(f"  H1-{d}: {v[d]['label']}  est {v[d]['estimate']:+.4f}  CI {v[d]['ci95'][0]:+.4f}..{v[d]['ci95'][1]:+.4f}"
              f"  p_holm {v[d]['p_holm']:.4f}  delta {v[d]['delta']:.4f}")
    if "--replay" in sys.argv:
        r = R.run_block("evaluation", ev["cfg"], n_boot=fz["n_boot"], do_escalation=True, do_primary=True, do_sensitivity=False)
        for truth in ("truth_T", "truth_P"):
            for k, c in ev[truth]["contrasts"].items():
                if k == "identity_tier_D1":
                    continue
                for d in ("D1", "D2"):
                    a, b = c[d]["estimate"], r[truth]["contrasts"][k][d]["estimate"]
                    check(abs(a - b) < 1e-6, f"replay {truth} {k} {d}: {a:+.6f} vs {b:+.6f}")
        for k, c in ev["D3"]["contrasts"].items():
            check(abs(c["estimate"] - r["D3"]["contrasts"][k]["estimate"]) < 1e-6, f"replay D3 {k}")

print("VERIFY", "FAILED: " + str(len(FAIL)) if FAIL else "OK")
sys.exit(1 if FAIL else 0)
