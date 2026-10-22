"""Preserve unexpected released concentration/level identities without interpreting them."""
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"


def main():
    target = OUT / "CONCENTRATION_IDENTITY_DIAGNOSTICS.json"
    if target.exists():
        raise RuntimeError("Identity diagnostics already exist")
    rows = json.loads((OUT / "JOINED_IDENTITY_FLAGS.json").read_text(encoding="utf-8"))
    treated = [r for r in rows if r["DOSE_LEVEL"] != "Control"]
    zero = [r for r in treated if Decimal(r["DOSE"]) == 0]
    levels = defaultdict(set)
    for row in treated:
        levels[(row["COMPOUND_NAME"], str(Decimal(row["DOSE"]).normalize()), row["DOSE_UNIT"])].add(row["DOSE_LEVEL"])
    result = {"noncontrol_zero_dose_rows": len(zero),
              "noncontrol_zero_dose_compounds": len({r["COMPOUND_NAME"] for r in zero}),
              "noncontrol_zero_dose_level_conditions": len({(r["EXP_ID"], r["DOSE"], r["DOSE_UNIT"], r["DOSE_LEVEL"]) for r in zero}),
              "noncontrol_zero_dose_time_counts": dict(Counter(r["SACRIFICE_PERIOD"] for r in zero)),
              "concentrations_with_multiple_noncontrol_levels": [
                  {"COMPOUND_NAME": k[0], "canonical_dose": k[1], "DOSE_UNIT": k[2], "dose_levels": sorted(v)}
                  for k, v in levels.items() if len(v) > 1],
              "noncontrol_unit_counts": dict(Counter(r["DOSE_UNIT"] for r in treated)),
              "interpretation": "Released identity strings only; no imputation, unit conversion, nonzero-concentration certification, or endpoint-based exclusion"}
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
