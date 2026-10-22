"""Finite audit checks; hashes raw files without decoding any outcome values."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261021/oasis_source_qualification"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = json.loads((LOG / "PRE_DOWNLOAD_FREEZE.json").read_text())
    amended = json.loads((LOG / "PRE_AUDIT_FREEZE.json").read_text())
    sources = json.loads((LOG / "SOURCE_MANIFEST.json").read_text())
    ids = json.loads((LOG / "BLIND_IDENTIFIERS.json").read_text())
    allowed = {"compound_id", "is_dmso_control", "dose_um", "plate", "well", "source",
               "oasis_id", "library", "plate_type", "replicate", "functional_present"}
    result = {
        "original_protocol_unchanged": digest(LOG / "PROTOCOL.md") == frozen[str((LOG / "PROTOCOL.md").relative_to(ROOT))],
        "all_68_source_hashes_match": len(sources) == 68 and all(digest(ROOT / x["local_path"]) == x["sha256"] for x in sources),
        "amended_audit_hash_matches": digest(Path(__file__).with_name("blind_audit.py")) == amended["amended_hash"],
        "original_audit_hash_retained": frozen[str(Path(__file__).with_name("blind_audit.py").relative_to(ROOT))] == amended["original_hash"],
        "identifier_keys_whitelisted": all(set(x) <= allowed for x in ids),
        "functional_outputs_boolean_presence_only": all(isinstance(v, bool) for x in ids for v in x["functional_present"].values()),
        "no_functional_value_keys_in_identifier_output": not any(set(x) & {"mtt_lumi", "ldh_abs", "ldh_abs_signal", "ldh_abs_background", "mtt_normalized", "ldh_normalized", "mtt_ridge_norm", "ldh_ridge_norm"} for x in ids),
        "chemical_holdout_created": False,
        "sealed_file_count": len(sources),
    }
    (LOG / "VERIFY.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    checks = [v for k, v in result.items() if k not in {"chemical_holdout_created", "sealed_file_count"}]
    if not all(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
