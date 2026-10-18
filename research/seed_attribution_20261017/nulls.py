"""The fixed collection of scope-gate correspondence permutations (matched null libraries).

File summary
- Path: research/seed_attribution_20261017/nulls.py
- Purpose: arm E of the attribution study. Each null library keeps the seed library's capacity (10
  programs, one gate each, the same scope list, the same multiset of gates, the same shrinkage) and
  changes only WHICH scope is paired with WHICH gate. A null therefore removes the biological
  correspondence and nothing else.
- Rules (frozen before any null is evaluated; nothing is chosen after seeing performance):
  - a null is a permutation of the seed gates over the seed scope slots;
  - no (scope, gate) pair of the seed library may reappear, and no pair may repeat inside a null;
  - every null program passes the same structural rules the development bench applies to an added
    program (scope: >= 5 source drugs from >= 2 structure groups; gate: >= 5 positive and >= 5 negative
    source lines, positives from >= 2 lineages; interaction identifiable on the source observation
    pattern);
  - support match: the number of OBSERVED source cells in the scope x gate-positive quadrants, summed
    over the library, lies within +-20% of the seed library's. Outcome VALUES are never read here, only
    which cells exist.
  - no sign flips: the loading of each program is learned from data in every arm; a permutation changes
    pairing only.
- Draw: numpy ``default_rng(SEED)`` permutations of range(10) in draw order; the first N_NULLS that pass
  are kept; the rejection counts by reason are recorded. The set is never edited, reordered or reduced.
- Output: NULLS.json (write-once). Run: python nulls.py
- Limitation recorded: a permuted pairing can be biologically informative by accident (for example a
  PI3K scope with a PTEN gate). The null then understates the value of correspondence. The report says so.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corrected as C  # noqa: E402
from revise import SEED_LIBRARY, identifiable  # noqa: E402
from vc import LineContext, parse_state, scope_mask  # noqa: E402

SEED = 20261017
N_NULLS = 20
TOLERANCE = 0.20
OUT = HERE / "NULLS.json"


def program_stats(dom, scope, gate_state, drows, src_lines, observed, structure):
    sm = scope_mask(scope, dom.df, drows)
    ctx = LineContext(dom.lf, src_lines, {}, np.zeros(len(src_lines)))
    v = ctx.state(parse_state(gate_state))
    pos = v > 0.5
    lin = dom.lines.primary_tissue.to_numpy()[src_lines]
    reasons = []
    if sm.sum() < 5 or len(set(structure[drows[sm]])) < 2:
        reasons.append("SCOPE_TOO_NARROW")
    if pos.sum() < 5 or len(set(lin[pos])) < 2:
        reasons.append("GATE_TOO_RARE")
    if (~pos).sum() < 5:
        reasons.append("GATE_TOO_COMMON")
    if not reasons and not identifiable(observed, sm, v):
        reasons.append("INTERACTION_NOT_IDENTIFIABLE")
    quadrant = int(observed[np.ix_(np.flatnonzero(sm), np.flatnonzero(pos))].sum())
    return {"scope_drugs": int(sm.sum()), "gate_positive_lines": int(pos.sum()), "observed_quadrant_cells": quadrant,
            "refusals": reasons}


def main():
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; the null collection is write-once")
    dom = C.CorrectedDomain()
    drows = np.flatnonzero(dom.src_drug)
    src_lines = np.flatnonzero(dom.src_line)
    observed = np.isfinite(dom.Ymean[np.ix_(drows, src_lines)])
    structure = dom.drugs.structure_group.to_numpy()
    scopes = [s for s, _ in SEED_LIBRARY]
    gates = [g for _, g in SEED_LIBRARY]
    seed_pairs = set(SEED_LIBRARY)
    seed_stats = [program_stats(dom, s, g, drows, src_lines, observed, structure) for s, g in SEED_LIBRARY]
    seed_total = sum(p["observed_quadrant_cells"] for p in seed_stats)
    assert all(not p["refusals"] for p in seed_stats), "the seed library must itself be admissible"

    rng = np.random.default_rng(SEED)
    kept, rejected = [], {"seed_pair_reused": 0, "duplicate_pair": 0, "inadmissible": 0, "support_outside_tolerance": 0,
                          "identity_or_repeat": 0}
    seen = set()
    drawn = 0
    while len(kept) < N_NULLS and drawn < 200000:
        perm = tuple(int(i) for i in rng.permutation(len(gates)))
        drawn += 1
        if perm in seen:
            rejected["identity_or_repeat"] += 1
            continue
        seen.add(perm)
        pairs = [(scopes[i], gates[perm[i]]) for i in range(len(scopes))]
        if any(p in seed_pairs for p in pairs):
            rejected["seed_pair_reused"] += 1
            continue
        if len(set(pairs)) != len(pairs):
            rejected["duplicate_pair"] += 1
            continue
        stats = [program_stats(dom, s, g, drows, src_lines, observed, structure) for s, g in pairs]
        if any(st["refusals"] for st in stats):
            rejected["inadmissible"] += 1
            continue
        total = sum(st["observed_quadrant_cells"] for st in stats)
        if abs(total / seed_total - 1.0) > TOLERANCE:
            rejected["support_outside_tolerance"] += 1
            continue
        kept.append({"index": len(kept), "draw": drawn, "permutation": list(perm),
                     "programs": [{"scope": s, "state": g, **st} for (s, g), st in zip(pairs, stats)],
                     "total_observed_quadrant_cells": total, "support_ratio_to_seed": round(total / seed_total, 4)})
    if len(kept) < N_NULLS:
        raise SystemExit(f"only {len(kept)} admissible permutations in {drawn} draws")
    out = {"seed": SEED, "n_nulls": N_NULLS, "tolerance": TOLERANCE, "draws": drawn, "rejections": rejected,
           "seed_library": [{"scope": s, "state": g, **st} for (s, g), st in zip(SEED_LIBRARY, seed_stats)],
           "seed_total_observed_quadrant_cells": seed_total, "nulls": kept,
           "rules": "permutation of seed gates over seed scope slots; no seed pair reused; per-program structural admissibility; "
                    "total observed-quadrant support within +-20% of the seed library; first N_NULLS in draw order; no sign flips"}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("written", OUT.name, "nulls", len(kept), "draws", drawn, rejected)
    print("support ratios", [k["support_ratio_to_seed"] for k in kept])


if __name__ == "__main__":
    main()
