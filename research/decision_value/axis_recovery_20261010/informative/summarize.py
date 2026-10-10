"""Rebuild observability hints and exclusions from bounded named-table ranges."""
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from fetch import ROOT, records
from project import read_plate1, retained


STUDY = ROOT.parent.parent
RELIABILITY = STUDY / "observation_reliability"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    endpoint = json.loads((RELIABILITY / "ENDPOINT.json").read_text())
    sentinel = json.loads((RELIABILITY / "literature/UPDATED_SENTINELS.json").read_text())
    sample_path = RELIABILITY / "literature/sources/tahoe_sample_parquet.parquet"
    assert digest(sample_path) == "33167f0ce28cff8357c503cda67d1c7fea200bff6918ee1de3c4f3549175b9d3"
    sample = pd.read_parquet(sample_path)
    cell_receipt, cell_body = retained("official_cell_metadata")
    assert hashlib.sha256(cell_body).hexdigest() == "67641f5bdd3fb077978ff1fec4d0d617490674bcd42850515ae3997194c29d4d"
    cell = pd.read_parquet(io.BytesIO(cell_body))
    table, plans, metadata = read_plate1(["cell_line", "treatment"] + endpoint["symbols"])
    frame = table.to_pandas()
    assert len(frame) == 4443 and len(metadata.schema.names) == 2002
    conditions = sorted(set(frame.treatment))
    assert len(conditions) == 92 and len(set(frame.cell_line)) == 50
    official = sample.loc[sample.plate.eq("plate1") & sample.drugname_drugconc.isin(conditions)]
    assert set(conditions) == set(official.drugname_drugconc)
    controls = sample.loc[sample.plate.eq("plate1") & sample.drug.eq("DMSO_TF")]
    excluded_samples = sorted(set(official["sample"]) | set(controls["sample"]))
    protected_samples = {sid for entry in sentinel["selected"] for sid in entry["sample_counts"]}
    assert not set(conditions) & set(sentinel["selected_labels"])
    assert not set(excluded_samples) & protected_samples
    _, gene_body = retained("static_2k_genes")
    genes = json.loads(gene_body)
    assert len(genes) == len(set(genes)) == 2000
    assert genes == metadata.schema.names[2:]
    assert [genes[i] for i in endpoint["coordinates"]] == endpoint["symbols"]
    coverage = []
    for name, sid in (("c44.h5ad", "CVCL_1715"), ("c45.h5ad", "CVCL_1716")):
        identities = cell.loc[cell.Cell_ID_Cellosaur.eq(sid),
                              ["cell_name", "Cell_ID_Cellosaur", "Cell_ID_DepMap"]].drop_duplicates()
        assert len(identities) == 1
        subset = frame.loc[frame.cell_line.eq(sid)]
        gene_statistics = []
        for gene in endpoint["symbols"]:
            positives = subset.loc[subset[gene] > 0].sort_values([gene, "treatment"], ascending=[False, True])
            gene_statistics.append({"gene": gene, "positive_delta_conditions": len(positives),
                "nonzero_delta_conditions": int((subset[gene] != 0).sum()),
                "top_positive_conditions": positives[["treatment", gene]].head(3).rename(
                    columns={gene: "delta"}).to_dict("records")})
        coverage.append({"file": name, "cell_identity": identities.to_dict("records")[0],
                         "named_condition_rows": len(subset), "gene_statistics": gene_statistics})
    ledger = records()
    body_bytes = sum(r["received_body_bytes"] for r in ledger)
    assert body_bytes <= 25_000_000
    output = {"schema": "named_summary_observability_hints_v1",
        "status": "SOURCE_BOUNDED_HINTS_FOUND; FILTERED_AXIS_NOT_CERTIFIED",
        "repo": "tahoebio/tahoe-de-rhaister", "revision": "c7963cf334bec0683225d41c9586d900ca6303a2",
        "table": "cell_eval/plate_plate1.parquet", "table_size": 65_704_666,
        "table_lfs_sha256": "496a7727899fd16a590e535f6a3007f3ded6f120ad2aa10edc2f5a30ea924c16",
        "full_table_sha256_recomputed": False, "requested_gene_columns": endpoint["symbols"],
        "static_list_sha256": hashlib.sha256(gene_body).hexdigest(),
        "all39_declared_index_name_agreement": True, "actual_file_axis_certified": False,
        "checkpoint_output_axis_certified": False, "files": coverage,
        "source_preprocessing_lineage": "UNKNOWN: README sayslinear(normalized)delta; releasedRhaisterproducer applieslog1p(X_hvg). Neither provesexactStateFilteredrevision/rows/transform.",
        "interpretation": "Positive named deltas guide possible observability only; no target_mean, per-cell nonzero probability, noise estimate or axis identity is established.",
        "range_plans": plans, "network_http_responses_including_redirects": len(ledger),
        "measurable_received_body_bytes": body_bytes,
        "unmeasured_transport_failure": [r for r in ledger if r["status"] == "NETWORK_ERROR"],
        "new_raw_paired_cell_RNA_bytes": 0, "new_LLM_API_calls": 0,
        "local_cached_reads_new_network_bytes": 0, "future_independent_evaluation_exclusion": "All consultedplate1treatmentpooledsamples andpotentialplate1referencecontrols acrossalllines. Summaries areexpressionexposure.",
        "independent_decision_gain_claimed": False}
    exclusions = {"schema": "named_summary_expression_exclusions_v1", "source_revision": output["revision"],
        "scope": "Entire consultedplate1table rowgroup:4443rows,50lines,92noncontrollabels,39namedgene rowvalues; footeraggregate statistics for2000namedgenes.",
        "rowwise_expression_genes": endpoint["symbols"], "aggregate_footer_genes": genes,
        "line_ids": sorted(set(frame.cell_line)), "labels": conditions,
        "excluded_pooled_sample_ids": excluded_samples,
        "consulted_treatment_sample_ids": sorted(set(official["sample"])),
        "potential_reference_control_sample_ids": sorted(set(controls["sample"])),
        "actual_producer_reference_sample_join": "UNKNOWN; allplate1DMSOpooledsamples excludedconservatively, no independentculturecount inferred",
        "all_official_plate_label_joins_pass": True,
        "sentinel_label_overlap": [], "sentinel_pooled_sample_overlap": [],
        "exclusion_applies_to_all_lines_sharing_sample": True,
        "future_independent_decision_evaluation_allowed": False}
    return output, exclusions


if __name__ == "__main__":
    output, exclusions = build()
    for name, value in (("COVERAGE.json", output), ("EXPOSURES.json", exclusions)):
        (ROOT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": [{"file": row["file"], "positive_genes": sum(
        g["positive_delta_conditions"] > 0 for g in row["gene_statistics"])} for row in output["files"]],
        "network_bytes": output["measurable_received_body_bytes"],
        "excluded_pooled_samples": len(exclusions["excluded_pooled_sample_ids"])}))
