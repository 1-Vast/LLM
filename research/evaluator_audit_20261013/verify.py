"""Replay the mechanical facts behind the evaluator audit of knowledge_reality_20261013/confirm.py.

File summary
- Path: research/evaluator_audit_20261013/verify.py
- Purpose: re-derive, from frozen source files and the 24Q2 metadata, every fact README.md cites.
  Prose judgements (severity, corrections) are not machine-checked.
- Core points:
  - Source facts: each cited line of code must be present at the cited line number in the frozen
    confirm.py or develop.py.
  - Freeze: every knowledge_reality FREEZE.json digest must still match (CRLF normalised to LF),
    and no tmp/ path may be among the digests.
  - Metadata facts (skipped with a notice when tmp/ metadata is absent): REP.1M row and core counts,
    the AZ-628 screen overlap and its absence from the sealed set, and the three file digests.
  - Reads no PRISM 24Q2 response value.
- Command: `python research/evaluator_audit_20261013/verify.py` from the repository root.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = ROOT / "research/knowledge_reality_20261013"
META = ROOT / "tmp/knowledge_reality_20261013/sealed_metadata"

# (file, 1-based line, exact stripped content) for every source line README.md cites.
SOURCE_FACTS = [
    ("confirm.py", 58, "MIN_ID_MATCH = 0.9      # refuse to score if fewer requested compounds are found in the outcome matrix"),
    ("confirm.py", 292, "G19=fs[\"G\"].astype(np.float64), **{"),
    ("confirm.py", 308, "cl = pd.read_csv(ROOT / \"tmp/knowledge_reality_20261013/sealed_metadata/Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv\")"),
    ("confirm.py", 349, "G24 = np.nanmedian(read_outcomes_any(outcomes, list(sealed), panel), axis=0)"),
    ("confirm.py", 388, "G = np.nanmedian(Y, axis=0)                               # target definition: the sealed batch's generic profile"),
    ("confirm.py", 389, "S = M.residualise(Y, G)"),
    ("confirm.py", 390, "event = (D.robust_z(S) <= -3) & (Y <= -1)"),
    ("confirm.py", 391, "measured = np.isfinite(Y).sum(1) >= MIN_LINES"),
    ("confirm.py", 392, "active = measured & (event.sum(1) >= 5)"),
    ("confirm.py", 397, "r = {f\"{snap}:{arm}\": D.drug_r(P[f\"{snap}__{arm}\"][:, li].astype(np.float64), S, G) for snap in SNAPSHOTS for arm in ARMS}"),
    ("confirm.py", 432, "mt = np.isfinite(S) & measured[:, None]"),
    ("confirm.py", 451, "score = np.where(measured[c][:, None] & np.isfinite(Y[c]), score, np.nan)   # unmeasured wells cannot be nominated"),
    ("confirm.py", 463, "Gc = np.nanmedian(Yc, axis=0)"),
    ("confirm.py", 465, "act_c = (np.isfinite(Yc).sum(1) >= 50) & ((((D.robust_z(Sc) <= -3) & (Yc <= -1)).sum(1)) >= 5)"),
    ("develop.py", 294, "def drug_r(P: np.ndarray, S: np.ndarray, G: np.ndarray, lines: np.ndarray | None = None) -> np.ndarray:"),
    ("develop.py", 303, "p = P[i, f] - X @ np.linalg.lstsq(X, P[i, f], rcond=None)[0]"),
    ("develop.py", 404, "G = np.nanmedian(Y[train], axis=0)"),
]

META_DIGESTS = {
    "Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv": "13a85da9e45656c455d3911a4491f3636d7d0975a9d2333dc3d0a3e2cd3b0526",
    "Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv": "7e78f5901c1a97d2baab0789ab89832e716388da4eacaa9f094e7d2f2f5a3463",
    "Repurposing_Public_24Q2_Treatment_Meta_Data.csv": "6be6422ba804ad0775e78b457677bdf088707b9354746a03e110ae63f5eb2061",
}


def check_source(failures: list[str]) -> None:
    for name, line, expected in SOURCE_FACTS:
        lines = (STUDY / name).read_text(encoding="utf-8").split("\n")
        found = lines[line - 1].strip() if line <= len(lines) else ""
        if found != expected:
            failures.append(f"{name}:{line} differs from the cited line")


def check_freeze(failures: list[str]) -> int:
    freeze = json.loads((STUDY / "FREEZE.json").read_text(encoding="utf-8"))
    digests = freeze["sha256"]
    for relative, expected in digests.items():
        data = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != expected:
            failures.append(f"freeze digest mismatch: {relative}")
    if any(relative.startswith("tmp/") for relative in digests):
        failures.append("a tmp/ path is frozen; E6 no longer holds")
    return len(digests)


def check_metadata(failures: list[str]) -> bool:
    if not all((META / name).is_file() for name in META_DIGESTS):
        print("NOTICE: 24Q2 metadata absent from tmp/; E5 and C6 metadata facts not replayed")
        return False
    for name, expected in META_DIGESTS.items():
        if hashlib.sha256((META / name).read_bytes()).hexdigest() != expected:
            failures.append(f"metadata digest mismatch: {name}")
    with open(META / "Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rep = [r for r in rows if r["screen"] == "REP.1M"]
    cores = {r["IDs"].replace("BRD:", "")[:13] for r in rep}
    other = {r["IDs"] for r in rows if r["screen"] != "REP.1M"}
    shared = sorted({r["IDs"] for r in rep} & other)
    with open(STUDY / "sealed_compounds.csv", newline="", encoding="utf-8") as fh:
        sealed = {r["core"] for r in csv.DictReader(fh)}
    if (len(rep), len(cores)) != (1278, 1278):
        failures.append(f"REP.1M rows/cores {len(rep)}/{len(cores)}, expected 1278/1278")
    if shared != ["BRD:BRD-K05804044-001-18-5"]:
        failures.append(f"IDs shared across screens: {shared}")
    if any(s.replace("BRD:", "")[:13] in sealed for s in shared):
        failures.append("a cross-screen ID is in the sealed set")
    if len(sealed) != 1229:
        failures.append(f"sealed set has {len(sealed)} cores, expected 1229")
    with open(META / "Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv", newline="", encoding="utf-8") as fh:
        screens = {r["screen"] for r in csv.DictReader(fh)}
    if "REP1M" not in screens or "REP.1M" in screens:
        failures.append(f"cell-line screen spelling changed: {sorted(screens)}")
    return True


def main() -> int:
    failures: list[str] = []
    check_source(failures)
    n = check_freeze(failures)
    replayed = check_metadata(failures)
    if failures:
        print("AUDIT_FACTS_NOT_REPRODUCED")
        print("\n".join(failures))
        return 1
    print(f"OK: {len(SOURCE_FACTS)} cited source lines present; knowledge_reality freeze authenticates "
          f"({n} files); metadata facts {'replayed' if replayed else 'skipped'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
