"""Development tasks: the registered 2026-09-27 episodes, loaded through the historical context path.

File summary
- Path: research/belief_planning/tasks.py
- Purpose: build, for one (dataset, tier, fold), the fold context, the runner setting, the episode
  list, and the side tables the belief-planning arms need. These are the training compounds, the
  seeded virtual-cell partner derangement, and an evaluation-side reader of a partner compound's
  real reading, which is used only by the permuted-feedback control.
- Core points:
  - SciPlex3 uses `episodes.contexts`, the path that reproduces the registered 2026-09-27 episode
    manifests exactly. `external_validation.locked_replay.load` was changed after that run to a
    metadata path that adds 18 (tier A) and 153 (tier B) fold-0 episodes whose truth is `None`
    (unlabelled compounds), so it is not used here.
  - L1000 uses `lincs_evaluate.context`, unchanged since the registered run.
  - `sealed(task)` returns the context an arm receives, sealed with `external_validation.firewall.seal`;
    the planner's world model reads only training tables and structures.
- Interfaces: `TASKS`, `load`, `prepare`, `units`
- Depends on: research/dynamic_world_model, research/sequence_audit, research/external_validation/firewall.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("sequence_audit", "acquisition_link", "dynamic_world_model", "acquisition_followup"):
    sys.path.insert(0, str(ROOT / "research" / sub))

import policies as P  # noqa: E402
import lincs_evaluate as LE  # noqa: E402
import lincs_prepare as LP  # noqa: E402

C, E = P.C, P.E
SEED = 20260927
TASKS = [(dataset, tier, fold) for dataset, tiers in (("sciplex3", ("A", "B")), ("l1000", ("LT", "T")))
         for tier in tiers for fold in range(5)]
UNIT = {"sciplex3": "skeleton", "l1000": "component"}


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def l1000_smiles() -> dict:
    pert = pd.read_csv(LP.DATA / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str).fillna("")
    return {pid: (s if s and s != "-666" else None) for pid, s in zip(pert.pert_id, pert.canonical_smiles)}


def units(dataset: str) -> pd.DataFrame:
    """Independent unit per compound: SciPlex3 skeleton, L1000 identity/scaffold component."""
    if dataset == "sciplex3":
        analyze = _module(ROOT / "research/sequence_audit/analyze.py", "sequence_audit_analyze")
        frame = analyze.sciplex3_units().rename(columns={"scaffold": "murcko_scaffold"})
    else:
        analyze = _module(ROOT / "research/sequence_audit/lincs_analyze.py", "sequence_audit_lincs_analyze")
        table = analyze.units()
        frame = pd.DataFrame({name: series for name, series in table.items()})
        compounds = pd.read_csv(LP.OUT / "compounds.csv").set_index("compound")
        frame["murcko_scaffold"] = compounds.scaffold.reindex(frame.index)
    frame["compound"] = frame.index
    return frame


def load(dataset: str, tier_name: str, fold: int):
    spec = C.load_protocol()
    if dataset == "l1000":
        data = LP.load()
        smiles = l1000_smiles()
        data.compounds["smiles"] = [smiles.get(c) for c in data.compounds.compound]
        tier = LP.tiers()[tier_name]
        detected = data.conditions.detected.to_numpy(bool)
        ctx = LE.context(data, tier, fold, detected, spec)
        setting = LP.setting(tier)
    else:
        data = C.load()
        detected = C.detected_flags(data, C.detection_null(data, spec))
        ctx, _ = next(E.contexts(data, spec, detected, None, tier_names=(tier_name,), folds=(fold,)))
        setting = P.sciplex3_setting(ctx.tier)
    return data, ctx, setting


def partners(compounds, fold: int, tier: str) -> dict:
    """A seeded derangement of the fold's held-out compounds (the 2026-09-27 `vc_partners` rule)."""
    names = sorted(compounds)
    if len(names) < 2:
        return {c: c for c in names}
    rng = np.random.default_rng([SEED, int(fold), E.stable("vc_partner", tier)])
    order = list(rng.permutation(len(names)))
    partner = {names[i]: names[j] for i, j in zip(range(len(names)), order)}
    for position, name in enumerate(names):
        if partner[name] == name:
            swap = names[(position + 1) % len(names)]
            partner[name], partner[swap] = partner[swap], partner[name]
    return partner


def prepare(ctx, fold: int, tier: str, *, real_ctx=None):
    """Attach the training set, partners and the permuted-feedback reader to an arm's context."""
    real_ctx = real_ctx or ctx
    comp = real_ctx.data.compounds.drop_duplicates("compound").set_index("compound")
    episodes = E.episode_list(real_ctx, fold)
    held = sorted({e[0] for e in episodes})
    training = tuple(c for c in real_ctx.tier.compounds if comp.fold.get(c) != fold)
    if not training:
        # an external study lists only its test compounds in the tier: the QC-failure base rate then
        # comes from the reference arm, restricted like the test compounds to those with a row at
        # every condition of the menu
        keys = real_ctx.tier.keys
        training = tuple(sorted(c for c in comp.index if comp.fold.get(c) != fold and comp.klass.get(c) in real_ctx.tier.pool
                                and all(c in real_ctx.data.index.get(k, {}) for k in keys)))
    ctx.extra["training_compounds"] = training
    ctx.extra["vc_partner"] = partners(held, fold, tier)
    rng = np.random.default_rng([SEED, int(fold), E.stable("feedback_partner", tier)])
    order = [held[i] for i in rng.permutation(len(held))]
    position = {c: i for i, c in enumerate(order)}

    def other(compound, key, h1, h2):
        """Evaluation-side: a compatible partner's real reading of the same condition and contrast.

        Compatible means the partner's reading would also have left the episode running
        (unresolved or undetected), so the substituted history is one the runner could have
        produced. Partners are tried in a seeded order that starts after the compound itself.
        """
        from . import world as W
        start = position.get(compound, -1)
        for step in range(1, len(order)):
            partner = order[(start + step) % len(order)]
            outcome = E.execute(real_ctx, partner, key, h1, h2)["outcome"]
            if outcome in ("ambiguous", "undetected"):
                return W.label_of(outcome)
        return W.NONTERMINAL

    ctx.extra["feedback_partner_reading"] = other
    return episodes
