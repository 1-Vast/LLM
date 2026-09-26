"""Shared data, validator and scenario-card machinery for the measurement-choice study.

File summary
- Path: research/dynamic_world_model/common.py
- Purpose: load the prepared SciPlex3 conditions, build the vehicle-well detection null, and
  implement the frozen validator (quality, detection, absence, projected-similarity elimination)
  with its per-fold calibration and the reference-based scenario-card estimates.
- Core points:
  - Every similarity is a cosine after projecting out the shared axis of the training compounds
    at the same condition. Inner leave-one-out rows are computed from a Gram matrix so the left-out
    compound is removed from the axis as well as from the templates.
  - A training compound's leave-one-out outcome under the validator is simultaneously the
    calibration data and the branch of a scenario card: a card is the validator's behaviour on
    measured references, never a generated profile.
  - `evidence_update` routes every executed measurement through the repository's
    `InterpretationTable` and `EvidenceState`, so the belief a policy ends with is decided by the
    same code a real result would meet.
- Interfaces: `load`, `detection_null`, `Tier`, `FoldTables`, `build_fold_tables`, `calibrate`,
  `read_profile`, `card`, `evidence_update`, `mechanism_class`, `TIERS`
- Depends on: numpy, pandas, maestro.models, maestro.outcome, agent.cases
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

HERE = Path(__file__).resolve().parent
PREPARED = ROOT / "outputs/dynamic_world_model_20260926/prepared"
FROZEN = ROOT / "outputs/biological_depth_20260926/prepared"
OUTPUTS = ROOT / "outputs/dynamic_world_model_20260926"
SEED = 20260926


def load_protocol() -> dict:
    return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))


def frozen_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ("PROTOCOL.md", "protocol.json")}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, default=_default, allow_nan=False), encoding="utf-8")


def _default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    return str(value)


def clean(value):
    """Replace non-finite floats by None so records serialise with allow_nan=False."""
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, np.floating):
        return clean(float(value))
    if isinstance(value, np.integer):
        return int(value)
    return value


# ---------------------------------------------------------------------------------- classes
def mechanism_class(pathway_level_2: str, target: str) -> str | None:
    """The protocol's first-matching-rule class map (protocol.json, classes.rules)."""
    p = str(pathway_level_2 or "").strip()
    t = str(target or "").strip()
    if p == "Histone deacetylation" and "HDAC" in t:
        return "HDAC inhibition"
    if p == "Histone deacetylation" and "Sirtuin" in t:
        return "Sirtuin modulation"
    if p == "Aurora kinase activity":
        return "Aurora kinase inhibition"
    if p == "JAK kinase activity":
        return "JAK inhibition"
    if t == "PARP":
        return "PARP inhibition"
    if p == "Histone methylation":
        return "Histone methyltransferase inhibition"
    if p == "DNA methylation" and t == "DNA Methyltransferase":
        return "DNA methyltransferase inhibition"
    if p == "Nucleotide analog":
        return "Nucleotide analog"
    if p == "RTK activity":
        return "Receptor tyrosine kinase inhibition"
    if p == "HSP90 activity":
        return "HSP90 inhibition"
    if p == "MAPK activity":
        return "MEK/MAPK inhibition"
    if p == "Abl/Src activity":
        return "Abl/Src inhibition"
    if "Bcl-2" in t:
        return "BCL-2 family inhibition"
    if "Glucocorticoid" in t:
        return "Glucocorticoid receptor agonism"
    if p == "Alkylating agent":
        return "DNA alkylation"
    if p == "CDK activity":
        return "CDK inhibition"
    if p == "Bromodomain":
        return "BET bromodomain inhibition"
    if t == "HIF":
        return "HIF stabilisation or inhibition"
    return None


# ---------------------------------------------------------------------------------- data
@dataclass
class Data:
    conditions: pd.DataFrame
    shift: np.ndarray
    rep1: np.ndarray
    rep2: np.ndarray
    compounds: pd.DataFrame
    genes: pd.DataFrame
    gene_sets: dict
    wells: pd.DataFrame
    well_mean: np.ndarray
    agreement: np.ndarray = field(default_factory=lambda: np.zeros(0))
    index: dict = field(default_factory=dict)          # (line, time, dose) -> {compound: row}


def load(prepared: Path = PREPARED) -> Data:
    conditions = pd.read_csv(prepared / "conditions.csv")
    conditions["compound"] = conditions.compound.astype(str).str.strip()
    arrays = np.load(prepared / "shifts.npz")
    compounds = pd.read_csv(FROZEN / "compounds.csv")
    compounds["compound"] = compounds.compound.astype(str).str.strip()
    compounds["klass"] = [mechanism_class(p, t) for p, t in zip(compounds.pathway_level_2, compounds.target)]
    genes = pd.read_csv(FROZEN / "genes.csv")
    gene_sets = json.loads((FROZEN / "gene_sets.json").read_text(encoding="utf-8"))
    wells = pd.read_csv(prepared / "wells.csv")
    well_mean = np.load(prepared / "well_means.npz")["well_mean"]
    data = Data(conditions, arrays["shift"], arrays["rep1"], arrays["rep2"], compounds, genes, gene_sets, wells, well_mean)
    data.agreement = np.array([_pearson(a, b) if np.isfinite(a).all() and np.isfinite(b).all() else np.nan
                               for a, b in zip(data.rep1, data.rep2)])
    for row, r in conditions.iterrows():
        data.index.setdefault((r.cell_line, float(r.time), float(r.dose)), {})[r.compound] = row
    return data


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    denominator = float(np.sqrt((a @ a) * (b @ b)))
    return float(a @ b) / denominator if denominator > 0 else 0.0


def qc_passed(data: Data, row: int) -> bool:
    r = data.conditions.iloc[row]
    return int(r.replicates) == 2 and r.n_cells_rep1 >= 20 and r.n_cells_rep2 >= 20


# ---------------------------------------------------------------------------------- detection null
def detection_null(data: Data, protocol: dict) -> dict:
    """Vehicle wells as pseudo-conditions: one rep1 well against one rep2 well, same line and time."""
    rule = protocol["validator"]["detection"]
    wells = data.wells[data.wells.is_control]
    out = {}
    for (line, t), sub in wells.groupby(["cell_line", "time"]):
        shifts = {}
        for rep, part in sub.groupby("replicate"):
            for i, r in part.iterrows():
                others = part.drop(index=i)
                weights = others.n_cells.to_numpy()[:, None]
                reference = (data.well_mean[others.index] * weights).sum(0) / weights.sum()
                shifts.setdefault(rep, []).append(data.well_mean[i] - reference)
        values = [_pearson(a, b) for a in shifts.get("rep1", []) for b in shifts.get("rep2", [])]
        q = float(np.quantile(values, 0.99)) if values else float("nan")
        out[f"{line}|{t:g}"] = {"pairs": len(values), "q99": q, "median": float(np.median(values)) if values else None,
                                "max": float(np.max(values)) if values else None,
                                "threshold": max(0.10, q) if values else None}
    return out


def detected_flags(data: Data, null: dict) -> np.ndarray:
    thresholds = np.array([null[f"{r.cell_line}|{float(r.time):g}"]["threshold"] for r in data.conditions.itertuples()])
    ok = np.array([qc_passed(data, i) for i in range(len(data.conditions))])
    return ok & (np.nan_to_num(data.agreement, nan=-1.0) >= thresholds)


# ---------------------------------------------------------------------------------- tiers
@dataclass(frozen=True)
class Tier:
    name: str
    keys: tuple                      # condition keys (line, time, dose)
    pool: tuple                      # hypothesis classes
    compounds: tuple                 # compounds eligible as held-out episode compounds


def action_id(key) -> str:
    line, t, dose = key
    return f"{line}|{int(t):03d}h|{int(dose):05d}nM"


def tiers(data: Data, protocol: dict) -> dict[str, Tier]:
    spec = protocol["tiers"]
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    out = {}
    b = spec["B_line_dose"]
    keys_b = tuple((line, 24.0, float(d)) for line in b["lines"] for d in b["doses_nM"])
    units = data.compounds.dropna(subset=["klass"]).drop_duplicates("skeleton").klass.value_counts()
    pool_b = tuple(sorted(units[units >= b["minimum_units_per_class"]].index))
    measured_b = {c for k in keys_b for c in data.index.get(k, {})}
    out["B"] = Tier("B", keys_b, pool_b, tuple(sorted(c for c in measured_b if comp.klass.get(c) in pool_b)))
    a = spec["A_time_dose"]
    keys_a = tuple((line, float(t), float(d)) for line in a["lines"] for t in a["time_hours"] for d in a["doses_nM"])
    at72 = {c for k in keys_a if k[1] == 72.0 for c in data.index.get(k, {})}
    counts = pd.Series([comp.klass.get(c) for c in at72]).value_counts()
    pool_a = tuple(sorted(counts[counts >= a["minimum_compounds_per_class_at_72h"]].index))
    out["A"] = Tier("A", keys_a, pool_a, tuple(sorted(c for c in at72 if comp.klass.get(c) in pool_a)))
    return out


# ---------------------------------------------------------------------------------- fold tables
@dataclass
class ConditionTable:
    """Training compounds measured (QC-passed) at one condition, with Gram quantities."""

    key: tuple
    names: list
    klass: np.ndarray
    detected: np.ndarray
    Y: np.ndarray
    G: np.ndarray
    s: np.ndarray
    total: float                     # |S|^2
    S: np.ndarray                    # sum of rows


@dataclass
class FoldTables:
    fold: int
    tier: str
    tables: dict                     # key -> ConditionTable
    classes: tuple
    loo_scores: dict = field(default_factory=dict)   # key -> (n x C) class-max LOO similarity of each training compound


def build_fold_tables(data: Data, tier: Tier, fold: int, detected: np.ndarray, *, label_map: dict | None = None) -> FoldTables:
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    classes = tier.pool
    tables = {}
    for key in tier.keys:
        rows = [(c, r) for c, r in data.index.get(key, {}).items()
                if comp.fold.get(c) != fold and qc_passed(data, r)]
        names = [c for c, _ in rows]
        Y = data.shift[[r for _, r in rows]].astype(np.float64)
        G = Y @ Y.T
        S = Y.sum(0)
        s = G.sum(1)
        labels = label_map or {}
        kl = np.array([labels.get(c, comp.klass.get(c)) for c in names], dtype=object)
        tables[key] = ConditionTable(key, names, kl, detected[[r for _, r in rows]], Y, G, s, float(s.sum()), S)
    ft = FoldTables(fold, tier.name, tables, classes)
    for key, t in tables.items():
        ft.loo_scores[key] = _loo_class_scores(t, classes)
    return ft


def _loo_class_scores(t: ConditionTable, classes: tuple) -> np.ndarray:
    """For every training compound c: per class, the max projected cosine to that class's detected
    templates other than c, with the shared axis recomputed without c."""
    n = len(t.names)
    out = np.full((n, len(classes)), -np.inf)
    if n < 2:
        return out
    diag = np.diag(t.G)
    member = {k: np.flatnonzero((t.klass == k) & t.detected) for k in classes}
    for c in range(n):
        d = t.s - t.G[:, c]
        norm2 = t.total - 2 * t.s[c] + t.G[c, c]
        if norm2 <= 1e-12:
            continue
        perp_norm = np.sqrt(np.maximum(diag - d * d / norm2, 1e-12))
        row = (t.G[c] - d[c] * d / norm2) / (perp_norm[c] * perp_norm)
        for j, k in enumerate(classes):
            m = member[k][member[k] != c]
            if len(m):
                out[c, j] = row[m].max()
    return out


def heldout_class_scores(t: ConditionTable, y: np.ndarray, classes: tuple) -> np.ndarray:
    out = np.full(len(classes), -np.inf)
    if len(t.names) == 0 or t.total <= 1e-12:
        return out
    y = y.astype(np.float64)
    gy = t.Y @ y
    dy = float(y @ t.S)
    d = t.s
    perp_norm = np.sqrt(np.maximum(np.diag(t.G) - d * d / t.total, 1e-12))
    perp_y = math.sqrt(max(float(y @ y) - dy * dy / t.total, 1e-12))
    row = (gy - dy * d / t.total) / (perp_y * perp_norm)
    for j, k in enumerate(classes):
        m = np.flatnonzero((t.klass == k) & t.detected)
        if len(m):
            out[j] = row[m].max()
    return out


# ---------------------------------------------------------------------------------- the rule
def decide(detected: bool, scores: np.ndarray, a: int, b: int, n_measured: np.ndarray, n_templates: np.ndarray,
           floor: float, margin: float) -> str:
    """Outcome for contrast (class a, class b): eliminate_b, eliminate_a, ambiguous or undetected."""
    if not detected:
        return "undetected"
    sa, sb = scores[a], scores[b]

    def wins(x, y, sx, sy):
        if n_templates[x] == 0 or sx < floor:
            return False
        if n_templates[y] == 0:
            return n_measured[y] >= 2
        return sx - sy >= margin

    if wins(a, b, sa, sb):
        return "eliminate_b"
    if wins(b, a, sb, sa):
        return "eliminate_a"
    return "ambiguous"


def template_counts(t: ConditionTable, classes: tuple, exclude: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    keep = np.ones(len(t.names), bool)
    if exclude is not None:
        keep[exclude] = False
    measured = np.array([int(((t.klass == k) & keep).sum()) for k in classes])
    templates = np.array([int(((t.klass == k) & keep & t.detected).sum()) for k in classes])
    return measured, templates


def loo_outcomes(ft: FoldTables, key: tuple, floor: float, margin: float) -> dict:
    """Outcome of every training compound of a pool class against every other pool class."""
    cache = ft.__dict__.setdefault("_outcome_cache", {})
    if (key, floor, margin) not in cache:
        cache[(key, floor, margin)] = _loo_outcomes(ft, key, floor, margin)
    return cache[(key, floor, margin)]


def _loo_outcomes(ft: FoldTables, key: tuple, floor: float, margin: float) -> dict:
    t = ft.tables[key]
    classes = ft.classes
    out = {}
    for c in range(len(t.names)):
        if t.klass[c] not in classes:
            continue
        a = classes.index(t.klass[c])
        measured, templates = template_counts(t, classes, exclude=c)
        for b in range(len(classes)):
            if b == a:
                continue
            out[(t.names[c], classes[b])] = decide(bool(t.detected[c]), ft.loo_scores[key][c], a, b, measured, templates,
                                                   floor, margin)
    return out


def calibrate(ft: FoldTables, protocol: dict) -> dict:
    spec = protocol["validator"]["calibration"]
    best = None
    grid = []
    for floor in spec["floor_grid"]:
        for margin in spec["margin_grid"]:
            correct = wrong = pairs = detected = 0
            for key in ft.tables:
                for (_, _), outcome in loo_outcomes(ft, key, floor, margin).items():
                    pairs += 1
                    detected += outcome != "undetected"
                    correct += outcome == "eliminate_b"
                    wrong += outcome == "eliminate_a"
            rate = wrong / (correct + wrong) if correct + wrong else 0.0
            grid.append({"floor": floor, "margin": margin, "correct": correct, "wrong": wrong, "pairs": pairs,
                         "detected_pairs": detected, "wrong_among_eliminations": rate})
            if rate <= spec["maximum_wrong_elimination_rate"] and correct > 0:
                candidate = (correct, margin, floor)
                if best is None or candidate > best:
                    best = candidate
    if best is None:
        return {"floor": math.inf, "margin": math.inf, "eliminates": False, "grid": grid}
    return {"floor": best[2], "margin": best[1], "eliminates": True, "grid": grid}


def read_profile(ft: FoldTables, key: tuple, y: np.ndarray, detected: bool, a: str, b: str, params: dict) -> dict:
    t = ft.tables[key]
    classes = ft.classes
    scores = heldout_class_scores(t, y, classes)
    measured, templates = template_counts(t, classes)
    ia, ib = classes.index(a), classes.index(b)
    outcome = decide(detected, scores, ia, ib, measured, templates, params["floor"], params["margin"])
    return {"outcome": outcome, "score_a": float(scores[ia]), "score_b": float(scores[ib]),
            "templates_a": int(templates[ia]), "templates_b": int(templates[ib])}


# ---------------------------------------------------------------------------------- scenario cards
STEP1_CATEGORY = {"undetected": "undetected", "ambiguous": "detected_unresolved",
                  "eliminate_b": "detected_resolved", "eliminate_a": "detected_resolved"}


def card(ft: FoldTables, key: tuple, h1: str, h2: str, params: dict, *, minimum_references: int = 2,
         step1: tuple | None = None) -> dict:
    """Branch frequencies of the validator on measured references of each hypothesis at one condition.

    ``step1 = (key1, category)`` conditions each hypothesis's references on having behaved like the
    held-out compound at the first measured condition (dyn_ref): only references whose own
    leave-one-out outcome category at ``key1`` equals ``category`` are kept. If fewer than
    ``minimum_references`` remain, the unconditioned references are used and the card says so.
    """
    if key not in ft.tables:
        return {"served": False, "reason": "condition_not_in_menu"}
    outcomes = loo_outcomes(ft, key, params["floor"], params["margin"]) if params["eliminates"] else None
    first = (loo_outcomes(ft, step1[0], params["floor"], params["margin"])
             if step1 is not None and params["eliminates"] and step1[0] in ft.tables else None)
    t = ft.tables[key]
    branches = {}
    fallback = False
    for own, other, label in ((h1, h2, "H1"), (h2, h1, "H2")):
        refs = [c for c, k in zip(t.names, t.klass) if k == own]
        if step1 is not None:
            if first is None:
                fallback = True
            else:
                kept = [c for c in refs if STEP1_CATEGORY.get(first.get((c, other), ""), None) == step1[1]]
                if len(kept) >= minimum_references:
                    refs = kept
                else:
                    fallback = True
        if len(refs) < minimum_references:
            return {"served": False, "reason": f"too_few_references_at_condition:{own}:{len(refs)}"}
        if outcomes is None:
            counts = {"correct": 0, "wrong": 0, "ambiguous": 0, "undetected": len(refs)}
        else:
            values = [outcomes[(c, other)] for c in refs]
            counts = {"correct": values.count("eliminate_b"), "wrong": values.count("eliminate_a"),
                      "ambiguous": values.count("ambiguous"), "undetected": values.count("undetected")}
        n = len(refs)
        branches[label] = {"hypothesis": own, "references": n, "reference_compounds": refs,
                           **{f"p_{name}": count / n for name, count in counts.items()}}
    p_correct = 0.5 * (branches["H1"]["p_correct"] + branches["H2"]["p_correct"])
    p_wrong = 0.5 * (branches["H1"]["p_wrong"] + branches["H2"]["p_wrong"])
    # epistemic: a Jeffreys interval on the pooled correct-elimination probability from the reference counts
    n_total = branches["H1"]["references"] + branches["H2"]["references"]
    k = p_correct * n_total
    lo, hi = _jeffreys(k, n_total)
    return {"served": True, "key": list(key), "p_correct": p_correct, "p_wrong": p_wrong,
            "separation": p_correct - 2 * p_wrong, "branches": branches, "epistemic_interval": [lo, hi],
            "conditioned_fallback": fallback}


def _jeffreys(k: float, n: int, level: float = 0.9) -> tuple[float, float]:
    from scipy.stats import beta
    a, b = k + 0.5, n - k + 0.5
    return float(beta.ppf((1 - level) / 2, a, b)), float(beta.ppf(1 - (1 - level) / 2, a, b))


# ---------------------------------------------------------------------------------- repository evidence path
def evidence_update(state, contrast, action, key: tuple, reading: dict, h1: str, h2: str, *, qc: bool, agreement: float,
                    source: str):
    """Route one executed measurement through InterpretationTable and EvidenceState."""
    from agent.cases import MeasurementResult
    from maestro.models import EvidenceKind, EvidenceScope, FunctionalInterventionProfile
    from maestro.outcome import InterpretationTable, OutcomeRule

    line, t, dose = key
    outcome = reading["outcome"] if qc else "quality_failed"
    fields = {"eliminate_b": ("response_detected", "profile_matches:H1"),
              "eliminate_a": ("response_detected", "profile_matches:H2"),
              "ambiguous": ("response_detected", "profile_unresolved"),
              "undetected": ("no_detectable_response",),
              "quality_failed": ()}[outcome]
    result = MeasurementResult(
        action_identifier=action.identifier, statement=f"sci-RNA-seq3 pseudobulk shift, {line} {t:g} h {dose:g} nM",
        source_id=source, context_identifier=line, time_hours=t, independent_units=2 if qc else None,
        quality_passed=qc, conditions={"dose_nM": f"{dose:g}"},
        metrics={"replicate_agreement": f"{agreement:.4f}" if math.isfinite(agreement) else "nan",
                 "score_h1": f"{reading.get('score_a', float('nan')):.4f}",
                 "score_h2": f"{reading.get('score_b', float('nan')):.4f}"},
        evidence_kind=EvidenceKind.REAL_MEASUREMENT, interpretation_fields=fields,
        result_id=f"{source}:{action.identifier}")
    rules = (
        OutcomeRule("matches_h1", "profile_matches_h1", frozenset({"response_detected", "profile_matches:H1"}),
                    eliminates=frozenset({h2}), scope=EvidenceScope.MECHANISM_CONTRAST, requires_time_match=True,
                    minimum_independent_units=2,
                    boundary="A detected profile closer to H1's measured templates than to H2's removes H2 only."),
        OutcomeRule("matches_h2", "profile_matches_h2", frozenset({"response_detected", "profile_matches:H2"}),
                    eliminates=frozenset({h1}), scope=EvidenceScope.MECHANISM_CONTRAST, requires_time_match=True,
                    minimum_independent_units=2,
                    boundary="A detected profile closer to H2's measured templates than to H1's removes H1 only."),
        OutcomeRule("unresolved", "profile_unresolved", frozenset({"response_detected", "profile_unresolved"}),
                    scope=EvidenceScope.MEASUREMENT_FEASIBILITY,
                    boundary="A detected response that matches neither class better removes nothing."),
        OutcomeRule("no_response", "no_detectable_response", frozenset({"no_detectable_response"}),
                    scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
                    boundary="Absence cannot separate a failed perturbation from a mechanism inert at this condition."),
    )
    table = InterpretationTable(rules)
    profile = FunctionalInterventionProfile(mode="small_molecule", nominal_dose=dose, time_hours=t)
    interpretation = table.interpret(result, contrast, profile, action)
    return state.apply(interpretation, result), interpretation, outcome
