"""Verify exact source identity and freeze/byte accounting for the finite prior audit."""
import hashlib
import json
from pathlib import Path

from auditor_primary_prior import arxiv_metadata, crossref_metadata

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_state_refinement_review/primary_prior"


def main():
    target = OUT / "VERIFICATION.json"
    if target.exists():
        raise RuntimeError("Prior verification exists")
    checks = 0
    def check(value):
        nonlocal checks
        if not value:
            raise AssertionError("Primary prior identity invariant failed")
        checks += 1
    def load(name):
        return json.loads((OUT / name).read_text(encoding="utf-8"))
    for name, expected in load("PRE_REQUEST_FREEZE.json")["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
    ledger = load("NETWORK.json")
    check(len(ledger["requests"]) == 2)
    check(sum(r["bytes"] for r in ledger["requests"]) == ledger["consumed_HTTP_body_bytes"] == 9847 <= 500000)
    for receipt in ledger["requests"]:
        raw = (OUT / f"{receipt['name']}_SOURCE.body").read_bytes()
        check(len(raw) == receipt["bytes"])
        check(hashlib.sha256(raw).hexdigest() == receipt["sha256"])
        check(receipt["status"] == 200 and not receipt["truncated_at_shared_cap"] and receipt["metadata_projection"] == "SUCCESS")
        parsed = arxiv_metadata(raw) if receipt["name"] == "ARXIV" else crossref_metadata(raw)
        check(parsed == load(f"{receipt['name']}_METADATA.json"))
    arxiv = load("ARXIV_METADATA.json")["records"]
    check({r["id"] for r in arxiv} == {"http://arxiv.org/abs/cs/0406011v1", "http://arxiv.org/abs/1207.4167v1"})
    check({r["title"] for r in arxiv} == {"Blind Construction of Optimal Nonlinear Recursive Predictors for Discrete Sequences", "Predictive State Representations: A New Theory for Modeling Dynamical Systems"})
    check(all(r["abstract"] and r["authors"] for r in arxiv))
    crossref = load("CROSSREF_METADATA.json")["records"][0]
    check(crossref["DOI"] == "10.1016/0890-5401(87)90052-6")
    check(crossref["title"] == ["Learning regular sets from queries and counterexamples"])
    check(crossref["abstract"] is None)
    result = {"status": "PASS", "checks": checks, "HTTP_requests": 2, "consumed_HTTP_body_bytes": 9847,
              "frozen_protocol_and_acquisition_code_unchanged": True,
              "both_expected_arxiv_ID_title_pairs_matched": True,
              "Angluin_exact_DOI_title_metadata_matched_abstract_unavailable": True,
              "full_method_or_algorithm_steps_verified": False,
              "scope": "Exact primary metadata identity, faithful parsed abstracts, frozen bytes and finite access accounting"}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
