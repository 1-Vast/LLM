"""Paid scalar feedback updates shared STATE correction, without training STATE weights."""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("direction_packet",HERE/"packet.py")
packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
study=packet.study


class TrustBelief:
    def __init__(self,baseA,baseB,stateA,stateB,covariance,noise,adaptive):
        n=len(baseA)
        self.baseA=np.asarray(baseA);self.baseB=np.asarray(baseB)
        self.noise=np.asarray(noise)
        self.mean=np.zeros(n+1);self.mean[0]=.5
        self.cov=np.zeros((n+1,n+1));self.cov[1:,1:]=covariance
        self.cov[0,0]=.25 if adaptive else 0.
        self.G=np.column_stack([stateB,np.eye(n)])
        self.H=np.column_stack([stateA,np.eye(n)])

    def target_mean(self):return self.baseB+self.G @ self.mean

    def direction(self,index):
        h=self.H[index]
        variance=float(h @ self.cov @ h+self.noise[index])
        if not np.isfinite(variance) or variance<=0:raise ValueError("Invalid empirical observation variance")
        return self.G @ self.cov @ h/np.sqrt(variance)

    def kg(self,available,normals):
        mean=self.target_mean();current=np.sort(mean)[-5:].sum();scores={}
        for i in available:
            draws=mean[None]+normals[:,None]*self.direction(i)[None]
            scores[i]=float(np.partition(draws,len(mean)-5,axis=1)[:,-5:].sum(1).mean()-current)
        return scores

    def update(self,index,observed):
        h=self.H[index];v=self.cov @ h;denom=float(h @ v+self.noise[index])
        innovation=float(observed-self.baseA[index]-h @ self.mean)
        self.mean=self.mean+v/denom*innovation
        self.cov=self.cov-np.outer(v,v)/denom
        self.cov=(self.cov+self.cov.T)*.5
        return innovation


def run(out):
    frozen=json.loads((HERE/"SUCCESSOR_FREEZE.json").read_text())
    if study.digest(HERE/"SUCCESSOR_PROTOCOL.json")!=frozen["protocol_sha256"]:raise ValueError("Successor freeze changed")
    p=json.loads((HERE/"SUCCESSOR_PROTOCOL.json").read_text())
    path=HERE/p["source_packet"]
    if study.digest(path/"PACKET_MANIFEST.json")!=p["packet_manifest_sha256"]:raise ValueError("Successor packet manifest differs")
    out=Path(out).resolve()
    if out.exists():raise ValueError("Do not overwrite prior experiment")
    out.mkdir(parents=True);started=time.perf_counter();normals=np.random.default_rng(42).standard_normal(64)
    endpoint="curated_transcript_projection";results=[]
    with np.load(path/"public_prior.npz",allow_pickle=False) as public:
        for context in p["contexts"]:
            token=context.replace("/","_").replace("-","_")
            fc={m:{r:public[token+"__"+endpoint+"__"+m+"__"+r] for r in ["A","B"]} for m in ["M0","M1","M2","M21","M2_state_permuted"]}
            d={r:2*(fc["M2"][r]-fc["M0"][r]) for r in ["A","B"]}
            perm={r:2*(fc["M2_state_permuted"][r]-fc["M0"][r]) for r in ["A","B"]}
            cov=public[endpoint+"__cov"];noise=public[endpoint+"__obsvar"]
            for arm in p["arms"]:
                base=fc["M0"] if arm=="M0_KG" else fc["M1"]
                state={r:np.zeros_like(d[r]) for r in ["A","B"]} if arm=="M0_KG" else (perm if "permuted" in arm else d)
                adaptive=arm.startswith("adaptive_gamma")
                belief=TrustBelief(base["A"],base["B"],state["A"],state["B"],cov,noise,adaptive)
                initial=study.flags(type("Mean",(),{"mean":belief.target_mean()})(),5)
                order=[int(i) for i in np.lexsort((np.arange(146),-belief.target_mean()))]
                case_id=f"trust.{token}.{arm}";evaluator=packet.ScalarEvaluator(path,out,case_id,context,endpoint)
                available=set(range(146));screens=[];trajectory=[]
                if arm!="adaptive_gamma_none":
                    for step in range(8):
                        if arm=="adaptive_gamma_fixed_top8":choice=next(i for i in order if i in available);estimate=None
                        else:
                            scores=belief.kg(sorted(available),normals);choice=max(scores,key=lambda i:(scores[i],-i));estimate=scores[choice]
                            if estimate<=0:break
                        before=belief.target_mean().copy();gamma_before=float(belief.mean[0]);var_before=float(belief.cov[0,0])
                        study.append(out/"policy.jsonl",dict(case_id=case_id,step=step,choice=choice,
                            gamma_before=gamma_before,gamma_var_before=var_before,expected_gaussian_gain=estimate,
                            predictions_before=before.tolist(),purchased=screens))
                        observed=evaluator.screen(choice);innovation=belief.update(choice,observed)
                        unmeasured=sorted(available-{choice});change=belief.target_mean()-before
                        record=dict(step=step,choice=choice,observed=observed,innovation=innovation,
                            gamma_before=gamma_before,gamma_after=float(belief.mean[0]),gamma_var_after=float(belief.cov[0,0]),
                            max_abs_unmeasured_change=float(np.max(np.abs(change[unmeasured]))),
                            gamma_only_unmeasured_change=float(np.max(np.abs((belief.mean[0]-gamma_before)*state['B'][unmeasured]))))
                        trajectory.append(record);study.append(out/"trajectory.jsonl",dict(case_id=case_id,**record))
                        screens.append(choice);available.remove(choice)
                final=study.flags(type("Mean",(),{"mean":belief.target_mean()})(),5)
                values=evaluator.confirm(final)
                # Only diagnostic oracle/rawflag contributions read evaluator values after commitment.
                yB=evaluator._yB
                incoming=sorted(set(final)-set(initial));outgoing=sorted(set(initial)-set(final))
                utility=float(sum(values));original=float(yB[initial].sum());oracle=float(np.sort(yB)[-5:].sum())
                result=dict(context=context,arm=arm,case_id=case_id,initial_flags=initial,final_flags=final,screened=screens,
                    utility=utility,initial_utility=original,improvement_from_feedback=utility-original,
                    oracle_utility=oracle,headroom=oracle-original,
                    actual_credits=len(screens)+5,unused_cap=13-len(screens)-5,
                    final_gamma=float(belief.mean[0]),final_gamma_variance=float(belief.cov[0,0]),
                    trajectory=trajectory,swapped_in=incoming,swapped_out=outgoing,
                    replacement_contribution=float(yB[incoming].sum()-yB[outgoing].sum()),
                    negative_gamma=float(belief.mean[0])<0,
                    interpretation="Downstream task-specific STATE correction trust coefficient; not model finetuning or calibrated biological risk")
                results.append(result);study.append(out/"EPISODES.jsonl",result)
                print(json.dumps({"context":context,"arm":arm,"utility":utility,"gamma":result['final_gamma']}),flush=True)
    groups=[]
    for arm in p['arms']:
        rows=[r for r in results if r['arm']==arm]
        groups.append(dict(arm=arm,mean_utility=float(np.mean([r['utility'] for r in rows])),
            per_context={r['context']:r['utility'] for r in rows},actual_credits=sum(r['actual_credits'] for r in rows),
            final_gamma={r['context']:r['final_gamma'] for r in rows},
            mean_feedback_improvement=float(np.mean([r['improvement_from_feedback'] for r in rows])),
            total_swapped_in=sum(len(r['swapped_in']) for r in rows)))
    study.write(out/"SUMMARY.json",dict(status="Exploratory shared STATE-trust successor",groups=groups,
        episodes=len(results),paid_profiles=sum(r['actual_credits'] for r in results),
        protocol_sha256=study.digest(HERE/'SUCCESSOR_PROTOCOL.json'),
        elapsed_seconds=time.perf_counter()-started,api_calls=0,new_wet_experiments=0,
        no_untouched_evaluation=True,uncertainty='Only two exposed dev cells; no claimed independent gain or valid population CI'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();run(args.out)
