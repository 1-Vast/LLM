"""Source manifest and structural census of the PTV-1 / ProteinTalks release. Reads no sealed outcome value."""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, pandas as pd
import ptv_data as D

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()

R = D.Release(); rows = R.rows
log = (D.ROOT / "fetch.log").read_text().splitlines()
man = {"retrieved_utc": [l for l in log if " done " in l],
       "primary_article": {"url": "https://www.nature.com/articles/s41586-026-11001-9", "access": "public abstract page only; Methods paywalled; not read"},
       "supplement": {"url": "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-11001-9/MediaObjects/41586_2026_11001_MOESM1_ESM.pdf", "read_for": "table legends: 24 h sensitive/resistant labels, three biological replicates, labelling criteria 'described in the Methods' (not available)"},
       "github": {"repo": "https://github.com/guomics-lab/PTV-1", "commit": "23fc0c506978871c3836ac749f01b04d97c6bbc1", "licence": "MIT (LICENCE.md; dataset licence not stated)"},
       "data_host": {"url": "https://drive.google.com/drive/folders/1QRV-bD3zabVkFjznLR--Cca90fdU6Pr6", "access": "public share link, no login, 7 files",
                     "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(D.DRIVE.glob("*.csv"))}},
       "repo_files": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted((D.ROOT / "repo").glob("*"))},
       "checkpoint": {"file": "repo/best_checkpoint.pth", "layout": "5585 protein nodes, 935 drug features, hidden 64", "training_exposure": "UNKNOWN (layout matches this release; no split documented); NOT used for any held-out claim"},
       "dataset_licence": "not stated by the data host; academic/non-commercial use stated for the PTDS matrix at db.prottalks.com",
       "exposure": "public release; label prevalence per lineage and counts inspected during source check before the partition; every analysis from here is exposed development"}
ex = R.experiments()
single = ex[ex.ndrug == 1]; pair = ex[ex.ndrug == 2]
c = {}
c["rows"] = {"total": int(len(rows)), "by_time": rows.t.value_counts().sort_index().to_dict(), "proteins": len(R.nodes),
             "drug_rows": int(rows.is_drug.sum()), "control_or_baseline_rows": int((~rows.is_drug).sum())}
c["experiments"] = {"cell_by_perturbation_units": int(len(ex)), "single": int(len(single)), "pair": int(len(pair)),
                    "distinct_single_drugs": int(single.perts.nunique()), "distinct_pairs": int(pair.perts.nunique()),
                    "stocks": int(ex.cell.nunique()), "lineages": int(ex.lineage.nunique()),
                    "duplicate_runs_same_cell_perturbation": int((ex.n_records > 1).sum()), "duplicate_label_conflicts": int(ex.y_conflict.sum())}
pres = rows[rows.is_drug].drop_duplicates(["cell", "perts"]).groupby(["lineage"]).y_present.agg(["size", "sum"])
c["label_presence_by_lineage_all_parts"] = pres.to_dict("index")
c["labels_missing"] = {"single": int((~rows[rows.ndrug == 1].drop_duplicates(["cell", "perts"]).y_present).sum()),
                       "pair": int((~rows[rows.ndrug == 2].drop_duplicates(["cell", "perts"]).y_present).sum()),
                       "repo_loader_behaviour": "dataset.py maps NaN phenotype to 0.0 (resistant) - missing is NOT negative here"}
d = ex[ex.part != "final"]
c["pair_label_events"] = {"labelled_nonfinal": int(d[d.ndrug == 2].y.notna().sum()), "positives_nonfinal": int(d[d.ndrug == 2].y.sum()),
                          "note": "positives in sealed final lineages are not counted here; pair labels are NOT a single-agent efficacy endpoint (positive rate ~3.8 percent vs ~34 percent for single rows)"}
c["perturbation_tensor"] = {"values": [0.0, 0.5], "nonzero_fraction": float((R.P != 0).mean()),
                            "provenance": "per-perturbation constant (identical for every cell and time row of a perturbation id); pair vector == union of the two single vectors for all 59 pairs; it is a drug-target node encoding, NOT an experiment-derived PertScore and does not use the treated proteome",
                            "single_drugs_with_zero_target_nodes": int(sum(R.target_vector(p).sum() == 0 for p in single.perts.unique()))}
c["baseline_and_controls"] = {"t0_rows": int((rows.t == 0).sum()), "t0_rows_per_stock_max": int(rows[rows.t == 0].groupby("cell").size().max()),
                              "t0_zero_fraction_gt_0.5": int(((rows.t == 0) & (rows.zero_frac > 0.5)).sum()),
                              "repo_loader_baseline_rule": "first matching 0 h row by substring (regex) match: MDA-MB-453 inherits MDA-MB-453(ATCC)'s baseline; rows within a stock differ (corr ~0.67-0.74)",
                              "this_study_rule": "median log1p profile over a stock's 0 h rows with zero fraction <= 0.5",
                              "vehicle_control_labels_unexplained": sorted(rows[(~rows.is_drug) & (rows.t > 0)].perts.unique().tolist())}
c["missing_proteins"] = {"zero_fraction_all_rows": float((R._E == 0).mean()), "meaning": "0 = not quantified (protein missingness); repo normalisation log1p then per-sample min-max turns missing into the minimum value",
                         "treated_rows_zero_fraction_gt_0.9": int(((rows.is_drug) & (rows.zero_frac > 0.9)).sum())}
c["semantics_not_in_release"] = ["dose (none recorded)", "numerical sensitivity threshold (Methods paywalled)", "plate/batch/replicate id (none)", "the meaning of the pair label (efficacy or synergy)", "vehicle control definitions"]
c["partition"] = D.partition()
c["partition_counts"] = ex.groupby(["part", "ndrug"]).size().unstack().to_dict("index")
json.dump(man, open(D.STUDY / "SOURCE_MANIFEST.json", "w"), indent=1)
json.dump(c, open(D.STUDY / "CENSUS.json", "w"), indent=1, default=str)
print(json.dumps(c, indent=1, default=str)[:6000])
