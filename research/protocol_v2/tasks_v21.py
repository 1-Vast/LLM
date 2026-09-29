"""Protocol-v2.1 development tasks: per-fold pools and design-based eligibility on the registered data.

File summary
- Path: research/protocol_v2/tasks_v21.py
- Purpose: build, for one (dataset, tier, fold), the fold context protocol v2.1 runs on. The data,
  folds, units, validator and runner setting are protocol v2's; three things change, each fixing a
  block-4 audit finding.
- Core points:
  - Hypothesis pool from the fold's training compounds only (audit D7). SciPlex3 tier B counts
    training skeleton units per class (`common.tiers` with `reference_compounds`); tier A counts
    training compounds planned at 72 h. L1000 applies `lincs_prepare`'s rule (at least 6
    identities and 2 detected identities) to training compounds via `contracts.fold_pools`.
    Protocol v2 counted every compound, held-out ones included, before the split.
  - Eligibility from the study design (`design.py`, audit D8 and D10): SciPlex3 tier B needs a
    planned condition in the tier, tier A a planned 72 h condition, and L1000 every tier condition
    planned. L1000 v2 required every condition to have passed QC, so compounds with a QC failure
    were never evaluated.
  - The episode list keeps protocol v2's forced-choice construction and seeds (each scorable
    held-out compound's class against every other pool class, order seeded by `episodes.stable`),
    applied to design-eligible compounds.
  - `training` for the world model's QC-failure base rate is the fold's training compounds that
    are eligible and whose class is in the fold's pool, as in protocol v2.
- Interfaces: `load`, `episode_list`, `training_compounds`
- Depends on: design.py, contracts.py, research/belief_planning/tasks.py, research/dynamic_world_model,
  research/sequence_audit/lincs_prepare.py and lincs_evaluate.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import contracts as K
from . import design as DS

T = K.T
P, C, E = T.P, T.C, T.E
LP, LE = T.LP, T.LE


def _sciplex3_tier(data, spec, design, fold: int, name: str):
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    reference = {c for c in comp.index if comp.fold[c] != fold}
    base = C.tiers(data, spec, reference_compounds=reference)[name]
    keys = tuple(base.keys)
    eligibility = [k for k in keys if k[1] == 72.0] if name == "A" else list(keys)
    if name == "A":
        rule = spec["tiers"]["A_time_dose"]["minimum_compounds_per_class_at_72h"]
        at72 = [c for c in sorted(reference) if design.get(c, frozenset()) & set(eligibility)]
        counts = pd.Series([comp.klass.get(c) for c in at72], dtype=object).dropna().value_counts()
        pool = tuple(sorted(counts[counts >= rule].index))
    else:
        pool = tuple(base.pool)
    eligible = tuple(sorted(c for c in comp.index if design.get(c, frozenset()) & set(eligibility)))
    return C.Tier(name, keys, pool, eligible)


def _l1000_tier(data, design, fold: int, name: str, detected: np.ndarray):
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    keys = tuple(LP.TIERS[name]["keys"])
    complete = {c for c in comp.index if set(keys) <= design.get(c, frozenset())}
    training = [c for c in comp.index if comp.fold[c] != fold]
    detected_at = {}
    for c in training:
        rows = [data.index.get(k, {}).get(c) for k in keys]
        detected_at[c] = {k for k, r in zip(keys, rows) if r is not None and bool(detected[r])}
    pool = K.fold_pools(comp.klass.to_dict(), comp.identity.astype(str).to_dict(), training, complete, detected_at,
                        min_identities=LP.POOL_MIN_IDENTITIES, min_detected=LP.POOL_MIN_DETECTED_IDENTITIES)
    return C.Tier(name, keys, pool, tuple(sorted(complete)))


def _context(data, tier, fold: int, detected, spec, seed_name):
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    ft = C.build_fold_tables(data, tier, fold, detected)
    params = C.calibrate(ft, spec)
    rng = np.random.default_rng([C.SEED, int(fold), seed_name])
    train = [c for c in comp.index if comp.fold[c] != fold and comp.klass.get(c) in tier.pool]
    permuted = dict(zip(train, rng.permutation([comp.klass[c] for c in train])))
    ft_perm = C.build_fold_tables(data, tier, fold, detected, label_map=permuted)
    return E.FoldContext(data, tier, ft, ft_perm, params, detected, None, {}, {})


def load(dataset: str, tier_name: str, fold: int):
    """(data, fold context, runner setting, design) for protocol v2.1."""
    spec = C.load_protocol()
    design = DS.load(dataset)
    if dataset == "l1000":
        data = LP.load()
        smiles = T.l1000_smiles()
        data.compounds["smiles"] = [smiles.get(c) for c in data.compounds.compound]
        detected = data.conditions.detected.to_numpy(bool)
        tier = _l1000_tier(data, design, fold, tier_name, detected)
        ctx = _context(data, tier, fold, detected, spec, E.stable(tier.name))
        setting = LP.setting(tier)
    else:
        data = C.load()
        detected = C.detected_flags(data, C.detection_null(data, spec))
        tier = _sciplex3_tier(data, spec, design, fold, tier_name)
        ctx = _context(data, tier, fold, detected, spec, ord(tier_name))
        setting = P.sciplex3_setting(tier)
    return data, ctx, setting, design


def training_compounds(ctx, fold: int) -> tuple:
    comp = ctx.data.compounds.drop_duplicates("compound").set_index("compound")
    return tuple(c for c in ctx.tier.compounds if comp.fold.get(c) != fold and comp.klass.get(c) in ctx.tier.pool)


def episode_list(ctx, fold: int):
    """Protocol v2's forced-choice episodes over design-eligible held-out compounds (same seeds)."""
    comp = ctx.data.compounds.drop_duplicates("compound").set_index("compound")
    out = []
    for compound in ctx.tier.compounds:
        if compound not in comp.index or comp.fold[compound] != fold:
            continue
        truth = comp.klass[compound]
        if not isinstance(truth, str) or truth not in ctx.tier.pool:
            continue
        for decoy in ctx.tier.pool:
            if decoy == truth:
                continue
            rng = np.random.default_rng([C.SEED, E.stable(compound, decoy)])
            h1, h2 = (truth, decoy) if rng.random() < 0.5 else (decoy, truth)
            out.append((compound, truth, decoy, h1, h2))
    return out
