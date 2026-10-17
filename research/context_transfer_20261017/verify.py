"""Verifier for the context-transfer study.

File summary
- Path: research/context_transfer_20261017/verify.py
- Purpose: authenticate the study's frozen bytes and recompute its reported numbers from the
  per-context records, so that every number in DEVELOPMENT.json, POWER.json and RESULTS.json
  traces to a replay record.
- Core points:
  - FREEZE.json, when present, must match every frozen file (raw or LF-normalised digest).
  - DEVELOPMENT.json and POWER.json means are recomputed from the cached development records.
  - Menu configurations: records are merged with their base run, every per-fold choice is
    recomputed from the stored inner (source-only) records, and the auto records must equal the
    chosen procedure's outer records.
  - RULE_CHOICE.json is recomputed from the cached menus, and confirm.py must use its rule.
  - RESULTS.json, when present: the records digest must match; each primary contrast's mean,
    Holm p and verdict (P1-P5) is recomputed from the records; `maestro` must equal the selected
    procedure in every context; each fold's choice must obey the frozen bridge threshold.
  - Prints one line per check and exits non-zero on any failure. Missing caches are reported as
    NOT_CHECKED by name, never as passes.
- Interfaces: `python -B verify.py`.
"""
from __future__ import annotations

import hashlib
import json
import sys

import numpy as np

from common import CACHE, HERE, ROOT, paired

FAIL = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
    if not ok:
        FAIL.append(name)


def not_checked(name, why):
    print(f"NOT_CHECKED {name} ({why})")


def digests(path):
    raw = path.read_bytes()
    return {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}


def verify_freeze():
    path = HERE / "FREEZE.json"
    if not path.exists():
        not_checked("freeze", "FREEZE.json absent: study not frozen yet")
        return
    freeze = json.loads(path.read_text(encoding="utf-8"))
    bad = [rel for rel, d in freeze["sha256"].items()
           if not (ROOT / rel).exists() or d not in digests(ROOT / rel)]
    check("freeze digests", not bad, f"{len(freeze['sha256'])} files" if not bad else f"mismatch {bad}")
    for rel in freeze.get("not_hashed", []):
        check(f"not_hashed {rel} is outside the digest map", rel not in {k.split('/')[-1] for k in freeze["sha256"]})


def verify_means(summary_file, folder):
    path = HERE / summary_file
    if not path.exists():
        not_checked(summary_file, "absent")
        return
    summ = json.loads(path.read_text(encoding="utf-8"))
    for name, s in summ.items():
        rec_path = CACHE / folder / f"{name}.json"
        if not rec_path.exists():
            not_checked(f"{summary_file}:{name}", f"records cache {rec_path.name} absent")
            continue
        data = json.loads(rec_path.read_text(encoding="utf-8"))
        recs = data["records"]
        if folder == "dev" and data.get("config", {}).get("menu"):
            base_path = CACHE / folder / f"v2_{data['config']['regime']}_w32_b8_r40.json"
            if not base_path.exists():
                not_checked(f"{summary_file}:{name}", f"base records {base_path.name} absent")
                continue
            base = {r["context"]: r for r in json.loads(base_path.read_text(encoding="utf-8"))["records"]}
            recs = [{**base[r["context"]], **r} for r in recs]
        if data.get("menu"):
            import procedure
            recs = procedure.with_rule(recs, data["menu"], "hybrid")
        key = "mean_hits" if "mean_hits" in s else "mean"
        diffs = [a for a, v in s[key].items() if abs(float(np.mean([r[a] for r in recs])) - v) > 1e-9]
        check(f"{summary_file}:{name} means", not diffs, f"{len(s[key])} arms" if not diffs else str(diffs))
        if data.get("menu"):
            verify_choices(f"{summary_file}:{name}", data["menu"], data["choices"], recs)


def verify_choices(label, menu, stored, recs):
    """Each per-fold choice is a pure function of that fold's inner (source-only) records."""

    import procedure
    for rule, ch in stored.items():
        auto, again = procedure.apply(menu, rule)
        same = all(again[int(k)]["rank"] == v["rank"] and again[int(k)]["procedure"] == v["procedure"]
                   for k, v in ch.items())
        check(f"{label} {rule} choices recomputed from inner records", same and len(again) == len(ch))
        by = {r["context"]: r for r in recs}
        diffs = sum(abs(by[c][f"auto_{rule}"] - v["auto"]) > 1e-12 for c, v in auto.items())
        check(f"{label} {rule} auto records match the chosen outer records", diffs == 0, f"{len(auto)} contexts")


def verify_rule_choice():
    """RULE_CHOICE.json is recomputed from the cached menus under the pre-declared criterion."""

    path = HERE / "RULE_CHOICE.json"
    if not path.exists():
        not_checked("rule choice", "RULE_CHOICE.json absent")
        return
    import rule_choice
    stored = json.loads(path.read_text(encoding="utf-8"))
    missing = [s for s, p in rule_choice.SETTINGS.items() if not p.exists()]
    if missing:
        not_checked("rule choice", f"menus absent {missing}")
        return
    worst = {}
    for name, p in rule_choice.SETTINGS.items():
        again = rule_choice.evaluate(json.loads(p.read_text(encoding="utf-8"))["menu"])
        same = all(abs(again["rules"][r]["hits"] - stored["settings"][name]["rules"][r]["hits"]) < 1e-12
                   for r in rule_choice.RULES) and again["best_fixed"] == stored["settings"][name]["best_fixed"]
        check(f"rule choice {name} recomputed", same)
        for r in rule_choice.RULES:
            worst[r] = max(worst.get(r, -1.0), again["rules"][r]["relative_regret"])
    low = min(worst.values())
    chosen = [r for r in rule_choice.PREFERENCE if worst[r] - low < rule_choice.TIE][0]
    check("rule choice follows the declared criterion", chosen == stored["chosen"], chosen)
    import confirm
    check("confirm.py uses the chosen rule", confirm.FROZEN["selection_rule"] == chosen)


def verify_results():
    path = HERE / "RESULTS.json"
    if not path.exists():
        not_checked("results", "RESULTS.json absent: confirmation not run")
        return
    res = json.loads(path.read_text(encoding="utf-8"))
    rec_path = CACHE / "confirm_records.json"
    if not rec_path.exists():
        not_checked("results records", "confirm_records.json absent")
        return
    check("results records digest", res["records_sha256"] in digests(rec_path))
    recs = json.loads(rec_path.read_text(encoding="utf-8"))
    groups = [r["group"] for r in recs]
    import confirm
    raw = {}
    for hid, a, b in confirm.PRIMARY:
        st = paired(np.array([r[a] - r[b] for r in recs], float), groups)
        raw[hid] = st["p_one_sided"]
        check(f"{hid} mean", abs(st["mean"] - res["primary"][hid]["mean"]) < 1e-12)
    p5 = confirm.noninferiority(recs, groups, confirm.FROZEN["noninferiority_margin"])
    raw["P5"] = p5["p_one_sided"]
    check("P5 mean and comparator", abs(p5["mean"] - res["primary"]["P5"]["mean"]) < 1e-12
          and p5["best_fixed"] == res["primary"]["P5"]["best_fixed"], p5["best_fixed"])
    adj = confirm.holm(raw)
    for hid in raw:
        st = res["primary"][hid]
        if hid == "P5":
            ok = adj[hid] < confirm.FROZEN["alpha"] and st["ci95"][0] > -confirm.FROZEN["noninferiority_margin"]
            v = "NON_INFERIOR" if ok else "NOT_SHOWN"
        else:
            v = confirm.verdict(st, adj[hid], confirm.FROZEN["alpha"], confirm.FROZEN["min_useful"])
        check(f"{hid} Holm p and verdict", abs(adj[hid] - st["p_holm"]) < 1e-12 and v == st["verdict"], v)
    procs = {int(k): v["procedure"] for k, v in res["choices"].items()}
    check("maestro equals the selected procedure in every context",
          all(r["maestro"] == r[procs[r["fold"]]] and r["maestro_procedure"] == procs[r["fold"]] for r in recs))
    for k, v in res["choices"].items():
        check(f"fold {k} choice obeys the frozen rule on its stored inner gains",
              (v["procedure"] == "vc0") == all(g["z"] <= confirm.FROZEN["z_bridge"] for g in v["bridge_gains"].values()))


if __name__ == "__main__":
    verify_freeze()
    verify_means("DEVELOPMENT.json", "dev")
    verify_means("POWER.json", "power")
    verify_rule_choice()
    verify_results()
    print("VERIFIED" if not FAIL else f"FAILED {FAIL}")
    sys.exit(1 if FAIL else 0)
