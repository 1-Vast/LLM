"""Verify this phase's evidence bindings and preserve earlier frozen studies."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
LOG = ROOT / "log/20261022/intervention_program_renewal"
checks = []


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(name, passed):
    checks.append({"name": name, "passed": bool(passed)})


def write(path, result):
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    prior = 0
    for phase in ["functional_dynamics_gate", "dead_stock_information_gate", "stack_raw_qualification", "stack_conditional_information"]:
        manifest = load(ROOT / f"log/20261022/{phase}/FINAL_FILE_INVENTORY.json")
        for item in manifest["files"]:
            path = ROOT / item["path"]
            check("preserved:" + item["path"], path.stat().st_size == item["bytes"] and sha(path) == item["sha256"])
            prior += 1
    check("previous_file_count", prior == 337)
    for path in sorted(CODE.glob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"))
        check("parse:" + path.name, True)
    source_receipts = []
    for folder in ["data_auditor", "skeptic"]:
        for path in sorted((LOG / folder).glob("*_RECEIPT.json")):
            r = load(path)
            body = path.with_name(path.name.replace("_RECEIPT.json", ".body"))
            count = r.get("retained_bytes", r.get("bytes"))
            check("source_body:" + path.stem, body.stat().st_size == count and sha(body) == r["sha256"])
            source_receipts.append({"receipt": path.relative_to(ROOT).as_posix(), "status": r["status"], "bytes": count,
                                    "partial": r.get("truncated", False)})
    for path in sorted((LOG / "novelty_advocate/sources").glob("[0-9][0-9]_*.json")):
        if "PROJECTION" in path.name:
            continue
        r = load(path)
        body = path.with_suffix(".body")
        check("source_body:" + path.stem, body.stat().st_size == r["retained_bytes"] and sha(body) == r["sha256"])
        source_receipts.append({"receipt": path.relative_to(ROOT).as_posix(), "status": r["status"], "bytes": r["retained_bytes"], "partial": False})
    design = LOG / "az_design"
    for path in sorted(design.glob("GET_*.json")):
        r = load(path)
        body = design / r["body"]
        check("source_body:" + path.stem, body.stat().st_size == r["bytes"] and sha(body) == r["sha256"])
        source_receipts.append({"receipt": path.relative_to(ROOT).as_posix(), "status": r["status"], "bytes": r["bytes"], "partial": False})
    check("explicit_source_get_count", len(source_receipts) == 19)
    provider = []
    for folder, label in [("mechanism", "FSI"), ("improver", "CCIP")]:
        r = load(LOG / folder / "RECEIPT.json")
        response = LOG / folder / "RESPONSE.md"
        check(label + "_provider_hash", sha(response) == r["response_sha256"])
        audit = load(LOG / (label + "_ALGEBRA_AUDIT.json"))
        check(label + "_audit_source", sha(response) == audit["source_sha256"])
        check(label + "_audit_code", sha(CODE / (label.lower() + "_algebra_audit.py")) == audit["code_sha256"])
        check(label + "_audit_protocol", sha(LOG / (label + "_ALGEBRA_PROTOCOL.md")) == audit["protocol_sha256"])
        provider.append({"role": folder, "tokens": r["usage"]["total_tokens"], "calls": r["logical_requests"],
                         "transport_attempts": r["transport_attempts"], "thinking_enabled": r["thinking_enabled"]})
    check("provider_token_count", sum(r["tokens"] for r in provider) == 32518)
    bindings = [
        (load(design / "HEADERS.json"), "az_acquire_headers.py", "AZ_DESIGN_PROTOCOL.md"),
        (load(design / "CENSUS.json"), "az_design_census.py", "AZ_METADATA_PROJECTION.md"),
        (load(design / "EDGE_COVER.json"), "az_edge_cover.py", "AZ_EDGE_COVER_PROTOCOL.md"),
    ]
    for r, code, protocol in bindings:
        check(code + "_binding", sha(CODE / code) == r["code_sha256"])
        check(protocol + "_binding", sha(LOG / protocol) == r["protocol_sha256"])
    census = load(design / "CENSUS.json")
    check("design_projection_binding", sha(design / "DESIGN_MATRICES.jsonl") == census["design_projection_sha256"])
    audit = load(LOG / "data_auditor/CENSUS_REVIEW.json")
    check("independent_design_projection_binding", audit["projection_sha256"] == census["design_projection_sha256"])
    check("independent_census_counts", all(audit["actual"][k] == census["overall"][k] for k in audit["actual"]))
    snapshot = load(LOG / "data_auditor/AUDIT_SNAPSHOT.json")
    check("data_independent_draft_preserved", sha(LOG / "data_auditor/INDEPENDENT.md") == snapshot["independent_sha256_before_peer_reading"])
    edge = load(design / "EDGE_COVER.json")
    for scope, r in edge["scopes"].items():
        check("edge_witness:" + scope, sha(design / ("EDGE_WITNESSES_" + scope + ".jsonl")) == r["witnesses_sha256"])
    tests = [load(design / name) for name in ["PROJECTION_TEST.json", "EDGE_TEST.json"]]
    check("six_synthetic_checks", sum(t["tests_run"] for t in tests) == 6 and all(t["success"] for t in tests))
    diff = subprocess.run(["git", "diff", "--check", "--", str(CODE.relative_to(ROOT)), str(LOG.relative_to(ROOT)), "research/REPORT.md", "log/README.md"], cwd=ROOT, text=True, capture_output=True)
    check("scoped_git_diff_check", diff.returncode == 0)
    write(LOG / "RESOURCES_AND_EXPOSURE.json", {
        "runtime": "maestro Python -B", "explicit_source_GETs": len(source_receipts), "source_requests": source_receipts,
        "http_status_counts": dict(Counter(str(r["status"]) for r in source_receipts)),
        "source_retained_body_bytes": sum(r["bytes"] for r in source_receipts), "provider": provider,
        "decoded_DeepSeek_calls": 2, "DeepSeek_total_tokens": 32518, "provider_transport_attempts": "NOT_EXPOSED",
        "collaborator_platform_authentication_failure": 1, "new_archive_downloads": 1, "archive_bytes": 241088863,
        "algebra_audit_invocations": 2, "design_census_invocations": 1, "edge_cover_invocations": 1,
        "design_census_seconds": census["elapsed_seconds"], "edge_cover_seconds": edge["elapsed_seconds"],
        "synthetic_software_checks": 6, "biological_fits": 0, "biological_target_numeric_use": False,
        "source_response_byte_contact": True, "source_narrative_outcome_exposure": True,
        "cryptographic_secrecy_claim": False, "wetlab_experiments": 0, "external_contacts": 0,
    })
    passed = all(c["passed"] for c in checks)
    write(LOG / "FINAL_INTEGRITY.json", {"utc": datetime.now(timezone.utc).isoformat(), "passed": passed,
        "prior_inventoried_files_unchanged": prior, "phase_python_files_parse": len(list(CODE.glob("*.py"))),
        "checks": checks, "scoped_diff_stdout": diff.stdout, "scoped_diff_stderr": diff.stderr})
    if not passed:
        raise RuntimeError("Integrity failures: " + repr([c["name"] for c in checks if not c["passed"]]))
    files = sorted(p for folder in [CODE, LOG] for p in folder.rglob("*") if p.is_file() and p.name != "FINAL_FILE_INVENTORY.json")
    write(LOG / "FINAL_FILE_INVENTORY.json", {"utc": datetime.now(timezone.utc).isoformat(), "files": [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files],
        "excludes": "This inventory itself and mutable research/REPORT.md and log/README.md navigation."})
    print(json.dumps({"passed": passed, "checks": len(checks), "previous_files": prior, "phase_files": len(files),
                      "source_GETs": len(source_receipts), "provider_tokens": 32518}))


if __name__ == "__main__":
    main()
