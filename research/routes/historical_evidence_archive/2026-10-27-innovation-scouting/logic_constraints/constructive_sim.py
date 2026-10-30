# R198-A2v3 constructive simulator (DESIGN VERSION; DO NOT RUN IN THIS ROUND)
# -----------------------------------------------------------------------------
# Status: written for freeze; NOT executed. This file is listed in the freeze
# checklist and its SHA256 is recorded in record_v3.md / usage_v3.json.
# Running it requires an explicit --confirm-run flag AND a frozen protocol; this
# round explicitly forbids running simulators/effects.
#
# Purpose: implement the pre-registered design of spec_v3.md §4 / protocol_draft_v3.md §3:
#   - metadata-only world generator (dimensions from folds.json; no response values)
#   - injections I (nuisance shift), II (relation flip in 5 of 8 cell groups), III (observable
#     but unmodeled BARCODE-derived state z), null
#   - K_A2 classifier with pre-registered rules and abstention accounting
#   - four endpoints E1..E4 with same-unit delta_min and MDE simulation plan
#   - budget table k in {6,12,20,24,36}
# The generator never reads response columns of the GDSC table; it only uses the
# design artifacts (folds.json) and pre-registered parameters.
import argparse, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEED_BASE = 20261027
SIGMAS = (0.5, 1.0, 2.0)
DELTAS = (1.0, 2.0)  # in units of sigma
K_GRID = (6, 12, 20, 24, 36)
DELTA_MIN = {"E1": 0.30, "E2": 0.20, "E3": 0.05, "E4": 0.10}  # same-unit as MDE (accuracy/rate difference)
N_WORLDS_PER_CLASS = 24
N_BATCHES_MDE = 1000
CLASSES = ("I", "II", "III", "null")


def load_design(path=None):
    """Load folds.json design artifact (metadata-derived; no response values)."""
    p = path or os.path.join(BASE, "folds.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def build_cell_groups(design):
    """8 pre-registered cell groups (from folds.json cell_groups_8)."""
    return {k: list(v) for k, v in design["cell_groups_8"].items()}


def make_world(design, cls, sigma, delta, seed):
    """Return a world specification dict (no response values; synthetic generator params only).

    y = b_cell + b_pair + b_dose + g_group + h_state*z + eps
    z = BARCODE-derived 2-level observable metadata state, NOT used by model/relations.
    """
    return {"class": cls, "sigma": sigma, "delta": delta, "seed": seed,
             "groups": build_cell_groups(design),
             "injection": {"I": "nuisance_shift", "II": "relation_flip_5of8_groups",
                           "III": "observable_unmodeled_state", "null": "none"}[cls]}


def k_allocation(k):
    """Pre-registered explicit unit allocation and reuse rules (protocol_v3 §3.4)."""
    table = {
        6: {"in": 3, "out": 3, "state_per_stratum": 3, "can_judge": ["I"]},
        12: {"in": 6, "out": 6, "state_per_stratum": 3, "can_judge": ["I", "III"]},
        20: {"in": 10, "out": 10, "state_per_stratum": 5, "can_judge": ["I", "II", "III"]},
        24: {"in": 10, "out": 10, "state_per_stratum": 5, "reserve": 4, "can_judge": ["I", "II"]},
        36: {"in": 10, "out": 10, "state_per_stratum": 5, "confirm_batch": 16,
             "confirm_in_out": 8, "can_judge": ["I", "II", "III"], "confirm_is_stability_only": True},
    }
    if k not in table:
        raise ValueError(f"k must be in {sorted(table)}")
    return table[k]


def classify(batch, world, k):
    """K_A2 pre-registered classifier skeleton (to be implemented at freeze; design stub).

    Returns one of: 'I', 'II', 'III', 'null_ok', 'unresolvable' plus reason.
    Rule 1: nuisance scalar refit -> r_I <= q_0.10(null) and C2' violation rate <= 0.05
    Rule 2: C2' violation significant AND in-out consistency gap >= 0.20 with >=10 units
            each AND >=5 independent cell-group sign flips -> II
    Rule 3: residual structure statistic significant AND a candidate state (<=6 candidates,
            max-statistic permutation) passes corrected threshold -> III (identified_state)
    Rule 4: else unresolvable.
    """
    return {"decision": None, "reason": "DESIGN_STUB_NOT_IMPLEMENTED"}


def endpoints(predictions, truths):
    """E1..E4 with pre-registered abstention accounting (protocol_v3 §3.3).

    E1/E2: denominator = ALL non-null worlds; abstention counts as ERROR.
    E3: null false-class rate; abstention on null counts as NO false class; null resolved rate <=0.50 (descriptive cap).
    E4: unresolvable rate over non-null worlds <= 0.10; E4b per-class resolved rate >= 0.85.
    MDE (per endpoint) = minimal detectable accuracy/rate difference at 80% power (same units as DELTA_MIN).
    """
    raise NotImplementedError("DESIGN_STUB: implement at freeze; not run this round")


def mde_plan():
    """Budget plan for the freeze-time MDE simulation (not executed this round)."""
    return {
        "worlds_per_class": N_WORLDS_PER_CLASS,
        "classes": list(CLASSES),
        "sigma_grid": list(SIGMAS),
        "delta_grid": list(DELTAS),
        "worlds_total": N_WORLDS_PER_CLASS * len(CLASSES),
        "k_grid": list(K_GRID),
        "batches_mde": N_BATCHES_MDE,
        "classifier_calls_estimate": N_BATCHES_MDE * len(K_GRID) * len(CLASSES),
        "estimated_runtime_min": "<=5 (CPU; hard cap 30)",
        "required": "for each endpoint and k: MDE <= DELTA_MIN[endpoint]; else design_uninformative",
    }


def main(argv):
    ap = argparse.ArgumentParser(description="A2v3 constructive simulator (DESIGN VERSION; DO NOT RUN THIS ROUND)")
    ap.add_argument("--confirm-run", action="store_true",
                    help="required to run; forbidden in R198-A2v3 (design-only round)")
    ap.add_argument("--plan", action="store_true", help="print design plan only")
    args = ap.parse_args(argv)
    if not args.confirm_run:
        print("REFUSING TO RUN: design-only round. Use --confirm-run only after protocol freeze.")
        print(json.dumps({"k_allocation": {str(k): k_allocation(k) for k in K_GRID},
                          "mde_plan": mde_plan(), "delta_min": DELTA_MIN}, ensure_ascii=False, indent=1))
        return 0
    raise SystemExit("--confirm-run is not implemented in the design version; implement at freeze.")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
