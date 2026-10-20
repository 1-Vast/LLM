"""Extract the audit-relevant numbers and absence scans from the supplementary files read for the audit.

Inputs are two directories holding the files that Europe PMC's `supplementaryFiles` bundles served for
PMC7610535 (S1) and PMC12833858 (S2). Those directories are not in the repository (about 70 MB, publisher
material); only this script's output, `supplement_extracts.json`, is. The output carries file digests so the
read is auditable, the AURKA rows as channel values, and keyword counts that document what the texts do and
do not contain.

Usage: python extract_supplements.py <S1_FILES_DIR> <S2_FILES_DIR>
"""
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
HERE = Path(__file__).resolve().parent


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sheet_rows(xlsx: Path, sheet_index: int, wanted):
    z = zipfile.ZipFile(xlsx)
    ss = ["".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])) for si in ET.parse(z.open("xl/sharedStrings.xml")).getroot().findall("m:si", NS)]
    root = ET.parse(z.open(f"xl/worksheets/sheet{sheet_index}.xml")).getroot()
    out = []
    for i, r in enumerate(root.find("m:sheetData", NS).findall("m:row", NS)):
        d = {}
        for c in r.findall("m:c", NS):
            v = c.find("m:v", NS)
            if v is not None:
                d[re.sub(r"\d", "", c.get("r"))] = ss[int(v.text)] if c.get("t") == "s" else v.text
        if wanted(i, d):
            out.append((i, d))
    return out


def pdf_text(p: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def scan(text: str, patterns: dict) -> dict:
    return {k: len(re.findall(v, text, flags=re.I)) for k, v in patterns.items()}


def main(s1_dir: Path, s2_dir: Path):
    out = {"note": "extracted by extract_supplements.py; inputs not stored in the repository", "files": {}, "values": {}, "scans": {}}
    for tag, d in (("S1", s1_dir), ("S2", s2_dir)):
        for p in sorted(d.iterdir()):
            if p.is_file():
                out["files"][f"{tag}/{p.name}"] = {"bytes": p.stat().st_size, "sha256": sha(p)}

    ds3 = s1_dir / "EMS118351-supplement-Supp_Data_Set_3_13_Aug.xlsx"
    hdr = sheet_rows(ds3, 2, lambda i, d: i == 5)[0][1]
    row = sheet_rows(ds3, 2, lambda i, d: d.get("C") == "AURKA")[0][1]
    chans = {hdr[k]: float(row[k]) for k in "KLMNOPQRST"}
    out["values"]["S1_DS3_IMR5_TMT_AURKA_log2_reporter"] = {
        "locator": "Supp Data Set 3, sheet 'PROTAC induced Degradation', gene AURKA", "cells": "IMR5", "dose_uM": 1.0, "time_h": 6,
        "channels": chans, "single_TMT11_batch": True, "vehicle_channel_present": False,
        "reported_stats_columns": {"log2FC_JB170_vs_alisertib": float(row["W"]), "log2FC_JB170_vs_JB211": float(row["Z"])}}

    s2x = s2_dir / "jm5c03024_si_002.xlsx"
    for idx, name in ((1, "CCT400028"), (2, "cmpd50"), (3, "JB170")):
        h = sheet_rows(s2x, idx, lambda i, d: i == 0)[0][1]
        r = sheet_rows(s2x, idx, lambda i, d: d.get("K") == "AURKA")[0][1]
        out["values"][f"S2_Kelly_proteomics_AURKA_{name}"] = {
            "locator": f"SI xlsx sheet {idx}, gene AURKA", "cells": "Kelly", "dose_uM": 1.0, "time_h": 4,
            "log2_channels": {h[k]: float(r[k]) for k in "EFGHIJ"}, "log2Ratio": float(r["D"]), "pval": float(r["B"]), "BH_adjusted_p": float(r["C"])}
    out["values"]["S2_SI_xlsx_compounds_in_proteomics"] = ["CCT400028", "cmpd 50", "JB170"]

    s1si = pdf_text(s1_dir / "EMS118351-supplement-Supplementary_Information_.pdf")
    s2si = pdf_text(s2_dir / "jm5c03024_si_001.pdf")
    pats = {"JB211": r"JB\s?211", "pT288_or_T288": r"p?T288|autophosph", "kinase_activity_assay": r"kinase (activity )?assay|in vitro kinase", "IC50": r"IC\s?50",
            "viability": r"viabil", "GI50": r"GI\s?50", "apoptosis": r"apopto|annexin", "alisertib": r"alisertib|MLN8237"}
    out["scans"]["S1_SI_pdf"] = scan(s1si, pats)
    out["scans"]["S2_SI_pdf"] = scan(s2si, {**pats, "compound_57": r"\b57\b", "inactive_control": r"inactive control"})
    out["scans"]["S2_SI_pdf"]["viability_mention_within_300_chars_of_57"] = sum(
        1 for m in re.finditer(r"\b57\b", s2si) if re.search(r"viabil|GI\s?50|alamar", s2si[max(0, m.start() - 300): m.end() + 300], flags=re.I))
    (HERE / "supplement_extracts.json").write_text(json.dumps(out, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("wrote supplement_extracts.json", len(out["files"]), "files catalogued")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
