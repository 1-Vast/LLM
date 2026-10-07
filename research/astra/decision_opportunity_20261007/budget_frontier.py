"""Post hoc all-prefix counterfactual budget frontier from registered paid traces."""
from __future__ import annotations

import csv
import importlib.util
import json
from datetime import datetime,timezone
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frontier_packet",HERE/"packet.py")
packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
study=packet.study


def main():
    out=HERE/"budget_frontier1"
    if out.exists():raise ValueError("Do not overwrite an existing frontier")
    out.mkdir()
    source=HERE/"development_run1"
    register=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status="Posthoc diagnostic after frozen direction and shared-trust results; no new outcomes or confirmatory claim",
        source_episode_sha256=study.digest(source/"EPISODES.jsonl"),
        packet_manifest_sha256=study.digest(HERE/"compact_packet2/PACKET_MANIFEST.json"),
        endpoint="curated_transcript_projection",models=["M0","M1","M2","M21"],
        policies=["fixed_top_prior","knowledge_gradient"],all_prefix_budgets=list(range(9)),
        cost="K existingpaidfirstwelldraws+5counterfactualBconfirmations; no extra actual purchases. Full saved8-stepsequence prefixes used.",
        comparison="AllK statevsbaseline sameK; exact percell STATEKutility>=M0KG8, then checkbothcells. No chosenKsuccess claim or hidden negativepoint.",
        limitation="Counterfactualsubsampleddecision evaluateseverystored Bprojection already exposed; not a newlytargetblindconfirmedpolicy" )
    study.write(out/"PROTOCOL.json",register)
    study.write(out/"FREEZE.json",dict(created_utc=datetime.now(timezone.utc).isoformat(),
                                      protocol_sha256=study.digest(out/"PROTOCOL.json")))
    results=[json.loads(line) for line in (source/"EPISODES.jsonl").read_text().splitlines()]
    meta=json.loads((HERE/"compact_packet2/PACKET_MANIFEST.json").read_text())
    rows=[]
    with np.load(HERE/"compact_packet2/public_prior.npz",allow_pickle=False) as public, np.load(HERE/"compact_packet2/evaluator_private.npz",allow_pickle=False) as private:
        for r in results:
            if r['endpoint']!='curated_transcript_projection' or r['model'] not in register['models'] or r['policy'] not in register['policies']:continue
            token=r['context'].replace('/','_').replace('-','_');ep=r['endpoint']
            prior=public[token+'__'+ep+'__'+r['model']+'__B']
            belief=study.Belief(prior.copy(),public[ep+'__cov'].copy(),public[ep+'__obsvar'].copy())
            offset=public[ep+'__offset'];yA=private[token+'__'+ep+'__A'];yB=private[token+'__'+ep+'__B']
            for k in range(9):
                if k>0:study.gaussian_update(belief,r['screened'][k-1],yA[r['screened'][k-1]],offset)
                final=study.flags(belief,5)
                rows.append(dict(context=r['context'],model=r['model'],policy=r['policy'],screens=k,
                    counterfactual_credits=k+5,utility=float(yB[final].sum()),flags=json.dumps(final),
                    selection_prefix=json.dumps(r['screened'][:k])))
    with (out/'FRONTIER.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    baseline={c:next(r['utility'] for r in rows if r['context']==c and r['model']=='M0' and r['policy']=='knowledge_gradient' and r['screens']==8) for c in meta['contexts']}
    comparisons=[]
    for model in register['models']:
        for policy in register['policies']:
            for k in range(9):
                selected=[r for r in rows if r['model']==model and r['policy']==policy and r['screens']==k]
                comparisons.append(dict(model=model,policy=policy,screens=k,credits=k+5,
                    mean_utility=float(np.mean([r['utility'] for r in selected])),
                    difference_from_simpleKG8={r['context']:r['utility']-baseline[r['context']] for r in selected},
                    meets_simpleKG8_both_contexts=all(r['utility']>=baseline[r['context']]-1e-12 for r in selected)))
    study.write(out/'SUMMARY.json',dict(status=register['status'],points=len(rows),actual_new_purchases=0,
        simpleKG8=baseline,all_comparisons=comparisons,
        first_exact_attainment={m+':'+pol:next((c['screens'] for c in comparisons if c['model']==m and c['policy']==pol and c['meets_simpleKG8_both_contexts']),None) for m in register['models'] for pol in register['policies']},
        no_confirmatory_benefit=True))
    print(json.dumps({'points':len(rows),'first_exact_attainment':json.loads((out/'SUMMARY.json').read_text())['first_exact_attainment']}))


if __name__=='__main__':main()
