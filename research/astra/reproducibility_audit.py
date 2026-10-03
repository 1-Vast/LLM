"""Separate Git source bytes from frozen asset bytes; never relax frozen checksums."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def git_bytes(root: Path, revision: str, name: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"{revision}:{name}"], cwd=root, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def classify(root: Path, name: str, expected: str, revision: str) -> dict:
    current = file_digest(root / name)
    blob = git_bytes(root, revision, name)
    git_hash = digest(blob) if blob is not None else None
    crlf_hash = digest(blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")) if blob is not None else None
    return {"path": name, "frozen_raw_sha256": expected, "worktree_sha256": current,
            "raw_match": current == expected, "git_revision": revision, "git_blob_sha256": git_hash,
            "git_crlf_candidate_sha256": crlf_hash,
            "git_represents_frozen_CRLF": git_hash != expected and crlf_hash == expected}


def restore_pack(cache: Path, destination: Path, *, manifest_path: Path | None = None) -> dict:
    """Create a new verified pack; an absent cache is a blocker, not a new manifest."""
    manifest_path = manifest_path or cache / "pack_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    recovered = {}
    for name in ("pack.json", "pack_arrays.npz"):
        source = cache / name
        raw = source.read_bytes()
        expected = manifest["outputs"][name]
        method = "raw_copy"
        if digest(raw) != expected and name == "pack.json":
            raw = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            method = "verified_CRLF_reconstruction"
        if digest(raw) != expected:
            raise ValueError(f"frozen_asset_hash_mismatch:{name}")
        recovered[name] = (raw, expected, method)
    # All identities must pass before writing any asset. Never overwrite a destination.
    destination.mkdir(parents=True, exist_ok=False)
    result = {}
    for name, (raw, expected, method) in recovered.items():
        (destination / name).write_bytes(raw)
        result[name] = {"sha256": expected, "method": method}
    (destination / "pack_manifest.json").write_bytes(manifest_path.read_bytes())
    return result


def audit(root: Path, revision: str) -> dict:
    before = json.loads((root / "research/astra/results/20261003_responsibility_followup_v2/before.json").read_text())
    protected = before["protected_sha256"]
    mismatches = [classify(root, name, expected, revision) for name, expected in protected.items()
                  if file_digest(root / name) != expected]
    pack_dir = root / "data/processed/case_memory_integration"
    manifest = json.loads((pack_dir / "pack_manifest.json").read_text())
    pack = [classify(root, f"data/processed/case_memory_integration/{name}", expected, revision)
            for name, expected in manifest["outputs"].items()]
    return {"protected_count": len(protected), "raw_matches": len(protected) - len(mismatches),
            "protected_differences": mismatches, "pack": pack,
            "raw_asset_checks_pass": all(record["raw_match"] for record in pack),
            "rule": "Git/LF equivalence is diagnostic only; frozen raw-asset checks remain byte-exact."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--revision", default="16eed5142ff817535b37a004a6ff7280e7a658b8")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--restore-pack-from", type=Path)
    parser.add_argument("--restore-pack-to", type=Path)
    args = parser.parse_args()
    result = {}
    if bool(args.restore_pack_from) != bool(args.restore_pack_to):
        parser.error("--restore-pack-from and --restore-pack-to must be supplied together")
    if args.restore_pack_from:
        result["restoration"] = restore_pack(args.restore_pack_from, args.restore_pack_to,
            manifest_path=args.root / "data/processed/case_memory_integration/pack_manifest.json")
    result["audit"] = audit(args.root, args.revision)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
