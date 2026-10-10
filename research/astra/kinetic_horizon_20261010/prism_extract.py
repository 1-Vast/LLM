"""Sealed PRISM 19Q4 extraction: parse only the rows of an allowed tier.

Tiers come from SPLIT.json. ``development`` is always allowed. ``confirmation`` and ``heldout``
are refused (``TIER_SEALED``) until FREEZE.json exists and ``--allow-sealed`` is given. Row
filtering happens inside ``read_csv`` (``skiprows``), so values of other tiers are never parsed.

Outputs data/external/kinetic_horizon_20261010/prism_<tier>.npz with lines x Tahoe-drug arrays:
* primary_2p5   PRISM primary (HTS, 5 days) log2 fold change at 2.5 uM;
* secondary_2p5 PRISM secondary (MTS010 preferred over HTS002) log2 fold change nearest 2.5 uM;
* secondary_mean mean secondary log2 fold change over the 8-dose series (>= 6 doses required).
Several broad_ids for one drug (salts, re-supplies) are averaged. A receipt JSON records hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "data/external/prism_19q4/raw"
OUT = ROOT / "data/external/kinetic_horizon_20261010"
FILES = {
    "primary": RAW / "primary-screen-replicate-collapsed-logfold-change.csv",
    "secondary": RAW / "secondary-screen-replicate-collapsed-logfold-change.csv",
}
COL = re.compile(r"^(BRD-[A-Z0-9-]+)::([0-9.eE-]+)::(\w+)$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def tier_files(split: dict, tier: str) -> list:
    return split["development"] if tier == "development" else split["confirmation"] if tier == "confirmation" else split["heldout_zeroshot"]


def read_rows(path: Path, depmap_ids: list) -> pd.DataFrame:
    ids = pd.read_csv(path, usecols=[0]).iloc[:, 0].astype(str).tolist()
    keep = {i + 1 for i, r in enumerate(ids) if r in set(depmap_ids)}  # +1: header is line 0
    df = pd.read_csv(path, index_col=0, skiprows=lambda i: i != 0 and i not in keep)
    assert set(df.index) <= set(depmap_ids), "parsed a row outside the tier"
    return df


MIX_DRUGS = ("Trametinib", "Afatinib", "Everolimus", "Gemcitabine", "Dabrafenib", "Navitoclax", "Taselisib", "JQ1",
             "Idasanutlin", "Bortezomib")


def mix_match() -> dict:
    """MIX-Seq drug -> PRISM broad_ids by normalised name (treatment metadata only)."""
    pri = pd.read_csv(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    sec = pd.read_csv(RAW / "secondary-screen-replicate-collapsed-treatment-info.csv")
    sec = sec[sec.screen_id.isin(["HTS002", "MTS010"])]
    n = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())  # noqa: E731
    return {d: {"primary": sorted(set(pri[pri.name.map(n) == n(d)].broad_id)),
                "secondary": sorted(set(sec[sec.name.map(n) == n(d)].broad_id))} for d in MIX_DRUGS}


def external_lines() -> list:
    """PRISM lines evaluated nowhere: not in MIX-Seq pools A/C/D, not a sealed Tahoe line."""
    ms = json.loads((HERE / "MIXSEQ_SPLIT.json").read_text(encoding="utf-8"))
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    sealed = set(ms["pool_A"]) | set(ms["pool_C"]) | set(ms["pool_D"])
    sealed |= {split["lines"][f]["depmap_id"] for f in split["confirmation"] + split["heldout_zeroshot"] + split["heldout_no_late_endpoint"]}
    ids = pd.read_csv(FILES["primary"], usecols=[0]).iloc[:, 0].astype(str)
    return sorted(i for i in ids if i.startswith("ACH-") and "_" not in i and i not in sealed)


def tier_lines(tier: str) -> tuple[list, list, dict]:
    if tier.startswith("external_"):
        dep = external_lines()
        if tier == "external_mix":
            return dep, dep, mix_match()
        return dep, dep, json.loads((HERE / "DRUG_MATCH.json").read_text(encoding="utf-8"))["drugs"]
    if tier.startswith("mix_"):
        ms = json.loads((HERE / "MIXSEQ_SPLIT.json").read_text(encoding="utf-8"))
        dev = ms["pool_A_development"]
        if tier == "mix_development":
            dep = dev
        else:
            dep = sorted((set(ms["pool_A"]) | set(ms["pool_C"]) | set(ms["pool_D"])) - set(dev))
        return dep, dep, mix_match()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    files = tier_files(split, tier)
    match = json.loads((HERE / "DRUG_MATCH.json").read_text(encoding="utf-8"))["drugs"]
    return files, [split["lines"][f]["depmap_id"] for f in files], match


def main(tier: str, allow_sealed: bool) -> dict:
    if tier not in ("development", "mix_development", "external_mix", "external_tahoe") and not ((HERE / "FREEZE.json").exists() and allow_sealed):
        raise SystemExit(f"TIER_SEALED: {tier} requires FREEZE.json and --allow-sealed")
    files, dep, match = tier_lines(tier)
    drugs = sorted(d for d, v in match.items() if v["primary"] or v["secondary"])
    t0 = time.time()
    prim = read_rows(FILES["primary"], dep)
    sec = read_rows(FILES["secondary"], dep)
    pcols = {}
    for c in prim.columns:
        m = COL.match(c)
        if m and abs(float(m.group(2)) - 2.5) < 1e-6:
            pcols.setdefault(m.group(1), []).append(c)
    scols = {}
    for c in sec.columns:
        m = COL.match(c)
        if m:
            scols.setdefault((m.group(1), m.group(3)), []).append((float(m.group(2)), c))
    shape = (len(files), len(drugs))
    p25, s25, smean = np.full(shape, np.nan), np.full(shape, np.nan), np.full(shape, np.nan)
    for j, d in enumerate(drugs):
        pc = [c for b in match[d]["primary"] for c in pcols.get(b, [])]
        if pc:
            p25[:, j] = prim.reindex(dep)[pc].mean(axis=1).to_numpy()
        at, means = [], []
        for b in match[d]["secondary"]:
            series = scols.get((b, "MTS010")) or scols.get((b, "HTS002")) or []
            if not series:
                continue
            series = sorted(series)
            dose = np.array([s[0] for s in series])
            near = int(np.argmin(np.abs(np.log(dose / 2.5))))
            if abs(np.log(dose[near] / 2.5)) < np.log(1.2):
                at.append(sec.reindex(dep)[series[near][1]].to_numpy())
            block = sec.reindex(dep)[[s[1] for s in series]].to_numpy()
            ok = np.isfinite(block).sum(1) >= 6
            means.append(np.where(ok, np.nanmean(block, 1), np.nan))
        if at:
            s25[:, j] = np.nanmean(np.vstack(at), 0)
        if means:
            smean[:, j] = np.nanmean(np.vstack(means), 0)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / f"prism_{tier}.npz", files=np.array(files), depmap=np.array(dep), drugs=np.array(drugs),
                        primary_2p5=p25, secondary_2p5=s25, secondary_mean=smean)
    receipt = {
        "tier": tier, "files": files, "depmap_ids": dep, "n_drugs": len(drugs),
        "rows_parsed": {"primary": prim.index.tolist(), "secondary": sec.index.tolist()},
        "finite": {"primary_2p5": int(np.isfinite(p25).sum()), "secondary_2p5": int(np.isfinite(s25).sum()),
                   "secondary_mean": int(np.isfinite(smean).sum())},
        "source_sha256": {k: sha256(v) for k, v in FILES.items()},
        "seconds": round(time.time() - t0, 1),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (HERE / f"PRISM_{tier.upper()}_RECEIPT.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    return receipt


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tier", choices=["development", "confirmation", "heldout", "mix_development", "mix_sealed", "external_mix", "external_tahoe"])
    ap.add_argument("--allow-sealed", action="store_true")
    a = ap.parse_args()
    r = main(a.tier, a.allow_sealed)
    print(json.dumps({k: r[k] for k in ("tier", "n_drugs", "finite", "seconds")}, indent=1))
