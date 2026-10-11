"""PRISM viability tiers for block N, extracted once from the local PRISM 19Q4 files.

* primary: replicate-collapsed log fold change at 2.5 uM (HTS or MTS004), mean over a drug's columns.
* secondary: replicate-collapsed log fold change of the independent secondary screen at the dose
  closest to 2.5 uM (different plates and run), for drugs it contains.

Open tier: reference and development drugs. Sealed tier: confirmation drugs, refused by name
(``TIER_SEALED``) until FREEZE.json exists. ``extract()`` writes both tiers and TIERS_RECEIPT.json;
``load(tier)`` checks the receipt digest before returning arrays.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "data/external/prism_19q4/raw"
DERIVED = ROOT / "data/external/prism_19q4/derived"
FILES = {"open": DERIVED / "block_n_prism_open.npz", "sealed": DERIVED / "block_n_prism_sealed.npz"}


class TierSealed(RuntimeError):
    code = "TIER_SEALED"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract() -> dict:
    receipt = HERE / "TIERS_RECEIPT.json"
    if receipt.exists():
        raise SystemExit("TIERS_RECEIPT.json exists; tiers are extracted once")
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))["units"]
    lfc = pd.read_csv(RAW / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    lines = list(lfc.index)
    sec_info = pd.read_csv(RAW / "secondary-screen-replicate-collapsed-treatment-info.csv")
    sec = pd.read_csv(RAW / "secondary-screen-replicate-collapsed-logfold-change.csv", index_col=0).reindex(lines)
    sec_cols = {}
    for name, grp in sec_info[sec_info["column_name"].isin(sec.columns)].groupby(sec_info["name"].astype(str).str.lower()):
        best = grp.iloc[np.argsort(np.abs(np.log(grp["dose"].astype(float) / 2.5)).to_numpy())]
        dose = float(best["dose"].iloc[0])
        sec_cols[name] = (best[np.isclose(best["dose"].astype(float), dose)]["column_name"].tolist(), dose)
    tiers = {"open": [d for d, u in split.items() if u["role"] in ("reference", "development")],
             "sealed": [d for d, u in split.items() if u["role"] == "confirmation"]}
    DERIVED.mkdir(parents=True, exist_ok=True)
    out = {"sources": {f: sha256(RAW / f) for f in ("primary-screen-replicate-collapsed-logfold-change.csv",
                                                     "primary-screen-replicate-collapsed-treatment-info.csv",
                                                     "secondary-screen-replicate-collapsed-logfold-change.csv",
                                                     "secondary-screen-replicate-collapsed-treatment-info.csv")},
           "n_lines": len(lines), "tiers": {}}
    for tier, drugs in tiers.items():
        drugs = sorted(drugs)
        P = np.stack([lfc[split[d]["prism_columns"]].mean(axis=1).to_numpy(np.float32) for d in drugs])
        S2 = np.full_like(P, np.nan)
        sdose = np.full(len(drugs), np.nan)
        for i, d in enumerate(drugs):
            if d.lower() in sec_cols:
                cols, dose = sec_cols[d.lower()]
                S2[i] = sec[cols].mean(axis=1).to_numpy(np.float32)
                sdose[i] = dose
        np.savez_compressed(FILES[tier], drug=np.array(drugs), moa=np.array([split[d]["moa"] for d in drugs]),
                            role=np.array([split[d]["role"] for d in drugs]), line=np.array(lines),
                            primary=P, secondary=S2, secondary_dose=sdose)
        out["tiers"][tier] = {"file": FILES[tier].name, "sha256": sha256(FILES[tier]), "n_drugs": len(drugs),
                              "n_with_secondary": int(np.isfinite(sdose).sum())}
    receipt.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def load(tier: str) -> dict:
    if tier == "sealed" and not (HERE / "FREEZE.json").exists():
        raise TierSealed(f"{TierSealed.code}: the confirmation tier opens only after FREEZE.json")
    rec = json.loads((HERE / "TIERS_RECEIPT.json").read_text(encoding="utf-8"))["tiers"][tier]
    if sha256(FILES[tier]) != rec["sha256"]:
        raise RuntimeError(f"TIER_DIGEST_MISMATCH: {FILES[tier].name}")
    with np.load(FILES[tier], allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


if __name__ == "__main__":
    print(json.dumps(extract(), indent=1))
