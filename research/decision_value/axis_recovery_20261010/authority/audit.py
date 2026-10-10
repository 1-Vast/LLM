"""Offline verification of bounded public axis-authority evidence."""
import argparse
import hashlib
import io
import json
import pickle
import zipfile
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources"
DATASET_REV = "fdf87abece385feea6fa5e9944ab46e173b6af50"
CHECKPOINT_REV = "ca6b751972493f8448e3256d1340ae70ad43e1e7"
CANDIDATE_HASH = "6a29f993fbf166ed0c07eea58517b61a63c92ffec9e5fe8c9588593e7a8fa243"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


class MetadataUnpickler(pickle.Unpickler):
    """Allow only the two NumPy globals used by this retained metadata."""

    def find_class(self, module, name):
        allowed = {
            ("numpy", "dtype"): np.dtype,
            ("numpy._core.multiarray", "scalar"): np._core.multiarray.scalar,
        }
        if (module, name) not in allowed:
            raise pickle.UnpicklingError(f"Forbidden global: {module}.{name}")
        return allowed[(module, name)]


def audit():
    receipts = read_json(HERE / "RECEIPTS.json")
    reused = read_json(HERE / "REUSED_SOURCES.json")
    records = receipts["records"] + reused["records"]
    for row in records:
        require(row["status"] == "retained", f"Unretained source: {row['name']}")
        path = HERE / row["path"]
        require(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                f"Source hash mismatch: {row['name']}")
    received = sum(row["bytes"] for row in receipts["records"])
    require(received == receipts["successful_body_bytes"], "Response-byte total mismatch")
    require(received == receipts["known_all_received_body_bytes"] <= 5_000_000,
            "Public-body cap exceeded or accounting incomplete")
    require(receipts["expression_data_requested"] is False, "Expression access forbidden")
    require(receipts["maintainer_messages_sent"] is False, "Maintainer messages forbidden")
    dataset_info = read_json(SOURCES / "DATASET_INFO.json")
    model_info = read_json(SOURCES / "MODEL_INFO.json")
    require(dataset_info["sha"] == DATASET_REV, "Wrong dataset release")
    require(model_info["sha"] == CHECKPOINT_REV, "Wrong checkpoint release")
    dims = MetadataUnpickler(io.BytesIO((SOURCES / "CHECKPOINT_VAR_DIMS.pkl").read_bytes())).load()
    hparams = yaml.safe_load((SOURCES / "CHECKPOINT_HPARAMS.yaml").read_text())
    with zipfile.ZipFile(SOURCES / "CHECKPOINT_DATA_MODULE.torch") as archive:
        data_module = MetadataUnpickler(io.BytesIO(archive.read("archive/data.pkl"))).load()
    genes = dims["gene_names"]
    require(genes == hparams["gene_names"] and len(genes) == len(set(genes)) == 62710,
            "Checkpoint full-gene metadata disagree")
    for data in (dims, hparams):
        require(all(int(data[k]) == 2000 for k in ("input_dim", "hvg_dim", "output_dim")),
                "Checkpoint dimensions disagree")
    candidate_path = SOURCES / "RHAISTER_splits__tahoe__static_2k_genes.json"
    candidate = read_json(candidate_path)
    require(sha(candidate_path) == CANDIDATE_HASH and len(candidate) == len(set(candidate)) == 2000,
            "Candidate list hash/count mismatch")
    require(candidate_path.read_bytes() == (SOURCES / "REUSED_STATIC_2K.json").read_bytes(),
            "Dataset and model candidate lists differ")
    endpoint = read_json(SOURCES / "REUSED_ENDPOINT.json")
    endpoint_matches = [candidate[i] == gene for i, gene in zip(endpoint["coordinates"], endpoint["symbols"])]
    require(len(endpoint_matches) == 39 and all(endpoint_matches), "Endpoint declarations disagree")
    raw_indices = {gene: index for index, gene in enumerate(genes)}
    candidate_indices = [raw_indices[gene] for gene in candidate]
    require(all(a < b for a, b in zip(candidate_indices, candidate_indices[1:])),
            "Candidate is not in full-gene order")
    partial = []
    for row in read_json(SOURCES / "REUSED_PRIOR_AXIS_RESULTS.json")["files"]:
        passed = [item for item in row["endpoint_records"] if item["passed"]]
        require(all(candidate[item["coordinate"]] == item["source_symbol"] for item in passed),
                "Prior authenticated coordinates disagree with candidate")
        partial.append({"file": row["file"], "previously_authenticated_endpoint_coordinates": len(passed),
                        "candidate_agrees_with_all_previously_authenticated_coordinates": True,
                        "does_not_authenticate_previously_unresolved_coordinates": True})
    prep = (SOURCES / "RHAISTER_scripts__data_prep__compute_celleval_deltas.py").read_text()
    require('X = np.log1p(adata.obsm[hvg_key])' in prep, "Rhaister scale evidence changed")
    require('linear (normalized) scale' in (SOURCES / "REUSED_RHAISTER_DATASET_README.md").read_text(),
            "Dataset scale statement changed")
    return {
        "schema": "public_axis_authority_audit_v1",
        "status": "CANDIDATE_FOUND_RELEASE_LINEAGE_UNPROVEN",
        "dataset": {"repo": dataset_info["id"], "revision": DATASET_REV,
                    "inspected_release_tree_entries": len(read_json(SOURCES / "DATASET_TREE.json")),
                    "authoritative_ordered_2000_map_for_exact_release_found": False},
        "checkpoint": {"repo": model_info["id"], "revision": CHECKPOINT_REV,
                       "inspected_release_tree_entries": len(read_json(SOURCES / "MODEL_TREE.json")),
                       "input_dim": 2000, "output_dim": 2000, "hvg_dim": 2000,
                       "var_dims_gene_dim": int(dims["gene_dim"]), "hparams_gene_dim": hparams["gene_dim"],
                       "ordered_gene_names_count": len(genes), "unique_gene_names": len(set(genes)),
                       "var_dims_and_hparams_gene_names_identical": True,
                       "data_module_embed_key": data_module["embed_key"],
                       "data_module_contains_ordered_gene_list": "gene_names" in data_module,
                       "authoritative_decoder_axis_for_exact_checkpoint_found": False},
        "candidate": {"dataset_repo": "tahoebio/tahoe-de-rhaister",
                      "dataset_revision": "c7963cf334bec0683225d41c9586d900ca6303a2",
                      "dataset_path": "definition/static_2k_genes.json",
                      "model_repo": "tahoebio/Rhaister",
                      "model_revision": read_json(SOURCES / "RHAISTER_MODEL_INFO.json")["sha"],
                      "model_path": "splits/tahoe/static_2k_genes.json",
                      "sha256": CANDIDATE_HASH, "count": 2000, "unique_count": 2000,
                      "identical_bytes_across_public_dataset_and_model": True,
                      "legacy_endpoint_coordinate_matches": sum(endpoint_matches),
                      "strictly_increasing_subset_of_checkpoint_full_gene_names": True,
                      "first_20_full_gene_indices": candidate_indices[:20],
                      "supports_calibration_candidate_names_only": True,
                      "certifies_dataset_X_hvg_axis": False, "certifies_checkpoint_decoder_axis": False},
        "prior_file_local_evidence": partial,
        "producer_evidence": {
            "state_source_revision": read_json(SOURCES / "STATE_TREE.json")["sha"],
            "cell_load_source_revision": read_json(SOURCES / "CELL_LOAD_TREE.json")["sha"],
            "Rhaister_input": "Private-path plate*_full_filtered.h5ad.gz, not pinned STATE c*.h5ad",
            "Rhaister_input_gene_name_column": "gene_symbol, unlike inspected STATE var/gene_name",
            "Rhaister_published_HVG_recipe": "log1p(obsm[X_hvg])",
            "Rhaister_dataset_README_scale": "linear (normalized)",
            "summary_statistics_scale_certified": False,
            "release_or_checkpoint_generation_manifest_linking_candidate_found": False},
        "network": {"request_count": len(receipts["records"]), "successful_body_bytes": received,
                    "known_all_received_body_bytes": received, "successful_body_cap_bytes": 5_000_000,
                    "all_retained_HTTP_statuses": sorted({row["http_status"] for row in receipts["records"]}),
                    "failures": 0, "expression_data_requested": False, "maintainer_messages_sent": False},
        "next_allowed_step": "Freeze file-local informative calibration separately; authenticate each required endpoint coordinate. Checkpoint decoder axis remains a separate claim.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    computed = audit()
    audit_path = HERE / "AUDIT.json"
    if not args.verify:
        audit_path.write_text(json.dumps(computed, indent=2) + "\n", encoding="utf-8")
    else:
        require(read_json(audit_path) == computed, "Stored audit is not independently reproduced")
        for row in read_json(HERE / "CLOSURE.json")["files"]:
            path = HERE / row["path"]
            require(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                    f"Portable closure mismatch: {row['path']}")
        try:
            MetadataUnpickler(io.BytesIO(b"cos\nsystem\n.")).load()
        except pickle.UnpicklingError:
            pass
        else:
            raise ValueError("Restricted metadata parser accepted an arbitrary global")
        receipt = {"schema": "public_axis_authority_offline_verification_v1", "status": "PASS",
                   "network_calls": 0, "new_expression_reads": 0, "audit_sha256": sha(audit_path),
                   "conclusion": computed["status"], "public_source_records_verified": len(read_json(HERE / "RECEIPTS.json")["records"]),
                   "candidate_map_is_not_release_or_checkpoint_certification": True}
        (HERE / "VERIFICATION.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "conclusion": computed["status"],
                      "endpoint_matches": computed["candidate"]["legacy_endpoint_coordinate_matches"]}))


if __name__ == "__main__":
    main()
