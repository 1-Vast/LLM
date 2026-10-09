"""Cached representation content retrieval; known annotations are not negatives."""
import time

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

ARMS = ("molecule256", "knowledge1024", "morgan2048", "knowledge_permuted")
OPPOSING_MODES = {"inhibit": "activate", "activate": "inhibit", "agonist": "antagonist", "antagonist": "agonist"}


def labels(record):
    edges = record.get("edges", []) if record["kg_exact_identity"] else []
    genes = {edge["gene"] for edge in edges}
    typed = {(edge["direction"], edge["gene"]) for edge in edges if edge["direction"] != "unknown"}
    return genes, typed


def benchmark(records, features):
    started = time.perf_counter()
    for key in ("molecule256", "knowledge1024"):
        if len(features[key]) != len(records) or not np.isfinite(features[key]).all():
            raise ValueError("nonfinite_or_unaligned_features")
    grouped = {}
    for index, record in enumerate(records):
        molecule = Chem.MolFromSmiles(record["smiles"])
        if molecule is None or Chem.MolToSmiles(molecule, isomericSmiles=True) != record["smiles"]:
            raise ValueError("noncanonical_fullfragment_stereochemical_identity")
        grouped.setdefault((record["smiles"], record["cid"]), []).append(index)
    identities = sorted(grouped)
    gallery, indices = [], []
    for identity in identities:
        rows = grouped[identity]
        for key in ("molecule256", "knowledge1024"):
            if not np.allclose(features[key][rows], features[key][rows[0]], atol=1e-5, rtol=0):
                raise ValueError("same_identity_dose_features_differ")
        genes, typed = set(), set()
        for row in rows:
            g, t = labels(records[row]); genes.update(g); typed.update(t)
        edges = list({(edge["gene"], edge["direction"], edge["relation"], str(edge["source_row"])): edge
                      for row in rows if records[row]["kg_exact_identity"]
                      for edge in records[row].get("edges", [])}.values())
        gallery.append(dict(smiles=identity[0], cid=identity[1], drugs=sorted({records[row]["drug"] for row in rows}),
                            menu_rows=rows, genes=genes, typed=typed, edges=edges))
        indices.append(rows[0])
    matrix = {key: np.asarray(features[key][indices], dtype=float) for key in ("molecule256", "knowledge1024")}
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fingerprints = []
    for item in gallery:
        bits = np.zeros(2048)
        DataStructs.ConvertToNumpyArray(generator.GetFingerprint(Chem.MolFromSmiles(item["smiles"])), bits)
        fingerprints.append(bits)
    matrix["morgan2048"] = np.array(fingerprints)
    permutation = np.random.default_rng(20261009).permutation(len(gallery))
    matrix["knowledge_permuted"] = matrix["knowledge1024"][permutation]
    similarities = {}
    for arm, values in matrix.items():
        normalized = np.divide(values, np.linalg.norm(values, axis=1)[:, None],
                               out=np.zeros_like(values), where=np.linalg.norm(values, axis=1)[:, None] > 0)
        similarities[arm] = normalized @ normalized.T
    results = []
    for query_index, query in enumerate(gallery):
        if not query["genes"]:
            continue
        for arm in ARMS:
            scores = similarities[arm][query_index].copy()
            scores[query_index] = -np.inf
            neighbors = np.lexsort((np.arange(len(gallery)), -scores))[:5].tolist()
            neighbors = [i for i in neighbors if i != query_index]
            genes = set().union(*(gallery[i]["genes"] for i in neighbors))
            typed = set().union(*(gallery[i]["typed"] for i in neighbors))
            same = len(query["typed"] & typed)
            opposite = sum((OPPOSING_MODES[direction], gene) in typed
                           for direction, gene in query["typed"] if direction in OPPOSING_MODES)
            results.append(dict(query=query_index, drug=query["drugs"], cid=query["cid"], arm=arm,
                known_gene_labels=len(query["genes"]), known_typed_labels=len(query["typed"]),
                gene_known_hit_at5=bool(query["genes"] & genes), gene_known_recall_at5=len(query["genes"] & genes)/len(query["genes"]),
                typed_known_hit_at5=bool(same) if query["typed"] else None,
                typed_known_recall_at5=same/len(query["typed"]) if query["typed"] else None,
                same_mode_gene_annotations=same, opposing_mode_gene_annotations=int(opposite),
                unlabeled_neighbors=sum(not gallery[i]["genes"] for i in neighbors),
                unknown_mode_annotations=sum(edge["direction"] == "unknown" for i in neighbors for edge in gallery[i]["edges"]),
                neighbors=[dict(index=i, drugs=gallery[i]["drugs"], cid=gallery[i]["cid"], smiles=gallery[i]["smiles"],
                                cosine=float(scores[i]), known_gene_labels=len(gallery[i]["genes"]),
                                annotation_source_rows=sorted({str(edge["source_row"]) for edge in gallery[i]["edges"]})) for i in neighbors]))
    summary = {}
    for arm in ARMS:
        rows = [row for row in results if row["arm"] == arm]
        summary[arm] = {metric: float(np.mean([row[metric] for row in rows if row[metric] is not None]))
                       if any(row[metric] is not None for row in rows) else None
                       for metric in ("gene_known_hit_at5", "gene_known_recall_at5", "typed_known_hit_at5", "typed_known_recall_at5")}
        summary[arm].update(gene_queries=len(rows), typed_queries=sum(row["known_typed_labels"] > 0 for row in rows),
                            same_mode_gene_annotations=sum(row["same_mode_gene_annotations"] for row in rows),
                            opposing_mode_gene_annotations=sum(row["opposing_mode_gene_annotations"] for row in rows))
    return dict(summary=summary, results=results, menu_rows=len(records), gallery_structures=len(gallery),
                permutation=permutation.tolist(), seconds=time.perf_counter()-started,
                scope="Cached known-annotation retrieval only; pretraining exposure possible. Typed modes are source pharmacology annotations, not cell-expression direction. Unlabeled is unknown, not biological negative. No response, causal or decision-risk inference.")
