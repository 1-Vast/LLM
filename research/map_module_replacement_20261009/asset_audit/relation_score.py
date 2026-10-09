"""Prespecified original relation-composition content scoring; requires parent freeze."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from relation_encoder import GENERIC,official_classes,tensor

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/"outputs/map_module_replacement_20261009/relation_content"
ASSETS=ROOT/"data/external/map_module_replacement_20261009"
ARMS=["outgoing_molecule_relation_to_projected_protein_cosine",
      "incoming_molecule_to_relation_projected_protein_cosine",
      "outgoing_canonical_name_relation_to_canonical_gene_name_cosine",
      "incoming_canonical_drug_name_to_relation_canonical_gene_name_cosine",
      "relation_only_to_projected_protein_cosine",
      "outgoing_molecule_with_fixed_relation_identity_permutation",
      "outgoing_molecule_relation_with_fixed_protein_identity_permutation",
      "molecule256_nearest_five_other_identity_exactrelation_target_votes",
      "query_excluded_other_identity_exactrelation_target_popularity"]
def sha(p):return hashlib.file_digest(p.open("rb"),"sha256").hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def unit(x):
    x=np.asarray(x,dtype=np.float64)
    d=np.linalg.norm(x,axis=1,keepdims=True)
    if not np.isfinite(x).all() or np.any(d==0):raise RuntimeError("Invalid feature norm")
    return x/d
def report(scores,truth,genes):
    order=np.argsort(-scores,kind="stable")
    ranked=[genes[j] for j in order]
    pos={g:i+1 for i,g in enumerate(ranked)}
    known=sorted(pos[g] for g in truth if g in pos)
    top5=set(ranked[:5]);top20=set(ranked[:20])
    return {"hit5":int(bool(top5&truth)),"hit20":int(bool(top20&truth)),
            "recall5":len(top5&truth)/len(truth),"recall20":len(top20&truth)/len(truth),
            "mrr":1/known[0] if known else 0,"known_target_ranks":known,
            "top20":[{"gene":ranked[i],"score":float(scores[order[i]]),"known_assertion":ranked[i] in truth} for i in range(20)]}
def summarize(rows,arms):
    grouped=defaultdict(list)
    for r in rows:grouped[r["identity_index"]].append(r)
    output={}
    for arm in arms:
        values=[r["arms"][arm] for r in rows]
        macro={metric:float(np.mean([np.mean([q["arms"][arm][metric] for q in drugrows]) for drugrows in grouped.values()]))
               for metric in ["hit5","hit20","recall5","recall20","mrr"]} if rows else {}
        micro={metric:float(np.mean([q[metric] for q in values])) for metric in ["hit5","hit20","recall5","recall20","mrr"]} if rows else {}
        output[arm]={"drug_denominator":len(grouped),"query_denominator":len(rows),
                     "query_hit5_count":sum(v["hit5"] for v in values),"query_hit20_count":sum(v["hit20"] for v in values),
                     "drug_macro":macro,"query_micro":micro}
    return output

def main():
    if OUT.exists():raise RuntimeError("Refuse overwrite relation scoring")
    frozen=read(HERE/"RELATION_FREEZE.json")
    for name,digest in frozen["sha256"].items():
        if sha(ROOT/name)!=digest:raise RuntimeError("Relation freeze mismatch:"+name)
    required=["RELATION_PROTOCOL.json","relation_score.py","relation_encoder.py","RELATION_COMPATIBILITY.json","RELATION_ASSET_RECEIPTS.json"]
    if not all(str((HERE/x).relative_to(ROOT)).replace("\\","/") in frozen["sha256"] for x in required):raise RuntimeError("Required relation freeze files absent")
    if not read(HERE/"RELATION_COMPATIBILITY.json")["strict_original_subset_load"]:raise RuntimeError("Relation compatibility failed")
    a=read(ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json")["records"]
    first={}
    for r in a:
        if r["smiles"]:first.setdefault((str(r["cid"]),r["smiles"]),r)
    molecules=[first[k] for k in sorted(first)]
    cache=np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz")
    raw=unit([cache["molecule256"][r["candidate"]] for r in molecules])
    drug=cache["knowledge1024"][[r["candidate"] for r in molecules]].astype(np.float32)
    protein=np.load(ASSETS/"PROTEIN_FEATURES.npz")
    text=np.load(ASSETS/"RELATION_FEATURES.npz")
    np.testing.assert_array_equal(text["identity_cids"],[r["cid"] for r in molecules])
    np.testing.assert_array_equal(text["identity_smiles"],[r["smiles"] for r in molecules])
    np.testing.assert_array_equal(protein["gene_ids"],text["gene_ids"])
    genes=list(map(str,protein["gene_ids"]))
    protein_x=protein["protein1024"].astype(np.float32)
    gene_names=text["gene_name1024"].astype(np.float32)
    drug_names=text["drug_name1024"].astype(np.float32)
    relation_x=text["relation1024"].astype(np.float32)
    relations=list(map(str,text["relations"]))
    lookup={r:i for i,r in enumerate(relations)}
    truth_by_identity=[]
    for r in molecules:
        truth=defaultdict(set)
        if r["kg_exact_identity"]:
            for e in r["edges"]:truth[e["relation"]].add(e["gene"])
        truth_by_identity.append(dict(truth))
    queries=[(i,phrase,truth) for i,relationmap in enumerate(truth_by_identity) for phrase,truth in sorted(relationmap.items())]
    generic_sorted=sorted(r for r in GENERIC if r in lookup)
    generic_perm=np.random.default_rng(20261012).permutation(len(generic_sorted))
    full_perm=np.random.default_rng(20261012).permutation(len(relations))
    generic_mapping={p:generic_sorted[int(j)] for p,j in zip(generic_sorted,generic_perm)}
    full_mapping={p:relations[int(j)] for p,j in zip(relations,full_perm)}
    _,Fusion=official_classes()
    fusion=Fusion(1024).eval()
    specs=read(HERE/"mapkg_encoder_METADATA.json")["tensor_specs"]
    fusion.load_state_dict({k.removeprefix("fusion_module."):tensor(s) for k,s in specs.items() if k.startswith("fusion_module.")},strict=True)
    protein_perm=np.random.default_rng(20261010).permutation(len(genes))
    gene_index={g:i for i,g in enumerate(genes)}
    p_unit=unit(protein_x);name_unit=unit(gene_names)
    torch.set_num_threads(4)
    neighbors={}
    for i,r in enumerate(molecules):
        other=[j for j,t in enumerate(molecules) if i!=j and t["cid"]!=r["cid"] and t["smiles"]!=r["smiles"]]
        similar=raw[i]@raw[other].T
        neighbors[i]=[other[j] for j in np.argsort(-similar,kind="stable")[:5]]
    results=[];score_rows=[]
    with torch.inference_mode():
        incoming_by_relation={};incoming_names_by_relation={}
        for phrase in relations:
            rel=torch.from_numpy(relation_x[lookup[phrase]][None]).expand(len(genes),-1)
            incoming_by_relation[phrase]=unit(fusion(rel,torch.from_numpy(protein_x)).numpy())
            incoming_names_by_relation[phrase]=unit(fusion(rel,torch.from_numpy(gene_names)).numpy())
        for i,phrase,truth in queries:
            zdrug=torch.from_numpy(drug[i:i+1]);zrel=torch.from_numpy(relation_x[lookup[phrase]:lookup[phrase]+1])
            fused=unit(fusion(zdrug,zrel).numpy())[0]
            outgoing=fused@p_unit.T
            incoming=unit(drug[i:i+1])[0]@incoming_by_relation[phrase].T
            name_fused=unit(fusion(torch.from_numpy(drug_names[i:i+1]),zrel).numpy())[0]
            name_out=name_fused@name_unit.T
            name_in=unit(drug_names[i:i+1])[0]@incoming_names_by_relation[phrase].T
            relation_only=unit(relation_x[lookup[phrase]:lookup[phrase]+1])[0]@p_unit.T
            changed=generic_mapping.get(phrase,full_mapping[phrase])
            changed_rel=torch.from_numpy(relation_x[lookup[changed]:lookup[changed]+1])
            rel_shuffle=unit(fusion(zdrug,changed_rel).numpy())[0]@p_unit.T
            protein_shuffle=outgoing[protein_perm]
            vote=np.zeros(len(genes));pop=np.zeros(len(genes))
            for donor in neighbors[i]:
                for g in truth_by_identity[donor].get(phrase,set()):
                    if g in gene_index:vote[gene_index[g]]+=.2
            for j,r in enumerate(molecules):
                if j==i or r["cid"]==molecules[i]["cid"] or r["smiles"]==molecules[i]["smiles"]:continue
                for g in truth_by_identity[j].get(phrase,set()):
                    if g in gene_index:pop[gene_index[g]]+=1
            scores=[outgoing,incoming,name_out,name_in,relation_only,rel_shuffle,protein_shuffle,vote,pop]
            score_rows.append(np.array(scores))
            results.append({"identity_index":i,"cid":molecules[i]["cid"],"smiles":molecules[i]["smiles"],
                            "drug":molecules[i]["drug"],"relation":phrase,"generic":phrase in GENERIC,
                            "truth_genes":sorted(truth),"unresolved_truth":sorted(truth-set(genes)),
                            "shuffled_relation":changed,"molecule_neighbors":neighbors[i],
                            "arms":{name:report(s,truth,genes) for name,s in zip(ARMS,scores)}})
    primary=[r for r in results if r["generic"]]
    prim=summarize(primary,ARMS)
    allsummary=summarize(results,ARMS)
    primary_value=prim[ARMS[0]]["drug_macro"]["hit5"]
    passed=all(primary_value>prim[ARMS[j]]["drug_macro"]["hit5"] for j in [4,7,8])
    mode_summary={phrase:summarize([r for r in primary if r["relation"]==phrase],ARMS) for phrase in GENERIC}
    summary={"generic_primary":prim,"all_original_phrases_exploratory":allsummary,"generic_relation_strata":mode_summary,
             "menu_candidates":len(a),"unique_encodable_identities":len(molecules),"all_known_assertion_drugs":len({r["identity_index"] for r in results}),
             "relation_dictionary":len(relations),"primary_content_advantage_passed":passed,
             "comparison":"Outgoing generic drug-macro hit5 must exceed relation-only, molecular exactrelation votes and exactrelation popularity.",
             "scope":"Original relation-conditioned known-graph content only; target-enriched gallery, possible training exposure; target-naming exploratory relation prose is answer-bearing. No biological/causal/response/decision claim.",
             "whole_checkpoint_sha256_verified":False,"frozen_input_sha256":frozen["sha256"]}
    OUT.mkdir(parents=True)
    (OUT/"RESULTS.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    (OUT/"SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    np.savez_compressed(OUT/"SCORES.npz",gene_ids=np.array(genes),scores=np.array(score_rows),protein_permutation=protein_perm,
                        query_identity_indices=np.array([i for i,_,_ in queries]),query_relations=np.array([p for _,p,_ in queries]))
    print(json.dumps({"generic_primary":prim,"primary_content_advantage_passed":passed},indent=2))

if __name__=="__main__":main()

