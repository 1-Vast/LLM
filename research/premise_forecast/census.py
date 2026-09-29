"""E-AG1 stage 0: premise-only census of genetic-pharmacological discordance cases and premise capabilities.

File summary
- Path: research/premise_forecast/census.py
- Purpose: count, without reading any engagement or signature value, how many independent target
  genes have a real discordance case (strong selective CRISPR dependency, expressed target, inactive
  drug annotated to that target, in the same DepMap model) and a feasible, context-matched
  measurement of the missing interpretation premise. The rules are fixed in `census_spec.json`,
  written before this code ran.
- Core points:
  - Cases use the engagement_v1 archetype rule (`evaluation.engagement_cases.screen_mcf7` and
    `evaluation.construction.ARCHETYPE_THRESHOLDS`) on every DepMap model with PRISM 19Q4 secondary
    curves, one curve per (model, compound) by the package's screen preference.
  - Capabilities are typed by what they measure. `engagement_in_context` (PISA living-cell arm, K562)
    measures an engagement shift in intact cells. `proximal_activity_in_context` has no local or
    downloaded source. `phenocopy_*` (L1000 GSE92742 and GSE70138, LINCS 2020, CPJUMP1) says only
    that a same-cell compound signature and a same-cell knockdown or knockout signature of the target
    were planned: a pathway-level readout that the typed rules do not accept as engagement.
  - Only design columns are read from signature tables (identifiers, type, cell, dose, time);
    signature-quality columns and values are never read (`SIGINFO_COLUMNS`, `test_census.py`).
  - Counting unit: target gene. Cases, contexts and compounds are reported beside it.
  - Sensitivity (added after the specification, disclosed): `sensitivity_cases` also admits
    multi-target annotations with the primary target taken as the strongest dependency in the
    model (engagement_v1's K562 rule), and GDSC2 8.5 phenotypes (IC50 inside the screened range
    means active; engagement_v1's K562 source). GDSC2 compounds join signature tables by folded
    name only, so their phenocopy flags are name-matched. The registered decision uses the
    specified population; the sensitivity says whether it could change.
- Run: python -m research.premise_forecast.census [--out DIR]
- Interfaces: `discordance_cases`, `sensitivity_cases`, `capabilities`, `count`, `decide`, `main`, `SIGINFO_COLUMNS`
- Depends on: pandas; src/evaluation (thresholds, compound folding, PISA annotation reader)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools.evaluation.construction import ARCHETYPE_THRESHOLDS  # noqa: E402
from tools.evaluation.engagement_cases import (  # noqa: E402
    K562_MODEL, PISA_ANNOTATION_MEMBER, PISA_CELL_MEMBER, PISA_ZIP, PRISM_MAXIMUM_DOSE_MICROMOLAR,
    PRISM_SCREEN_PREFERENCE)
from tools.evaluation.engagement_sources import normalise_compound  # noqa: E402

OUT = ROOT / "outputs" / "premise_forecast_20260927" / "census"
SPEC = json.loads((Path(__file__).resolve().parent / "census_spec.json").read_text(encoding="utf-8"))
DEPMAP = ROOT / "data/raw/depmap"
PRISM = ROOT / "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv"
GSE92742 = ROOT / "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_sig_info.txt.gz"
GSE70138 = ROOT / "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz"
LINCS2020 = ROOT / "data/external/lincs2020"
JUMP = ROOT / "data/external/jump_target"
DEPENDENCY = -0.5
U2OS_MODEL = "ACH-000364"
SIGINFO_COLUMNS = {"geo": ["pert_id", "pert_iname", "pert_type", "cell_id", "pert_idose", "pert_itime"],
                   "lincs2020": ["pert_id", "pert_type", "cmap_name", "cell_iname", "pert_dose", "pert_dose_unit",
                                 "pert_time", "pert_time_unit"]}
FORBIDDEN_COLUMNS = {"cc_q75", "tas", "pct_self_rank_q25", "is_hiq", "qc_pass", "distil_cc_q75", "distil_ss",
                     "median_recall_rank_spearman", "median_recall_rank_wtcs_50", "median_recall_score_spearman",
                     "median_recall_score_wtcs_50", "is_exemplar_sig", "is_ncs_sig", "is_null_sig"}


def _brd(identifier) -> str | None:
    text = str(identifier or "").strip()
    return text[:13] if text.startswith("BRD-") and len(text) >= 13 else None


def _stripped(name) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(name or "").upper())


# ------------------------------------------------------------------------------ cases
def _prism_curves() -> pd.DataFrame:
    cols = ["broad_id", "depmap_id", "screen_id", "name", "target", "ic50", "r2", "auc", "moa"]
    frame = pd.read_csv(PRISM, usecols=cols, dtype={"broad_id": str, "depmap_id": str, "screen_id": str, "name": str,
                                                   "target": str, "moa": str})
    frame["name"] = frame.name.fillna("").str.strip()
    frame["target"] = frame.target.fillna("").str.strip()
    frame = frame[(frame.name != "") & (frame.target != "") & ~frame.target.str.contains(",")].copy()
    rank = {s: i for i, s in enumerate(PRISM_SCREEN_PREFERENCE)}
    frame["screen_rank"] = frame.screen_id.map(rank).fillna(99)
    frame = frame.sort_values(["depmap_id", "name", "screen_rank"]).drop_duplicates(["depmap_id", "name"])
    return frame.reset_index(drop=True)


def _gene_matrix(path: Path, genes: set) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0).columns
    keep = {c: c.split(" (")[0].strip() for c in header[1:] if c.split(" (")[0].strip() in genes}
    frame = pd.read_csv(path, usecols=[header[0], *keep], index_col=0)
    frame = frame.rename(columns=keep)
    return frame.loc[:, ~frame.columns.duplicated()]


def discordance_cases(*, require_selective: bool = True) -> tuple[pd.DataFrame, dict]:
    """Every (model, compound, target) meeting the engagement-gap rule, and why the others fail."""
    t = ARCHETYPE_THRESHOLDS
    curves = _prism_curves()
    genes = set(curves.target)
    effect = _gene_matrix(DEPMAP / "CRISPRGeneEffect.csv", genes)
    expression = _gene_matrix(DEPMAP / "OmicsExpressionProteinCodingGenesTPMLogp1.csv", genes)
    fraction = (effect <= DEPENDENCY).sum() / effect.notna().sum()
    curves["gene_effect"] = [effect.at[m, g] if m in effect.index and g in effect.columns else np.nan
                             for m, g in zip(curves.depmap_id, curves.target)]
    curves["expression"] = [expression.at[m, g] if m in expression.index and g in expression.columns else np.nan
                            for m, g in zip(curves.depmap_id, curves.target)]
    curves["dependent_fraction"] = curves.target.map(fraction)
    curves["active"] = curves.ic50.notna() & (curves.ic50 <= PRISM_MAXIMUM_DOSE_MICROMOLAR + 1e-12)
    reasons = {}
    fit = curves.r2 >= t["minimum_curve_r2"]
    premise = curves.gene_effect.notna() & curves.expression.notna() & curves.dependent_fraction.notna()
    strong = curves.gene_effect <= t["strong_dependency"]
    selective = curves.dependent_fraction <= t["selective_gene_fraction"]
    expressed = curves.expression >= t["expressed_log2_tpm1"]
    rule = fit & premise & strong & expressed & ~curves.active & (selective if require_selective else True)
    reasons = {"curves_single_target": int(len(curves)), "curve_fit_below_minimum": int((~fit).sum()),
               "premise_incomplete": int((fit & ~premise).sum()),
               "not_strong_dependency": int((fit & premise & ~strong).sum()),
               "not_expressed": int((fit & premise & strong & ~expressed).sum()),
               "compound_active": int((fit & premise & strong & expressed & curves.active).sum()),
               "not_selective": int((fit & premise & strong & expressed & ~curves.active & ~selective).sum()),
               "cases": int(rule.sum())}
    concordant = fit & premise & strong & selective & expressed & curves.active
    cases = curves[rule].copy()
    cases["archetype"] = "engagement_gap_or_mode"
    refs = curves[concordant].copy()
    refs["archetype"] = "concordant_support"
    return pd.concat([cases, refs], ignore_index=True), reasons


GDSC2 = ROOT / "data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx"


def _primary(targets, model, effect) -> str | None:
    """engagement_v1's rule: the annotated target with the strongest dependency in this model."""
    scored = [(effect.at[model, g], g) for g in targets
              if model in effect.index and g in effect.columns and pd.notna(effect.at[model, g])]
    return sorted(scored)[0][1] if scored else None


def sensitivity_cases(*, require_selective: bool = True) -> tuple[pd.DataFrame, dict]:
    """PRISM with multi-target annotations, and GDSC2 8.5, under the same thresholds."""
    t = ARCHETYPE_THRESHOLDS
    cols = ["broad_id", "depmap_id", "screen_id", "name", "target", "ic50", "r2"]
    prism = pd.read_csv(PRISM, usecols=cols, dtype={"broad_id": str, "depmap_id": str, "screen_id": str, "name": str,
                                                   "target": str})
    prism["name"] = prism.name.fillna("").str.strip()
    prism = prism[(prism.name != "") & prism.target.notna()].copy()
    rank = {s: i for i, s in enumerate(PRISM_SCREEN_PREFERENCE)}
    prism["screen_rank"] = prism.screen_id.map(rank).fillna(99)
    prism = prism.sort_values(["depmap_id", "name", "screen_rank"]).drop_duplicates(["depmap_id", "name"])
    prism = prism[prism.r2 >= t["minimum_curve_r2"]]
    prism["targets"] = prism.target.str.split(r",\s*")
    prism["active"] = prism.ic50.notna() & (prism.ic50 <= PRISM_MAXIMUM_DOSE_MICROMOLAR + 1e-12)
    prism["source"] = "PRISM 19Q4 (multi-target admitted)"
    gdsc = pd.read_excel(GDSC2, usecols=["SANGER_MODEL_ID", "DRUG_NAME", "PUTATIVE_TARGET", "MAX_CONC", "LN_IC50"])
    models = pd.read_csv(DEPMAP / "Model.csv", usecols=["ModelID", "SangerModelID"], dtype=str).dropna()
    gdsc = gdsc.merge(models, left_on="SANGER_MODEL_ID", right_on="SangerModelID")
    gdsc = gdsc.assign(depmap_id=gdsc.ModelID, name=gdsc.DRUG_NAME.astype(str).str.strip(), broad_id=None,
                       targets=gdsc.PUTATIVE_TARGET.fillna("").astype(str).str.split(r",\s*"),
                       active=np.exp(gdsc.LN_IC50) <= gdsc.MAX_CONC + 1e-12, source="GDSC2 8.5")
    frame = pd.concat([prism[["depmap_id", "name", "broad_id", "targets", "active", "source"]],
                       gdsc[["depmap_id", "name", "broad_id", "targets", "active", "source"]]], ignore_index=True)
    genes = {g for ts in frame.targets for g in ts if g}
    effect = _gene_matrix(DEPMAP / "CRISPRGeneEffect.csv", genes)
    expression = _gene_matrix(DEPMAP / "OmicsExpressionProteinCodingGenesTPMLogp1.csv", genes)
    fraction = (effect <= DEPENDENCY).sum() / effect.notna().sum()
    frame["target"] = [_primary([g for g in ts if g], m, effect) for ts, m in zip(frame.targets, frame.depmap_id)]
    frame = frame[frame.target.notna()].copy()
    frame["gene_effect"] = [effect.at[m, g] for m, g in zip(frame.depmap_id, frame.target)]
    frame["expression"] = [expression.at[m, g] if m in expression.index and g in expression.columns else np.nan
                           for m, g in zip(frame.depmap_id, frame.target)]
    frame["dependent_fraction"] = frame.target.map(fraction)
    selective = (frame.dependent_fraction <= t["selective_gene_fraction"]) if require_selective else True
    rule = (frame.gene_effect <= t["strong_dependency"]) & selective \
        & (frame.expression >= t["expressed_log2_tpm1"]) & ~frame.active
    cases = frame[rule].drop(columns=["targets"]).copy()
    cases["archetype"] = "engagement_gap_or_mode"
    return cases.reset_index(drop=True), {"curves_with_scored_primary_target": int(len(frame)), "cases": int(rule.sum()),
                                           "target_genes_by_source": cases.groupby("source").target.nunique().to_dict()}


# ------------------------------------------------------------------------------ capabilities
def _models() -> pd.DataFrame:
    m = pd.read_csv(DEPMAP / "Model.csv", usecols=["ModelID", "StrippedCellLineName", "CCLEName"], dtype=str)
    m["stripped"] = m.StrippedCellLineName.map(_stripped)
    return m


def _geo_signatures(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t", usecols=SIGINFO_COLUMNS["geo"], dtype=str)
    frame["cell"] = frame.cell_id.str.split(".").str[0].map(_stripped)
    dose = frame.pert_idose.str.extract(r"([0-9.]+)\s*(\S+)")
    scale = dose[1].map({"µM": 1.0, "um": 1.0, "uM": 1.0, "nM": 1e-3, "nm": 1e-3}).astype(float)
    frame["dose_um"] = dose[0].astype(float) * scale
    frame["time_h"] = frame.pert_itime.str.extract(r"([0-9.]+)")[0].astype(float)
    frame["brd"] = frame.pert_id.map(_brd)
    frame["gene"] = frame.pert_iname
    frame["folded"] = frame.pert_iname.fillna("").astype(str).map(normalise_compound)
    return frame


def _lincs2020_signatures() -> pd.DataFrame:
    frame = pd.read_csv(LINCS2020 / "siginfo_beta.txt", sep="\t", usecols=SIGINFO_COLUMNS["lincs2020"], dtype=str)
    cells = pd.read_csv(LINCS2020 / "cellinfo_beta.txt", sep="\t", usecols=["cell_iname", "ccle_name"], dtype=str)
    frame = frame.merge(cells, on="cell_iname", how="left")
    frame["cell"] = frame.cell_iname.map(_stripped)
    unit = frame.pert_dose_unit.fillna("").str.lower().map({"um": 1.0, "µm": 1.0, "nm": 1e-3})
    frame["dose_um"] = pd.to_numeric(frame.pert_dose, errors="coerce") * unit
    frame["time_h"] = pd.to_numeric(frame.pert_time, errors="coerce")
    frame["brd"] = frame.pert_id.map(_brd)
    frame["gene"] = frame.cmap_name
    frame["folded"] = frame.cmap_name.fillna("").astype(str).map(normalise_compound)
    return frame


def _pairs(frame: pd.DataFrame, compound_types, gene_types) -> tuple[set, set, dict]:
    """(cell, brd) with a compound signature <= 10 uM and (cell, gene) with a knockdown/knockout signature."""
    cp = frame[frame.pert_type.isin(compound_types) & (frame.dose_um <= PRISM_MAXIMUM_DOSE_MICROMOLAR + 1e-9)]
    kd = frame[frame.pert_type.isin(gene_types)]
    compounds = set(zip(cp.cell, cp.brd)) | {(c, "name:" + f) for c, f in zip(cp.cell, cp.folded)}
    genes = set(zip(kd.cell, kd.gene))
    times = {"compound_h": sorted(cp.time_h.dropna().unique().tolist()), "genetic_h": sorted(kd.time_h.dropna().unique().tolist())}
    return compounds, genes, times


def _pisa_coverage() -> tuple[set, set, dict]:
    """Compound labels (cell-arm header) and quantified gene symbols (first column); no value cell is read."""
    from tools.evaluation.engagement_cases import _pisa_annotation
    from tools.evaluation.engagement_sources import Workbook
    workbook = Workbook(ROOT / PISA_ZIP, member=PISA_CELL_MEMBER)
    rows = workbook.rows("Cell-based data")
    header = next(rows)
    labels = set()
    for value in header[1:]:
        match = re.match(r"^(?P<label>.+)_Log2FC_Rep\d+$", str(value or "").strip())
        if match and not match.group("label").upper().startswith("DMSO"):
            labels.add(normalise_compound(match.group("label").strip()))
    genes = set()
    for row in rows:
        if row and isinstance(row[0], str):
            genes.add(row[0].strip().split("_")[0])
    workbook.close()
    annotation = _pisa_annotation(ROOT / PISA_ZIP)
    in_cells = {normalise_compound(k) for k, v in annotation.items() if v["in_cells"]}
    return labels & in_cells, genes, {k: v for k, v in annotation.items()}


def _jump() -> tuple[dict, set]:
    compounds = pd.read_csv(JUMP / "JUMP-Target-1_compound_metadata.tsv", sep="\t", dtype=str)
    crispr = pd.read_csv(JUMP / "JUMP-Target-1_crispr_metadata.tsv", sep="\t", dtype=str)
    design = pd.read_csv(JUMP / "CPJUMP1_experiment-metadata.tsv", sep="\t", dtype=str)
    main = design[design.Batch == "2020_11_04_CPJUMP1"]
    cells = {p: set(main[main.Perturbation == p].Cell_type) for p in ("compound", "crispr")}
    both = cells["compound"] & cells["crispr"]
    treated = compounds[compounds.pert_type == "trt"]
    brd = {}
    for b, name, t in zip(treated.broad_sample, treated.pert_iname, treated.target_list):
        targets = set(str(t).split("|"))
        for key in (_brd(b), "name:" + normalise_compound(str(name or ""))):
            if key:
                brd.setdefault(key, set()).update(targets)
    genes = set(crispr[crispr.pert_type == "trt"].gene.dropna())
    return {"compound_targets": brd, "crispr_genes": genes, "cells": both}, genes


def capabilities(cases: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    models = _models()
    stripped = dict(zip(models.ModelID, models.stripped))
    cases = cases.copy()
    cases["cell"] = cases.depmap_id.map(stripped)
    cases["brd"] = [_brd(b) or "name:" + normalise_compound(n) for b, n in zip(cases.broad_id, cases.name)]
    cases["folded"] = cases.name.map(normalise_compound)
    cases["identity_route"] = ["broad_id" if _brd(b) else "folded_name" for b in cases.broad_id]
    notes = {}
    pisa_compounds, pisa_genes, _ = _pisa_coverage()
    cases["engagement_in_context"] = (cases.depmap_id == K562_MODEL) & cases.folded.isin(pisa_compounds) & \
        cases.target.isin(pisa_genes)
    cases["proximal_activity_in_context"] = False
    geo1 = _geo_signatures(GSE92742)
    c1, g1, notes["gse92742_times"] = _pairs(geo1, {"trt_cp"}, {"trt_sh.cgs"})
    geo2 = _geo_signatures(GSE70138)
    c2, g2, notes["gse70138_times"] = _pairs(geo2, {"trt_cp"}, {"trt_xpr"})
    lincs = _lincs2020_signatures()
    c3, g3, notes["lincs2020_times"] = _pairs(lincs, {"trt_cp"}, {"trt_sh.cgs", "trt_xpr"})
    cases["phenocopy_gse92742"] = [(c, b) in c1 and (c, g) in g1 for c, b, g in zip(cases.cell, cases.brd, cases.target)]
    # GSE70138 knockouts are in Cas9 derivatives of the same line ('A375.311'); both GEO series share cell names
    cases["phenocopy_geo_any"] = [((c, b) in c1 or (c, b) in c2) and ((c, g) in g1 or (c, g) in g2)
                                  for c, b, g in zip(cases.cell, cases.brd, cases.target)]
    cases["phenocopy_lincs2020"] = [(c, b) in c3 and (c, g) in g3 for c, b, g in zip(cases.cell, cases.brd, cases.target)]
    jump, _ = _jump()
    jump_cells = {_stripped(c) for c in jump["cells"]}
    cases["phenocopy_cpjump1"] = [c in jump_cells and b in jump["compound_targets"] and g in jump["crispr_genes"]
                                  and g in jump["compound_targets"][b]
                                  for c, b, g in zip(cases.cell, cases.brd, cases.target)]
    cases["phenocopy_same_cell"] = cases[["phenocopy_geo_any", "phenocopy_lincs2020", "phenocopy_cpjump1"]].any(axis=1)
    cases["strict_premise_capability"] = cases.engagement_in_context | cases.proximal_activity_in_context
    notes["cpjump1_cells"] = sorted(jump["cells"])
    notes["pisa"] = {"compounds_in_cells": len(pisa_compounds), "genes_quantified": len(pisa_genes)}
    return cases, notes


def count(frame: pd.DataFrame, column: str | None = None) -> dict:
    sub = frame if column is None else frame[frame[column]]
    return {"cases": int(len(sub)), "target_genes": int(sub.target.nunique()), "contexts": int(sub.depmap_id.nunique()),
            "compounds": int(sub.name.nunique())}


CAPABILITY_COLUMNS = ("strict_premise_capability", "engagement_in_context", "proximal_activity_in_context",
                      "phenocopy_same_cell", "phenocopy_gse92742", "phenocopy_geo_any", "phenocopy_lincs2020",
                      "phenocopy_cpjump1")


MINIMUM_CLUSTERS = 30
MINIMUM_REFERENCES_PER_BRANCH = 20


def decide(strict: int, phenocopy: int, joint: int) -> dict:
    """The census decisions of `census_spec.json`, from target-gene cluster counts."""
    return {"AG-G0_population": "READY_FOR_STAGE1_PREREGISTRATION" if strict >= MINIMUM_CLUSTERS else "NOT_READY",
            "strict_target_gene_clusters": strict,
            "phenocopy_track": "CANDIDATE_TASK_FOR_A_DIFFERENT_PREMISE" if phenocopy >= MINIMUM_CLUSTERS else "INSUFFICIENT",
            "phenocopy_target_gene_clusters": phenocopy,
            "joint_task": ("CANDIDATE" if joint >= MINIMUM_REFERENCES_PER_BRANCH else "NOT_READY"),
            "joint_rule": "target genes whose case has both an independently labelled premise measurement (engagement "
                          "in context) and a forecastable readout (same-cell phenocopy); >= 20 needed per branch",
            "joint_target_genes": joint}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    result = {"spec": "research/premise_forecast/census_spec.json", "populations": {}}
    tables = []
    for selective in (True, False):
        frame, reasons = discordance_cases(require_selective=selective)
        frame, notes = capabilities(frame)
        label = "selective" if selective else "any_dependency"
        cases = frame[frame.archetype == "engagement_gap_or_mode"]
        refs = frame[frame.archetype == "concordant_support"]
        entry = {"screening": reasons, "notes": notes, "all": count(cases),
                 "by_capability": {c: count(cases, c) for c in CAPABILITY_COLUMNS},
                 "concordant_references": {"all": count(refs), **{c: count(refs, c) for c in CAPABILITY_COLUMNS}}}
        phen = cases[cases.phenocopy_same_cell]
        entry["phenocopy_by_context"] = phen.groupby("cell").target.nunique().sort_values(ascending=False).to_dict()
        entry["strict_genes"] = sorted(cases[cases.strict_premise_capability].target.unique())
        entry["joint_target_genes"] = int(cases[cases.strict_premise_capability & cases.phenocopy_same_cell].target.nunique())
        result["populations"][label] = entry
        frame.assign(population=label).to_csv(out / f"cases_{label}.csv", index=False, lineterminator="\n")
        tables.append(entry)
    result["sensitivity"] = {}
    for selective in (True, False):
        label = "selective" if selective else "any_dependency"
        frame, reasons = sensitivity_cases(require_selective=selective)
        frame, notes = capabilities(frame)
        frame.assign(population=f"sensitivity_{label}").to_csv(out / f"cases_sensitivity_{label}.csv", index=False,
                                                               lineterminator="\n")
        result["sensitivity"][label] = {
            "screening": reasons, "all": count(frame), "by_capability": {c: count(frame, c) for c in CAPABILITY_COLUMNS},
            "strict_genes": sorted(frame[frame.strict_premise_capability].target.unique()),
            "phenocopy_genes": sorted(frame[frame.phenocopy_same_cell].target.unique()),
            "joint_target_genes": int(frame[frame.strict_premise_capability & frame.phenocopy_same_cell].target.nunique()),
            "phenocopy_by_context": frame[frame.phenocopy_same_cell].groupby("cell").target.nunique()
            .sort_values(ascending=False).to_dict(),
            "note": "added after the specification; GDSC2 compounds are name-matched to signature tables"}
    sel = result["populations"]["selective"]
    result["decisions"] = decide(sel["by_capability"]["strict_premise_capability"]["target_genes"],
                                 sel["by_capability"]["phenocopy_same_cell"]["target_genes"],
                                 sel["joint_target_genes"])
    result["decisions_if_sensitivity_were_primary"] = {
        label: decide(e["by_capability"]["strict_premise_capability"]["target_genes"],
                      e["by_capability"]["phenocopy_same_cell"]["target_genes"], e["joint_target_genes"])
        for label, e in result["sensitivity"].items()}
    (out / "census.json").write_bytes(json.dumps(result, indent=1, default=float).encode("utf-8") + b"\n")
    print(json.dumps({k: {"screening": v["screening"], "all": v["all"], "by_capability": v["by_capability"]}
                      for k, v in result["populations"].items()}, indent=1))
    for label, entry in result["sensitivity"].items():
        print("sensitivity", label, json.dumps({k: entry[k] for k in ("screening", "all", "strict_genes", "phenocopy_genes")}),
              {c: (v["cases"], v["target_genes"]) for c, v in entry["by_capability"].items()})
    print(json.dumps(result["decisions"], indent=1))


if __name__ == "__main__":
    main()
