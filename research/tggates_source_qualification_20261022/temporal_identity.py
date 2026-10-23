"""Count shared time menus from released identity rows; no viability/arrays."""
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_source_qualification"


def main():
    target = OUT / "TEMPORAL_IDENTITY.json"
    assert not target.exists()
    rows = pd.read_json(OUT / "HUMAN_CELL_IDENTITIES.json", dtype=False)
    treated = rows[rows["DOSE_LEVEL"].ne("Control")].copy()
    def canonical(value):
        try:
            return str(Decimal(str(value)).normalize())
        except InvalidOperation:
            return f"UNPARSED:{value}"
    treated["canonical_dose"] = treated["DOSE"].map(canonical)
    time_sets = treated.groupby(["COMPOUND_NAME", "canonical_dose", "DOSE_UNIT"])["SACRIFICE_PERIOD"].agg(set)
    full = {"2 hr", "8 hr", "24 hr"}
    counts = {"|".join(sorted(k)): int(v) for k, v in time_sets.map(lambda x: tuple(sorted(x))).value_counts().items()}
    times_per_compound = treated.groupby("COMPOUND_NAME")["SACRIFICE_PERIOD"].agg(set)
    matched = time_sets.map(lambda x: full.issubset(x))
    metadata = {"noncontrol_samples": len(treated), "compound_dose_unit_conditions": len(time_sets),
                "time_set_counts": counts, "same_compound_dose_unit_all_three_times": int(matched.sum()),
                "compounds_with_all_three_times_any_dose": int(times_per_compound.map(lambda x: full.issubset(x)).sum()),
                "compounds_with_some_noncontrol_records": len(times_per_compound),
                "noncontrol_unparsed_dose_rows": int(treated["canonical_dose"].str.startswith("UNPARSED:").sum()),
                "noncontrol_dose_unit_counts": treated["DOSE_UNIT"].value_counts().to_dict(),
                "interpretation": "Temporal condition overlap only. No lot/source/culture mapping; destructive array samples are not longitudinal same-cell trajectories.",
                "DNA_LDH_or_expression_values_read": False}
    target.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
