"""External-validation firewall: digests, manifests, sealed policy views and the outcome vault.

File summary
- Path: research/external_validation/firewall.py
- Purpose: make it mechanically impossible for a policy to read a hidden outcome, for fitting code
  to read an external test once it is sealed, and for a frozen component to change unnoticed.
- Core points:
  - `seal` gives the arms a copy of the data in which every compound of the held-out fold has no
    profile, no QC fields, no detection flag and no mechanism annotation. The executor keeps the
    real data and reveals only what an arm buys, through `Visible`.
  - `validate` checks the three manifest schemas (a JSON-Schema subset; `jsonschema` is not in the
    environment).
  - `boundary_report` measures compound, group and batch overlap across a boundary; the external
    boundary must be disjoint on all three, the internal folds on the first two.
  - `Vault` holds an external study's outcomes. It opens once, only under a verified freeze, and
    once open every function decorated with `fitting` refuses to run in that process.
  - `project_policy_input` is the typed policy boundary: only public evidence, legal actions,
    budgets, calibrated distributions and provenance can cross it; evaluator truth is rejected.
- Depends on: numpy, pandas, research/dynamic_world_model/common.py
"""
from __future__ import annotations

import copy
import functools
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from collections.abc import Mapping
from types import MappingProxyType

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMAS = HERE / "schemas"

ANNOTATION_COLUMNS = ("klass", "pathway_level_1", "pathway_level_2", "target", "hub_targets", "hub_moa",
                      "name", "multi_moa", "route")
CONDITION_MASKS = {"replicates": 0, "n_cells": 0, "n_cells_rep1": 0, "n_cells_rep2": 0, "n_wells": 0,
                   "n_plates": 0, "signatures": 0, "qc": False, "detected": False,
                   "cc_q75": np.nan, "signature_strength": np.nan}


class ExternalOutcomesRevealed(RuntimeError):
    """A fitting step was called after an external study's outcomes were revealed."""


class FreezeMismatch(RuntimeError):
    """A frozen file, dataset or manifest no longer matches its recorded digest."""


class ExternalStudyUnavailable(RuntimeError):
    """No external study is registered; the reason names the blocker."""


class PolicyInputViolation(ValueError):
    """The object crossing the policy boundary contains evaluator-only state."""


# The public type lives in ``src/maestro`` so production users and the research
# harness share one contract.  Import lazily in the projection function as the
# research modules are also used by standalone scripts before ``src`` is on
# ``sys.path``.
_HIDDEN_POLICY_FIELDS = frozenset({
    "truth", "hidden_truth", "ground_truth", "groundtruth", "heldout", "held_out",
    "klass", "mechanism", "annotation", "annotations", "mechanism_annotation",
    "mechanism_class", "mechanism_label", "evaluator", "future_outcome",
    "future_action_outcome", "outcome_truth", "truth_label", "heldout_profile",
    "data", "conditions", "shift", "compounds", "index", "outcomes",
})


def _forbidden_policy_fields(value, path: str = "$") -> list[str]:
    """Find evaluator-only keys in a user-supplied policy payload.

    Policy evidence may be a measurement result or an immutable summary, so
    this check intentionally inspects mapping keys only.  It never traverses
    arbitrary objects (which could invoke a model or a hidden data property).
    """

    problems = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            name = str(key).strip().lower()
            if name in _HIDDEN_POLICY_FIELDS:
                problems.append(f"{path}.{key}: evaluator-only field")
            if isinstance(nested, Mapping):
                problems.extend(_forbidden_policy_fields(nested, f"{path}.{key}"))
            elif isinstance(nested, (tuple, list)):
                for i, item in enumerate(nested):
                    problems.extend(_forbidden_policy_fields(item, f"{path}.{key}[{i}]"))
    elif isinstance(value, (tuple, list)):
        for i, item in enumerate(value):
            problems.extend(_forbidden_policy_fields(item, f"{path}[{i}]"))
    elif hasattr(value, "__dict__"):
        # Inspect instance storage only; never invoke arbitrary properties on
        # a model/result object supplied by a caller.
        for key, nested in vars(value).items():
            name = str(key).strip().lower()
            if name in _HIDDEN_POLICY_FIELDS:
                problems.append(f"{path}.{key}: evaluator-only field")
            if isinstance(nested, (Mapping, tuple, list)):
                problems.extend(_forbidden_policy_fields(nested, f"{path}.{key}"))
    return problems


def _freeze_policy_value(value):
    """Copy containers crossing the boundary so policy code receives read-only state."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_policy_value(nested) for key, nested in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_policy_value(item) for item in value)
    if isinstance(value, np.ndarray):
        copied = value.copy()
        copied.setflags(write=False)
        return copied
    return value


def project_policy_input(*, visible_evidence=(), legal_actions=(), budget: float,
                         calibrated_action_distributions=None, provenance=None):
    """Project public policy state into the typed :class:`PolicyInput`.

    This function has an intentionally explicit keyword-only signature.  A
    sealed context, raw ``Data`` object, held-out truth, and future outcomes
    cannot be passed accidentally because none is accepted by the API.  The
    mapping-key check catches the common case where a caller tries to smuggle
    one of those fields inside a hand-built evidence dictionary.
    """

    evidence_items = (visible_evidence,) if isinstance(visible_evidence, Mapping) else tuple(visible_evidence)
    problems = _forbidden_policy_fields(evidence_items)
    problems.extend(_forbidden_policy_fields(calibrated_action_distributions or {}, "$.calibrated"))
    problems.extend(_forbidden_policy_fields(provenance or {}, "$.provenance"))
    if problems:
        raise PolicyInputViolation("; ".join(problems))
    try:
        from maestro.handoff import PolicyInput, make_policy_input
    except ImportError as exc:  # pragma: no cover - only for malformed standalone imports
        raise RuntimeError("maestro.handoff is required for the policy firewall") from exc
    projected = make_policy_input(
        visible_evidence=tuple(_freeze_policy_value(item) for item in evidence_items),
        legal_actions=tuple(legal_actions),
        budget=budget,
        calibrated_action_distributions=calibrated_action_distributions or {},
        provenance=provenance or {},
    )
    if not isinstance(projected, PolicyInput):
        raise PolicyInputViolation("policy projection did not produce PolicyInput")
    return projected


def project_policy_view(view, *, legal_actions=(), budget: float,
                        calibrated_action_distributions=None, provenance=None):
    """Project only already-revealed evidence from a sealed view.

    ``view`` is deliberately duck-typed to keep this module independent of
    the dynamic-world-model dataclasses.  The function reads the executor's
    ``Visible.profiles`` map only; it does not inspect ``view.data`` or any
    annotations on the sealed context.
    """

    visible = getattr(view, "profiles", {})
    if not isinstance(visible, Mapping):
        raise PolicyInputViolation("visible evidence must be a mapping")
    evidence = tuple(
        {"action_key": tuple(key),
         # Visible.reveal already copies arrays; copy once more at the typed
         # boundary so a policy cannot mutate executor state through a view.
         "profile": np.asarray(profile, dtype=np.float64).copy() if profile is not None else None}
        for key, profile in sorted(visible.items(), key=lambda item: repr(item[0]))
    )
    return project_policy_input(
        visible_evidence=evidence,
        legal_actions=legal_actions,
        budget=budget,
        calibrated_action_distributions=calibrated_action_distributions,
        provenance=provenance,
    )


def policy_input_problems(value) -> list[str]:
    """Return contract violations for a value received by a policy."""

    try:
        from maestro.handoff import PolicyInput
    except ImportError:
        return ["maestro.handoff unavailable"]
    if not isinstance(value, PolicyInput):
        return ["expected maestro.handoff.PolicyInput"]
    problems = _forbidden_policy_fields(value.visible_evidence, "$.visible_evidence")
    problems.extend(_forbidden_policy_fields(value.calibrated_action_distributions, "$.calibrated"))
    problems.extend(_forbidden_policy_fields(value.provenance, "$.provenance"))
    # A projection is a closed value: raw data/evaluator handles must not be
    # attached after construction either.
    for field in ("data", "truth", "heldout", "klass", "outcomes", "evaluator"):
        if hasattr(value, field):
            problems.append(f"$.{field}: forbidden policy field")
    return problems


def assert_policy_input(value) -> None:
    problems = policy_input_problems(value)
    if problems:
        raise PolicyInputViolation("; ".join(problems))


# ------------------------------------------------------------------------------ digests
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_state(paths=()) -> dict:
    def run(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
        # Preserve the leading status-column space from ``git status``; using
        # ``strip`` would turn `` M path`` into ``M path`` and drop the first
        # character when the porcelain prefix is removed below.
        return result.stdout.rstrip("\r\n") if result.returncode == 0 else None

    status = run("status", "--porcelain", "--", *[str(Path(p).relative_to(ROOT).as_posix()) for p in paths]) or ""
    return {"commit": run("rev-parse", "HEAD"), "uncommitted_paths": sorted(line[3:] for line in status.splitlines())}


# ------------------------------------------------------------------------------ schema validation
_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _is_type(value, name: str) -> bool:
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def validate(instance, schema: dict, path: str = "$") -> list[str]:
    """The subset of JSON Schema the manifests use; returns every violation found."""
    problems = []
    kind = schema.get("type")
    if kind is not None:
        kinds = kind if isinstance(kind, list) else [kind]
        if not any(_is_type(instance, k) for k in kinds):
            return [f"{path}: expected {kind}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        problems.append(f"{path}: {instance!r} not in {schema['enum']}")
    if "const" in schema and instance != schema["const"]:
        problems.append(f"{path}: must equal {schema['const']!r}")
    if isinstance(instance, str) and "pattern" in schema:
        import re
        if not re.fullmatch(schema["pattern"], instance):
            problems.append(f"{path}: {instance!r} does not match {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool) and "minimum" in schema \
            and instance < schema["minimum"]:
        problems.append(f"{path}: {instance} < {schema['minimum']}")
    if isinstance(instance, dict):
        for name in schema.get("required", []):
            if name not in instance:
                problems.append(f"{path}: missing {name}")
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for name, value in instance.items():
            if name in properties:
                problems += validate(value, properties[name], f"{path}.{name}")
            elif extra is False:
                problems.append(f"{path}: unexpected {name}")
            elif isinstance(extra, dict):
                problems += validate(value, extra, f"{path}.{name}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            problems.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, value in enumerate(instance):
                problems += validate(value, schema["items"], f"{path}[{i}]")
    return problems


def schema(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def check_manifest(instance: dict, name: str) -> None:
    problems = validate(instance, schema(name))
    if problems:
        raise ValueError(f"{name} manifest invalid: " + "; ".join(problems[:10]))


# ------------------------------------------------------------------------------ boundaries
def boundary_report(train: dict, test: dict) -> dict:
    """Overlap of compound identities, scaffold/identity groups and batches across one boundary.

    ``train`` and ``test`` map "compounds", "groups" and "batches" to iterables of labels.
    """
    out = {}
    for field in ("compounds", "groups", "scaffolds", "batches"):
        a = {str(x) for x in train.get(field, ()) if x is not None and x == x}
        b = {str(x) for x in test.get(field, ()) if x is not None and x == x}
        shared = sorted(a & b)
        out[field] = {"train": len(a), "test": len(b), "shared": len(shared), "examples": shared[:5]}
    return out


def external_boundary_problems(report: dict) -> list[str]:
    return [f"{field}_cross_external_boundary" for field in ("compounds", "groups", "scaffolds", "batches")
            if report.get(field, {}).get("shared", 0)]


def internal_boundary_problems(report: dict) -> list[str]:
    return [f"{field}_cross_fold_boundary" for field in ("compounds", "groups") if report.get(field, {}).get("shared", 0)]


# ------------------------------------------------------------------------------ sealed policy view
def sealed_rows(data, heldout: set) -> list[int]:
    return sorted({row for members in data.index.values() for compound, row in members.items() if compound in heldout})


def seal_data(data, heldout: set):
    """A copy of `common.Data` with every held-out compound's measurements and annotations removed."""
    rows = sealed_rows(data, heldout)
    sealed = copy.copy(data)
    sealed.shift = data.shift.copy()
    sealed.shift[rows] = np.nan
    for name in ("rep1", "rep2"):
        array = getattr(data, name)
        if array.size:
            array = array.copy()
            array[rows] = np.nan
            setattr(sealed, name, array)
    sealed.agreement = data.agreement.astype(float).copy()
    sealed.agreement[rows] = np.nan
    conditions = data.conditions.copy()
    for column, value in CONDITION_MASKS.items():
        if column in conditions.columns:
            if isinstance(value, float) and np.isnan(value):
                conditions[column] = conditions[column].astype(float)
            conditions.loc[rows, column] = value
    sealed.conditions = conditions
    if len(getattr(data, "wells", ())) and "compound" in data.wells.columns and data.well_mean.size:
        mask = data.wells.compound.astype(str).str.strip().isin(heldout).to_numpy()
        sealed.well_mean = data.well_mean.copy()
        sealed.well_mean[mask] = np.nan
    compounds = data.compounds.copy()
    held = compounds.compound.isin(heldout)
    for column in ANNOTATION_COLUMNS:
        if column in compounds.columns:
            compounds[column] = compounds[column].astype(object)
            compounds.loc[held, column] = None
    sealed.compounds = compounds
    sealed.index = {key: {c: r for c, r in members.items() if c not in heldout} for key, members in data.index.items()}
    return sealed


class Visible:
    """What the executor has revealed in the current episode: executed readings and profiles only."""

    def __init__(self):
        self.profiles: dict = {}

    def reveal(self, key, profile) -> None:
        self.profiles[tuple(key)] = None if profile is None else np.asarray(profile, dtype=np.float64).copy()

    def profile(self, key):
        return self.profiles.get(tuple(key))


def seal(ctx, heldout: set, *, vc_factory=None):
    """The context an arm receives: sealed data, the same training tables, a fresh cache."""
    data = seal_data(ctx.data, heldout)
    detected = np.asarray(ctx.detected, dtype=bool).copy()
    detected[sealed_rows(ctx.data, heldout)] = False
    magnitude = vc_factory(data, detected) if vc_factory is not None else None
    sealed = replace(ctx, data=data, detected=detected, magnitude=magnitude, card_cache={}, extra={})
    sealed.extra["visible"] = Visible()
    sealed.extra["sealed_compounds"] = frozenset(heldout)
    return sealed


def sealed_view_problems(sealed, heldout: set) -> list[str]:
    """Independent check that no held-out measurement or annotation reached the policy view."""
    problems = []
    rows = [r for c, r in ((c, r) for m in sealed.data.index.values() for c, r in m.items()) if c in heldout]
    if rows:
        problems.append("heldout_compound_in_policy_index")
    comp = sealed.data.compounds
    held = comp[comp.compound.isin(heldout)]
    for column in ANNOTATION_COLUMNS:
        if column in held.columns and held[column].notna().any():
            problems.append(f"heldout_annotation_visible:{column}")
    for key, table in sealed.ft.tables.items():
        if heldout & set(table.names):
            problems.append(f"heldout_compound_in_reference_table:{key}")
    return problems


# ------------------------------------------------------------------------------ vault
_STATE = {"revealed": None}


def fitting(function):
    """Mark a step that fits, tunes, calibrates, retrieves or selects; it refuses once a vault is open."""

    @functools.wraps(function)
    def guarded(*args, **kwargs):
        if _STATE["revealed"] is not None:
            raise ExternalOutcomesRevealed(f"{function.__name__} refused: external study "
                                           f"{_STATE['revealed']} was revealed in this process")
        return function(*args, **kwargs)

    guarded.is_fitting_step = True
    return guarded


def verify_freeze(freeze: dict, root: Path = ROOT) -> list[str]:
    """Every frozen file must still hash to its recorded digest."""
    problems = []
    for relative, expected in freeze.get("sha256", {}).items():
        path = root / relative
        if not path.is_file():
            problems.append(f"missing:{relative}")
        elif sha256_file(path) != expected:
            problems.append(f"changed:{relative}")
    return problems


class Vault:
    """An external study's outcomes, sealed until a verified freeze opens them exactly once."""

    def __init__(self, study: str, outcomes, *, manifest_sha256: str):
        self.study, self._outcomes, self.manifest_sha256 = study, outcomes, manifest_sha256
        self.opened = False

    def open(self, freeze: dict, *, root: Path = ROOT, access_log: Path | None = None):
        if self.opened:
            raise RuntimeError("vault_already_opened")
        registered = freeze.get("external_study", {})
        if registered.get("manifest_sha256") != self.manifest_sha256:
            raise FreezeMismatch("external_manifest_not_in_freeze")
        problems = verify_freeze(freeze, root)
        if problems:
            raise FreezeMismatch("; ".join(problems))
        self.opened = True
        _STATE["revealed"] = self.study
        if access_log is not None:
            with Path(access_log).open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps({"study": self.study, "manifest_sha256": self.manifest_sha256,
                                         "freeze_protocol_sha256": freeze.get("sha256", {}).get(
                                             "research/external_validation/protocol.json")}) + "\n")
        return self._outcomes


def revealed() -> str | None:
    return _STATE["revealed"]


def _reset_for_tests() -> None:
    _STATE["revealed"] = None
