"""Verify frozen evidence and documented URL redactions; never rewrite manifests."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qsl, urlparse


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify():
    out = Path(__file__).resolve().parent
    root = out.parents[3]
    redactions = json.loads((out / "receipt_url_redactions.json").read_text(encoding="utf-8"))
    allowed = {r["path"]: r for r in redactions["files"]}
    redaction_errors = [name for name, item in allowed.items()
                        if digest(root / name) != item["after_sha256"]]
    manifests = [(out / "historical_sha256.json", root),
                 (root / "tools/datasets/audit_results/20261001_state_search_checkpoint/historical_hashes_before_tests.json", root)]
    manifests.extend((out / name / "manifest.json", out / name) for name in
                     ["certification_v1", "certification_v2", "knowledge_run_v1", "knowledge_run_v2", "source_review_v3"])
    checks = []
    for manifest, base in manifests:
        entries = json.loads(manifest.read_text(encoding="utf-8"))
        mismatch, documented = [], []
        for name, expected in entries.items():
            path = base / name
            actual = digest(path) if path.is_file() else None
            correction = allowed.get(path.relative_to(root).as_posix(), {})
            if actual != expected:
                if correction.get("before_sha256") == expected and correction.get("after_sha256") == actual:
                    documented.append(name)
                else:
                    mismatch.append(name)
        checks.append(dict(manifest=manifest.relative_to(root).as_posix(), files=len(entries),
                           mismatches=mismatch, documented_receipt_redactions=documented))
    api = json.loads((out / "source_review_v3/api_summary.json").read_text(encoding="utf-8"))
    raw_bad, url_flags, raw_count = [], [], 0
    for receipt in api["receipts"]:
        if receipt.get("sha256"):
            raw_count += 1
            path = root / receipt["source_path"]
            if not path.is_file() or digest(path) != receipt["sha256"]:
                raw_bad.append(receipt["id"])
        for key in ("url", "final_url"):
            parsed = urlparse(receipt.get(key, ""))
            risky = [k for k, _ in parse_qsl(parsed.query)
                     if re.search(r"token|secret|signature|credential|api.?key|authorization", k, re.I)]
            if risky or parsed.password:
                url_flags.append(dict(source_id=receipt["id"], field=key, query_keys_only=risky))
    prefix = subprocess.check_output(["git", "show", "1d8c9440070b77f43094c9f5da81d3f88a3964f4:log/20261001/README.md"], cwd=root)
    unchanged = (root / "log/20261001/README.md").read_bytes().startswith(prefix)
    diff = subprocess.run(["git", "diff", "--check"], cwd=root, capture_output=True, text=True)
    link_errors = []
    for path in (out / "REPORT.md", out / "collection/README.md"):
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" not in link and link != "final_integrity.json" and not (path.parent / link.split("#")[0]).exists():
                link_errors.append(dict(document=path.relative_to(root).as_posix(), link=link))
    changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=root, text=True).splitlines()
    return dict(verified_at_utc=datetime.now(timezone.utc).isoformat(), manifests=checks,
                acquired_raw_files_checked=raw_count, raw_hash_mismatches=raw_bad,
                sensitive_URL_field_findings=url_flags, historical_log_prefix_unchanged=unchanged,
                redaction_hash_mismatches=redaction_errors,
                report_local_link_errors=link_errors, git_diff_check_returncode=diff.returncode,
                git_diff_check_output=diff.stdout + diff.stderr, tracked_changed=changed,
                all_checks_passed=not any(c["mismatches"] for c in checks) and not raw_bad and
                not url_flags and not redaction_errors and unchanged and not link_errors and diff.returncode == 0 and
                not any(p.startswith("src/") for p in changed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": report["all_checks_passed"], "raw_files": report["acquired_raw_files_checked"]}))
    raise SystemExit(0 if report["all_checks_passed"] else 1)
