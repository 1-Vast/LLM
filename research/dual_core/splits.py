"""Split integrity: fold identifiers, independent units, coverage, duplicates and cross-fitting roles.

File summary
- Path: research/dual_core/splits.py
- Purpose: check programmatically, before any scoring, that the splits every dual-core experiment
  uses are what they claim to be, and write a manifest with hashes of the data and splits.
- Core points:
  - Fold identifiers must be exactly the registered set (0-4). An empty intended task is an error,
    not a silent zero. Block 6's first runs used 1-5; that error is a regression test here.
  - The declared independent unit (`belief_planning.tasks.UNIT`) must never span two folds.
    - SciPlex3's unit is the InChIKey connectivity block (the first 14 characters, stored as
      `skeleton`). It is not a Murcko scaffold.
    - L1000's unit is a connected component of identity and Murcko scaffold.
    Murcko scaffolds that span folds are reported separately; they are not the declared unit.
  - Every eligible compound is held out exactly once across folds.
  - `crossfit_roles` gives, for each test fold, the calibration folds and asserts they are disjoint
    from it. Models are always fitted on the test fold's training folds.
  - `duplicated_records` rejects evaluation tables in which a key occurs twice.
- Interfaces: `FOLDS`, `check_folds`, `check_units`, `check_coverage`, `check_tasks`, `crossfit_roles`,
  `duplicated_records`, `murcko_scaffolds`, `manifest`
- Depends on: research/protocol_v2/tasks_v21.py, research/belief_planning/tasks.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FOLDS = (0, 1, 2, 3, 4)


class SplitError(ValueError):
    """A split does not satisfy its declared integrity property."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_folds(requested, available=FOLDS) -> tuple:
    """The requested folds, validated against the registered identifiers."""
    requested = tuple(int(f) for f in requested)
    bad = sorted(set(requested) - set(available))
    if bad:
        raise SplitError(f"unregistered fold identifiers {bad}; registered folds are {sorted(available)}")
    if len(set(requested)) != len(requested):
        raise SplitError("a fold is requested twice")
    return requested


def check_units(fold_of: pd.Series, unit_of: pd.Series) -> None:
    """Every declared unit lies in exactly one fold, and every compound has a unit and a fold."""
    frame = pd.DataFrame({"fold": fold_of, "unit": unit_of.reindex(fold_of.index)})
    if frame.fold.isna().any():
        raise SplitError(f"compounds without a fold: {sorted(frame.index[frame.fold.isna()])[:5]}")
    if frame.unit.isna().any():
        raise SplitError(f"compounds without a unit: {sorted(frame.index[frame.unit.isna()])[:5]}")
    spans = frame.groupby("unit").fold.nunique()
    if (spans > 1).any():
        raise SplitError(f"units in more than one fold: {sorted(spans.index[spans > 1])[:5]}")


def check_coverage(heldout_by_fold: dict, eligible) -> None:
    """Each eligible compound is held out in exactly one fold and nothing else is held out."""
    seen: dict = {}
    for fold, compounds in heldout_by_fold.items():
        for c in compounds:
            seen.setdefault(c, []).append(fold)
    twice = sorted(c for c, f in seen.items() if len(f) > 1)
    if twice:
        raise SplitError(f"compounds held out in more than one fold: {twice[:5]}")
    missing = sorted(set(eligible) - set(seen))
    if missing:
        raise SplitError(f"eligible compounds never held out: {missing[:5]} ({len(missing)} in all)")
    extra = sorted(set(seen) - set(eligible))
    if extra:
        raise SplitError(f"held-out compounds that are not eligible: {extra[:5]}")


def check_tasks(counts: dict) -> None:
    """An intended task with no evaluation items is an error."""
    empty = sorted(k for k, n in counts.items() if n == 0)
    if empty:
        raise SplitError(f"intended tasks with no items: {empty}")


def crossfit_roles(folds=FOLDS) -> dict:
    """For each test fold: the calibration folds (all others). Disjointness is asserted."""
    folds = check_folds(folds)
    roles = {f: tuple(g for g in folds if g != f) for f in folds}
    for f, cal in roles.items():
        if f in cal or not cal:
            raise SplitError(f"calibration folds for test fold {f} are not disjoint from it or are empty")
    return roles


def duplicated_records(frame: pd.DataFrame, key) -> None:
    dup = frame.duplicated(list(key))
    if dup.any():
        raise SplitError(f"{int(dup.sum())} duplicated evaluation records on {list(key)}")


def murcko_scaffolds(compounds: pd.DataFrame) -> pd.Series:
    """Generic-free Murcko scaffold SMILES per compound ('acyclic:<name>' when there is no ring system)."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold
    RDLogger.DisableLog("rdApp.*")
    out = {}
    for name, smiles in compounds["smiles"].items():
        mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles else None
        text = Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol)) if mol is not None else ""
        out[name] = text or f"acyclic:{name}"
    return pd.Series(out)


def dataset_frame(dataset: str):
    """(compound table indexed by compound with fold, unit and scaffold, data object)."""
    from research.belief_planning import tasks as T
    from research.protocol_v2 import tasks_v21 as TV
    data = TV.C.load() if dataset == "sciplex3" else TV.LP.load()
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    units = T.units(dataset)
    frame = pd.DataFrame({"fold": comp.fold, "unit": units[T.UNIT[dataset]].reindex(comp.index).astype(str),
                          "unit_kind": "inchikey_connectivity" if dataset == "sciplex3" else "identity_scaffold_component",
                          "scaffold": units["murcko_scaffold"].reindex(comp.index)})
    return frame, data


def manifest(out: Path, *, tasks=(("sciplex3", "A"), ("sciplex3", "B"), ("l1000", "LT"), ("l1000", "T"))) -> dict:
    """Run every check on the registered data and write `split_manifest.json` with hashes."""
    from research.protocol_v2 import tasks_v21 as TV
    result = {"folds": list(FOLDS), "datasets": {}, "tasks": {}, "files": {}}
    for dataset in ("sciplex3", "l1000"):
        frame, _ = dataset_frame(dataset)
        check_folds(sorted(frame.fold.unique()))
        check_units(frame.fold, frame.unit)
        spans = frame.groupby("scaffold").fold.nunique()
        spanning = sorted(spans.index[spans > 1])
        result["datasets"][dataset] = {
            "compounds": int(len(frame)), "units": int(frame.unit.nunique()), "unit_kind": frame.unit_kind.iloc[0],
            "fold_sizes_units": frame.drop_duplicates("unit").fold.value_counts().sort_index().to_dict(),
            "murcko_scaffolds": int(frame.scaffold.nunique()), "murcko_scaffolds_spanning_folds": spanning,
            "compounds_sharing_a_spanning_scaffold": int(frame.scaffold.isin(spanning).sum()),
            "assignment_sha256": hashlib.sha256(frame[["fold", "unit"]].sort_index().to_csv().encode()).hexdigest()}
    for dataset, tier in tasks:
        heldout, counts, eligible = {}, {}, set()
        for fold in FOLDS:
            data, ctx, setting, design = TV.load(dataset, tier, fold)
            comp = data.compounds.drop_duplicates("compound").set_index("compound")
            episodes = TV.episode_list(ctx, fold)
            counts[f"{dataset}_{tier}_{fold}"] = len(episodes)
            heldout[fold] = sorted({e[0] for e in episodes})
            eligible |= {c for c in ctx.tier.compounds if comp.klass.get(c) in ctx.tier.pool and comp.fold.get(c) == fold}
        check_tasks(counts)
        check_coverage(heldout, eligible)
        result["tasks"][f"{dataset}_{tier}"] = {"episodes_by_fold": counts,
                                                "heldout_compounds_by_fold": {f: len(v) for f, v in heldout.items()}}
    prepared = [ROOT / "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
                ROOT / "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
                ROOT / "outputs/biological_depth_20260926/prepared/compounds.csv",
                ROOT / "outputs/biological_depth_20260926/prepared/gene_sets.json",
                ROOT / "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
                ROOT / "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
                ROOT / "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz"]
    result["files"] = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in prepared}
    result["roles"] = {str(k): list(v) for k, v in crossfit_roles().items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    res = manifest(ROOT / "outputs/dual_core_20260927/split_manifest.json")
    print(json.dumps({k: v for k, v in res.items() if k != "files"}, indent=1, default=str)[:3000])
