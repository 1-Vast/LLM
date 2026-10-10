"""Frozen scalar A/B channel audit; no new policy or target-effect scoring."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
OUT = ROOT / "outputs/decision_value/pairwise_v3_p0"
spec = importlib.util.spec_from_file_location("p0_frozen_old_model", ROOT / "research/decision_value/pairwise_20261009/model.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def correlation(a, b):
    a, b = np.asarray(a, float).ravel(), np.asarray(b, float).ravel()
    if len(a) < 3 or not np.isfinite(a).all() or not np.isfinite(b).all():
        return None
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def distribution(values):
    values = np.array([v for v in values if v is not None], float)
    if not len(values):
        return dict(count=0, median=None, q25=None, q75=None, minimum=None, maximum=None)
    return dict(count=len(values), median=float(np.median(values)), q25=float(np.quantile(values, .25)),
                q75=float(np.quantile(values, .75)), minimum=float(values.min()), maximum=float(values.max()))


def raw_channels(arrays, complete, labels):
    doses = np.array([ast.literal_eval(label)[0][1] for label in labels])
    groups = {"all": np.arange(len(labels)), **{str(d): np.flatnonzero(doses == d) for d in sorted(set(doses))}}
    rows = []
    for context in complete:
        for name, indices in groups.items():
            a, b = arrays["train_A"][context, indices], arrays["train_B"][context, indices]
            rows.append(dict(context=int(context), dose_group=name, candidates=len(indices), pearson=correlation(a, b),
                spearman=float(spearmanr(a, b).statistic), mean_A=float(a.mean()), mean_B=float(b.mean()),
                mean_A_minus_B=float((a-b).mean()), sd_A_minus_B=float((a-b).std(ddof=1))))
    summary = {name: dict(candidates=len(indices), pearson=distribution([r["pearson"] for r in rows if r["dose_group"] == name]),
        spearman=distribution([r["spearman"] for r in rows if r["dose_group"] == name])) for name, indices in groups.items()}
    across_background = [dict(candidate=i, pearson=correlation(arrays["train_A"][complete, i], arrays["train_B"][complete, i]))
                         for i in range(len(labels))]
    return dict(per_context=rows, summary=summary, per_candidate_across_background=across_background,
                interpretation="Within-background raw correlation is across candidate responses, not residual transfer, noise-corrected reliability or independent biological risk.")


def source_metadata(arrays, manifest, complete):
    source = json.loads((HERE / "SOURCE_RECEIPTS.json").read_text())
    upstream = json.loads((ROOT / "research/astra/boundary_acquisition_20261007/PROTOCOL.json").read_text())
    labels = manifest["labels"]
    bindings = []
    for i, label in enumerate(labels):
        (drug, dose, unit), = ast.literal_eval(label)
        plate_A, plate_B = manifest["wells"][label]
        bindings.append(dict(candidate=i, label=label, drug_label=drug, dose=dose, unit=unit,
                             plate_A=plate_A, plate_B=plate_B, same_plate=plate_A == plate_B))
    pair_groups = {}
    for row in bindings:
        pair_groups.setdefault((row["plate_A"], row["plate_B"]), []).append(row["candidate"])
    offsets = []
    for (a, b), indices in sorted(pair_groups.items()):
        difference = arrays["train_A"][np.ix_(complete, indices)] - arrays["train_B"][np.ix_(complete, indices)]
        offsets.append(dict(plate_A=a, plate_B=b, candidates=len(indices), background_count=len(complete),
                            descriptive_mean_A_minus_B=float(difference.mean()),
                            background_mean_difference=distribution(difference.mean(1).tolist())))
    missing = [name for name in upstream["upstream_dependencies"] if not (ROOT / name).exists()]
    return dict(candidate_bindings=bindings, plate_pair_offset_descriptions=offsets, historical_source_receipts=source,
        original_upstream_assets=dict(declared=len(upstream["upstream_dependencies"]), absent=len(missing), missing=missing),
        facts=["Packet A/B are two different original label+plate groups, not the hash-split cell halves called meanA/meanB in observations.py.",
            "Each original well response subtracts the reference-half DMSO mean from the same plate. Basal DMSO cells are separate from reference DMSO cells.",
            "Training treated summaries used at most32 sampled cells per well before full-QC filtering; source selection used contiguous metadata-only windows.",
            "precision_B is inverse mean sampling variance over2000genes, not authenticated covariance of the39gene scalar projection.",
            "The24hour metadata in the paid replay action is simulation metadata; the scalar packet does not authenticate real exposure duration.",
            "Plate categories and sample enumerations do not establish independent culture batches or joined sample/plate identities."],
        unknowns=["Separate biological response variance, plate/source effects, sampling noise and control noise cannot be identified from one scalar A and one scalar B per action/background.",
            "Per-gene within-well covariance, sampled-cell counts, replicate-control summaries and source sample/plate joins are absent from the scalar training packet.",
            "The frozen raw extraction arrays and authenticated2000gene coordinate asset are absent; this audit authenticates the scalar cache and source recipe, not a fresh raw rebuild."],
        decomposition_status="NOT_IDENTIFIABLE_FROM_CURRENT_SCALAR_PACKET")


def inner_transfer(arrays, complete, kernels, mask):
    rows, query_rows = [], []
    for outer in complete:
        for seed in old.SEEDS:
            for size, train in old.histories(complete, outer, seed).items():
                history = old.training_view(arrays, train)
                full = old.fit(history, kernels, mask)
                public = old.public_view(arrays, outer)
                baseline = old.prior(history, public)
                pairs, query, _ = old.pairs_and_query(baseline)
                n, pair = len(baseline), np.array(pairs)
                matrix = full["matrices"]["empirical"]
                contrast = matrix[pair[:, 0], n:] - matrix[pair[:, 1], n:]
                information = (contrast**2 / np.diag(matrix)[None, n:]).sum(0)
                order = np.lexsort((np.arange(n), -information))
                query_rows.append(dict(outer_context=int(outer), seed=seed, history_size=size,
                    query=query, model_information_rank=int(np.flatnonzero(order == query)[0])+1,
                    model_information_ratio=float(information[query]/information.max()) if information.max()>0 else 0.,
                    pairs_with_dose_support=int(sum(mask[i, query] > 0 or mask[j, query] > 0 for i, j in pairs)),
                    rho=full["rho"]))
                for fold in range(3):
                    keep = [i for i in range(size) if i % 3 != fold]
                    validation = [i for i in range(size) if i % 3 == fold]
                    training = old.training_view(history, keep)
                    fitted = old.fit(training, kernels, mask)
                    pearsons, predicted, actual, support = [], [], [], []
                    for held in validation:
                        public = old.public_view(history, held)
                        base = old.prior(training, public)
                        pairs, q, _ = old.pairs_and_query(base)
                        e_a = history["train_A"][held] - base - fitted["offset"]
                        e_b = history["train_B"][held] - base
                        pearsons.append(correlation(e_a, e_b))
                        pair = np.array(pairs); covariance = fitted["matrices"]["empirical"]
                        beta = (covariance[pair[:,0], n+q] - covariance[pair[:,1], n+q]) / covariance[n+q,n+q]
                        predicted.extend((beta*e_a[q]).tolist())
                        actual.extend((e_b[pair[:,0]]-e_b[pair[:,1]]).tolist())
                        similarity = np.maximum(old.cell_similarity(fitted, public), 0.)
                        total_square = similarity@similarity
                        support.append(float(similarity.sum()**2/total_square) if total_square>0 else 0.)
                    predicted, actual = np.array(predicted), np.array(actual)
                    rows.append(dict(outer_context=int(outer), seed=seed, history_size=size, inner_fold=fold,
                        outer_history_ids=train, fitting_ids=[train[i] for i in keep], validation_ids=[train[i] for i in validation],
                        raw_OOF_residual_pearson=distribution(pearsons), covariance_rho=fitted["rho"],
                        validation_contexts=len(validation), support_eligible=sum(x>=2 for x in support), n_eff=support,
                        pair_transfer_correlation=correlation(predicted, actual),
                        pair_zero_prediction_MSE=float(np.mean(actual**2)),
                        pair_full_transfer_MSE=float(np.mean((actual-predicted)**2)),
                        pair_fixed_point1_transfer_MSE=float(np.mean((actual-.1*predicted)**2))))
        print(f"P0 diagnostic outer{outer}: fits exclude outer and inner-held labels", flush=True)
    summary = {}
    for size in old.SIZES:
        subset = [r for r in rows if r["history_size"] == size]
        queries = [r for r in query_rows if r["history_size"] == size]
        summary[str(size)] = dict(inner_fits=len(subset), inner_validation_cases=sum(r["validation_contexts"] for r in subset),
            old_support_eligible=sum(r["support_eligible"] for r in subset),
            covariance_rho=distribution([r["covariance_rho"] for r in subset]),
            model_boundary_query_rank=distribution([r["model_information_rank"] for r in queries]),
            model_boundary_query_relative_information=distribution([r["model_information_ratio"] for r in queries]),
            mean_pairs_with_dose_support=float(np.mean([r["pairs_with_dose_support"] for r in queries])),
            mean_inner_pair_zero_prediction_MSE=float(np.mean([r["pair_zero_prediction_MSE"] for r in subset])),
            mean_inner_pair_full_transfer_MSE=float(np.mean([r["pair_full_transfer_MSE"] for r in subset])),
            mean_inner_pair_fixed_point1_transfer_MSE=float(np.mean([r["pair_fixed_point1_transfer_MSE"] for r in subset])))
    return dict(inner_rows=rows, outer_public_query_diagnostics=query_rows, summary=summary,
        interpretation="Train-only validation of the original baseline-residual transfer estimator. Full mean/offset/residual moments refitted excluding each innerheld group; no outer target A/B used. MSE/correlation diagnose transfer, not new target policy utility or independent identifiability.")


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command", choices=["freeze", "run"])
    parser.add_argument("--freeze", default="FREEZE.json")
    args=parser.parse_args(); command=args.command
    if command == "freeze":
        protocol=json.loads((HERE/"PROTOCOL.json").read_text())
        paths=[str((HERE/"audit.py").relative_to(ROOT)).replace("\\","/"),
               str((HERE/"PROTOCOL.json").relative_to(ROOT)).replace("\\","/"),
               str((HERE/"SOURCE_RECEIPTS.json").relative_to(ROOT)).replace("\\","/"), *protocol["dependencies"]]
        write(HERE/args.freeze, dict(scope="P0 original-channel diagnostics only", inputs={p:sha(ROOT/p) for p in paths}))
        return
    freeze=json.loads((HERE/args.freeze).read_text())
    for name,expected in freeze["inputs"].items():
        if sha(ROOT/name)!=expected: raise ValueError("p0_freeze_mismatch:"+name)
    if OUT.exists(): raise ValueError("Refuse overwrite of frozen P0 diagnostics")
    OUT.mkdir(parents=True)
    arrays=dict(np.load(PACKET/"training_arrays.npz")); manifest=json.loads((PACKET/"PACKET_MANIFEST.json").read_text())
    if sha(PACKET/"training_arrays.npz")!=manifest["hashes"]["training_arrays.npz"]:
        raise ValueError("packet_training_hash_mismatch")
    complete=np.flatnonzero((arrays["availability_A"] & arrays["availability_B"]).all(1)).tolist()
    if len(complete)!=43: raise ValueError("original_complete_context_count_changed")
    records=json.loads((ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json").read_text())["records"]
    features=dict(np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz"))
    kernels,_,mask,_=old.prepare_kernels(records,features)
    write(OUT/"RAW_CHANNELS.json", raw_channels(arrays,complete,manifest["labels"]))
    write(OUT/"SOURCE_AUDIT.json", source_metadata(arrays,manifest,complete))
    transfer=inner_transfer(arrays,complete,kernels,mask)
    write(OUT/"TRANSFER_DIAGNOSTICS.json",transfer)
    write(OUT/"RECEIPT.json",dict(protocol_sha256=sha(HERE/"PROTOCOL.json"), freeze_sha256=sha(HERE/args.freeze),
        outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}, new_API_calls=0, new_data_downloads=0,
        target_policy_scoring=False, diagnosis="Scalar-source causes remain nonidentifiable; estimates are exposed development diagnostics."))


if __name__ == "__main__":
    with threadpool_limits(limits=1): main()
