"""Metadata-only census for the selective hit-triage campaign (no confirmation outcome is read).

File summary
- Path: research/selective_hit_triage_20261013/census.py
- Purpose: establish which compounds, cell lines and (compound, line) pairs are eligible before any
  CTRP response value is opened, and record source hashes.
- Core points:
  - PRISM 19Q4 (primary 2.5 uM, secondary 8-dose) is the screen the campaign triages. It has been
    used by earlier MAESTRO blocks and is treated as exposed input, never as confirmation.
  - CTRP v2 (2015 expanded archive, downloaded 2026-10-02, SHA256 recorded then) is the
    independent-platform confirmation source. Only its metadata files and the identifier columns
    of the pre-QC table (which compound was tested in which experiment) are read here.
  - Compounds are matched by Broad core identifier or by InChIKey connectivity block; cell lines by
    DepMap identifier through the CCLE stripped name.
  - Mechanism families are connected components of compounds sharing a Repurposing Hub target gene
    or MoA string; they define the development/test split so no family crosses it.
- Output: CENSUS.json and census_tables.npz in this folder.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRISM = ROOT / "data/external/prism_19q4/raw"
CCLE = ROOT / "data/external/depmap_19q4"
LINCS = ROOT / "data/external/lincs_l1000_gse92742"
CTRP_ZIP = ROOT / "tmp/gdsc_transport_sources_v5/ctrp_archive.raw.txt"
CTRP_SHA256 = "8f62b3b5ed70cfd367cf52ce0a99884dd0a674d1a8c301474b707648689bdee3"
SPLIT_SALT = "selective-hit-triage-20261013"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def brd_core(broad_id: str) -> str:
    return str(broad_id)[:13]


def strip_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(name).upper())


def connectivity(smiles: str) -> str | None:
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    for part in str(smiles).split(","):
        mol = Chem.MolFromSmiles(part.strip())
        if mol is not None:
            key = Chem.MolToInchiKey(mol)
            return key.split("-")[0] if key else None
    return None


def ctrp_table(z: zipfile.ZipFile, member: str, **kw) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(z.read(member)), sep="\t", encoding="latin-1", **kw)


def families(rows: list[dict]) -> list[int]:
    """Connected components over shared target genes or shared MoA strings."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict = {}
    for i, r in enumerate(rows):
        for token in ["T:" + t for t in r["targets"]] + ["M:" + m for m in r["moas"]]:
            if token in owner:
                a, b = find(i), find(owner[token])
                if a != b:
                    parent[a] = b
            else:
                owner[token] = i
    return [find(i) for i in range(len(rows))]


def main() -> None:
    if sha256(CTRP_ZIP) != CTRP_SHA256:
        raise SystemExit("CTRP_ARCHIVE_MISMATCH")
    sources = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in (
        PRISM / "primary-screen-replicate-collapsed-logfold-change.csv",
        PRISM / "primary-screen-replicate-collapsed-treatment-info.csv",
        PRISM / "secondary-screen-replicate-collapsed-treatment-info.csv",
        PRISM / "secondary-screen-replicate-collapsed-logfold-change.csv",
        CCLE / "sample_info.csv", LINCS / "repurposing_drugs_20200324.txt")}
    sources["tmp/gdsc_transport_sources_v5/ctrp_archive.raw.txt"] = CTRP_SHA256

    # ---- PRISM primary (exposed input)
    pinfo = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-treatment-info.csv")
    lfc = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    prism_lines = [str(x) for x in lfc.index]
    pinfo = pinfo[pinfo["column_name"].isin(lfc.columns)].copy()
    pinfo["core"] = pinfo["broad_id"].map(brd_core)
    # one primary column per compound core: prefer the HTS screen, then the dose nearest 2.5 uM
    pinfo["rank"] = list(zip(pinfo["screen_id"].ne("HTS"), (pinfo["dose"] - 2.5).abs()))
    pinfo = pinfo.sort_values(["core", "rank"]).drop_duplicates("core")
    sinfo = pd.read_csv(PRISM / "secondary-screen-replicate-collapsed-treatment-info.csv")
    secondary_cores = set(sinfo["broad_id"].map(brd_core))

    # ---- CTRP metadata (confirmation source; metadata and identifiers only)
    z = zipfile.ZipFile(CTRP_ZIP)
    ccpd = ctrp_table(z, "v20.meta.per_compound.txt")
    cccl = ctrp_table(z, "v20.meta.per_cell_line.txt")
    cexp = ctrp_table(z, "v20.meta.per_experiment.txt")
    tested = ctrp_table(z, "v20.data.per_cpd_pre_qc.txt", usecols=["experiment_id", "master_cpd_id"]).drop_duplicates()

    # ---- compound matching
    pconn = {r.core: connectivity(r.smiles) for r in pinfo.itertuples()}
    ccpd["core"] = ccpd["broad_cpd_id"].map(lambda x: brd_core(x) if isinstance(x, str) else None)
    ccpd["conn"] = ccpd["cpd_smiles"].map(connectivity)
    by_core = {c: k for k, c in zip(ccpd["master_cpd_id"], ccpd["core"]) if c}
    by_conn: dict = {}
    for k, c in zip(ccpd["master_cpd_id"], ccpd["conn"]):
        if c:
            by_conn.setdefault(c, []).append(int(k))
    match = {}
    for r in pinfo.itertuples():
        if r.core in by_core:
            match[r.core] = (int(by_core[r.core]), "broad_core")
        elif pconn[r.core] and len(by_conn.get(pconn[r.core], [])) == 1:
            match[r.core] = (by_conn[pconn[r.core]][0], "inchikey_connectivity")

    # ---- cell-line matching: CTRP name -> DepMap id via stripped name
    info = pd.read_csv(CCLE / "sample_info.csv")
    strip_to_depmap: dict = {}
    for d, s in zip(info["DepMap_ID"], info["stripped_cell_line_name"]):
        strip_to_depmap.setdefault(strip_name(s), set()).add(d)
    ccl_to_depmap = {}
    for k, name in zip(cccl["master_ccl_id"], cccl["ccl_name"]):
        ids = strip_to_depmap.get(strip_name(name), set())
        if len(ids) == 1:
            ccl_to_depmap[int(k)] = next(iter(ids))
    exp_line = {int(e): ccl_to_depmap.get(int(c)) for e, c in zip(cexp["experiment_id"], cexp["master_ccl_id"])}

    # ---- eligible pairs: tested in CTRP and screened in the PRISM primary
    prism_set = set(prism_lines)
    cpd_to_core = {v[0]: k for k, v in match.items()}
    pairs: dict = {}
    for e, k in zip(tested["experiment_id"], tested["master_cpd_id"]):
        line = exp_line.get(int(e))
        if line in prism_set and int(k) in cpd_to_core:
            pairs.setdefault((cpd_to_core[int(k)], line), set()).add(int(e))

    # ---- annotation and mechanism families (Repurposing Hub fields as carried by PRISM)
    rows = []
    for r in pinfo.itertuples():
        if r.core not in match:
            continue
        targets = sorted({t.strip() for t in str(r.target).split(",") if t.strip() and t.strip() != "nan" and t.strip() != "NA"})
        moas = sorted({m.strip() for m in str(r.moa).split(",") if m.strip() and m.strip() not in ("nan", "NA")})
        rows.append({"core": r.core, "name": r.name, "column": r.column_name, "dose": float(r.dose), "screen": r.screen_id,
                     "phase": str(r.phase), "targets": targets, "moas": moas, "smiles": str(r.smiles).split(",")[0].strip(),
                     "connectivity": pconn[r.core], "ctrp_master_cpd_id": match[r.core][0], "match": match[r.core][1],
                     "secondary": r.core in secondary_cores,
                     "ctrp_lines": sum(1 for (c, _l) in pairs if c == r.core)})
    rows = [r for r in rows if r["ctrp_lines"] > 0]
    fam = families(rows)
    fam_ids = {f: f"F{abs(int(hashlib.sha256(','.join(sorted(rows[i]['core'] for i in range(len(rows)) if fam[i] == f)).encode()).hexdigest()[:8], 16)):08d}" for f in set(fam)}
    for i, r in enumerate(rows):
        r["family"] = fam_ids[fam[i]]
    sizes = pd.Series([r["family"] for r in rows]).value_counts()

    # ---- L1000 and CCLE context availability
    lincs = pd.read_csv(LINCS / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", usecols=["pert_id", "pert_type"])
    lincs_cores = set(lincs.loc[lincs["pert_type"] == "trt_cp", "pert_id"].astype(str).str[:13])
    expr_lines = set(pd.read_csv(CCLE / "CCLE_expression.csv", usecols=[0]).iloc[:, 0].astype(str))
    for r in rows:
        r["l1000"] = r["core"] in lincs_cores

    census = {
        "label": "metadata only; no CTRP response value read",
        "sources_sha256": sources,
        "prism_primary": {"compounds": int(len(pinfo)), "lines": len(prism_lines)},
        "ctrp": {"compounds": int(len(ccpd)), "cell_lines": int(len(cccl)), "experiments": int(len(cexp)),
                 "lines_mapped_to_depmap": len(ccl_to_depmap)},
        "matched_compounds": len(match), "match_kinds": pd.Series([v[1] for v in match.values()]).value_counts().to_dict(),
        "eligible_compounds": len(rows), "eligible_pairs": len(pairs),
        "eligible_lines": len({l for (_c, l) in pairs}),
        "pairs_with_multiple_ctrp_experiments": sum(1 for v in pairs.values() if len(v) > 1),
        "with_secondary": sum(r["secondary"] for r in rows), "with_l1000": sum(r["l1000"] for r in rows),
        "lines_with_ccle_expression": len({l for (_c, l) in pairs} & expr_lines),
        "families": int(len(sizes)), "largest_family_sizes": sizes.head(8).tolist(),
        "phase_counts": pd.Series([r["phase"] for r in rows]).value_counts().to_dict(),
        "compounds": rows,
    }
    (HERE / "CENSUS.json").write_text(json.dumps(census, indent=1) + "\n", encoding="utf-8")
    keys = sorted(pairs)
    np.savez_compressed(HERE / "census_pairs.npz", core=np.array([k[0] for k in keys]), line=np.array([k[1] for k in keys]),
                        experiments=np.array([";".join(map(str, sorted(pairs[k]))) for k in keys]))
    print(json.dumps({k: v for k, v in census.items() if k not in ("compounds", "sources_sha256")}, indent=1))


if __name__ == "__main__":
    main()
