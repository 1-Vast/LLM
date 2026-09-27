"""Immutable experiment registration, verification at the registration commit, and replay integrity.

File summary
- Path: research/protocol_v2/registry.py
- Purpose: make a registered experiment reproducible from what it records, and impossible to
  rewrite silently. Protocol v1 froze file digests of a dirty working tree and verified them
  against whatever the tree held later, so later edits either broke verification or, when the
  freeze itself was regenerated, erased the record of what had been registered.
- Core points:
  - `register` refuses a dirty working tree (`DirtyTree`) and an existing record
    (`AlreadyRegistered`). It records protocol_version, experiment, git_commit, git_dirty,
    protocol/manifest/code/data SHA-256 digests, the environment lock, the command, the random
    seed and runtime versions. The file is written once, LF-terminated, and made read-only.
  - `development_record` writes the same content for a development run on a dirty tree, with
    `registered: false`. It is a disclosure, not a registration, and no gate may cite it as one.
  - `verify_at_commit` checks digests against the blobs of the registration commit for tracked
    files, and against the disk for untracked data. A historical experiment is replayed from a
    worktree at its commit (`replay_instructions`), never from the moving working tree.
  - `compare_decisions` checks replay integrity at the decision level: chosen actions, stop
    reason, readings, eliminations, terminal decision, measurements and days must match exactly;
    numeric diagnostics within an absolute and relative tolerance of 1e-8. Byte equality of JSON
    is not required (last-bit float formatting differs across builds).
- Interfaces: `DirtyTree`, `AlreadyRegistered`, `git_state`, `environment_lock`, `sha256_file`,
  `register`, `development_record`, `verify_at_commit`, `replay_instructions`, `compare_decisions`
- Depends on: git on PATH; the Python standard library
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[2]
TIMEZONE = timezone(timedelta(hours=8))
RUNTIME_PACKAGES = ("numpy", "scipy", "pandas", "scikit-learn", "rdkit", "h5py", "threadpoolctl", "pytest")
DECISION_FIELDS = ("stop", "final", "measurements", "remaining")
STEP_FIELDS = ("action", "outcome", "qc", "eliminated", "state")


class DirtyTree(RuntimeError):
    """Registration refused: the working tree has uncommitted or untracked changes."""


class AlreadyRegistered(RuntimeError):
    """Registration refused: a record for this experiment already exists."""


def _git(root: Path, *args, binary: bool = False):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout if binary else result.stdout.decode("utf-8", "replace")


def git_state(root: Path = ROOT) -> dict:
    """HEAD, whether anything tracked or untracked-and-not-ignored differs, and what."""
    commit = (_git(root, "rev-parse", "HEAD") or "").strip() or None
    status = _git(root, "status", "--porcelain", "--untracked-files=normal")
    lines = [line for line in (status or "").splitlines() if line.strip()]
    return {"commit": commit, "dirty": bool(lines) or status is None or commit is None,
            "changes": sorted(line[3:] for line in lines),
            "branch": (_git(root, "rev-parse", "--abbrev-ref", "HEAD") or "").strip() or None}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def environment_lock() -> dict:
    """Interpreter, platform, BLAS and every installed distribution, with one digest over the list."""
    distributions = sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()
                            if d.metadata.get("Name")}, key=str.lower)
    versions = {}
    for name in RUNTIME_PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    blas = []
    try:
        from threadpoolctl import threadpool_info
        blas = [{k: v for k, v in info.items() if k in ("internal_api", "version", "threading_layer", "architecture")}
                for info in threadpool_info()]
    except Exception:  # noqa: BLE001 - a missing optional probe is recorded as absent, not fatal
        blas = []
    return {"python": sys.version.split()[0], "implementation": platform.python_implementation(),
            "executable": sys.executable, "platform": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor(), "float": "float64", "runtime_versions": versions, "blas": blas,
            "distributions": distributions, "distributions_sha256": sha256_bytes("\n".join(distributions).encode())}


def _tracked(root: Path, relative: str) -> bool:
    return _git(root, "ls-files", "--error-unmatch", "--", relative) is not None


def _lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def content_sha256(root: Path, relative: str) -> str:
    """Tracked files: SHA-256 of the LF-normalised content (the blob git stores, whatever the checkout's
    line endings). Untracked data: SHA-256 of the raw bytes. Protocol v1 hashed raw working bytes, so
    its digests changed with a checkout's line endings (58 tracked files were CRLF on 2026-09-27)."""
    path = root / relative
    return sha256_bytes(_lf(path.read_bytes())) if _tracked(root, relative) else sha256_file(path)


def _digests(root: Path, paths) -> dict:
    out, missing = {}, []
    for p in paths:
        relative = str(Path(p).as_posix())
        if not (root / relative).is_file():
            missing.append(relative)
            continue
        out[relative] = content_sha256(root, relative)
    if missing:
        raise FileNotFoundError(f"cannot digest missing files: {missing}")
    return out


def _record(experiment, *, protocol_files, manifest_files, code_files, data_files, command, seed, root, git,
            registered: bool) -> dict:
    return {"protocol_version": PROTOCOL_VERSION, "experiment": experiment, "registered": registered,
            "status": "registered" if registered else "development_unregistered",
            "recorded_at": datetime.now(TIMEZONE).isoformat(timespec="seconds"),
            "git_commit": git["commit"], "git_dirty": git["dirty"], "git_changes": git["changes"],
            "git_branch": git["branch"],
            "protocol_sha256": _digests(root, protocol_files), "manifest_sha256": _digests(root, manifest_files),
            "code_sha256": _digests(root, code_files), "data_sha256": _digests(root, data_files),
            "environment_lock": environment_lock(), "command": list(command), "random_seed": seed}


def _write_once(path: Path, record: dict) -> dict:
    path = Path(path)
    if path.exists():
        raise AlreadyRegistered(f"{path} exists; register a new experiment name instead of rewriting it")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, indent=1, sort_keys=True).encode("utf-8") + b"\n"
    record = {**record, "record_sha256": sha256_bytes(payload)}
    path.write_bytes(json.dumps(record, indent=1, sort_keys=True).encode("utf-8") + b"\n")
    os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    return record


def register(path, experiment: str, *, protocol_files, manifest_files=(), code_files=(), data_files=(),
             command=None, seed=None, root: Path = ROOT) -> dict:
    """Register an experiment: a clean tree, a new record, every digest, then read-only."""
    git = git_state(root)
    if git["dirty"]:
        raise DirtyTree(f"registration refused: working tree is dirty ({len(git['changes'])} paths): "
                        f"{git['changes'][:10]}")
    record = _record(experiment, protocol_files=protocol_files, manifest_files=manifest_files, code_files=code_files,
                     data_files=data_files, command=command or sys.argv, seed=seed, root=root, git=git,
                     registered=True)
    return _write_once(path, record)


def development_record(path, experiment: str, *, protocol_files, manifest_files=(), code_files=(), data_files=(),
                       command=None, seed=None, root: Path = ROOT) -> dict:
    """The same record for a development run; allowed on a dirty tree and marked unregistered."""
    git = git_state(root)
    record = _record(experiment, protocol_files=protocol_files, manifest_files=manifest_files, code_files=code_files,
                     data_files=data_files, command=command or sys.argv, seed=seed, root=root, git=git,
                     registered=False)
    return _write_once(path, record)


def verify_at_commit(digests: dict, commit: str, root: Path = ROOT) -> dict:
    """Digests against the commit's blobs (tracked files) or the disk (untracked data).

    Each file gets a status:
    - `exact`: the blob (or LF-normalised blob) has the digest;
    - `eol_equivalent`: the digest was taken of a CRLF or mixed-ending checkout of the same
      content. Shown either by the blob converted to CRLF, or by a disk file that still has the
      digest and equals the blob once line endings are normalised;
    - `disk`: untracked data whose bytes still have the digest;
    - `changed` or `missing` otherwise. Only these two are problems.
    """
    problems, status = [], {}
    for relative, expected in digests.items():
        blob = _git(root, "cat-file", "blob", f"{commit}:{relative}", binary=True)
        path = root / relative
        disk = path.read_bytes() if path.is_file() else None
        if blob is not None:
            if expected in (sha256_bytes(blob), sha256_bytes(_lf(blob))):
                status[relative] = "exact"
            elif sha256_bytes(_lf(blob).replace(b"\n", b"\r\n")) == expected or (
                    disk is not None and sha256_bytes(disk) == expected and _lf(disk) == _lf(blob)):
                status[relative] = "eol_equivalent"
            else:
                status[relative] = "changed"
        elif disk is not None:
            status[relative] = "disk" if sha256_bytes(disk) == expected else "changed"
        else:
            status[relative] = "missing"
        if status[relative] in ("changed", "missing"):
            problems.append(f"{status[relative]}:{relative}")
    return {"commit": commit, "problems": problems, "status": status}


def replay_instructions(record: dict) -> list[str]:
    """How to re-run a registered experiment: from a worktree at its commit, with its command."""
    commit = record.get("git_commit") or record.get("git", {}).get("commit")
    name = record.get("experiment") or record.get("protocol_version", "experiment")
    return [f"git worktree add ../MAESTRO_{name} {commit}",
            f"cd ../MAESTRO_{name}  # copy or link the untracked data and outputs the record lists",
            " ".join(record.get("command") or ["<command recorded with the experiment>"])]


def _close(a, b, tol: float = 1e-8) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
        except (TypeError, ValueError):
            return False
    return a == b


def compare_decisions(old: list[dict], new: list[dict], *, key=("arm", "compound", "h1", "h2"),
                      tol: float = 1e-8) -> dict:
    """Decision-level replay integrity between two record lists (order-insensitive)."""
    def index(rows):
        out = {}
        for r in rows:
            k = tuple(r.get(f) if f != "arm" else (r.get("arm") or r.get("policy")) for f in key)
            out.setdefault(k, []).append(r)
        return out

    a, b = index(old), index(new)
    problems = []
    for k in sorted(set(a) | set(b), key=repr):
        if k not in a or k not in b:
            problems.append({"episode": k, "problem": "missing_in_" + ("new" if k not in b else "old")})
            continue
        if len(a[k]) != len(b[k]):
            problems.append({"episode": k, "problem": "record_count_differs"})
            continue
        for x, y in zip(a[k], b[k]):
            fields = [f for f in DECISION_FIELDS if f in x or f in y]
            for f in fields:
                same = _close(x.get(f), y.get(f), tol) if isinstance(x.get(f), float) else x.get(f) == y.get(f)
                if not same:
                    problems.append({"episode": k, "problem": f"{f}_differs"})
            xs, ys = x.get("steps") or [], y.get("steps") or []
            if len(xs) != len(ys):
                problems.append({"episode": k, "problem": "step_count_differs"})
                continue
            for i, (s, t) in enumerate(zip(xs, ys)):
                for f in STEP_FIELDS:
                    if (f in s or f in t) and s.get(f) != t.get(f):
                        problems.append({"episode": k, "problem": f"step{i}_{f}_differs"})
    return {"episodes_old": len(a), "episodes_new": len(b), "problems": problems[:200],
            "problem_count": len(problems), "identical_decisions": not problems}
