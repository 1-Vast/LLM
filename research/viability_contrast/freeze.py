"""Freeze and verify the viability-contrast protocol, code and data pack.

File summary
- Path: research/viability_contrast/freeze.py
- Purpose: write-once digest record. `python -m research.viability_contrast.freeze` writes
  freeze.json with SHA-256 of protocol.json, prepare.py, qualify.py and the prepared pack
  before any qualification run; `--verify` re-checks them afterwards.
- Depends on: research/viability_contrast/{protocol.json, prepare.py}
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/viability_contrast"
PACK = ROOT / "outputs/viability_contrast_20260928/prepared"
FREEZE = ROOT / "research/viability_contrast/freeze.json"
FREEZE2 = ROOT / "research/viability_contrast/freeze2.json"
FREEZE3 = ROOT / "research/viability_contrast/freeze3.json"
FREEZE4 = ROOT / "research/viability_contrast/freeze4.json"
FREEZE5 = ROOT / "research/viability_contrast/freeze5.json"
FREEZE5B = ROOT / "research/viability_contrast/freeze5b.json"
FREEZE6 = ROOT / "research/viability_contrast/freeze6.json"
FREEZE7 = ROOT / "research/viability_contrast/freeze7.json"
FREEZE8 = ROOT / "research/viability_contrast/freeze8.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def targets(version: int = 1) -> dict:
    if version == 9:
        files = {"protocol": HERE / "protocol8.json", "run8": HERE / "run8.py",
                 "run7": HERE / "run7.py", "run6": HERE / "run6.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv"):
            files[f"pack/{name}"] = PACK / name
        return files
    if version == 8:
        files = {"protocol": HERE / "protocol7.json", "run7": HERE / "run7.py",
                 "run6": HERE / "run6.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv"):
            files[f"pack/{name}"] = PACK / name
        return files
    if version == 7:
        files = {"protocol": HERE / "protocol6.json", "run6": HERE / "run6.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv"):
            files[f"pack/{name}"] = PACK / name
        return files
    if version == 6:
        files = {"protocol": HERE / "protocol5b.json",
                 "world5b": HERE / "world5b.py", "run5b": HERE / "run5b.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv", "genetic.npz", "class_gene.json"):
            files[f"pack/{name}"] = PACK / name
        return files
    if version == 5:
        files = {"protocol": HERE / "protocol5.json", "prepare5": HERE / "prepare5.py",
                 "world5": HERE / "world5.py", "run5": HERE / "run5.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv", "genetic.npz", "class_gene.json"):
            files[f"pack/{name}"] = PACK / name
        return files
    if version == 4:
        files = {"protocol": HERE / "protocol4.json",
                 "world4": HERE / "world4.py", "run4": HERE / "run4.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv"):
            files[f"pack/{name}"] = PACK / name
        return files
    if version == 3:
        files = {"protocol": HERE / "protocol3.json", "prepare3": HERE / "prepare3.py",
                 "world3": HERE / "world3.py", "run3": HERE / "run3.py"}
        for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json",
                     "smiles.csv"):
            files[f"pack/{name}"] = PACK / name
        return files
    files = {"protocol": HERE / ("protocol2.json" if version == 2 else "protocol.json"),
             "prepare": HERE / "prepare.py",
             "qualify": HERE / ("qualify2.py" if version == 2 else "qualify.py")}
    for name in ("auc.npz", "meta.csv", "folds.json", "menu.json", "manifest.json"):
        files[f"pack/{name}"] = PACK / name
    return files


def freeze(version: int = 1) -> dict:
    target = {1: FREEZE, 2: FREEZE2, 3: FREEZE3, 4: FREEZE4, 5: FREEZE5,
              6: FREEZE5B, 7: FREEZE6, 8: FREEZE7, 9: FREEZE8}[version]
    if target.exists():
        raise SystemExit(f"{target.name} exists; refusing to overwrite a write-once record")
    notes = {
        1: ("frozen after the data pack was built and before any qualification run; "
            "seen before the freeze: the pre-freeze census counts in tmp/prism_census_probe*.json "
            "(descriptive matrix statistics, class sizes, separability descriptives)"),
        2: ("frozen after the v1 gate failed and the failure mechanism was diagnosed from "
            "registered v1 outputs (README section 3.1). A first v2 attempt crashed in the "
            "summary step (missing outcome fields) after its episode loop; no scored number "
            "was read from it, the episodes file it wrote was never opened, and the crash-fixed "
            "code is what this freeze records, before the first completed v2 run"),
        3: ("frozen after the v2 measurement showed the floor arms cannot certify any decision "
            "on this task while the clairvoyant ceiling certifies almost all (README section "
            "3.2); the dual-core estimand replaces the informative-baseline gate. A smoke run "
            "exercised every arm's code path printing shapes only, never a score"),
        4: ("frozen after the v3 measurement (README section 3.3) identified the missing core "
            "as a compound-level predictive (lambda = 0 for structure; margin-optimising "
            "destroys margin calibration). The profile channel is the registered answer. "
            "Non-profile arms are imported from the frozen v3 outputs"),
        5: ("frozen after the v4 measurement (README section 3.4) showed the kNN profile "
            "channel helps prediction (beta = 0.25 in 3/5 folds) but cannot certify, and "
            "the estimand was purified (floor 0 / realistic 0 / oracle 98.8 percent). The "
            "learned world, the non-margin acquisition rules and the gated genetic tier are "
            "the registered answers. A smoke run exercised every arm's code path printing "
            "shapes only, never a score. Non-v5 arms are imported from the frozen v3/v4 "
            "outputs"),
        6: ("frozen after an external review of the v5 measurement (README section 3.6) "
            "identified a numerical defect (diagonal-only posterior covariance in "
            "world5._predictive) and three inference weaknesses (uncalibrated precision "
            "blend; point-estimate tau screening; the oracle mixing reading and label "
            "access), all four verified against the frozen v5 code before registration. "
            "protocol5b.json registers the corrections. A synthetic smoke run exercised "
            "every arm's code path including both decomposed oracles, printing shapes "
            "only, never a score. v5 outputs are retained unchanged and imported for "
            "cross-run comparison"),
        7: ("frozen after the v5b measurement (log/20260928/VIABILITY_CONTRAST_V5B.md) "
            "retired margin-statistic qualification on the 39-class task even under "
            "perfect label-blind response prediction and carried the two-compound "
            "contrast as the next registered direction. protocol6.json unifies it with "
            "the e-process reformulation: a fixed a-priori LLR threshold, no "
            "calibration. A synthetic smoke run (tmp/smoke6.py) exercised every arm's "
            "code path including the oracle, masked, shuffled and no-winsorization "
            "variants, printing shapes only, never a score"),
        8: ("frozen after the v6 measurement (log/20261008/README.md) showed the "
            "naive Gaussian LLR is not a valid e-process on this task (conditional "
            "wrong 0.40-0.45 at threshold log(20); mechanism: heavy-tailed residuals "
            "plus cross-line correlation mean |rho| = 0.49). protocol7.json registers "
            "the three statistic families attacking exactly these mechanisms "
            "(S_huber, S_corr, S_bet). A synthetic smoke run (tmp/smoke7.py) "
            "exercised every arm's code path printing shapes only, never a score"),
        9: ("frozen after a three-agent research synthesis (statistics: LMM "
            "marginal LR with the compound random effect integrated out; "
            "conformal-risk-control literature; repository empirics: ICC 0.49, "
            "tau2 ~ 0.7, bet power insufficient at budget 48). protocol8.json "
            "registers the double layer (LMM statistic + CRC certification) and "
            "a fold-0 pilot before the global run. A synthetic smoke run "
            "(tmp/smoke8.py) exercised every arm and stopping path, shapes only"),
    }
    record = {
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": notes[version],
        "digests": {name: digest(path) for name, path in targets(version).items()},
    }
    target.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def verify(version: int = 1) -> dict:
    target = {1: FREEZE, 2: FREEZE2, 3: FREEZE3, 4: FREEZE4, 5: FREEZE5,
              6: FREEZE5B, 7: FREEZE6, 8: FREEZE7, 9: FREEZE8}[version]
    record = json.loads(target.read_text(encoding="utf-8"))
    status = {}
    ok = True
    for name, path in targets(version).items():
        if not path.exists():
            status[name] = "missing"
            ok = False
            continue
        match = digest(path) == record["digests"].get(name)
        status[name] = "ok" if match else "CHANGED"
        ok = ok and match
    return {"frozen_at": record["frozen_at"], "all_match": ok, "files": status}


if __name__ == "__main__":
    version = (9 if "--v8" in sys.argv else
               8 if "--v7" in sys.argv else
               7 if "--v6" in sys.argv else
               6 if "--v5b" in sys.argv else
               5 if "--v5" in sys.argv else
               4 if "--v4" in sys.argv else
               3 if "--v3" in sys.argv else
               2 if "--v2" in sys.argv else 1)
    if "--verify" in sys.argv:
        print(json.dumps(verify(version), indent=1))
    else:
        print(json.dumps(freeze(version), indent=1))
