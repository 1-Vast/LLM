"""Execution-grounded claim audit: every reported number is checked against an immutable run record.

Claims bind to re-read run artifacts, including negative, failed and excluded runs. This audit does not establish freedom from leakage."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence


class RunStatus(str, Enum):
    SUCCEEDED = "succeeded"
    NEGATIVE = "negative"
    FAILED = "failed"
    EXCLUDED = "excluded"


class ClaimVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    ARTIFACT_MISSING = "ARTIFACT_MISSING"
    ARTIFACT_MODIFIED = "ARTIFACT_MODIFIED"
    POINTER_MISSING = "POINTER_MISSING"
    RUN_UNKNOWN = "RUN_UNKNOWN"
    FROM_FAILED_RUN = "FROM_FAILED_RUN"
    FROM_EXCLUDED_RUN = "FROM_EXCLUDED_RUN"


def file_sha256(path: Path) -> str:
    """Digest with CRLF normalised to LF, so a checkout's line endings do not change identity."""

    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    status: RunStatus
    artifact: str
    sha256: str
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.artifact.strip():
            raise ValueError("a run needs an identifier and an artifact path")
        if not isinstance(self.status, RunStatus):
            raise TypeError("run status must be a RunStatus")
        if self.status in (RunStatus.FAILED, RunStatus.EXCLUDED) and not self.reason.strip():
            raise ValueError(f"run {self.run_id} is {self.status.value} and must state why")
        if len(self.sha256) != 64 and not (self.status == RunStatus.FAILED and self.sha256 == ""):
            raise ValueError("run digest must be a sha256 hex string")


@dataclass(frozen=True)
class RunManifest:
    runs: tuple[RunRecord, ...]
    roots: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ("*.json",)

    def __post_init__(self) -> None:
        ids = [r.run_id for r in self.runs]
        if len(ids) != len(set(ids)):
            raise ValueError("run identifiers must be unique")

    def get(self, run_id: str) -> RunRecord | None:
        return next((r for r in self.runs if r.run_id == run_id), None)

    @classmethod
    def from_json(cls, data: dict) -> "RunManifest":
        runs = tuple(RunRecord(r["run_id"], RunStatus(r["status"]), r["artifact"], r["sha256"], r.get("reason", "")) for r in data["runs"])
        return cls(runs, tuple(data.get("roots", ())), tuple(data.get("patterns", ("*.json",))))


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    run_id: str
    pointer: tuple[str, ...]
    relation: str
    value: float | str | bool
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if self.relation not in ("==", "<=", ">=", "<", ">", "approx", "count"):
            raise ValueError("claim relation must be one of ==, <=, >=, <, >, approx, count")
        if self.relation == "approx" and not (isinstance(self.tolerance, (int, float)) and self.tolerance > 0):
            raise ValueError("an approximate claim needs a positive tolerance")


@dataclass(frozen=True)
class ClaimResult:
    claim_id: str
    verdict: ClaimVerdict
    observed: object = None


@dataclass(frozen=True)
class AuditReport:
    results: tuple[ClaimResult, ...]
    findings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.findings and all(r.verdict == ClaimVerdict.SUPPORTED for r in self.results)

    @property
    def unsupported(self) -> int:
        return sum(r.verdict != ClaimVerdict.SUPPORTED for r in self.results)

    def summary(self) -> dict:
        counts: dict = {}
        for r in self.results:
            counts[r.verdict.value] = counts.get(r.verdict.value, 0) + 1
        return {"claims": len(self.results), "verdicts": counts, "findings": list(self.findings), "passed": self.passed}


def _lookup(data, pointer: Sequence[str]):
    for key in pointer:
        if isinstance(data, dict) and key in data:
            data = data[key]
        elif isinstance(data, list) and key.lstrip("-").isdigit() and -len(data) <= int(key) < len(data):
            data = data[int(key)]
        else:
            raise KeyError(key)
    return data


def _compare(observed, relation: str, value, tolerance: float) -> bool:
    if relation == "count":
        return isinstance(observed, (list, dict)) and len(observed) == value
    if relation == "==":
        if isinstance(value, float) or isinstance(observed, float):
            return isinstance(observed, (int, float)) and not isinstance(observed, bool) and math.isclose(float(observed), float(value), rel_tol=0, abs_tol=1e-12)
        return observed == value
    if isinstance(observed, bool) or not isinstance(observed, (int, float)):
        return False
    if relation == "approx":
        return abs(float(observed) - float(value)) <= tolerance
    return {"<=": observed <= value, ">=": observed >= value, "<": observed < value, ">": observed > value}[relation]


def audit(claims: Iterable[Claim], manifest: RunManifest, root: Path) -> AuditReport:
    root = Path(root)
    results, cited = [], set()
    loaded: dict = {}
    for claim in claims:
        run = manifest.get(claim.run_id)
        if run is None:
            results.append(ClaimResult(claim.claim_id, ClaimVerdict.RUN_UNKNOWN))
            continue
        cited.add(run.run_id)
        if run.status == RunStatus.FAILED:
            results.append(ClaimResult(claim.claim_id, ClaimVerdict.FROM_FAILED_RUN))
            continue
        if run.status == RunStatus.EXCLUDED:
            results.append(ClaimResult(claim.claim_id, ClaimVerdict.FROM_EXCLUDED_RUN))
            continue
        path = root / run.artifact
        if not path.is_file():
            results.append(ClaimResult(claim.claim_id, ClaimVerdict.ARTIFACT_MISSING))
            continue
        if file_sha256(path) != run.sha256:
            results.append(ClaimResult(claim.claim_id, ClaimVerdict.ARTIFACT_MODIFIED))
            continue
        if run.artifact not in loaded:
            loaded[run.artifact] = json.loads(path.read_text(encoding="utf-8"))
        try:
            observed = _lookup(loaded[run.artifact], claim.pointer)
        except KeyError:
            results.append(ClaimResult(claim.claim_id, ClaimVerdict.POINTER_MISSING))
            continue
        ok = _compare(observed, claim.relation, claim.value, claim.tolerance)
        results.append(ClaimResult(claim.claim_id, ClaimVerdict.SUPPORTED if ok else ClaimVerdict.CONTRADICTED, observed))
    findings = [f"OMITTED_NEGATIVE_RUN:{r.run_id}" for r in manifest.runs if r.status == RunStatus.NEGATIVE and r.run_id not in cited]
    listed = {Path(r.artifact).as_posix() for r in manifest.runs}
    for base in manifest.roots:
        for pattern in manifest.patterns:
            for path in sorted((root / base).glob(pattern)):
                relative = path.relative_to(root).as_posix()
                if relative not in listed:
                    findings.append(f"MANIFEST_INCOMPLETE:{relative}")
    return AuditReport(tuple(results), tuple(findings))
