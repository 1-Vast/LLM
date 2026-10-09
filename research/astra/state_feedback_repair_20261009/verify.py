"""Independent crossfit arithmetic, batch conditioning and complete repeat."""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
OUT = ROOT / "outputs/paper_01286/state_feedback_repair"
STRENGTHS = (None, 0., 1., 10., 100., 1000.)
MEANS = ("M0", "M2", "drug_gain")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=1e-11, atol=1e-12)


def top(values):
    return sorted(range(len(values)), key=lambda i: (-values[i], i))[:5]


class Arithmetic:
    """Vectorized leave-context-out sums; no worker fitting imports."""
    def __init__(self, arrays, manifest):
        self.a = arrays
        drugs = [ast.literal_eval(v)[0][0] for v in manifest["labels"]]
        names = sorted(set(drugs))
        self.groups = np.array([names.index(d) for d in drugs])
        self.cache = {}

    def reference(self, train, held):
        a = self.a
        keep = [i for i in train if i != held]
        w = a["precision_B"][keep] * a["availability_B"][keep]
        mean = (np.where(a["availability_B"][keep], a["train_B"][keep], 0.) * w).sum(0) / w.sum(0)
        supported = a["state_available_B"][keep]
        centre = np.where(supported, a["state_B"][keep], 0.).sum(0) / supported.sum(0)
        deviation = np.where(a["state_available_B"][held], a["state_B"][held] - centre, 0.)
        valid = a["availability_A"][held] & a["availability_B"][held] & a["state_available_B"][held]
        return mean, deviation, valid

    def statistics(self, train):
        a = self.a
        w = a["precision_B"][train] * a["availability_B"][train]
        weighted = np.where(a["availability_B"][train], a["train_B"][train], 0.) * w
        means = (weighted.sum(0)[None] - weighted) / (w.sum(0)[None] - w)
        supported = a["state_available_B"][train]
        states = np.where(supported, a["state_B"][train], 0.)
        centres = (states.sum(0)[None] - states) / (supported.sum(0)[None] - supported)
        x = np.where(supported, a["state_B"][train] - centres, 0.)
        valid = a["availability_A"][train] & a["availability_B"][train] & supported
        numerator = np.where(valid, x * (a["train_B"][train] - means), 0.).sum(0)
        denominator = np.where(valid, x*x, 0.).sum(0)
        scale = max(float(denominator.sum() / (len(train)*len(self.groups))), 1e-12)
        return numerator, denominator, scale

    def coefficients(self, statistics, strength):
        if strength is None:
            return np.full(len(self.groups), .5)
        numerator, denominator, scale = statistics
        penalty = strength * scale
        output = np.full(len(self.groups), .5)
        for group in np.unique(self.groups):
            ix = self.groups == group
            n, d = numerator[ix].sum(), denominator[ix].sum()
            output[ix] = np.clip((n+.5*penalty)/(d+penalty) if d+penalty > 0 else .5, 0., 1.5)
        return output

    def fit(self, train, arm):
        key = tuple(train), arm
        if key in self.cache:
            return self.cache[key]
        if arm != "drug_gain":
            value = np.full(len(self.groups), .5), dict(strength=None, losses=[])
        else:
            inner = []
            for held in train:
                keep = [i for i in train if i != held]
                mean, deviation, valid = self.reference(keep, held)
                inner.append((self.statistics(keep), mean, deviation, valid, self.a["train_B"][held]))
            losses = []
            for strength in STRENGTHS:
                errors = [np.mean((mean[valid]+self.coefficients(stats, strength)[valid]*dev[valid]-y[valid])**2)
                          for stats, mean, dev, valid, y in inner]
                losses.append(dict(strength=strength, mean_cell_mse=float(np.mean(errors))))
            strength = min(enumerate(losses), key=lambda item: (item[1]["mean_cell_mse"], item[0]))[1]["strength"]
            value = self.coefficients(self.statistics(train), strength), dict(strength=strength, losses=losses)
        self.cache[key] = value
        return value

    def common(self, train):
        a = self.a
        valid = (a["availability_A"] & a["availability_B"])[train]
        counts = valid.sum(0)
        b = a["train_B"][train]
        centre = np.where(valid, b, 0.).sum(0) / counts
        filled = np.where(valid, b, centre)
        centered = filled-filled.mean(0)
        cov = centered.T@centered/(len(train)-1)
        cov = .5*cov+.5*np.diag(np.diag(cov))+np.eye(len(centre))*1e-12
        differences = a["train_A"][train]-b
        offset = np.where(valid, differences, 0.).sum(0)/counts
        noise = np.maximum(np.where(valid, (differences-offset)**2, 0.).sum(0)/(counts-1), 1e-12)
        joint = np.block([[cov, cov], [cov, cov+np.diag(noise)]])
        return joint, offset

    def build(self, public, manifest):
        models, predictions, choices = {}, {}, {}
        a = self.a
        for fold in (0, 1, 2, "targets"):
            train = [i for i in range(45) if fold == "targets" or i % 3 != fold]
            scope = "targets" if fold == "targets" else f"fold{fold}"
            common, offset = self.common(train)
            for arm in MEANS:
                prefix = scope+"__"+arm
                gains, choice = self.fit(train, arm)
                errors_b, errors_a, cells, cross_choices = [], [], [], []
                for cell in train:
                    if not (a["availability_A"][cell] & a["availability_B"][cell]).all():
                        continue
                    keep = [i for i in train if i != cell]
                    cross_gains, cross_choice = self.fit(keep, arm)
                    mean, dev, _ = self.reference(keep, cell)
                    p = mean if arm == "M0" else mean+cross_gains*dev
                    _, cross_offset = self.common(keep)
                    errors_b.append(a["train_B"][cell]-p)
                    errors_a.append(a["train_A"][cell]-p-cross_offset)
                    cells.append(cell)
                    cross_choices.append(dict(cell=cell, strength=cross_choice["strength"]))
                eb, ea = np.array(errors_b), np.array(errors_a)
                errors = np.concatenate((eb, ea), axis=1)
                moment = errors.T@errors/len(cells)
                joint = .5*moment+.5*np.diag(np.diag(moment))+np.eye(len(moment))*1e-12
                for name, value in (("common", common), ("joint", joint), ("offset", offset),
                                    ("error_B", eb), ("error_A", ea), ("gains", gains)):
                    models[prefix+"__"+name] = value
                choices[prefix] = dict(**choice, train=train, residual_cells=cells,
                                       crossfit_choices=cross_choices, covariance_contexts=len(cells))
                if fold == "targets":
                    for context in manifest["contexts"]:
                        key = context.replace("-", "_").replace("/", "_")
                        mean = public[key+"__M0"]
                        predictions[key+"__"+arm] = mean if arm == "M0" else mean+gains*2*(public[key+"__M2"]-mean)
                else:
                    for held in range(45):
                        if held % 3 == fold:
                            mean, dev, _ = self.reference(train, held)
                            predictions[f"ref{held}__"+arm] = mean if arm == "M0" else mean+gains*dev
        return models, predictions, choices


def batch_condition(initial, covariance, purchased, values):
    if not purchased:
        return initial.copy(), covariance.copy()
    coordinates = len(initial)//2+np.array(purchased)
    cross = covariance[:, coordinates]
    marginal = covariance[np.ix_(coordinates, coordinates)]
    innovation = np.array(values)-initial[coordinates]
    mean = initial+cross@np.linalg.solve(marginal, innovation)
    posterior = covariance-cross@np.linalg.solve(marginal, cross.T)
    return mean, posterior


def verify_record(row, mean_b, offset, covariance, y_a, y_b, common_schedule):
    n = len(mean_b)
    initial = np.concatenate((mean_b, mean_b+offset))
    purchased, values = [], []
    normals = np.random.default_rng(20261008).standard_normal(64)
    if row["policy"] == "joint_shared":
        schedule = common_schedule
    elif row["policy"] == "joint_boundary":
        ordered = sorted(range(n), key=lambda i: (-mean_b[i], i))
        midpoint = .5*(mean_b[ordered[4]]+mean_b[ordered[5]])
        schedule = sorted(range(n), key=lambda i: (abs(mean_b[i]-midpoint), i))[:8]
    else:
        schedule = None
    for step, receipt in enumerate(row["history"][:-1]):
        mean, post = batch_condition(initial, covariance, purchased, values)
        if schedule is None:
            available = [i for i in range(n) if i not in purchased]
            directions = post[:n, n+np.array(available)].T/np.sqrt(np.maximum(np.diag(post)[n+np.array(available)], 0.))[:, None]
            draws = mean[None, None, :n]+normals[None, :, None]*directions[:, None, :]
            gains = np.sort(draws, axis=2)[:, :, -5:].sum(2).mean(1)-sum(mean[i] for i in top(mean[:n]))
            index = max(zip(gains, available), key=lambda pair: (pair[0], -pair[1]))[1]
        else:
            index = schedule[step]
        assert receipt["purchased_A"] == index, (row["context"], row["mean"], row["policy"], step, index)
        assert receipt["step"] == step and receipt["cumulative_A_cost"] == step+1
        equal(receipt["predicted_A"], mean[n+index])
        equal(receipt["variance_A"], post[n+index, n+index])
        equal(receipt["observed_A"], y_a[index])
        equal(receipt["innovation_z"], (y_a[index]-mean[n+index])/np.sqrt(post[n+index, n+index]))
        purchased.append(index)
        values.append(y_a[index])
    mean, post = batch_condition(initial, covariance, purchased, values)
    selected, initial_selected = top(mean[:n]), top(mean_b)
    assert len(purchased) == len(set(purchased)) == 8 and row["purchased_A"] == purchased
    assert selected == row["selected"] and initial_selected == row["initial_selected"]
    assert row["cost"] == 13 and row["history"][-1] == dict(committed_B=selected, cost_after_five_B=13)
    equal(row["posterior_mean_B"], mean[:n])
    equal(row["posterior_variance_B"], np.diag(post)[:n])
    incoming, outgoing = sorted(set(selected)-set(initial_selected)), sorted(set(initial_selected)-set(selected))
    assert row["swapped_in"] == incoming and row["swapped_out"] == outgoing
    for name, value in (("initial_B", y_b[initial_selected].sum()), ("terminal_B", y_b[selected].sum()),
                        ("static_delta_B", y_b[selected].sum()-y_b[initial_selected].sum()),
                        ("swap_in_B", y_b[incoming].sum()), ("swap_out_B", y_b[outgoing].sum()),
                        ("initial_mse", np.mean((mean_b-y_b)**2)), ("posterior_mse", np.mean((mean[:n]-y_b)**2))):
        equal(row[name], value)


def main():
    started = time.perf_counter()
    verifier_freeze = json.loads((HERE/"VERIFY_FREEZE.json").read_text())
    assert verifier_freeze["verifier_sha256"] == sha(Path(__file__))
    assert verifier_freeze["trial_freeze_sha256"] == sha(HERE/"FREEZE.json")
    freeze = json.loads((HERE/"FREEZE.json").read_text())
    for path, expected in freeze["inputs"].items():
        assert sha(ROOT/path) == expected, path
    checks = ["Verifier separately frozen; all10registered inputs unchanged"]
    arrays, public, private = (dict(np.load(PACKET/name)) for name in ("training_arrays.npz", "public_prior.npz", "evaluator_private.npz"))
    manifest = json.loads((PACKET/"PACKET_MANIFEST.json").read_text())
    models, predictions = dict(np.load(OUT/"MODELS.npz")), dict(np.load(OUT/"PREDICTIONS.npz"))
    choices = json.loads((OUT/"MODEL_CHOICES.json").read_text())
    results = json.loads((OUT/"RESULTS.json").read_text())
    independent = Arithmetic(arrays, manifest)
    rebuilt_models, rebuilt_predictions, rebuilt_choices = independent.build(public, manifest)
    assert set(models) == set(rebuilt_models) and set(predictions) == set(rebuilt_predictions)
    for key, value in models.items():
        equal(value, rebuilt_models[key])
        if key.endswith(("__joint", "__common")):
            assert np.linalg.eigvalsh(value).min() >= -1e-12
    for key, value in predictions.items():
        equal(value, rebuilt_predictions[key])
    for key, value in choices.items():
        expected = rebuilt_choices[key]
        for field in ("strength", "train", "residual_cells", "crossfit_choices", "covariance_contexts"):
            assert value[field] == expected[field], (key, field)
        assert len(value["losses"]) == len(expected["losses"])
        for observed, desired in zip(value["losses"], expected["losses"]):
            assert observed["strength"] == desired["strength"]
            equal(observed["mean_cell_mse"], desired["mean_cell_mse"])
    checks.append("All12final and allcrossfit gain choices,72model arrays and150forecasts independently reconstructed")
    assert len(results) == 528
    incomplete = np.flatnonzero(~(arrays["availability_A"] & arrays["availability_B"]).all(1)).tolist()
    assert incomplete == [31, 34] and not any(r["context"] in ("ref31", "ref34") for r in results)
    common = {(r["context"], r["mean"]): r["purchased_A"] for r in results if r["policy"] == "common_kg"}
    for row in results:
        scope = "targets" if row["fold"] == "targets" else f"fold{row['fold']}"
        context, arm = row["context"], row["mean"]
        prefix = scope+"__"+arm
        if context.startswith("ref"):
            index = int(context[3:]); y_a, y_b = arrays["train_A"][index], arrays["train_B"][index]
        else:
            y_a, y_b = private[context+"__A"], private[context+"__B"]
        kind = "common" if row["policy"] == "common_kg" else "joint"
        verify_record(row, predictions[context+"__"+arm], models[prefix+"__offset"], models[prefix+"__"+kind], y_a, y_b, common[(context, arm)])
    checks.append("All528acquisition histories, closed-form joint posteriors,5Bchoices,utilities and13unit charges rebuilt")
    checks.append("Allshared policies receive identical8Aindices/values; incomplete contexts never scored or included in joint moments")
    old = json.loads((ROOT/"outputs/paper_01286/state_readout_repair/RESULTS.json").read_text())
    for row in results:
        if row["fold"] == "targets" and row["policy"] == "common_kg":
            earlier = next(r for r in old if r["context"] == row["context"] and r["arm"] == row["mean"])
            assert row["selected"] == earlier["kg"]["selected"]
            assert row["purchased_A"] == [h["purchased_A"] for h in earlier["kg"]["history"][:-1]]
            equal(row["terminal_B"], earlier["kg"]["terminal_B"])
    checks.append("All15old target comparators reproduce predecessor selections,purchases andterminal outcomes")
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("frozen_feedback_study_verifier", HERE/"run.py")
    study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    # Getter can release only the next already-recorded acquisition; every other
    # A coordinate is unavailable. No B vector is part of the policy interface.
    for row in results:
        if row["fold"] != "targets":
            continue
        prefix = "targets__"+row["mean"]
        values, sequence, accesses = private[row["context"]+"__A"], row["purchased_A"], []
        def paid_only(index):
            assert len(accesses) < 8 and index == sequence[len(accesses)]
            accesses.append(index)
            return float(values[index])
        kind = "common" if row["policy"] == "common_kg" else "joint"
        schedule = common[(row["context"], row["mean"])] if row["policy"] == "joint_shared" else None
        policy = "boundary" if row["policy"] == "joint_boundary" else "kg"
        repeated = study.replay(predictions[row["context"]+"__"+row["mean"]], models[prefix+"__offset"], models[prefix+"__"+kind], paid_only, policy=policy, schedule=schedule)
        assert repeated["selected"] == row["selected"] and accesses == sequence
    poisoned_private = {k: (np.full_like(v, 1e6) if k.endswith("__B") else v.copy()) for k, v in private.items()}
    with contextlib.redirect_stdout(io.StringIO()):
        poisoned = study.evaluate(arrays, poisoned_private, manifest, models, predictions)
    for original, changed in zip(results, poisoned):
        for field in ("selected", "history", "purchased_A", "posterior_mean_B", "posterior_variance_B"):
            assert original[field] == changed[field]
    checks.append("All55target policies access only8authorized A scalars; poisoning alltarget B cannot alter any528decisions/posteriors")
    poisoned_arrays = {k: v.copy() for k, v in arrays.items()}
    held = [i for i in range(45) if i % 3 == 0]
    for key in ("train_A", "train_B", "precision_B", "state_B", "state_B_permuted", "basal"):
        poisoned_arrays[key][held] = 1e6
    poisoned_arithmetic = Arithmetic(poisoned_arrays, manifest)
    train = [i for i in range(45) if i % 3 != 0]
    original_common, original_offset = independent.common(train)
    poison_common, poison_offset = poisoned_arithmetic.common(train)
    equal(original_common, poison_common); equal(original_offset, poison_offset)
    for arm in MEANS:
        original_gain, original_choice = independent.fit(train, arm)
        poison_gain, poison_choice = poisoned_arithmetic.fit(train, arm)
        equal(original_gain, poison_gain); assert original_choice == poison_choice
        for cell in choices["fold0__"+arm]["residual_cells"]:
            keep = [i for i in train if i != cell]
            og, oc = independent.fit(keep, arm); pg, pc = poisoned_arithmetic.fit(keep, arm)
            equal(og, pg); assert oc == pc
            om, od, _ = independent.reference(keep, cell); pm, pd, _ = poisoned_arithmetic.reference(keep, cell)
            equal(om, pm); equal(od, pd)
            _, oo = independent.common(keep); _, po = poisoned_arithmetic.common(keep)
            equal(oo, po)
    checks.append("Poisoned complete outerfold A/B,precision,STATE/basal values cannot enter fitting,innerchoices orcrossfit offsets")
    # Execute the actual frozen fitting body for one outer fold. The harness
    # narrows its outer iterator only; fit/centering/selection logic is unchanged.
    parsed = ast.parse((HERE/"run.py").read_text())
    fitting_body = next(node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name == "build_models")
    outer_loop = next(node for node in fitting_body.body if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "fold")
    outer_loop.iter = ast.copy_location(ast.List(elts=[ast.Constant(value=0)], ctx=ast.Load()), outer_loop.iter)
    single_fold = ast.fix_missing_locations(ast.Module(body=[fitting_body], type_ignores=[]))
    namespace = study.__dict__.copy()
    exec(compile(single_fold, str(HERE/"run.py"), "exec"), namespace)
    with contextlib.redirect_stdout(io.StringIO()):
        poison_models, _, poison_choices = namespace["build_models"](poisoned_arrays, public, manifest)
    assert poison_choices == {key: value for key, value in choices.items() if key.startswith("fold0__")}
    for key, value in poison_models.items():
        np.testing.assert_array_equal(value, models[key])
    checks.append("Actual frozen fitting body rerun forouterfold0withhelddata poisoned; allchoices/modelarrays exactlyunchanged")
    original_out = study.OUT
    with tempfile.TemporaryDirectory(prefix="state_feedback_exact_repeat_") as temporary:
        study.OUT = Path(temporary)/"fresh"
        with contextlib.redirect_stdout(io.StringIO()):
            study.main()
        for name in ("MODEL_CHOICES.json", "RESULTS.json"):
            assert json.loads((study.OUT/name).read_text()) == json.loads((original_out/name).read_text()), name
        for name in ("MODELS.npz", "PREDICTIONS.npz"):
            with np.load(study.OUT/name) as repeated, np.load(original_out/name) as saved:
                assert set(repeated.files) == set(saved.files)
                for key in saved.files:
                    np.testing.assert_array_equal(repeated[key], saved[key])
        repeated_summary = json.loads((study.OUT/"SUMMARY.json").read_text())
        saved_summary = json.loads((original_out/"SUMMARY.json").read_text())
        repeated_summary.pop("seconds"); saved_summary.pop("seconds")
        assert repeated_summary == saved_summary
    study.OUT = original_out
    checks.append("Fresh complete fitting/evaluation exactly reproduces allscientific JSON andarrays; elapsedtime ignored")
    summary = json.loads((OUT/"SUMMARY.json").read_text())
    primary = next(r for r in summary["comparisons"] if r["mean"] == "M2" and r["policy"] == "joint_kg" and r["scope"] == "reference")
    receipt = dict(status="PASS", checks=checks, check_groups=len(checks),
                   reconstructed_records=len(results), primary_reference=primary,
                   verifier_sha256=sha(Path(__file__)), seconds=time.perf_counter()-started,
                   limits="Arithmetic/isolation verification only; references overlap STATE pretraining;5targets exposed; source A/B not independently started cultures; no phenotype orLLM-effect confirmation")
    with (OUT/"VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
