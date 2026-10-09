"""Frozen STATE RNA-score decisions: LOO development, protected shadow EVSI."""
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from .utility import estimate, permission_blocks, protected_selection

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT / "research/astra/state_feedback_repair_20261009"
sys.path.insert(0, str(PREVIOUS))
spec = importlib.util.spec_from_file_location("frozen_joint_feedback", PREVIOUS / "run.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
posterior = sys.modules["posterior"]
POLICIES = ("no_screen", "common_kg", "joint_kg", "joint_boundary",
            "shadow_evsi", "shadow_protected_evsi", "certified_evsi")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def offset(arrays, train):
    available = (arrays["availability_A"] & arrays["availability_B"])[train]
    difference = np.where(available, arrays["train_A"][train]-arrays["train_B"][train], np.nan)
    return np.nanmean(difference, axis=0)


def model(arrays, train):
    old_c, old_v, current_offset = previous.common_parameters(arrays, train)
    error_a, error_b, cells = [], [], []
    for cell in train:
        if not (arrays["availability_A"][cell] & arrays["availability_B"][cell]).all():
            continue
        keep = [i for i in train if i != cell]
        mean, deviation, _, _ = previous.readout.references(arrays, keep, cell)
        prediction = mean + .5*deviation
        error_b.append(arrays["train_B"][cell]-prediction)
        error_a.append(arrays["train_A"][cell]-offset(arrays, keep)-prediction)
        cells.append(cell)
    error_b, error_a = np.array(error_b), np.array(error_a)
    joint, count = posterior.fit_joint(error_b, error_a, np.ones_like(error_b, bool))
    return {"joint": joint, "common": posterior.common_joint(old_c, old_v),
            "offset": current_offset, "error_B": error_b, "error_A": error_a}, cells


def build(arrays, public, manifest):
    complete = (arrays["availability_A"] & arrays["availability_B"]).all(1)
    priors, models, qualifications = {}, {}, []
    for cell in range(len(complete)):
        if not complete[cell]:
            qualifications.append({"context": f"ref{cell}", "evaluable": False,
                "reason": "full146menu_A_B_support_missing", "A_count": int(arrays["availability_A"][cell].sum()),
                "B_count": int(arrays["availability_B"][cell].sum())})
            continue
        train = [i for i in range(45) if i != cell]
        mean, deviation, _, _ = previous.readout.references(arrays, train, cell)
        key = f"ref{cell}"
        priors[key] = mean+.5*deviation
        fitted, residual_cells = model(arrays, train)
        for name, value in fitted.items():
            models[key+"__"+name] = value
        qualifications.append({"context": key, "evaluable": True, "train": train,
            "residual_cells": residual_cells, "independent_confirmation": False})
    fitted, residual_cells = model(arrays, list(range(45)))
    for context in manifest["contexts"]:
        key = context.replace("-", "_").replace("/", "_")
        priors[key] = public[key+"__M2"]
        for name, value in fitted.items():
            models[key+"__"+name] = value
        qualifications.append({"context": key, "evaluable": True, "train": list(range(45)),
            "residual_cells": residual_cells, "independent_confirmation": False, "previously_exposed": True})
    return models, priors, qualifications


def shadow(mean_b, current_offset, covariance, buy, gated):
    """Model-only uncosted sensitivity; never presented as certified net EVSI."""
    mean = np.r_[mean_b, mean_b+current_offset]
    covariance = covariance.copy()
    selected = posterior.top5(mean_b)
    initial = selected.copy()
    rng = np.random.default_rng(20261009)
    purchased, history = [], []
    n = len(mean_b)
    for step in range(8):
        # Fresh independent draws each step; identical draws across compared arms.
        samples = rng.standard_normal(512)
        scores = estimate(mean, covariance, selected, samples, gated=gated)
        available = [i for i in range(n) if i not in purchased]
        index = max(available, key=lambda i: (scores["mc_lower"][i], -i))
        bound = float(scores["mc_lower"][index])
        if bound <= 0:
            history.append({"stop": "no_positive_model_EVSI_integration_lower_bound", "A_cost": len(purchased),
                "max_mc_lower": bound, "model_risk_certificate": False,
                "second_check": "identical_unchanged_belief_cached;no_new_evidence_or_round"})
            break
        row = {"step": step, "purchased_A": index, "cumulative_A_cost": step+1,
               "mc_lower": bound, "cap": float(scores["cap"][index]), "integration_only": True}
        history.append(row)  # Charge before the only permitted observation read.
        value = float(buy(index))
        if not np.isfinite(value):
            raise ValueError("paid_observation_nonfinite")
        row["observed_A"] = value
        mean, covariance = posterior.condition(mean, covariance, index, value)
        if gated:
            decision = protected_selection(mean[:n], covariance[:n, :n], selected)
            selected = decision["selected"]
            row["update_gate"] = decision
        else:
            selected = posterior.top5(mean[:n])
        purchased.append(index)
    history.append({"committed_B": selected, "cost_after_five_B": len(purchased)+5})
    return {"selected": selected, "initial_selected": initial, "purchased_A": purchased,
            "history": history, "cost": len(purchased)+5, "posterior_mean_B": mean[:n],
            "posterior_variance_B": np.diag(covariance[:n, :n]), "shadow_only": True}


def run_policy(prior, fitted, buy, policy):
    if policy in ("no_screen", "certified_evsi"):
        return {"selected": posterior.top5(prior), "purchased_A": [], "cost": 5,
                "posterior_mean_B": prior.copy(), "posterior_variance_B": np.diag(fitted["joint"])[:len(prior)],
                "history": [{"committed_B": posterior.top5(prior), "cost_after_five_B": 5}],
                "permission_blocks": permission_blocks() if policy == "certified_evsi" else []}
    if policy.startswith("shadow"):
        return shadow(prior, fitted["offset"], fitted["joint"], buy, policy == "shadow_protected_evsi")
    result = posterior.replay(prior, fitted["offset"], fitted["common" if policy == "common_kg" else "joint"],
                              buy, policy="boundary" if policy == "joint_boundary" else "kg")
    result["posterior_variance_B"] = np.diag(result.pop("posterior_cov_B"))
    return result


def evaluate(arrays, private, models, priors, qualifications):
    results = []
    for q in qualifications:
        if not q["evaluable"]:
            continue
        context = q["context"]
        reference = context.startswith("ref")
        if reference:
            cell = int(context[3:]); y_a, y_b = arrays["train_A"][cell], arrays["train_B"][cell]
        else:
            y_a, y_b = private[context+"__A"], private[context+"__B"]
        prior = priors[context]
        fitted = {name: models[context+"__"+name] for name in ("joint", "common", "offset")}
        initial = posterior.top5(prior)
        best = posterior.top5(y_b)  # Evaluator only; never provided to the policy.
        for policy in POLICIES:
            result = run_policy(prior, fitted, lambda i: float(y_a[i]), policy)
            selected = result["selected"]
            incoming, outgoing = sorted(set(selected)-set(initial)), sorted(set(initial)-set(selected))
            # Pair distinct replacements using committed predictions, never B.
            # All-cross-pair comparisons would count the same candidate repeatedly.
            final_mean = np.asarray(result["posterior_mean_B"])
            pairs = list(zip(sorted(incoming, key=lambda i: (-final_mean[i], i)),
                             sorted(outgoing, key=lambda i: (final_mean[i], i))))
            replacements = [{"in": i, "out": j, "B_delta": float(y_b[i]-y_b[j])} for i, j in pairs]
            for name in ("posterior_mean_B", "posterior_variance_B"):
                result[name] = np.asarray(result[name]).tolist()
            results.append({"context": context, "scope": "reference" if reference else "exposed_targets", "policy": policy,
                "terminal_B": float(y_b[selected].sum()), "initial_B": float(y_b[initial].sum()),
                "delta_vs_no_screen": float(y_b[selected].sum()-y_b[initial].sum()),
                "top5_regret": float(y_b[best].sum()-y_b[selected].sum()),
                "swapped_in": incoming, "swapped_out": outgoing, "replacement_pairs": replacements,
                "harmful_replacements": sum(p["B_delta"] < -1e-12 for p in replacements), **result})
        print(f"Evaluated {context}: seven fixed RNA-score policies", flush=True)
    return results


def summarize(results):
    summary = {}
    for scope in ("reference", "exposed_targets"):
        summary[scope] = {}
        for policy in POLICIES:
            rows = [r for r in results if r["scope"] == scope and r["policy"] == policy]
            summary[scope][policy] = {"contexts": len(rows), "mean_B": float(np.mean([r["terminal_B"] for r in rows])),
                "delta_vs_no_screen": float(np.mean([r["delta_vs_no_screen"] for r in rows])),
                "mean_A_purchases": float(np.mean([len(r["purchased_A"]) for r in rows])),
                "mean_cost": float(np.mean([r["cost"] for r in rows])), "total_cost": sum(r["cost"] for r in rows),
                "harm_contexts": sum(r["delta_vs_no_screen"] < -1e-12 for r in rows),
                "improved_contexts": sum(r["delta_vs_no_screen"] > 1e-12 for r in rows),
                "mean_top5_regret": float(np.mean([r["top5_regret"] for r in rows])),
                "harmful_replacements": sum(r["harmful_replacements"] for r in rows),
                "replacements": sum(len(r["replacement_pairs"]) for r in rows)}
    return {"policies": summary, "scientific_admission": "BLOCKED: independent model-risk certificate, utility-unit price and failure/latency contract unavailable",
            "scope": "Strict LOO43full-menu reference contexts are development,in-STATE-pretraining;five targets exposed. Shadowmodel-EVSI lower bound controlsMCintegrationerroronly. RNAutility,notfunctionalorcertifiedbenefit.",
            "promotion": "No production promotion or target-based policy selection"}


def main(packet, out):
    freeze = json.loads((HERE/"FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        if digest(ROOT/name) != expected:
            raise ValueError("frozen_input_changed:"+name)
    if packet.resolve() != (ROOT/"research/astra/boundary_acquisition_20261007/packet2").resolve():
        raise ValueError("only_registered_packet_qualified")
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    arrays, public = dict(np.load(packet/"training_arrays.npz")), dict(np.load(packet/"public_prior.npz"))
    manifest = json.loads((packet/"PACKET_MANIFEST.json").read_text())
    models, priors, qualifications = build(arrays, public, manifest)
    np.savez_compressed(out/"MODELS.npz", **models)
    np.savez_compressed(out/"PRIORS.npz", **priors)
    write(out/"QUALIFICATION.json", qualifications)
    private = dict(np.load(packet/"evaluator_private.npz"))
    results = evaluate(arrays, private, models, priors, qualifications)
    write(out/"RESULTS.json", results)
    write(out/"SUMMARY.json", {**summarize(results), "seconds": time.perf_counter()-started})
    print(json.dumps(summarize(results), indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        main(args.packet, args.out)
