"""Strict original pretrained relation subset; no MAP response runtime or scoring."""
import ast,hashlib,json,sys,zlib
from pathlib import Path
import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ASSETS=ROOT/"data/external/map_module_replacement_20261009"
GENERIC=["functions as an inhibitor on the protein target","functions as an activator on the protein target",
         "functions as an agonist on the protein target","functions as an antagonist on the protein target","binds to the protein target"]
def sha(path):return hashlib.file_digest(path.open("rb"),"sha256").hexdigest()
def read(path):return json.loads(path.read_text(encoding="utf-8"))

def tensor(spec):
    path=ASSETS/"relation_storages"/spec["storage"]["key"]
    kind=spec["storage"]["type"]
    dtype="<i8" if kind=="torch.LongStorage" else "<f4" if kind=="torch.FloatStorage" else None
    if dtype is None:raise RuntimeError("Unsupported original tensor type")
    data=np.fromfile(path,dtype=dtype)
    if len(data)!=spec["storage"]["numel"] or spec["offset"]!=0:raise RuntimeError("Original storage metadata mismatch")
    value=torch.from_numpy(data).reshape(spec["shape"])
    if list(value.stride())!=spec["stride"]:raise RuntimeError("Unsupported stored view")
    return value

def official_classes():
    source=ROOT/"research/knowledge_layer_validation_20261009/sources/MAP-KG__model__model.py"
    parsed=ast.parse(source.read_text(encoding="utf-8"))
    selected=[n for n in parsed.body if isinstance(n,ast.ClassDef) and n.name in ["ResidualProjector","GatedFusion"]]
    scope={"torch":torch,"nn":torch.nn}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),"exec"),scope)
    return scope["ResidualProjector"],scope["GatedFusion"]

def load():
    from transformers import BertConfig,BertModel,BertTokenizer
    meta=read(HERE/"mapkg_encoder_METADATA.json")
    specs=meta["tensor_specs"]
    cfg=BertConfig.from_json_file(str(ASSETS/"biobert_tokenizer/config.json"))
    cfg.output_hidden_states=True
    with torch.device("meta"):
        bert=BertModel(cfg)
    original={k.removeprefix("text_encoder."):tensor(s) for k,s in specs.items() if k.startswith("text_encoder.")}
    if "embeddings.position_ids" in original:
        # Old HF stored this original deterministic ID buffer persistently;
        # modern HF marks it nonpersistent. Preserve the actual released value.
        bert.embeddings.register_buffer("position_ids",original["embeddings.position_ids"],persistent=True)
    expected=bert.state_dict()
    assert not set(original)-set(expected)
    missing=set(expected)-set(original)
    # Older Hugging Face releases stored deterministic ID buffers; require originals.
    extras=set(original)-set(expected)
    if extras:raise RuntimeError("Unexpected original text keys")
    if missing:raise RuntimeError("Missing original trainable text keys")
    for k,v in expected.items():
        if v.shape!=original[k].shape:raise RuntimeError("Text shape mismatch")
    bert.load_state_dict(original,strict=True,assign=True)
    # The original forward omits token_type_ids. Rebuild only modern HF's
    # nonpersistent all-zero default buffer; it is not a trained missing tensor.
    if hasattr(bert.embeddings,"token_type_ids"):
        bert.embeddings.token_type_ids=torch.zeros((1,cfg.max_position_embeddings),dtype=torch.long)
    if any(v.is_meta for v in bert.buffers()):raise RuntimeError("Unmaterialized text buffer")
    Residual,Fusion=official_classes()
    text=Residual(768,1024,768)
    text.load_state_dict({k.removeprefix("text_projector."):tensor(s) for k,s in specs.items() if k.startswith("text_projector.")},strict=True)
    fusion=Fusion(1024)
    fusion.load_state_dict({k.removeprefix("fusion_module."):tensor(s) for k,s in specs.items() if k.startswith("fusion_module.")},strict=True)
    tokenizer=BertTokenizer.from_pretrained(str(ASSETS/"biobert_tokenizer"),local_files_only=True)
    if len(tokenizer)!=original["embeddings.word_embeddings.weight"].shape[0]:raise RuntimeError("Vocabulary/tensor mismatch")
    return bert.eval(),text.eval(),fusion.eval(),tokenizer,{"text_keys":len(original),"text_head_keys":10,"fusion_keys":12,"config":cfg.to_dict()}

def encode(bert,text,tokenizer,values):
    result=[]
    with torch.inference_mode():
        for start in range(0,len(values),16):
            tokens=tokenizer(values[start:start+16],add_special_tokens=True,max_length=512,
                             padding="max_length",truncation=True,return_tensors="pt")
            tokens=tokens.to(next(bert.parameters()).device)
            output=bert(input_ids=tokens["input_ids"],attention_mask=tokens["attention_mask"])
            result.append(text(output.pooler_output).cpu().numpy())
            if start%160==0:print("Encoded text",min(start+16,len(values)),"/",len(values),flush=True)
    return np.concatenate(result)

def prepare():
    if (ASSETS/"RELATION_FEATURES.npz").exists():raise RuntimeError("Refuse overwrite relation feature cache")
    receipts=read(HERE/"RELATION_ASSET_RECEIPTS.json")
    for row in receipts["members"]:
        data=(ROOT/row["file"]).read_bytes()
        if len(data)!=row["bytes"] or hashlib.sha256(data).hexdigest()!=row["sha256"] or f"{zlib.crc32(data)&0xffffffff:08x}"!=row["crc32"]:
            raise RuntimeError("Original relation storage integrity failed")
    for row in receipts["tokenizer_assets"]:
        if sha(ROOT/row["file"])!=row["sha256"]:raise RuntimeError("Tokenizer hash mismatch")
    audit=read(ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json")["records"]
    by_identity={}
    for row in audit:by_identity.setdefault((str(row["cid"]),row["smiles"]),row)
    identities=[by_identity[k] for k in sorted(by_identity) if by_identity[k]["smiles"]]
    relations=sorted({e["relation"] for row in identities for e in row["edges"]})
    drug_nodes=pd.read_csv(ROOT/"data/external/mapkg_20261009/DRUG_merged_drugs_with_residuals.csv",dtype=str,keep_default_na=False)
    drug_name_by_cid={}
    for row in drug_nodes.to_dict("records"):
        drug_name_by_cid.setdefault(row["PubChem ID"],set()).add(row["Drug Name"])
    names=[]
    for row in identities:
        values=drug_name_by_cid.get(row["cid"],set())
        names.append(next(iter(values)) if row["kg_exact_identity"] and len(values)==1 else row["drug"])
    qualification=read(HERE/"GALLERY_QUALIFICATION.json")
    gene_names=[r["symbol"] for r in qualification["gallery"]]
    torch.set_num_threads(4)
    bert,text,fusion,tokenizer,load_info=load()
    # Faster modern HF backend must preserve the original eager attention equations.
    bert.set_attn_implementation("eager") if hasattr(bert,"set_attn_implementation") else None
    if torch.cuda.is_available():
        bert=bert.cuda()
        text=text.cuda()
    rel=encode(bert,text,tokenizer,relations)
    drug=encode(bert,text,tokenizer,names)
    gene=encode(bert,text,tokenizer,gene_names)
    again=encode(bert,text,tokenizer,[relations[0],relations[-1]])
    np.testing.assert_allclose(again,np.array([rel[0],rel[-1]]),atol=1e-5,rtol=1e-5)
    with torch.inference_mode():
        zero=torch.zeros(2,1024)
        x=torch.from_numpy(rel[:2])
        manual=fusion.fusion_net(torch.cat([x,fusion.gate_net(torch.cat([x,zero],dim=-1))*zero],dim=-1))
        torch.testing.assert_close(fusion(x,zero),manual,atol=0,rtol=0)
        swap=fusion(zero,x)
    path=ASSETS/"RELATION_FEATURES.npz"
    np.savez_compressed(path,relations=np.array(relations),relation1024=rel,
                        identity_cids=np.array([r["cid"] for r in identities]),
                        identity_smiles=np.array([r["smiles"] for r in identities]),
                        canonical_drug_names=np.array(names),drug_name1024=drug,
                        gene_ids=np.array([r["gene_id"] for r in qualification["gallery"]]),
                        canonical_gene_names=np.array(gene_names),gene_name1024=gene)
    report={"strict_original_subset_load":True,**{k:v for k,v in load_info.items() if k!="config"},
            "original_tensors_loaded":222,"relation_count":len(relations),"drug_names":len(names),"gene_names":len(gene_names),
            "tokenizer":"Pinned original BioBERT tokenizer; do_lower_case=False; CLS/SEP, truncation and maximum512padding.",
            "encode_implementation":"Original BioBERT BertModel pooler output -> original ResidualProjector; no pretrained-text substitute.",
            "fusion_exact_official_class":True,"fusion_order_probe_gap":float((manual-swap).abs().max()),
            "determinism_max_gap":float(np.max(np.abs(again-np.array([rel[0],rel[-1]])))),
            "cache_file":str(path.relative_to(ROOT)),"cache_sha256":sha(path),
            "scores_computed":False,"whole_checkpoint_sha256_verified":False,
            "forward_semantics":"Outgoing fusion(source,relation); incoming fusion(relation,target); gate multiplies second argument in both. No native RNA/runtime restoration.",
            "library_versions":{"torch":torch.__version__,"transformers":__import__("transformers").__version__}}
    (HERE/"RELATION_COMPATIBILITY.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":prepare()

