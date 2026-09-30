"""Source registry: where every asset came from, what it holds and what it cannot be used for.

File summary
- Path: research/maestro_vc_v1/sources.py
- Purpose: one `SourceRecord` per data source with URL, publication, version, licence, retrieval date,
  checksum, schema, feature mapping and known limitations, assembled only from what a provenance file
  or the file itself states.
- Core points:
  - Nothing is invented. A field the local record does not state is the literal string `unverified`, so
    a reader can tell a checked fact from a gap. Licences are copied from a provenance file or from a
    project document that quotes them; otherwise `unverified`.
  - Checksums are computed for files up to `HASH_LIMIT` bytes. For larger files the recorded
    checksum from the provenance file is used and labelled `recorded`; if none exists the value is
    `not_computed` and the size and modification time are given instead.
  - Schemas are read from the file (header row, `var` labels, sheet names), never assumed. Large
    matrices contribute their shape only.
  - Known limitations are statements the project itself already made about the asset (data README,
    provenance notes, case-package READMEs) or that follow directly from what the file is; each names
    its basis.
  - The registry is data: `SOURCES` is a list of dictionaries; `collect` adds the verified fields.
- Interfaces: `SOURCES`, `collect`, `sha256_file`, `UNVERIFIED`, `HASH_LIMIT`
- Depends on: h5py (optional), pandas
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNVERIFIED = "unverified"
HASH_LIMIT = 700 * 1024 * 1024

SOURCES = [
    {"id": "sciplex3", "path": "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad", "role": "state_table (transcriptome, 3 cell lines, 188 compounds)",
     "url": "https://figshare.com/articles/dataset/24681285 (file 43381398)", "publication": "Srivatsan et al. 2020, Science (sci-Plex)",
     "licence": "CC BY 4.0 (data/README.md; confirmed by the Figshare API on 2026-09-29, public_checks_20260929)", "recorded_sha256": "bde2420ce24c8aad00d4b0fcbeb0351334e7cd6945d06030ce47be6bcc63b35f",
     "feature_mapping": "column j holds the gene of label row j + 1; resolved by identity markers (virtual_cell.artifacts)",
     "limitations": ["feature labels are offset by one row: the first entry is a stray header (data/README.md)",
                     "the gene_symbol column is unusable; read labels only through resolve_label_offset",
                     "pseudobulk shifts per (cell line, dose, time) with two replicate groups; not single-cell resolution"]},
    {"id": "sciplex3_prepared", "path": "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
     "role": "state_table conditions (prepared)", "url": "derived from sciplex3 by research/dynamic_world_model", "licence": "derived; inherits sciplex3",
     "limitations": ["a (compound, cell line, time, dose) group with fewer than 20 cells per replicate group is dropped before this table; "
                     "protocol v2.1 charges such a planned condition as a QC failure"]},
    {"id": "l1000_phase1_prepared", "path": "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
     "role": "state_table conditions (prepared, 978 landmark genes)",
     "url": "derived from GSE92742 Level 5 by research/sequence_audit/lincs_prepare.py", "licence": "derived; inherits GSE92742",
     "limitations": ["Level 5 MODZ signatures are already normalised against plate population controls; a per-condition "
                     "vehicle well does not exist, so control matching is a property of the release, not checkable here",
                     "mechanism-class labels are the Repurposing Hub annotation, a curated label and not ground truth"]},
    {"id": "l1000_phase1_meta", "path": "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_pert_info.txt.gz",
     "role": "compound metadata (structure, identity)", "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92742",
     "publication": "Subramanian et al. 2017, Cell", "licence": UNVERIFIED,
     "limitations": ["canonical_smiles is missing or -666 for some perturbagens; those compounds have no structure fingerprint"]},
    {"id": "l1000_phase2_meta", "path": "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_pert_info.txt.gz",
     "role": "phase II metadata; GSE70138 was opened by belief-planning-1", "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE70138",
     "licence": UNVERIFIED, "limitations": ["opened by an earlier session: it is not an unopened external confirmation set (README, protocol v2)"]},
    {"id": "prism_secondary", "path": "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv",
     "licence": "CC BY 4.0 (Figshare API, 2026-09-29, public_checks_20260929)",
     "role": "viability bridge (fitted dose-response AUC per compound and cell line)", "provenance": "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv.provenance.json",
     "limitations": ["a fitted screening curve is one retrospective record, not an independent replicate set",
                     "the screen measures pooled viability, neither target engagement nor pathway activity"]},
    {"id": "depmap_crispr", "path": "data/raw/depmap/CRISPRGeneEffect.csv", "role": "dependency bridge",
     "licence": "CC BY 4.0 (Figshare API, 2026-09-29, public_checks_20260929)",
     "provenance": "data/raw/depmap/CRISPRGeneEffect.csv.provenance.json",
     "limitations": ["a processed cross-study dependency score is not a condition-matched engagement measurement",
                     "CRISPR removes the protein over days; it is not dose- or time-matched to a compound exposure"]},
    {"id": "depmap_expression", "path": "data/raw/depmap/OmicsExpressionProteinCodingGenesTPMLogp1.csv", "role": "target abundance premise",
     "licence": "CC BY 4.0 (Figshare API, 2026-09-29, public_checks_20260929)",
     "provenance": "data/raw/depmap/OmicsExpressionProteinCodingGenesTPMLogp1.csv.provenance.json",
     "limitations": ["bulk RNA abundance is not protein abundance, isoform usage or residual catalytic activity"]},
    {"id": "gdsc2", "path": "data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx", "role": "independent phenotype release",
     "provenance": "data/external/gdsc2_fitted/provenance.json", "limitations": ["fitted dose-response per cell line and drug; a different study from PISA and DepMap"]},
    {"id": "pisa_living_cells", "path": "data/external/pisa_living_cells/PMC11554310_supplementary.zip", "role": "engagement (thermal stability shift, K562 living cells)",
     "provenance": "data/external/pisa_living_cells/provenance.json", "limitations": ["living-cell arm only; the lysate arm is not used for engagement",
                                                                                   "thermal stability shift is an engagement proxy, not occupancy"]},
    {"id": "kinobeads", "path": "data/raw/kinobeads/Klaeger_allTargets.xlsx", "role": "engagement (kinobead competition binding, lysate)",
     "url": UNVERIFIED, "publication": "Klaeger et al. 2017, Science (from the file name; not re-verified)", "licence": UNVERIFIED,
     "limitations": ["cell-lysate competition binding: the framework refuses a lysate assay as a supplier of condition-matched engagement (engagement package)"]},
    {"id": "nyman2020", "path": "data/external/nyman2020/README.md", "role": "temporal protein response (melanoma line)",
     "url": "https://www.biorxiv.org/content/10.1101/568758v1", "licence": UNVERIFIED,
     "limitations": ["a single melanoma line; used only as a measured-record source in the licensing tests"]},
    {"id": "hgnc", "path": "data/external/hgnc/hgnc_complete_set.txt", "provenance": "data/external/hgnc/hgnc_complete_set.txt.provenance.json",
     "role": "gene identifier canonicalisation", "limitations": ["licence note says CC0 per the HGNC page and was not re-verified when downloaded"]},
    {"id": "msigdb_hallmark", "path": "data/external/msigdb/h.all.v2024.1.Hs.symbols.gmt", "provenance": "data/external/msigdb/h.all.v2024.1.Hs.symbols.gmt.provenance.json",
     "role": "pathway anchors and pathway readouts", "limitations": ["Hallmark sets are coarse; a set score is not a pathway activity measurement"]},
    {"id": "reactome", "path": "data/raw/ontology/NCBI2Reactome.txt", "provenance": "data/raw/ontology/NCBI2Reactome.txt.provenance.json",
     "role": "gene to pathway edges for the hypothesis graph", "limitations": ["lowest-level pathway mapping; membership is not causal direction"]},
    {"id": "public_checks_20260929", "path": "data/external/public_checks_20260929/public_checks.json",
     "role": "independent agreement checks: Figshare licences, PubChem InChIKey blocks, ChEMBL mechanisms",
     "provenance": "data/external/public_checks_20260929/provenance.json",
     "url": "https://api.figshare.com ; https://pubchem.ncbi.nlm.nih.gov/rest/pug ; https://www.ebi.ac.uk/chembl/api",
     "licence": "each service's own terms; only small metadata responses are stored",
     "limitations": ["a name can resolve to a salt or another form, so a disagreement is a finding to inspect, not an error",
                     "ChEMBL holds a curated mechanism for only a minority of research compounds",
                     "the SciPlex3 licence row of the main run failed transiently; figshare_sciplex3_retry.json holds the retry"]},
    {"id": "case_package_real_v3", "path": "data/evaluation/derived/real_case_manifest_v3.json", "role": "58 typed-premise genetic-pharmacological cases",
     "provenance": "data/evaluation/cases/real_v3/README.md", "licence": "derived from DepMap 24Q2 and PRISM 19Q4",
     "limitations": ["retrospective; contains no new experiment", "decision rules are an evidence-sufficiency convention declared in advance, not biological truth"]},
    {"id": "case_package_engagement_v1", "path": "data/evaluation/cases/engagement_v1", "role": "6 engagement-repair cases",
     "provenance": "data/evaluation/README.md", "limitations": ["the hidden engagement partition is a lysate release usable only as a test of a decision already made"]},
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _schema(path: Path) -> dict:
    """What the file itself says about its columns or contents; empty when it cannot be read cheaply."""
    name = path.name.lower()
    try:
        if name.endswith(".csv") or name.endswith(".tsv") or name.endswith(".txt") and path.stat().st_size < 4 << 30:
            delimiter = "\t" if name.endswith((".tsv", ".txt")) else ","
            with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
                header = next(csv.reader(fh, delimiter=delimiter), [])
            return {"columns": header[:40], "n_columns": len(header)}
        if name.endswith(".gz") and not name.endswith(".gctx.gz"):
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
                header = fh.readline().rstrip("\n").split("\t")
            return {"columns": header[:40], "n_columns": len(header)}
        if name.endswith(".gmt"):
            with open(path, "r", encoding="utf-8") as fh:
                sets = [line.split("\t")[0] for line in fh if line.strip()]
            return {"n_sets": len(sets), "first_sets": sets[:5]}
        if name.endswith(".xlsx") or name.endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
            return {"n_members": len(names), "first_members": names[:6]}
        if name.endswith(".h5ad"):
            import h5py

            with h5py.File(path, "r") as f:
                obs = list(f["obs"].keys())
                var = f["var"]
                first = []
                for key in ("ensembl_id", "gene_symbol"):
                    if key not in var:
                        continue
                    column = var[key]
                    if hasattr(column, "keys"):
                        raw = [column["categories"][:][i] for i in column["codes"][:3]]
                    else:
                        raw = column[:3]
                    first.append({key: [x.decode() if isinstance(x, bytes) else str(x) for x in raw]})
                shape = f["X"].attrs.get("shape") if "X" in f else None
            return {"obs_columns": obs[:30], "var_first_entries": first, "shape": [int(x) for x in shape] if shape is not None else None}
    except Exception as exc:  # pragma: no cover - reported, not hidden
        return {"schema_error": f"{type(exc).__name__}: {exc}"}
    return {}


def collect(sources=SOURCES, root: Path = ROOT) -> list[dict]:
    """Verified records: each source with its checksum, size, schema and any provenance file's own words."""
    out = []
    for source in sources:
        path = root / source["path"]
        record = {k: source.get(k, UNVERIFIED) for k in ("url", "publication", "licence")}
        record.update({k: v for k, v in source.items() if k in ("id", "role", "path", "feature_mapping", "limitations")})
        record["exists"] = path.exists()
        if source.get("provenance"):
            pv = root / source["provenance"]
            if pv.suffix == ".json" and pv.exists():
                data = json.loads(pv.read_text(encoding="utf-8"))
                record["provenance_file"] = source["provenance"]
                record["provenance_says"] = {k: data[k] for k in data if k in (
                    "release", "source_url", "url", "figshare_doi", "doi", "published_date", "retrieved_at_utc", "retrieved",
                    "licence", "license_note", "bytes", "sha256", "declared_md5", "observed_md5", "md5_match", "source", "article",
                    "acquisition_date_asia_shanghai")}
                data_url = data.get("source_url") or data.get("url")
                if data_url and record["url"] == UNVERIFIED:
                    record["url"] = data_url
                if record["licence"] == UNVERIFIED:
                    record["licence"] = data.get("licence") or data.get("license_note") or UNVERIFIED
                record["download_date"] = (data.get("retrieved_at_utc") or data.get("retrieved") or
                                           data.get("acquisition_date_asia_shanghai") or UNVERIFIED)
            elif pv.exists():
                record["provenance_file"] = source["provenance"]
        record.setdefault("download_date", UNVERIFIED)
        if path.is_file():
            size = path.stat().st_size
            record["bytes"] = size
            if size <= HASH_LIMIT:
                record["sha256"], record["checksum_source"] = sha256_file(path), "computed"
            elif source.get("recorded_sha256"):
                record["sha256"], record["checksum_source"] = source["recorded_sha256"], "recorded"
            else:
                pv_sha = (record.get("provenance_says") or {}).get("sha256")
                record["sha256"] = pv_sha or "not_computed"
                record["checksum_source"] = "recorded" if pv_sha else "not_computed"
            record["schema"] = _schema(path)
        elif path.is_dir():
            files = [p for p in path.rglob("*") if p.is_file()]
            record["bytes"] = sum(p.stat().st_size for p in files)
            record["n_files"] = len(files)
            record["sha256"] = hashlib.sha256("".join(sorted(f"{p.relative_to(path).as_posix()}:{sha256_file(p)}" for p in files
                                                             if p.stat().st_size < 50 << 20)).encode()).hexdigest()
            record["checksum_source"] = "computed_over_files_under_50MB"
        out.append(record)
    return out
