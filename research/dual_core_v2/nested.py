"""Nested fold contexts with recorded lineage: a model that has never seen the test fold or the calibration fold.

File summary
- Path: research/dual_core_v2/nested.py
- Purpose: repair block 7's calibration independence. In block 7, for test fold f, thresholds and
  Platt maps were fitted on the traces of every other fold g, and those traces came from models
  (`TV.load(dataset, tier, g)`) trained on all folds except g, fold f included. Fold f's references,
  labels and validator templates therefore shaped the calibration scores used to choose fold f's
  policy, and the calibration traces came from other models than the one tested on f. Disjoint row
  indices did not make the roles independent.
- Core points:
  - `load(dataset, tier, heldout)` builds the protocol-v2.1 fold context with every fold in `heldout`
    removed from every outcome-dependent step at once: reference tables, the hypothesis pool, the
    validator calibration (floor, margin), the world model's references and hyperparameters, and
    the transfer fits. It does so by giving the held-out folds' compounds one sentinel fold before
    `tasks_v21` runs, so the registered code path is unchanged.
  - `Lineage` records what a model was fitted on: the training compounds (with a SHA-256), the folds
    they came from, the excluded folds, the pool and the validator parameters.
    `check_independent(lineage, test_units)` raises if any test compound or unit reached a fit.
  - Designs (roles are fixed by `ROLES`, before any outcome is seen):
    - `split`: for test fold f, one model M(f, c) with c = f + 1 mod 5, trained on the other three
      folds, calibrated on fold c and tested on fold f. Calibration and test units are exchangeable
      given one frozen model-policy process: the design Learn-then-Test's guarantee needs.
    - `nested_crossfit`: for test fold f, calibration traces from M(f, g) on fold g for all g != f
      (four models, none trained on f); the policy is then applied to fold f by each M(f, g) and the
      four test estimates are averaged. More calibration units, but calibration pools four models, so
      the guarantee is approximate. It is reported as descriptive.
  - Every M(f, g) is trained on three folds, not four. That is the price of keeping f and the
    calibration fold out of the fit; the block 7 models (four folds) are the "before" comparison.
- Interfaces: `SENTINEL`, `ROLES`, `split_pairs`, `all_pairs`, `load`, `Lineage`, `lineage_of`,
  `check_independent`, `episodes_for`
- Depends on: research/protocol_v2/tasks_v21.py, research/belief_planning/tasks.py
"""
from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass

import numpy as np

FOLDS = (0, 1, 2, 3, 4)
SENTINEL = 97
"""The fold id given to every held-out compound of a nested context (not a registered fold)."""

ROLES = {"split": {f: (f + 1) % 5 for f in FOLDS}}
"""Pre-declared calibration fold of the split design, per test fold."""


def split_pairs():
    return [(f, c) for f, c in ROLES["split"].items()]


def all_pairs():
    return list(itertools.combinations(FOLDS, 2))


class LineageError(ValueError):
    """A fitted component saw a unit it must not have seen."""


@dataclass(frozen=True)
class Lineage:
    dataset: str
    tier: str
    excluded_folds: tuple
    training_folds: tuple
    training_compounds: tuple
    training_sha256: str
    reference_names: tuple
    pool: tuple
    validator: dict

    def payload(self) -> dict:
        return {"dataset": self.dataset, "tier": self.tier, "excluded_folds": list(self.excluded_folds),
                "training_folds": list(self.training_folds), "training_compounds": len(self.training_compounds),
                "training_sha256": self.training_sha256, "reference_names": len(self.reference_names),
                "reference_sha256": hashlib.sha256("|".join(sorted(self.reference_names)).encode()).hexdigest(),
                "pool": list(self.pool), "validator": self.validator}


def load(dataset: str, tier_name: str, heldout):
    """(data, ctx, setting, design, original_fold) for protocol v2.1 with the folds `heldout` removed.

    `original_fold` maps each compound to its registered fold; `data.compounds.fold` carries
    SENTINEL for the held-out ones, which is what `tasks_v21` sees.
    """
    from research.protocol_v2 import tasks_v21 as TV
    heldout = tuple(sorted(int(f) for f in heldout))
    if not heldout or set(heldout) - set(FOLDS):
        raise ValueError(f"held-out folds must be registered folds: {heldout}")
    C, LP, K, DS = TV.C, TV.LP, TV.K, TV.DS
    spec = C.load_protocol()
    design = DS.load(dataset)
    if dataset == "l1000":
        data = LP.load()
        smiles = TV.T.l1000_smiles()
        data.compounds["smiles"] = [smiles.get(c) for c in data.compounds.compound]
    else:
        data = C.load()
    data.compounds = data.compounds.copy()
    original = dict(zip(data.compounds.compound, data.compounds.fold.astype(int)))
    data.compounds.loc[data.compounds.fold.isin(heldout), "fold"] = SENTINEL
    if dataset == "l1000":
        detected = data.conditions.detected.to_numpy(bool)
        tier = TV._l1000_tier(data, design, SENTINEL, tier_name, detected)
        ctx = TV._context(data, tier, SENTINEL, detected, spec, TV.E.stable(tier.name))
        setting = LP.setting(tier)
    else:
        detected = C.detected_flags(data, C.detection_null(data, spec))
        tier = TV._sciplex3_tier(data, spec, design, SENTINEL, tier_name)
        ctx = TV._context(data, tier, SENTINEL, detected, spec, ord(tier_name))
        setting = TV.P.sciplex3_setting(tier)
    return data, ctx, setting, design, original


def lineage_of(dataset, tier, heldout, ctx, original) -> Lineage:
    from research.protocol_v2 import tasks_v21 as TV
    training = TV.training_compounds(ctx, SENTINEL)
    names = sorted(set().union(*[set(t.names) for t in ctx.ft.tables.values()])) if ctx.ft.tables else []
    folds = sorted({original[c] for c in names} | {original[c] for c in training})
    validator = {k: (bool(v) if isinstance(v, (bool, np.bool_)) else float(v) if isinstance(v, (int, float, np.floating))
                     else v) for k, v in ctx.params.items() if k in ("floor", "margin", "eliminates")}
    return Lineage(dataset, tier, tuple(sorted(heldout)), tuple(folds), tuple(sorted(training)),
                   hashlib.sha256("|".join(sorted(training)).encode()).hexdigest(), tuple(names),
                   tuple(ctx.tier.pool), validator)


def check_independent(lineage: Lineage, test_compounds, unit_of: dict) -> None:
    """Raise if a test compound, or another compound of a test unit, entered any fitted component."""
    test_units = {unit_of.get(c, c) for c in test_compounds}
    seen = set(lineage.training_compounds) | set(lineage.reference_names)
    leaked = sorted(c for c in seen if c in set(test_compounds) or unit_of.get(c, c) in test_units)
    if leaked:
        raise LineageError(f"{len(leaked)} fitted compounds belong to test units, e.g. {leaked[:3]}")


def episodes_for(ctx, original, fold: int):
    """The protocol-v2.1 episodes of the compounds registered in `fold`, from a nested context."""
    from research.protocol_v2 import tasks_v21 as TV
    return [e for e in TV.episode_list(ctx, SENTINEL) if original.get(e[0]) == fold]
