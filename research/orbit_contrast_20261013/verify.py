"""Offline verification of the orbit-contrast study: interface refusals, orbit machinery, S0, freeze, claims.

File summary
- Path: research/orbit_contrast_20261013/verify.py
- Purpose: show, without reading any outcome, that the evidence interface refuses what INTERFACE.md
  says it refuses and that orbits are valid stratum partitions; replay S0 byte for byte; check the
  freeze; and check that every number README.md cites is in CLAIMS.json and recomputes from the
  result files.
- Core points:
  - Interface: MERGE_REFUSED, TRANSPORT_UNDECLARED, AVAILABLE_AFTER_QUERY, EXCLUDED_SOURCE,
    ORBIT_UNDECLARED, UNSIGNED_IN_SIGNED_ROUTE; missing evidence is `Absent` (falsy, never zero).
  - Orbits: `stratum_groups` partitions members; donors never include the member; global
    permutations stay within strata.
  - S0: `synthetic.run()` must reproduce RESULTS_S0.json exactly.
  - Freeze: `freeze.require_freeze()` when FREEZE.json exists.
  - Locks: DEVIATIONS.json D4 (run_s2.py, with run.py still at its frozen digest) and D5
    (TASK_C.md, taskc.py) record the current SHA-256 of those files.
  - Claims: `claims.build()` must reproduce CLAIMS.json, and each claim's text must appear in README.md.
  - `--replay` reruns S1 into memory and compares its headline numbers with RESULTS_S1.json.
- Command: `python research/orbit_contrast_20261013/verify.py [--replay]`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import evidence as ev  # noqa: E402
from routes import permutation_from, stratum_donors, stratum_groups  # noqa: E402


def check_interface(fail: list) -> None:
    c = ev.Entity("compound", "test", "c1")
    g = ev.Entity("gene", "symbol", "EGFR")
    p = ev.Entity("perturbation", "test", "kd:EGFR")
    store = ev.EvidenceStore()
    store.add(ev.EvidenceRecord(c, "targets", g, -1, "curated_annotation", "inhibition", None, "hub", "2020-03-24", "curated"))
    store.add(ev.EvidenceRecord(c, "targets", g, -1, "assay_measurement", "inhibition", None, "mapkg", "2026-10-08", "assay"))
    q_old = ev.Query(c, None, "x", as_of="2021-01-01")
    got = store.select(q_old, c, "targets")
    if isinstance(got, ev.Absent) or [r.source for r in got] != ["hub"]:
        fail.append("snapshot rule did not drop a later record")
    try:
        store.select(q_old, c, "targets", strict=True)
        fail.append("AVAILABLE_AFTER_QUERY not raised")
    except ev.EvidenceRefused as e:
        if e.code != "AVAILABLE_AFTER_QUERY":
            fail.append(f"wrong refusal {e.code}")
    try:
        store.select(ev.Query(c, None, "x", excluded_sources=frozenset({"hub"})), c, "targets", strict=True)
        fail.append("EXCLUDED_SOURCE not raised")
    except ev.EvidenceRefused as e:
        if e.code != "EXCLUDED_SOURCE":
            fail.append(f"wrong refusal {e.code}")
    missing = store.select(q_old, g, "targets")
    if not isinstance(missing, ev.Absent) or bool(missing):
        fail.append("missing evidence is not Absent/falsy")
    obs = ev.EvidenceRecord(p, "response", None, 0, "observational_association", None, "A375", "s1", "2017-01-01", "assay")
    kd = ev.EvidenceRecord(p, "response", None, 0, "interventional_response", "genetic_knockdown", "A375", "s2", "2017-01-01", "assay")
    ko = ev.EvidenceRecord(p, "response", None, 0, "interventional_response", "genetic_knockout", "A375", "s3", "2017-01-01", "assay")
    for pair, label in (((obs, kd), "observational+interventional"), ((kd, ko), "knockdown+knockout")):
        try:
            ev.check_poolable(pair)
            fail.append(f"MERGE_REFUSED not raised for {label}")
        except ev.EvidenceRefused as e:
            if e.code != "MERGE_REFUSED":
                fail.append(f"wrong refusal {e.code}")
    try:
        ev.transport(kd, "efficacy", 1)
        fail.append("TRANSPORT_UNDECLARED not raised")
    except ev.EvidenceRefused as e:
        if e.code != "TRANSPORT_UNDECLARED":
            fail.append(f"wrong refusal {e.code}")
    t = ev.transport(kd, "inhibition", 1)
    if t.observation != "transported" or "knockdown_as_inhibition_proxy" not in t.provenance:
        fail.append("transport lost its provenance")
    try:
        ev.require_orbit("genetic", {})
        fail.append("ORBIT_UNDECLARED not raised")
    except ev.EvidenceRefused as e:
        if e.code != "ORBIT_UNDECLARED":
            fail.append(f"wrong refusal {e.code}")
    unsigned = ev.EvidenceRecord(c, "targets", g, 0, "assay_measurement", "binding", None, "mapkg", "2026-10-08", "assay")
    try:
        ev.require_signed(unsigned)
        fail.append("UNSIGNED_IN_SIGNED_ROUTE not raised")
    except ev.EvidenceRefused as e:
        if e.code != "UNSIGNED_IN_SIGNED_ROUTE":
            fail.append(f"wrong refusal {e.code}")


def check_orbits(fail: list) -> None:
    rng = np.random.default_rng(0)
    keys = np.stack([rng.integers(0, 3, 200), rng.integers(0, 6, 200)], 1)
    members = np.flatnonzero(rng.random(200) < 0.8)
    groups = stratum_groups(keys, members, 5, fallbacks=[(0,)])
    flat = np.sort(np.concatenate(groups))
    if not np.array_equal(flat, np.sort(members)):
        fail.append("stratum_groups is not a partition of the members")
    if sum(len(g) < 5 for g in groups) > 1:
        fail.append("more than one undersized stratum")
    donors = stratum_donors(keys, members, 5, fallbacks=[(0,)])
    if any(i in d for i, d in donors.items()):
        fail.append("a member donates to itself")
    perm = permutation_from(donors, 200, np.random.default_rng(1))
    gid = {int(i): k for k, g in enumerate(groups) for i in g}
    if any(gid[int(i)] != gid[int(perm[i])] for i in members):
        fail.append("global permutation leaves its stratum")
    if any(perm[i] != i for i in set(range(200)) - set(members.tolist())):
        fail.append("global permutation moves a non-member")


def check_s0(fail: list) -> None:
    import synthetic
    from run import jsonable
    saved = json.loads((HERE / "RESULTS_S0.json").read_text(encoding="utf-8"))
    now = json.loads(json.dumps(jsonable(synthetic.run())))
    if now != saved:
        fail.append("S0 does not reproduce RESULTS_S0.json")


def check_freeze(fail: list) -> str:
    if not (HERE / "FREEZE.json").is_file():
        return "no FREEZE.json yet"
    import freeze
    try:
        f = freeze.require_freeze()
    except SystemExit as e:
        fail.append(str(e))
        return "mismatch"
    return f"{len(f['sha256'])} files authenticate"


def check_locks(fail: list) -> str:
    dev = {d["id"]: d for d in json.loads((HERE / "DEVIATIONS.json").read_text(encoding="utf-8"))["deviations"]}
    if "D4" not in dev:
        return "no D4/D5 yet"
    import freeze
    sha = lambda n: freeze.digest(HERE / n)  # noqa: E731
    frozen = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))["sha256"]
    if dev["D4"]["run_s2_py_sha256"] != sha("run_s2.py"):
        fail.append("run_s2.py differs from the digest recorded in D4")
    if dev["D4"]["run_py_sha256_frozen"] != frozen[f"{freeze.STUDY}/run.py"]:
        fail.append("D4 run.py digest is not the frozen one")
    if "D5" in dev and dev["D5"]["sha256"] != {n: sha(n) for n in ("TASK_C.md", "taskc.py")}:
        fail.append("TASK_C.md or taskc.py differs from the digests recorded in D5")
    return "D4" + ("/D5" if "D5" in dev else "") + " digests match"


def check_claims(fail: list) -> str:
    if not (HERE / "CLAIMS.json").is_file():
        return "no CLAIMS.json yet"
    import claims
    saved = json.loads((HERE / "CLAIMS.json").read_text(encoding="utf-8"))
    now = json.loads(json.dumps(claims.build(), ensure_ascii=False))
    if now != saved:
        fail.append("CLAIMS.json does not recompute from the result files")
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    missing = [c["id"] for c in saved["claims"] if c["text"] not in readme]
    if missing:
        fail.append("README.md lacks claims: " + ", ".join(missing))
    return f"{len(saved['claims'])} claims recompute and appear in README.md"


def replay_s1(fail: list) -> None:
    import run
    out = run.stage([0], "S1 development (replay)", controls=False, n_relabel=1)
    out.update(run.gates_s1(out))
    saved = json.loads((HERE / "RESULTS_S1.json").read_text(encoding="utf-8"))
    now = json.loads(json.dumps(run.jsonable(out)))
    for task, pop in (("A", "primary_active"), ("B_full", "primary_all"), ("B_nontrivial", "primary_all")):
        a, b = saved[task][pop]["arms"], now[task][pop]["arms"]
        if any(abs(a[k] - b[k]) > 1e-9 for k in a):
            fail.append(f"S1 replay differs: {task}/{pop}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()
    fail: list = []
    check_interface(fail)
    check_orbits(fail)
    check_s0(fail)
    fz = check_freeze(fail)
    lk = check_locks(fail)
    cl = check_claims(fail)
    if args.replay:
        replay_s1(fail)
    if fail:
        print("VERIFY_FAILED")
        print("\n".join(fail))
        return 1
    print(f"OK: interface refusals, orbit partitions, S0 replay; freeze: {fz}; locks: {lk}; claims: {cl}"
          + ("; S1 replay identical" if args.replay else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
