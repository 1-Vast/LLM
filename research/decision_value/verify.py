"""Independent LOO, scalar decision integration and complete numerical repeat."""
import contextlib
import hashlib
import io
import json
import tempfile
import time
from pathlib import Path

import numpy as np
from scipy.stats import norm
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKET = ROOT/"research/astra/boundary_acquisition_20261007/packet2"
OUT = ROOT/"outputs/decision_value_validation_20261009"
BLOCKS = ["independent_model_risk_certificate_missing", "cost_utility_registration_missing",
          "failure_latency_registration_missing"]
Z_CRITICAL = norm.ppf(1-.05/(25*8))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-11)


def top(values):
    return np.lexsort((np.arange(len(values)), -np.asarray(values)))[:5].tolist()


def prior(arrays, train, held):
    train = [i for i in train if i != held]
    valid = arrays["availability_B"][train]
    weights = np.where(valid, arrays["precision_B"][train], 0.)
    empirical = (weights*np.where(valid, arrays["train_B"][train], 0.)).sum(0)/weights.sum(0)
    supported = arrays["state_available_B"][train]
    centre = np.where(supported, arrays["state_B"][train], 0.).sum(0)/supported.sum(0)
    deviation = np.where(arrays["state_available_B"][held], arrays["state_B"][held]-centre, 0.)
    return empirical+.5*deviation


def common(arrays, train):
    valid = (arrays["availability_A"] & arrays["availability_B"])[train]
    counts = valid.sum(0)
    b, a = arrays["train_B"][train], arrays["train_A"][train]
    centre = np.where(valid, b, 0.).sum(0)/counts
    filled = np.where(valid, b, centre)
    deviations = filled-filled.mean(0)
    raw = deviations.T@deviations/(len(train)-1)
    c = .5*raw+.5*np.diag(np.diag(raw))+np.eye(raw.shape[0])*1e-12
    differences = a-b
    offset = np.where(valid, differences, 0.).sum(0)/counts
    variance = np.maximum(np.where(valid, (differences-offset)**2, 0.).sum(0)/(counts-1), 1e-12)
    return np.block([[c, c], [c, c+np.diag(variance)]]), offset


def calibration(arrays, train):
    old, offset = common(arrays, train)
    cells = [i for i in train if (arrays["availability_A"][i] & arrays["availability_B"][i]).all()]
    eb, ea = [], []
    for cell in cells:
        keep = [i for i in train if i != cell]
        p = prior(arrays, keep, cell)
        _, inner_offset = common(arrays, keep)
        eb.append(arrays["train_B"][cell]-p)
        ea.append(arrays["train_A"][cell]-p-inner_offset)
    eb, ea = np.array(eb), np.array(ea)
    errors = np.concatenate((eb, ea), axis=1)
    moment = errors.T@errors/len(cells)
    covariance = .5*moment+.5*np.diag(np.diag(moment))+np.eye(len(moment))*1e-12
    return dict(joint=covariance, common=old, offset=offset, error_B=eb, error_A=ea), cells


def condition(initial, covariance, purchased, readings):
    if not purchased:
        return initial.copy(), covariance.copy()
    coords = len(initial)//2+np.array(purchased)
    cross = covariance[:, coords]
    marginal = covariance[np.ix_(coords, coords)]
    mu = initial+cross@np.linalg.solve(marginal, np.array(readings)-initial[coords])
    c = covariance-cross@np.linalg.solve(marginal, cross.T)
    return mu, c


def protection(mean, covariance, incumbent):
    proposal = top(mean)
    incoming, outgoing = sorted(set(proposal)-set(incumbent)), sorted(set(incumbent)-set(proposal))
    accepted, probabilities = True, []
    for i in incoming:
        for j in outgoing:
            difference = mean[i]-mean[j]
            sd = np.sqrt(max(covariance[i, i]+covariance[j, j]-2*covariance[i, j], 0.))
            accepted &= difference > 0 and difference >= Z_CRITICAL*sd
            p = norm.cdf(difference/sd) if sd > 0 else (1. if difference > 0 else .5 if difference == 0 else 0.)
            probabilities.append(dict(incoming=i, outgoing=j, probability=float(p)))
    return dict(selected=proposal if accepted else list(incumbent), proposal=proposal,
                incoming=incoming, outgoing=outgoing, accepted=bool(accepted),
                pair_probabilities=probabilities, model_only=True)


def candidate_gain(mean, covariance, incumbent, normals, index, gated):
    """One query's sample gains, with scalar pair checks across sample vectors."""
    n = len(mean)//2
    variance = covariance[n+index, n+index]
    direction = covariance[:n, n+index]/np.sqrt(variance) if variance > 0 else np.zeros(n)
    draws = mean[:n]+normals[:, None]*direction
    proposals = np.lexsort((np.broadcast_to(np.arange(n), draws.shape), -draws), axis=1)[:, :5]
    proposed_sum = np.take_along_axis(draws, proposals, axis=1).sum(1)
    raw = proposed_sum-draws[:, incumbent].sum(1)
    assert raw.min() >= -1e-11
    if gated:
        posterior_b = covariance[:n, :n]-np.outer(direction, direction)
        allowed = np.ones(len(normals), bool)
        incumbent_set = set(incumbent)
        # For each incumbent and proposal position, check only true replacements.
        for j in incumbent:
            outgoing = ~(proposals == j).any(1)
            for position in range(5):
                i = proposals[:, position]
                active = outgoing & np.array([int(q) not in incumbent_set for q in i])
                difference = draws[np.arange(len(normals)), i]-draws[:, j]
                sd = np.sqrt(np.maximum(posterior_b[i, i]+posterior_b[j, j]-2*posterior_b[i, j], 0.))
                allowed &= ~active | ((difference > 0) & (difference >= Z_CRITICAL*sd))
        raw = np.where(allowed, raw, 0.)
    current_gain = mean[top(mean[:n])].sum()-mean[incumbent].sum()
    direction_sorted = np.sort(direction)
    incumbent_direction = direction[incumbent].sum()
    slope = max(abs(direction_sorted[-5:].sum()-incumbent_direction),
                abs(direction_sorted[:5].sum()-incumbent_direction))
    cap = max(float(current_gain), 0.)+3*slope
    raw = np.maximum(raw, 0.)
    clipped = np.minimum(raw, cap)
    assert np.all(clipped <= raw) and np.all(clipped >= 0)
    lower = clipped.mean()-cap*np.sqrt(np.log(146*8/.05)/(2*len(normals)))
    return raw, cap, float(lower)


def integration(mean, covariance, incumbent, normals, gated):
    values = [candidate_gain(mean, covariance, incumbent, normals, i, gated) for i in range(len(mean)//2)]
    return np.array([v[2] for v in values]), np.array([v[1] for v in values])


def independently_replay(row, p, fitted, y_a):
    policy, n = row["policy"], len(p)
    selected, purchased, values = top(p), [], []
    initial = np.concatenate((p, p+fitted["offset"]))
    covariance = fitted["common" if policy == "common_kg" else "joint"]
    normals_kg = np.random.default_rng(20261008).standard_normal(64)
    rng = np.random.default_rng(20261009)
    if policy in ("no_screen", "certified_evsi"):
        assert row["history"] == [dict(committed_B=selected, cost_after_five_B=5)]
        assert row["permission_blocks"] == (BLOCKS if policy == "certified_evsi" else [])
        return selected, p, np.diag(covariance)[:n]
    if policy == "joint_boundary":
        ordered = np.lexsort((np.arange(n), -p))
        midpoint = .5*(p[ordered[4]]+p[ordered[5]])
        schedule = sorted(range(n), key=lambda i: (abs(p[i]-midpoint), i))[:8]
    for receipt in row["history"][:-1]:
        mean, post = condition(initial, covariance, purchased, values)
        available = [i for i in range(n) if i not in purchased]
        if policy.startswith("shadow"):
            normals = rng.standard_normal(512)
            lower, caps = integration(mean, post, selected, normals, policy == "shadow_protected_evsi")
            index = max(available, key=lambda i: (lower[i], -i))
            if "stop" in receipt:
                assert lower[index] <= 0 and receipt["A_cost"] == len(purchased)
                equal(receipt["max_mc_lower"], lower[index])
                assert not receipt["model_risk_certificate"]
                assert receipt["second_check"] == "identical_unchanged_belief_cached;no_new_evidence_or_round"
                break
            assert lower[index] > 0 and receipt["integration_only"]
            equal(receipt["mc_lower"], lower[index]); equal(receipt["cap"], caps[index])
        elif policy == "joint_boundary":
            index = schedule[len(purchased)]
        else:
            directions = post[:n, n+np.array(available)].T/np.sqrt(np.diag(post)[n+np.array(available)])[:, None]
            samples = mean[None, None, :n]+normals_kg[None, :, None]*directions[:, None, :]
            gains = np.sort(samples, axis=2)[:, :, -5:].sum(2).mean(1)-mean[top(mean[:n])].sum()
            index = max(zip(gains, available), key=lambda pair: (pair[0], -pair[1]))[1]
            equal(receipt["predicted_A"], mean[n+index])
            equal(receipt["variance_A"], post[n+index, n+index])
            equal(receipt["innovation_z"], (y_a[index]-mean[n+index])/np.sqrt(post[n+index, n+index]))
        assert receipt["purchased_A"] == index and receipt["step"] == len(purchased)
        assert receipt["cumulative_A_cost"] == len(purchased)+1
        equal(receipt["observed_A"], y_a[index])
        purchased.append(index); values.append(y_a[index])
        mean, post = condition(initial, covariance, purchased, values)
        if policy == "shadow_protected_evsi":
            gate = protection(mean[:n], post[:n, :n], selected)
            observed = receipt["update_gate"]
            for field in ("selected", "proposal", "incoming", "outgoing", "accepted", "model_only"):
                assert observed[field] == gate[field]
            for actual, expected in zip(observed["pair_probabilities"], gate["pair_probabilities"]):
                assert actual["incoming"] == expected["incoming"] and actual["outgoing"] == expected["outgoing"]
                equal(actual["probability"], expected["probability"])
            selected = gate["selected"]
        else:
            selected = top(mean[:n])
    mean, post = condition(initial, covariance, purchased, values)
    assert row["purchased_A"] == purchased and len(set(purchased)) == len(purchased) <= 8
    if not policy.startswith("shadow"):
        assert len(purchased) == 8
    assert row["history"][-1] == dict(committed_B=selected, cost_after_five_B=len(purchased)+5)
    return selected, mean[:n], np.diag(post)[:n]


def main():
    started = time.perf_counter()
    vf = json.loads((HERE/"VERIFY_FREEZE.json").read_text())
    assert sha(Path(__file__)) == vf["verifier_sha256"] and sha(HERE/"FREEZE.json") == vf["trial_freeze_sha256"]
    freeze = json.loads((HERE/"FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        assert sha(ROOT/name) == expected, name
    checks = ["Separately frozen verifier and all13registered source/input hashes intact"]
    arrays, public, private = (dict(np.load(PACKET/name)) for name in ("training_arrays.npz", "public_prior.npz", "evaluator_private.npz"))
    manifest = json.loads((PACKET/"PACKET_MANIFEST.json").read_text())
    models, priors = dict(np.load(OUT/"MODELS.npz")), dict(np.load(OUT/"PRIORS.npz"))
    qualifications = json.loads((OUT/"QUALIFICATION.json").read_text())
    results = json.loads((OUT/"RESULTS.json").read_text())
    assert len(qualifications) == 50 and len(priors) == 48 and len(models) == 240 and len(results) == 336
    assert [q["context"] for q in qualifications if not q["evaluable"]] == ["ref31", "ref34"]
    targets = calibration(arrays, list(range(45)))
    for q in qualifications:
        context = q["context"]
        if not q["evaluable"]:
            i = int(context[3:]); assert not (arrays["availability_A"][i] & arrays["availability_B"][i]).all()
            assert q["A_count"] == int(arrays["availability_A"][i].sum()) and q["B_count"] == int(arrays["availability_B"][i].sum())
            continue
        if context.startswith("ref"):
            held = int(context[3:]); train = [i for i in range(45) if i != held]
            equal(priors[context], prior(arrays, train, held)); rebuilt, cells = calibration(arrays, train)
        else:
            train = list(range(45)); np.testing.assert_array_equal(priors[context], public[context+"__M2"])
            rebuilt, cells = targets
        assert q["train"] == train and q["residual_cells"] == cells and not q["independent_confirmation"]
        for name, value in rebuilt.items():
            equal(models[context+"__"+name], value)
        assert np.linalg.eigvalsh(rebuilt["joint"]).min() > 0
    checks.append("All48fixedM2priors/240modelarrays independently reconstructed with outerandinnercontext exclusions;43complete references only")
    print("Independent model arithmetic passed", flush=True)
    for number, row in enumerate(results):
        context = row["context"]
        if context.startswith("ref"):
            i = int(context[3:]); y_a, y_b = arrays["train_A"][i], arrays["train_B"][i]
        else:
            y_a, y_b = private[context+"__A"], private[context+"__B"]
        fitted = {name: models[context+"__"+name] for name in ("common", "joint", "offset")}
        selected, final_mean, final_variance = independently_replay(row, priors[context], fitted, y_a)
        assert row["selected"] == selected and row["cost"] == 5+len(row["purchased_A"]) <= 13
        equal(row["posterior_mean_B"], final_mean); equal(row["posterior_variance_B"], final_variance)
        initial = top(priors[context]); incoming = sorted(set(selected)-set(initial)); outgoing = sorted(set(initial)-set(selected))
        assert row["swapped_in"] == incoming and row["swapped_out"] == outgoing
        pairs = list(zip(sorted(incoming, key=lambda i: (-final_mean[i], i)), sorted(outgoing, key=lambda i: (final_mean[i], i))))
        assert [(p["in"], p["out"]) for p in row["replacement_pairs"]] == pairs
        for replacement in row["replacement_pairs"]:
            equal(replacement["B_delta"], y_b[replacement["in"]]-y_b[replacement["out"]])
        assert row["harmful_replacements"] == sum(y_b[i]-y_b[j] < -1e-12 for i, j in pairs)
        equal(row["terminal_B"], y_b[selected].sum()); equal(row["initial_B"], y_b[initial].sum())
        equal(row["delta_vs_no_screen"], y_b[selected].sum()-y_b[initial].sum())
        equal(row["top5_regret"], y_b[top(y_b)].sum()-y_b[selected].sum())
        equal(sum(v["B_delta"] for v in row["replacement_pairs"]), row["delta_vs_no_screen"])
        if number % 49 == 48:
            print(f"Independent policies passed {number+1}/336", flush=True)
    checks.append("All336records independently reconstructed: batchposteriors,KG/boundary choices,512drawscalarEVSIcaps/Hoeffdingbounds,protectedpairs,uniquereplacements,andactualcosts")
    from research.decision_value import validation as study
    from research.decision_value import utility as worker
    # Compare sample-level scalar arithmetic with the vectorized implementation,
    # including a nonoptimal incumbent and both gate states.
    fixture_context = next(iter(priors))
    mean = np.r_[priors[fixture_context], priors[fixture_context]+models[fixture_context+"__offset"]]
    covariance = models[fixture_context+"__joint"]
    samples = np.random.default_rng(20261011).standard_normal(512)
    for incumbent in (top(mean[:146]), [0, 1, 2, 3, 4]):
        for gated in (False, True):
            raw, caps = worker.expected_gains(mean, covariance, incumbent, samples, gated)
            estimates = worker.estimate(mean, covariance, incumbent, samples, gated)
            for index in (0, 5, 49, 72, 123, 145):
                scalar, cap, lower = candidate_gain(mean, covariance, incumbent, samples, index, gated)
                equal(raw[index], scalar); equal(caps[index], cap); equal(estimates["mc_lower"][index], lower)
    checks.append("24queryfixture/sample comparisons verify scalarversusvectorizedpairedEVSIandnominal25x8protection,includingnonoptimalincumbent")
    old = json.loads((ROOT/"outputs/paper_01286/state_readout_repair/RESULTS.json").read_text())
    for row in results:
        if row["scope"] == "exposed_targets" and row["policy"] == "common_kg":
            earlier = next(r for r in old if r["context"] == row["context"] and r["arm"] == "M2")
            assert row["selected"] == earlier["kg"]["selected"]
            assert row["purchased_A"] == [h["purchased_A"] for h in earlier["kg"]["history"][:-1]]
            equal(row["terminal_B"], earlier["kg"]["terminal_B"])
    checks.append("All5oldtargetKGpriors/purchases/choices/terminaloutcomes unchanged;strictLOOcomparators refit separately")
    for row in results:
        if row["scope"] != "exposed_targets":
            continue
        context, accesses = row["context"], []
        fitted = {name: models[context+"__"+name] for name in ("common", "joint", "offset")}
        def paid_only(index):
            assert len(accesses) < len(row["purchased_A"]) and index == row["purchased_A"][len(accesses)]
            accesses.append(index); return float(private[context+"__A"][index])
        repeated = study.run_policy(priors[context], fitted, paid_only, row["policy"])
        assert accesses == row["purchased_A"] and repeated["selected"] == row["selected"] and repeated["history"] == row["history"]
    checks.append("All35exposedtargetpolicies accessonlyauthorizedpurchasedA;no-screen/certified refusals neverreadA")
    poisoned = {k: np.full_like(v, 1e6) if k.endswith("__B") else v.copy() for k, v in private.items()}
    target_q = [q for q in qualifications if q["evaluable"] and not q["context"].startswith("ref")]
    with contextlib.redirect_stdout(io.StringIO()):
        changed = study.evaluate(arrays, poisoned, models, priors, target_q)
    originals = [r for r in results if r["scope"] == "exposed_targets"]
    for original, poison in zip(originals, changed):
        for field in ("selected", "purchased_A", "history", "posterior_mean_B", "posterior_variance_B", "cost"):
            assert original[field] == poison[field]
    held, train = 0, list(range(1, 45))
    poisoned_arrays = {k: v.copy() for k, v in arrays.items()}
    for key in ("train_A", "train_B", "precision_B", "state_B", "basal"):
        poisoned_arrays[key][held] = 1e6
    fitting, cells = study.model(poisoned_arrays, train)
    assert cells == next(q for q in qualifications if q["context"] == "ref0")["residual_cells"]
    for name, value in fitting.items():
        np.testing.assert_array_equal(value, models["ref0__"+name])
    poisoned_labels = {k: v.copy() for k, v in arrays.items()}
    for key in ("train_A", "train_B", "precision_B"):
        poisoned_labels[key][held] = 1e6
    m, d, _, _ = study.previous.readout.references(poisoned_labels, train, held)
    np.testing.assert_array_equal(m+.5*d, priors["ref0"])
    checks.append("AlltargetBpoison leaves35policy decisions unchanged;actualref0fitwithheldA/B/precision/STATE/basalpoisonexactlyunchanged")
    print("Isolation checks passed; complete fresh rerun starting", flush=True)
    with tempfile.TemporaryDirectory(prefix="decision_value_exact_repeat_") as temporary:
        fresh = Path(temporary)/"fresh"
        with contextlib.redirect_stdout(io.StringIO()):
            study.main(PACKET, fresh)
        for name in ("QUALIFICATION.json", "RESULTS.json"):
            assert json.loads((fresh/name).read_text()) == json.loads((OUT/name).read_text()), name
        for name in ("MODELS.npz", "PRIORS.npz"):
            with np.load(fresh/name) as repeated, np.load(OUT/name) as saved:
                assert set(repeated.files) == set(saved.files)
                for key in saved.files:
                    np.testing.assert_array_equal(repeated[key], saved[key])
        repeated_summary, saved_summary = json.loads((fresh/"SUMMARY.json").read_text()), json.loads((OUT/"SUMMARY.json").read_text())
        repeated_summary.pop("seconds"); saved_summary.pop("seconds")
        assert repeated_summary == saved_summary
    checks.append("Fresh complete run bit-for-bit reproduces allscientificarrays/JSON,excludingelapsedtime")
    # A descriptive power diagnosis uses only saved models and the registered
    # first-step random draws; it selects no new policy or parameter.
    power = []
    samples = np.random.default_rng(20261009).standard_normal(512)
    factor = np.sqrt(np.log(146*8/.05)/(2*512))
    for context, p in priors.items():
        mean = np.r_[p, p+models[context+"__offset"]]
        for gated in (False, True):
            raw, caps = worker.expected_gains(mean, models[context+"__joint"], top(p), samples, gated)
            gross, clipped = raw.mean(1), np.minimum(raw, caps[:, None]).mean(1)
            radius = caps*factor
            lower = clipped-radius
            ratio = np.divide(clipped, caps, out=np.zeros_like(caps), where=caps > 0)
            best_lower, best_gross, best_ratio = int(np.argmax(lower)), int(np.argmax(gross)), int(np.argmax(ratio))
            r = float(ratio[best_ratio])
            indicative_n = int(np.floor(np.log(146*8/.05)/(2*r*r))+1) if clipped[best_ratio] > 1e-12 else None
            power.append(dict(context=context, scope="reference" if context.startswith("ref") else "exposed_targets",
                              protected=gated, sample_count=512, MC_radius_per_cap=float(factor),
                              diagnostic_numerical_tolerance=1e-12,
                              positive_sample_gross_candidates=int((gross > 1e-12).sum()),
                              positive_clipped_sample_candidates=int((clipped > 1e-12).sum()),
                              positive_MC_lower_candidates=int((lower > 0).sum()),
                              best_lower_query=best_lower, best_MC_lower=float(lower[best_lower]),
                              max_gross_query=best_gross, max_sample_gross=float(gross[best_gross]),
                              radius_at_max_gross=float(radius[best_gross]), cap_at_max_gross=float(caps[best_gross]),
                              best_signal_per_cap_query=best_ratio, best_clipped_sample_per_cap=r,
                              indicative_minimum_N_if_current_sample_ratio_were_fixed=indicative_n))
    power_receipt = dict(post_hoc=True, no_policy_or_parameter_selection=True, rows=power,
                         interpretation="Initialdraw/model-onlydiagnostic;positivegrosssamplesandnegativeMCboundscan coexist. IndicativeNusesa512sampleestimatedratio,nottrueexpectationandnotanexecutedthresholdchange. ZeroMonteCarlogatedgainisnotproofofzeroGaussianmodelinformation.",
                         inputs_sha256={name:sha(OUT/name) for name in ("MODELS.npz", "PRIORS.npz")})
    with (OUT/"MC_POWER_DIAGNOSTIC.json").open("x", encoding="utf-8") as stream:
        json.dump(power_receipt, stream, indent=2, allow_nan=False); stream.write("\n")
    checks.append("Initialmodel-onlyintegrationpowerdiagnosisloggedposthocwithoutnewoutcomes,policiesorthresholdchanges")
    receipt = dict(status="PASS", checks=checks, check_groups=len(checks), reconstructed_records=len(results),
                   verifier_sha256=sha(Path(__file__)), seconds=time.perf_counter()-started,
                   MC_scope="HoeffdingboundscontrolonlyintegrationoffixedfittedGaussianmodel;clippedgainexpectationislowerthanmodelEVSI;notmodel-riskcertificate",
                   limits="43completeLOOreferencesoverlapSTATEpretraining;fiveexposedtargets;RNAutilityhasnounitcost/failure-latencycontractorfunctionalbridge;all-abstentionisnotnewdecisionvalue")
    with (OUT/"VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
