"""L1000 Level 5 (MODZ) readers shared by the development feasibility check and the external study.

File summary
- Path: research/belief_planning/l1000_level5.py
- Purpose: turn the public Level 5 signatures of GSE92742 (Phase I) and GSE70138 (Phase II) into
  `common.Data` conditions: a profile, QC, detection and batch for each (compound, line, 24 h,
  dose). The rules are the ones `sequence_audit/lincs_prepare.py` froze for the development L1000
  tiers:
  - Profile: the mean MODZ vector, over the 978 measured landmark genes, of a condition's usable
    signatures.
  - Usable signature: at least two replicates and a finite replicate correlation.
  - Detection: the median `distil_cc_q75` of the usable signatures is at least max(0.10, the
    0.99 quantile of the same study's DMSO signatures at that line and time).
  - Labels: exact Repurposing Hub joins, single mechanism only.
- Core points:
  - `sig_info` and `pert_info` are metadata. `sig_metrics` (replicate correlation, sample
    counts) and the gctx matrix are measurements. The external study reads them only inside the
    vault (`external_phase2.open_study`).
  - `phase1_line_task_feasibility` records why the strict cross-study design was not run. That
    design used a Phase I reference library for a four-line, 10 uM, 24 h task. Phase I measured
    only 266 labelled compounds at all four conditions, only four classes qualify for the pool,
    and it yields 96 development episodes: too few to develop or check a policy.
- Interfaces: `FILES`, `sig_info`, `qc_metrics`, `vehicle_null`, `read_profiles`, `annotations`,
  `build_conditions`, `inchikey_blocks_sciplex3`, `phase1_line_task_feasibility`
- Depends on: data/external/lincs_l1000_phase{1,2}, research/sequence_audit/lincs_prepare.py,
  research/acquisition_followup/lincs_flow.py, h5py, rdkit
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import tasks as T

P, C, E = T.P, T.C, T.E
LP = T.LP
import lincs_flow as LF  # noqa: E402  (acquisition_followup is on sys.path through tasks)

ROOT = T.ROOT
PHASE1 = ROOT / "data/external/lincs_l1000_phase1"
PHASE2 = ROOT / "data/external/lincs_l1000_phase2"
OUT = ROOT / "outputs" / "belief_planning_20260927" / "l1000_level5"
FILES = {
    "phase1": {"sig_info": PHASE1 / "GSE92742_Broad_LINCS_sig_info.txt.gz",
               "sig_metrics": PHASE1 / "GSE92742_Broad_LINCS_sig_metrics.txt.gz",
               "pert_info": PHASE1 / "GSE92742_Broad_LINCS_pert_info.txt.gz",
               "gene_info": PHASE1 / "GSE92742_Broad_LINCS_gene_info.txt.gz",
               "gctx": PHASE1 / "GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx"},
    "phase2": {"sig_info": PHASE2 / "GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz",
               "sig_metrics": PHASE2 / "GSE70138_Broad_LINCS_sig_metrics_2017-03-06.txt.gz",
               "pert_info": PHASE2 / "GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz",
               "gene_info": PHASE2 / "GSE70138_Broad_LINCS_gene_info_2017-03-06.txt.gz",
               "gctx": PHASE2 / "GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx"},
}
TIME = 24.0


def _dose_nm(text: str) -> float | None:
    """'10.0 um', '10 µM', '500 nM' -> nanomolar; None when unparsable."""
    try:
        value, unit = str(text).split()
        factor = {"um": 1000.0, "µm": 1000.0, "nm": 1.0}[unit.lower()]
        return round(float(value) * factor, 6)
    except (ValueError, KeyError):
        return None


# ------------------------------------------------------------------------------ metadata
def sig_info(study: str) -> pd.DataFrame:
    """Signature metadata only (no QC metric, no expression)."""
    sig = pd.read_csv(FILES[study]["sig_info"], sep="\t", dtype=str)
    sig["time"] = pd.to_numeric(sig.pert_itime.str.split().str[0], errors="coerce")
    sig["batch"] = sig.sig_id.str.split("_").str[0]
    sig["dose_nm"] = [_dose_nm(d) for d in sig.pert_idose]
    return sig


def pert_info(study: str) -> pd.DataFrame:
    return pd.read_csv(FILES[study]["pert_info"], sep="\t", dtype=str).fillna("")


def inchikey_blocks_sciplex3() -> set:
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    data = C.load()
    out = set()
    for smiles in data.compounds.drop_duplicates("compound").smiles:
        mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles else None
        if mol is not None:
            out.add(Chem.MolToInchiKey(mol).split("-")[0])
    return out


def landmark_genes(study: str) -> list[str]:
    genes = pd.read_csv(FILES[study]["gene_info"], sep="\t", dtype=str)
    return sorted(genes[genes.pr_is_lm == "1"].pr_gene_id.tolist(), key=int)


def annotations(study: str, pert_ids) -> dict:
    """Repurposing Hub mechanism per compound (the frozen `lincs_flow.annotation_map` join)."""
    pert = pert_info(study)
    table = LF.annotation_map(pert[pert.pert_id.isin(set(pert_ids))])
    out = {}
    for pid, a in table.items():
        moa = a["moa"]
        single = len(moa) == 1 and "|" not in moa[0]
        out[pid] = {"klass": moa[0] if single else None, "route": a["annotation_route"],
                    "multi_moa": bool(moa) and not single}
    return out


# ------------------------------------------------------------------------------ measurements
def qc_metrics(study: str) -> pd.DataFrame:
    m = pd.read_csv(FILES[study]["sig_metrics"], sep="\t", dtype=str)
    m["cc"] = pd.to_numeric(m.distil_cc_q75, errors="coerce")
    m["n"] = pd.to_numeric(m.distil_nsample, errors="coerce").fillna(0).astype(int)
    m["ss"] = pd.to_numeric(m.distil_ss, errors="coerce")
    return m[["sig_id", "cc", "n", "ss"]]


def vehicle_null(study: str, lines) -> dict:
    """max(0.10, q99) of DMSO replicate correlation at each line, 24 h (lincs_prepare's rule)."""
    sig = sig_info(study).merge(qc_metrics(study), on="sig_id")
    out = {}
    for line in lines:
        v = sig[(sig.cell_id == line) & (sig.time == TIME) & (sig.pert_type == "ctl_vehicle") & (sig.n >= 2)
                & (sig.cc > -600)]
        q = float(v.cc.quantile(0.99)) if len(v) else float("nan")
        out[line] = {"signatures": int(len(v)), "q99": q, "threshold": max(0.10, q) if len(v) else None}
    return out


def read_profiles(study: str, sig_ids) -> dict[str, np.ndarray]:
    """Landmark MODZ vectors for the named signatures, read row-wise from the gctx."""
    import h5py
    genes = landmark_genes(study)
    with h5py.File(FILES[study]["gctx"], "r") as f:
        col = [x.decode() for x in f["0/META/COL/id"][:]]
        row = {x.decode(): i for i, x in enumerate(f["0/META/ROW/id"][:])}
        gpos = np.asarray([row[g] for g in genes])
        where = {s: i for i, s in enumerate(col)}
        wanted = sorted((where[s], s) for s in set(sig_ids) if s in where)
        matrix = f["0/DATA/0/matrix"]
        out = {}
        for start in range(0, len(wanted), 1024):
            block = wanted[start:start + 1024]
            values = matrix[[i for i, _ in block], :]
            for (_, s), vec in zip(block, values):
                out[s] = vec[gpos].astype(np.float32)
    return out


def build_conditions(study: str, keys, compounds) -> tuple[pd.DataFrame, np.ndarray, dict]:
    """One row per (compound, key) measured: profile, QC and detection. Reads measurements."""
    lines = sorted({k[0] for k in keys})
    wanted = {(k[0], float(k[2])) for k in keys}
    sig = sig_info(study)
    sig = sig[(sig.pert_type == "trt_cp") & (sig.time == TIME) & sig.pert_id.isin(set(compounds))]
    sig = sig[[(line, d) in wanted for line, d in zip(sig.cell_id, sig.dose_nm)]]
    sig = sig.merge(qc_metrics(study), on="sig_id", how="left")
    null = vehicle_null(study, lines)
    usable = sig[(sig.n >= 2) & (sig.cc > -600) & sig.cc.notna()]
    vectors = read_profiles(study, usable.sig_id.tolist())
    rows, shifts = [], []
    for (pid, line, dose), group in sig.groupby(["pert_id", "cell_id", "dose_nm"], sort=True):
        ok = group[group.sig_id.isin(vectors) & group.sig_id.isin(usable.sig_id)]
        vec = np.mean([vectors[s] for s in ok.sig_id], axis=0) if len(ok) else np.zeros(978, np.float32)
        qc = bool(len(ok) >= 1 and np.isfinite(vec).all())
        cc = float(ok.cc.median()) if qc else float("nan")
        threshold = null[line]["threshold"]
        rows.append({"compound": pid, "cell_line": line, "time": TIME, "dose": float(dose),
                     "signatures": int(len(ok)), "batch": "|".join(sorted(set(group.batch))),
                     "cc_q75": cc, "signature_strength": float(ok.ss.median()) if qc else float("nan"),
                     "qc": qc, "detected": bool(qc and threshold is not None and cc >= threshold),
                     # the SciPlex3 QC fields, set so that common.qc_passed reproduces the rule
                     "replicates": 2 if qc else 0, "n_cells_rep1": 20, "n_cells_rep2": 20})
        shifts.append(vec)
    return pd.DataFrame(rows), np.asarray(shifts, dtype=np.float32), null


def as_data(conditions: pd.DataFrame, shift: np.ndarray, compounds: pd.DataFrame) -> C.Data:
    data = C.Data(conditions, shift, np.zeros(0), np.zeros(0), compounds, pd.DataFrame(), {}, pd.DataFrame(), np.zeros(0))
    data.agreement = conditions.cc_q75.to_numpy()
    for row, r in conditions.iterrows():
        data.index.setdefault((r.cell_line, float(r.time), float(r.dose)), {})[r.compound] = row
    return data


# ------------------------------------------------------------------------------ the strict design, not run
def phase1_line_task_feasibility() -> dict:
    """Why a Phase I reference library for a Phase II line-choice task was not used (metadata + Phase I)."""
    lines = ("MCF7", "PC3", "A375", "HT29")
    keys = tuple((line, TIME, 10000.0) for line in lines)
    sig = sig_info("phase1")
    treated = sig[(sig.pert_type == "trt_cp") & (sig.time == TIME) & (sig.dose_nm == 10000.0) & sig.cell_id.isin(lines)]
    conditions, _, null = build_conditions("phase1", keys, set(treated.pert_id))
    labels = annotations("phase1", set(conditions.compound))
    pert = pert_info("phase1").set_index("pert_id")
    qc = conditions[conditions.qc]
    measured = qc.groupby("compound").cell_line.apply(set)
    detected = qc[qc.detected].groupby("compound").cell_line.apply(set)
    labelled = {c: v["klass"] for c, v in labels.items() if v["klass"]}
    complete = [c for c in labelled if set(lines) <= measured.get(c, set())]
    stats = {}
    for c in complete:
        s = stats.setdefault(labelled[c], {"identities": set(), "detected": set()})
        ident = (pert.inchi_key.get(c, "") or c).split("-")[0]
        s["identities"].add(ident)
        if detected.get(c):
            s["detected"].add(ident)
    pool = sorted(k for k, s in stats.items()
                  if len(s["identities"]) >= LP.POOL_MIN_IDENTITIES and len(s["detected"]) >= LP.POOL_MIN_DETECTED_IDENTITIES)
    eligible = [c for c in complete if labelled[c] in pool]
    return {"lines": list(lines), "vehicle_null": null, "conditions": int(len(conditions)),
            "detected_by_line": {l: [int(g.detected.sum()), int(g.qc.sum())] for l, g in conditions.groupby("cell_line")},
            "labelled_compounds": len(labelled), "complete_labelled": len(complete), "pool": pool,
            "eligible_episode_compounds": len(eligible), "episodes": len(eligible) * max(len(pool) - 1, 0)}


def write_feasibility() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    result = phase1_line_task_feasibility()
    (OUT / "phase1_line_task_feasibility.json").write_bytes(json.dumps(result, indent=1, default=str).encode())
    return result


if __name__ == "__main__":
    print(json.dumps(write_feasibility(), indent=1, default=str))
