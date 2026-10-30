"""R204-DATA4 scout: public multi-time functional/population-snapshot resource retrieval and D1-D7 qualification.

This script is OFFLINE verification/reporting: downloads were performed via public HTTPS/FTP
(recorded in receipts/ and record_data4.md). It reads only local metadata files and, for the
local Mix-seq h5ad, obs/var metadata only (never X values, never response/function values).
It does NOT run effects, fit models, or read response values.

Outputs: scout_data4.json (deterministic; sort_keys; no timestamps).
"""
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REC = os.path.join(HERE, "receipts")
OUT = os.path.join(HERE, "scout_data4.json")
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")

INPUTS = {
    "PROBLEM_M2_STAGE2_v0_2.md": os.path.join(ROOT, "research", "2026-10-28-m2-stage2-prep", "PROBLEM_M2_STAGE2_v0_2.md"),
    "DESIGN_M2_STAGE2_v0_2.md": os.path.join(ROOT, "research", "2026-10-28-m2-stage2-prep", "DESIGN_M2_STAGE2_v0_2.md"),
    "DECISION_R204_M2_STAGE2_ACCEPT.md": os.path.join(ROOT, "research", "2026-10-28-m2-stage2-prep", "DECISION_R204_M2_STAGE2_ACCEPT.md"),
    "report_data1.md": os.path.join(ROOT, "research", "2026-10-28-az-data-acquisition", "report_data1.md"),
    "report_data2.md": os.path.join(ROOT, "research", "2026-10-28-az-code-hunt", "report_data2.md"),
    "BRIEF_R204.md": os.path.join(ROOT, "research", "2026-10-28-deep-coupling-redesign", "BRIEF_R204.md"),
    "report_R204.md": os.path.join(ROOT, "research", "2026-10-28-deep-coupling-redesign", "report.md"),
    "ERRATA_R201_R202.md": os.path.join(ROOT, "research", "2026-10-27-agent-cell-colearning", "ERRATA_R201_R202.md"),
}
PROTOCOL = os.path.join(HERE, "PROTOCOL_DATA4.md")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def file_meta(path, url=""):
    return {"path": os.path.relpath(path, ROOT).replace(os.sep, "/"),
            "url": url,
            "present": os.path.exists(path),
            "bytes": os.path.getsize(path) if os.path.exists(path) else None,
            "sha256": sha256_file(path) if os.path.exists(path) else None}


def read_gz_text(name, max_lines=None):
    p = os.path.join(REC, name)
    with gzip.open(p, "rt", errors="replace") as f:
        if max_lines is None:
            return f.read()
        return "".join([next(f) for _ in range(max_lines)])


def gz_lines(name, limit=120):
    p = os.path.join(REC, name)
    out = []
    with gzip.open(p, "rt", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            out.append(line.rstrip("\n"))
    return out


def series_meta(name):
    """Parse GEO series matrix header fields + sample titles."""
    p = os.path.join(REC, name)
    meta = {}
    samples = []
    with gzip.open(p, "rt", errors="replace") as f:
        for line in f:
            if line.startswith("!Series_title"):
                meta["title"] = line.split("\t", 1)[1].strip().strip('"')
            elif line.startswith("!Series_summary"):
                meta.setdefault("summary", []).append(line.split("\t", 1)[1].strip().strip('"'))
            elif line.startswith("!Series_overall_design"):
                meta["overall_design"] = line.split("\t", 1)[1].strip().strip('"')
            elif line.startswith("!Sample_title"):
                samples = [x.strip().strip('"') for x in line.rstrip("\n").split("\t")[1:]]
    meta["sample_titles"] = samples
    return meta


def main():
    out = {
        "meta": {
            "task": "task-172 R204-DATA4 public multi-time functional/population-snapshot retrieval and D1-D7 qualification",
            "protocol_sha256": sha256_file(PROTOCOL),
            "date": "2026-10-28",
            "mode": "bounded retrieval + public download + structural-only verification",
            "effect_run": False,
            "model_fit": False,
            "response_values_read_for_effect": False,
            "download_limit_bytes_per_file": 500 * 1024 * 1024,
            "login_or_license_bypass": False,
            "claims": "no novelty/migration/decision-benefit/mechanism claims; bounded search (not 'does not exist')",
        },
        "inputs_sha256": {},
        "downloads": {},
        "search_log": {},
        "candidates": {},
        "overall": {},
    }
    for k, p in INPUTS.items():
        out["inputs_sha256"][k] = file_meta(p)
    out["local_mixseq"] = file_meta(H5AD, "local scPerturb asset; no download this task")

    # ---------- downloaded receipts registry (public URLs used) ----------
    registry = [
        # GSE214965 (DRUG-Seq, 2 time points, 20 drugs, LN-229)
        ("GSE214965_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214965/matrix/GSE214965_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE214965_sample_metadata_LN229_DRUG_Seq.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214965/suppl/GSE214965_sample_metadata_LN229_DRUG_Seq.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE214965_rawcounts_LN229_DRUG_Seq.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214965/suppl/GSE214965_rawcounts_LN229_DRUG_Seq.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        # GSE139944 (sci-Plex; small metadata only; big matrices not downloaded)
        ("GSE139944-GPL21697_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/matrix/GSE139944-GPL21697_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE139944-GPL24625_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/matrix/GSE139944-GPL24625_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE139944-GPL24676_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/matrix/GSE139944-GPL24676_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE139944_filelist.txt", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/suppl/filelist.txt", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSM4150377_sciPlex2_pData.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150377/suppl/GSM4150377_sciPlex2_pData.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSM4150377_sciPlex2_hashSampleSheet.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150377/suppl/GSM4150377_sciPlex2_hashSampleSheet.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSM4150378_sciPlex3_pData.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150378/suppl/GSM4150378_sciPlex3_pData.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSM4150378_sciPlex3_hashSampleSheet.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150378/suppl/GSM4150378_sciPlex3_hashSampleSheet.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSM4150378_sciPlex3_screen_cell.annotations.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150378/suppl/GSM4150378_sciPlex3_A549_MCF7_K562_screen_cell.annotations.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSM4150379_sciPlex4_pData.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150379/suppl/GSM4150379_sciPlex4_pData.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        # Tahoe-100M metadata (public CC0; large parquet not downloaded)
        ("Tahoe_sample_metadata.parquet", "https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/main/metadata/sample_metadata.parquet", "CC0-1.0", False),
        ("Tahoe_drug_metadata.parquet", "https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/main/metadata/drug_metadata.parquet", "CC0-1.0", False),
        ("Tahoe_cell_line_metadata.parquet", "https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/main/metadata/cell_line_metadata.parquet", "CC0-1.0", False),
        ("Tahoe_README.md", "https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/main/README.md", "CC0-1.0", False),
        ("Tahoe_LICENSE.md", "https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/main/LICENSE.md", "CC0-1.0", False),
        # X-Atlas/Orion metadata (CC-BY-NC-SA; large parquet not downloaded)
        ("XAtlas_README.md", "https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion/resolve/main/README.md", "CC-BY-NC-SA-4.0", False),
        ("XAtlas_LICENSE.md", "https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion/resolve/main/LICENSE.md", "CC-BY-NC-SA-4.0", False),
        # HF API metadata snapshots (public)
        ("Xaira-Therapeutics__X-Atlas-Orion.api.json", "https://huggingface.co/api/datasets/Xaira-Therapeutics/X-Atlas-Orion", "public API metadata", False),
        ("tahoebio__Tahoe-100M.api.json", "https://huggingface.co/api/datasets/tahoebio/Tahoe-100M", "public API metadata", False),
        # GEO search receipts
        ("eutils_gds_1.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=8&term=single+cell+drug+time+course+apoptosis", "NCBI public API", False),
        ("eutils_gds_2.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=8&term=perturb-seq+time+course", "NCBI public API", False),
        ("eutils_gds_3.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=8&term=single+cell+drug+treatment+time+series", "NCBI public API", False),
        ("eutils_gds_4.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=8&term=single+cell+RNA-seq+apoptosis+FACS+drug", "NCBI public API", False),
        ("eutils_gds_5.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=8&term=organoid+drug+single+cell+time+course", "NCBI public API", False),
        # Zenodo search receipts (no qualified dataset found in top hits)
        ("zenodo_organoid%20drug%20single%20cell%20time%20course.json", "https://zenodo.org/api/records?q=organoid%20drug%20single%20cell%20time%20course&size=5", "CC0/other-open per record", False),
        ("zenodo_sequential%20drug%20treatment%20organoid%20single%20cell.json", "https://zenodo.org/api/records?q=sequential%20drug%20treatment%20organoid%20single%20cell&size=5", "CC0/other-open per record", False),
    ]
    for name, url, lic, login in registry:
        p = os.path.join(REC, name)
        m = file_meta(p, url)
        m["license"] = lic
        m["login_required"] = login
        m["download_status"] = "downloaded_public" if m["present"] else "missing"
        if m["bytes"] is not None and m["bytes"] > 500 * 1024 * 1024:
            m["download_status"] = "not_downloaded_over_500MB"
        out["downloads"][name] = m

    # large files not downloaded (recorded)
    out["not_downloaded_over_500MB"] = [
        {"candidate": "sci-Plex GSE139944", "file": "GSE139944_RAW.tar", "bytes": 9902397440,
         "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/suppl/GSE139944_RAW.tar",
         "reason": "9.90 GB > 500 MB per-file limit; metadata/small pData used instead"},
        {"candidate": "sci-Plex GSE139944", "file": "sciPlex3 A549/K562/MCF7 RDS + screen UMI matrix",
         "bytes": None, "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/suppl/",
         "reason": "individual RDS 530-2200 MB and screen UMI matrix 2.9 GB >500 MB; not downloaded"},
        {"candidate": "Tahoe-100M", "file": "data/train-*.parquet (3,388 shards)", "bytes": 337644770670,
         "url": "https://huggingface.co/datasets/tahoebio/Tahoe-100M", "reason": "337 GB total; per-shard >500 MB; metadata only"},
        {"candidate": "X-Atlas/Orion", "file": "data/HCT116*.parquet / HEK293T*.parquet", "bytes": 126 * 1024**3,
         "url": "https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion", "reason": "126 GB total; >500 MB per file; metadata only"},
        {"candidate": "AZ/GDSC 2024", "file": "Overall_ANOVA_results.csv", "bytes": 1958509070,
         "url": "https://figshare.com/projects/163378", "reason": "1.96 GB >500 MB; DATA1 report; not re-downloaded"},
    ]

    # ---------- structural checks ----------
    # GSE214965
    g214_meta = gz_lines("GSE214965_sample_metadata_LN229_DRUG_Seq.txt.gz", 2000)
    header = g214_meta[0].replace('"', "").split("\t")
    rows = [line.replace('"', "").split("\t") for line in g214_meta[1:] if line.strip()]
    idx = {h: i for i, h in enumerate(header)}
    times = sorted({r[idx["timepoint"]] for r in rows}) if "timepoint" in idx else []
    drugs = sorted({r[idx["drug"]] for r in rows}) if "drug" in idx else []
    reps = sorted({r[idx["replicate"]] for r in rows}) if "replicate" in idx else []
    func_cols_214 = [h for h in header if any(k in h.lower() for k in ("apop", "casp", "viab", "function", "response", "regrow"))]
    rawcount_lines = gz_lines("GSE214965_rawcounts_LN229_DRUG_Seq.txt.gz", 3)
    struct_214 = {
        "source": "GSE214965 series matrix + sample metadata + raw counts",
        "series_title": series_meta("GSE214965_series_matrix.txt.gz").get("title"),
        "timepoints": times,
        "n_drugs": len(drugs),
        "drugs_sample": drugs[:8],
        "replicates": reps,
        "n_rows_metadata": len(rows),
        "metadata_columns": header,
        "functional_columns": func_cols_214,
        "rawcounts_header_sample": rawcount_lines[0][:300] if rawcount_lines else None,
        "rawcounts_n_genes": None,
        "rawcounts_n_samples": None,
    }
    if rawcount_lines:
        hdr = rawcount_lines[0].rstrip("\n").split("\t")
        n_genes = 0
        with gzip.open(os.path.join(REC, "GSE214965_rawcounts_LN229_DRUG_Seq.txt.gz"), "rt", errors="replace") as f:
            next(f)
            for _ in f:
                n_genes += 1
        struct_214["rawcounts_n_genes"] = n_genes
        struct_214["rawcounts_n_samples"] = len(hdr)
    # GSE139944 (pData is space-delimited with mixed quoted/unquoted fields)
    import re
    sci_series = series_meta("GSE139944-GPL21697_series_matrix.txt.gz")
    pdata_path = os.path.join(REC, "GSM4150378_sciPlex3_pData.txt.gz")
    _pat = re.compile(r'"[^"]*"|[^\s"]+')

    def _toks(line):
        return [x.strip('"') for x in _pat.findall(line)]

    with gzip.open(pdata_path, "rt", errors="replace") as f:
        sci_header = _toks(f.readline())
        idx = {k: i for i, k in enumerate(sci_header)}
        times = set(); drugs = set(); doses = set(); cultures = set(); reps = set()
        time_counts = {}
        for i, line in enumerate(f):
            if i >= 200000:
                break
            toks = _toks(line)
            if len(toks) < len(sci_header):
                continue
            off = len(toks) - len(sci_header)  # right-align trailing annotation fields
            tv = toks[idx["time_point"] + off]
            times.add(tv)
            time_counts[tv] = time_counts.get(tv, 0) + 1
            drugs.add(toks[idx["product_name"] + off])
            doses.add(toks[idx["dose"] + off])
            cultures.add(toks[idx["culture_plate"] + off])
            reps.add(toks[idx["replicate"] + off])
    sci_struct = {
        "source": "GSE139944 series matrix + GSM4150378 sciPlex3 pData",
        "series_title": sci_series.get("title"),
        "sample_titles": sci_series.get("sample_titles"),
        "pdata_columns": sci_header,
        "pdata_rows_scanned": 200000,
        "time_point_columns": [c for c in sci_header if "time" in c.lower()],
        "unique_time_points": sorted(times),
        "time_point_counts": time_counts,
        "dose_columns": [c for c in sci_header if any(k in c.lower() for k in ("dose", "drug"))],
        "n_drugs": len(drugs),
        "n_doses": len(doses),
        "n_culture_plates": len(cultures),
        "replicate_columns": [c for c in sci_header if "replicat" in c.lower()],
        "unique_replicates": sorted(reps),
        "functional_columns": [c for c in sci_header if any(k in c.lower() for k in ("apop", "casp", "viab", "function", "response", "regrow"))],
        "sample_notes": "sciPlex3 sample harvested 24h after drug exposure; file names *_24hrs; sciPlex2/4 also 24h per series text",
    }
    # Tahoe
    import pandas as pd
    tahoe = {
        "sample_metadata": {},
        "drug_metadata": {},
        "cell_line_metadata": {},
    }
    try:
        s = pd.read_parquet(os.path.join(REC, "Tahoe_sample_metadata.parquet"))
        tahoe["sample_metadata"] = {"shape": list(s.shape), "columns": list(s.columns),
                                    "n_plates": int(s["plate"].nunique()) if "plate" in s else None,
                                    "n_drugs": int(s["drug"].nunique()) if "drug" in s else None,
                                    "time_columns": [c for c in s.columns if "time" in c.lower()],
                                    "functional_columns": [c for c in s.columns if any(k in c.lower() for k in ("apop", "casp", "viab", "function", "response", "regrow"))],
                                    "drug_conc_sample": str(s["drugname_drugconc"].head(2).tolist()) if "drugname_drugconc" in s else None}
        d = pd.read_parquet(os.path.join(REC, "Tahoe_drug_metadata.parquet"))
        tahoe["drug_metadata"] = {"shape": list(d.shape), "columns": list(d.columns)}
        c = pd.read_parquet(os.path.join(REC, "Tahoe_cell_line_metadata.parquet"))
        tahoe["cell_line_metadata"] = {"shape": list(c.shape), "columns": list(c.columns)}
    except Exception as e:
        tahoe["error"] = str(e)
    # X-Atlas
    xatlas = {}
    try:
        readme = open(os.path.join(REC, "XAtlas_README.md"), encoding="utf-8", errors="replace").read()
        api = json.load(open(os.path.join(REC, "Xaira-Therapeutics__X-Atlas-Orion.api.json"), encoding="utf-8"))
        xatlas = {"license": api.get("cardData", {}).get("license"),
                  "gated": api.get("gated"), "private": api.get("private"),
                  "sibling_count": len(api.get("siblings", [])),
                  "description": readme[:700],
                  "time_columns_mentioned": [w for w in ("time", "hour", "timepoint") if w in readme.lower()],
                  "functional_terms_mentioned": [w for w in ("apoptosis", "viability", "caspase", "function") if w in readme.lower()],
                  "download_plan": "metadata/README only; 126 GB parquet >500 MB/file not downloaded"}
    except Exception as e:
        xatlas["error"] = str(e)
    # Mix-seq local
    import anndata as ad
    a = ad.read_h5ad(H5AD, backed="r")
    obs_cols = list(a.obs.columns)
    tm = a.obs["time"].astype(str).value_counts().to_dict()
    func_cols = [c for c in obs_cols if any(k in c.lower() for k in ("apop", "casp", "viab", "function", "response", "regrow", "fitness"))]
    mixseq = {"path": os.path.relpath(H5AD, ROOT).replace(os.sep, "/"),
              "shape": [int(a.n_obs), int(a.n_vars)],
              "obs_columns": obs_cols,
              "time_counts": {str(k): int(v) for k, v in tm.items()},
              "functional_columns": func_cols,
              "dose_columns": [c for c in obs_cols if "dose" in c.lower()],
              "read": "obs/var metadata only; X values not read"}
    a.file.close()

    # ---------- candidates + D1-D7 ----------
    def gate(status, evidence):
        return {"status": status, "evidence": evidence}

    candidates = {
        "mixseq": {
            "name": "Mix-seq (McFarland et al. 2020; local scPerturb asset)",
            "source": ["local h5ad: data/external/mixseq_scperturb/mcfarland_2020.h5ad"],
            "license": "local scPerturb-derived asset; original publication; no explicit redistribution license recorded locally",
            "access": "local asset; h5ad 1.46 GB (>500 MB but pre-existing, not downloaded this task)",
            "structure": mixseq,
            "gates": {
                "D1": gate("pass", "multi-time population snapshots: 6h/24h arms + Trametinib 3/6/12/24/48h; but no functional readout"),
                "D2": gate("unclear", "same cell-line/drug keys but no culture/batch/passage labels; 6h/24h are separate arms, not same-culture tracking"),
                "D3": gate("partial", "dose/time present; function readout absent (RNA only)"),
                "D4": gate("fail", "treatment labels only; no recorded pi/randomized assignment/propensity"),
                "D5": gate("fail", "no independent culture/plate replicate records; no batch labels; not certifiable"),
                "D6": gate("fail", "RNA only; no orthologous function modality"),
                "D7": gate("pass", "raw/processed RNA counts + RNA; but no functional counts"),
            },
            "overall": "not_qualified",
            "blocking": ["D4", "D5", "D6", "D2(unclear)"],
            "missing": "functional readout (apoptosis/caspase/viability) at same timepoints; independent culture/plate/batch; recorded treatment assignment/pi; mapping to function",
            "next": "not a Stage2 dataset; usable only as RNA-only population-snapshot side resource; cannot satisfy M2 Stage2 independent functional decision",
        },
        "scipl_ex": {
            "name": "sci-Plex (Srivatsan et al. 2020; GSE139944)",
            "source": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139944",
                       "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE139nnn/GSE139944/"],
            "license": "NCBI GEO public data; no explicit license; NCBI data usage policies",
            "access": "public; small metadata downloaded; big RDS/UMI matrices >500 MB/file not downloaded",
            "structure": sci_struct,
            "gates": {
                "D1": gate("pass", "multi-time population snapshots (sciPlex3 pData time_point includes 24h and 72h); no functional readout"),
                "D2": gate("partial", "same cell line and hashed plate/well design (culture_plate labels); no independent culture/batch exchangeability certified"),
                "D3": gate("partial", "dose (drug_dose) and time_point present; no functional readout"),
                "D4": gate("fail", "drug treatment labels only; no recorded pi/randomized assignment/propensity"),
                "D5": gate("partial", "plate/well and replicate labels; no independent culture records; technical/well replicates not certified independent"),
                "D6": gate("fail", "RNA only; no orthogonal function"),
                "D7": gate("pass", "UMI counts + RNA + cell annotations"),
            },
            "overall": "not_qualified",
            "blocking": ["D4", "D6", "D2(partial)", "D5(partial)"],
            "missing": "multi-time functional readout; independent culture/batch; recorded pi; orthogonal function",
            "next": "could serve as dose-response RNA reference, not Stage2 functional qualification",
        },
        "drugseq_gse214965": {
            "name": "DRUG-Seq LN-229 20 drugs, 6h/22h (GSE214965)",
            "source": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE214965",
                       "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214965/"],
            "license": "NCBI GEO public data; no explicit license; NCBI data usage policies",
            "access": "public; small metadata + raw counts downloaded (1.7 MB raw counts)",
            "structure": struct_214,
            "gates": {
                "D1": gate("pass", "two timepoints (6h, 22h) with population RNA snapshots"),
                "D2": gate("unclear", "same LN-229 line, two libraries/plates; no culture/batch/passage labels"),
                "D3": gate("partial", "fixed 20 uM, time 6/22h present; no functional readout (count_sum/genes_detected are RNA QC)"),
                "D4": gate("fail", "drug labels + replicate labels only; no recorded pi/randomization"),
                "D5": gate("partial", "4 'biological_replicate' labels within two libraries; no independent culture/passage evidence"),
                "D6": gate("fail", "RNA only; no orthogonal function"),
                "D7": gate("pass", "raw counts + RNA"),
            },
            "overall": "not_qualified",
            "blocking": ["D4", "D6", "D2(unclear)", "D5(partial)"],
            "missing": "functional readout; independent culture/plate; pi/randomization records",
            "next": "RNA time-series reference only; cannot support independent functional decision",
        },
        "tahoe": {
            "name": "Tahoe-100M (2025; tahoebio)",
            "source": ["https://huggingface.co/datasets/tahoebio/Tahoe-100M"],
            "license": "CC0-1.0",
            "access": "public; metadata downloaded; 337 GB parquet (3,388 shards) not downloaded",
            "structure": tahoe,
            "gates": {
                "D1": gate("fail", "single-time 95.6M-cell drug atlas; public sample metadata has no time column"),
                "D2": gate("unclear", "plate labels present; no culture/batch exchangeability across time"),
                "D3": gate("partial", "drug/dose labels present; no time series; no functional readout (RNA only)"),
                "D4": gate("fail", "drug/plate labels only; no recorded pi/randomization"),
                "D5": gate("unclear", "plate labels only; no independent culture/plate replicates"),
                "D6": gate("fail", "RNA only; no orthogonal function"),
                "D7": gate("pass", "RNA counts (expression) + metadata"),
            },
            "overall": "not_qualified",
            "blocking": ["D1", "D4", "D6", "D2/D5 unclear"],
            "missing": "multi-time; functional readout; independent culture/batch; pi",
            "next": "RNA-only atlas; cannot satisfy Stage2 functional/time gate",
        },
        "xatlas": {
            "name": "X-Atlas/Orion (2025; Xaira)",
            "source": ["https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion"],
            "license": "CC-BY-NC-SA-4.0",
            "access": "public; metadata/README downloaded; 126 GB parquet (337 files) not downloaded",
            "structure": xatlas,
            "gates": {
                "D1": gate("fail", "single-time FiCS Perturb-seq atlas; no time course"),
                "D2": gate("partial", "Batch1... labels present; single time; no cross-time exchangeability"),
                "D3": gate("fail", "no dose/time/function readout; RNA-only gene perturbation atlas"),
                "D4": gate("fail", "guide/target labels only; no recorded pi/randomization"),
                "D5": gate("partial", "batch labels; no independent culture evidence"),
                "D6": gate("fail", "RNA only; no orthogonal function"),
                "D7": gate("pass", "RNA counts + metadata"),
            },
            "overall": "not_qualified",
            "blocking": ["D1", "D3", "D4", "D6"],
            "missing": "time course; dose; function readout; independent culture; pi",
            "next": "gene-perturbation RNA atlas only; not a drug multi-time function dataset",
        },
        "az_gdsc_2024": {
            "name": "AZ/GDSC 2024 matrix screen (functional; DATA1/DATA2 already checked)",
            "source": ["https://figshare.com/projects/163378", "https://gdsc-combinations.depmap.sanger.ac.uk/",
                       "research/2026-10-28-az-data-acquisition/report_data1.md",
                       "research/2026-10-28-az-code-hunt/report_data2.md"],
            "license": "public Figshare/GDSC; no explicit license; DATA1 records public access; no login/terms encountered",
            "access": "public raw well ZIP 241 MB + matrix summaries; mapping/functional numeric missing; not re-downloaded here",
            "structure": {
                "source": "DATA1/DATA2 reports; no new download",
                "available": ["72h CellTiter-Glo viability", "raw well intensities (241 MB ZIP)", "matrix summaries", "caspase/PARP/western only as figures/PDF"],
                "missing": ["per-barcode experiment/occasion/technical replicate/treatment date/passage/culture mapping",
                            "Fig 4/5/6 caspase/PARP/western numeric", "RNA/counts paired with function (no scRNA)"],
                "D1_D7_note": "six occasions / technical triplicates; not a time course; no RNA pairing",
            },
            "gates": {
                "D1": gate("partial", "functional viability at 72h and caspase/PARP reported; six occasions but not multi-time functional series; no RNA population snapshot pairing"),
                "D2": gate("unclear", "no culture/batch mapping; technical triplicates≠independent cultures"),
                "D3": gate("partial", "dose/time/viability present; functional numeric (caspase/PARP) not public"),
                "D4": gate("fail", "no recorded pi/randomization/assignment probabilities"),
                "D5": gate("partial", "6 occasions x 3 technical matrices; independent culture not certified"),
                "D6": gate("partial", "viability + caspase/PARP reported in paper; numeric not public"),
                "D7": gate("fail", "no RNA/counts paired with function"),
            },
            "overall": "data_unavailable",
            "blocking": ["D1(partial)", "D2(unclear)", "D4", "D7", "mapping/functional numeric not public"],
            "missing": "mapping + functional numeric + paired RNA/counts + independent-culture labels",
            "next": "DATA1 request spec P0/P1 remains; if mapping/function numeric provided, re-qualify; not Stage2-qualified now",
        },
    }
    out["candidates"] = candidates

    # ---------- search log ----------
    out["search_log"] = {
        "bounded": True,
        "note": "bounded search only; not exhaustive; 'not found' != 'does not exist'",
        "web_and_api_queries": [
            "sci-Plex single cell drug time course 24h 72h GEO GSE139944 timepoints",
            "multi-timepoint single-cell drug perturbation dataset apoptosis caspase functional readout GEO 2024 2025",
            "perturb-seq time course dataset public 2024 2025 multiple time points",
            "sequential drug treatment organoid single-cell dataset Dryad Figshare Zenodo",
            "GEO eutils gds: single cell drug time course apoptosis; perturb-seq time course; single cell drug treatment time series; single cell RNA-seq apoptosis FACS drug; organoid drug single cell time course",
            "Zenodo API: organoid drug single cell time course; sequential drug treatment organoid single cell",
            "HuggingFace API: tahoebio/Tahoe-100M; Xaira-Therapeutics/X-Atlas-Orion",
        ],
        "geo_hits": {
            "GSE214965": "DRUG-Seq LN-229, 20 drugs, 2 time points (6/22h), 4 replicates, RNA counts",
            "GSE139944": "sci-Plex 24h, multi-dose/cell-line, RNA counts; no functional readout",
            "GSE342498": "retinal waves/apoptosis/angiogenesis (not drug perturbation; not included)",
        },
        "zenodo_top_hits": ["15621414 Organoid Technology...", "7561908 retinal organoid development", "10370690 organoid review",
                            "8404609 kidney organoid omics", "20142884 organoid morphology images"],
        "zenodo_conclusion": "no top hit provides multi-time function + RNA + recorded pi + independent culture; bounded negative only",
        "not_found_in_bounded_search": [
            "public dataset combining multi-time functional readout (apoptosis/caspase/viability/regrowth) with paired RNA/counts and recorded pi/action labels at same culture/batch level",
            "organoid/patient-derived sequential dosing public dataset satisfying D1-D7",
        ],
        "not_found_meaning": "bounded search did not find; not evidence of absence",
    }
    # ---------- overall ----------
    out["overall"] = {
        "verdict": "not_qualified",
        "qualified_candidates": [],
        "partial_candidates": ["mixseq", "scipl_ex", "drugseq_gse214965", "tahoe", "xatlas", "az_gdsc_2024"],
        "blocking_common": ["D4 (no recorded pi/randomization)", "D6 (no orthogonal functional readout)", "D2/D5 (independent culture/batch not certifiable)"],
        "why_not_data_unavailable": "we did retrieve and structurally verify public datasets for multiple candidates; they fail gates, so not_qualified (not merely description-insufficient). AZ/GDSC functional branch remains data_unavailable for M2 because mapping/functional numeric/paired RNA are not public.",
        "m2_stage2_gate_status": "failed; data readiness remains open",
        "next": [
            "Do not run Stage2; do not synthesize/RNA-substitute independent functional decisions",
            "If a candidate later adds multi-time functional + RNA + pi + independent culture: wash/mapping/qualification under new protocol",
            "AZ/GDSC: keep DATA1 request spec P0/P1 (mapping, functional numeric, per-barcode 18-replicate map); no new wet-lab claim",
            "Bounded search result only; no 'does not exist' claim; request spec for M2 function+pi data remains",
        ],
        "no_claims": ["novelty", "migration", "decision benefit", "mechanism", "pharmacology"],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("WROTE", OUT)
    print(json.dumps({"verdict": out["overall"]["verdict"], "n_candidates": len(candidates),
                      "downloads": len([m for m in out["downloads"].values() if m["present"]]),
                      "candidates": {k: v["overall"] for k, v in candidates.items()}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
