"""Shared paths, folds, access control and data loading for the mono-pretraining study.

File summary
- Path: research/astra/mono_pretraining_20261005/common.py
- Purpose: one place for the frozen constants (seeds, folds, grids), the outcome-access guard and the
  loaders. Every read of an outcome value (GDSC2 LN_IC50, Jaaks outcome columns) goes through `guard`,
  which refuses unless `FREEZE.json` exists and every frozen file still has its recorded SHA256, and
  appends to `access_log.jsonl`.
- Core points: folds are fixed by hashing; the 14 PROGENy covariates are standardised on all 1,431
  public-context cells (covariates only, identical for every arm); Jaaks lines are excluded from mono
  training per fold (the held-out fold's lines are never in that fold's mono training set).
- Interfaces: `guard`, `load_context`, `load_split`, `fold_of`, `load_mono`, `drug_table`.
- Depends on: numpy, pandas; `tools.datasets.combination_screens.open_vault`; the repo xlsx reader.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tools.datasets.combination_screens import open_vault

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
S0 = HERE / "data_s0"
RESULTS = HERE / "results"
FREEZE = HERE / "FREEZE.json"
ACCESS_LOG = HERE / "access_log.jsonl"
GDSC2 = ROOT / "data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
PROGENY = ROOT / "research/astra/knowledge_transfer_20261004/context/raw/GDSC_progeny_activities.csv"
PARTITION = ROOT / "research/astra/confirmation_campaign_20261004/protocol/partition.json"

TISSUE_CODE = {"Breast": 1, "Colon": 2, "Pancreas": 3}
SEED = 20261005
N_FOLDS = 5
N_PERM = 10
N_DRAWS = 10
N_HIST = 4
FOLDS = tuple(range(N_FOLDS)) + ("E",)


def guard(purpose: str, source: Path) -> dict:
    """Outcome access ticket; refuses unless the freeze exists and every frozen file is intact."""
    return open_vault(FREEZE, ACCESS_LOG, purpose=purpose, source=source, root=ROOT)


def load_context() -> tuple[list[str], np.ndarray, dict]:
    """(sidms, standardised 14-score matrix, sidm -> row) over all public-context cells."""
    raw = pd.read_csv(PROGENY, index_col=0).T            # rows = SIDM, columns = 14 pathways
    raw = raw.sort_index()
    x = raw.to_numpy(float)
    z = (x - x.mean(0)) / x.std(0)
    sidms = list(raw.index)
    return sidms, z, {s: i for i, s in enumerate(sidms)}


def load_split() -> dict:
    return json.loads(PARTITION.read_text(encoding="utf-8"))["split"]


def fold_of(split: dict) -> dict:
    """sidm -> (tissue, 'E' | 0..4); HD lines are tissue-stratified into five hashed folds."""
    out = {}
    for tissue, parts in split.items():
        for sidm in parts["E"]:
            out[sidm] = (tissue, "E")
        hd = sorted(parts["HD"])
        perm = np.random.default_rng([SEED, TISSUE_CODE[tissue]]).permutation(len(hd))
        for rank, i in enumerate(perm):
            out[hd[i]] = (tissue, int(rank % N_FOLDS))
    return out


def drug_table() -> pd.DataFrame:
    """Jaaks drug ids in a fixed order: the 63 mapped drugs first, then 2265 and the composite."""
    d = pd.read_csv(S0 / "drug_identity_map.csv", dtype={"jaaks_id": str})
    mapped = sorted(d.loc[d.status == "mapped", "jaaks_id"])
    other = sorted(set(d.jaaks_id) - set(mapped))
    ids = mapped + other
    return pd.DataFrame({"jaaks_id": ids, "row": range(len(ids)), "mapped": [i in set(mapped) for i in ids]})


def history_draw(tissue_code: int, fold, draw: int, candidates: list[str], n: int) -> list[str]:
    """Histories of one (tissue, outer fold, draw): n lines of the allowed candidates, shared by that fold."""
    cand = sorted(candidates)
    key = [SEED, int(tissue_code), 99 if fold == "E" else int(fold), int(draw)]
    perm = np.random.default_rng(key).permutation(len(cand))
    return sorted(cand[i] for i in perm[:min(n, len(cand))])


def _read_gdsc2_labels() -> pd.DataFrame:
    from research.certified_discovery.xlsx import iter_rows
    it = iter_rows(GDSC2)
    header = next(it)
    ix = {name: i for i, name in enumerate(header)}
    need = ["NLME_CURVE_ID", "SANGER_MODEL_ID", "DRUG_ID", "MIN_CONC", "MAX_CONC", "LN_IC50", "AUC", "RMSE"]
    rows = [[r[ix[n]] for n in need] for r in it]
    df = pd.DataFrame(rows, columns=["nlme_curve_id", "sidm", "drug_id", "min_conc", "max_conc", "ln_ic50", "auc", "rmse"])
    for c in ("nlme_curve_id", "min_conc", "max_conc", "ln_ic50", "auc", "rmse"):
        df[c] = pd.to_numeric(df[c])
    df["drug_id"] = df["drug_id"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    return df


def load_mono() -> pd.DataFrame:
    """GDSC2 mono records joined to the S0 flags; the label read is a guarded, logged outcome access."""
    guard("GDSC2 mono labels (LN_IC50, MAX_CONC, AUC, RMSE) for pretraining and held-out mono evaluation", GDSC2)
    cache = RESULTS / "mono_labels.csv.gz"
    if not cache.exists():
        RESULTS.mkdir(exist_ok=True)
        lab = _read_gdsc2_labels()
        cov = pd.read_csv(S0 / "coverage_all_gdsc2_records.csv.gz", dtype={"jaaks_drug_id": str, "drug_id": str})
        m = cov.merge(lab[["nlme_curve_id", "min_conc", "max_conc", "ln_ic50", "auc", "rmse"]], on="nlme_curve_id", how="left",
                      suffixes=("", "_lab"))
        assert len(m) == len(cov) == 242036 and m["ln_ic50"].notna().all()
        assert np.allclose(m["max_conc"], m["max_conc_uM"]), "label-file MAX_CONC disagrees with the S0 design column"
        m["y_rel"] = (m["ln_ic50"] - np.log(m["max_conc"])) / np.log(2.0)
        m.to_csv(cache, index=False, compression="gzip")
    return pd.read_csv(cache, dtype={"jaaks_drug_id": str, "drug_id": str})


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dump(path: Path, obj) -> None:
    from research.astra.confirmation_campaign_20261004.design import campaign as c
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c.jsonable(obj), indent=1, allow_nan=False) + "\n", encoding="utf-8")
