"""Contracts of the execution-grounded claim audit (maestro.claim_audit)."""
import json

import pytest

from maestro.claim_audit import Claim, ClaimVerdict, RunManifest, RunRecord, RunStatus, audit, file_sha256


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, indent=1) + "\n").encode())
    return file_sha256(path)


@pytest.fixture
def study(tmp_path):
    ok = _write(tmp_path / "runs" / "primary.json", {"primary": {"P2": {"difference": 14.0, "p_greater": 0.003, "verdict": "CONFIRMED"}},
                                                    "arms": [{"hits": 76}, {"hits": 62}]})
    neg = _write(tmp_path / "runs" / "memory.json", {"MEM-NO_MEM": {"difference": -1.0, "verdict": "NOT_CONFIRMED"}})
    bad = _write(tmp_path / "runs" / "crashed.json", {"hits": 99})
    manifest = RunManifest((RunRecord("primary", RunStatus.SUCCEEDED, "runs/primary.json", ok),
                            RunRecord("memory", RunStatus.NEGATIVE, "runs/memory.json", neg),
                            RunRecord("crashed", RunStatus.FAILED, "runs/crashed.json", bad, reason="out of memory")),
                           roots=("runs",))
    return tmp_path, manifest


def test_supported_claims_pass_only_when_negatives_are_reported(study):
    root, manifest = study
    claims = [Claim("c1", "P2 confirmed", "primary", ("primary", "P2", "verdict"), "==", "CONFIRMED"),
              Claim("c2", "MAESTRO_LOOP found 76 hits", "primary", ("arms", "0", "hits"), "==", 76),
              Claim("c3", "p below 0.025", "primary", ("primary", "P2", "p_greater"), "<=", 0.025)]
    report = audit(claims, manifest, root)
    assert all(r.verdict == ClaimVerdict.SUPPORTED for r in report.results)
    assert report.findings == ("OMITTED_NEGATIVE_RUN:memory",) and not report.passed
    claims.append(Claim("c4", "memory did not help", "memory", ("MEM-NO_MEM", "verdict"), "==", "NOT_CONFIRMED"))
    assert audit(claims, manifest, root).passed


def test_contradicted_inflated_and_misattributed_claims_are_caught(study):
    root, manifest = study
    claims = [Claim("inflated", "80 hits", "primary", ("arms", "0", "hits"), "==", 80),
              Claim("rounded", "difference about 14", "primary", ("primary", "P2", "difference"), "approx", 15.0, tolerance=0.5),
              Claim("pointer", "a number that is not there", "primary", ("primary", "P3", "difference"), "==", 1.0),
              Claim("ghost", "an unlisted run", "secret", ("x",), "==", 1),
              Claim("failed", "a crashed run's number", "crashed", ("hits",), "==", 99),
              Claim("typed", "a string is not a number", "primary", ("primary", "P2", "verdict"), ">=", 1.0),
              Claim("memory", "negative reported", "memory", ("MEM-NO_MEM", "difference"), "<", 0.0),
              Claim("count", "two arms listed", "primary", ("arms",), "count", 2),
              Claim("miscount", "three arms listed", "primary", ("arms",), "count", 3),
              Claim("list_as_number", "a list is not a number", "primary", ("arms",), "==", 2)]
    verdicts = {r.claim_id: r.verdict for r in audit(claims, manifest, root).results}
    assert verdicts == {"inflated": ClaimVerdict.CONTRADICTED, "rounded": ClaimVerdict.CONTRADICTED,
                        "pointer": ClaimVerdict.POINTER_MISSING, "ghost": ClaimVerdict.RUN_UNKNOWN,
                        "failed": ClaimVerdict.FROM_FAILED_RUN, "typed": ClaimVerdict.CONTRADICTED,
                        "memory": ClaimVerdict.SUPPORTED, "count": ClaimVerdict.SUPPORTED,
                        "miscount": ClaimVerdict.CONTRADICTED, "list_as_number": ClaimVerdict.CONTRADICTED}


def test_modified_or_missing_artifacts_and_unlisted_runs_fail(study):
    root, manifest = study
    claim = Claim("c", "76 hits", "primary", ("arms", "0", "hits"), "==", 76)
    data = json.loads((root / "runs" / "primary.json").read_text())
    data["arms"][0]["hits"] = 76.0 + 0                              # same value, different bytes
    (root / "runs" / "primary.json").write_bytes(json.dumps(data).encode())
    assert audit([claim], manifest, root).results[0].verdict == ClaimVerdict.ARTIFACT_MODIFIED
    (root / "runs" / "primary.json").unlink()
    assert audit([claim], manifest, root).results[0].verdict == ClaimVerdict.ARTIFACT_MISSING
    _write(root / "runs" / "rerun_with_better_seed.json", {"hits": 90})
    assert "MANIFEST_INCOMPLETE:runs/rerun_with_better_seed.json" in audit([claim], manifest, root).findings


def test_crlf_checkouts_keep_the_same_digest(tmp_path):
    (tmp_path / "a.json").write_bytes(b'{"x": 1}\n')
    (tmp_path / "b.json").write_bytes(b'{"x": 1}\r\n')
    assert file_sha256(tmp_path / "a.json") == file_sha256(tmp_path / "b.json")


def test_manifest_requires_reasons_for_failed_and_excluded_runs():
    with pytest.raises(ValueError, match="must state why"):
        RunRecord("x", RunStatus.EXCLUDED, "runs/x.json", "0" * 64)
    assert RunRecord("crash", RunStatus.FAILED, "script.py", "", reason="refused before writing").sha256 == ""
    with pytest.raises(ValueError, match="sha256"):
        RunRecord("x", RunStatus.SUCCEEDED, "runs/x.json", "")
    with pytest.raises(ValueError, match="must state why"):
        RunRecord("crash", RunStatus.FAILED, "script.py", "")
    with pytest.raises(ValueError, match="unique"):
        RunManifest((RunRecord("x", RunStatus.SUCCEEDED, "a.json", "0" * 64), RunRecord("x", RunStatus.SUCCEEDED, "b.json", "0" * 64)))
    data = {"runs": [{"run_id": "x", "status": "negative", "artifact": "a.json", "sha256": "0" * 64}], "roots": ["runs"]}
    assert RunManifest.from_json(data).get("x").status == RunStatus.NEGATIVE
