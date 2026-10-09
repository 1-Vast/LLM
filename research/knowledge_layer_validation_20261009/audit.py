"""Pinned MAP-KG content audit and cached representation retrieval; no RNA fitting."""
import ast
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from rdkit import Chem, RDLogger

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / "data/external/mapkg_20261009"
OUT = ROOT / "outputs/knowledge_layer_validation_20261009"
RELEASE = ROOT / "outputs/paper_01286/released_test"
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
REVISION = "2a9af1bd2645fef86fab495b85a1b08a52356e26"
FILES = {
    "DRUG_merged_drugs_with_residuals.csv": (30886178, "19b9fd94475ad9d3f47f8c73c9ce10a2f04d29e16b0e2df35c2cb29e49f63e3f"),
    "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv": (36169383, "3b4edcab5c98c441cadcb7a3e4c61cbc3048c065223c555694f9c9313c225aa4"),
    # This non-LFS source has a pinned Git revision; its local digest is recorded.
    "GENE_tahoe_filtered.csv": (688979, None),
    "drug_metadata.parquet": (40475, "7a04c7a6611e74c92253163b994ff0a47191928ee7511f1c2ca508cee0e79f28"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    records = []
    for name, (size, expected) in FILES.items():
        url = (f"https://huggingface.co/datasets/RainGate/MAP-KG/resolve/{REVISION}/{name}"
               if name != "drug_metadata.parquet" else
               "https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/2dc57900b7981cfcf5e211527169a0b006546a95/metadata/drug_metadata.parquet")
        path = RAW / name
        restored = not path.exists()
        if restored:
            response = requests.get(url, timeout=(20, 120), stream=True)
            response.raise_for_status()
            with path.with_suffix(path.suffix+".partial").open("xb") as stream:
                for chunk in response.iter_content(1024*1024):
                    stream.write(chunk)
            path.with_suffix(path.suffix+".partial").rename(path)
        digest = sha(path)
        if path.stat().st_size != size or expected is not None and digest != expected:
            raise ValueError("official_asset_mismatch:"+name)
        records.append({"path": path.relative_to(ROOT).as_posix(), "url": url,
            "bytes": size, "sha256": digest, "downloaded_this_run": restored,
            "publisher_lfs_sha256": expected})
        print(f"Qualified {name}: {size} bytes", flush=True)
    return records


def canonical(smiles):
    mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    return Chem.MolToSmiles(mol, isomericSmiles=True) if mol is not None else None


def direction(relation):
    # Only a controlled explicit predicate is typed. Assay prose stays unknown;
    # IC50, binding and inhibition are never equated by substring heuristics.
    text = relation.strip().casefold()
    predicates = {
        "functions as an inhibitor on the protein target": "inhibit",
        "functions as an activator on the protein target": "activate",
        "functions as an agonist on the protein target": "agonist",
        "functions as an antagonist on the protein target": "antagonist",
        "binds to the protein target": "bind",
    }
    return predicates.get(text, "unknown")


def content():
    RDLogger.DisableLog("rdApp.error")
    labels = json.loads((PACKET / "PACKET_MANIFEST.json").read_text())["labels"]
    metadata = pd.read_parquet(RAW / "drug_metadata.parquet")
    by_name = {}
    for r in metadata.to_dict("records"):
        by_name.setdefault(r["drug"].strip().casefold(), []).append(r)
    menu_cids = {str(int(r["pubchem_cid"])) for r in metadata.to_dict("records") if pd.notna(r["pubchem_cid"])}
    kg = {}
    with (RAW / "DRUG_merged_drugs_with_residuals.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        drug_columns = reader.fieldnames
        total_drugs = 0
        for row_number, r in enumerate(reader, start=2):
            total_drugs += 1
            if r["PubChem ID"] in menu_cids:
                kg.setdefault(r["PubChem ID"], []).append({**r, "source_row": row_number})
    records = []
    for candidate, label in enumerate(labels):
        components = ast.literal_eval(label)
        if len(components) != 1:
            raise ValueError("composite_menu_requires_explicit_component_mapping")
        name, dose, unit = components[0]
        hits = by_name.get(name.strip().casefold(), [])
        record = {"candidate": candidate, "drug": name, "dose": dose, "unit": unit,
                  "cid": None, "smiles": None, "kg_exact_identity": False, "edges": [], "moa": []}
        if len(hits) == 1:
            h = hits[0]
            record["smiles"] = canonical(h["canonical_smiles"])
            record["cid"] = str(int(h["pubchem_cid"])) if pd.notna(h["pubchem_cid"]) else None
            exact = [r for r in kg.get(record["cid"], []) if canonical(r["smiles"]) == record["smiles"] and record["smiles"]]
            record["kg_exact_identity"] = bool(exact)
            record["kg_rows"] = [r["source_row"] for r in exact]
            record["moa"] = sorted({r["moa"] for r in exact if r["moa"].strip()})
        records.append(record)
    qualified = {r["cid"] for r in records if r["kg_exact_identity"]}
    edges = {cid: [] for cid in qualified}
    edge_fields, nonempty_fields, relations = Counter(), Counter(), Counter()
    examples = {}
    with (RAW / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        edge_columns = reader.fieldnames
        total_edges = 0
        for row_number, r in enumerate(reader, start=2):
            total_edges += 1
            relation = r["relation"]
            kind = direction(relation)
            edge_fields[kind] += 1
            relations[relation] += 1
            for key, value in r.items():
                nonempty_fields[key] += bool(value and value.strip())
            if kind not in examples:
                examples[kind] = {**r, "source_row": row_number}
            if r["Drug ID"] in qualified:
                edges[r["Drug ID"]].append({"gene": r["Gene ID"], "relation": relation, "direction": kind,
                    "source_row": row_number, "source_asset": "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"})
    for r in records:
        r["edges"] = edges.get(r["cid"], []) if r["kg_exact_identity"] else []
    with (RAW / "GENE_tahoe_filtered.csv").open(encoding="utf-8-sig", newline="") as stream:
        genes_reader = csv.DictReader(stream)
        gene_columns = genes_reader.fieldnames
        genes = list(genes_reader)
    gene_index = {}
    for gene in genes:
        gene_index.setdefault(gene["Gene stable ID"], []).append(gene)
    for r in records:
        for edge in r["edges"]:
            edge["gene_node_matches"] = gene_index.get(edge["gene"], [])
    stats = {"menu_candidates": len(records), "unique_drugs": len({r["drug"] for r in records}),
        "encodable_candidates": sum(bool(r["smiles"]) for r in records),
        "kg_exact_candidates": sum(r["kg_exact_identity"] for r in records),
        "kg_exact_drugs": len({r["drug"] for r in records if r["kg_exact_identity"]}),
        "drugs_with_relations": len({r["drug"] for r in records if r["edges"]}),
        "component_preserved_drugs": len({r["drug"] for r in records if r["smiles"] and "." in r["smiles"]}),
        "raw_drug_rows": total_drugs, "raw_drug_gene_rows": total_edges, "raw_gene_rows": len(genes),
        "drug_columns": drug_columns, "edge_columns": edge_columns, "gene_columns": gene_columns,
        "global_explicit_directions": dict(edge_fields), "nonempty_edge_fields": dict(nonempty_fields),
        "top_relation_texts": relations.most_common(8), "relation_examples": examples,
        "menu_edge_gene_node_missing": len({edge["gene"] for r in records for edge in r["edges"]
                                            if not edge["gene_node_matches"]}),
        "sequence_column_present": any("sequence" in column.casefold() for column in gene_columns),
        "scope": "KG assertions and source-row lineage, not target-cell observations or calibrated effects. Unknown edge is not biological negative."}
    return records, stats


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("frozen_source_changed:"+name)
    if OUT.exists():
        raise RuntimeError("Refuse to overwrite frozen content/retrieval audit")
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    acquisitions = acquire()
    records, stats = content()
    cached = json.loads((RELEASE / "IDENTITIES.json").read_text())["records"]
    if [(r["smiles"], r["cid"]) for r in records] != [(r["smiles"], r["cid"]) for r in cached]:
        raise ValueError("restored_identity_does_not_bind_cached_vectors")
    audit = {"acquisitions": acquisitions, "statistics": stats, "records": records}
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    from benchmark import benchmark
    features = dict(np.load(RELEASE / "FEATURES.npz"))
    retrieval = benchmark(records, features)
    (OUT / "RETRIEVAL.json").write_text(json.dumps(retrieval, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    status = {"knowledge_index": "SOURCE_TYPED_CONTENT_AUDITED",
        "molecule_knowledge_cache": "Content-retrieval comparison executed; graph-pretraining exposure unknown",
        "joint_molecule_protein_space": "BLOCKED: protein projected vectors and matching encoder assets absent",
        "response_or_decision_gain": "Not evaluated in this content audit; earlier controlled response corrections did not improve final choices",
        "seconds": time.perf_counter()-started, "retrieval_summary": retrieval["summary"], "coverage": stats}
    (OUT / "SUMMARY.json").write_text(json.dumps(status, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(status, indent=2), flush=True)


if __name__ == "__main__":
    main()
