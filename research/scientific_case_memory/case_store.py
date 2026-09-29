"""Append-only, digest-chained store for cases.

File summary
- Path: research/scientific_case_memory/case_store.py
- Purpose: hold cases so that nothing is ever edited in place. A new fact about a case is a new
  version that names the digest of the version it supersedes; the store refuses everything else.
- Core points:
  - `append` accepts a new case id at version 1, or the next version of a known id whose
    `supersedes` equals the digest of the latest version. Re-adding identical content is a no-op;
    the same id and version with different content is refused (`VersionConflict`).
  - `verify` recomputes every digest and every supersession link, so a hand-edited file is
    detected rather than trusted.
  - The file format is JSON lines, optionally gzip. A snapshot's `snapshot_digest` is the digest of
    its sorted (case id, version, digest) triples: two memories with the same digest hold exactly
    the same cases, whichever order they were written in.
  - `latest` is what retrieval reads; `versions` is the history. A case whose measurement arrives
    later is `supersede`d, so the calibration history of a memory can always be replayed.
- Interfaces: `CaseStore`, `VersionConflict`, `StoreCorrupt`
- Depends on: case_schema.py
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Iterable, Iterator

from . import case_schema as S


def open_text(path: Path, mode: str):
    """Text opener for JSON lines. Gzip output carries no timestamp, so equal content gives an equal
    file hash; appending is only supported for plain files."""
    path = Path(path)
    if not str(path).endswith(".gz"):
        return open(path, mode.replace("t", ""), encoding="utf-8", newline="\n" if "r" not in mode else None)
    if "r" in mode:
        return gzip.open(path, "rt", encoding="utf-8")
    if "a" in mode:
        raise ValueError("append_to_gzip_unsupported")

    class _Gz(io.TextIOWrapper):
        def close(self):  # closes the underlying file too, which GzipFile would leave open
            try:
                super().close()
            finally:
                handle.close()

    handle = open(path, "wb")
    return _Gz(gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0), encoding="utf-8", newline="\n")


class VersionConflict(ValueError):
    """A case id/version already exists with different content, or a supersession link is wrong."""


class StoreCorrupt(ValueError):
    """A stored line does not match its recorded digest or supersession chain."""


class CaseStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._versions: dict[str, list[S.Case]] = {}
        if self.path and self.path.exists():
            for case in self._read(self.path):
                self._admit(case, persist=False)

    # ---------------------------------------------------------------- reading
    @staticmethod
    def _read(path: Path) -> Iterator[S.Case]:
        with open_text(path, "rt") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                case = S.case_from_dict(row["case"])
                if S.digest(case) != row["digest"]:
                    raise StoreCorrupt(f"digest_mismatch:{row['case']['case_id']}:v{row['case']['case_version']}")
                yield case

    def __len__(self) -> int:
        return len(self._versions)

    def __contains__(self, case_id: str) -> bool:
        return case_id in self._versions

    def ids(self) -> list[str]:
        return sorted(self._versions)

    def get(self, case_id: str, version: int | None = None) -> S.Case:
        history = self._versions[case_id]
        if version is None:
            return history[-1]
        return next(c for c in history if c.case_version == version)

    def versions(self, case_id: str) -> tuple[S.Case, ...]:
        return tuple(self._versions[case_id])

    def latest(self) -> list[S.Case]:
        return [self._versions[i][-1] for i in sorted(self._versions)]

    def all_versions(self) -> list[S.Case]:
        return [c for i in sorted(self._versions) for c in self._versions[i]]

    # ---------------------------------------------------------------- writing
    def _admit(self, case: S.Case, *, persist: bool) -> bool:
        history = self._versions.setdefault(case.case_id, [])
        new_digest = S.digest(case)
        for existing in history:
            if existing.case_version == case.case_version:
                if S.digest(existing) == new_digest:
                    return False
                raise VersionConflict(f"version_exists_with_different_content:{case.case_id}:v{case.case_version}")
        if not history:
            if case.case_version != 1 or case.supersedes:
                self._versions.pop(case.case_id)
                raise VersionConflict(f"first_version_must_be_1_without_supersedes:{case.case_id}")
        else:
            latest = history[-1]
            if case.case_version != latest.case_version + 1:
                raise VersionConflict(f"version_gap:{case.case_id}:{latest.case_version}->{case.case_version}")
            if case.supersedes != S.digest(latest):
                raise VersionConflict(f"supersedes_mismatch:{case.case_id}")
        errors = S.validate_case(case)
        if errors:
            if not history:
                self._versions.pop(case.case_id, None)
            raise ValueError("invalid_case:" + ",".join(errors))
        history.append(case)
        if persist and self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open_text(self.path, "at") as fh:
                fh.write(json.dumps({"digest": new_digest, "case": S.to_dict(case)}, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False) + "\n")
        return True

    def append(self, case: S.Case) -> bool:
        """Add a case; True when the store changed, False when identical content was already there."""
        return self._admit(case, persist=True)

    def append_many(self, cases: Iterable[S.Case]) -> int:
        return sum(self.append(c) for c in cases)

    def supersede(self, previous: S.Case, **changes) -> S.Case:
        """A new version of `previous` with `changes` applied, linked to it by digest, then appended."""
        from dataclasses import replace
        latest = self.get(previous.case_id)
        if S.digest(latest) != S.digest(previous):
            raise VersionConflict(f"stale_previous:{previous.case_id}")
        new = replace(latest, case_version=latest.case_version + 1, supersedes=S.digest(latest), **changes)
        self.append(new)
        return new

    # ---------------------------------------------------------------- integrity
    def verify(self) -> tuple[str, ...]:
        """Recompute every digest and supersession link; return named problems (empty when sound)."""
        problems: list[str] = []
        for case_id, history in self._versions.items():
            for i, case in enumerate(history):
                if case.case_version != i + 1:
                    problems.append(f"version_sequence:{case_id}")
                previous = S.digest(history[i - 1]) if i else None
                if case.supersedes != previous:
                    problems.append(f"supersedes_chain:{case_id}:v{case.case_version}")
                for error in S.validate_case(case):
                    problems.append(f"schema:{case_id}:{error}")
        return tuple(problems)

    def snapshot_digest(self, latest_only: bool = True) -> str:
        cases = self.latest() if latest_only else self.all_versions()
        triples = sorted((c.case_id, c.case_version, S.digest(c)) for c in cases)
        return hashlib.sha256(json.dumps(triples, separators=(",", ":")).encode("utf-8")).hexdigest()

    def write_snapshot(self, path: str | Path, *, latest_only: bool = False) -> str:
        """Write every version (or the latest only) to a fresh file and return its SHA-256."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cases = self.latest() if latest_only else self.all_versions()
        with open_text(path, "wt") as fh:
            for case in cases:
                fh.write(json.dumps({"digest": S.digest(case), "case": S.to_dict(case)}, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False) + "\n")
        return hashlib.sha256(path.read_bytes()).hexdigest()
