"""Separately frozen training-only diagnosis after both conditional means."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from research.decision_value.pairwise_20261009 import model as base
from research.decision_value.pairwise_v3 import joint_residual as joint
from research.decision_value.pairwise_v3 import support

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
OUT = ROOT / "outputs/decision_value/pairwise_v3_p0/conditional"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def corr(a, b):
    a,b=np.asarray(a).ravel(),np.asarray(b).ravel()
    return float(np.corrcoef(a,b)[0,1]) if len(a)>2 and a.std()>0 and b.std()>0 else None


def run():
    frozen=json.loads((HERE/"CONDITIONAL_FREEZE.json").read_text())
    for name,expected in frozen["inputs"].items():
        if sha(ROOT/name)!=expected: raise ValueError("conditional_diagnostic_freeze_mismatch:"+name)
    if OUT.exists(): raise ValueError("Refuse overwrite of conditional channel diagnostics")
    OUT.mkdir()
    arrays=dict(np.load(PACKET/"training_arrays.npz"))
    complete=np.flatnonzero((arrays["availability_A"]&arrays["availability_B"]).all(1)).tolist()
    records=json.loads((ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json").read_text())["records"]
    features=dict(np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz"))
    kernels,eigens,mask,_=base.prepare_kernels(records,features)
    reference=support.freeze_reference(arrays["basal"])
    write(OUT/"PUBLIC_REFERENCE.json",dict(public_contexts=reference["public_context_count"],
        bandwidth_sq=reference["bandwidth_sq"],transductive_public_covariates=True,
        outcome_labels_used=False,scope="All45packetbasalrows include outerheld publicstate; no independent external reference."))
    rows=[]
    for outer in complete:
        for seed in base.SEEDS:
            for size,ids in base.histories(complete,outer,seed).items():
                history=base.training_view(arrays,ids)
                for fold in range(3):
                    keep=[i for i in range(size) if i%3!=fold]
                    validation=[i for i in range(size) if i%3==fold]
                    training=base.training_view(history,keep)
                    for representation in (None,*base.REPRESENTATIONS):
                        fitted=joint.fit(training,kernels,eigens,mask,reference,representation,penalty=10.)
                        residual_a,residual_b,movement_old,movement_refit,actual,support_rows=[],[],[],[],[],[]
                        for held in validation:
                            public=base.public_view(history,held)
                            initial=base.prior(training,public)
                            pairs,query,_=base.pairs_and_query(initial)
                            mu_b,mu_a=joint.mean(fitted,public,eigens,reference)
                            ea=history["train_A"][held]-mu_a
                            eb=history["train_B"][held]-mu_b
                            residual_a.extend(ea.tolist()); residual_b.extend(eb.tolist())
                            pair=np.asarray(pairs);actual.extend((eb[pair[:,0]]-eb[pair[:,1]]).tolist())
                            n=len(initial)
                            for name,destination in (("old",movement_old),("refit",movement_refit)):
                                cov=fitted[name+"_matrices"]["empirical"]
                                contrast=cov[pair[:,0],n+query]-cov[pair[:,1],n+query]
                                destination.extend((contrast/cov[n+query,n+query]*ea[query]).tolist())
                            support_rows.append(support.assess(training["basal"],public["basal"],reference))
                        actual=np.asarray(actual); old=np.asarray(movement_old); refit=np.asarray(movement_refit)
                        rows.append(dict(outer_context=int(outer),seed=seed,history_size=size,fold=fold,
                            representation=representation or "baseline",fitting_ids=[ids[i] for i in keep],
                            validation_ids=[ids[i] for i in validation],lambda_fixed=10.,
                            corrected_residual_pearson=corr(residual_a,residual_b),
                            old_rho=fitted["old_rho"],refit_rho=fitted["refit_rho"],
                            residual_pair_zero_MSE=float(np.mean(actual**2)),
                            residual_pair_old_full_MSE=float(np.mean((actual-old)**2)),
                            residual_pair_refit_full_MSE=float(np.mean((actual-refit)**2)),
                            residual_pair_old_point1_MSE=float(np.mean((actual-.1*old)**2)),
                            residual_pair_refit_point1_MSE=float(np.mean((actual-.1*refit)**2)),
                            new_support=[{k:x[k]for k in ["n_eff","weight","distance_ratio"]}for x in support_rows]))
        print(f"Conditional P0 outer{outer}: train-only double leave-out mean and residual fits",flush=True)
    summary={}
    for size in base.SIZES:
        summary[str(size)]={}
        for rep in ("baseline",*base.REPRESENTATIONS):
            subset=[r for r in rows if r["history_size"]==size and r["representation"]==rep]
            summary[str(size)][rep]=dict(innerfits=len(subset),
                **{key:float(np.mean([r[key]for r in subset]))for key in ["old_rho","refit_rho",
                "residual_pair_zero_MSE","residual_pair_old_full_MSE","residual_pair_refit_full_MSE",
                "residual_pair_old_point1_MSE","residual_pair_refit_point1_MSE"]},
                validation_cases=sum(len(r["validation_ids"])for r in subset),
                positive_continuous_support=sum(x["weight"]>0 for r in subset for x in r["new_support"]))
    for name,expected in frozen["inputs"].items():
        if sha(ROOT/name)!=expected: raise ValueError("diagnostic_dependency_changed_during_run:"+name)
    write(OUT/"RESULTS.json",rows);write(OUT/"SUMMARY.json",dict(history_sizes=summary,
        interpretation="Only historical innerheld residual-prediction MSE, no outer target outcomes or policyutility. Corrected means need not imply useful residual transfer. Repeated overlapping fits are diagnostic, not independent confirmation."))
    write(OUT/"RECEIPT.json",dict(freeze_sha256=sha(HERE/"CONDITIONAL_FREEZE.json"),
        outputs={p.name:sha(p)for p in OUT.iterdir()if p.is_file()},new_API_calls=0,target_policy_scoring=False))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["freeze","run"])
    if parser.parse_args().command=="freeze":
        protocol=json.loads((HERE/"CONDITIONAL_PROTOCOL.json").read_text())
        paths=["research/decision_value/pairwise_v3/p0/conditional.py",
               "research/decision_value/pairwise_v3/p0/CONDITIONAL_PROTOCOL.json",*protocol["dependencies"]]
        write(HERE/"CONDITIONAL_FREEZE.json",dict(inputs={p:sha(ROOT/p)for p in paths}))
    else:
        with threadpool_limits(limits=1):run()
