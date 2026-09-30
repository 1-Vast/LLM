"""Keep treatment-plate connectivity separate from shared control-calibration dependence."""
from __future__ import annotations

import pandas as pd

from research.identifiability_audit import round2 as R


def run(out):
    results = {}
    for dataset, tier in R.TASKS:
        task = dataset + "_" + tier
        p = out / "round1_replay" / task / "action_source.csv"
        source = pd.read_csv(p)
        columns = ["prep_plate_rep1", "prep_plate_rep2"] if dataset == "sciplex3" else ["inst_plate_names"]
        treatment, nplates = R.physical_components(source, columns)
        # The registered detection/control calibration is shared by this entire cell/time stratum.
        # These are dependency nodes, not additional physical plates or independent replicates.
        source["shared_control_calibration"] = "control:" + source.cell_line.astype(str) + ":" + source.time.astype(str)
        combined, nodes = R.physical_components(source, columns + ["shared_control_calibration"])
        results[task] = {"source_sha256": R.file_hash(p), "distinct_treatment_plates": nplates,
                         "treatment_plate_components": len(set(treatment.values())),
                         "shared_control_calibration_strata": source.shared_control_calibration.nunique(),
                         "components_including_shared_controls": len(set(combined.values())),
                         "ci95": None, "basis": "Round 1 control presence and registered cell/time vehicle-null "
                         "calibration. Control-stratum nodes denote dependence, not extra physical plates. "
                         "One combined cluster cannot estimate an independent plate/batch interval.",
                         "compound_component": combined}
    R.save(out / "physical_controls.json", results)


if __name__ == "__main__":
    run(R.OUT)
