"""Audit retained metadata receipts, code blobs and independent-draft ordering."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/data_auditor"
checks = []
for path in sorted(OUT.glob("*_RECEIPT.json")):
    receipt = json.loads(path.read_text(encoding="utf-8"))
    body = path.with_name(path.name.replace("_RECEIPT.json", ".body")).read_bytes()
    checks.append({"name": path.stem, "attempt": receipt["attempt"], "status": receipt.get("status"),
                   "hash_ok": hashlib.sha256(body).hexdigest() == receipt["sha256"],
                   "size_ok": len(body) == receipt["retained_bytes"] <= 8 * 1024 * 1024,
                   "redirect_retry_off": receipt["automatic_redirects"] is False and receipt["automatic_retries"] is False,
                   "timeout_ok": receipt["timeout_seconds"] <= 30})
repository = json.loads((OUT / "az_author_repo.body").read_bytes())
code = []
for label, name in (("az_figure1_code", "Figure 1.Rmd"), ("az_supp1_code", "Supplementary Figure 1.Rmd")):
    body = (OUT / (label + ".body")).read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
    expected = next(item["sha"] for item in repository if item["name"] == name)
    code.append({"name": name, "git_blob_sha": sha, "metadata_sha": expected, "matches": sha == expected})
independent = OUT / "INDEPENDENT.md"
result = {"receipts": checks, "code_blobs": code, "attempts": len(checks),
          "attempt_numbers": sorted(item["attempt"] for item in checks),
          "independent_sha256_before_peer_reading": hashlib.sha256(independent.read_bytes()).hexdigest(),
          "biological_response_arrays_downloaded": 0, "fits": 0,
          "qualification": "DESIGN_CENSUS_CONDITIONALLY_QUALIFIED; NO_RESPONSE_OPENING"}
assert len(checks) == 8 and result["attempt_numbers"] == list(range(1, 9))
assert all(all(item[key] for key in ("hash_ok", "size_ok", "redirect_retry_off", "timeout_ok")) for item in checks)
assert all(item["matches"] for item in code)
(OUT / "AUDIT_SNAPSHOT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
