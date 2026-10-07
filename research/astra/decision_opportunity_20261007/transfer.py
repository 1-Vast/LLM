"""Frozen task transfer via a public-prior/evaluator-private scalar packet."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("direction_transfer_study", HERE / "run.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def protocol():
    p = json.loads((HERE / "TRANSFER_PROTOCOL.json").read_text())
    freeze = json.loads((HERE / "TRANSFER_FREEZE.json").read_text())
    if study.digest(HERE / "TRANSFER_PROTOCOL.json") != freeze["protocol_sha256"]:
        raise ValueError("Transfer protocol changed after freeze")
    for name, expected in p["source_dependencies"].items():
        if study.digest(ROOT / name) != expected:
            raise ValueError("Transfer source dependency changed: " + name)
    return p


def build_packet(out):
    p = protocol()
    out = Path(out).resolve()
    if out.exists():
        raise ValueError("Use a fresh packet directory")
    out.mkdir(parents=True)
    started = time.perf_counter()
    labels, wells = p["menu"]["labels"], p["menu"]["wells"]
    keys = sorted({(label, plate) for label in labels for plate in wells[label]})
    index = {key: i for i, key in enumerate(keys)}
    ia = np.array([index[(label, wells[label][0])] for label in labels])
    ib = np.array([index[(label, wells[label][1])] for label in labels])
    weights = np.zeros(2000)
    coordinates = [r["coordinate"] for r in p["primary"]["mapped"]]
    weights[coordinates] = 1 / len(coordinates)
    panel = study.wm.Panel(keys)
    m0 = panel.apply(panel.w_precision())
    train = panel.delta.astype(np.float64) @ weights
    availability = panel.avail[:, ia] & panel.avail[:, ib]
    cov, obsvar, offset, n = study.fit_common_belief(train[:, ia], train[:, ib], availability)
    public = dict(cov=cov, obsvar=obsvar, offset=offset, train_A=train[:, ia],
                  train_B=train[:, ib], availability=availability, reference_counts=n)
    private = {}
    source_hashes = {}
    for context, file in p["contexts"].items():
        # This is the first target projection of the newly frozen task; the full
        # profiles had been opened in earlier studies, as registered explicitly.
        t = study.wm.target(context, panel)
        target_index = {key: i for i, key in enumerate(t["keys"])}
        if any(key not in target_index for key in keys):
            raise ValueError("Full registered menu unavailable: " + context)
        kk = np.array([target_index[key] for key in keys])
        if not np.all(t["eligible"][kk]):
            raise ValueError("Unqualified registered source; do not trim menu: " + context)
        m2 = m0 + .5 * t["devS"][kk]
        token = context.replace("/", "_").replace("-", "_")
        public[token + "__M0"] = m0[ib] @ weights
        public[token + "__M2"] = m2[ib] @ weights
        private[token + "__A"] = t["delta"][kk[ia]] @ weights
        private[token + "__B"] = t["delta"][kk[ib]] @ weights
        obs = study.wm.load_obs(file)
        oindex = {key: i for i, key in enumerate(zip(obs["label"].tolist(), obs["plate"].tolist()))}
        private[token + "__counts_A"] = np.array([obs["n"][oindex[(label, wells[label][0])]] for label in labels])
        private[token + "__counts_B"] = np.array([obs["n"][oindex[(label, wells[label][1])]] for label in labels])
    for file in panel.files + list(p["contexts"].values()):
        for kind in ("observations", "state_forecasts"):
            path = study.wm.CACHE / kind / (file + ".npz")
            source_hashes[str(path.relative_to(ROOT)).replace("\\", "/")] = study.digest(path)
    np.savez_compressed(out / "public_prior.npz", **public)
    np.savez_compressed(out / "evaluator_private.npz", **private)
    names = ["public_prior.npz", "evaluator_private.npz"]
    study.write(out / "PACKET_MANIFEST.json", dict(schema="frozen_direction_transfer_packet_v1",
        protocol_sha256=study.digest(HERE / "TRANSFER_PROTOCOL.json"), contexts=p["contexts"],
        labels=labels, wells=wells, arms=p["arms"], source_hashes=source_hashes,
        hashes={name: study.digest(out / name) for name in names},
        sizes={name: (out / name).stat().st_size for name in names},
        elapsed_seconds=time.perf_counter()-started,
        logical_upstream_bytes=sum((ROOT / path).stat().st_size for path in source_hashes),
        privacy="Derived public priors and evaluator-only outcomes; split is a contract, not an OS sandbox",
        upstream="Regeneration still requires pinned cached profiles and native STATE weight validation; small replay is not small raw acquisition"))
    print(json.dumps({"packet_bytes": sum((out / name).stat().st_size for name in names), "contexts": len(p["contexts"])}))


class TransferEvaluator(study.PaidObservations):
    def __init__(self, packet, out, case_id, context, arm):
        meta = json.loads((packet / "PACKET_MANIFEST.json").read_text())
        token = context.replace("/", "_").replace("-", "_")
        with np.load(packet / "evaluator_private.npz", allow_pickle=False) as private:
            yA, yB = private[token + "__A"], private[token + "__B"]
            counts = {role: private[token + "__counts_" + role] for role in ("A", "B")}
        super().__init__(out, case_id, context, meta["labels"], meta["wells"], yA, yB, counts,
                         budget=float(arm["cap"]), max_screens=arm["screens"])


def episode(prior, cov, obsvar, offset, evaluator, arm, normals):
    """No evaluator-private outcome arrays enter acquisition or commitment."""
    belief = study.Belief(prior.copy(), cov.copy(), obsvar.copy())
    order = [int(i) for i in np.lexsort((np.arange(len(prior)), -prior))]
    available = set(range(len(prior)))
    initial = study.flags(belief, 5)
    screened = []
    for step in range(arm["screens"]):
        gain = None
        if arm["policy"] == "fixed_top_prior":
            choice = next(i for i in order if i in available)
        else:
            scores = study.kg_values(belief, 5, sorted(available), normals)
            choice = max(scores, key=lambda i: (scores[i], -i))
            gain = scores[choice]
            if gain <= 0:
                break
        study.append(evaluator.out / "policy.jsonl", dict(case_id=evaluator.case_id, step=step,
            policy=arm["policy"], choice=choice, mean_before=belief.mean.tolist(),
            estimated_gaussian_gain=gain, B_outcomes_unavailable=True))
        observed = evaluator.screen(choice)
        study.gaussian_update(belief, choice, observed, offset)
        screened.append(choice)
        available.remove(choice)
    final = study.flags(belief, 5)
    values = evaluator.confirm(final)
    snapshot = evaluator.store.snapshot(evaluator.case_id)
    return dict(case_id=evaluator.case_id, context=evaluator.context, arm=arm["name"],
        model=arm["model"], policy=arm["policy"], initial_flags=initial, final_flags=final,
        screened=screened, swapped_in=sorted(set(final)-set(initial)), swapped_out=sorted(set(initial)-set(final)),
        final_B_values=values, utility=float(sum(values)), actual_credits=snapshot.spent,
        budget_cap=arm["cap"], unused_cap=arm["cap"]-snapshot.spent,
        endpoint="mean member-transcript delta in 39 named native coordinates; not apoptosis function")


def replay(packet, out):
    p = protocol()
    packet, out = Path(packet).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError("Use a fresh output directory")
    out.mkdir(parents=True)
    started = time.perf_counter()
    meta = json.loads((packet / "PACKET_MANIFEST.json").read_text())
    if meta["protocol_sha256"] != study.digest(HERE / "TRANSFER_PROTOCOL.json"):
        raise ValueError("Wrong packet protocol")
    for name, expected in meta["hashes"].items():
        if study.digest(packet / name) != expected:
            raise ValueError("Packet integrity mismatch")
    results = []
    normals = np.random.default_rng(42).standard_normal(64)
    with np.load(packet / "public_prior.npz", allow_pickle=False) as public:
        for context in p["contexts"]:
            token = context.replace("/", "_").replace("-", "_")
            for arm in p["arms"]:
                case_id = token + "." + arm["name"]
                evaluator = TransferEvaluator(packet, out, case_id, context, arm)
                result = episode(public[token + "__" + arm["model"]], public["cov"], public["obsvar"],
                                 public["offset"], evaluator, arm, normals)
                results.append(result)
                study.append(out / "EPISODES.jsonl", result)
            print(json.dumps({"context": context, "episodes": 5}), flush=True)
    comparisons = []
    for context in p["contexts"]:
        rows = {r["arm"]: r for r in results if r["context"] == context}
        comparisons.append(dict(context=context, utilities={name: r["utility"] for name, r in rows.items()},
            M2fixed5_minus_M0KG8=rows["M2_fixed5"]["utility"]-rows["M0_KG8"]["utility"],
            M2fixed5_minus_M0fixed5=rows["M2_fixed5"]["utility"]-rows["M0_fixed5"]["utility"],
            credits_saved_vs_M0KG8=rows["M0_KG8"]["actual_credits"]-rows["M2_fixed5"]["actual_credits"]))
    means = {arm["name"]: float(np.mean([r["utility"] for r in results if r["arm"] == arm["name"]])) for arm in p["arms"]}
    success = means["M2_fixed5"] >= means["M0_KG8"] and all(r["credits_saved_vs_M0KG8"] == 3 for r in comparisons)
    study.write(out / "SUMMARY.json", dict(status=p["status"], episodes=len(results),
        profiles=sum(r["actual_credits"] for r in results), budget_cap_total=sum(r["budget_cap"] for r in results),
        full_menu=146, training_contexts=45, comparison_by_context=comparisons, mean_utilities=means,
        registered_raw_mean_cost_transfer_success=success,
        M2fixed5_minus_M0KG8_mean=means["M2_fixed5"]-means["M0_KG8"],
        api_calls=0, new_downloaded_bytes=0, new_wet_experiments=0, fresh_STATE_inference=0,
        elapsed_seconds=time.perf_counter()-started,
        packet_hash=study.digest(packet / "PACKET_MANIFEST.json"),
        protocol_sha256=study.digest(HERE / "TRANSFER_PROTOCOL.json"),
        nonclaim="Only three previously exposed public contexts; no population efficacy, apoptosis function, or LLM superiority"))
    print(json.dumps({"means": means, "registered_success": success, "profiles": sum(r["actual_credits"] for r in results)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "replay"])
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        build_packet(args.out)
    else:
        replay(args.packet, args.out)
