"""Frozen unconditioned molecule/protein content assay; no RNA or outcome access."""
import hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/"outputs/map_module_replacement_20261009/protein_content"
ARMS=[
 "knowledge1024_to_projected_protein1024_cosine",
 "knowledge1024_to_fixed_symbol_shuffled_protein1024_cosine",
 "knowledge1024_fixed_whole_query_identity_permutation_to_projected_protein1024_cosine",
 "molecule256_nearest_five_other_identities_target_votes",
 "query_excluded_other_identity_target_popularity",
]

def sha(path):
    return hashlib.file_digest(path.open("rb"),"sha256").hexdigest()

def verify_freeze():
    p=HERE/"PROTEIN_FREEZE.json"
    if not p.exists():raise RuntimeError("Scoring requires parent-created PROTEIN_FREEZE.json")
    frozen=json.loads(p.read_text())
    for name,expected in frozen["sha256"].items():
        if sha(ROOT/name)!=expected:raise RuntimeError("Freeze mismatch: "+name)
    protocol=HERE/"PROTEIN_PROTOCOL.json"
    required={str(protocol.relative_to(ROOT)),str(Path(__file__).resolve().relative_to(ROOT)),
              "data/external/map_module_replacement_20261009/PROTEIN_FEATURES.npz",
              "outputs/paper_01286/released_test/FEATURES.npz",
              "outputs/paper_01286/released_test/IDENTITIES.json",
              "outputs/knowledge_layer_validation_20261009/AUDIT.json",
              str((HERE/"GALLERY_QUALIFICATION.json").relative_to(ROOT)),
              str((HERE/"PARTIAL_ASSET_RECEIPTS.json").relative_to(ROOT))}
    if not required.issubset(frozen["sha256"]):raise RuntimeError("Freeze does not bind required inputs")
    return frozen

def normalize(a):
    a=np.asarray(a,dtype=np.float64)
    if not np.isfinite(a).all():raise ValueError("Nonfinite features")
    norms=np.linalg.norm(a,axis=1,keepdims=True)
    if np.any(norms<=0):raise ValueError("Zero feature vector")
    return a/norms

def identities():
    audit=json.loads((ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json").read_text())
    old=json.loads((ROOT/"outputs/paper_01286/released_test/IDENTITIES.json").read_text())["records"]
    f=np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz")
    if len(audit["records"])!=len(old) or len(old)!=len(f["mask"]):raise ValueError("Candidate axes differ")
    grouped={}
    for row in audit["records"]:
        i=row["candidate"]
        source=old[i]
        for key in ["cid","smiles","drug","dose","unit"]:
            if row.get(key)!=source.get(key):raise ValueError("Candidate identity mismatch")
        if bool(f["mask"][i])!=bool(row["smiles"]):raise ValueError("Candidate feature mask mismatch")
        if not row["smiles"]:continue
        key=(str(row["cid"]),row["smiles"])
        if key not in grouped:
            grouped[key]={"cid":row["cid"],"smiles":row["smiles"],"candidate_indices":[],
                          "drug_names":set(),"truth":set(),"edges":[],"molecule256":f["molecule256"][i],
                          "knowledge1024":f["knowledge1024"][i]}
        g=grouped[key]
        np.testing.assert_array_equal(g["molecule256"],f["molecule256"][i])
        np.testing.assert_array_equal(g["knowledge1024"],f["knowledge1024"][i])
        g["candidate_indices"].append(i)
        g["drug_names"].add(row["drug"])
        if row["kg_exact_identity"]:
            g["truth"].update(e["gene"] for e in row["edges"])
            g["edges"].extend(row["edges"])
    order=sorted(grouped)
    records=[grouped[key] for key in order]
    return records,f,audit

def sorted_genes(scores):
    # The gallery already has ascending stable gene ID order.
    return np.argsort(-scores,kind="stable")

def metrics(scores,truth,gene_ids):
    rank=sorted_genes(scores)
    ranked=[str(gene_ids[i]) for i in rank]
    target_ranks=sorted(ranked.index(g)+1 for g in truth if g in set(ranked))
    return {"hit5":int(bool(set(ranked[:5])&truth)),"hit20":int(bool(set(ranked[:20])&truth)),
            "recall5":len(set(ranked[:5])&truth)/len(truth),
            "recall20":len(set(ranked[:20])&truth)/len(truth),
            "mrr":1/target_ranks[0] if target_ranks else 0,
            "known_target_ranks":target_ranks,
            "top20":[{"gene":ranked[j],"score":float(scores[rank[j]]),"is_known_assertion":ranked[j] in truth}
                     for j in range(min(20,len(rank)))]}

def main():
    if OUT.exists():raise RuntimeError("Refuse to overwrite protein-content assay")
    frozen=verify_freeze()
    assets=json.loads((HERE/"PARTIAL_ASSET_RECEIPTS.json").read_text())
    if not assets["molecule_cache_reconstruction_passed"] or not assets["strict_projector_load"]:
        raise RuntimeError("Partial asset compatibility failed")
    qualification=json.loads((HERE/"GALLERY_QUALIFICATION.json").read_text())
    p=np.load(ROOT/"data/external/map_module_replacement_20261009/PROTEIN_FEATURES.npz")
    gene_ids=p["gene_ids"]
    expected=[r["gene_id"] for r in qualification["gallery"]]
    np.testing.assert_array_equal(gene_ids,np.array(expected))
    if list(gene_ids)!=sorted(gene_ids):raise ValueError("Gene tie order is not frozen ascending ID")
    records,feature,audit=identities()
    raw=normalize([r["molecule256"] for r in records])
    kg=normalize([r["knowledge1024"] for r in records])
    protein=normalize(p["protein1024"])
    qindices=[i for i,r in enumerate(records) if r["truth"]]
    protein_permutation=np.random.default_rng(20261010).permutation(len(protein))
    identity_permutation=np.random.default_rng(20261011).permutation(len(records))
    direct=kg[qindices]@protein.T
    shuffled=kg[qindices]@protein[protein_permutation].T
    permuted=kg[identity_permutation[qindices]]@protein.T
    gene_to_index={str(g):i for i,g in enumerate(gene_ids)}
    vote=np.zeros_like(direct)
    popularity=np.zeros_like(direct)
    neighbor_indices=[]
    for qi,source_index in enumerate(qindices):
        query=records[source_index]
        eligible=[i for i,r in enumerate(records)
                  if i!=source_index and r["cid"]!=query["cid"] and r["smiles"]!=query["smiles"]]
        similarities=raw[source_index]@raw[eligible].T
        order=np.argsort(-similarities,kind="stable")
        neighbors=[eligible[int(j)] for j in order[:5]]
        if len(neighbors)!=5:raise RuntimeError("Insufficient structural control neighbors")
        neighbor_indices.append(neighbors)
        for i in neighbors:
            for gene in records[i]["truth"]:
                if gene in gene_to_index:vote[qi,gene_to_index[gene]]+=1/5
        for i in eligible:
            for gene in records[i]["truth"]:
                if gene in gene_to_index:popularity[qi,gene_to_index[gene]]+=1
    all_scores=[direct,shuffled,permuted,vote,popularity]
    results=[]
    gallery_ids=set(map(str,gene_ids))
    for qi,index in enumerate(qindices):
        row=records[index]
        source_edges={(e["gene"],e["relation"],e["source_row"]):e for e in row["edges"]}
        results.append({"identity_index":index,"cid":row["cid"],"smiles":row["smiles"],
                        "candidate_indices":row["candidate_indices"],"drug_names":sorted(row["drug_names"]),
                        "truth_genes_all":sorted(row["truth"]),
                        "truth_genes_in_gallery":sorted(row["truth"]&gallery_ids),
                        "unresolved_truth":sorted(row["truth"]-gallery_ids),
                        "source_assertions":list(source_edges.values()),
                        "molecular_neighbor_identities":[{"identity_index":j,"cid":records[j]["cid"],
                                                          "smiles":records[j]["smiles"],
                                                          "drug_names":sorted(records[j]["drug_names"])}
                                                         for j in neighbor_indices[qi]],
                        "arms":{name:metrics(scores[qi],row["truth"],gene_ids)
                                for name,scores in zip(ARMS,all_scores)}})
    summary={}
    eligible_summary={}
    for arm in ARMS:
        values=[r["arms"][arm] for r in results]
        summary[arm]={"queries":len(values),"hit5_count":sum(v["hit5"] for v in values),
                      "hit20_count":sum(v["hit20"] for v in values),
                      **{name:float(np.mean([v[name] for v in values]))
                         for name in ["hit5","hit20","recall5","recall20","mrr"]}}
        eligible=[r["arms"][arm] for r in results if r["truth_genes_in_gallery"]]
        eligible_summary[arm]={"queries":len(eligible),
                               **{name:float(np.mean([v[name] for v in eligible]))
                                  for name in ["hit5","hit20","recall5","recall20","mrr"]}}
    primary_pass=(summary[ARMS[0]]["hit5_count"]>summary[ARMS[3]]["hit5_count"] and
                  summary[ARMS[0]]["hit5_count"]>summary[ARMS[4]]["hit5_count"])
    receipt={"frozen_input_sha256":frozen["sha256"],"menu_candidates":len(audit["records"]),
             "encodable_candidates":int(feature["mask"].sum()),"unique_molecule_identities":len(records),
             "known_assertion_queries":len(results),"protein_gallery":len(gene_ids),
             "unassessable_biology_queries":sum(not r["truth_genes_in_gallery"] for r in results),
             "query_unresolved_known_target_ids":sorted({g for r in results for g in r["unresolved_truth"]}),
             "partial_asset_scope":assets["provenance_limit"],"gallery_scope":qualification["gallery_scope"],
             "arm_metrics":summary,"descriptive_eligible_truth_query_view":eligible_summary,
             "primary_content_advantage_passed":primary_pass,
             "conclusion":"Observed descriptive content advantage under the fixed assay" if primary_pass else "No content advantage over both structural-vote and popularity controls",
             "claim_boundary":"Target-enriched known-assertion content assay with potentially pretrained graph exposure; no authenticated held-out-edge or biological target validation, RNA prediction, functional outcome, causal effect or decision benefit."}
    OUT.mkdir(parents=True)
    (OUT/"RESULTS.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    (OUT/"SUMMARY.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    np.savez_compressed(OUT/"SCORES.npz",gene_ids=gene_ids,query_identity_indices=np.array(qindices),
                        protein_permutation=protein_permutation,identity_permutation=identity_permutation,
                        **{f"arm_{i}":scores for i,scores in enumerate(all_scores)})
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":main()

