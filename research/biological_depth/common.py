"""Shared helpers for the pre-registered biological-depth audit.

File summary
- Path: research/biological_depth/common.py
- Purpose: one place for the frozen protocol, compound identity, structure resolution, fold
  assignment, gene sets and compound-clustered statistics, so every step reads them the same way.
- Core points:
  - Compound identity is folded (salt words, punctuation, case) before any comparison.
  - The split unit is the skeleton group, so salts and stereoisomers never straddle a fold.
  - Uncertainty is clustered by compound: cells and genes are not replicates.
- Depends on: numpy, pandas, rdkit
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SALT_WORDS = (r"\b(hcl|2hcl|dihydrochloride|hydrochloride|sodium|disodium|trihydrate|hydrate|free base|"
              r"citrate|mesylate|tosylate|ditosylate|diphosphate|phosphate|l-\(\+\)-tartaric acid|tartaric acid|salt|acetate|"
              r"maleate|sulfate)\b")


def load_protocol() -> dict:
    return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))


def load_anchors() -> dict:
    return json.loads((HERE / "anchors.json").read_text(encoding="utf-8"))


def frozen_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("PROTOCOL.md", "protocol.json", "anchors.json")}


def name_keys(name: str) -> list[str]:
    """Folded identity keys: the full name, the name without parentheses, and each alias."""

    parts = [name.strip(), re.sub(r"\([^)]*\)", "", name)] + re.findall(r"\(([^)]*)\)", name)
    keys = []
    for part in parts:
        for piece in re.split(r"[,/]", part):
            key = re.sub(r"[^a-z0-9]", "", re.sub(SALT_WORDS, "", piece.lower()))
            if len(key) >= 3:
                keys.append(key)
    return list(dict.fromkeys(keys))


def canonical_parent(smiles: str) -> str | None:
    from rdkit import Chem, RDLogger

    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fragments = Chem.GetMolFrags(mol, asMols=True)
    return Chem.MolToSmiles(max(fragments, key=lambda item: item.GetNumHeavyAtoms()))


def skeleton(smiles: str) -> str:
    from rdkit import Chem

    return Chem.MolToInchiKey(Chem.MolFromSmiles(smiles)).split("-")[0]


def resolve_structures(compounds: list[str], subset_pairs: list[tuple[str, str]],
                       hub: pd.DataFrame, manual: dict[str, tuple[str, str]]) -> tuple[dict, dict]:
    """Resolve one parent structure per compound; ambiguity is recorded, never guessed."""

    tables = []
    for label, pairs in (("chemcpa_subset", subset_pairs), ("repurposing_hub", list(zip(hub.pert_iname, hub.smiles)))):
        table: dict[str, set[str]] = {}
        for name, smiles in pairs:
            if not isinstance(smiles, str):
                continue
            parent = canonical_parent(smiles)
            if parent:
                for key in name_keys(name):
                    table.setdefault(key, set()).add(parent)
        tables.append((label, table))
    resolved, source = {}, {}
    for compound in compounds:
        for label, table in tables:
            candidates = set().union(*(table.get(key, set()) for key in name_keys(compound)))
            if len(candidates) == 1:
                resolved[compound], source[compound] = next(iter(candidates)), label
                break
            if len(candidates) > 1:
                source.setdefault(compound, f"{label}:ambiguous:{len(candidates)}")
        if compound not in resolved and compound in manual:
            resolved[compound] = canonical_parent(manual[compound][0])
            source[compound] = manual[compound][1]
    return resolved, source


def assign_folds(units: pd.DataFrame, folds: int) -> dict[str, int]:
    """Deal skeleton groups round-robin within each pathway stratum in hash order."""

    assignment: dict[str, int] = {}
    offset = 0
    for _, stratum in units.groupby("pathway_level_1", sort=True):
        ordered = sorted(stratum.skeleton.unique(),
                         key=lambda s: hashlib.sha256(("maestro-biodepth-v1|" + s).encode()).hexdigest())
        for index, value in enumerate(ordered):
            assignment[value] = (index + offset) % folds
        offset += len(ordered)
    return assignment


def inner_validation(skeletons: list[str], fraction: float = 0.15) -> set[str]:
    ranked = sorted(skeletons, key=lambda s: hashlib.sha256(("maestro-biodepth-inner|" + s).encode()).hexdigest())
    return set(ranked[: max(1, int(round(len(ranked) * fraction)))])


def read_gmt(path: Path) -> dict[str, list[str]]:
    sets = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) > 2:
            sets[fields[0]] = [gene for gene in fields[2:] if gene]
    return sets


def cluster_bootstrap(values_by_cluster: dict[str, float], *, seed: int = 20260926, draws: int = 2000) -> dict:
    """Mean over clusters with a percentile interval from resampling clusters."""

    values = np.array([v for v in values_by_cluster.values() if np.isfinite(v)], dtype=float)
    if values.size == 0:
        return {"mean": None, "ci95": [None, None], "clusters": 0}
    rng = np.random.default_rng(seed)
    means = values[rng.integers(values.size, size=(draws, values.size))].mean(axis=1)
    return {"mean": float(values.mean()), "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
            "clusters": int(values.size)}


def paired_bootstrap(a: dict[str, float], b: dict[str, float], *, seed: int = 20260926, draws: int = 2000) -> dict:
    keys = [k for k in a if k in b and np.isfinite(a[k]) and np.isfinite(b[k])]
    return cluster_bootstrap({k: a[k] - b[k] for k in keys}, seed=seed, draws=draws)


def write_json(path: Path, value) -> None:
    """Strict JSON; a non-finite number is written as null rather than as NaN or a guess."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(value), indent=1, allow_nan=False, default=_default) + "\n", encoding="utf-8")


def _clean(value):
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(type(value).__name__)
