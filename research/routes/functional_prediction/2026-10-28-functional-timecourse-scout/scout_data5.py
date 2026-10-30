"""R204-DATA5 scout: public drug-induced functional time-course retrieval and D1/D6 verification.

Offline structural verification of public downloads (receipts/). Downloads were performed via
public GEO FTP / BBBC / Zenodo HTTPS (see record_data5.md). This script reads only metadata /
tables for structure (fields, rows, timepoints, functional-column names) and never reads response
values for effect; no effect statistics, no model fitting.

Output: scout_data5.json (deterministic; sort_keys; no timestamps).
"""
import gzip
import hashlib
import json
import os
import re
import sys
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REC = os.path.join(HERE, "receipts")
OUT = os.path.join(HERE, "scout_data5.json")
PROTOCOL = os.path.join(HERE, "PROTOCOL_DATA5.md")

INPUTS = {
    "report_data4.md": os.path.join(ROOT, "research", "2026-10-28-multitime-data-scout", "report_data4.md"),
    "scout_data4.json": os.path.join(ROOT, "research", "2026-10-28-multitime-data-scout", "scout_data4.json"),
    "PROBLEM_M2_STAGE2_v0_2.md": os.path.join(ROOT, "research", "2026-10-28-m2-stage2-prep", "PROBLEM_M2_STAGE2_v0_2.md"),
    "DESIGN_M2_STAGE2_v0_2.md": os.path.join(ROOT, "research", "2026-10-28-m2-stage2-prep", "DESIGN_M2_STAGE2_v0_2.md"),
    "report_data3.md": os.path.join(ROOT, "research", "2026-10-28-az-download-verify", "report_data3.md"),
    "BRIEF_R204.md": os.path.join(ROOT, "research", "2026-10-28-deep-coupling-redesign", "BRIEF_R204.md"),
    "report_R204.md": os.path.join(ROOT, "research", "2026-10-28-deep-coupling-redesign", "report.md"),
    "EVIDENCE_REGISTER.md": os.path.join(ROOT, "research", "EVIDENCE_REGISTER.md"),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def meta(path, url="", license_="", login=False):
    return {"path": os.path.relpath(path, ROOT).replace(os.sep, "/"), "url": url,
            "present": os.path.exists(path), "bytes": os.path.getsize(path) if os.path.exists(path) else None,
            "sha256": sha256_file(path) if os.path.exists(path) else None,
            "license": license_, "login_required": login}


def gz_lines(path, limit=None):
    out = []
    with gzip.open(path, "rt", errors="replace") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            out.append(line.rstrip("\n"))
    return out


def series_struct(path):
    title = design = None
    summaries = []
    chars = []
    samples = []
    with gzip.open(path, "rt", errors="replace") as f:
        for line in f:
            if line.startswith("!Series_title"):
                title = line.split("\t", 1)[1].strip().strip('"')
            elif line.startswith("!Series_summary"):
                summaries.append(line.split("\t", 1)[1].strip().strip('"'))
            elif line.startswith("!Series_overall_design"):
                design = line.split("\t", 1)[1].strip().strip('"')
            elif line.startswith("!Sample_title"):
                samples = [x.strip().strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            elif line.startswith("!Sample_characteristics") or line.startswith("!Sample_treatment_protocol"):
                chars.append(line.rstrip("\n"))
    text = " \n".join([title or "", " ".join(summaries), design or "", " ".join(samples), " ".join(chars)])
    return {"title": title, "design": design, "sample_titles": samples,
            "n_samples": len(samples), "text": text,
            "functional_terms": [w for w in ("apoptosis", "caspase", "parp", "viability", "celltiter", "incucyte", "regrowth", "colony")
                                 if w in text.lower()]}


def main():
    out = {"meta": {"task": "task-174 R204-DATA5 public functional time-course retrieval and D1/D6 verification",
                    "protocol_sha256": sha256_file(PROTOCOL), "date": "2026-10-28",
                    "mode": "bounded retrieval + public download + structural-only verification",
                    "effect_run": False, "model_fit": False,
                    "response_values_read_for_effect": False,
                    "download_limit_bytes_per_file": 500 * 1024 * 1024,
                    "login_or_license_bypass": False},
           "inputs_sha256": {}, "downloads": {}, "search_log": {}, "candidates": {}, "overall": {}}
    for k, p in INPUTS.items():
        out["inputs_sha256"][k] = meta(p)

    registry = [
        ("GSE149428_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE149nnn/GSE149428/matrix/GSE149428_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE129012_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE129nnn/GSE129012/matrix/GSE129012_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE154932_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE154nnn/GSE154932/matrix/GSE154932_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("GSE248450_series_matrix.txt.gz", "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE248nnn/GSE248450/matrix/GSE248450_series_matrix.txt.gz", "NCBI GEO public data; no explicit license; NCBI data usage policies", False),
        ("BBBC021_v1_compound.csv", "https://data.broadinstitute.org/bbbc/BBBC021/BBBC021_v1_compound.csv", "BBBC public data; no explicit license; Broad BBBC terms", False),
        ("BBBC021_v1_image.csv", "https://data.broadinstitute.org/bbbc/BBBC021/BBBC021_v1_image.csv", "BBBC public data; no explicit license; Broad BBBC terms", False),
        ("BBBC022_v1_image.csv", "https://data.broadinstitute.org/bbbc/BBBC022/BBBC022_v1_image.csv", "BBBC public data; no explicit license; Broad BBBC terms", False),
        ("BBBC021.html", "https://bbbc.broadinstitute.org/BBBC021", "BBBC public page", False),
        ("BBBC022.html", "https://bbbc.broadinstitute.org/BBBC022", "BBBC public page", False),
        ("ctos_drug_response_networks.zip", "https://zenodo.org/records/20043756/files/ctos-drug-response-networks_zenodo_v0.1.0_doi-10.5281-zenodo.20043756.zip?download=1", "CC-BY-4.0", False),
        ("eutils_gds_1.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=10&term=drug+treatment+time+course+apoptosis", "NCBI public API", False),
        ("eutils_gds_2.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=10&term=drug+treatment+time+course+viability", "NCBI public API", False),
        ("eutils_gds_3.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=10&term=caspase+activity+time+course+drug", "NCBI public API", False),
        ("eutils_gds_4.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=10&term=high+content+imaging+drug+time+course", "NCBI public API", False),
        ("eutils_gds_5.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=10&term=organoid+drug+response+time+course", "NCBI public API", False),
        ("eutils_gds_6.xml", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmax=10&term=live+cell+imaging+drug+response+time+lapse", "NCBI public API", False),
        ("biostudies_drug%20time%20course%20apoptosis.json", "https://www.ebi.ac.uk/biostudies/api/v1/search?query=drug%20time%20course%20apoptosis&pageSize=10", "EBI BioStudies public API", False),
        ("zenodo_1.json", "https://zenodo.org/api/records?q=organoid+time+lapse+drug+response&size=5", "CC0/other-open per record", False),
        ("zenodo_2.json", "https://zenodo.org/api/records?q=spheroid+drug+response+time+lapse&size=5", "CC0/other-open per record", False),
        ("zenodo_3.json", "https://zenodo.org/api/records?q=IncuCyte+drug+response&size=5", "CC0/other-open per record", False),
        ("zenodo_4.json", "https://zenodo.org/api/records?q=RealTime-Glo+viability+time+course&size=5", "CC0/other-open per record", False),
        ("zenodo_5.json", "https://zenodo.org/api/records?q=caspase+time+course+drug&size=5", "CC0/other-open per record", False),
        ("zenodo_record_20043756.json", "https://zenodo.org/api/records/20043756", "CC-BY-4.0", False),
        ("zenodo_record_3333613.json", "https://zenodo.org/api/records/3333613", "CC-BY-4.0", False),
        ("zenodo_record_20142884.json", "https://zenodo.org/api/records/20142884", "CC-BY-4.0", False),
        ("zenodo_record_20718919.json", "https://zenodo.org/api/records/20718919", "CC-BY-4.0", False),
    ]
    for name, url, lic, login in registry:
        p = os.path.join(REC, name)
        m = meta(p, url, lic, login)
        m["download_status"] = "downloaded_public" if m["present"] else "missing"
        out["downloads"][name] = m

    out["not_downloaded_over_500MB"] = [
        {"candidate": "BBBC021", "file": "55 image ZIPs (~750 MB each)", "bytes": None,
         "url": "https://data.broadinstitute.org/bbbc/BBBC021/", "reason": "per-file ~750 MB > 500 MB; metadata CSVs used instead"},
        {"candidate": "BBBC022", "file": "image ZIPs", "bytes": None,
         "url": "https://data.broadinstitute.org/bbbc/BBBC022/", "reason": "large image ZIPs >500 MB; metadata CSV used instead"},
        {"candidate": "GSE154932/GSE248450/other GEO", "file": "supplementary raw/processed archives",
         "bytes": None, "url": "https://ftp.ncbi.nlm.nih.gov/geo/", "reason": "not required for structural metadata; GEO series matrix used; large archives not downloaded"},
        {"candidate": "TRACI IncuCyte example", "file": "TRACI-test-data-v2.zip", "bytes": 211843215,
         "url": "https://zenodo.org/records/20718919", "reason": "time-lapse migration example, not drug-response multi-time function; not downloaded"},
    ]

    # ---------- structural checks ----------
    geo = {}
    for g, fn in [("GSE149428", "GSE149428_series_matrix.txt.gz"),
                  ("GSE129012", "GSE129012_series_matrix.txt.gz"),
                  ("GSE154932", "GSE154932_series_matrix.txt.gz"),
                  ("GSE248450", "GSE248450_series_matrix.txt.gz")]:
        s = series_struct(os.path.join(REC, fn))
        # extract timepoints (candidate-specific; from Series_overall_design / characteristics)
        if g == "GSE149428":
            m = re.search(r"at\s+([\d,\s and]+?)\s*hours", s["design"] or s["text"])
            tps = sorted({int(x) for x in re.findall(r"\d+", m.group(1))}) if m else []
        elif g == "GSE129012":
            tps = sorted({int(x) for x in re.findall(r"(\d+)\s*hrs", s["design"] or s["text"])})
        elif g == "GSE154932":
            tps = sorted(set(re.findall(r"time point:\s*([^\"\t]+)", s["text"])))
        else:
            m = re.search(r"for\s+([\d,\s and]+?)\s*days", s["design"] or s["text"])
            tps = sorted({int(x) for x in re.findall(r"\d+", m.group(1))}) if m else []
        geo[g] = {"title": s["title"], "design": s["design"], "n_samples": s["n_samples"],
                  "sample_titles": s["sample_titles"][:12], "timepoints": tps,
                  "functional_terms_in_metadata": s["functional_terms"],
                  "functional_columns_present": False,
                  "note": "GEO series matrix metadata only; function numeric not found in series matrix; functional terms may be paper/design mentions only"}
    # BBBC021
    b21 = pd.read_csv(os.path.join(REC, "BBBC021_v1_image.csv"))
    b21c = pd.read_csv(os.path.join(REC, "BBBC021_v1_compound.csv"))
    bbbc021 = {"image_rows": int(b21.shape[0]), "image_columns": list(b21.columns),
               "compounds": int(b21["Image_Metadata_Compound"].nunique()),
               "concentrations": sorted({float(x) for x in b21["Image_Metadata_Concentration"].unique()})[:10],
               "replicates": sorted({str(x) for x in b21["Replicate"].unique()}),
               "has_treatment_time_column": any("time" in c.lower() for c in b21.columns),
               "channels": [c for c in b21.columns if c.startswith("Image_FileName_")],
               "page_note": "BBBC021 page: MCF-7 treated for 24 h; fixed/labeled DNA, F-actin, beta-tubulin; single treatment time"}
    # BBBC022
    b22 = pd.read_csv(os.path.join(REC, "BBBC022_v1_image.csv"), on_bad_lines="skip")
    bbbc022 = {"image_rows": int(b22.shape[0]), "image_columns": list(b22.columns),
               "compounds": int(b22["Image_Metadata_SOURCE_COMPOUND_NAME"].nunique()),
               "has_treatment_time_column": False,
               "time_column_meaning": "Image_Metadata_Time = acquisition timestamp (ms), not treatment time",
               "n_time_values": int(b22["Image_Metadata_Time"].nunique()),
               "page_note": "BBBC022 page: U2OS Cell Painting, single compound-profiling experiment"}
    # ctos
    z = zipfile.ZipFile(os.path.join(REC, "ctos_drug_response_networks.zip"))
    ctos = {"members": len(z.namelist()), "readme": z.read("ctos-drug-response-networks/README.md").decode("utf-8", "replace")[:700]}
    ds = pd.read_csv(z.open("ctos-drug-response-networks/derived_data/drug_response/drug_sensitivity_table.tsv"), sep="\t")
    qp = pd.read_csv(z.open("ctos-drug-response-networks/derived_data/validation/qpcr_long.tsv"), sep="\t")
    src = pd.read_csv(z.open("ctos-drug-response-networks/docs/source_sample_metadata.tsv"), sep="\t")
    ctos.update({"drug_sensitivity_shape": list(ds.shape), "drug_sensitivity_columns": list(ds.columns),
                 "drug_sensitivity_n_patients": int(ds["patient_id"].nunique()),
                 "drug_sensitivity_n_drugs": int(ds["drug"].nunique()),
                 "qpcr_shape": list(qp.shape), "qpcr_columns": list(qp.columns),
                 "qpcr_timepoints": sorted({str(x) for x in qp["timepoint"].unique()}),
                 "source_metadata_shape": list(src.shape), "source_columns": list(src.columns),
                 "functional_columns": [c for c in ds.columns if any(k in c.lower() for k in ("viab", "response", "apop", "casp"))],
                 "note": "organoid/patient-derived derived data; viability single endpoint + qPCR 8h; raw RNA controlled access not shipped"})

    # candidate gates
    def gate(s, e):
        return {"status": s, "evidence": e}

    candidates = {
        "gse149428": {
            "name": "GSE149428 — matched time-course RNAseq of drug combinations (MCF7/LNCaP)",
            "source": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149428",
                       "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE149nnn/GSE149428/"],
            "license": "NCBI GEO public data; no explicit license",
            "access": "public; series matrix 16 KB downloaded; expression matrix not downloaded (not needed for structure)",
            "structure": geo["GSE149428"],
            "gates": {
                "D1": gate("pass", "6 timepoints 0/3/6/9/12/24 h; RNA population snapshots (not functional)"),
                "D2": gate("unclear", "same cell lines, triplicate A/B/C; no culture/batch/passage labels"),
                "D3": gate("partial", "dose (20 uM) + times present; no functional readout (RNA only)"),
                "D4": gate("fail", "drug treatment labels only; no pi/randomization"),
                "D5": gate("partial", "triplicate labels; no independent culture/plate records"),
                "D6": gate("fail", "RNA only; no orthogonal function"),
                "D7": gate("pass", "RNA counts at multiple times"),
            },
            "overall": "not_qualified", "blocking": ["D4", "D6", "D2", "D5"],
            "missing": "functional readout at the same times; independent culture; pi",
            "next": "RNA time-course reference only; cannot fill D6; no Stage2",
        },
        "gse129012": {
            "name": "GSE129012 — AZD4573 CDK9 inhibitor RNA-seq time course (MCF7)",
            "source": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE129012",
                       "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE129nnn/GSE129012/"],
            "license": "NCBI GEO public data; no explicit license",
            "access": "public; series matrix 3.3 KB downloaded",
            "structure": geo["GSE129012"],
            "gates": {
                "D1": gate("pass", "4 h and 8 h RNA timepoints; RNA population snapshots"),
                "D2": gate("unclear", "same MCF7 line; no culture/batch labels"),
                "D3": gate("partial", "dose/time present; apoptosis reported in paper but no public function numeric"),
                "D4": gate("fail", "treatment labels only; no pi/randomization"),
                "D5": gate("partial", "3 replicates; no independent culture records"),
                "D6": gate("fail", "no public apoptosis/caspase numeric; RNA only"),
                "D7": gate("pass", "RNA counts"),
            },
            "overall": "not_qualified", "blocking": ["D4", "D6", "D2"],
            "missing": "function numeric (caspase/apoptosis/viability); independent culture; pi",
            "next": "RNA time-course reference only; not D6 evidence",
        },
        "gse154932": {
            "name": "GSE154932 — MDA-MB-231 doxorubicin resistance; scRNA + Incucyte monitoring",
            "source": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE154932",
                       "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE154nnn/GSE154932/"],
            "license": "NCBI GEO public data; no explicit license",
            "access": "public; series matrix 3.1 KB downloaded; functional Incucyte numeric not in series matrix",
            "structure": geo["GSE154932"],
            "gates": {
                "D1": gate("partial", "RNA at 0/7/10 weeks; Incucyte treatment-response protocol described, but function numeric not public in series matrix"),
                "D2": gate("unclear", "same MDA-MB-231 line; no culture/batch labels"),
                "D3": gate("partial", "dose (0-1000 nM) and times/weeks in protocol; public function numeric missing"),
                "D4": gate("fail", "treatment labels only; no pi/randomization"),
                "D5": gate("partial", "6 replicate wells mentioned; independent culture not certified"),
                "D6": gate("partial", "Incucyte functional monitoring described + RNA; numeric not public → not usable as D6 evidence"),
                "D7": gate("pass", "scRNA counts at timepoints"),
            },
            "overall": "not_qualified", "blocking": ["D4", "D6(numeric missing)", "D2"],
            "missing": "public Incucyte/viability numeric per well/time; independent culture; pi",
            "next": "request spec for functional numeric + well-level time series if author provides; no Stage2",
        },
        "gse248450": {
            "name": "GSE248450 — HCC4006 FUCCI real-time cell-cycle + RNA after osimertinib±tipifarnib",
            "source": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE248450",
                       "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE248nnn/GSE248450/"],
            "license": "NCBI GEO public data; no explicit license",
            "access": "public; series matrix 3.2 KB downloaded; FUCCI time-series numeric not in series matrix",
            "structure": geo["GSE248450"],
            "gates": {
                "D1": gate("partial", "RNA at 4/20/12 days; FUCCI real-time monitoring described, public function numeric missing"),
                "D2": gate("unclear", "same HCC4006 line; no culture/batch labels"),
                "D3": gate("partial", "drug dose/times present; function numeric missing"),
                "D4": gate("fail", "treatment labels only; no pi/randomization"),
                "D5": gate("partial", "FACS-sorted replicates; independent culture not certified"),
                "D6": gate("partial", "FUCCI cell-cycle + RNA; numeric not public → not usable D6 evidence"),
                "D7": gate("pass", "RNA counts"),
            },
            "overall": "not_qualified", "blocking": ["D4", "D6(numeric missing)", "D2"],
            "missing": "public FUCCI time-series numeric; independent culture; pi",
            "next": "request spec if author provides; not D6 evidence now",
        },
        "bbbc021": {
            "name": "BBBC021 — MCF7 compound-profiling high-content imaging",
            "source": ["https://bbbc.broadinstitute.org/BBBC021"],
            "license": "BBBC public data; no explicit license",
            "access": "public metadata CSVs downloaded; 55 image ZIPs ~750 MB each not downloaded",
            "structure": bbbc021,
            "gates": {
                "D1": gate("fail", "single treatment time 24 h (fixed cells); no multi-time functional series"),
                "D2": gate("partial", "plates/wells; technical replicates; no culture exchangeability"),
                "D3": gate("partial", "113 compounds × 8 concentrations at 24 h; imaging morphology, no viability/apoptosis numeric"),
                "D4": gate("fail", "compound labels only; no pi/randomization"),
                "D5": gate("partial", "well/plate replicates; independent culture not certified"),
                "D6": gate("fail", "DNA/F-actin/tubulin morphology only; no apoptosis/viability orthogonal function"),
                "D7": gate("fail", "no RNA/counts"),
            },
            "overall": "not_qualified", "blocking": ["D1", "D4", "D6", "D7"],
            "missing": "multi-time functional readout; orthogonal function; RNA pairing; pi",
            "next": "imaging benchmark only; not Stage2 data",
        },
        "bbbc022": {
            "name": "BBBC022 — U2OS Cell Painting compound profiling",
            "source": ["https://bbbc.broadinstitute.org/BBBC022"],
            "license": "BBBC public data; no explicit license",
            "access": "public metadata CSV 37 MB downloaded; image ZIPs not downloaded",
            "structure": bbbc022,
            "gates": {
                "D1": gate("fail", "single compound-profiling experiment; Image_Metadata_Time is acquisition timestamp, not treatment time"),
                "D2": gate("partial", "plates/wells technical replicates"),
                "D3": gate("partial", "compound/concentration; imaging morphology only"),
                "D4": gate("fail", "compound labels only; no pi"),
                "D5": gate("partial", "well replicates; independent culture not certified"),
                "D6": gate("fail", "Cell Painting morphology channels only; no apoptosis/viability function"),
                "D7": gate("fail", "no RNA/counts"),
            },
            "overall": "not_qualified", "blocking": ["D1", "D4", "D6", "D7"],
            "missing": "multi-time function; orthogonal function; RNA; pi",
            "next": "imaging benchmark only",
        },
        "ctos": {
            "name": "ctos-drug-response-networks (Zenodo 20043756) — colorectal cancer organoid derived data",
            "source": ["https://zenodo.org/records/20043756", "https://github.com/clinfo/ctos-drug-response-networks"],
            "license": "CC-BY-4.0",
            "access": "public 105,618 B zip downloaded; raw WES/RNA controlled access not shipped",
            "structure": ctos,
            "gates": {
                "D1": gate("fail", "viability single endpoint (drug_sensitivity_table); qPCR 8h/48h molecular only; no multi-time functional series"),
                "D2": gate("partial", "patient-derived organoids; no culture/batch exchangeability documentation"),
                "D3": gate("partial", "drug + viability_ratio endpoint; qPCR 8h/48h; no dose/time functional series"),
                "D4": gate("fail", "treatment labels only; no pi/randomization"),
                "D5": gate("partial", "replicate info not sufficient; independent culture not certified"),
                "D6": gate("partial", "viability + qPCR (orthogonal-ish), but qPCR only 8h/48h and no RNA counts public"),
                "D7": gate("partial", "qPCR + derived tables; raw RNA controlled access; no counts+RNA in release"),
            },
            "overall": "not_qualified", "blocking": ["D1", "D4", "D7", "D2"],
            "missing": "multi-time function; paired RNA counts; independent culture; pi",
            "next": "derived-data reference only; raw controlled access; not Stage2",
        },
        "az_gdsc": {
            "name": "AZ/GDSC 2024 — functional viability + caspase/PARP figures (DATA1/2/3)",
            "source": ["https://figshare.com/projects/163378", "https://gdsc-combinations.depmap.sanger.ac.uk/",
                       "research/2026-10-28-az-download-verify/report_data3.md"],
            "license": "public Figshare/GDSC; no explicit license; DATA1 no login/terms",
            "access": "public raw well ZIP 241 MB; mapping/functional numeric missing; no new download",
            "structure": {"available": ["72h CellTiter-Glo viability", "raw well intensities", "matrix summaries"],
                          "missing": ["experiment/occasion/technical replicate/treatment date/passage/culture mapping",
                                      "Fig4/5/6 caspase/PARP numeric", "paired RNA/counts"],
                          "D1_D7_note": "functional at 72h; six occasions/technical triplicates; no time series; no RNA"},
            "gates": {
                "D1": gate("partial", "72h viability + caspase/PARP reported; six occasions not multi-time; no RNA population snapshots"),
                "D2": gate("unclear", "no culture/batch mapping; technical triplicates≠independent"),
                "D3": gate("partial", "dose/time/viability; function numeric missing"),
                "D4": gate("fail", "no pi/randomization"),
                "D5": gate("partial", "6×3 technical; independent culture not certified"),
                "D6": gate("partial", "viability + caspase/PARP reported; numeric not public"),
                "D7": gate("fail", "no RNA/counts paired"),
            },
            "overall": "data_unavailable", "blocking": ["D1", "D4", "D7", "D2"],
            "missing": "mapping + function numeric + paired RNA/counts + independent culture",
            "next": "DATA1 request spec P0/P1; not Stage2",
        },
    }
    out["candidates"] = candidates

    out["search_log"] = {
        "bounded": True,
        "note": "bounded search only; not exhaustive; not_found != does not exist",
        "queries": [
            "GEO eutils gds: drug treatment time course apoptosis; drug treatment time course viability; caspase activity time course drug; high content imaging drug time course; organoid drug response time course; live cell imaging drug response time lapse",
            "GEO eutils gds: CellTiter-Glo time course; IncuCyte drug treatment; RealTime-Glo viability; caspase 3/7 time course drug; PARP cleavage time course drug",
            "GEO eutils gds: TRAIL time course RNA-seq; apoptosis RNA-seq time course drug; FACS apoptosis RNA-seq drug",
            "BioStudies/ArrayExpress API: drug time course apoptosis; organoid drug response time course (broad hits; no qualifying functional multi-time)",
            "Zenodo API: organoid time lapse drug response; spheroid drug response time lapse; IncuCyte drug response; RealTime-Glo viability time course; caspase time course drug",
            "BBBC: BBBC021/BBBC022 pages + metadata CSVs",
        ],
        "geo_hits": {
            "GSE149428": "matched time-course RNAseq of drug combinations; 0/3/6/9/12/24 h; RNA only",
            "GSE129012": "AZD4573 CDK9 inhibitor; 4/8 h RNA; apoptosis in paper, numeric not public",
            "GSE154932": "MDA-MB-231 doxorubicin; scRNA at 0/7/10 weeks; Incucyte protocol, numeric not public",
            "GSE248450": "HCC4006 FUCCI cell-cycle RNA at 4/20/12 days; function numeric not public",
        },
        "bbbc_hits": {
            "BBBC021": "MCF7 24 h fixed imaging, 113 compounds×8 concentrations, DNA/actin/tubulin; single time",
            "BBBC022": "U2OS Cell Painting; single time; Image_Metadata_Time is acquisition timestamp",
        },
        "zenodo_hits": {
            "20043756": "ctos-drug-response-networks derived data; viability endpoint + qPCR 8h; raw RNA controlled",
            "20718919": "TRACI IncuCyte test data; time-lapse migration example, not drug-response multi-time function",
            "20142884": "organoid 2D microscopy paper/images; no public multi-time functional table",
            "3333613": "DIPG viability method PDF; no multi-time dataset",
        },
        "not_found_in_bounded_search": [
            "public drug-induced multi-time functional numeric (apoptosis/caspase/PARP/viability/regrowth) paired with RNA/counts in the same culture/batch with recorded pi/randomization",
            "organoid/spheroid time-course dataset with public functional numeric + paired RNA/counts satisfying D1-D7",
        ],
        "not_found_meaning": "bounded search did not find; not evidence of absence",
    }
    out["overall"] = {
        "verdict": "not_qualified",
        "qualified_candidates": [],
        "partial_candidates": ["gse149428", "gse129012", "gse154932", "gse248450", "bbbc021", "bbbc022", "ctos", "az_gdsc"],
        "blocking_common": ["D4 (no recorded pi/randomization)", "D6 (no public orthogonal functional numeric)", "D2/D5 (independent culture/batch not certifiable)", "D1 (functional time series missing in RNA-only time courses)"],
        "m2_stage2_gate_status": "failed; data readiness remains open",
        "why_not_data_unavailable": "we retrieved and structurally verified several public RNA/imaging/organoid datasets; they fail gates, so not_qualified; AZ functional branch remains data_unavailable for missing mapping/function numeric.",
        "next": [
            "Do not run Stage2; do not synthesize/RNA-substitute independent functional decisions",
            "Keep AZ/GDSC DATA1 request spec P0/P1 (mapping, function numeric, per-barcode map)",
            "If public multi-time function + paired RNA/counts + pi + independent culture appears: wash/map/qualify under new protocol",
            "Bounded search only; no 'does not exist' claim",
        ],
        "no_claims": ["novelty", "migration", "decision benefit", "mechanism", "pharmacology"],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("WROTE", OUT)
    print(json.dumps({"verdict": out["overall"]["verdict"], "n_candidates": len(candidates),
                      "candidates": {k: v["overall"] for k, v in candidates.items()}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
