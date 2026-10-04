"""Map O'Neil and NCI-ALMANAC cell-line names to DepMap 24Q2 models and record coverage.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/depmap_map.py
- Purpose: the untreated baseline state (expression, hotspot mutations, CRISPR-inferred growth
  rate) comes from DepMap, measured independently of both combination screens. This script maps
  screen names to DepMap ModelIDs with a declared match class per line and flags identity traps.
- Core points:
  - Match classes: EXACT (normalised name equals StrippedCellLineName), ALIAS (documented synonym:
    NCI-60 suffixes "/ATCC", "(TB)", "NIH:" prefix, digit-zero "786-0" vs letter "786-O",
    "SR" = SR-786, "MSTO" = MSTO-211H, "LNCAP" = LNCaP clone FGC), SIBLING (different derivative
    of the same patient: COLO320DM -> COLO-320, MDA-MB-435 -> MDA-MB-435S; excluded from analysis),
    UNMAPPED (no DepMap model: EFM192B (DepMap has only EFM-192A), UWB1289BRCA1 (only the parental
    UWB1.289), NCI/ADR-RES (OVCAR-8 derivative)).
  - Identity flags from DepMap PublicComments / Cellosaurus-known relations: KPL-1 is an MCF-7
    derivative; MDA-MB-435(S) is an M14 derivative (both M14 and MDA-MB-435 are ALMANAC lines);
    SNB-19 and U-251 MG share an origin; NCI/ADR-RES is OVCAR-8-derived.
  - Coverage of expression / hotspot mutation / CRISPR growth-rate rows per mapped model.
- Interfaces: `python depmap_map.py` -> outputs/depmap_mapping.csv, outputs/depmap_coverage.json
- Depends on: pandas; common.py.
"""
from __future__ import annotations

import json
import re

import pandas as pd

from common import ALMANAC, ONEIL, OUT, ROOT, load, sha256_file, write_json

DEPMAP = ROOT / "data/raw/depmap"
ALIAS = {   # screen name -> DepMap StrippedCellLineName (documented synonyms)
    "A549/ATCC": "A549", "MDA-MB-231/ATCC": "MDAMB231", "HL-60(TB)": "HL60", "OVCAR-3": "NIHOVCAR3",
    "OVCAR3": "NIHOVCAR3", "786-0": "786O", "U251": "U251MG", "SR": "SR786", "MSTO": "MSTO211H", "LNCAP": "LNCAPCLONEFGC",
}
SIBLING = {"COLO320DM": "COLO320", "MDA-MB-435": "MDAMB435S"}
UNMAPPED = {"EFM192B": "DepMap 24Q2 has EFM-192A (CVCL_1812) only; EFM-192B is a different line",
            "UWB1289BRCA1": "DepMap 24Q2 has only parental UWB1.289 (ACH-001418); BRCA1-restored derivative absent",
            "NCI/ADR-RES": "absent from DepMap 24Q2; OVCAR-8 derivative (do not substitute OVCAR-8)"}
FLAGS = {"KPL1": "DepMap: SNP fingerprint says MCF-7 derivative", "MDA-MB-435": "M14 derivative (also an ALMANAC line)",
         "M14": "MDA-MB-435 is an M14 derivative (also an ALMANAC line)", "SNB-19": "shares origin with U-251 MG (Cellosaurus)",
         "U251": "shares origin with SNB-19 (Cellosaurus)", "NCI/ADR-RES": "OVCAR-8 derivative (also an ALMANAC line)",
         "OVCAR-8": "NCI/ADR-RES is an OVCAR-8 derivative"}
# O'Neil tissue from its supplementary cell table (Supplementary Table 1, 'Indication')
ONEIL_TISSUE = {
    "MSTO": "Lung", "A2780": "Ovarian", "A375": "Melanoma", "DLD1": "Colon", "SKOV3": "Ovarian", "A2058": "Melanoma",
    "SKMEL30": "Melanoma", "RKO": "Colon", "KPL1": "Breast", "PA1": "Ovarian", "OCUBM": "Breast", "ES2": "Ovarian",
    "HT29": "Colon", "NCIH1650": "Lung", "NCIH2122": "Lung", "T47D": "Breast", "NCIH520": "Lung", "SKMES1": "Lung",
    "A427": "Lung", "EFM192B": "Breast", "UACC62": "Melanoma", "RPMI7951": "Melanoma", "SW620": "Colon",
    "NCIH460": "Lung", "SW837": "Colon", "VCAP": "Prostate", "LNCAP": "Prostate", "OVCAR3": "Ovarian",
    "MDAMB436": "Breast", "COLO320DM": "Colon", "HT144": "Melanoma", "NCIH23": "Lung", "OV90": "Ovarian",
    "HCT116": "Colon", "UWB1289BRCA1": "Ovarian", "CAOV3": "Ovarian", "LOVO": "Colon", "UWB1289": "Ovarian",
    "ZR751": "Breast"}


def norm(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(name).upper())


def main() -> int:
    model = pd.read_csv(DEPMAP / "Model.csv", dtype=str)
    model["key"] = model["StrippedCellLineName"].map(norm)
    by_key = {}
    for _, row in model.iterrows():
        by_key.setdefault(row["key"], []).append(row)
    expr_ids = set(pd.read_csv(DEPMAP / "OmicsExpressionProteinCodingGenesTPMLogp1.csv", usecols=[0]).iloc[:, 0])
    mut_ids = set(pd.read_csv(DEPMAP / "OmicsSomaticMutationsMatrixHotspot.csv", usecols=[0]).iloc[:, 0])
    growth = pd.read_csv(DEPMAP / "CRISPRInferredModelGrowthRate.csv")
    growth_ids = set(growth.loc[growth.iloc[:, 1:].notna().any(axis=1), "ModelID"])
    rows = []
    for screen, path in (("oneil", ONEIL), ("almanac", ALMANAC)):
        lib = load(path)
        for line in lib.lines:
            cls, target, note = "UNMAPPED", None, UNMAPPED.get(line, "")
            if line in UNMAPPED:
                pass
            elif line in SIBLING:
                cls, target = "SIBLING", SIBLING[line]
            elif line in ALIAS:
                cls, target = "ALIAS", ALIAS[line]
            elif norm(line) in by_key:
                cls, target = "EXACT", norm(line)
            else:
                note = "no normalised-name match"
            hit = by_key.get(target, [None])[0] if target else None
            mid = hit["ModelID"] if hit is not None else None
            rows.append({
                "screen": screen, "screen_line": line, "match_class": cls, "depmap_model_id": mid,
                "depmap_name": hit["CellLineName"] if hit is not None else None,
                "rrid": hit["RRID"] if hit is not None else None,
                "depmap_lineage": hit["OncotreeLineage"] if hit is not None else None,
                "screen_tissue": ONEIL_TISSUE.get(line) if screen == "oneil" else None,
                "expression": bool(mid in expr_ids) if mid else False,
                "hotspot_mutations": bool(mid in mut_ids) if mid else False,
                "crispr_growth_rate": bool(mid in growth_ids) if mid else False,
                "identity_flag": FLAGS.get(line, ""), "note": note,
                "depmap_public_comment": (hit["PublicComments"] if hit is not None and isinstance(hit["PublicComments"], str) else ""),
                "n_depmap_candidates_same_key": len(by_key.get(target, [])) if target else 0,
            })
    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "depmap_mapping.csv", index=False)
    coverage = {}
    for screen, g in frame.groupby("screen"):
        usable = g[g.match_class.isin(["EXACT", "ALIAS"])]
        coverage[screen] = {
            "lines": int(len(g)), "match_class_counts": g.match_class.value_counts().to_dict(),
            "usable_exact_or_alias": int(len(usable)),
            "with_expression": int(usable.expression.sum()), "with_hotspot_mutations": int(usable.hotspot_mutations.sum()),
            "with_crispr_growth_rate": int(usable.crispr_growth_rate.sum()),
            "identity_flags": g.loc[g.identity_flag != "", ["screen_line", "identity_flag"]].values.tolist(),
            "duplicate_model_ids": g.depmap_model_id.dropna()[g.depmap_model_id.dropna().duplicated()].tolist(),
        }
    provenance = {p.name: json.loads(p.read_text()) for p in DEPMAP.glob("*.provenance.json")}
    write_json("depmap_coverage.json", {
        "coverage": coverage,
        "depmap_release": sorted({v.get("release") for v in provenance.values()}),
        "depmap_published_date": sorted({v.get("published_date") for v in provenance.values()}),
        "depmap_md5_match": all(v.get("md5_match") for v in provenance.values()),
        "model_csv_sha256": sha256_file(DEPMAP / "Model.csv"),
    })
    print(frame[["screen", "screen_line", "match_class", "depmap_model_id", "expression", "identity_flag"]].to_string())
    print(json.dumps(coverage, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
