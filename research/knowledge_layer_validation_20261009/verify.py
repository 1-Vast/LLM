"""Independent raw entity/edge reconstruction and cached retrieval arithmetic."""
import ast
import collections
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolDescriptors

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT/"data/external/mapkg_20261009"
OUT = ROOT/"outputs/knowledge_layer_validation_20261009"
RELEASE = ROOT/"outputs/paper_01286/released_test"
PACKET = ROOT/"research/astra/boundary_acquisition_20261007/packet2"
PREDICATES = {"functions as an inhibitor on the protein target": "inhibit",
              "functions as an activator on the protein target": "activate",
              "functions as an agonist on the protein target": "agonist",
              "functions as an antagonist on the protein target": "antagonist",
              "binds to the protein target": "bind"}
OPPOSITE = dict(inhibit="activate", activate="inhibit", agonist="antagonist", antagonist="agonist")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(smiles):
    mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    return Chem.MolToSmiles(mol, isomericSmiles=True) if mol is not None else None


def mode(relation):
    return PREDICATES.get(relation.strip().casefold(), "unknown")


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, [(i, row) for i, row in enumerate(reader, 2)]


def verify_content(audit):
    labels = json.loads((PACKET/"PACKET_MANIFEST.json").read_text())["labels"]
    metadata = pd.read_parquet(RAW/"drug_metadata.parquet").to_dict("records")
    names = collections.defaultdict(list)
    for row in metadata:
        names[row["drug"].strip().casefold()].append(row)
    drug_fields, drug_rows = csv_rows(RAW/"DRUG_merged_drugs_with_residuals.csv")
    by_cid, by_kg_name = collections.defaultdict(list), collections.defaultdict(list)
    for number, row in drug_rows:
        by_cid[row["PubChem ID"]].append((number, row))
        by_kg_name[row["Drug Name"].strip().casefold()].append(row)
    edge_fields, edge_rows = csv_rows(RAW/"DRUG-GENE_filtered_by_existing_drugs_and_genes.csv")
    gene_fields, genes = csv_rows(RAW/"GENE_tahoe_filtered.csv")
    gene_index = collections.defaultdict(list)
    for _, row in genes:
        gene_index[row["Gene stable ID"]].append(row)
    direction_counts, field_counts, relations = collections.Counter(), collections.Counter(), collections.Counter()
    examples, by_drug = {}, collections.defaultdict(list)
    for number, row in edge_rows:
        kind = mode(row["relation"])
        direction_counts[kind] += 1; relations[row["relation"]] += 1
        for key, value in row.items():
            field_counts[key] += bool(value and value.strip())
        examples.setdefault(kind, {**row, "source_row": number})
        by_drug[row["Drug ID"]].append(dict(gene=row["Gene ID"], relation=row["relation"],
                                            direction=kind, source_row=number,
                                            source_asset="DRUG-GENE_filtered_by_existing_drugs_and_genes.csv",
                                            gene_node_matches=gene_index.get(row["Gene ID"], [])))
    assert len(labels) == len(audit["records"]) == 146
    for index, (label, record) in enumerate(zip(labels, audit["records"])):
        components = ast.literal_eval(label); assert len(components) == 1
        name, dose, unit = components[0]
        assert (record["candidate"], record["drug"], record["dose"], record["unit"]) == (index, name, dose, unit)
        hits = names[name.strip().casefold()]
        assert len(hits) == 1
        cid = str(int(hits[0]["pubchem_cid"])) if pd.notna(hits[0]["pubchem_cid"]) else None
        structure = canonical(hits[0]["canonical_smiles"])
        matching = [(number, row) for number, row in by_cid.get(cid, [])
                    if structure is not None and canonical(row["smiles"]) == structure]
        assert record["cid"] == cid and record["smiles"] == structure
        assert record["kg_exact_identity"] == bool(matching)
        assert record["kg_rows"] == [number for number, _ in matching]
        assert record["moa"] == sorted({row["moa"] for _, row in matching if row["moa"].strip()})
        assert record["edges"] == (by_drug.get(cid, []) if matching else [])
    records = audit["records"]
    statistics = dict(menu_candidates=len(records), unique_drugs=len({r["drug"] for r in records}),
                      encodable_candidates=sum(bool(r["smiles"]) for r in records),
                      kg_exact_candidates=sum(r["kg_exact_identity"] for r in records),
                      kg_exact_drugs=len({r["drug"] for r in records if r["kg_exact_identity"]}),
                      drugs_with_relations=len({r["drug"] for r in records if r["edges"]}),
                      component_preserved_drugs=len({r["drug"] for r in records if "." in r["smiles"]}),
                      raw_drug_rows=len(drug_rows), raw_drug_gene_rows=len(edge_rows), raw_gene_rows=len(genes),
                      drug_columns=drug_fields, edge_columns=edge_fields, gene_columns=gene_fields,
                      global_explicit_directions=dict(direction_counts), nonempty_edge_fields=dict(field_counts),
                      top_relation_texts=[list(pair) for pair in relations.most_common(8)], relation_examples=examples,
                      menu_edge_gene_node_missing=len({e["gene"] for r in records for e in r["edges"] if not e["gene_node_matches"]}),
                      sequence_column_present=any("sequence" in c.casefold() for c in gene_fields))
    for key, value in statistics.items():
        assert audit["statistics"][key] == value, key
    old = json.loads((RELEASE/"IDENTITIES.json").read_text())["records"]
    for current, cached in zip(records, old):
        for key in ("drug", "dose", "unit", "cid", "smiles", "kg_exact_identity", "moa"):
            assert current[key] == cached[key], key
        assert sorted({(e["relation"], e["gene"]) for e in current["edges"]}) == sorted(tuple(e) for e in cached["directed_relations"])
    pilot = json.loads((ROOT/"research/astra/map_knowledge_pilot_20261008/QUALIFIED_KNOWLEDGE.json").read_text())
    old_name_rows = {r["drug"]:r for r in pilot["records"]}
    qualified_names = []
    for name in {r["drug"].strip().casefold() for r in records}:
        hits = by_kg_name[name]
        if len(hits) == 1 and canonical(hits[0]["smiles"]) is not None:
            qualified_names.append(name)
            old_row = old_name_rows[name]
            assert old_row["pubchem"] == hits[0]["PubChem ID"]
            assert canonical(old_row["smiles"]) == canonical(hits[0]["smiles"])
    assert set(qualified_names) == set(old_name_rows) and len(qualified_names) == 48
    assert sum(r["drug"].strip().casefold() in old_name_rows for r in records) == pilot["matched_rows"] == 65
    return dict(old_release_entity_differences=0, old_release_relation_set_differences=0,
                old_exact_name_drugs=48, old_exact_name_menu_rows=65,
                raw_gene_ESM_is_exact_gene_name=sum(row["ESM"] == row["Gene name"] for _, row in genes),
                raw_gene_ESM_nonempty=sum(bool(row["ESM"].strip()) for _, row in genes),
                raw_gene_unique_IDs=len(gene_index), raw_gene_duplicate_IDs=sum(len(v) > 1 for v in gene_index.values()))


def verify_retrieval(records, features, retrieval):
    identities = sorted({(r["smiles"], r["cid"]) for r in records})
    assert len(identities) == retrieval["gallery_structures"] == 111
    gallery, first = [], []
    for identity in identities:
        rows = [i for i, r in enumerate(records) if (r["smiles"], r["cid"]) == identity]
        for name in ("molecule256", "knowledge1024"):
            assert np.isfinite(features[name][rows]).all()
            np.testing.assert_allclose(features[name][rows], np.broadcast_to(features[name][rows[0]], features[name][rows].shape), atol=1e-5, rtol=0)
        edges = {e["source_row"]:e for i in rows if records[i]["kg_exact_identity"] for e in records[i]["edges"]}
        gallery.append(dict(smiles=identity[0], cid=identity[1], drugs=sorted({records[i]["drug"] for i in rows}),
                            genes={e["gene"] for e in edges.values()},
                            typed={(e["direction"], e["gene"]) for e in edges.values() if e["direction"] != "unknown"},
                            edges=list(edges.values())))
        first.append(rows[0])
    matrix = {name:np.array(features[name][first], float) for name in ("molecule256", "knowledge1024")}
    # Use the legacy Morgan bit-vector API independently of the worker generator.
    matrix["morgan2048"] = np.array([np.array(rdMolDescriptors.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(g["smiles"]), 2, nBits=2048)) for g in gallery], float)
    permutation = np.random.default_rng(20261009).permutation(111)
    assert permutation.tolist() == retrieval["permutation"]
    matrix["knowledge_permuted"] = matrix["knowledge1024"][permutation]
    rebuilt = []
    for index, query in enumerate(gallery):
        if not query["genes"]:
            continue
        for arm, vectors in matrix.items():
            normalized = vectors/np.linalg.norm(vectors, axis=1)[:, None]
            # Compute each dot product directly, separate from matrix multiply.
            scores = np.array([float(np.dot(normalized[index], v)) for v in normalized])
            neighbors = sorted((i for i in range(111) if i != index), key=lambda i:(-scores[i], i))[:5]
            genes = {gene for i in neighbors for gene in gallery[i]["genes"]}
            typed = {label for i in neighbors for label in gallery[i]["typed"]}
            same = len(query["typed"] & typed)
            opposing = sum((OPPOSITE[direction], gene) in typed for direction, gene in query["typed"] if direction in OPPOSITE)
            row = dict(query=index, drug=query["drugs"], cid=query["cid"], arm=arm,
                       known_gene_labels=len(query["genes"]), known_typed_labels=len(query["typed"]),
                       gene_known_hit_at5=bool(query["genes"] & genes),
                       gene_known_recall_at5=len(query["genes"] & genes)/len(query["genes"]),
                       typed_known_hit_at5=bool(same) if query["typed"] else None,
                       typed_known_recall_at5=same/len(query["typed"]) if query["typed"] else None,
                       same_mode_gene_annotations=same, opposing_mode_gene_annotations=int(opposing),
                       unlabeled_neighbors=sum(not gallery[i]["genes"] for i in neighbors),
                       unknown_mode_annotations=sum(e["direction"] == "unknown" for i in neighbors for e in gallery[i]["edges"]),
                       neighbors=[dict(index=i, drugs=gallery[i]["drugs"], cid=gallery[i]["cid"], smiles=gallery[i]["smiles"],
                                       cosine=float(scores[i]), known_gene_labels=len(gallery[i]["genes"]),
                                       annotation_source_rows=sorted({str(e["source_row"]) for e in gallery[i]["edges"]})) for i in neighbors])
            rebuilt.append(row)
    assert len(rebuilt) == len(retrieval["results"]) == 176
    for expected, actual in zip(rebuilt, retrieval["results"]):
        for key in expected:
            if key == "neighbors":
                for neighbor, saved in zip(expected[key], actual[key]):
                    for field in neighbor:
                        if field == "cosine":
                            np.testing.assert_allclose(neighbor[field], saved[field], atol=1e-12, rtol=1e-11)
                        else:
                            assert neighbor[field] == saved[field], (actual["arm"], actual["query"], field)
            else:
                assert actual[key] == expected[key], (actual["arm"], actual["query"], key)
    for arm in matrix:
        rows = [r for r in rebuilt if r["arm"] == arm]
        for metric in ("gene_known_hit_at5", "gene_known_recall_at5", "typed_known_hit_at5", "typed_known_recall_at5"):
            values = [r[metric] for r in rows if r[metric] is not None]
            assert retrieval["summary"][arm][metric] == float(np.mean(values))
        assert retrieval["summary"][arm]["gene_queries"] == 44
        assert retrieval["summary"][arm]["typed_queries"] == 30
        for metric in ("same_mode_gene_annotations", "opposing_mode_gene_annotations"):
            assert retrieval["summary"][arm][metric] == sum(r[metric] for r in rows)
    # Source-only annotation ceiling keeps the registered query denominators.
    ceilings = []
    for index, query in enumerate(gallery):
        if not query["genes"]:
            continue
        other_genes = {g for i, item in enumerate(gallery) if i != index for g in item["genes"]}
        other_typed = {g for i, item in enumerate(gallery) if i != index for g in item["typed"]}
        ceilings.append(dict(query=index, drugs=query["drugs"], cid=query["cid"],
                             alternative_known_gene_hit_possible=bool(query["genes"] & other_genes),
                             alternative_known_gene_recall_ceiling=len(query["genes"] & other_genes)/len(query["genes"]),
                             alternative_typed_hit_possible=bool(query["typed"] & other_typed) if query["typed"] else None,
                             alternative_typed_recall_ceiling=len(query["typed"] & other_typed)/len(query["typed"]) if query["typed"] else None))
    typed_rows = [r for r in ceilings if r["alternative_typed_hit_possible"] is not None]
    return dict(post_hoc=True, no_denominator_or_model_selection=True, query_count=len(ceilings), typed_query_count=len(typed_rows),
                gene_queries_with_any_alternative=sum(r["alternative_known_gene_hit_possible"] for r in ceilings),
                gene_queries_without_any_alternative=sum(not r["alternative_known_gene_hit_possible"] for r in ceilings),
                typed_queries_with_any_alternative=sum(r["alternative_typed_hit_possible"] for r in typed_rows),
                typed_queries_without_any_alternative=sum(not r["alternative_typed_hit_possible"] for r in typed_rows),
                mean_all_gallery_gene_recall_ceiling=float(np.mean([r["alternative_known_gene_recall_ceiling"] for r in ceilings])),
                mean_all_gallery_typed_recall_ceiling=float(np.mean([r["alternative_typed_recall_ceiling"] for r in typed_rows])),
                rows=ceilings, limits="Allremaininggalleryannotationceiling,notanattainabletop5policy;unknownparsermodeisunparsedpredicate,notbiologicalnegative")


def previous_controls():
    pilot = ROOT/"research/astra/map_knowledge_pilot_20261008"
    checks = []
    for folder, predictions_name, results_name, choices_name, baseline, skip in (
            (pilot, "PREDICTIONS.npz", "RESULTS.json", "MODEL_CHOICES.json", "M2", {"M0"}),
            (pilot, "CONTRASTIVE_PREDICTIONS.npz", "CONTRASTIVE_RESULTS.json", "CONTRASTIVE_CHOICES.json", "structure24", set()),
            (RELEASE, "PREDICTIONS.npz", "RESULTS.json", "MODEL_CHOICES.json", "M2", set())):
        predictions = dict(np.load(folder/predictions_name))
        rows = json.loads((folder/results_name).read_text())
        choices = json.loads((folder/choices_name).read_text())
        for arm, choice in choices.items():
            if arm not in skip:
                assert choice["alpha"] == 0
        for row in rows:
            if row["arm"] in skip:
                continue
            original = next(r for r in rows if r["context"] == row["context"] and r["arm"] == baseline)
            assert {k:v for k,v in row.items() if k != "arm"} == {k:v for k,v in original.items() if k != "arm"}
            np.testing.assert_array_equal(predictions[row["context"]+"__"+row["arm"]], predictions[row["context"]+"__"+baseline])
        checks.append(dict(results=results_name, records=len(rows), enabled_correction_heads=0, all_control_predictions_and_decisions_equal=True))
    return checks


def main():
    started = time.perf_counter()
    RDLogger.DisableLog("rdApp.warning"); RDLogger.DisableLog("rdApp.error")
    vf = json.loads((HERE/"VERIFY_FREEZE.json").read_text())
    assert sha(Path(__file__)) == vf["verifier_sha256"] and sha(HERE/"FREEZE.json") == vf["trial_freeze_sha256"]
    freeze = json.loads((HERE/"FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        assert sha(ROOT/name) == expected, name
    audit = json.loads((OUT/"AUDIT.json").read_text())
    retrieval = json.loads((OUT/"RETRIEVAL.json").read_text())
    features = dict(np.load(RELEASE/"FEATURES.npz"))
    for acquisition in audit["acquisitions"]:
        path = ROOT/acquisition["path"]
        assert path.stat().st_size == acquisition["bytes"] and sha(path) == acquisition["sha256"]
        if acquisition["publisher_lfs_sha256"] is not None:
            assert acquisition["publisher_lfs_sha256"] == acquisition["sha256"]
        assert "2a9af1bd2645fef86fab495b85a1b08a52356e26" in acquisition["url"] or "2dc57900b7981cfcf5e211527169a0b006546a95" in acquisition["url"]
    checks = ["All8registeredinputs andfourpinnedrestoredassetbytes/hashes intact;verifierseparatelyfrozen"]
    entity_receipt = verify_content(audit)
    checks.append("All146officialname/CID/fullcanonicalstereochemical/componentidentities and rawtypedsourceedges/gene-nodejoins independentlyrebuilt")
    checks.append("Original48name-onlydrugs/65rows and released79strictidentitydrugs/44relationdrugs reproduced withoutentity/relationsetdifferences")
    ceiling = verify_retrieval(audit["records"], features, retrieval)
    checks.append("All111galleryidentities,dosevectorbindings,176fourarmqueries,880neighbors/cosines/source-rowlistsandallmetrics independentlyreconstructed")
    controls = previous_controls()
    checks.append("Allsavedpriorprojection/contrastive/releasednegativecontrolcorrections disabledandforecasts/decisions/outcomesidentical")
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("frozen_knowledge_audit_verifier", HERE/"audit.py")
    study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    original = study.OUT
    with tempfile.TemporaryDirectory(prefix="knowledge_audit_exact_repeat_") as temporary:
        study.OUT = Path(temporary)/"fresh"
        with contextlib.redirect_stdout(io.StringIO()):
            study.main()
        repeat_audit = json.loads((study.OUT/"AUDIT.json").read_text())
        original_audit = json.loads((original/"AUDIT.json").read_text())
        for records in (repeat_audit["acquisitions"], original_audit["acquisitions"]):
            for record in records:
                record.pop("downloaded_this_run")
        assert repeat_audit == original_audit
        for name in ("RETRIEVAL.json", "SUMMARY.json"):
            repeated = json.loads((study.OUT/name).read_text()); saved = json.loads((original/name).read_text())
            repeated.pop("seconds"); saved.pop("seconds")
            assert repeated == saved, name
    study.OUT = original
    checks.append("Freshcompletecontentauditandbenchmark exactlyreproduce scientificresults;elapsed/downloadexecutionflags excluded")
    with (OUT/"ANNOTATION_CEILING_DIAGNOSTIC.json").open("x", encoding="utf-8") as stream:
        json.dump(ceiling, stream, indent=2, allow_nan=False); stream.write("\n")
    receipt = dict(status="PASS", checks=checks, check_groups=len(checks), entities=entity_receipt,
                   prior_control_checks=controls, retrieval_summary=retrieval["summary"],
                   verifier_sha256=sha(Path(__file__)), seconds=time.perf_counter()-started,
                   limits="Knownannotationsandpossiblepretrainingexposureonly;unlabeledunknown,notnegative;ESMkeysarenotsequencesorproteinprojectedvectors;noresponse/decision/risk/functionalorLLMbenefitclaim")
    with (OUT/"VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()
