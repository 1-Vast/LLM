"""The frozen external replay: eight feature arms and the decision-level comparators.

File summary
- Path: research/case_memory_integration/external_replay.py
- Purpose: execute the pre-registered evaluation of `research/case_memory_integration/PROTOCOL.md`
  on the untouched LINCS 2020 data pack: validator readings per protocol section 3, the eight
  frozen feature arms of section 4, forecast-level and decision-level metrics of section 5, and
  the unit-cluster bootstrap of the primary endpoint.
- Core points:
  - Reference readings and detection thresholds are fitted on reference blocks only, with the
    reference compound itself left out of its own centroid. Test-unit signatures are read once,
    at scoring time, by this frozen code.
  - Arm definitions are fixed here and were registered in the protocol; they are not tuned after
    the fact. `oracle` is clairvoyant and reported for headroom only.
  - The unseen stratum is exploratory (protocol section 8): no confirmatory claim is computed.
- Interfaces: `run_replay`, `load_results`, `ARM_NAMES`, `READING_CODES`
- Depends on: research/case_memory_integration/external_data.py (the hashed pack), numpy
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .external_data import CORE_CELL_LINES, ROOT, SEED, load_pack

READING_CODES = ("match_own", "match_decoy", "unresolved", "undetected")
ARM_NAMES = ("scalar", "signed_direction", "pathway_direction", "combined",
             "mechanism_prior_only", "case_memory_only", "full", "oracle")
MARGIN = 0.02
DETECTION_PERCENTILE = 5.0
DRAWS = 2000
OUT = ROOT / "outputs/case_memory_integration"


# -------------------------------------------------------------------------------- features
def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(a @ b / (na * nb))


def _pathway_vector(vec: np.ndarray, symbols: list[str], gene_sets: dict[str, list[str]],
                    set_names: list[str]) -> np.ndarray:
    pos = {g: i for i, g in enumerate(symbols)}
    out = np.zeros(len(set_names), dtype=np.float64)
    for j, name in enumerate(set_names):
        rows = [pos[g] for g in gene_sets[name] if g in pos]
        if rows:
            out[j] = vec[rows].sum() / np.sqrt(len(rows))
    return out


def _features(vec: np.ndarray, arm: str, symbols, gene_sets, set_names,
              pathway_cache: dict[int, np.ndarray]) -> np.ndarray:
    if arm in ("scalar", "mechanism_prior_only", "case_memory_only"):
        return np.zeros(1)
    key = id(vec)
    if arm == "signed_direction":
        return vec.astype(np.float64)
    if key not in pathway_cache:
        pathway_cache[key] = _pathway_vector(vec, symbols, gene_sets, set_names)
    if arm == "pathway_direction":
        return pathway_cache[key]
    return np.concatenate([vec.astype(np.float64), pathway_cache[key]])


# -------------------------------------------------------------------------------- validator
def _reading(vec: np.ndarray, centroid_own: np.ndarray, centroid_decoy: np.ndarray,
             threshold: float) -> int:
    if float(np.linalg.norm(vec)) < threshold:
        return 3
    own, decoy = _cos(vec, centroid_own), _cos(vec, centroid_decoy)
    if abs(own - decoy) < MARGIN:
        return 2
    return 0 if own > decoy else 1


def _reference_centric(pack, arrays, klass: str, cell: str, exclude: str | None = None) -> np.ndarray | None:
    members = [b for b, u in pack["units"].items()
               if not u["unseen"] and u["moa"] == klass and b != exclude
               and f"vec::{b}::{cell}" in arrays]
    if not members:
        return None
    return np.mean([arrays[f"vec::{b}::{cell}"] for b in members], axis=0)


# -------------------------------------------------------------------------------- replay
def run_replay(out_dir: Path | None = None) -> dict:
    """Execute the frozen replay and write `outputs/case_memory_integration/results.json`."""

    out_dir = out_dir or OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    pack, arrays = load_pack()
    pool = pack["pool"]
    symbols = pack["landmark_symbols"]
    gene_sets = pack["gene_sets"]
    set_names = sorted(gene_sets)
    units = pack["units"]
    reference = sorted(b for b, u in units.items() if not u["unseen"])
    test = sorted(b for b, u in units.items() if u["unseen"])
    rng = np.random.default_rng(SEED)

    # detection thresholds from reference norms only (protocol section 3)
    thresholds: dict[str, float] = {}
    for cell in CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        thresholds[cell] = float(np.percentile(norms, DETECTION_PERCENTILE)) if norms else 0.0

    # reference readings: every reference block at every available condition against every other
    # pool class, the block itself left out of its class centroid (leakage boundary, section 2)
    ref_readings: dict[tuple, int] = {}
    for b in reference:
        own = units[b]["moa"]
        for cell in units[b]["conditions"]:
            vec = arrays[f"vec::{b}::{cell}"]
            co = _reference_centric(pack, arrays, own, cell, exclude=b)
            if co is None:
                continue
            for decoy in pool:
                if decoy == own:
                    continue
                cd = _reference_centric(pack, arrays, decoy, cell)
                if cd is None:
                    continue
                ref_readings[(b, cell, decoy)] = _reading(vec, co, cd, thresholds[cell])

    # test items: (unit, condition, contrast) with the contrast order seeded
    items: list[dict] = []
    for b in test:
        own = units[b]["moa"]
        for cell in units[b]["conditions"]:
            contrasts = [d for d in pool if d != own]
            rng.shuffle(contrasts)
            for decoy in contrasts:
                items.append({"unit": b, "cell": cell, "own": own, "decoy": decoy})
    # realized codes for test items, read once, here, by the frozen code
    for item in items:
        vec = arrays[f"vec::{item['unit']}::{item['cell']}"]
        co = _reference_centric(pack, arrays, item["own"], item["cell"])
        cd = _reference_centric(pack, arrays, item["decoy"], item["cell"])
        item["code"] = _reading(vec, co, cd, thresholds[item["cell"]])

    # -------------------------------------------------------------------------------- arms
    pathway_cache: dict[int, np.ndarray] = {}

    def _own_class_codes(own: str, decoy: str, cell: str) -> list[tuple[str, int]]:
        """(reference block, reading code) pairs of class `own` against `decoy` at `cell`."""

        return [(b, code) for (b, c2, d2), code in ref_readings.items()
                if units[b]["moa"] == own and c2 == cell and d2 == decoy]

    def _pooled(codes: list[int]) -> np.ndarray:
        counts = np.full(4, 0.5)
        for code in codes:
            counts[code] += 1.0
        return counts / counts.sum()

    def forecast(item: dict, arm: str, swapped: bool = False) -> np.ndarray:
        """Frozen per-arm forecast of the reading-code distribution for one item."""

        own, decoy = (item["decoy"], item["own"]) if swapped else (item["own"], item["decoy"])
        cell = item["cell"]
        if arm == "oracle":
            out = np.full(4, 1e-9)
            out[item["code"]] = 1.0 - 3e-9
            return out / out.sum()
        all_codes = [code for (bb, cc, dd), code in ref_readings.items() if cc == cell]
        own_pairs = _own_class_codes(own, decoy, cell)
        if arm == "mechanism_prior_only":
            return _pooled(all_codes)
        if arm == "case_memory_only":
            return _pooled([code for (bb, _, _), code in ref_readings.items()
                            if units[bb]["moa"] == own])
        if arm == "scalar" or not own_pairs:
            return _pooled([code for _, code in own_pairs] or all_codes)
        vec = arrays[f"vec::{item['unit']}::{cell}"]
        fv = _features(vec, arm, symbols, gene_sets, set_names, pathway_cache)
        weights = np.array([
            max(0.0, _cos(fv, _features(arrays[f"vec::{b}::{cell}"], arm, symbols, gene_sets,
                                        set_names, pathway_cache)))
            for b, _ in own_pairs])
        if arm == "full":
            weights = weights * (len(own_pairs) / (len(own_pairs) + 2.0))
            if weights.max(initial=0.0) < 0.05:
                # domain shift: no positive-similarity precedent; shrink to the pooled memory
                pooled = _pooled([code for _, code in own_pairs])
                weighted = np.full(4, 1e-9)
                for w, (_, code) in zip(weights, own_pairs):
                    weighted[code] += w
                if weighted.sum() > 0:
                    return 0.5 * pooled + 0.5 * weighted / weighted.sum()
                return pooled
        if weights.sum() == 0.0:
            return _pooled([code for _, code in own_pairs])
        weighted = np.full(4, 0.5)
        for w, (_, code) in zip(weights, own_pairs):
            weighted[code] += w
        return weighted / weighted.sum()

    # forecast-level metrics
    item_records: list[dict] = []
    metrics: dict[str, dict] = {}
    for arm in ARM_NAMES:
        nll, brier, correct_dir, detected = 0.0, 0.0, 0, 0
        p_wrong, y_wrong = [], []
        discrimination = 0.0
        for item in items:
            p = forecast(item, arm)
            item_records.append({"arm": arm, "unit": item["unit"], "cell": item["cell"],
                                 "own": item["own"], "decoy": item["decoy"], "code": item["code"],
                                 "p": [round(float(x), 6) for x in p]})
            nll -= float(np.log(max(p[item["code"]], 1e-12)))
            pw = float(p[1])
            p_wrong.append(pw)
            y_wrong.append(1.0 if item["code"] == 1 else 0.0)
            brier += (pw - (1.0 if item["code"] == 1 else 0.0)) ** 2
            if item["code"] < 2:
                detected += 1
                correct_dir += int((p[0] > p[1]) == (item["code"] == 0))
            if arm != "oracle":
                p_swap = forecast(item, arm, swapped=True)
                discrimination += float(np.log(max(p[item["code"]], 1e-12))
                                        - np.log(max(p_swap[item["code"]], 1e-12)))
        p_arr = np.array(p_wrong)
        y_arr = np.array(y_wrong)
        # ECE over 10 support-aware bins
        ece = 0.0
        bins = np.linspace(0, 1, 11)
        for lo, hi in zip(bins[:-1], bins[1:]):
            mask = (p_arr >= lo) & (p_arr < hi)
            if mask.any():
                ece += mask.mean() * abs(p_arr[mask].mean() - y_arr[mask].mean())
        n = len(items)
        metrics[arm] = {
            "nll": nll / n, "brier_wrong_elimination": brier / n, "ece_wrong_elimination": ece,
            "directional_accuracy": (correct_dir / detected) if detected else None,
            "detected_items": detected,
            "discrimination_nats": (discrimination / n) if arm != "oracle" else None,
            "observed_wrong_elimination": float(y_arr.mean()),
            "forecast_wrong_elimination": float(p_arr.mean()),
        }

    # primary endpoint: paired NLL difference full - scalar, unit-cluster bootstrap
    def nll_by_unit(arm: str) -> dict[str, float]:
        per: dict[str, list[float]] = {}
        for item in items:
            p = forecast(item, arm)
            per.setdefault(item["unit"], []).append(-float(np.log(max(p[item["code"]], 1e-12))))
        return {u: float(np.mean(v)) for u, v in per.items()}

    full_nll, scalar_nll = nll_by_unit("full"), nll_by_unit("scalar")
    units_list = sorted(full_nll)
    diffs = np.array([full_nll[u] - scalar_nll[u] for u in units_list])
    boot = []
    for _ in range(DRAWS):
        idx = rng.integers(0, len(units_list), len(units_list))
        boot.append(float(diffs[idx].mean()))
    primary = {"estimate": float(diffs.mean()),
               "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
               "units": len(units_list), "items": len(items), "draws": DRAWS, "seed": SEED}

    # decision level: episodes are (unit, contrast); actions are the unit's conditions
    decisions: dict[str, dict] = {}
    planner_arms = ("scalar", "combined", "full")
    arm_rows: dict[str, dict[str, float]] = {}

    def episode_action(unit: str, arm: str) -> str | None:
        best, best_score = None, -np.inf
        for cell in units[unit]["conditions"]:
            item = {"unit": unit, "cell": cell, "own": units[unit]["moa"], "decoy": None,
                    "code": None}
            # score the condition by forecast separation between match and non-match codes
            own = units[unit]["moa"]
            decoys = [d for d in pool if d != own]
            sep = 0.0
            for d in decoys:
                it = {"unit": unit, "cell": cell, "own": own, "decoy": d, "code": None}
                p = forecast(it, arm)
                sep += float(np.log(max(p[0], 1e-9)) - np.log(max(p[1], 1e-9)))
            if sep > best_score:
                best, best_score = cell, sep
        return best

    decision_arms = ("fixed", "random_legal", "oracle") + tuple(f"planner_{a}" for a in planner_arms)
    for arm in decision_arms:
        correct = wrong = undetermined = deferred = measurements = 0
        for b in test:
            own = units[b]["moa"]
            conditions = units[b]["conditions"]
            if not conditions:
                deferred += 1
                continue
            if arm == "fixed":
                cell = next((c for c in CORE_CELL_LINES if c in conditions), conditions[0])
            elif arm == "random_legal":
                cell = conditions[rng.integers(0, len(conditions))]
            elif arm == "oracle":
                cell = next((c for c in conditions
                             if all(_reading(arrays[f"vec::{b}::{c}"],
                                             _reference_centric(pack, arrays, own, c),
                                             _reference_centric(pack, arrays, d, c),
                                             thresholds[c]) == 0 for d in pool if d != own)), None)
                if cell is None:
                    deferred += 1
                    continue
            else:
                cell = episode_action(b, arm.split("_", 1)[1])
            decoy = sorted(d for d in pool if d != own)[0]
            code = _reading(arrays[f"vec::{b}::{cell}"], _reference_centric(pack, arrays, own, cell),
                            _reference_centric(pack, arrays, decoy, cell), thresholds[cell])
            measurements += 1
            if code == 0:
                correct += 1
            elif code == 1:
                wrong += 1
            elif code == 2:
                undetermined += 1
            else:
                deferred += 1
        n = len(test)
        decisions[arm] = {"correct": correct / n, "wrong": wrong / n,
                          "undetermined": undetermined / n, "deferred": deferred / n,
                          "measurements": measurements / n, "episodes": n}
    headroom = decisions["oracle"]["correct"] - decisions["fixed"]["correct"]

    results = {
        "protocol": "research/case_memory_integration/PROTOCOL.md",
        "pack_version": pack["version"],
        "seed": SEED,
        "population": {"pool": pool, "reference_blocks": len(reference), "test_blocks": len(test),
                       "forecast_items": len(items)},
        "exploratory": True,
        "exploratory_reason": ("the unseen stratum (26 pool blocks; 93 unseen core-scope blocks) "
                               "does not meet the confirmatory population minimum of protocol v2; "
                               "all statements are stratum-level or descriptive"),
        "thresholds": thresholds,
        "forecast_metrics": metrics,
        "primary_endpoint_full_minus_scalar_nll": primary,
        "decision_metrics": decisions,
        "oracle_headroom_correct": headroom,
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    with open(out_dir / "forecast_items.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for record in item_records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    return results


def load_results() -> dict:
    return json.loads((OUT / "results.json").read_text(encoding="utf-8"))
