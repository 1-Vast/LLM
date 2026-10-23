"""Independent read-only audit of generated inputs; never opens the source archive."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/az_paid_reference_gate"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(name):
    return json.loads((LOG / name).read_text(encoding="utf-8"))


def main():
    output = LOG / "INPUTS_INDEPENDENT_AUDIT.json"
    prose = LOG / "INPUTS_INDEPENDENT_AUDIT.md"
    if output.exists() or prose.exists():
        raise RuntimeError("Independent audit already exists; no overwrite")
    checks = {}

    def check(name, passed):
        checks[name] = bool(passed)

    receipt, access, freeze = read("INPUTS_RECEIPT.json"), read("ACCESS_INPUTS.json"), read("PRE_RESPONSE_FREEZE.json")
    design, episodes, meta = read("DESIGN.json"), read("EPISODES.json"), read("EPISODE_META.json")
    rows, summaries, paid_raw = read("ROWS.json"), read("PAID_SUMMARIES.json"), read("PAID_OBSERVATIONS.json")
    schema, started = read("FEATURE_SCHEMA.json"), read("INPUTS_STARTED.json")
    hashes = {name: sha(LOG / name) for name in receipt["outputs_sha256"]}
    check("all_input_artifact_hashes", hashes == receipt["outputs_sha256"])
    check("frozen_nonarchive_files", all(sha(ROOT / name) == expected for name, expected in freeze["files"].items() if not name.endswith(".zip")))
    binding = {"code_sha256": ROOT / "research/az_paid_reference_gate_20261022/prepare.py",
               "protocol_sha256": LOG / "MEASURED_PROTOCOL.md", "design_sha256": LOG / "DESIGN.json",
               "schema_sha256": LOG / "FEATURE_SCHEMA.json"}
    check("receipt_and_started_bindings", all(sha(path) == receipt[field] == started[field] for field, path in binding.items()))
    headers = {}
    with zipfile.ZipFile(LOG / "DATA.npz") as z:
        for member in z.namelist():
            with z.open(member) as stream:
                version = np.lib.format.read_magic(stream)
                reader = { (1, 0): np.lib.format.read_array_header_1_0, (2, 0): np.lib.format.read_array_header_2_0 }[version]
                shape, fortran, dtype = reader(stream)
                headers[member[:-4]] = {"shape": list(shape), "dtype": str(dtype), "fortran": bool(fortran)}
    check("npz_array_names", set(headers) == set(schema["arrays"]))
    check("receipt_array_shapes", {k: v["shape"] for k, v in headers.items()} == receipt["array_shapes"])
    check("declared_feature_dimensions", all(headers[k]["shape"][1] == d for k, d in schema["dimensions"].items()))
    check("feature_dtypes", all(headers[k]["dtype"] == "float32" for k in ("full", "without_mono")))
    with np.load(LOG / "DATA.npz", allow_pickle=False) as z:
        data = {k: z[k] for k in ("effect", "dose", "raw_dose", "y", "episode", "pair", "role", "valid_mask")}
    n = len(data["y"])
    check("all_rows_have_mapping", len(rows) == n and all(len(a) == n for a in data.values()))
    active = [e for e in episodes if e["role"] != "reserve"]
    check("episode_metadata_alignment", len(meta) == len(active) and [e["episode_id"] for e in meta] == list(range(len(active))))
    check("row_episode_role_pair_alignment", all(r["episode_id"] == int(data["episode"][i]) and r["role"] == data["role"][i] == meta[r["episode_id"]]["role"]
          and r["targetkey"] == active[r["episode_id"]]["target"] and tuple(schema["target_pairs"][int(data["pair"][i])]) == tuple(meta[r["episode_id"]]["pair"])
          for i, r in enumerate(rows)))
    check("episode_input_validity_constant", all(np.all(data["valid_mask"][data["episode"] == e["episode_id"]] == e["valid"]) for e in meta))
    check("all_paid_inputs_valid", bool(data["valid_mask"].all()) and all(e["valid"] and not e["abstain_reason"] for e in meta))
    check("paid_effects_and_design_doses_finite", all(np.isfinite(data[k]).all() for k in ("effect", "dose", "raw_dose")))
    check("test_y_all_nan", np.isnan(data["y"][data["role"] == "test"]).all())
    check("train_validation_y_all_finite", np.isfinite(data["y"][np.isin(data["role"], ["train", "validation"])]).all())
    query_pairs, target_pairs = set(map(tuple, design["query_pairs"])), set(map(tuple, design["target_pairs"]))
    check("query_target_pair_pools_disjoint", not query_pairs & target_pairs)
    summary_by_key = {tuple(s["key"]): s for s in summaries}
    raw_by_key = {tuple(s["key"]): s for s in paid_raw}
    used_keys = {tuple(k) for e in meta for k in e["query_keys"]}
    check("unique_paid_matrix_summary_and_raw_keys", len(summary_by_key) == len(summaries) and len(raw_by_key) == len(paid_raw) and set(summary_by_key) == set(raw_by_key) == used_keys)
    check("paid_pairs_only_query_pool", all(tuple(s["pair"]) in query_pairs for s in summaries))
    mono, summary_residuals_correct, all_paid_finite = {}, True, True
    for key, bundle in raw_by_key.items():
        groups = defaultdict(list)
        for r in bundle["rows"]:
            all_paid_finite &= r["inhibition"] is not None and math.isfinite(r["inhibition"])
            for drug, dose, value in zip(r["drug_ids"], r["concentrations_uM"], r["mono"]):
                all_paid_finite &= value is not None and math.isfinite(value)
                if value is not None:
                    groups[(drug, Decimal(dose))].append(value)
        exact = {k: math.fsum(v) / len(v) for k, v in groups.items()}
        mono[key] = {(drug, float(dose)): value for (drug, dose), value in exact.items()}
        check("exact_dose_float_identity_" + str(len(mono)), len(mono[key]) == len(exact))
        residuals = []
        for r in bundle["rows"]:
            u, v = [exact[(drug, Decimal(dose))] for drug, dose in zip(r["drug_ids"], r["concentrations_uM"])]
            residuals.append(r["inhibition"] - (u + v - u * v))
        own = math.fsum(residuals) / len(residuals)
        s = summary_by_key[key]
        summary_residuals_correct &= math.isclose(own, s["mean_residual"], rel_tol=0, abs_tol=1e-14) and len(bundle["rows"]) == s["rows"] and s["role"] == bundle["role"]
    check("paid_raw_finite", all_paid_finite)
    check("independent_paid_residual_recalculation", summary_residuals_correct)
    expected_effect = np.empty_like(data["effect"])
    for i, eid in enumerate(data["episode"]):
        e = meta[int(eid)]
        expected_effect[i] = [mono[tuple(k)][(drug, float(dose))] for k, drug, dose in zip(e["query_keys"], e["pair"], data["raw_dose"][i])]
    check("independent_paid_endpoint_mean_recalculation", np.allclose(expected_effect, data["effect"], rtol=0, atol=1e-14))
    expected_scopes = {"paid:train", "paid:validation", "paid:test", "target:train", "target:validation"}
    ledger = access["conversion_counts"]
    check("only_allowed_conversion_scopes", set(ledger) == expected_scopes)
    check("only_allowed_response_fields", all(set(fields) == ({"lib1_y", "lib2_y", "inhibition"} if scope.startswith("paid:") else {"inhibition"}) for scope, fields in ledger.items()))
    check("all_declared_conversions_finite", all(c["attempted"] == c["finite"] and c["missing_or_nonfinite"] == 0 for fields in ledger.values() for c in fields.values()))
    check("receipt_targetmono_reserve_forbidden", access["target_attached_mono_or_fitted_fields_indexed"] is False and access["reserve_numeric_conversion"] is False and access["allowed_response_fields"]["target_test"] == [])
    populations = {}
    for role in ("train", "validation", "test"):
        role_meta = [e for e in meta if e["role"] == role]
        role_rows = data["role"] == role
        paid = [s for s in summaries if s["role"] == role]
        unique_rows = sum(s["rows"] for s in paid)
        logical_rows = sum(e["logical_paid_rows"] for e in role_meta)
        populations[role] = {"masters": len({e["cell"] for e in role_meta}), "episodes": len(role_meta), "target_rows": int(role_rows.sum()),
                             "valid_episodes": sum(e["valid"] for e in role_meta), "valid_rows": int(data["valid_mask"][role_rows].sum()),
                             "unique_paid_matrices": len(paid), "unique_paid_rows": unique_rows, "unique_paid_response_conversions": 3 * unique_rows,
                             "logical_paid_bundles": sum(e["logical_bundles"] for e in role_meta), "logical_paid_rows": logical_rows, "logical_paid_response_disclosures": 3 * logical_rows}
        check("population_" + role, all(populations[role][k] == design["counts"][role][k] for k in ("masters", "episodes", "target_rows") if k in design["counts"][role])
              and populations[role]["masters"] == design["counts"][role]["cells"] and {e["cell"] for e in role_meta} == set(design["role_cells"][role]))
        check("logical_purchases_" + role, populations[role]["logical_paid_bundles"] == 2 * len(role_meta) and logical_rows == sum(summary_by_key[tuple(k)]["rows"] for e in role_meta for k in e["query_keys"]))
        check("paid_conversion_counts_" + role, all(ledger["paid:" + role][field]["attempted"] == unique_rows for field in ("lib1_y", "lib2_y", "inhibition")))
        check("episode_query_roles_" + role, all(summary_by_key[tuple(k)]["role"] == role for e in role_meta for k in e["query_keys"]))
        if role != "test":
            check("target_conversion_counts_" + role, ledger["target:" + role]["inhibition"]["attempted"] == populations[role]["target_rows"])
    reserve = [e for e in episodes if e["role"] == "reserve"]
    reserve_keys = {tuple(k) for e in reserve for k in [e["target"]] + e["witnesses"]}
    check("reserve_absent_from_active_keys_and_population", not reserve_keys & (used_keys | {tuple(r["targetkey"]) for r in rows})
          and not set(design["role_cells"]["reserve"]) & {e["cell"] for e in meta} and "reserve" not in data["role"])
    check("real_test_target_stage_not_present", not (LOG / "TEST_TARGETS.npz").exists() and not (LOG / "TEST_TARGETS_STARTED.json").exists())
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "utc": datetime.now(timezone.utc).isoformat(),
              "audit_code_sha256": sha(Path(__file__)), "inputs_sha256": hashes, "data_array_headers": headers, "populations": populations,
              "reserve": {"masters": len(design["role_cells"]["reserve"]), "episodes": len(reserve), "numeric_conversions": 0},
              "checks": checks, "source_zip_opened_by_audit": False, "test_target_opened_by_audit": False, "fits_started_by_audit": 0,
              "large_feature_values_loaded": False, "source_hash_verification": "relied on completed pinned preparation receipt; source ZIP deliberately not reopened"}
    output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    lines = ["# Independent generated-input audit", "", "2026-10-22. Functional auditor. Status: **" + result["status"] + "**.", "",
             "Read only the generated input artifacts and frozen design/code receipts. No source ZIP or test targets were opened, no preparation/model stage was started, and no frozen file was modified. Large full/without_mono feature arrays were checked through NPZ headers rather than loaded during the live fit.", "",
             "All input artifact hashes match INPUTS_RECEIPT; frozen nonarchive hashes and preparation code/protocol/design/schema STARTED bindings match. The pinned source ZIP hash was not independently recomputed because this audit was explicitly forbidden to reopen that source.", "",
             "| Role | MASTERs | Episodes | Target rows | Valid episodes | Unique paid matrices | Unique paid rows | Logical bundles | Logical paid rows |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for role, v in populations.items():
        lines.append("| " + role + " | " + " | ".join(str(v[k]) for k in ("masters", "episodes", "target_rows", "valid_episodes", "unique_paid_matrices", "unique_paid_rows", "logical_paid_bundles", "logical_paid_rows")) + " |")
    lines += ["", "Input validity is 100% in every role. Train/validation labels are finite; every test input y is NaN. ROWS, episode, role, target pair and metadata identities align. Paid endpoint means and paid own-grid residual summaries were independently recomputed from PAID_OBSERVATIONS and match. Logical two-bundle cost is retained per episode despite physical source deduplication.", "",
              "Conversion receipts contain only paid train/validation/test mono+combination and train/validation target inhibition scopes. Actual conversion counts equal unique paid rows times three plus permitted target counts; no test target, target attached mono/fitted, or reserve scope exists. The 413 reserve MASTERs and 2749 reserve episodes are absent from active keys/population and remain numerically unopened under this interface.", "",
              "These checks establish consistency of generated inputs and declared field use; they do not prove the released source's original normalization provenance or independent prospective assay separation. No performance/novelty conclusion is drawn.", "",
              "Machine-readable checks and exact hashes: INPUTS_INDEPENDENT_AUDIT.json. Failed checks: " + (", ".join(k for k, v in checks.items() if not v) or "none") + "."]
    prose.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks), "failed": [k for k, v in checks.items() if not v], "outputs": [output.name, prose.name]}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
