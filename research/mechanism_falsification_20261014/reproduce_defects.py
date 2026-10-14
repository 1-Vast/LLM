"""Reproduce the suspected scientific-decision contract defects on the *historical* modules.

Reads only miniature in-memory fixtures. Prints one JSON line per defect. The historical
modules are imported unchanged; nothing is written.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from maestro.case_memory import ScientificMeasurementStatus as S
from maestro.decision_review import EvidenceItem, Explanation, Prediction, admit, review
from maestro.models import EvidenceKind as K

CTX = "assay:A"
EXPL = (Explanation("TARGET", "engages the target", (Prediction("engagement_z", "<=", -2.0),
                                                      Prediction("rescue_fraction", ">=", 0.5)), progression=True),
        Explanation("OFFTARGET", "acts off target", (Prediction("engagement_z", ">", -1.0),)))


def item(obs, value, kind=K.REAL_MEASUREMENT, status=S.QUALIFIED, sha="0" * 64, source="x.csv"):
    return EvidenceItem(obs, value, kind, status, CTX, source, sha)


out = {}
d = review("c", EXPL, [], context=CTX, funded=True, no_signal=True)
out["D1_unauthenticated_no_go"] = {"evidence_supplied": 0, "status": d.status.value, "reasons": d.reasons}
d = review("c", EXPL, [item("engagement_z", -3.0)], context=CTX, funded=True)
out["D2_premature_go"] = {"status": d.status.value, "reasons": d.reasons,
                          "limitations": d.limitations, "untested_required": "rescue_fraction >= 0.5"}
a = item("engagement_z", -3.0, sha="f" * 64, source="nonexistent_file.csv")
out["D3_unauthenticated_digest_admitted"] = {"admit": admit(a, CTX), "source_exists": Path("nonexistent_file.csv").exists()}
d = review("c", EXPL, [item("engagement_z", -3.0, sha="a" * 64), item("engagement_z", -2.5, sha="b" * 64)],
           context=CTX, funded=True)
out["D3b_independent_flag_not_consulted"] = {"independent_flag_values": [True, True],
                                             "distinct_digests_for_one_upstream_run": 2, "status": d.status.value}
d = review("c", EXPL, [item("engagement_z", -3.0, kind=K.DERIVED_ANALYSIS)], context=CTX, funded=True)
out["D3c_derived_without_lineage"] = {"status": d.status.value, "note": "a DERIVED_ANALYSIS needs no parent; a prediction can be relabelled as one"}
print(json.dumps(out, indent=1, default=str))
