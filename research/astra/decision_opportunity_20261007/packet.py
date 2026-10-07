"""Build and replay a small derived packet; raw/STATE generation remains upstream."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec=importlib.util.spec_from_file_location("direction_study",HERE/"run.py")
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)


def build(run_path, out):
    run_path=Path(run_path).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError("Use a new packet directory")
    out.mkdir(parents=True)
    p=study.protocol()
    with np.load(run_path/"analysis_arrays.npz",allow_pickle=False) as a:
        keys=[tuple(row) for row in a["keys"].tolist()]
        idx={key:i for i,key in enumerate(keys)}
        labels=a["labels"].tolist()
        ia=[idx[(l,p["menu"]["wells"][l][0])] for l in labels]
        ib=[idx[(l,p["menu"]["wells"][l][1])] for l in labels]
        endpoints={"curated_transcript_projection":"curated_weights",
                   "native_reference_phenocopy":"phenocopy_weights",
                   "permuted_transcript_membership":"permuted_weights"}
        public={};sealed={}
        for endpoint,wkey in endpoints.items():
            w=a[wkey]
            public[endpoint+"__cov"]=a[endpoint+"_cov"]
            public[endpoint+"__obsvar"]=a[endpoint+"_obsvar"]
            public[endpoint+"__offset"]=a[endpoint+"_offset"]
            public[endpoint+"__train_A"]=a["train_delta"][:,ia].astype(float) @ w
            public[endpoint+"__train_B"]=a["train_delta"][:,ib].astype(float) @ w
            for context in p["contexts"]:
                token=context.replace("/","_").replace("-","_")
                sealed[token+"__"+endpoint+"__A"]=a[token+"_"+endpoint+"_yA"]
                sealed[token+"__"+endpoint+"__B"]=a[token+"_"+endpoint+"_yB"]
                for model in ["M0","M1","M2","M21","M2_state_permuted"]:
                    public[token+"__"+endpoint+"__"+model+"__A"]=a[token+"_"+model][ia] @ w
                    public[token+"__"+endpoint+"__"+model+"__B"]=a[token+"_"+model][ib] @ w
        np.savez_compressed(out/"public_prior.npz",**public)
        np.savez_compressed(out/"evaluator_private.npz",**sealed)
    inputs=[run_path/"analysis_arrays.npz",HERE/"PROTOCOL.json",HERE/"PROTOCOL_FREEZE.json",HERE/"sources/genesets.apoptosis.json"]
    study.write(out/"PACKET_MANIFEST.json",dict(schema="derived_native_direction_replay_packet_v1",
        meaning="Public prior features and separate evaluator-private target projections; no raw/control rows or checkpoint weights included",
        labels=labels,wells=p["menu"]["wells"],contexts=p["contexts"],endpoints=list(endpoints),
        source_hashes={str(path.relative_to(ROOT)):study.digest(path) for path in inputs},
        upstream_requirement="Re-generation requires pinned native observed/STATE arrays. Independent physical data extraction and checkpoint validation need larger upstream assets.",
        sizes={n:(out/n).stat().st_size for n in ["public_prior.npz","evaluator_private.npz"]},
        hashes={n:study.digest(out/n) for n in ["public_prior.npz","evaluator_private.npz"]},
        privacy="Filesystem partition is an evaluation contract, not an operating-system sandbox. Selector receives no evaluator-private file path or outcome array."))
    print(json.dumps({"packet_bytes":sum((out/n).stat().st_size for n in ["public_prior.npz","evaluator_private.npz"])}))


class ScalarEvaluator(study.PaidObservations):
    """Evaluator keeps outcomes; acquisition sees only reveal(index) results."""

    def __init__(self,packet,out,case_id,context,endpoint):
        manifest=json.loads((Path(packet)/"PACKET_MANIFEST.json").read_text())
        for name in ("public_prior.npz","evaluator_private.npz"):
            if study.digest(Path(packet)/name)!=manifest["hashes"][name]:raise ValueError("Packet content mismatch")
        with np.load(Path(packet)/"evaluator_private.npz",allow_pickle=False) as a:
            token=context.replace("/","_").replace("-","_")
            yA=a[token+"__"+endpoint+"__A"];yB=a[token+"__"+endpoint+"__B"]
        # Counts here reflect scalar source records, not original per-cell counts.
        super().__init__(out,case_id,context,manifest["labels"],manifest["wells"],yA,yB,
                         {"A":np.ones(len(yA),int),"B":np.ones(len(yB),int)})


def replay(packet,out):
    packet=Path(packet).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError("Use a new output directory")
    out.mkdir(parents=True)
    meta=json.loads((packet/"PACKET_MANIFEST.json").read_text())
    normals=np.random.default_rng(42).standard_normal(64)
    saved=[]
    with np.load(packet/"public_prior.npz",allow_pickle=False) as public:
        for context in meta["contexts"]:
            token=context.replace("/","_").replace("-","_")
            for endpoint in meta["endpoints"]:
                cov=public[endpoint+"__cov"];var=public[endpoint+"__obsvar"];offset=public[endpoint+"__offset"]
                for model in ["M0","M1","M2","M21","M2_state_permuted"]:
                    prior=public[token+"__"+endpoint+"__"+model+"__B"]
                    for policy in ["none","fixed_top_prior","knowledge_gradient"]:
                        case_id=f"{token}.{endpoint}.{model}.{policy}"
                        evaluator=ScalarEvaluator(packet,out,case_id,context,endpoint)
                        belief=study.Belief(prior.copy(),cov.copy(),var.copy())
                        available=set(range(len(prior)));order=[int(i) for i in np.lexsort((np.arange(len(prior)),-prior))]
                        choices=[]
                        if policy!="none":
                            for step in range(8):
                                if policy=="fixed_top_prior":choice=next(i for i in order if i in available)
                                else:
                                    scores=study.kg_values(belief,5,sorted(available),normals)
                                    choice=max(scores,key=lambda i:(scores[i],-i))
                                    if scores[choice]<=0:break
                                # No A/B target array is passed to the acquisition calculation.
                                observed=evaluator.screen(choice)
                                study.gaussian_update(belief,choice,observed,offset)
                                choices.append(choice);available.remove(choice)
                        final=study.flags(belief,5)
                        values=evaluator.confirm(final)
                        saved.append(dict(case_id=case_id,screened=choices,final_flags=final,
                                          utility=float(sum(values)),actual_credits=len(choices)+5))
    study.write(out/"REPLAY.json",dict(episodes=saved,packet_hash=study.digest(packet/"PACKET_MANIFEST.json"),
                                     claim="Small packet reconstruction of registered paid replay; no raw-data or biological validation."))
    print(json.dumps({"episodes":len(saved),"profiles":sum(x['actual_credits'] for x in saved)}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["build","replay"])
    parser.add_argument("--source",type=Path,required=True);parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();(build if args.command=="build" else replay)(args.source,args.out)
