"""Shared, testable logic for the sci-Plex pilot v2 repair (construction protocol v2).

File summary
- Path: tools/datasets/sciplex_v2_lib.py
- Purpose: pure functions for identity validation, two-intervention classification,
  correct absolute-effect counting, sample-sheet key parsing and stable-ID-first gene
  mapping, so the builder, QA and regression tests exercise the same logic.
- Run: imported by `build_sciplex_pilot_v2.py`, `qa_sciplex_pilot_v2.py` and
  `tests/test_sciplex_pilot_v2.py`.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Identity validation (protocol v2 section 1)
# ---------------------------------------------------------------------------

_MISSING_STRINGS = {"nan", "none", ""}


def is_missing(value: object) -> bool:
    """True for actual nulls and missing-like strings ('nan', 'None', '', whitespace).

    Applied to RAW obs values before any string coercion; a real string 'nan' from the
    source is treated as missing, and valid identities never become 'nan::nan'.
    """
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if value is pd.NA or (hasattr(pd, "isna") and pd.isna(value)):
        return True
    s = str(value).strip()
    return s.lower() in _MISSING_STRINGS


def classify_two_intervention(p1: object, p2: object) -> str:
    """Classify the complete two-intervention identity (protocol v2 section 2).

    Returns one of: vehicle_vehicle, agent1_only, agent2_only, combination,
    unresolved_identity. A nonempty second field alone never implies rescue semantics;
    classification is purely identity-based.
    """
    if is_missing(p1) or is_missing(p2):
        return "unresolved_identity"
    c1 = str(p1).strip() == "control"
    c2 = str(p2).strip() == "control"
    if c1 and c2:
        return "vehicle_vehicle"
    if not c1 and c2:
        return "agent1_only"
    if c1 and not c2:
        return "agent2_only"
    return "combination"


# ---------------------------------------------------------------------------
# Effect arithmetic (protocol v2 section 7 / review P1: abs arithmetic)
# ---------------------------------------------------------------------------


def abs_above(effect: np.ndarray, threshold: float) -> int:
    """Count feature rows with |effect| > threshold (both directions)."""
    effect = np.asarray(effect)
    return int(np.sum(np.abs(effect) > threshold))


# ---------------------------------------------------------------------------
# Feature-name suffix handling (protocol v2 section 6, rule F)
# ---------------------------------------------------------------------------

_SUFFIX_RE = re.compile(r":\d+$")


def strip_name_suffix(name: str) -> tuple[str, bool]:
    """Strip only a verified name-uniqueness suffix ':N'; return (base, stripped).

    Stripping never establishes that two columns are the same biological gene; callers
    must record collision groups and shared/differing stable IDs.
    """
    m = _SUFFIX_RE.search(name)
    if m:
        return name[: m.start()], True
    return name, False


# ---------------------------------------------------------------------------
# Sample-sheet key parsing (protocol v2 section 7)
# ---------------------------------------------------------------------------


def parse_sheet_key_s4(key: str) -> dict | None:
    """Parse a sciPlex4 hash-sheet key '{dose1}_{agent1}_{dose2}_{agent2}_{cell}_{plate}_{well}'.

    Returns None for keys that do not have the seven underscore fields (reported in the
    reconciliation ledger, never guessed).
    """
    parts = key.split("_")
    if len(parts) < 7:
        return None
    # agent tokens may themselves contain '_' only in principle; the observed sheet uses
    # single-token agents. If more than 7 fields appear, the split is ambiguous -> None.
    if len(parts) > 7:
        return None
    d1, a1, d2, a2, cell, plate, well = parts
    return {"dose1": d1, "agent1": a1, "dose2": d2, "agent2": a2,
            "cell": cell, "plate": plate, "well": well}


def parse_sheet_key_s2(key: str) -> dict | None:
    """Parse a sciPlex2 hash-sheet key '{agent}_{dose}_{well}'."""
    parts = key.split("_")
    if len(parts) != 3:
        return None
    agent, dose, well = parts
    return {"agent": agent, "dose": dose, "well": well}


# ---------------------------------------------------------------------------
# Gene identity mapping (protocol v2 section 6)
# ---------------------------------------------------------------------------

METHODS = ["stable_id", "stable_id_ambiguous", "symbol_approved",
           "symbol_prev_or_alias_unique", "symbol_alias_ambiguous", "unresolved"]


def _alias_targets(hgnc: pd.DataFrame) -> dict[str, list[str]]:
    """Map previous/alias symbols to the list of candidate approved symbols."""
    out: dict[str, list[str]] = {}
    for col in ("prev_symbol", "alias_symbol"):
        for _, row in hgnc[["symbol", col]].dropna().iterrows():
            for token in str(row[col]).split("|"):
                token = token.strip().strip('"')
                if token:
                    out.setdefault(token, [])
                    if row["symbol"] not in out[token]:
                        out[token].append(row["symbol"])
    return out


def build_gene_mapping(feature_names: list[str], ensembl_ids: list[str],
                       hgnc: pd.DataFrame) -> pd.DataFrame:
    """Row-level, stable-ID-first gene mapping on the ORIGINAL feature axis.

    Rules: stable ID primary; exact approved symbol as evidence; prev/alias with explicit
    ambiguity (never first-wins); stable-ID/symbol conflict resolved in favor of the
    stable ID and recorded; collision groups flagged with shared/differing Ensembl IDs.
    No columns are merged, summed or overwritten here.
    """
    approved = set(hgnc["symbol"].dropna())
    hgnc_by_eid: dict[str, list[str]] = {}
    for _, row in hgnc[["symbol", "ensembl_gene_id"]].dropna().iterrows():
        eid = str(row["ensembl_gene_id"]).strip()
        if eid and eid.lower() != "nan":
            hgnc_by_eid.setdefault(eid, [])
            if row["symbol"] not in hgnc_by_eid[eid]:
                hgnc_by_eid[eid].append(row["symbol"])
    alias_map = _alias_targets(hgnc)

    rows = []
    for i, (name, eid) in enumerate(zip(feature_names, ensembl_ids)):
        base, stripped = strip_name_suffix(str(name))
        eid = "" if is_missing(eid) else str(eid).strip()
        stable_cands = hgnc_by_eid.get(eid, []) if eid else []
        if base in approved:
            sym_cands, sym_class = [base], "approved"
        elif base in alias_map:
            sym_cands, sym_class = sorted(alias_map[base]), "alias"
        else:
            sym_cands, sym_class = [], "none"

        if len(stable_cands) == 1:
            method = "stable_id"
            target = stable_cands[0]
            ambiguous = False
            conflict = bool(sym_cands) and target not in sym_cands
        elif len(stable_cands) > 1:
            method = "stable_id_ambiguous"
            target = ""
            ambiguous = True
            conflict = False
        else:
            conflict = False
            if sym_class == "approved":
                method, target, ambiguous = "symbol_approved", base, False
            elif len(sym_cands) == 1:
                method, target, ambiguous = "symbol_prev_or_alias_unique", sym_cands[0], False
            elif len(sym_cands) > 1:
                method, target, ambiguous = "symbol_alias_ambiguous", "", True
            else:
                method, target, ambiguous = "unresolved", "", False

        rows.append({
            "feature_index": i,
            "feature_name": str(name),
            "ensembl_id": eid,
            "name_suffix_stripped": stripped,
            "symbol_lookup_name": base,
            "stable_id_candidates": "|".join(stable_cands),
            "symbol_candidates": "|".join(sym_cands),
            "symbol_evidence_class": sym_class,
            "mapping_method": method,
            "selected_hgnc_id": "",
            "selected_symbol": target,
            "ambiguity_status": "ambiguous" if ambiguous else "unambiguous",
            "conflict_status": ("stable_id_vs_symbol_resolved_stable_wins" if conflict
                                else "none"),
            "collision_group": "",
            "shared_ensembl_in_collision": "",
        })

    mp = pd.DataFrame(rows)
    hgnc_ids = dict(zip(hgnc["symbol"], hgnc["hgnc_id"].astype(str)))
    sel = mp["selected_symbol"] != ""
    mp.loc[sel, "selected_hgnc_id"] = mp.loc[sel, "selected_symbol"].map(hgnc_ids)

    # collision groups: same selected symbol across multiple feature rows
    counts = mp.loc[sel, "selected_symbol"].value_counts()
    dup_symbols = set(counts[counts > 1].index)
    for sym in dup_symbols:
        idx = mp.index[mp["selected_symbol"] == sym]
        eids = set(mp.loc[idx, "ensembl_id"]) - {""}
        shared = "yes" if len(eids) == 1 else ("no" if len(eids) > 1 else "unknown")
        mp.loc[idx, "collision_group"] = f"COLL::{sym}"
        mp.loc[idx, "shared_ensembl_in_collision"] = shared
    return mp


def mapping_stats(mp: pd.DataFrame) -> dict:
    """Reconciled mapping counts (protocol v2 section 6 reporting requirements)."""
    sel = mp["selected_symbol"] != ""
    methods = {m: int((mp["mapping_method"] == m).sum()) for m in METHODS}
    coll = mp[mp["collision_group"] != ""]
    groups = coll["collision_group"].nunique()
    shared_groups = (coll.drop_duplicates("collision_group")
                     ["shared_ensembl_in_collision"] == "yes").sum()
    return {
        "input_feature_rows": int(len(mp)),
        "unique_source_stable_ids": int(mp.loc[mp["ensembl_id"] != "", "ensembl_id"].nunique()),
        "mapped_rows": int(sel.sum()),
        "unique_target_ids": int(mp.loc[sel, "selected_symbol"].nunique()),
        "unresolved_rows": methods["unresolved"],
        "ambiguous_rows": int((mp["ambiguity_status"] == "ambiguous").sum()),
        "stable_id_vs_symbol_conflicts": int(
            (mp["conflict_status"] != "none").sum()),
        "collision_groups": int(groups),
        "collision_groups_with_shared_ensembl": int(shared_groups),
        "collision_groups_with_different_ensembl": int(groups - shared_groups),
        "mapping_method_counts_mutually_exclusive": methods,
    }
