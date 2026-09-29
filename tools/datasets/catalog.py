"""Inspect dataset candidates and local source provenance without loading matrices."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = Path(__file__).with_name("candidates.json")
SOURCES = Path(__file__).with_name("sources.json")
HASH_LIMIT = 700 * 1024 * 1024


def load_inventory(path: Path = INVENTORY) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload["candidates"])


def load_sources(path: Path = SOURCES) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def candidates(*, role: str | None = None, path: Path = INVENTORY) -> list[dict[str, Any]]:
    records = load_inventory(path)
    if role:
        records = [record for record in records if role in record.get("roles", [])]
    return [{"id": record["id"], "name": record["name"],
             "roles": record.get("roles", []), "fit": record.get("suitability", {}).get("fit"),
             "confidence": record.get("suitability", {}).get("confidence"),
             "not_eligible_for": record.get("suitability", {}).get("not_eligible_for"),
             "overlap": record.get("overlap"),
             "qualification": "historical_candidate_only; current construction and checkpoint exposure must be audited",
             "construction_limit": ("sciPlex4 rescue contrasts are not constructible from the qualified v2 subset"
                                    if record["id"] == "sci-plex-family" else None)}
            for record in records]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _columns(path: Path) -> list[str] | None:
    name = path.name.lower()
    if name.endswith((".csv", ".tsv", ".txt")):
        opener = path.open
        delimiter = "," if name.endswith(".csv") else "\t"
    elif name.endswith((".csv.gz", ".tsv.gz", ".txt.gz")):
        opener = lambda **kwargs: gzip.open(path, "rt", **kwargs)
        delimiter = "," if name.endswith(".csv.gz") else "\t"
    else:
        return None
    with opener(encoding="utf-8", errors="replace", newline="") as handle:
        return next(csv.reader(handle, delimiter=delimiter), [])


def audit_source(record: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    """Report observed facts separately from declarations and unresolved metadata."""
    path = root / record["path"]
    result: dict[str, Any] = {
        "id": record["id"], "path": record["path"], "exists": path.exists(),
        "role": record.get("role"), "url": record.get("url", "unverified"),
        "licence": record.get("licence", "unverified"),
        "limitations": record.get("limitations", []),
    }
    provenance_path = root / record["provenance"] if record.get("provenance") else None
    if provenance_path and provenance_path.is_file() and provenance_path.suffix == ".json":
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        result["provenance_file"] = record["provenance"]
        result["retrieved_at"] = (provenance.get("retrieved_at_utc") or provenance.get("retrieved")
                                  or provenance.get("acquisition_date_asia_shanghai"))
        result["url"] = provenance.get("source_url") or provenance.get("url") or result["url"]
        result["licence"] = provenance.get("licence") or provenance.get("license_note") or result["licence"]
        expected = provenance.get("sha256") or record.get("recorded_sha256")
    else:
        expected = record.get("recorded_sha256")
    if path.is_file():
        size = path.stat().st_size
        result["bytes"] = size
        if size <= HASH_LIMIT:
            digest = _sha256(path)
            result["sha256"] = digest
            result["checksum_status"] = ("match" if expected == digest else "mismatch") if expected else "computed_no_reference"
        else:
            result["sha256"] = expected
            result["checksum_status"] = "recorded_unverified" if expected else "not_computed"
        result["columns"] = _columns(path)
    elif path.is_dir():
        result["checksum_status"] = "directory_not_hashed"
    else:
        result["checksum_status"] = "missing"
    return result


def probe_metadata(url: str, *, timeout: float = 15.0) -> dict[str, Any]:
    """Read response headers only; a probe never downloads a dataset body."""
    if not url.startswith("https://"):
        raise ValueError("metadata probes require an HTTPS URL")
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "MAESTRO-dataset-catalog/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"url": url, "status": response.status, "resolved_url": response.url,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": response.headers.get("Content-Length"),
                    "last_modified": response.headers.get("Last-Modified")}
    except urllib.error.HTTPError as error:
        return {"url": url, "status": error.code, "error": "http_error"}
    except urllib.error.URLError as error:
        return {"url": url, "status": None, "error": str(error.reason)}


def search(query: str, *, provider: str = "zenodo", limit: int = 10) -> dict[str, Any]:
    if not query.strip() or not 1 <= limit <= 50:
        raise ValueError("search needs a nonempty query and limit between 1 and 50")
    if provider == "zenodo":
        url = "https://zenodo.org/api/records?" + urllib.parse.urlencode({"q": query, "size": limit})
        request = urllib.request.Request(url)
    elif provider == "figshare":
        url = "https://api.figshare.com/v2/articles/search"
        request = urllib.request.Request(url, data=json.dumps({"search_for": query, "page_size": limit}).encode(),
                                         headers={"Content-Type": "application/json"})
    else:
        raise ValueError("unknown metadata provider")
    request.add_header("User-Agent", "MAESTRO-dataset-catalog/1.0")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read((4 << 20) + 1)
        if len(body) > 4 << 20:
            raise ValueError("metadata response exceeds 4 MiB")
    payload = json.loads(body)
    records = payload.get("hits", {}).get("hits", []) if provider == "zenodo" else payload
    return {"provider": provider, "query": query, "url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "response_sha256": hashlib.sha256(body).hexdigest(), "records": records,
            "qualification": "discovery_only; access does not establish task eligibility or independence"}


def fetch(url: str, destination: Path, *, expected_sha256: str,
          max_bytes: int = 32 << 20, licence: str = "unverified") -> dict[str, Any]:
    """Stream one explicitly selected asset, then verify before committing its bytes."""
    if not url.startswith("https://") or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("fetch requires HTTPS and a declared SHA-256")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    destination = destination.resolve()
    if not destination.is_relative_to((ROOT / "data").resolve()):
        raise ValueError("download destination must remain under data/")
    if destination.exists():
        if _sha256(destination) != expected_sha256.lower():
            raise ValueError("existing destination does not match declared SHA-256")
        return {"path": str(destination), "sha256": expected_sha256.lower(), "status": "already_verified"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    digest = hashlib.sha256()
    size = 0
    output = temporary.open("xb")
    try:
        with output:
            request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-dataset-catalog/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                for block in iter(lambda: response.read(1 << 20), b""):
                    size += len(block)
                    if size > max_bytes:
                        raise ValueError("download exceeds declared byte budget")
                    output.write(block)
                    digest.update(block)
        actual = digest.hexdigest()
        if actual != expected_sha256.lower():
            raise ValueError("download SHA-256 mismatch")
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    record = {"url": url, "sha256": actual, "bytes": size, "licence": licence,
              "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
              "qualification": "verified_bytes_only; task eligibility and exposure require separate audit"}
    destination.with_suffix(destination.suffix + ".provenance.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    candidates_cmd = commands.add_parser("candidates", help="List reviewed dataset candidates")
    candidates_cmd.add_argument("--role", choices=("A", "B", "C", "D", "E"))
    source_cmd = commands.add_parser("source", help="Audit one registered local source")
    source_cmd.add_argument("id")
    probe_cmd = commands.add_parser("probe", help="Read remote metadata headers only")
    probe_cmd.add_argument("url")
    search_cmd = commands.add_parser("search", help="Search Figshare or Zenodo metadata")
    search_cmd.add_argument("query")
    search_cmd.add_argument("--provider", choices=("zenodo", "figshare"), default="zenodo")
    search_cmd.add_argument("--limit", type=int, default=10)
    search_cmd.add_argument("--output", type=Path, help="Save a metadata snapshot")
    fetch_cmd = commands.add_parser("fetch", help="Download one hash-pinned asset")
    fetch_cmd.add_argument("url")
    fetch_cmd.add_argument("destination", type=Path)
    fetch_cmd.add_argument("--sha256", required=True)
    fetch_cmd.add_argument("--max-bytes", type=int, default=32 << 20)
    fetch_cmd.add_argument("--licence", default="unverified")
    arguments = parser.parse_args(argv)
    if arguments.command == "candidates":
        payload = candidates(role=arguments.role)
    elif arguments.command == "source":
        registered = {record["id"]: record for record in load_sources()}
        if arguments.id not in registered:
            parser.error(f"unknown source id: {arguments.id}")
        payload = audit_source(registered[arguments.id])
    elif arguments.command == "probe":
        payload = probe_metadata(arguments.url)
    elif arguments.command == "search":
        payload = search(arguments.query, provider=arguments.provider, limit=arguments.limit)
        if arguments.output:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        payload = fetch(arguments.url, arguments.destination, expected_sha256=arguments.sha256,
                        max_bytes=arguments.max_bytes, licence=arguments.licence)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
