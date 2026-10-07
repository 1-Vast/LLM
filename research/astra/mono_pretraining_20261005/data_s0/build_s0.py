"""Stage S0 (before labels) for GDSC2 mono -> Jaaks anchored-combination transfer.

File summary
- Path: research/astra/mono_pretraining_20261005/data_s0/build_s0.py
- Purpose: build the S0 identity / coverage / duplicate-fit / observation-contract deliverables from METADATA ONLY.
- HARD RULE: no GDSC2 LN_IC50 / AUC / RMSE / Z_SCORE value and no Jaaks outcome column value (SYNERGY_*, LIBRARY_RMSE/EMAX/XMID/AUC,
  ANCHOR_VIABILITY, Synergy, DAY1_*, GROWTH_RATE, DOUBLING_TIME) is read. The GDSC2 workbook is parsed by a custom streaming reader that
  only resolves cell values for column indices 0-14 (identity/group/design); indices 15-18 are skipped before the value element is read.
  The Jaaks CSVs are read with an explicit design-column whitelist (`usecols`).
- Behaviour: refuses to run if any deliverable already exists (never overwrites); every file/columns access is appended to access_log.jsonl.
- Network: downloads SMALL public metadata only (Cell Model Passports model lists + compound table, DepMap documentation pages, gdscIC50
  source on GitHub, Jaaks 2022 full text + supplement table 2, PubChem identity lookups). Receipts go to source_manifest.json.
- Run: `PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/data_s0/build_s0.py`
- Interfaces: `main()`; deliverables are written next to this file.
- Depends on: pandas, numpy, requests (all in the maestro environment).
"""
from __future__ import annotations

import datetime
import gzip
import hashlib
import io
import json
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[3]
HERE = SCRIPT_DIR                       # output directory (overridable with --out DIR for dry runs outside the repo)
if "--out" in sys.argv:
    HERE = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    HERE.mkdir(parents=True, exist_ok=True)
SRC = HERE / "sources"
PROV = HERE / "provenance"
ACCESS_LOG = HERE / "access_log.jsonl"

GDSC2 = ROOT / "data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx"
GDSC2_PROV = ROOT / "data/external/gdsc2_fitted/provenance.json"
JAAKS_DIR = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare"
JAAKS_ORIG = JAAKS_DIR / "original_screen_all_tissues_fitted.csv"
JAAKS_VAL = JAAKS_DIR / "validation_screen_all_tissues_fitted.csv"
PARTITION = ROOT / "research/astra/confirmation_campaign_20261004/protocol/partition.json"
CONTEXT_DIR = ROOT / "research/astra/knowledge_transfer_20261004/context"
CONTEXT_PATHWAY_125 = CONTEXT_DIR / "pathway_125_lines.csv"
CONTEXT_PATHWAY_ALL = CONTEXT_DIR / "raw/GDSC_progeny_activities.csv"
DOCS_DIR = ROOT / "data/external/gdsc_combinations/docs"

# ---- column whitelists (identity / design / group / metadata only) --------------------------------------------------
GDSC2_META_COLS = ["DATASET", "NLME_RESULT_ID", "NLME_CURVE_ID", "COSMIC_ID", "CELL_LINE_NAME", "SANGER_MODEL_ID", "TCGA_DESC",
                   "DRUG_ID", "DRUG_NAME", "PUTATIVE_TARGET", "PATHWAY_NAME", "COMPANY_ID", "WEBRELEASE", "MIN_CONC", "MAX_CONC"]
GDSC2_OUTCOME_COLS = ["LN_IC50", "AUC", "RMSE", "Z_SCORE"]          # header names only; values are never read
JAAKS_DESIGN_COLS = ["BARCODE", "COMBI_ID", "Tissue", "CELL_LINE_NAME", "SIDM", "COSMIC_ID", "ANCHOR_ID", "ANCHOR_NAME", "ANCHOR_TARGET",
                     "ANCHOR_PATHWAY", "ANCHOR_DRUG_TYPE", "ANCHOR_Clin_Rel", "ANCHOR_CONC", "LIBRARY_ID", "LIBRARY_NAME", "LIBRARY_TARGET",
                     "LIBRARY_PATHWAY", "LIBRARY_DRUG_TYPE", "LIBRARY_Clin_Rel", "LIBRARY_CONC"]
SEED = 20261005
MONO_VAL_FRACTION_MOD = 5      # 1 of 5 entity groups -> 20% proposed mono validation (hash based, grouped)

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
UA = {"User-Agent": "MAESTRO-S0-metadata-census/1.0 (research; contact via repo owner)"}
GDSC_BIN_URL = "https://cog.sanger.ac.uk/cmp/download/"

DELIVERABLES = ["drug_identity_map.csv", "cell_identity_map.csv", "coverage_by_drug_cell.csv", "coverage_all_gdsc2_records.csv.gz",
                "coverage_count_by_drug.csv", "coverage_tissue_by_drug.csv", "ceiling_diagnostic_target_line_counts.csv",
                "fit_duplicate_groups.csv", "observation_contract.json", "source_manifest.json", "s0_facts.json",
                "jaaks_pair_coverage.csv"]


def utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log_access(path: str, columns: str, purpose: str, outcome_values_read: bool = False, note: str = "") -> None:
    rec = {"utc": utc(), "actor": "agent_B_data_s0", "phase": "build_s0.py", "file": path, "columns": columns, "purpose": purpose,
           "outcome_values_read": outcome_values_read, "note": note}
    with open(ACCESS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


# ---- GDSC2 workbook: metadata-only streaming reader --------------------------------------------------------------------
def _colidx(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_gdsc2_meta(path: Path) -> pd.DataFrame:
    """Header + columns A..O only. Cells in columns P..S (LN_IC50, AUC, RMSE, Z_SCORE) are skipped before their <v> is touched."""
    allowed = set(range(len(GDSC2_META_COLS)))
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        strings = ["".join(t.text or "" for t in si.iter(NS + "t")) for si in root.iter(NS + "si")]
        rows, header_all = [], None
        with z.open("xl/worksheets/sheet1.xml") as handle:
            for _, el in ET.iterparse(handle, events=("end",)):
                if el.tag != NS + "row":
                    continue
                vals, full_header = {}, {}
                first = header_all is None
                for c in el.iter(NS + "c"):
                    i = _colidx(c.get("r"))
                    if first:                                   # header row: names of ALL columns (names only)
                        v = c.find(NS + "v")
                        full_header[i] = strings[int(v.text)] if v is not None and c.get("t") == "s" else None
                        continue
                    if i not in allowed:
                        continue                                # outcome columns: value never read
                    v = c.find(NS + "v")
                    vals[i] = None if v is None else (strings[int(v.text)] if c.get("t") == "s" else v.text)
                if first:
                    header_all = [full_header[i] for i in sorted(full_header)]
                else:
                    rows.append([vals.get(i) for i in range(len(GDSC2_META_COLS))])
                el.clear()
    assert header_all[:15] == GDSC2_META_COLS, header_all
    assert header_all[15:] == GDSC2_OUTCOME_COLS, header_all
    return pd.DataFrame(rows, columns=GDSC2_META_COLS), header_all


# ---- downloads with receipts -------------------------------------------------------------------------------------------
def fetch(url: str, dest: Path, receipts: list, *, role: str, licence: str, version: str = "", timeout: int = 180,
          keep: bool = True, ok_status=(200,)) -> bytes | None:
    t0 = time.time()
    r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=True)
    body = r.content
    rec = {"url": url, "final_url": r.url, "http_status": r.status_code, "retrieved_utc": utc(), "bytes": len(body),
           "sha256": sha256_bytes(body), "last_modified_header": r.headers.get("last-modified"), "etag": r.headers.get("etag"),
           "role": role, "licence": licence, "version": version, "elapsed_s": round(time.time() - t0, 2),
           "stored_as": str(dest.relative_to(HERE)) if keep else None}
    receipts.append(rec)
    if r.status_code not in ok_status:
        return None
    if keep:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
    return body


def norm_name(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def tokset(s) -> set:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return set()
    return {re.sub(r"[^a-z0-9]", "", t.lower()) for t in re.split(r"[,;|/]", str(s)) if re.sub(r"[^a-z0-9]", "", t.lower())}


# ---- PubChem ---------------------------------------------------------------------------------------------------------------
def _pubchem_get(url: str, receipts_pc: list, timeout: int = 60):
    """GET with up to 5 attempts; 429/503 (ServerBusy) are retried with backoff. Every attempt is receipted."""
    r = None
    for attempt in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=timeout)
        except Exception as exc:                                # network failure is recorded, never fatal
            receipts_pc.append({"url": url, "attempt": attempt, "http_status": None, "error": type(exc).__name__, "retrieved_utc": utc()})
            time.sleep(2 * (attempt + 1))
            continue
        receipts_pc.append({"url": url, "attempt": attempt, "http_status": r.status_code, "retrieved_utc": utc(), "bytes": len(r.content),
                            "sha256": sha256_bytes(r.content), "body": r.text[:2000] if r.status_code == 200 else r.text[:300]})
        time.sleep(0.35)
        if r.status_code in (429, 503):
            time.sleep(3 * (attempt + 1))
            continue
        return r
    return r


def pubchem_lookup(name: str, receipts_pc: list) -> list[int]:
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + requests.utils.quote(name, safe="") + "/cids/JSON"
    r = _pubchem_get(url, receipts_pc)
    if r is None or r.status_code != 200:
        return []
    try:
        return [int(c) for c in r.json()["IdentifierList"]["CID"]]
    except Exception:
        return []


def pubchem_props(cids: list[int], receipts_pc: list) -> dict:
    out: dict = {}
    for i in range(0, len(cids), 50):
        chunk = cids[i:i + 50]
        url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/" + ",".join(map(str, chunk)) +
               "/property/Title,MolecularFormula,SMILES,ConnectivitySMILES,InChIKey/JSON")
        r = _pubchem_get(url, receipts_pc)
        if r is not None and r.status_code == 200:
            for p in r.json()["PropertyTable"]["Properties"]:
                out[int(p["CID"])] = p
    return out


def main() -> int:
    existing = [d for d in DELIVERABLES if (HERE / d).exists()]
    if existing or SRC.exists() or PROV.exists():
        print("REFUSING to overwrite existing S0 outputs:", existing, "sources/provenance dirs present:", SRC.exists(), PROV.exists())
        return 2
    SRC.mkdir()
    PROV.mkdir()
    t_start = utc()
    receipts: list[dict] = []
    facts: dict = {"build_started_utc": t_start, "seed": SEED, "python": sys.version.split()[0], "pandas": pd.__version__}

    # ===================================================================================================================
    # 0. Local source hashes (byte identity only)
    # ===================================================================================================================
    local_sources = []
    for p, role in [(GDSC2, "GDSC2 release 8.5 fitted dose response (identity/design columns only at S0)"),
                    (GDSC2_PROV, "receipt of the GDSC2 download"),
                    (JAAKS_ORIG, "Jaaks 2022 original screen (design columns only at S0)"),
                    (JAAKS_VAL, "Jaaks 2022 validation (re)screen (design columns only at S0)"),
                    (PARTITION, "125-line E/HD partition (line identity only)"),
                    (CONTEXT_PATHWAY_125, "PROGENy 14-pathway scores for 125 Jaaks lines (HEADER ONLY: SIDM list)"),
                    (CONTEXT_PATHWAY_ALL, "PROGENy GDSC activities for public-context SIDMs (HEADER ONLY: SIDM list)")]:
        local_sources.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "bytes": p.stat().st_size, "sha256": sha256_file(p), "role": role,
                              "kind": "local_file", "hashed_utc": utc()})
    for p in sorted(DOCS_DIR.glob("*.pdf")):
        local_sources.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "bytes": p.stat().st_size, "sha256": sha256_file(p),
                              "role": "Sanger GDSC combinations screening documentation (text read)", "kind": "local_file", "hashed_utc": utc()})
    gsha = {s["path"]: s["sha256"] for s in local_sources}
    assert gsha["data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx"] == json.loads(GDSC2_PROV.read_text())["sha256"], "GDSC2 hash != receipt"
    facts["gdsc2_sha256_matches_receipt"] = True

    # ===================================================================================================================
    # 1. Remote metadata/documentation (small files)
    # ===================================================================================================================
    cmp_latest = fetch(GDSC_BIN_URL + "model_list_latest.csv", SRC / "model_list_latest.csv", receipts,
                       role="Cell Model Passports model list (aliases, parent/sample/patient relations, synonyms)",
                       licence="Sanger DepMap data usage policy (non-exclusive internal research/educational use; no resale/commercial services)",
                       version="model_list_latest (server Last-Modified recorded)")
    cmp_2024 = fetch(GDSC_BIN_URL + "model_list_20240110.csv", SRC / "model_list_20240110.csv", receipts,
                     role="Cell Model Passports model list snapshot closest to the GDSC2 8.5 release (sensitivity for relations)",
                     licence="Sanger DepMap data usage policy", version="20240110")
    comp_tbl = fetch(GDSC_BIN_URL + "screened_compounds_rel_8.5.csv", SRC / "screened_compounds_rel_8.5.csv", receipts,
                     role="GDSC compound annotation (DRUG_ID, screening site, names, synonyms, target, pathway) for release 8.5",
                     licence="Sanger DepMap data usage policy", version="release 8.5")
    for slug, nm in [("documentation/datasets/drug-sensitivity/", "depmap_doc_drug_sensitivity.html"),
                     ("documentation/data-usage-policy/", "depmap_doc_data_usage_policy.html"),
                     ("documentation/cell-models/model-relationships/", "depmap_doc_model_relationships.html")]:
        fetch("https://depmap.sanger.ac.uk/" + slug, SRC / nm, receipts, role="Sanger DepMap documentation page (text)",
              licence="Sanger DepMap site terms", version="accessed")
    fetch("https://www.cancerrxgene.org/downloads/bulk_download", SRC / "cancerrxgene_bulk_download_status.html", receipts,
          role="legacy cancerrxgene.org bulk-download page (site now redirects to Cell Model Passports/DepMap; HTTP status is the evidence)",
          licence="n/a", ok_status=(200, 410))
    for rel in ["R/nlme_fit_stats.R", "R/nlme_fit_prep.R", "R/nlme_fit.R", "vignettes/gdscIC50.Rmd", "DESCRIPTION", "LICENSE", "README.md"]:
        fetch("https://raw.githubusercontent.com/CancerRxGene/gdscIC50/master/" + rel, SRC / ("gdscIC50_" + rel.replace("/", "_")), receipts,
              role="gdscIC50 R package source (defines LN_IC50, AUC, RMSE, x-scale, concentration units)", licence="GPL-3 (package); we only read it",
              version="master at retrieval; commit sha in gdscIC50_commit.json")
    fetch("https://api.github.com/repos/CancerRxGene/gdscIC50/commits/master", SRC / "gdscIC50_commit.json", receipts,
          role="gdscIC50 master commit identity", licence="GitHub API metadata")
    fetch("https://api.figshare.com/v2/articles/16843597", SRC / "figshare_16843597_original_screen.json", receipts,
          role="Figshare record of the Jaaks original screen file (licence, md5)", licence="Figshare metadata")
    fetch("https://api.figshare.com/v2/articles/16843600", SRC / "figshare_16843600.json", receipts,
          role="Figshare record 16843600 (Jaaks data availability list)", licence="Figshare metadata", ok_status=(200, 404))
    fetch("https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8891012/fullTextXML", SRC / "jaaks2022_PMC8891012_fulltext.xml", receipts,
          role="Jaaks et al. 2022 Nature 603:166 open-access full text (methods, ED Fig 2e statement on GDSC comparison)",
          licence="CC BY 4.0 (article)", version="PMC8891012")
    supp_zip = fetch("https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8891012/supplementaryFiles", SRC / "_supp.zip", receipts,
                     role="Jaaks 2022 supplementary files bundle (only Supplementary Table 2, cell-line metadata, is retained)",
                     licence="CC BY 4.0 (article)", version="PMC8891012", keep=False)
    supp2 = None
    if supp_zip:
        zf = zipfile.ZipFile(io.BytesIO(supp_zip))
        raw = zf.read("41586_2022_4437_MOESM5_ESM.xlsx")
        (SRC / "jaaks2022_supp_table2_cell_lines.xlsx").write_bytes(raw)
        receipts.append({"url": "(member of supplementary bundle above) 41586_2022_4437_MOESM5_ESM.xlsx", "http_status": 200, "retrieved_utc": utc(),
                         "bytes": len(raw), "sha256": sha256_bytes(raw), "role": "Jaaks Supplementary Table 2: cell-line identity/provenance columns",
                         "licence": "CC BY 4.0 (article)", "version": "PMC8891012 MOESM5", "stored_as": "sources/jaaks2022_supp_table2_cell_lines.xlsx"})
        supp2 = raw
    log_access("sources/* (downloaded)", "documentation / metadata only", "fetch public metadata and documentation with receipts")
    assert cmp_latest and cmp_2024 and comp_tbl, "required metadata downloads failed"

    ml = pd.read_csv(io.BytesIO(cmp_latest), dtype=str, low_memory=False)
    ml24 = pd.read_csv(io.BytesIO(cmp_2024), dtype=str, low_memory=False)
    comp = pd.read_csv(io.BytesIO(comp_tbl), dtype=str, keep_default_na=False)

    # ===================================================================================================================
    # 2. GDSC2 metadata (identity/design/group columns only)
    # ===================================================================================================================
    g2, g2_header = read_gdsc2_meta(GDSC2)
    log_access(str(GDSC2.relative_to(ROOT)).replace("\\", "/"),
               "header names (all 19); cell values for 15 columns DATASET..MAX_CONC; LN_IC50/AUC/RMSE/Z_SCORE cells skipped unread",
               "metadata census; identity, group, design", note="XML tokenisation touches all bytes; values for indices 15-18 are never extracted")
    facts["gdsc2_rows"] = int(len(g2))
    facts["gdsc2_header"] = g2_header
    for c in ["DRUG_NAME", "CELL_LINE_NAME", "PUTATIVE_TARGET", "PATHWAY_NAME", "SANGER_MODEL_ID", "DRUG_ID", "COSMIC_ID"]:
        s = g2[c].dropna()
        facts[f"gdsc2_{c}_has_edge_whitespace"] = int((s != s.str.strip()).sum())
    for c in ["DRUG_NAME", "CELL_LINE_NAME", "PUTATIVE_TARGET", "PATHWAY_NAME"]:
        g2[c] = g2[c].str.strip()
    g2["mn"] = g2["MIN_CONC"].astype(float)
    g2["mx"] = g2["MAX_CONC"].astype(float)
    g2["range_ratio"] = g2["mx"] / g2["mn"]
    g2["dose_range_group"] = g2["DRUG_ID"] + "|" + g2["mn"].map(lambda v: f"{v:.6g}") + "|" + g2["mx"].map(lambda v: f"{v:.6g}")
    facts.update({"gdsc2_cells": int(g2.SANGER_MODEL_ID.nunique()), "gdsc2_drug_ids": int(g2.DRUG_ID.nunique()),
                  "gdsc2_drug_names": int(g2.DRUG_NAME.nunique()), "gdsc2_nlme_result_ids": sorted(g2.NLME_RESULT_ID.unique().tolist()),
                  "gdsc2_datasets": sorted(g2.DATASET.unique().tolist()), "gdsc2_webrelease_values": sorted(g2.WEBRELEASE.unique().tolist()),
                  "gdsc2_curve_ids_unique": bool(g2.NLME_CURVE_ID.is_unique), "gdsc2_cell_drugid_pairs_repeated": int(g2.duplicated(["SANGER_MODEL_ID", "DRUG_ID"]).sum()),
                  "gdsc2_cosmic_to_sidm_one_to_one": bool(g2.groupby("COSMIC_ID").SANGER_MODEL_ID.nunique().max() == 1 and g2.groupby("SANGER_MODEL_ID").COSMIC_ID.nunique().max() == 1),
                  "gdsc2_invalid_dose_ranges": int(((g2.mn <= 0) | (g2.mx <= g2.mn)).sum()),
                  "gdsc2_company_ids_per_drug_id_max": int(g2.groupby("DRUG_ID").COMPANY_ID.nunique().max())})

    # ===================================================================================================================
    # 3. Jaaks design columns
    # ===================================================================================================================
    jo = pd.read_csv(JAAKS_ORIG, usecols=JAAKS_DESIGN_COLS, dtype=str, low_memory=False)
    jv = pd.read_csv(JAAKS_VAL, usecols=JAAKS_DESIGN_COLS, dtype=str, low_memory=False)
    for f in (JAAKS_ORIG, JAAKS_VAL):
        log_access(str(f.relative_to(ROOT)).replace("\\", "/"), ",".join(JAAKS_DESIGN_COLS),
                   "Jaaks design/identity census; no outcome columns", note="pandas usecols whitelist; ANCHOR_VIABILITY, LIBRARY_RMSE/EMAX/XMID/AUC, SYNERGY_*, Synergy, DAY1_*, GROWTH_RATE, DOUBLING_TIME not read")
    for d in (jo, jv):
        for c in ["ANCHOR_ID", "LIBRARY_ID", "SIDM", "BARCODE", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME"]:
            d[c] = d[c].str.strip()
    part = json.loads(PARTITION.read_text())["split"]
    log_access(str(PARTITION.relative_to(ROOT)).replace("\\", "/"), "split", "125 line identities and E/HD roles")
    role = {}
    for tissue, v in part.items():
        for k in ("E", "HD"):
            for s in v[k]:
                role[s] = (tissue, k)
    jaaks126 = set(jo.SIDM) | set(jv.SIDM)          # 125 original + 1 validation-only = 126 (design files)
    facts.update({"jaaks_original_rows": int(len(jo)), "jaaks_validation_rows": int(len(jv)), "jaaks_original_sidms": int(jo.SIDM.nunique()),
                  "jaaks_validation_sidms": int(jv.SIDM.nunique()), "jaaks_partition_sidms": len(role), "jaaks_union_sidms": len(jaaks126),
                  "jaaks_original_equals_partition": bool(set(jo.SIDM) == set(role)),
                  "jaaks_validation_only_sidms": sorted(set(jv.SIDM) - set(jo.SIDM)),
                  "jaaks_barcodes_original": int(jo.BARCODE.nunique()), "jaaks_barcodes_validation": int(jv.BARCODE.nunique())})

    # Jaaks Supplementary Table 2 (cell metadata) -- identity columns only
    supp2_df = read_supp_table2(supp2) if supp2 else None
    jaaks_supp_only = set(supp2_df.SIDM) - jaaks126 if supp2_df is not None else set()
    jaaks_all = jaaks126 | jaaks_supp_only          # exclusion seeds: also lines listed in the paper's Supplementary Table 2
    if supp2_df is not None:
        log_access("sources/jaaks2022_supp_table2_cell_lines.xlsx", ",".join(supp2_df.columns), "Jaaks cell-line identity / replicate flags (no response columns exist in this table)")

    # ===================================================================================================================
    # 4. Drug identity map
    # ===================================================================================================================
    pcs: list[dict] = []
    # Jaaks drug entities (anchor + library), design columns only
    parts = []
    for tag, d in (("original", jo), ("validation", jv)):
        for r in ("ANCHOR", "LIBRARY"):
            x = d[[f"{r}_ID", f"{r}_NAME", f"{r}_TARGET", f"{r}_PATHWAY", f"{r}_DRUG_TYPE", f"{r}_CONC", "Tissue", "SIDM"]].copy()
            x.columns = ["id", "name", "target", "pathway", "drug_type", "conc", "tissue", "sidm"]
            x["role"] = r.lower()
            x["screen"] = tag
            parts.append(x)
    jd = pd.concat(parts, ignore_index=True)
    jd["id"] = jd["id"].str.strip()
    gd_by_id = g2.groupby("DRUG_ID").agg(gdsc2_name=("DRUG_NAME", "first"), gdsc2_target=("PUTATIVE_TARGET", lambda s: s.dropna().iloc[0] if s.notna().any() else ""),
                                          gdsc2_pathway=("PATHWAY_NAME", "first"), n_records=("SANGER_MODEL_ID", "size"), n_cells=("SANGER_MODEL_ID", "nunique"),
                                          n_names=("DRUG_NAME", "nunique"), company_id=("COMPANY_ID", "first"),
                                          ranges=("dose_range_group", lambda s: sorted(set(s))), max_conc_set=("mx", lambda s: sorted(set(s))))
    name_to_ids = g2.groupby(g2.DRUG_NAME.str.casefold()).DRUG_ID.agg(lambda s: sorted(set(s), key=int))
    comp = comp.rename(columns=str)
    comp["DRUG_ID"] = comp["DRUG_ID"].str.strip()
    comp_by_id = comp.set_index("DRUG_ID")
    drug_rows = []
    jaaks_ids = sorted(jd["id"].unique(), key=lambda s: (("|" in s), int(s.split("|")[0])))
    # PubChem lookups: names + up to 3 synonyms per single drug present in GDSC compound table
    single_ids = [i for i in jaaks_ids if "|" not in i]
    pc_hits: dict[str, dict] = {}
    all_cids = set()
    for i in single_ids:
        jname = jd.loc[jd.id == i, "name"].iloc[0]
        syns = []
        if i in comp_by_id.index:
            syns = [s.strip() for s in re.split(r",\s*", comp_by_id.loc[i, "SYNONYMS"]) if s.strip()] if isinstance(comp_by_id.loc[i, "SYNONYMS"], str) else []
        queries = [jname] + [s for s in syns if s.casefold() != jname.casefold()][:3]
        stripped = re.sub(r"\s*\([^)]*\)", "", jname).strip()
        if stripped and stripped.casefold() != jname.casefold():
            queries.append(stripped)                              # e.g. 'Nutlin-3a (-)' -> 'Nutlin-3a' (stereo caveat is flagged separately)
        res = {}
        for q in queries:
            res[q] = pubchem_lookup(q, pcs)
        pc_hits[i] = {"queries": res}
        all_cids |= {c for v in res.values() for c in v}
    props = pubchem_props(sorted(all_cids), pcs)
    (PROV / "pubchem_receipts.jsonl").write_text("\n".join(json.dumps(r) for r in pcs) + "\n", encoding="utf-8")
    pc_total_bytes = sum(r.get("bytes", 0) or 0 for r in pcs)
    receipts.append({"url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{name|cid}/... (PUG REST; %d calls)" % len(pcs), "http_status": "mixed",
                     "retrieved_utc": utc(), "bytes": pc_total_bytes, "sha256": sha256_file(PROV / "pubchem_receipts.jsonl"),
                     "role": "PubChem identity lookups (name->CID, CID->title/SMILES/InChIKey); supporting evidence only; per-call receipts with response sha256 in provenance/pubchem_receipts.jsonl (sha256 here is of the receipt file)",
                     "licence": "NCBI/NLM PubChem data are public (https://www.ncbi.nlm.nih.gov/home/about/policies/); no restriction on use beyond citation",
                     "version": "PUG REST live at retrieval", "stored_as": "provenance/pubchem_receipts.jsonl"})

    salt_pat = re.compile(r"\b(hcl|hydrochloride|malate|mesylate|tosylate|maleate|phosphate|sodium|acetate|citrate|besylate|succinate|sulfate|dihydrochloride)\b", re.I)
    stereo_pat = re.compile(r"(\([+\-]\)|\(\s*[RS]\s*\)|\b[RS]-|\(-\)|\(\+\)|-3a|\bL-|\bD-)")
    lib_conc_by_id = jd[jd.role == "library"].groupby("id").conc.agg(lambda s: sorted(set(s), key=lambda v: float(v) if re.fullmatch(r"[0-9.eE+-]+", v) else 1e9))
    for i in jaaks_ids:
        sub = jd[jd["id"] == i]
        names = sorted(set(sub["name"]))
        tg = sorted(set(sub["target"].dropna()))
        pw = sorted(set(sub["pathway"].dropna()))
        roles = sorted(set(sub["role"]))
        row = {"jaaks_id": i, "jaaks_names": " ; ".join(names), "jaaks_roles": "+".join(roles), "jaaks_target": " ; ".join(tg), "jaaks_pathway": " ; ".join(pw),
               "jaaks_tissues": "+".join(sorted(set(sub.tissue))), "jaaks_n_design_rows_original": int(((jd.id == i) & (jd.screen == "original")).sum()),
               "jaaks_n_lines": int(sub.sidm.nunique()), "jaaks_library_conc_uM_set": " ; ".join(lib_conc_by_id.get(i, [])) if i in lib_conc_by_id.index else ""}
        if "|" in i:
            row.update({"status": "composite", "status_reason": "Composite intervention (fixed co-treatment); NOT split into single drugs; no GDSC2 single-agent mapping is defined",
                        "gdsc2_drug_id": "", "gdsc2_drug_name": "", "id_equal": False, "name_equal_casefold": False})
            drug_rows.append(row)
            continue
        cmp_row = comp_by_id.loc[i] if i in comp_by_id.index else None
        row["cmp_compound_table_present"] = cmp_row is not None
        if cmp_row is not None:
            row.update({"cmp_name": cmp_row["DRUG_NAME"], "cmp_site": cmp_row["SCREENING_SITE"], "cmp_target": cmp_row["TARGET"], "cmp_pathway": cmp_row["TARGET_PATHWAY"], "cmp_synonyms": cmp_row["SYNONYMS"]})
        pc = pc_hits[i]["queries"]
        row["pubchem_queries"] = json.dumps({k: v[:5] for k, v in pc.items()}, ensure_ascii=False)
        first_name_cids = pc.get(names[0], [])
        used_query = names[0]
        if not first_name_cids:
            for q, v in pc.items():
                if v:
                    first_name_cids, used_query = v, q
                    break
        row["pubchem_query_used_for_cid"] = used_query if first_name_cids else ""
        row["pubchem_name_cid_count"] = len(first_name_cids)
        row["pubchem_cid"] = first_name_cids[0] if first_name_cids else ""
        agree = 0
        for q, v in pc.items():
            if q != used_query and v and row["pubchem_cid"] and row["pubchem_cid"] in v[:3]:
                agree += 1
        row["pubchem_synonym_queries_agreeing"] = agree
        row["pubchem_synonym_queries_tried"] = sum(1 for q in pc if q != used_query)
        if row["pubchem_cid"] and int(row["pubchem_cid"]) in props:
            p = props[int(row["pubchem_cid"])]
            row.update({"pubchem_title": p.get("Title", ""), "pubchem_formula": p.get("MolecularFormula", ""), "pubchem_inchikey": p.get("InChIKey", ""),
                        "pubchem_smiles": p.get("SMILES", ""), "pubchem_multicomponent": "." in (p.get("SMILES", "") or "")})
        # GDSC2 relations
        if i in gd_by_id.index:
            g = gd_by_id.loc[i]
            row.update({"gdsc2_drug_id": i, "gdsc2_drug_name": g.gdsc2_name, "id_equal": True,
                        "name_equal_casefold": g.gdsc2_name.casefold().strip() == names[0].casefold().strip(),
                        "name_equal_exact": g.gdsc2_name == names[0], "gdsc2_target": g.gdsc2_target, "gdsc2_pathway": g.gdsc2_pathway,
                        "gdsc2_company_id": g.company_id, "gdsc2_n_records_all_cells": int(g.n_records), "gdsc2_n_cells_all": int(g.n_cells),
                        "gdsc2_dose_range_groups": len(g.ranges), "gdsc2_max_conc_uM_set": " ; ".join(f"{v:g}" for v in g.max_conc_set)})
            sib = [j for j in name_to_ids.get(g.gdsc2_name.casefold(), []) if j != i]
            row["gdsc2_sibling_ids_same_name"] = " ; ".join(sib)
            tj, tg2 = tokset(" ; ".join(tg)), tokset(g.gdsc2_target)
            row["target_tokens_jaaks_vs_gdsc2"] = ("gdsc2_missing" if not tg2 else ("equal" if tj == tg2 else ("overlap" if tj & tg2 else "disjoint")))
            row["pathway_equal"] = (" ; ".join(pw).strip().casefold() == g.gdsc2_pathway.strip().casefold())
            row["jaaks_library_max_conc_in_gdsc2_max_set"] = bool(i in lib_conc_by_id.index and all(
                any(abs(float(v) - m) <= 1e-6 * max(1.0, m) for m in g.max_conc_set) for v in lib_conc_by_id[i]))
            flags = []
            if sib:
                flags.append("sibling_drug_id_same_name")
            if row["target_tokens_jaaks_vs_gdsc2"] in ("disjoint",):
                flags.append("target_annotation_conflict")
            if not row["name_equal_casefold"]:
                flags.append("name_disagreement")
            syn_text = (row.get("cmp_synonyms", "") or "") + " " + names[0] + " " + g.gdsc2_name
            if salt_pat.search(syn_text):
                flags.append("salt_form_named_in_synonyms")
            if stereo_pat.search(names[0] + " " + g.gdsc2_name):
                flags.append("stereo_designator_in_name")
            if row.get("pubchem_name_cid_count", 0) and row["pubchem_name_cid_count"] > 1:
                flags.append("pubchem_name_multiple_cids")
            if re.search(r"inhibitor$", names[0], re.I):
                flags.append("generic_descriptor_name")
            if not row["pubchem_cid"]:
                flags.append("pubchem_unresolved")
                row["pubchem_support"] = "unresolved"
            else:
                tnorm = norm_name(row.get("pubchem_title", ""))
                title_ok = tnorm in {norm_name(names[0]), norm_name(g.gdsc2_name)}
                if not title_ok:
                    flags.append("pubchem_title_differs_from_name")
                if row["pubchem_synonym_queries_tried"] and row["pubchem_synonym_queries_agreeing"] == 0:
                    flags.append("pubchem_synonym_queries_disagree_or_unresolved")
                row["pubchem_support"] = ("consistent" if (title_ok or row["pubchem_synonym_queries_agreeing"] >= 1) and "generic_descriptor_name" not in flags else "unverified")
            if row.get("pubchem_multicomponent"):
                flags.append("pubchem_cid_is_salt_or_mixture")
            row["caveat_flags"] = " ; ".join(flags)
            if "name_disagreement" in flags or "target_annotation_conflict" in flags:
                row["status"], row["status_reason"] = "ambiguous", "ID equal but name/target annotation conflict"
            else:
                row["status"] = "mapped"
                row["status_reason"] = "Sanger DRUG_ID equal and names equal (same Sanger compound registry); structure/lot identity is NOT authenticated" + ("; sibling IDs share the name" if sib else "")
        else:
            alt = name_to_ids.get(names[0].casefold(), [])
            hay = comp.assign(h=(comp.DRUG_NAME + " " + comp.SYNONYMS).str.casefold())
            probe = [names[0].casefold()]
            if names[0].casefold() == "galunisertib":
                probe += ["ly2157299", "ly-2157299"]
            found = hay[hay.h.apply(lambda t: any(q in t for q in probe))].DRUG_ID.tolist()
            row["cmp_compound_table_hits_for_name_or_known_code"] = " ; ".join(found)
            row.update({"gdsc2_drug_id": "", "gdsc2_drug_name": "", "id_equal": False, "name_equal_casefold": bool(alt), "gdsc2_sibling_ids_same_name": " ; ".join(alt),
                        "status": "ambiguous" if alt else "unmapped",
                        "status_reason": ("no GDSC2 record under this ID; same name under other ID(s) -> needs adjudication" if alt else "no GDSC2 record under this DRUG_ID or name" + ("" if found else " and absent from the release-8.5 screened-compound table (name and known code searched)") + "; not in GDSC2 release 8.5")})
            row["caveat_flags"] = ""
        drug_rows.append(row)
    drug_map = pd.DataFrame(drug_rows)
    drug_map.to_csv(HERE / "drug_identity_map.csv", index=False)
    mapped_ids = set(drug_map.loc[drug_map.status == "mapped", "jaaks_id"])
    facts["drug_status_counts"] = drug_map.status.value_counts().to_dict()
    facts["jaaks_distinct_ids"] = int(len(jaaks_ids))
    facts["drug_caveat_flag_counts"] = dict(Counter(f for s in drug_map.get("caveat_flags", pd.Series(dtype=str)).fillna("") for f in s.split(" ; ") if f))
    sibling_of = {}
    for _, r in drug_map[drug_map.status == "mapped"].iterrows():
        for s in str(r.get("gdsc2_sibling_ids_same_name", "") or "").split(" ; "):
            if s:
                sibling_of[s] = r.jaaks_id
    facts["sibling_ids_of_jaaks_drugs"] = sibling_of

    # Jaaks pair coverage (design only)
    pairs = pd.concat([jo[["Tissue", "ANCHOR_ID", "LIBRARY_ID", "SIDM"]], jv[["Tissue", "ANCHOR_ID", "LIBRARY_ID", "SIDM"]]]).drop_duplicates()
    pairs["anchor_mapped"] = pairs.ANCHOR_ID.str.strip().isin(mapped_ids)
    pairs["library_mapped"] = pairs.LIBRARY_ID.str.strip().isin(mapped_ids)
    pp = pairs.groupby(["Tissue", "ANCHOR_ID", "LIBRARY_ID"]).agg(n_lines=("SIDM", "nunique"), anchor_mapped=("anchor_mapped", "first"), library_mapped=("library_mapped", "first")).reset_index()
    pp["both_mapped"] = pp.anchor_mapped & pp.library_mapped
    pp.to_csv(HERE / "jaaks_pair_coverage.csv", index=False)
    facts["jaaks_pairs_total_tissue_anchor_library"] = int(len(pp))
    facts["jaaks_pairs_both_mapped"] = int(pp.both_mapped.sum())
    facts["jaaks_pairs_by_tissue"] = {t: {"total": int(len(s)), "both_mapped": int(s.both_mapped.sum())} for t, s in pp.groupby("Tissue")}
    facts["jaaks_unique_unordered_pairs_total"] = int(pp.assign(k=pp.apply(lambda r: tuple(sorted([r.ANCHOR_ID.strip(), r.LIBRARY_ID.strip()])), axis=1)).k.nunique())

    # ===================================================================================================================
    # 5. Cell identity map + exclusion rule
    # ===================================================================================================================
    ctx_all_hdr = pd.read_csv(CONTEXT_PATHWAY_ALL, nrows=0).columns.tolist()[1:]
    log_access(str(CONTEXT_PATHWAY_ALL.relative_to(ROOT)).replace("\\", "/"), "header row only (SIDM column names)", "public-context SIDM list; no score values read")
    ctx125 = pd.read_csv(CONTEXT_PATHWAY_125, nrows=0).columns.tolist()
    log_access(str(CONTEXT_PATHWAY_125.relative_to(ROOT)).replace("\\", "/"), "header row only", "SIDM-orientation check of the 125-line context file")
    facts["context_public_sidms"] = len(ctx_all_hdr)
    ctx_set = set(ctx_all_hdr)

    # relation graph over the CMP model list(s)
    def build_graph(m: pd.DataFrame):
        edges = defaultdict(set)

        def add(a, b, k):
            if a != b:
                edges[(min(a, b), max(a, b))].add(k)
        for col, k in (("sample_id", "same_sample"), ("patient_id", "same_patient")):
            for _, grp in m.dropna(subset=[col]).groupby(col):
                ids = list(grp.model_id)
                for x in range(len(ids)):
                    for y in range(x + 1, len(ids)):
                        add(ids[x], ids[y], k)
        for _, r in m.dropna(subset=["parent_id"]).iterrows():
            add(r.model_id, r.parent_id, "parent_child")
        names = {}
        for _, r in m.iterrows():
            s = {r.model_name}
            if isinstance(r.synonyms, str):
                s |= {x.strip() for x in r.synonyms.split(";") if x.strip()}
            names[r.model_id] = s
        pats = [(mid, nm, re.compile(r"(?<![A-Za-z0-9])" + re.escape(nm) + r"(?![A-Za-z0-9])")) for mid, ss in names.items() for nm in ss if len(re.sub(r"[^A-Za-z0-9]", "", nm)) >= 4]
        for _, r in m.dropna(subset=["model_relations_comment"]).iterrows():
            for mid, nm, p in pats:
                if mid != r.model_id and p.search(r.model_relations_comment):
                    add(r.model_id, mid, "comment_mention")
        return edges, names

    edges_a, names_a = build_graph(ml)
    edges_b, names_b = build_graph(ml24)
    edges = defaultdict(set)
    for E in (edges_a, edges_b):
        for k, v in E.items():
            edges[k] |= v
    adj = defaultdict(set)
    for (a, b) in edges:
        adj[a].add(b)
        adj[b].add(a)
    all_names = defaultdict(set)
    for nn in (names_a, names_b):
        for k, v in nn.items():
            all_names[k] |= v

    def component(seed: str) -> set:
        seen, stack = {seed}, [seed]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return seen
    comp_id = {}
    for node in set(adj) | set(ml.model_id) | set(ml24.model_id):
        if node not in comp_id:
            c = component(node)
            rep = min(c)
            for n in c:
                comp_id[n] = rep
    jaaks_comp_reps = {comp_id[s] for s in jaaks_all if s in comp_id}
    # first-order evidence for each cell
    first_order: dict[str, list] = defaultdict(list)
    for (a, b), ks in edges.items():
        if (a in jaaks_all) != (b in jaaks_all):
            j, x = (a, b) if a in jaaks_all else (b, a)
            first_order[x].append((j, "|".join(sorted(ks))))
    # alias key collisions (name/synonym/COSMIC/BROAD/CCLE/RRID) between a GDSC2 cell and a Jaaks line under a different SIDM
    key_to_sidms = defaultdict(set)
    for mid, ss in all_names.items():
        for nm in ss:
            key_to_sidms[norm_name(nm)].add(mid)
    for m in (ml, ml24):
        for col in ("COSMIC_ID", "BROAD_ID", "CCLE_ID", "RRID"):
            for _, r in m.dropna(subset=[col]).iterrows():
                key_to_sidms[f"{col}:{r[col]}"].add(r.model_id)
    alias_collision = defaultdict(list)
    for k, sset in key_to_sidms.items():
        if len(sset) > 1 and (sset & jaaks_all):
            for s in sset - jaaks_all:
                alias_collision[s].append(k)
    g2_cells = g2.drop_duplicates("SANGER_MODEL_ID")[["SANGER_MODEL_ID", "COSMIC_ID", "CELL_LINE_NAME", "TCGA_DESC"]].copy()
    g2_cells["n_gdsc2_records"] = g2_cells.SANGER_MODEL_ID.map(g2.groupby("SANGER_MODEL_ID").size())
    cmp_cols = ["model_id", "model_name", "synonyms", "tissue", "cancer_type", "model_type", "parent_id", "sample_id", "patient_id", "COSMIC_ID"]
    all_sidm = sorted(set(g2_cells.SANGER_MODEL_ID) | ctx_set | jaaks_all)
    cm = pd.DataFrame({"sidm": all_sidm})
    cm = cm.merge(g2_cells.rename(columns={"SANGER_MODEL_ID": "sidm", "COSMIC_ID": "gdsc2_cosmic_id", "CELL_LINE_NAME": "gdsc2_cell_line_name", "TCGA_DESC": "gdsc2_tcga_desc"}), on="sidm", how="left")
    cm = cm.merge(ml[cmp_cols].rename(columns={"model_id": "sidm", "model_name": "cmp_model_name", "synonyms": "cmp_synonyms", "tissue": "cmp_tissue", "cancer_type": "cmp_cancer_type",
                                                 "model_type": "cmp_model_type", "parent_id": "cmp_parent_id", "sample_id": "cmp_sample_id", "patient_id": "cmp_patient_id", "COSMIC_ID": "cmp_cosmic_id"}), on="sidm", how="left")
    cm["in_gdsc2"] = cm.gdsc2_cosmic_id.notna()
    cm["in_context14_public"] = cm.sidm.isin(ctx_set)
    cm["in_jaaks_supp_table2_only"] = cm.sidm.isin(jaaks_supp_only)
    cm["in_jaaks_original"] = cm.sidm.isin(set(jo.SIDM))
    cm["in_jaaks_validation"] = cm.sidm.isin(set(jv.SIDM))
    cm["jaaks_partition_tissue"] = cm.sidm.map(lambda s: role.get(s, ("", ""))[0])
    cm["jaaks_partition_role"] = cm.sidm.map(lambda s: role.get(s, ("", ""))[1])
    cm.loc[cm.in_jaaks_validation & ~cm.in_jaaks_original, "jaaks_partition_role"] = "validation_only_not_in_125_partition"
    jt = pd.concat([jo[["SIDM", "Tissue", "CELL_LINE_NAME", "COSMIC_ID"]], jv[["SIDM", "Tissue", "CELL_LINE_NAME", "COSMIC_ID"]]]).drop_duplicates("SIDM").set_index("SIDM")
    cm["jaaks_tissue"] = cm.sidm.map(jt.Tissue)
    cm["jaaks_cell_line_name"] = cm.sidm.map(jt.CELL_LINE_NAME)
    cm["jaaks_cosmic_id"] = cm.sidm.map(jt.COSMIC_ID)
    cm["cosmic_agree_gdsc2_cmp"] = (cm.gdsc2_cosmic_id == cm.cmp_cosmic_id) | cm.gdsc2_cosmic_id.isna() | cm.cmp_cosmic_id.isna()
    cm["cosmic_agree_jaaks_gdsc2"] = (cm.jaaks_cosmic_id == cm.gdsc2_cosmic_id) | cm.jaaks_cosmic_id.isna() | cm.gdsc2_cosmic_id.isna()
    cm["in_cmp_model_list"] = cm.cmp_model_name.notna()
    cm["relation_to_jaaks_first_order"] = cm.sidm.map(lambda s: " ; ".join(f"{j}:{k}" for j, k in first_order.get(s, [])))
    cm["alias_key_collision_with_jaaks"] = cm.sidm.map(lambda s: " ; ".join(sorted(set(alias_collision.get(s, [])))))
    cm["relation_component"] = cm.sidm.map(comp_id).fillna(cm.sidm)
    cm["in_jaaks_component"] = cm.relation_component.isin(jaaks_comp_reps)
    comp_sizes = cm.groupby("relation_component").size()
    cm["component_size_in_map"] = cm.relation_component.map(comp_sizes)

    def tier(r) -> str:
        if r.sidm in jaaks_all:
            return "T1_exact_jaaks_sidm"
        if r.alias_key_collision_with_jaaks:
            return "T2_alias_key_collision"
        if r.relation_to_jaaks_first_order:
            ks = r.relation_to_jaaks_first_order
            if "same_sample" in ks or "parent_child" in ks:
                return "T3_derivative_same_sample_or_parent_child"
            if "same_patient" in ks:
                return "T4_same_patient"
            return "T5_comment_mention"
        if r.in_jaaks_component:
            return "T6_transitive_relation_component"
        return ""
    cm["exclusion_tier"] = cm.apply(tier, axis=1)
    cm["excluded_from_mono"] = cm.exclusion_tier != ""
    cm["exclusion_reason"] = cm.exclusion_tier.map({"": "", "T1_exact_jaaks_sidm": "SIDM is a Jaaks 2022 line (original screen 125, validation screen, or listed in the paper's Supplementary Table 2)",
                                                      "T2_alias_key_collision": "name/synonym/COSMIC/BROAD/CCLE/RRID key collides with a Jaaks line under a different SIDM",
                                                      "T3_derivative_same_sample_or_parent_child": "Cell Model Passports: same sample or parent/child of a Jaaks line",
                                                      "T4_same_patient": "Cell Model Passports: same patient as a Jaaks line (conservative)",
                                                      "T5_comment_mention": "Cell Model Passports relation comment names a Jaaks line (ambiguous; conservative)",
                                                      "T6_transitive_relation_component": "connected to a Jaaks line through a chain of relations (conservative)"})
    cm["ambiguous_conservatively_excluded"] = cm.exclusion_tier.isin(["T4_same_patient", "T5_comment_mention", "T6_transitive_relation_component", "T2_alias_key_collision"])
    # homonym collisions inside GDSC2 (same normalised name, different SIDM)
    gk = g2_cells.assign(k=g2_cells.CELL_LINE_NAME.map(norm_name))
    homon = set(gk[gk.k.duplicated(keep=False)].SANGER_MODEL_ID)
    cm["gdsc2_name_homonym_other_sidm"] = cm.sidm.isin(homon)
    # proposed grouped mono-validation assignment (hash of component representative; metadata only)
    def vsplit(rep: str) -> str:
        h = int(hashlib.sha256(f"mono_val_v1|{SEED}|{rep}".encode()).hexdigest()[:8], 16)
        return "val" if h % MONO_VAL_FRACTION_MOD == 0 else "train"
    cm["entity_group_id"] = cm.relation_component
    cm["proposed_mono_split"] = np.where(cm.excluded_from_mono, "excluded", cm.entity_group_id.map(vsplit))
    cm["has_gdsc2_records"] = cm.in_gdsc2
    cm["eligible_for_mono_cell_entity"] = cm.in_gdsc2 & ~cm.excluded_from_mono
    cm["eligible_with_context14"] = cm.eligible_for_mono_cell_entity & cm.in_context14_public
    cm.to_csv(HERE / "cell_identity_map.csv", index=False)
    log_access("sources/model_list_latest.csv + model_list_20240110.csv", "model_id, model_name, synonyms, tissue, cancer_type, model_type, parent_id, sample_id, patient_id, model_relations_comment, COSMIC_ID, BROAD_ID, CCLE_ID, RRID", "alias/relation graph")

    gc = cm[cm.in_gdsc2]
    facts["cells"] = {
        "gdsc2_cells": int(len(gc)), "jaaks_union_sidms": len(jaaks126), "jaaks_in_gdsc2": int(gc.sidm.isin(jaaks126).sum()),
        "cosmic_disagree_gdsc2_cmp": int((~cm.cosmic_agree_gdsc2_cmp).sum()), "cosmic_disagree_jaaks_gdsc2": int((~cm.cosmic_agree_jaaks_gdsc2).sum()),
        "gdsc2_cells_missing_from_cmp": int((gc.in_cmp_model_list == False).sum()),
        "exclusion_tier_counts_gdsc2_cells": gc.exclusion_tier.replace("", "none").value_counts().to_dict(),
        "excluded_gdsc2_cells": int(gc.excluded_from_mono.sum()), "eligible_gdsc2_cells": int(gc.eligible_for_mono_cell_entity.sum()),
        "eligible_with_context14": int(gc.eligible_with_context14.sum()),
        "eligible_without_context14": int((gc.eligible_for_mono_cell_entity & ~gc.in_context14_public).sum()),
        "context14_public_total": len(ctx_set), "context14_in_gdsc2": int(cm[cm.in_context14_public].in_gdsc2.sum()),
        "context14_in_gdsc2_not_excluded": int(cm[cm.in_context14_public & cm.in_gdsc2 & ~cm.excluded_from_mono].shape[0]),
        "context14_not_in_gdsc2": int((cm.in_context14_public & ~cm.in_gdsc2).sum()),
        "gdsc2_cells_without_context14": int((gc.in_context14_public == False).sum()),
        "jaaks_neighbours_first_order_total_in_cmp": len(first_order), "jaaks_neighbours_first_order_in_gdsc2": int(sum(1 for s in first_order if s in set(gc.sidm))),
        "relation_edge_kind_counts_all_cmp": dict(Counter(k for ks in edges.values() for k in ks)),
        "alias_key_collisions_with_jaaks_total": len(alias_collision), "alias_key_collisions_in_gdsc2": int(sum(1 for s in alias_collision if s in set(gc.sidm))),
        "gdsc2_name_homonym_pairs": sorted(gk[gk.k.duplicated(keep=False)][["SANGER_MODEL_ID", "CELL_LINE_NAME"]].values.tolist()),
        "gdsc2_cells_sharing_relation_component": int((gc.component_size_in_map > 1).sum()),
        "proposed_mono_split_counts_eligible": gc[gc.eligible_for_mono_cell_entity].proposed_mono_split.value_counts().to_dict(),
        "cmp_model_list_latest_rows": int(len(ml)), "cmp_model_list_20240110_rows": int(len(ml24)),
        "jaaks_supp_table2_sidms": None if supp2_df is None else int(supp2_df.SIDM.nunique()),
        "jaaks_supp_table2_sidms_equal_union": None if supp2_df is None else bool(set(supp2_df.SIDM) == jaaks126),
        "jaaks_supp_table2_only_sidms": sorted(jaaks_supp_only), "jaaks_design_not_in_supp_table2": sorted(jaaks126 - set(supp2_df.SIDM)) if supp2_df is not None else None,
        "jaaks_all_exclusion_seed_sidms": len(jaaks_all), "jaaks_supp_only_in_gdsc2": int(sum(1 for x in jaaks_supp_only if x in set(g2_cells.SANGER_MODEL_ID))),
        "jaaks_supp_table2_replicate_lines": None if supp2_df is None else int((supp2_df["Replicate cell line"].str.lower() == "yes").sum()),
    }
    tissue_map = {"Breast": "BRCA", "Colon": "COREAD", "Pancreas": "PAAD"}
    tcga_counts = gc.groupby("gdsc2_tcga_desc").agg(total=("sidm", "size"), jaaks=("sidm", lambda s: int(s.isin(jaaks126).sum())), eligible=("eligible_for_mono_cell_entity", "sum"))
    facts["cells"]["tcga_total_jaaks_eligible"] = {k: {kk: int(vv) for kk, vv in v.items()} for k, v in tcga_counts.to_dict("index").items()}
    cmp_t = gc.groupby("cmp_tissue").agg(total=("sidm", "size"), jaaks=("sidm", lambda s: int(s.isin(jaaks126).sum())), eligible=("eligible_for_mono_cell_entity", "sum"))
    facts["cells"]["cmp_tissue_total_jaaks_eligible"] = {k: {kk: int(vv) for kk, vv in v.items()} for k, v in cmp_t.to_dict("index").items()}

    # ===================================================================================================================
    # 6. Coverage
    # ===================================================================================================================
    cell_cols = cm.set_index("sidm")
    g2["jaaks_mapped_drug_id"] = np.where(g2.DRUG_ID.isin(mapped_ids), g2.DRUG_ID, g2.DRUG_ID.map(sibling_of).fillna(""))
    g2["record_is_id_equal_jaaks_drug"] = g2.DRUG_ID.isin(mapped_ids)
    g2["record_is_sibling_of_jaaks_drug"] = g2.DRUG_ID.isin(sibling_of)
    g2["cell_excluded"] = g2.SANGER_MODEL_ID.map(cell_cols.excluded_from_mono).astype(bool)
    g2["exclusion_tier"] = g2.SANGER_MODEL_ID.map(cell_cols.exclusion_tier)
    g2["has_context14"] = g2.SANGER_MODEL_ID.isin(ctx_set)
    g2["cmp_tissue"] = g2.SANGER_MODEL_ID.map(cell_cols.cmp_tissue)
    g2["entity_group_id"] = g2.SANGER_MODEL_ID.map(cell_cols.entity_group_id)
    g2["proposed_mono_split"] = g2.SANGER_MODEL_ID.map(cell_cols.proposed_mono_split)
    pair_counts = g2.groupby(["SANGER_MODEL_ID", g2.DRUG_NAME.str.casefold()]).DRUG_ID.transform("nunique")
    g2["same_name_multi_id_pair"] = pair_counts > 1
    g2["eligible_primary_pretrain"] = g2.record_is_id_equal_jaaks_drug & ~g2.cell_excluded & g2.has_context14
    g2["eligible_if_siblings_pooled"] = (g2.record_is_id_equal_jaaks_drug | g2.record_is_sibling_of_jaaks_drug) & ~g2.cell_excluded & g2.has_context14
    g2["eligible_no_context_requirement"] = g2.record_is_id_equal_jaaks_drug & ~g2.cell_excluded
    g2["jaaks_line_own_mono_diagnostic_only"] = g2.record_is_id_equal_jaaks_drug & g2.SANGER_MODEL_ID.isin(jaaks126)
    out_cols = {"SANGER_MODEL_ID": "sidm", "COSMIC_ID": "cosmic_id", "CELL_LINE_NAME": "cell_line_name", "TCGA_DESC": "tcga_desc", "cmp_tissue": "cmp_tissue",
                "DRUG_ID": "drug_id", "DRUG_NAME": "drug_name", "jaaks_mapped_drug_id": "jaaks_drug_id", "NLME_CURVE_ID": "nlme_curve_id",
                "mn": "min_conc_uM", "mx": "max_conc_uM", "dose_range_group": "dose_range_group", "cell_excluded": "cell_excluded_from_mono",
                "exclusion_tier": "exclusion_tier", "has_context14": "has_context14", "entity_group_id": "entity_group_id",
                "proposed_mono_split": "proposed_mono_split", "same_name_multi_id_pair": "same_name_multi_id_pair",
                "record_is_sibling_of_jaaks_drug": "sibling_id_record", "eligible_primary_pretrain": "eligible_primary_pretrain",
                "eligible_if_siblings_pooled": "eligible_if_siblings_pooled", "eligible_no_context_requirement": "eligible_no_context_requirement",
                "jaaks_line_own_mono_diagnostic_only": "NOT_ELIGIBLE_target_line_own_mono_diagnostic_only"}
    cov = g2[g2.record_is_id_equal_jaaks_drug | g2.record_is_sibling_of_jaaks_drug][list(out_cols)].rename(columns=out_cols)
    cov.to_csv(HERE / "coverage_by_drug_cell.csv", index=False)
    allrec = g2[list(out_cols)].rename(columns=out_cols)
    allrec.to_csv(HERE / "coverage_all_gdsc2_records.csv.gz", index=False, compression="gzip")

    cnt = []
    for did in sorted(mapped_ids, key=int):
        s = g2[g2.DRUG_ID == did]
        sib = [k for k, v in sibling_of.items() if v == did]
        sib_s = g2[g2.DRUG_ID.isin(sib)]
        cnt.append({"jaaks_drug_id": did, "drug_name": s.DRUG_NAME.iloc[0] if len(s) else "", "records_all_cells": len(s), "cells_all": s.SANGER_MODEL_ID.nunique(),
                    "records_jaaks_lines": int(s.SANGER_MODEL_ID.isin(jaaks126).sum()), "records_other_excluded": int((s.cell_excluded & ~s.SANGER_MODEL_ID.isin(jaaks126)).sum()),
                    "records_after_exclusion": int((~s.cell_excluded).sum()), "records_eligible_no_context_req": int(s.eligible_no_context_requirement.sum()),
                    "records_eligible_primary": int(s.eligible_primary_pretrain.sum()), "cells_eligible_primary": int(s[s.eligible_primary_pretrain].SANGER_MODEL_ID.nunique()),
                    "dose_range_groups_all": s.dose_range_group.nunique(), "dose_range_groups_eligible": s[s.eligible_primary_pretrain].dose_range_group.nunique(),
                    "sibling_ids": " ; ".join(sib), "sibling_records_eligible_if_pooled": int(sib_s.eligible_if_siblings_pooled.sum()),
                    "eligible_primary_proposed_train": int((s.eligible_primary_pretrain & (s.proposed_mono_split == "train")).sum()),
                    "eligible_primary_proposed_val": int((s.eligible_primary_pretrain & (s.proposed_mono_split == "val")).sum()),
                    "eligible_primary_in_BRCA_COREAD_PAAD": int((s.eligible_primary_pretrain & s.TCGA_DESC.isin(["BRCA", "COREAD", "PAAD"])).sum())})
    cnt = pd.DataFrame(cnt)
    cnt.to_csv(HERE / "coverage_count_by_drug.csv", index=False)
    el = g2[g2.eligible_primary_pretrain]
    t1 = el.groupby(["DRUG_ID", "DRUG_NAME", "TCGA_DESC"]).size().rename("records").reset_index()
    t1.to_csv(HERE / "coverage_tissue_by_drug.csv", index=False)
    # ceiling diagnostic: counts only
    jl = g2[g2.record_is_id_equal_jaaks_drug & g2.SANGER_MODEL_ID.isin(jaaks126)]
    jl_t = jl.merge(jt.reset_index().rename(columns={"SIDM": "SANGER_MODEL_ID", "Tissue": "jaaks_tissue"})[["SANGER_MODEL_ID", "jaaks_tissue"]], on="SANGER_MODEL_ID")
    ce = jl_t.groupby(["DRUG_ID", "DRUG_NAME", "jaaks_tissue"]).SANGER_MODEL_ID.nunique().unstack(fill_value=0)
    ce["lines_total"] = ce.sum(axis=1)
    ce.insert(0, "FLAG", "NOT_ELIGIBLE_FOR_PRIMARY_PRETRAINING__target_line_own_mono_ceiling_diagnostic_only__counts_only")
    ce.reset_index().to_csv(HERE / "ceiling_diagnostic_target_line_counts.csv", index=False)
    per_line = jl.groupby("SANGER_MODEL_ID").DRUG_ID.nunique()
    facts["coverage"] = {
        "records_all": int(len(g2)), "records_jaaks_drugs_id_equal_all_cells": int(g2.record_is_id_equal_jaaks_drug.sum()),
        "records_jaaks_drugs_after_exclusion": int((g2.record_is_id_equal_jaaks_drug & ~g2.cell_excluded).sum()),
        "records_jaaks_drugs_in_excluded_cells": int((g2.record_is_id_equal_jaaks_drug & g2.cell_excluded).sum()),
        "eligible_primary_records": int(g2.eligible_primary_pretrain.sum()), "eligible_primary_cells": int(g2[g2.eligible_primary_pretrain].SANGER_MODEL_ID.nunique()),
        "eligible_primary_drugs": int(g2[g2.eligible_primary_pretrain].DRUG_ID.nunique()),
        "eligible_no_context_requirement_records": int(g2.eligible_no_context_requirement.sum()),
        "eligible_no_context_requirement_cells": int(g2[g2.eligible_no_context_requirement].SANGER_MODEL_ID.nunique()),
        "eligible_if_siblings_pooled_records": int(g2.eligible_if_siblings_pooled.sum()),
        "sibling_records_in_eligible_cells": int((g2.record_is_sibling_of_jaaks_drug & ~g2.cell_excluded & g2.has_context14).sum()),
        "per_drug_eligible_range": [int(cnt.records_eligible_primary.min()), int(cnt.records_eligible_primary.max())],
        "per_drug_eligible_median": float(cnt.records_eligible_primary.median()),
        "eligible_in_BRCA_COREAD_PAAD_records": int((g2.eligible_primary_pretrain & g2.TCGA_DESC.isin(["BRCA", "COREAD", "PAAD"])).sum()),
        "eligible_in_BRCA_COREAD_PAAD_cells": int(g2[g2.eligible_primary_pretrain & g2.TCGA_DESC.isin(["BRCA", "COREAD", "PAAD"])].SANGER_MODEL_ID.nunique()),
        "eligible_cells_by_tcga": g2[g2.eligible_primary_pretrain].drop_duplicates("SANGER_MODEL_ID").TCGA_DESC.fillna("NA").value_counts().to_dict(),
        "eligible_records_by_tcga": g2[g2.eligible_primary_pretrain].TCGA_DESC.fillna("NA").value_counts().to_dict(),
        "jaaks_lines_with_any_mono_record_of_63": int(jl.SANGER_MODEL_ID.nunique()), "jaaks_line_records_63drugs": int(len(jl)),
        "jaaks_line_drugs_per_line_min_median_max": [int(per_line.min()), float(per_line.median()), int(per_line.max())],
        "same_name_multi_id_records_total": int(g2.same_name_multi_id_pair.sum()),
        "proposed_split_eligible_records": g2[g2.eligible_primary_pretrain].proposed_mono_split.value_counts().to_dict(),
        "proposed_split_eligible_cells": g2[g2.eligible_primary_pretrain].drop_duplicates("SANGER_MODEL_ID").proposed_mono_split.value_counts().to_dict(),
        "context_orphans_eligible_cells_without_context": int(g2[g2.record_is_id_equal_jaaks_drug & ~g2.cell_excluded & ~g2.has_context14].SANGER_MODEL_ID.nunique()),
    }

    # ===================================================================================================================
    # 7. Fit / duplicate groups
    # ===================================================================================================================
    fd = []
    fd.append({"group_type": "joint_nlme_fit", "group_key": f"NLME_RESULT_ID={','.join(map(str, sorted(g2.NLME_RESULT_ID.unique())))}|DATASET={','.join(sorted(g2.DATASET.unique()))}",
               "sidm": "", "drug_name": "", "drug_ids": "", "nlme_curve_ids": "", "dose_ranges": "", "n_records": int(len(g2)), "n_cells": int(g2.SANGER_MODEL_ID.nunique()), "n_drug_ids": int(g2.DRUG_ID.nunique()),
               "note": "ALL records belong to ONE NLME fit (NLME_RESULT_ID constant): fitted LN_IC50/AUC are jointly estimated across every cell x compound (docs: complete set fitted simultaneously; scale parameter varies by cell, position by cell and compound). Fitted-parameter transfer, not independent observations."})
    fd.append({"group_type": "curve_id_uniqueness", "group_key": "NLME_CURVE_ID", "sidm": "", "drug_name": "", "drug_ids": "", "nlme_curve_ids": "", "dose_ranges": "",
               "n_records": int(len(g2)), "n_cells": int(g2.SANGER_MODEL_ID.nunique()), "n_drug_ids": int(g2.DRUG_ID.nunique()),
               "note": f"NLME_CURVE_ID unique per record: {bool(g2.NLME_CURVE_ID.is_unique)}; (cell, DRUG_ID) pairs repeated: {int(g2.duplicated(['SANGER_MODEL_ID','DRUG_ID']).sum())}. One fitted curve per (cell, DRUG_ID); technical replicate wells are merged inside the fit and are not separate rows."})
    multi = g2[g2.same_name_multi_id_pair].copy()
    for (sidm, nm), s in multi.groupby(["SANGER_MODEL_ID", multi.DRUG_NAME.str.casefold()]):
        fd.append({"group_type": "same_drug_name_multiple_drug_ids", "group_key": f"{sidm}|{nm}", "sidm": sidm, "drug_name": s.DRUG_NAME.iloc[0],
                   "drug_ids": " ; ".join(s.DRUG_ID), "nlme_curve_ids": " ; ".join(s.NLME_CURVE_ID), "dose_ranges": " ; ".join(s.dose_range_group),
                   "n_records": len(s), "n_cells": 1, "n_drug_ids": s.DRUG_ID.nunique(),
                   "note": "same compound name under >1 DRUG_ID in the same cell: different registered stocks/ranges ('internal tracking' per DepMap docs); repeated measurement of the same drug; keep in one split"})
    for grp, s in g2.groupby("dose_range_group"):
        fd.append({"group_type": "dose_range_design_group", "group_key": grp, "sidm": "", "drug_name": s.DRUG_NAME.iloc[0], "drug_ids": s.DRUG_ID.iloc[0], "nlme_curve_ids": "",
                   "dose_ranges": f"min={s.mn.iloc[0]:.6g}uM max={s.mx.iloc[0]:.6g}uM", "n_records": len(s), "n_cells": s.SANGER_MODEL_ID.nunique(), "n_drug_ids": 1,
                   "note": "records sharing DRUG_ID + MIN_CONC + MAX_CONC = same dose-range design (proxy for screening campaign/library layout; barcodes/dates are not in the file)"})
    pd.DataFrame(fd).to_csv(HERE / "fit_duplicate_groups.csv", index=False)
    rr = g2.range_ratio.round(0)
    facts["fit"] = {
        "same_name_multi_id_pair_records": int(g2.same_name_multi_id_pair.sum()), "same_name_multi_id_pairs": int(g2[g2.same_name_multi_id_pair].groupby(["SANGER_MODEL_ID", g2.DRUG_NAME.str.casefold()]).ngroups),
        "drug_names_with_multiple_ids": {k: v for k, v in g2.groupby("DRUG_NAME").DRUG_ID.agg(lambda s: sorted(set(s), key=int)).items() if len(v) > 1},
        "dose_range_groups_total": int(g2.dose_range_group.nunique()),
        "drug_ids_with_multiple_ranges": int((g2.groupby("DRUG_ID").dose_range_group.nunique() > 1).sum()),
        "drug_ids_total": int(g2.DRUG_ID.nunique()),
        "max_conc_distinct_within_drug_id_gt1": int((g2.groupby("DRUG_ID").mx.nunique() > 1).sum()),
        "range_ratio_top": {str(int(k)): int(v) for k, v in rr.value_counts().head(12).items()},
        "range_ratio_min_max": [float(g2.range_ratio.min()), float(g2.range_ratio.max())],
        "mn_distinct_within_drug_id_gt1": int((g2.groupby("DRUG_ID").mn.nunique() > 1).sum()),
        "company_ids": g2.COMPANY_ID.value_counts().to_dict(),
    }
    # Jaaks library concentration design vs GDSC2 max conc (design columns only)
    match = drug_map[(drug_map.status == "mapped")].get("jaaks_library_max_conc_in_gdsc2_max_set")
    facts["jaaks_library_conc_design_in_gdsc2_max_conc_set_true_of_mapped"] = [int(match.sum()), int(match.notna().sum())] if match is not None else None

    # ===================================================================================================================
    # 8. Manifest + contract
    # ===================================================================================================================
    facts["build_finished_utc"] = utc()
    (HERE / "s0_facts.json").write_text(json.dumps(facts, indent=1, default=str), encoding="utf-8")
    manifest = {"stage": "S0", "built_utc": facts["build_finished_utc"], "script": "research/astra/mono_pretraining_20261005/data_s0/build_s0.py",
                "script_sha256": sha256_file(Path(__file__).resolve()), "local_sources": local_sources, "remote_sources": receipts,
                "pubchem_calls": len(pcs), "licence_summary": {
                    "GDSC2_and_CMP_and_DepMap": "Sanger DepMap Data Usage Policy: non-exclusive, non-transferable right to use data files for internal proprietary research and educational purposes (incl. target, biomarker, drug discovery); excluded: resale alone or in combination with other data/product offerings, provision of commercial services; data provided as-is. Commercial use needs consent (depmap@sanger.ac.uk). The GDSC2 workbook itself carries no embedded licence text (verified only via the site policy).",
                    "Jaaks_2022_figshare_16843597": "Figshare licence field CC BY 4.0; record description repeats the Sanger internal-research-use wording above (the two statements differ; treat the stricter as binding).",
                    "Jaaks_article": "CC BY 4.0", "gdscIC50": "GPL-3 (source read only)", "PubChem": "public NCBI data"}}
    (HERE / "source_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    # observation contract (data-derived facts are pulled from the computed objects; prose rules are fixed text)
    contract = build_contract(facts, g2)
    (HERE / "observation_contract.json").write_text(json.dumps(contract, indent=1), encoding="utf-8")
    print(json.dumps({k: facts[k] for k in ("gdsc2_rows", "gdsc2_cells", "gdsc2_drug_ids", "drug_status_counts")}, indent=1))
    print(json.dumps(facts["coverage"], indent=1, default=str))
    print(json.dumps(facts["cells"], indent=1, default=str)[:4000])
    return 0


def read_supp_table2(raw: bytes) -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(raw))
    ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = ["".join(t.text or "" for t in si.iter(NS + "t")) for si in ss.iter(NS + "si")]
    rows = []
    with z.open("xl/worksheets/sheet1.xml") as h:
        for _, el in ET.iterparse(h, events=("end",)):
            if el.tag == NS + "row":
                d = {}
                for c in el.iter(NS + "c"):
                    v = c.find(NS + "v")
                    d[_colidx(c.get("r"))] = None if v is None else (strings[int(v.text)] if c.get("t") == "s" else v.text)
                rows.append([d.get(i) for i in range(max(d) + 1)] if d else [])
                el.clear()
    hdr = rows[0]
    df = pd.DataFrame([r + [None] * (len(hdr) - len(r)) for r in rows[1:] if r], columns=hdr)
    keep = ["Tissue", "Cell line", "SIDM", "COSMIC ID", "Replicate cell line", "In validation screen", "Supplier:Cat.No.", "Screen Media"]
    return df[keep]


def build_contract(f: dict, g2: pd.DataFrame) -> dict:
    return {
        "stage": "S0", "status": "DESIGN_CONTRACT_NO_OUTCOME_VALUES_READ", "built_utc": f["build_finished_utc"],
        "source": {"file": "GDSC2_fitted_dose_response_27Oct23.xlsx", "release": "GDSC release 8.5 (file dated 27Oct23)", "sha256": "f950a7027be265f8a7a74220a27fd18cbd368485349bd8c2048e88bb1cd07560",
                   "rows": f["gdsc2_rows"], "cells": f["gdsc2_cells"], "drug_ids": f["gdsc2_drug_ids"], "dataset": f["gdsc2_datasets"], "webrelease": f["gdsc2_webrelease_values"]},
        "assay": {"endpoint": "cell viability by metabolic assay CellTiter-Glo (ATP luminescence); GDSC1 used Resazurin/Syto60 and is NOT this file",
                  "duration_h": 72, "format": "1536-well plates, Echo555 acoustic dispensing, drugging 24 h after seeding, RPMI or DMEM/F12 with 10% FBS",
                  "dose_formats": "7-point curves: half-log steps (1000-fold) or 2x2-fold then 4x4-fold (1024-fold); per-row MIN_CONC/MAX_CONC give the realised range",
                  "negative_control": "DMSO/medium-treated cells", "positive_control": "blank wells (medium, no cells)",
                  "normalisation": "per-plate viability = (treated - blank)/(negative control - blank)", "source": "Sanger DepMap documentation page Drug Sensitivity (retrieved 2026-10-04) and gdscIC50 vignette"},
        "fitting": {"method": "non-linear mixed-effects (NLME) two-parameter logistic of Vis et al. 2016, R package gdscIC50 (GPL-3, v0.99.4 at master commit recorded in sources/gdscIC50_commit.json)",
                    "joint_fit": f"NLME_RESULT_ID is constant ({f['gdsc2_nlme_result_ids']}) -> one joint fit over all cell x compound series; scale varies by cell model only, position (xmid) by cell model and compound; replicates of one cell+compound are pooled into one curve",
                    "independence": "fitted records are NOT independent observations: they share the joint model (borrowing strength). Treat as fitted-parameter transfer; split by cell entity so one cell's shape/position parameters stay on one side",
                    "x_scale": "x = log2(conc / maxc) + 9, so MAX_CONC is x=9 (gdscIC50 getXfromConc/getConcFromX)", "drug_level_specifier": "drug = DRUG_ID plus maxc by default: different MAX_CONC of the same DRUG_ID are different drug-level models"},
        "LN_IC50": {"definition": "natural log of the fitted IC50 (xmid) converted to micromolar: LN_IC50 = log(maxc * 2^(xmid - 9)), maxc in micromolar (gdscIC50 R/nlme_fit_stats.R calcIC50 + getConcFromX; plot axis label 'log_e uM')",
                    "unit": "ln(micromolar); IC50 = exp(LN_IC50) uM", "relative_form": "LN_IC50 - ln(MAX_CONC) = (xmid - 9) * ln 2, i.e. a dose-range-normalised potency in natural-log units; computed from MIN_CONC/MAX_CONC design columns only",
                    "documented_in": ["DepMap docs: 'LN_IC50 Natural log of the fitted IC50'; 'MIN_CONC/MAX_CONC: minimum/maximum micromolar screening concentration of the drug within the dataset'", "gdscIC50 source (formula)"],
                    "verification_status": "documentation/source-level verified; VALUE-LEVEL check (fraction of LN_IC50 inside [ln MIN_CONC, ln MAX_CONC], sanity on known potent compounds) is DEFERRED to S1 after FREEZE because it needs outcome values",
                    "jaaks_library_ic50_scale": "Jaaks LIBRARY_XMID_uM is IC50 in uM; its LIBRARY_XMID is log2-scale relative to the library range -1..9 (glossary) -> comparable form (log2 uM) differs by constant ln2 factors; not read at S0"},
        "out_of_range_ic50": {"documented_behaviour": "The fit is a sigmoid; xmid is a model parameter and is NOT clipped to the tested range. An IC50 beyond MAX_CONC is an extrapolation of the fitted curve, not an observed threshold. No censoring flag exists in the file.",
                              "evidence": "gdscIC50 code computes IC50 from xmid with no clipping; DepMap docs mention no censoring; protocol 'do_not_infer' list",
                              "design_columns_for_flag": "out_of_range_high := LN_IC50 > ln(MAX_CONC); out_of_range_low := LN_IC50 < ln(MIN_CONC) (to be computed at S1 from values + design columns)",
                              "handling_rule": "keep the fitted value as the label but carry the flag; report model error separately for in-range vs extrapolated rows; do not convert to right-censored data and do not drop silently; a sensitivity arm clips LN_IC50 to [ln MIN, ln MAX] (a recorded alternative, not the primary)"},
        "author_QC": {"RMSE": "root mean squared error of the fitted curve against the viability points; DepMap docs: 'Curves with RMSE > 0.3 are excluded prior to release as part of quality control' -> every released row already passed RMSE <= 0.3 (documented; unverified at S0)",
                      "Z_SCORE": "z of LN_IC50 vs mean/SD of that drug over all models in the dataset (descriptive; NOT a QC filter; depends on the cell panel and on the drug-ID's dose-range mixture)",
                      "plate_QC": "plates with failed controls are excluded upstream (gdscIC50 removeFailedDrugs 'FAIL' tag); thresholds for GDSC2 plates are not in the file. The Jaaks screening documentation lists CV<=0.18 and Z-factor>=0.3 for the combination screen; GDSC2 plate thresholds are not documented in the files read.",
                      "no_additional_filter_at_S0": "S1 may apply the documented RMSE <= 0.3 only as an assertion check; any stricter RMSE filter (e.g. Jaaks-style 0.2) must be declared in the freeze with the number of rows it drops"},
        "comparability_across_drugs": {"statement": "Raw LN_IC50 is NOT comparable across drugs: it is an absolute potency in each drug's own units and bounded in practice by that drug's screened range (ln MIN..ln MAX); ranges differ by up to orders of magnitude (see fit_duplicate_groups.csv).",
                                       "handling": ["primary label: dose-range-normalised potency y = (LN_IC50 - ln(MAX_CONC)) / ln 2 = xmid - 9 (log2 steps below the top dose); uses ONLY design columns MAX_CONC; removes the dose-range offset between drugs and between ranges of one drug",
                                                    "then standardise per drug within the mono TRAINING fold only (mean, SD from training cells), parameters exported; never from validation or Jaaks lines",
                                                    "drug-wise random effect b_a absorbs residual drug offset; cross-drug ranking is not claimed from mono labels",
                                                    "records of one DRUG_ID with different MAX_CONC are different dose-range groups; the xmid-9 normalisation handles the offset but the group id is carried as a covariate or the drug standardisation is done per dose-range group when a group has >= 30 training cells"]},
        "recommended_primary_mono_target": {"choice": "y_rel = (LN_IC50 - ln MAX_CONC)/ln 2 (= xmid - 9), standardised per drug on training cells; AUC reported as a secondary target",
                                            "rationale": ["it is the quantity actually modelled by the NLME fit (xmid) and is invariant to the arbitrary top-dose choice", "AUC (fraction of area between lowest and highest tested conc) is bounded in [0,1], never extrapolated, but is range dependent (a drug screened up to its toxic ceiling vs a narrow range gives different AUC for the same biology) and loses potency resolution for inactive drugs",
                                                          "the Jaaks action contrast is a within-cell comparison across drugs; a range-normalised potency retains within-cell ordering information better than raw ln uM when top doses differ; it also matches Jaaks LIBRARY_XMID (log2 scale relative to the library range)",
                                                          "decision only: no values were read, no choice between candidates was made on performance"],
                                            "secondary": ["AUC", "raw LN_IC50 (diagnostic only)"], "forbidden": ["adding mono IC50/AUC to a synergy score", "treating extrapolated IC50 as observed threshold"]},
        "licence": {"summary": "Sanger DepMap Data Usage Policy: non-exclusive, non-transferable, internal proprietary research and educational use; excludes resale (alone or combined) and commercial services; as-is; commercial use needs prior consent. Research use in this repo is compatible; any redistribution of derived files must keep this notice.", "source_url": "https://depmap.sanger.ac.uk/documentation/data-usage-policy/"},
        "unknown_at_S0": ["whether any LN_IC50 is missing/non-finite (needs values)", "per-row RMSE (needs values)", "screening dates/barcodes of GDSC2 plates (not in the file)", "lot/vendor identity of compounds vs the Jaaks stocks", "whether fitted values were later revised across releases"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
