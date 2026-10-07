"""Exposed-development native RNA direction decisions with charged well reveals."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = ROOT / "research/astra/zeroshot_context_20261007"
sys.path[:0] = [str(ROOT / "src"), str(PRIOR)]

import world_models as wm
from agent.case_store import CaseStore, MeasurementResult
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind
from agent_policy import Belief, flags


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def append(path, data):
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n")


def protocol():
    frozen = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text())
    if digest(HERE / "PROTOCOL.json") != frozen["protocol_sha256"]:
        raise ValueError("Protocol changed after registration")
    p = json.loads((HERE / "PROTOCOL.json").read_text())
    for name, sha in p["source_dependencies"].items():
        if digest(ROOT / name) != sha:
            raise ValueError("Registered source identity mismatch")
    return p


def fit_common_belief(trainA, trainB, availability):
    """Training-only empirical covariance; no assumption of independent gene scores."""
    available = np.asarray(availability, bool)
    x = np.where(available, trainB, np.nan)
    centre = np.nanmean(x, axis=0)
    count = available.sum(0)
    if np.any(count < 2):
        raise ValueError("Every registered candidate needs multiple training references")
    filled = np.where(available, trainB, centre[None])
    covariance = np.cov(filled, rowvar=False)
    covariance = .5 * covariance + .5 * np.diag(np.diag(covariance))
    covariance += np.eye(len(centre)) * 1e-12
    differences = np.where(available, trainA - trainB, np.nan)
    offset = np.nanmean(differences, axis=0)
    variance = np.maximum(np.nanvar(differences, axis=0, ddof=1), 1e-12)
    return covariance, variance, offset, count


def gaussian_update(belief, index, observed, offset):
    """The same conditional update for every world and every acquisition policy."""
    belief.update(index, observed - offset[index])


def kg_values(belief, m, available, normals):
    current = float(np.sort(belief.mean)[-m:].sum())
    result = {}
    for i in available:
        scale = np.sqrt(belief.cov[i, i] + belief.obs_var[i])
        direction = belief.cov[:, i] / scale
        draws = belief.mean[None] + normals[:, None] * direction[None]
        best = np.partition(draws, len(belief.mean) - m, axis=1)[:, -m:].sum(1)
        result[i] = float(best.mean() - current)
    return result


class PaidObservations:
    """Policy receives only explicitly purchased scalar first-well outcomes."""

    def __init__(self, out, case_id, context, labels, wells, yA, yB, counts,
                 *, budget=13., max_screens=8):
        self.store = CaseStore(out / "cases.sqlite")
        self.store.open_case(case_id, budget=budget)
        self.out, self.case_id, self.context = out, case_id, context
        self.labels, self.wells = labels, wells
        self._yA, self._yB = yA, yB
        self.counts = counts
        self.max_screens = max_screens
        self.purchased = set()
        self.confirmed = None

    def action(self, index, role):
        drug, dose = wm.parse_label(self.labels[index])
        plate = self.wells[self.labels[index]][0 if role == "A" else 1]
        return EvidenceAction(f"{role}.{index}", "Review a paid existing native-RNA source profile", 1., (),
            kind=EvidenceActionKind.EVIDENCE_REVIEW, time_hours=24.,
            expected_conditions={"drug": drug, "dose_uM": str(dose), "plate": plate,
                                 "native_readout": "registered_target_projection"})

    def reveal(self, index, role, version):
        action = self.action(index, role)
        self.store.start_action(self.case_id, version, action.identifier,
                                attempt_id=f"{self.case_id}.{action.identifier}", source="public_Tahoe_replay")
        append(self.out / "purchases.jsonl", dict(event="purchase_started", case_id=self.case_id,
            plan_version=version, candidate=index, role=role, label=self.labels[index],
            conditions=dict(action.expected_conditions), cost=1.))
        value = float(self._yA[index] if role == "A" else self._yB[index])
        if not np.isfinite(value):
            raise ValueError("Registered paid profile returned nonfinite projection")
        result = MeasurementResult(action.identifier,
            f"Published {self.context} {self.labels[index]} scalar native-RNA projection, role {role}",
            f"Tahoe:{self.context}:{self.labels[index]}:{action.expected_conditions['plate']}",
            self.context, 24., 1, True, conditions=action.expected_conditions,
            metrics={"registered_target_projection": str(value)}, record_count=int(self.counts[role][index]),
            evidence_kind=EvidenceKind.DERIVED_ANALYSIS,
            limitations=("Computed from previously exposed public RNA mean; no physical experiment or protein activity.",
                         "One well/source unit; sampled cells do not multiply independent replicates."),
            result_id=f"{self.case_id}.{action.identifier}.result", plan_version=version)
        imported = self.store.import_measurement(self.case_id, result)
        retry = self.store.import_measurement(self.case_id, result)
        if not imported.created or retry.created:
            raise ValueError("Paid replay result identity failed")
        append(self.out / "purchases.jsonl", dict(event="paid_reveal", case_id=self.case_id,
            plan_version=version, candidate=index, role=role, label=self.labels[index], value=value,
            result_id=result.result_id, recorded_credits=self.store.snapshot(self.case_id).spent,
            retry_created=retry.created, evidence_kind=result.evidence_kind.value))
        return value

    def screen(self, index):
        if (type(index) is not int or not 0 <= index < len(self.labels) or index in self.purchased
                or self.confirmed is not None or len(self.purchased) >= self.max_screens):
            raise ValueError("Invalid/duplicate/late screen purchase")
        plan = self.store.record_plan(self.case_id, [self.action(index, "A")], ready_to_measure=True,
                                      context_identifier=self.context)
        append(self.out / "purchases.jsonl", dict(event="screen_committed", case_id=self.case_id,
                                                  plan_version=plan.plan_version, candidate=index))
        value = self.reveal(index, "A", plan.plan_version)
        self.purchased.add(index)
        return value

    def confirm(self, selected):
        if (self.confirmed is not None or len(selected) != 5
                or any(type(i) is not int or not 0 <= i < len(self.labels) for i in selected)
                or len(set(selected)) != 5):
            raise ValueError("Five distinct committed flags required")
        self.confirmed = list(selected)
        plan = self.store.record_plan(self.case_id, [self.action(i, "B") for i in selected],
                                      ready_to_measure=True, context_identifier=self.context)
        append(self.out / "purchases.jsonl", dict(event="flags_committed", case_id=self.case_id,
            plan_version=plan.plan_version, candidates=selected, screen_order=sorted(self.purchased),
            biological_outcomes_B_unavailable_to_policy=True))
        values = [self.reveal(i, "B", plan.plan_version) for i in selected]
        self.store.record_decision(self.case_id, status="decided")
        return values


def decision_episode(prior, cov, obsvar, offset, yA, yB, labels, wells, context, counts,
                     out, case_id, policy, normals):
    belief = Belief(prior.copy(), cov.copy(), obsvar.copy())
    ledger = PaidObservations(out, case_id, context, labels, wells, yA, yB, counts)
    initial = flags(belief, 5)
    order = [int(i) for i in np.lexsort((np.arange(len(prior)), -prior))]
    available = set(range(len(prior)))
    screens, policies = [], []
    if policy != "none":
        for step in range(8):
            if policy == "fixed_top_prior":
                choice, estimated = next(i for i in order if i in available), None
            elif policy == "knowledge_gradient":
                scores = kg_values(belief, 5, sorted(available), normals)
                choice = max(scores, key=lambda i: (scores[i], -i))
                estimated = scores[choice]
                if estimated <= 0:
                    break
            else:
                raise ValueError("Unregistered selection policy")
            append(out / "policy.jsonl", dict(case_id=case_id, step=step, policy=policy,
                choice=choice, candidate_prior=float(prior[choice]), estimated_gaussian_gain=estimated,
                mean_before=belief.mean.tolist(), purchased_prior=screens))
            observed = ledger.screen(choice)
            gaussian_update(belief, choice, observed, offset)
            screens.append(choice)
            available.remove(choice)
            policies.append(estimated)
    final = flags(belief, 5)
    confirmed = ledger.confirm(final)
    swaps_in, swaps_out = sorted(set(final) - set(initial)), sorted(set(initial) - set(final))
    utility = float(sum(confirmed))
    # Outcome-rich quantities below are diagnostics computed after every flag was committed.
    oracle = [int(i) for i in np.lexsort((np.arange(len(yB)), -yB))[:5]]
    baseline = float(yB[initial].sum())
    best = float(yB[oracle].sum())
    gap = best - baseline
    return dict(case_id=case_id, context=context, policy=policy, initial_flags=initial, final_flags=final,
        screened=screens, swapped_in=swaps_in, swapped_out=swaps_out, utility=utility,
        initial_utility=baseline, improvement_from_feedback=utility-baseline,
        swapped_in_contribution=float(yB[swaps_in].sum()), swapped_out_contribution=float(yB[swaps_out].sum()),
        perfect_information_utility=best, perfect_information_flags=oracle, initial_headroom=gap,
        headroom_fraction_captured=(utility-baseline)/gap if gap > 1e-12 else None,
        actual_credits=len(screens)+5, unused_cap=13-len(screens)-5, failures=0,
        price_basis="One simulated credit per public profile; real download and compute priced separately",
        first_well_second_well_pearson=float(np.corrcoef(yA,yB)[0,1]),
        prior_B_rmse=float(np.sqrt(np.mean((prior-yB)**2))),
        prior_B_pearson=float(np.corrcoef(prior,yB)[0,1]),
        prior_A_rmse=float(np.sqrt(np.mean((prior+offset-yA)**2))))


def state_permutation(deviation, keys):
    rng = np.random.default_rng(42)
    groups = {}
    for i, (label, plate) in enumerate(keys):
        groups.setdefault((wm.parse_label(label)[1], plate), []).append(i)
    permutation = np.arange(len(keys))
    for indices in groups.values():
        permutation[indices] = rng.permutation(indices)
    return deviation[permutation], dict(changed_rows=int(np.sum(permutation != np.arange(len(keys)))),
        total_rows=len(keys), singleton_strata=sum(len(v)==1 for v in groups.values()),
        nonidentity_fraction=float(np.mean(permutation != np.arange(len(keys)))))


def run(out):
    p = protocol()
    out = Path(out).resolve()
    if out.exists():
        raise ValueError("Use a new output directory; prior runs are immutable")
    out.mkdir(parents=True)
    started = time.perf_counter()
    labels = p["menu"]["labels"]
    wells = p["menu"]["wells"]
    keys = sorted({(l, plate) for l in labels for plate in wells[l]})
    index = {key: i for i,key in enumerate(keys)}
    ia = np.array([index[(l,wells[l][0])] for l in labels])
    ib = np.array([index[(l,wells[l][1])] for l in labels])
    panel = wm.Panel(keys)
    W0 = panel.w_precision()
    m0 = panel.apply(W0)
    names = json.loads((ROOT / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json").read_text())["names"]
    apoptosis = np.zeros(2000)
    coordinates = [record["coordinate"] for record in p["primary"]["mapped"]]
    apoptosis[coordinates] = 1/len(coordinates)
    permuted = np.zeros(2000)
    randomcoords = np.random.default_rng(42).choice([i for i,n in enumerate(names) if n is not None],len(coordinates),replace=False)
    permuted[randomcoords] = 1/len(coordinates)
    refindex = index[(p["secondary"]["reference_label"],p["secondary"]["reference_plate"])]
    reference = m0[refindex]
    norm = float(np.linalg.norm(reference))
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("Fixed reference signature has zero/nonfinite norm")
    target = reference/norm/np.sqrt(2000)
    weights = {"curated_transcript_projection": apoptosis,
               "native_reference_phenocopy": target,
               "permuted_transcript_membership": permuted}
    vectors = dict(panel_mean=m0, keys=np.array(keys), labels=np.array(labels),
                   curated_weights=apoptosis, phenocopy_weights=target, permuted_weights=permuted,
                   train_delta=panel.delta, train_availability=panel.avail)
    endpoint_params = {}
    for endpoint,w in weights.items():
        train = panel.delta.astype(np.float64) @ w
        both = panel.avail[:,ia] & panel.avail[:,ib]
        cov,var,offset,n = fit_common_belief(train[:,ia],train[:,ib],both)
        endpoint_params[endpoint] = (cov,var,offset,n)
        vectors.update({f"{endpoint}_cov":cov,f"{endpoint}_obsvar":var,
                        f"{endpoint}_offset":offset,f"{endpoint}_reference_counts":n})
    normals = np.random.default_rng(42).standard_normal(64)
    results, mapping = [], {}
    for context,file in p["contexts"].items():
        # Read only the two already exposed development contexts. wm.target's
        # name resolves this exact dictionary entry, never evaluation contexts.
        if context not in ("PANC-1", "HepG2/C3A"):
            raise PermissionError("Evaluation contexts require a separate future freeze")
        t = wm.target(context,panel)
        tidx = {key:i for i,key in enumerate(t["keys"])}
        ta=np.array([tidx[(l,wells[l][0])] for l in labels]);tb=np.array([tidx[(l,wells[l][1])] for l in labels])
        if not np.all(t["eligible"][ta]) or not np.all(t["eligible"][tb]):
            raise ValueError("Some registered candidate source is not qualified; do not remove it")
        cols=t["panel_index"]
        # All selected labels are available, but align by keys rather than row order.
        kk=np.array([tidx[key] for key in keys])
        gate,_,_=panel.gate(t["basal"],W0,list(range(len(keys))),0.)
        state=t["devS"][kk]
        shuffled,check=state_permutation(state,keys);mapping[context]=check
        forecast={"M0":m0,"M1":m0+.5*gate,"M2":m0+.5*state,"M21":m0+.5*gate+.5*state,
                  "M2_state_permuted":m0+.5*shuffled}
        obsA=t["delta"][ta];obsB=t["delta"][tb]
        obs=wm.load_obs(file)
        oidx={key:i for i,key in enumerate(zip(obs["label"].tolist(),obs["plate"].tolist()))}
        counts={"A":np.array([obs["n"][oidx[(l,wells[l][0])]] for l in labels]),
                "B":np.array([obs["n"][oidx[(l,wells[l][1])]] for l in labels])}
        token=context.replace("/","_").replace("-","_")
        vectors[f"{token}_observed_A"]=obsA;vectors[f"{token}_observed_B"]=obsB
        for model, f in forecast.items():vectors[f"{token}_{model}"]=f
        for endpoint,w in weights.items():
            yA=obsA @ w;yB=obsB @ w
            cov,var,offset,n=endpoint_params[endpoint]
            vectors[f"{token}_{endpoint}_yA"]=yA;vectors[f"{token}_{endpoint}_yB"]=yB
            for model,f in forecast.items():
                prior=f[ib] @ w
                for policy in p["policies"]:
                    case_id=f"{token}.{endpoint}.{model}.{policy}"
                    result=decision_episode(prior,cov,var,offset,yA,yB,labels,wells,context,counts,
                        out,case_id,policy,normals)
                    result.update(endpoint=endpoint,model=model,target_kind="fixedRNAtranscriptprojection",
                                  independent_cells=1,repeat_drug_caveat="Drug-dose labels not independent drug samples")
                    results.append(result)
                    append(out/"EPISODES.jsonl",result)
            print(json.dumps({"context":context,"endpoint":endpoint,"episodes":15}),flush=True)
    np.savez(out/"analysis_arrays.npz",**vectors)
    grouped=[]
    for endpoint in weights:
        for model in forecast:
            for policy in p["policies"]:
                rows=[r for r in results if r["endpoint"]==endpoint and r["model"]==model and r["policy"]==policy]
                grouped.append(dict(endpoint=endpoint,model=model,policy=policy,contexts=len(rows),
                    mean_utility=float(np.mean([r["utility"] for r in rows])),
                    per_context={r["context"]:r["utility"] for r in rows},
                    mean_feedback_improvement=float(np.mean([r["improvement_from_feedback"] for r in rows])),
                    mean_initial_headroom=float(np.mean([r["initial_headroom"] for r in rows])),
                    mean_prior_rmse=float(np.mean([r["prior_B_rmse"] for r in rows])),
                    mean_A_B_correlation=float(np.mean([r["first_well_second_well_pearson"] for r in rows])),
                    swapped_candidates=sum(len(r["swapped_in"]) for r in rows),
                    actual_credits=sum(r["actual_credits"] for r in rows),
                    unused_cap=sum(r["unused_cap"] for r in rows)))
    bytes_read=sum((wm.CACHE/"observations"/(f+".npz")).stat().st_size+(wm.CACHE/"state_forecasts"/(f+".npz")).stat().st_size for f in panel.files+list(p["contexts"].values()))
    write(out/"SUMMARY.json",dict(status="development opportunity audit only",episodes=len(results),
        menu_labels=len(labels),training_contexts=len(panel.files),model_state_checkpoint="final.ckpt 2c9b2e74...f623a3",
        profiles=sum(r["actual_credits"] for r in results),resource_cap_total=len(results)*13,
        new_wet_experiments=0,api_calls=0,downloaded_bytes=0,logical_upstream_bytes=bytes_read,
        elapsed_seconds=time.perf_counter()-started,groups=grouped,state_permutation=mapping,
        target_coverage={"curated_named_genes":len(coordinates),"curated_members":161,"native_coordinates":2000},
        uncertainty="Two exposed development contexts; no inferential CI across independent cultures, no fitted biological mechanism threshold",
        arrays_sha256=digest(out/"analysis_arrays.npz"),protocol_sha256=digest(HERE/"PROTOCOL.json")))


if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();run(args.out)
