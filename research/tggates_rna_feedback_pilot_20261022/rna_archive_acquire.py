"""Write-once archive acquisition and exact-basename CEL extraction for this pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import requests


PHASE = Path("log/20261022/tggates_rna_feedback_pilot")
MANIFEST = PHASE / "RNA_IDENTITY_MANIFEST.json"
HEADS = PHASE / "RNA_ARCHIVE_HEADS.json"
AUTHORIZED_STATUS = "RNA_ACQUISITION_FROZEN_AND_AUTHORIZED"
BARCODE_RE = re.compile(r"^[0-9]{12}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_inputs(manifest_path: Path = MANIFEST, heads_path: Path = HEADS) -> tuple[dict, list[dict], str]:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    heads = json.loads(heads_path.read_text(encoding="utf-8"))
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    samples = manifest["samples"]
    if len(samples) != 172 or len({s["expected_CEL_basename"] for s in samples}) != 172:
        raise ValueError("manifest must contain 172 unique exact CEL basenames")
    actual_counts = Counter(f"{sample['role']}_{sample['identity']['DOSE_LEVEL']}" for sample in samples)
    actual_counts = {key: actual_counts.get(key, 0) for key in (
        "source_Middle", "source_High", "source_Control", "development_Middle", "development_Control")}
    if actual_counts != {
        "source_Middle": 48, "source_High": 48, "source_Control": 48,
        "development_Middle": 14, "development_Control": 14,
    } or manifest["sample_counts"] != actual_counts:
        raise ValueError("manifest sample counts do not match the frozen RNA scope")
    if len(manifest["compounds"]) != 31 or len(heads["receipts"]) != 31:
        raise ValueError("expected exactly 31 compounds and 31 HEAD receipts")

    by_label = {r["compound_label"]: r for r in heads["receipts"]}
    if len(by_label) != 31:
        raise ValueError("HEAD compound labels are not unique")
    jobs = []
    used_urls = set()
    for compound in manifest["compounds"]:
        label = compound["compound_label"]
        head = by_label.get(label)
        if head is None:
            raise ValueError(f"no HEAD receipt for {label}")
        url = compound["official_HTTPS_mirror_URL"]
        if (url != head["url"] or head["final_url"] != url or head["status"] != 200
                or head["method"] != "HEAD" or head["RNA_payload_body_bytes_downloaded"] != 0):
            raise ValueError(f"official URL/HEAD mismatch for {label}")
        if not url.startswith("https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/Human/in_vitro/"):
            raise ValueError(f"URL outside authenticated official archive path: {label}")
        expected = int(head["headers"]["Content-Length"])
        if expected <= 0 or url in used_urls:
            raise ValueError(f"invalid or duplicate archive URL/length for {label}")
        used_urls.add(url)
        expected_barcodes = set(compound["expected_allowed_barcodes"])
        sample_barcodes = {
            s["identity"]["BARCODE"] for s in samples
            if s["identity"]["COMPOUND_NAME"] == label
        }
        if expected_barcodes != sample_barcodes:
            raise ValueError(f"manifest/compound barcode mapping mismatch for {label}")
        if any(not BARCODE_RE.fullmatch(code) for code in expected_barcodes):
            raise ValueError(f"invalid barcode for {label}")
        jobs.append({"compound_label": label, "url": url, "expected_bytes": expected,
                     "allowed_basenames": {f"{code}.CEL" for code in expected_barcodes}})

    total = sum(job["expected_bytes"] for job in jobs)
    if total != 3658321111 or heads["known_sum_archive_bytes"] != total:
        raise ValueError(f"archive byte sum changed: {total}")
    return manifest, jobs, manifest_sha


def check_freeze(freeze_path: Path, manifest_sha: str, jobs: list[dict], heads_path: Path = HEADS) -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    expected = sum(job["expected_bytes"] for job in jobs)
    heads_sha = sha256_file(heads_path)
    script_sha = sha256_file(Path(__file__))
    if (freeze.get("status") != AUTHORIZED_STATUS
            or freeze.get("manifest_sha256") != manifest_sha
            or freeze.get("heads_sha256") != heads_sha
            or freeze.get("script_sha256") != script_sha
            or freeze.get("authorized_archive_count") != len(jobs)
            or freeze.get("expected_archive_bytes") != expected):
        raise ValueError("freeze does not explicitly authorize and pin these exact inputs and bytes")
    return freeze


def check_extraction_freeze(freeze_path: Path, manifest_sha: str,
                            heads_path: Path = HEADS) -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (freeze.get("status") != "CEL_EXTRACTION_FROZEN_AND_AUTHORIZED"
            or freeze.get("manifest_sha256") != manifest_sha
            or freeze.get("heads_sha256") != sha256_file(heads_path)
            or freeze.get("script_sha256") != sha256_file(Path(__file__))
            or freeze.get("selected_basename_rule_verified") is not True):
        raise ValueError("extraction requires a separate freeze after selected CEL naming is verified")
    return freeze


def _receipt_path(receipts_dir: Path, stem: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    path = receipts_dir / f"{stem}_{stamp}.json"
    if path.exists():
        raise FileExistsError(path)
    return path


def write_receipt(receipts_dir: Path, stem: str, receipt: dict) -> Path:
    receipts_dir.mkdir(parents=True, exist_ok=True)
    path = _receipt_path(receipts_dir, stem)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def publish_write_once(part: Path, target: Path) -> None:
    """Create target without replacing an existing file; both paths share a directory."""
    os.link(part, target)
    part.unlink()


def download_one(job: dict, archives_dir: Path, receipts_dir: Path,
                 session=requests) -> dict:
    archives_dir.mkdir(parents=True, exist_ok=True)
    target = archives_dir / f"{job['compound_label']}.zip"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    prior = sorted(receipts_dir.glob(f"{job['compound_label']}_*.json"))
    if target.exists():
        for path in prior:
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if (old.get("outcome") == "complete" and old.get("status") == 200
                    and old.get("actual_body_bytes") == job["expected_bytes"]
                    and target.stat().st_size == job["expected_bytes"]):
                actual_sha = sha256_file(target)
                if old.get("sha256") == actual_sha:
                    return {"outcome": "reused_verified", "archive": str(target), "sha256": actual_sha}
        raise FileExistsError(f"archive exists without a matching complete SHA receipt: {target}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    part = archives_dir / f"{job['compound_label']}.{stamp}.part"
    started = utc_now()
    body_bytes = 0
    status = None
    headers = {}
    final_url = None
    error = None
    try:
        with session.get(job["url"], stream=True, timeout=(10, 60)) as response:
            status = response.status_code
            headers = dict(response.headers)
            final_url = response.url
            if final_url != job["url"]:
                raise ValueError(f"unexpected redirected URL: {final_url}")
            if status != 200:
                raise ValueError(f"unexpected HTTP status: {status}")
            response.raise_for_status()
            with part.open("xb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        stream.write(chunk)
                        body_bytes += len(chunk)
                        if body_bytes > job["expected_bytes"]:
                            raise ValueError("response exceeded frozen body length; stream stopped")
        if body_bytes != job["expected_bytes"]:
            error = f"body length mismatch: expected {job['expected_bytes']}, received {body_bytes}"
        else:
            digest = sha256_file(part)
            publish_write_once(part, target)
            receipt = {"utc_started": started, "utc_finished": utc_now(), "method": "GET",
                       "compound_label": job["compound_label"], "url": job["url"],
                       "final_url": final_url, "status": status, "response_headers": headers,
                       "expected_body_bytes": job["expected_bytes"], "actual_body_bytes": body_bytes,
                       "sha256": digest, "archive": str(target), "outcome": "complete", "error": None}
            write_receipt(receipts_dir, job["compound_label"], receipt)
            return receipt
    except Exception as exc:  # Record network, HTTP, and local I/O failures with observed byte count.
        error = f"{type(exc).__name__}: {exc}"
    receipt = {"utc_started": started, "utc_finished": utc_now(), "method": "GET",
               "compound_label": job["compound_label"], "url": job["url"],
               "final_url": final_url, "status": status, "response_headers": headers,
               "expected_body_bytes": job["expected_bytes"], "actual_body_bytes": body_bytes,
               "sha256": sha256_file(part) if part.exists() else None,
               "partial_archive": str(part) if part.exists() else None,
               "outcome": "failed", "error": error,
               "extra_body_bytes": max(0, body_bytes - job["expected_bytes"])}
    write_receipt(receipts_dir, job["compound_label"], receipt)
    return receipt


def safe_member_basename(name: str) -> str:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts or "\\" in name or "\x00" in name:
        raise ValueError(f"unsafe ZIP member path: {name!r}")
    if not member.parts or member.name in {"", ".", ".."}:
        raise ValueError(f"invalid ZIP member path: {name!r}")
    return member.name


def verify_archive(job: dict, archive: Path, receipts_dir: Path) -> str:
    if archive.stat().st_size != job["expected_bytes"]:
        raise ValueError("archive length does not match frozen HEAD")
    digest = sha256_file(archive)
    for path in receipts_dir.glob(f"{job['compound_label']}_*.json"):
        old = json.loads(path.read_text(encoding="utf-8"))
        if (old.get("outcome") == "complete" and old.get("status") == 200
                and old.get("url") == job["url"]
                and old.get("actual_body_bytes") == job["expected_bytes"]
                and old.get("sha256") == digest):
            return digest
    raise ValueError("archive has no matching complete download receipt")


def extract_selected(archive: Path, allowed_basenames: set[str], output_dir: Path,
                     member_receipts_dir: Path | None = None) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        matches: dict[str, list[zipfile.ZipInfo]] = {name: [] for name in allowed_basenames}
        for info in zf.infolist():
            base = safe_member_basename(info.filename)
            if base in matches and not info.is_dir():
                matches[base].append(info)
        bad = {name: len(items) for name, items in matches.items() if len(items) != 1}
        if bad:
            raise ValueError(f"whitelist must match each basename exactly once: {bad}")
        receipts = []
        for basename, entries in sorted(matches.items()):
            info = entries[0]
            target = output_dir / basename
            temp = output_dir / f".{basename}.{os.getpid()}.part"
            if target.exists() and member_receipts_dir is not None:
                old_matches = list(member_receipts_dir.glob(f"{basename}_*.json"))
                verified = None
                for path in old_matches:
                    old = json.loads(path.read_text(encoding="utf-8"))
                    if (old.get("member") == info.filename
                            and old.get("uncompressed_bytes") == target.stat().st_size == info.file_size
                            and old.get("crc32") == f"{info.CRC:08x}"
                            and old.get("sha256") == sha256_file(target)):
                        verified = old
                        break
                if verified is None:
                    raise ValueError(f"existing CEL lacks matching member receipt: {target}")
                receipts.append(verified)
                continue
            if target.exists() or temp.exists():
                raise FileExistsError(f"refusing to overwrite extracted CEL: {target}")
            count = 0
            digest = hashlib.sha256()
            try:
                with zf.open(info, "r") as source, temp.open("xb") as dest:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        dest.write(chunk)
                        digest.update(chunk)
                        count += len(chunk)
                if count != info.file_size:
                    raise ValueError(f"uncompressed byte mismatch for {basename}: {count} != {info.file_size}")
                publish_write_once(temp, target)
            except Exception:
                if temp.exists():
                    temp.rename(output_dir / f"{basename}.{int(time.time())}.failed.part")
                raise
            item = {"member": info.filename, "basename": basename,
                             "barcode": basename[:-4],
                             "compressed_bytes": info.compress_size,
                             "uncompressed_bytes": count, "crc32": f"{info.CRC:08x}",
                             "sha256": digest.hexdigest(), "path": str(target),
                             "output": str(target)}
            if member_receipts_dir is not None:
                write_receipt(member_receipts_dir, basename, item)
            receipts.append(item)
    return receipts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("download", "extract"))
    parser.add_argument("--freeze-file", type=Path, required=True)
    parser.add_argument("--extraction-freeze-file", type=Path)
    parser.add_argument("--phase-dir", type=Path, default=PHASE)
    args = parser.parse_args(argv)
    try:
        _, jobs, manifest_sha = load_inputs(args.phase_dir / "RNA_IDENTITY_MANIFEST.json",
                                             args.phase_dir / "RNA_ARCHIVE_HEADS.json")
        check_freeze(args.freeze_file, manifest_sha, jobs, args.phase_dir / "RNA_ARCHIVE_HEADS.json")
        if args.action == "download":
            for index, job in enumerate(jobs, 1):
                print(f"[{index}/{len(jobs)}] downloading {job['compound_label']}", flush=True)
                result = download_one(job, args.phase_dir / "raw_archives", args.phase_dir / "receipts" / "archive_downloads")
                print(json.dumps(result, ensure_ascii=False), flush=True)
                if result.get("outcome") == "failed":
                    return 1
        else:
            if args.extraction_freeze_file is None:
                raise ValueError("extract action requires a separate --extraction-freeze-file")
            check_extraction_freeze(args.extraction_freeze_file, manifest_sha,
                                     args.phase_dir / "RNA_ARCHIVE_HEADS.json")
            output = args.phase_dir / "selected_cel_flat"
            for index, job in enumerate(jobs, 1):
                archive = args.phase_dir / "raw_archives" / f"{job['compound_label']}.zip"
                if not archive.is_file():
                    raise FileNotFoundError(archive)
                print(f"[{index}/{len(jobs)}] extracting selected members for {job['compound_label']}", flush=True)
                started = utc_now()
                try:
                    archive_sha = verify_archive(job, archive, args.phase_dir / "receipts" / "archive_downloads")
                    members = extract_selected(archive, job["allowed_basenames"], output,
                                               args.phase_dir / "receipts" / "cel_members")
                    receipt = {"utc_started": started, "utc_finished": utc_now(),
                               "compound_label": job["compound_label"], "archive": str(archive),
                               "archive_sha256": archive_sha, "outcome": "complete",
                               "member_count": len(members), "members": members, "error": None}
                except Exception as exc:
                    receipt = {"utc_started": started, "utc_finished": utc_now(),
                               "compound_label": job["compound_label"], "archive": str(archive),
                               "archive_sha256": sha256_file(archive), "outcome": "failed",
                               "member_count": None, "members": [],
                               "error": f"{type(exc).__name__}: {exc}"}
                write_receipt(args.phase_dir / "receipts" / "cel_extraction", job["compound_label"], receipt)
                print(json.dumps(receipt, ensure_ascii=False), flush=True)
                if receipt["outcome"] == "failed":
                    return 1
        return 0
    except Exception as exc:
        print(f"acquisition stopped: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
