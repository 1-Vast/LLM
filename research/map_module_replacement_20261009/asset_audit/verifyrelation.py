"""Independent original relation/fusion math and frozen retrieval verification."""
import hashlib,json,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ASSETS=ROOT/"data/external/map_module_replacement_20261009"
OUT=ROOT/"outputs/map_module_replacement_20261009/relation_content"
GENERIC=["functions as an inhibitor on the protein target","functions as an activator on the protein target",
         "functions as an agonist on the protein target","functions as an antagonist on the protein target","binds to the protein target"]
ARMS=["outgoing_molecule_relation_to_projected_protein_cosine","incoming_molecule_to_relation_projected_protein_cosine",
      "outgoing_canonical_name_relation_to_canonical_gene_name_cosine","incoming_canonical_drug_name_to_relation_canonical_gene_name_cosine",
      "relation_only_to_projected_protein_cosine","outgoing_molecule_with_fixed_relation_identity_permutation",
      "outgoing_molecule_relation_with_fixed_protein_identity_permutation","molecule256_nearest_five_other_identity_exactrelation_target_votes",
      "query_excluded_other_identity_exactrelation_target_popularity"]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.file_digest(p.open("rb"),"sha256").hexdigest()
def check(a,b,label):
    if a!=b:raise AssertionError(label)
def unit(a):
    a=np.asarray(a,dtype=np.float64)
    return a/np.sqrt(np.sum(a*a,axis=1))[:,None]

def params(prefix):
    specs=read(HERE/"mapkg_encoder_METADATA.json")["tensor_specs"]
    state={}
    for key,s in specs.items():
        if not key.startswith(prefix):continue
        dtype="<i8" if s["storage"]["type"]=="torch.LongStorage" else "<f4"
        a=np.fromfile(ASSETS/"relation_storages"/s["storage"]["key"],dtype=dtype).reshape(s["shape"])
        assert s["offset"]==0 and list(torch.from_numpy(a).stride())==s["stride"]
        state[key[len(prefix):]]=torch.from_numpy(a)
    return state

def functional_fusion(a,b,w):
    def linear(x,p):return F.linear(x,w[p+".weight"],w[p+".bias"])
    concat=torch.cat([a,b],dim=-1)
    gate=linear(concat,"gate_net.0")
    gate=F.layer_norm(gate,(gate.shape[-1],),w["gate_net.1.weight"],w["gate_net.1.bias"],1e-5)
    gate=torch.sigmoid(linear(F.gelu(gate),"gate_net.3"))
    hidden=linear(torch.cat([a,gate*b],dim=-1),"fusion_net.0")
    hidden=F.layer_norm(hidden,(hidden.shape[-1],),w["fusion_net.1.weight"],w["fusion_net.1.bias"],1e-5)
    return linear(F.gelu(hidden),"fusion_net.3")

def text_probe(t):
    from transformers import BertModel,BertConfig,BertTokenizer
    cfg=BertConfig.from_json_file(str(ASSETS/"biobert_tokenizer/config.json"))
    cfg.output_hidden_states=True
    cfg._attn_implementation="eager"
    original=params("text_encoder.")
    model=BertModel(cfg)
    model.embeddings.register_buffer("position_ids",original["embeddings.position_ids"],persistent=True)
    model.load_state_dict(original,strict=True)
    model=model.eval()
    tokenizer=BertTokenizer.from_pretrained(str(ASSETS/"biobert_tokenizer"),local_files_only=True)
    h=params("text_projector.")
    probes=[("relations","relation1024",[0,80,161]),("canonical_drug_names","drug_name1024",[0,55,110]),("canonical_gene_names","gene_name1024",[0,620,1240])]
    gaps={}
    if torch.cuda.is_available():
        model=model.cuda()
        h={k:v.cuda() for k,v in h.items()}
    with torch.inference_mode():
        for names,vectors,indices in probes:
            values=[str(t[names][i]) for i in indices]
            tokens=tokenizer(values,add_special_tokens=True,padding="max_length",truncation=True,max_length=512,return_tensors="pt").to(next(model.parameters()).device)
            out=model(input_ids=tokens["input_ids"],attention_mask=tokens["attention_mask"]).pooler_output
            transformed=F.linear(out,h["mlp.0.weight"],h["mlp.0.bias"])
            transformed=F.layer_norm(transformed,(768,),h["mlp.1.weight"],h["mlp.1.bias"],1e-5)
            transformed=F.linear(F.gelu(transformed),h["mlp.4.weight"],h["mlp.4.bias"])
            residual=F.linear(out,h["residual_proj.weight"],h["residual_proj.bias"])
            gate=torch.sigmoid(F.linear(out,h["gate.0.weight"],h["gate.0.bias"]))
            result=(gate*transformed+(1-gate)*residual).cpu().numpy()
            np.testing.assert_allclose(result,t[vectors][indices],atol=1e-5,rtol=1e-5)
            gaps[names]=float(np.max(np.abs(result-t[vectors][indices])))
    del model
    if torch.cuda.is_available():torch.cuda.empty_cache()
    return gaps

def main():
    self_freeze=read(HERE/"RELATION_VERIFY_FREEZE.json")
    check(sha(Path(__file__)),self_freeze["verifier_sha256"],"Verifier changed after freeze")
    frozen=read(HERE/"RELATION_FREEZE.json")
    for p,digest in frozen["sha256"].items():check(sha(ROOT/p),digest,"Relation input hash")
    asset=read(HERE/"RELATION_ASSET_RECEIPTS.json")
    for receipt in asset["members"]:
        data=(ROOT/receipt["file"]).read_bytes()
        check(len(data),receipt["bytes"],"Original relation member size")
        check(hashlib.sha256(data).hexdigest(),receipt["sha256"],"Original relation member SHA")
        check(f"{zlib.crc32(data)&0xffffffff:08x}",receipt["crc32"],"Original relation member CRC")
    t=np.load(ASSETS/"RELATION_FEATURES.npz")
    text_gaps=text_probe(t)
    p=np.load(ASSETS/"PROTEIN_FEATURES.npz")
    cache=np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz")
    raw_audit=read(ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json")["records"]
    first={}
    for row in raw_audit:
        if row["smiles"]:first.setdefault((str(row["cid"]),row["smiles"]),row)
    molecules=[first[k] for k in sorted(first)]
    relation_truth=[]
    for row in molecules:
        d=defaultdict(set)
        if row["kg_exact_identity"]:
            for edge in row["edges"]:d[edge["relation"]].add(edge["gene"])
        relation_truth.append(d)
    queries=[(i,r,truth) for i,d in enumerate(relation_truth) for r,truth in sorted(d.items())]
    raw_edges=pd.read_csv(ROOT/"data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv",dtype=str,keep_default_na=False).to_dict("records")
    for row in molecules:
        for e in row["edges"]:
            raw=raw_edges[e["source_row"]-2]
            check((raw["Drug ID"],raw["Gene ID"],raw["relation"]),(row["cid"],e["gene"],e["relation"]),"Raw query assertion closure")
    np.testing.assert_array_equal(t["identity_cids"],[row["cid"] for row in molecules])
    np.testing.assert_array_equal(t["identity_smiles"],[row["smiles"] for row in molecules])
    np.testing.assert_array_equal(t["gene_ids"],p["gene_ids"])
    relation_strings=list(map(str,t["relations"]))
    check(relation_strings,sorted({r for _,r,_ in queries}),"Relation dictionary")
    relations={s:i for i,s in enumerate(relation_strings)}
    generic=sorted(r for r in GENERIC if r in relations)
    gm={r:generic[j] for r,j in zip(generic,np.random.default_rng(20261012).permutation(len(generic)))}
    fm={r:relation_strings[j] for r,j in zip(relation_strings,np.random.default_rng(20261012).permutation(len(relation_strings)))}
    drug=cache["knowledge1024"][[r["candidate"] for r in molecules]].astype(np.float32)
    raw=unit(cache["molecule256"][[r["candidate"] for r in molecules]])
    protein=p["protein1024"].astype(np.float32)
    genes=list(map(str,p["gene_ids"]))
    gene_pos={g:i for i,g in enumerate(genes)}
    pn=unit(protein);gn=unit(t["gene_name1024"])
    shuffle=np.random.default_rng(20261010).permutation(len(genes))
    neighbors={}
    for i,q in enumerate(molecules):
        valid=[j for j,r in enumerate(molecules) if j!=i and r["cid"]!=q["cid"] and r["smiles"]!=q["smiles"]]
        scores=[np.dot(raw[i],raw[j]) for j in valid]
        neighbors[i]=[valid[j] for j in sorted(range(len(valid)),key=lambda k:(-scores[k],k))[:5]]
    w=params("fusion_module.")
    torch.set_num_threads(4)
    allscores=[]
    incoming={};incoming_name={}
    with torch.inference_mode():
        for phrase in relation_strings:
            relation=torch.from_numpy(t["relation1024"][relations[phrase]][None]).expand(len(genes),-1)
            incoming[phrase]=unit(functional_fusion(relation,torch.from_numpy(protein),w).numpy())
            incoming_name[phrase]=unit(functional_fusion(relation,torch.from_numpy(t["gene_name1024"]),w).numpy())
        for index,phrase,truth in queries:
            rel=torch.from_numpy(t["relation1024"][relations[phrase]][None])
            source=torch.from_numpy(drug[index:index+1])
            out=unit(functional_fusion(source,rel,w).numpy())[0]@pn.T
            inc=unit(drug[index:index+1])[0]@incoming[phrase].T
            name_out=unit(functional_fusion(torch.from_numpy(t["drug_name1024"][index:index+1]),rel,w).numpy())[0]@gn.T
            name_inc=unit(t["drug_name1024"][index:index+1])[0]@incoming_name[phrase].T
            rel_only=unit(t["relation1024"][relations[phrase]][None])[0]@pn.T
            swapped=gm.get(phrase,fm[phrase])
            swappedrel=torch.from_numpy(t["relation1024"][relations[swapped]][None])
            rel_shuffle=unit(functional_fusion(source,swappedrel,w).numpy())[0]@pn.T
            vote=np.zeros(len(genes));popular=np.zeros(len(genes))
            for donor in neighbors[index]:
                for g in relation_truth[donor].get(phrase,set()):
                    if g in gene_pos:vote[gene_pos[g]]+=.2
            for donor,row in enumerate(molecules):
                if donor==index or row["cid"]==molecules[index]["cid"] or row["smiles"]==molecules[index]["smiles"]:continue
                for g in relation_truth[donor].get(phrase,set()):
                    if g in gene_pos:popular[gene_pos[g]]+=1
            allscores.append(np.array([out,inc,name_out,name_inc,rel_only,rel_shuffle,out[shuffle],vote,popular]))
    allscores=np.array(allscores)
    # Only now inspect scored trial outputs.
    scores=np.load(OUT/"SCORES.npz")
    results=read(OUT/"RESULTS.json")
    summary=read(OUT/"SUMMARY.json")
    np.testing.assert_allclose(allscores,scores["scores"],atol=1e-12,rtol=1e-12)
    np.testing.assert_array_equal(scores["query_identity_indices"],[i for i,_,_ in queries])
    np.testing.assert_array_equal(scores["query_relations"],[r for _,r,_ in queries])
    np.testing.assert_array_equal(scores["protein_permutation"],shuffle)
    measurements=[]
    top20=0
    for qi,(index,phrase,truth) in enumerate(queries):
        saved=results[qi]
        check(saved["identity_index"],index,"Relation query identity")
        check(saved["relation"],phrase,"Original relation query")
        check(saved["truth_genes"],sorted(truth),"Complete original relation targets")
        check(saved["generic"],phrase in GENERIC,"Generic query selection")
        values={}
        for armno,arm in enumerate(ARMS):
            row=allscores[qi,armno]
            ordering=sorted(range(len(genes)),key=lambda j:(-row[j],j))
            ranks={genes[j]:n+1 for n,j in enumerate(ordering)}
            known=sorted(ranks[g] for g in truth if g in ranks)
            t5={genes[j] for j in ordering[:5]};t20={genes[j] for j in ordering[:20]}
            m={"hit5":int(bool(t5&truth)),"hit20":int(bool(t20&truth)),"recall5":len(t5&truth)/len(truth),"recall20":len(t20&truth)/len(truth),"mrr":1/known[0] if known else 0}
            for key,value in m.items():check(saved["arms"][arm][key],value,"Relation per-query metric "+key)
            check(saved["arms"][arm]["known_target_ranks"],known,"Known-target complete ranks")
            for n,j in enumerate(ordering[:20]):
                record=saved["arms"][arm]["top20"][n]
                check(record["gene"],genes[j],"Top20 target identity")
                check(record["known_assertion"],genes[j] in truth,"Top20 known assertion")
                np.testing.assert_allclose(record["score"],row[j],atol=1e-12,rtol=1e-12)
                top20+=1
            values[arm]=m
        measurements.append({"drug":index,"phrase":phrase,"generic":phrase in GENERIC,"metrics":values})
    for scope,subset in [("generic_primary",[m for m in measurements if m["generic"]]),("all_original_phrases_exploratory",measurements)]:
        bydrug=defaultdict(list)
        for m in subset:bydrug[m["drug"]].append(m)
        for arm in ARMS:
            s=summary[scope][arm]
            check(s["query_denominator"],len(subset),"Query denominator")
            check(s["drug_denominator"],len(bydrug),"Drug denominator")
            for key in ["hit5","hit20","recall5","recall20","mrr"]:
                micro=np.mean([m["metrics"][arm][key] for m in subset])
                macro=np.mean([np.mean([m["metrics"][arm][key] for m in rows]) for rows in bydrug.values()])
                np.testing.assert_allclose(s["query_micro"][key],micro,atol=1e-15,rtol=1e-15)
                np.testing.assert_allclose(s["drug_macro"][key],macro,atol=1e-15,rtol=1e-15)
    primary=summary["generic_primary"]
    hit=primary[ARMS[0]]["drug_macro"]["hit5"]
    check(summary["primary_content_advantage_passed"],all(hit>primary[ARMS[j]]["drug_macro"]["hit5"] for j in [4,7,8]),"Predefined acceptance")
    report={"passed":True,"verifier_frozen_before_output_inspection":True,"verifier_sha256":self_freeze["verifier_sha256"],
            "input_hash_entries_verified":len(frozen["sha256"]),"original_relation_members_verified":len(asset["members"]),
            "independent_text_probes_max_abs_gap":text_gaps,"independent_functional_gate_and_fusion_math":True,
            "query_rows_verified":len(queries),"generic_query_rows":sum(m["generic"] for m in measurements),
            "generic_drug_count":len({m["drug"] for m in measurements if m["generic"]}),
            "generic_relation_permutation_fixed_points":[r for r in generic if gm[r]==r],
            "generic_relation_permutation_fixed_point_count":sum(gm[r]==r for r in generic),
            "full_relation_permutation_fixed_point_count":sum(fm[r]==r for r in relation_strings),
            "all9_score_values_recomputed":int(allscores.size),"ranked_top20_records_verified":top20,
            "drugmacro_and_querymicro_recomputed":True,"scope":"Original relation-conditioned source-content only; generic primary and answer-bearing exploratory phrases remain separate. Whole checkpoint hash, biological effect and decision benefit unverified."}
    (OUT/"VERIFIED.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()

