"""Independent raw-storage and source-row verification of the frozen protein assay."""
import hashlib,json,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/"outputs/map_module_replacement_20261009/protein_content"

def sha(p):return hashlib.file_digest(p.open("rb"),"sha256").hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def assert_equal(a,b,what):
    if a!=b:raise AssertionError(what)
def unit(a):
    x=np.asarray(a,dtype=np.float64)
    return x/np.sqrt(np.sum(x*x,axis=1))[:,None]

def original_head(specs,prefix,x):
    weights={}
    for name,spec in specs.items():
        if not name.startswith(prefix):continue
        raw=ROOT/"data/external/map_module_replacement_20261009/mapkg_storages"/spec["storage"]["key"]
        a=np.fromfile(raw,dtype="<f4").reshape(spec["shape"])
        assert spec["offset"]==0 and list(torch.from_numpy(a).stride())==spec["stride"]
        weights[name[len(prefix):]]=torch.from_numpy(a)
    def linear(a,name):return F.linear(a,weights[name+".weight"],weights[name+".bias"])
    with torch.inference_mode():
        x=torch.from_numpy(x)
        hidden=linear(x,"mlp.0")
        hidden=F.layer_norm(hidden,(hidden.shape[-1],),weights["mlp.1.weight"],weights["mlp.1.bias"],1e-5)
        transformed=linear(F.gelu(hidden),"mlp.4")
        residual=linear(x,"residual_proj")
        gate=torch.sigmoid(linear(x,"gate.0"))
        return (gate*transformed+(1-gate)*residual).numpy()

def main():
    freeze=read(HERE/"PROTEIN_VERIFY_FREEZE.json")
    assert_equal(sha(Path(__file__)),freeze["verifier_sha256"],"Verifier changed after its pre-inspection freeze")
    trial=read(HERE/"PROTEIN_FREEZE.json")
    for name,value in trial["sha256"].items():assert_equal(sha(ROOT/name),value,"Trial input hash "+name)
    assets=read(HERE/"PARTIAL_ASSET_RECEIPTS.json")
    for m in assets["member_receipts"]:
        data=(ROOT/m["file"]).read_bytes()
        assert_equal(len(data),m["bytes"],"Partial member size")
        assert_equal(hashlib.sha256(data).hexdigest(),m["sha256"],"Partial member digest")
        assert_equal(f"{zlib.crc32(data)&0xffffffff:08x}",m["crc32"],"Partial member ZIP CRC")
    meta=read(HERE/"mapkg_encoder_METADATA.json")
    esm_meta=read(HERE/"protein_embeddings_METADATA.json")
    qualified=read(HERE/"GALLERY_QUALIFICATION.json")
    p=np.load(ROOT/"data/external/map_module_replacement_20261009/PROTEIN_FEATURES.npz")
    raw_vectors=[]
    for row in qualified["gallery"]:
        spec=esm_meta["tensor_specs"][row["symbol"]]
        vector=np.fromfile(ROOT/"data/external/map_module_replacement_20261009/protein_storages"/spec["storage"]["key"],dtype="<f4")
        assert spec["shape"]==[5120] and spec["offset"]==0
        raw_vectors.append(vector)
    raw_vectors=np.array(raw_vectors)
    np.testing.assert_array_equal(raw_vectors,p["esm5120"])
    torch.set_num_threads(4)
    recomputed=original_head(meta["tensor_specs"],"gene_projector.",raw_vectors)
    np.testing.assert_allclose(recomputed,p["protein1024"],atol=1e-5,rtol=1e-5)
    cache=np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz")
    kg_rebuilt=original_head(meta["tensor_specs"],"smiles_projector.",cache["molecule256"].astype(np.float32))
    np.testing.assert_allclose(kg_rebuilt,cache["knowledge1024"],atol=1e-5,rtol=1e-5)
    audit=read(ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json")
    identities=read(ROOT/"outputs/paper_01286/released_test/IDENTITIES.json")["records"]
    gene_rows=pd.read_csv(ROOT/"data/external/mapkg_20261009/GENE_tahoe_filtered.csv",dtype=str,keep_default_na=False).to_dict("records")
    ids_to_symbols=defaultdict(set)
    symbols_to_ids=defaultdict(set)
    for row in gene_rows:
        gene,symbol=row["Gene stable ID"],row["ESM"]
        if gene and symbol:
            ids_to_symbols[gene].add(symbol)
            symbols_to_ids[symbol].add(gene)
    valid={g:next(iter(s)) for g,s in ids_to_symbols.items() if len(s)==1 and len(symbols_to_ids[next(iter(s))])==1 and next(iter(s)) in esm_meta["tensor_specs"]}
    raw_targets={e["gene"] for r in audit["records"] for e in r["edges"]}
    retained=sorted(raw_targets&set(valid))
    choices=sorted((symbol,gene) for gene,symbol in valid.items() if symbol not in {valid[g] for g in retained})
    draw=np.sort(np.random.default_rng(20261009).choice(len(choices),size=1000,replace=False))
    expected=[{"gene_id":g,"symbol":valid[g],"role":"menu_target"} for g in retained]
    expected += [{"gene_id":choices[int(i)][1],"symbol":choices[int(i)][0],"role":"fixed_global_distractor"} for i in draw]
    expected.sort(key=lambda x:x["gene_id"])
    assert_equal(expected,qualified["gallery"],"Independent global gallery construction")
    np.testing.assert_array_equal(p["gene_ids"],np.array([r["gene_id"] for r in expected]))
    np.testing.assert_array_equal(p["symbols"],np.array([r["symbol"] for r in expected]))
    # Bind every menu query assertion to raw CID/ENSG relation rows.
    edges=pd.read_csv(ROOT/"data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv",dtype=str,keep_default_na=False)
    edge_rows=edges.to_dict("records")
    groups={}
    for row in audit["records"]:
        i=row["candidate"]
        old=identities[i]
        for k in ["cid","smiles","drug","dose","unit"]:assert_equal(row[k],old[k],"Candidate identity "+k)
        assert_equal(bool(cache["mask"][i]),bool(row["smiles"]),"Encodable identity")
        if not row["smiles"]:continue
        key=(str(row["cid"]),row["smiles"])
        if key not in groups:groups[key]={"candidates":[],"truth":set(),"index":i,"cid":row["cid"],"smiles":row["smiles"]}
        g=groups[key]
        g["candidates"].append(i)
        np.testing.assert_array_equal(cache["molecule256"][i],cache["molecule256"][g["index"]])
        np.testing.assert_array_equal(cache["knowledge1024"][i],cache["knowledge1024"][g["index"]])
        if row["kg_exact_identity"]:
            for e in row["edges"]:
                raw=edge_rows[e["source_row"]-2]
                assert_equal(raw["Drug ID"],row["cid"],"Raw edge CID")
                assert_equal(raw["Gene ID"],e["gene"],"Raw edge stable gene")
                assert_equal(raw["relation"],e["relation"],"Raw relation text")
            g["truth"].update(e["gene"] for e in row["edges"])
    molecules=[groups[k] for k in sorted(groups)]
    query_ids=[i for i,g in enumerate(molecules) if g["truth"]]
    m=unit(np.array([cache["molecule256"][g["index"]] for g in molecules]))
    k=unit(np.array([cache["knowledge1024"][g["index"]] for g in molecules]))
    protein=unit(p["protein1024"])
    shuffle=np.random.default_rng(20261010).permutation(len(protein))
    permute=np.random.default_rng(20261011).permutation(len(molecules))
    computed=[k[query_ids]@protein.T,k[query_ids]@protein[shuffle].T,k[permute[query_ids]]@protein.T,
              np.zeros((len(query_ids),len(protein))),np.zeros((len(query_ids),len(protein)))]
    genes=list(map(str,p["gene_ids"]))
    gene_pos={g:i for i,g in enumerate(genes)}
    neighbor_lists=[]
    for q,index in enumerate(query_ids):
        source=molecules[index]
        others=[i for i,g in enumerate(molecules) if i!=index and g["cid"]!=source["cid"] and g["smiles"]!=source["smiles"]]
        similarity=[float(np.dot(m[index],m[j])) for j in others]
        neighbors=[others[i] for i in sorted(range(len(others)),key=lambda i:(-similarity[i],i))[:5]]
        neighbor_lists.append(neighbors)
        for donor in neighbors:
            for gene in molecules[donor]["truth"]:
                if gene in gene_pos:computed[3][q,gene_pos[gene]]+=.2
        for donor in others:
            for gene in molecules[donor]["truth"]:
                if gene in gene_pos:computed[4][q,gene_pos[gene]]+=1
    # First access to scored outputs occurs only after independent reconstruction.
    scores=np.load(OUT/"SCORES.npz")
    result=read(OUT/"RESULTS.json")
    summary=read(OUT/"SUMMARY.json")
    np.testing.assert_array_equal(scores["query_identity_indices"],query_ids)
    np.testing.assert_array_equal(scores["gene_ids"],p["gene_ids"])
    np.testing.assert_array_equal(scores["protein_permutation"],shuffle)
    np.testing.assert_array_equal(scores["identity_permutation"],permute)
    assert_equal(len(result),len(query_ids),"Query denominator")
    arm_names=list(result[0]["arms"])
    collected={a:[] for a in arm_names}
    top20_count=0
    for arm_index,name in enumerate(arm_names):
        np.testing.assert_allclose(scores[f"arm_{arm_index}"],computed[arm_index],atol=1e-12,rtol=1e-12)
        for q,index in enumerate(query_ids):
            known=molecules[index]["truth"]
            ordering=sorted(range(len(genes)),key=lambda j:(-computed[arm_index][q,j],j))
            rank_of={genes[j]:rank+1 for rank,j in enumerate(ordering)}
            ranks=sorted(rank_of[g] for g in known if g in rank_of)
            top5={genes[j] for j in ordering[:5]}
            top20={genes[j] for j in ordering[:20]}
            measured={"hit5":int(bool(top5&known)),"hit20":int(bool(top20&known)),
                      "recall5":len(top5&known)/len(known),"recall20":len(top20&known)/len(known),
                      "mrr":1/ranks[0] if ranks else 0,"known_target_ranks":ranks}
            saved=result[q]["arms"][name]
            for metric,value in measured.items():assert_equal(saved[metric],value,"Independent metric "+name+" "+metric)
            for rank,j in enumerate(ordering[:20]):
                assert_equal(saved["top20"][rank]["gene"],genes[j],"Top20 identity")
                assert_equal(saved["top20"][rank]["is_known_assertion"],genes[j] in known,"Top20 assertion flag")
                np.testing.assert_allclose(saved["top20"][rank]["score"],computed[arm_index][q,j],atol=1e-12,rtol=1e-12)
                top20_count+=1
            collected[name].append(measured)
    for q,index in enumerate(query_ids):
        assert_equal(result[q]["identity_index"],index,"Query identity")
        assert_equal(result[q]["candidate_indices"],molecules[index]["candidates"],"Dose identity membership")
        assert_equal(result[q]["truth_genes_all"],sorted(molecules[index]["truth"]),"Complete query truth")
        assert_equal([r["identity_index"] for r in result[q]["molecular_neighbor_identities"]],neighbor_lists[q],"Molecule donor order")
    for name,rows in collected.items():
        s=summary["arm_metrics"][name]
        assert_equal(s["queries"],len(rows),"Summary denominator")
        for metric in ["hit5","hit20","recall5","recall20","mrr"]:
            np.testing.assert_allclose(s[metric],np.mean([x[metric] for x in rows]),atol=1e-15,rtol=1e-15)
        assert_equal(s["hit5_count"],sum(r["hit5"] for r in rows),"Hit5 numerator")
        assert_equal(s["hit20_count"],sum(r["hit20"] for r in rows),"Hit20 numerator")
    hit=[summary["arm_metrics"][a]["hit5_count"] for a in arm_names]
    assert_equal(summary["primary_content_advantage_passed"],hit[0]>hit[3] and hit[0]>hit[4],"Acceptance arithmetic")
    report={"verifier_frozen_before_output_inspection":True,"verifier_sha256":freeze["verifier_sha256"],
            "trial_frozen_hash_entries_verified":len(trial["sha256"]),"partial_members_verified":len(assets["member_receipts"]),
            "protein_vectors_recomputed":len(raw_vectors),"protein_max_abs_gap":float(np.max(np.abs(recomputed-p["protein1024"]))),
            "molecule_cache_max_abs_gap":float(np.max(np.abs(kg_rebuilt-cache["knowledge1024"]))),
            "raw_assertions_bound_to_CID_gene_and_text":sum(len(r["edges"]) for r in audit["records"]),
            "menu_candidates_verified":len(audit["records"]),"unique_identity_rows_verified":len(molecules),"query_rows_verified":len(result),
            "score_values_verified":sum(x.size for x in computed),"ranked_top20_records_verified":top20_count,
            "all_five_arms_and_metrics_recomputed":True,"passed":True,
            "scope":"Source-content assay only; target-enriched gallery, possible pretraining graph exposure, no whole-file checkpoint digest or biological/decision validation."}
    (OUT/"VERIFIED.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()

