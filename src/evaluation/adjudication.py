"""Blind adjudication: two fixed adjudicators, neither of which sees an arm's output.

File summary
- Path: src/evaluation/adjudication.py
- Purpose: produce, for each case, the set of development actions the evidence supports, from
  two adjudicators fixed before any arm output is compared to them - the package's own
  licensing rules, and an independent reviewer given the whole evidence and nothing else.
  Without this the section 37 table can never be evidence for the core claim, however
  complete its rows are.
- Core points:
  - The packet contains the premise, the registered explanations, the menu's declarations and
    every hidden record the case holds. It contains no licensing rule, no policy name, no
    decision and no arm output, so a reviewer cannot recognise a strategy's answer.
  - The mechanical adjudicator is the package's frozen rule set evaluated with every record
    revealed; its digest is recorded per case.
  - Agreement is reported as raw agreement on the supported set and as Cohen's kappa over
    per-action binary judgements, with every disagreement listed and both verdicts quoted. A
    disputed case is reported separately and never merged into a headline rate.
  - The reviewer shares a model family with two of the evaluated arms, which is a stated
    weakness of the protocol and is reported beside every agreement figure.
- Interfaces: `REVIEWER_PROMPT`, `adjudication_packet`, `mechanical_verdict`, `review_case`,
  `agreement`, `adjudicate_package`, `main`
- Depends on: evaluation.cases, evaluation.scoring, evaluation.provider_spend
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.cases import CaseRepository, ReplayCase, RevealedEvidence  # noqa: E402
from evaluation.provider_spend import SpendLedger  # noqa: E402
from evaluation.scoring import licensed_decisions  # noqa: E402

REVIEWER_PROMPT = (
    "You are an independent reviewer of one experimental case. You are given the evidence that "
    "exists for it: the starting records, the registered competing explanations and the "
    "development action each one implies, the measurements that could be bought and what each "
    "was declared to show, and every result that was actually obtained, including results that "
    "were held back from the people who worked on the case.\n\n"
    "You are not given anyone's decision, and you are not given any scoring rule. Judge the "
    "evidence itself.\n\n"
    "Return one JSON object and nothing else:\n"
    '  {"supported_decisions": ["<development action>", ...], '
    '"ruled_out": ["<development action>", ...], '
    '"minimum_evidence": ["<record identifier>", ...], '
    '"rationale": "<two sentences at most>"}\n\n'
    "Use only the development actions listed in the case. 'defer' means the evidence does not "
    "support acting on either explanation; include it when that is your judgement, alone or "
    "beside another action. A decision is supported only if every explanation still compatible "
    "with the evidence would accept it."
)


def _record_payload(record: RevealedEvidence) -> Mapping[str, object]:
    """One record as an adjudicator needs it: the claim, its numbers and its two main limits.

    The packet is deliberately terse. A reviewer that reasons before it answers spends its
    completion budget in proportion to what it was given, and repeating a record's conditions
    after its statement has already named them buys no evidence: the first runs returned
    `finish_reason=length` with no content at all on 8 to 13 kilobyte packets.
    """

    return {
        "identifier": record.action_identifier,
        "outcome": record.outcome,
        "statement": record.statement,
        "metrics": dict(record.metrics),
        "quality": record.biological_quality,
        "evidence_kind": record.evidence_kind.value,
        "limitations": list(record.limitations)[:2],
    }


def adjudication_packet(case: ReplayCase, outcomes: Mapping[str, RevealedEvidence]) -> Mapping[str, object]:
    """Everything an adjudicator may see: the evidence, and no one's answer."""

    public = case.public
    return {
        "case": public.identifier,
        "context_identifier": public.context_identifier,
        "starting_records": [
            {
                "identifier": item.identifier,
                "statement": item.statement,
                "evidence_kind": item.evidence_kind.value,
                "limitations": list(item.limitations)[:2],
            }
            for item in public.initial_evidence
        ],
        "explanations": [
            {
                "identifier": item["identifier"],
                "description": item["description"],
                "development_action": item["development_action"],
            }
            for item in public.hypotheses
        ],
        "measurements_offered": [
            {
                "identifier": item.action.identifier,
                "quantity": item.action.quantity.value,
                "available": item.available,
                "declared_outcome_by_explanation": dict(item.action.expected_outcomes),
                "interpretation_gate": item.action.interpretation_gate,
            }
            for item in public.actions
        ],
        "results_obtained": [_record_payload(record) for record in outcomes.values()],
        "results_obtained_by_repair": [
            _record_payload(record) for record in case.scoring.repair_outcomes.values()
        ],
        "results_held_back_from_everyone": [
            {
                "identifier": record.identifier,
                "statement": record.statement,
                "outcome": record.outcome,
                "quality": record.biological_quality,
                "evidence_kind": record.evidence_kind.value,
                "limitations": list(record.limitations)[:2],
            }
            for record in case.scoring.final_test
        ],
        "case_limitations": list(public.limitations)[:4],
    }


def mechanical_verdict(case: ReplayCase, outcomes: Mapping[str, RevealedEvidence]) -> tuple[str, ...]:
    """What the package's own frozen rules license once every record is revealed."""

    observed = dict(outcomes)
    observed.update(case.scoring.repair_outcomes)
    return tuple(sorted(item.value for item in licensed_decisions(case, observed)))


@dataclass(frozen=True)
class ReviewerVerdict:
    """One reviewer answer, or a named failure in its place."""

    case: str
    supported: tuple[str, ...]
    ruled_out: tuple[str, ...]
    minimum_evidence: tuple[str, ...]
    rationale: str
    refusal: str | None = None

    def payload(self) -> Mapping[str, object]:
        return {
            "case": self.case,
            "supported_decisions": list(self.supported),
            "ruled_out": list(self.ruled_out),
            "minimum_evidence": list(self.minimum_evidence),
            "rationale": self.rationale,
            "refusal": self.refusal,
        }


def review_case(
    client,
    packet: Mapping[str, object],
    *,
    registered_actions: Sequence[str],
    ledger: SpendLedger | None = None,
    # The configured model reasons at length before emitting an object, and reasoning counts
    # against this budget: at 4000 the first runs returned `finish_reason=length` with no
    # content at all, and at 12000 eleven of fifty-eight still did while successful calls used
    # a mean of 7,659 completion tokens and a maximum of 11,689. A cap inside the observed
    # distribution does not fail at random: it drops the cases with the most evidence to weigh.
    # The budget is a cap, not a charge; only tokens actually produced are paid for.
    max_tokens: int = 20000,
    estimate_usd: float = 0.020,
) -> ReviewerVerdict:
    """One reviewer call, priced into the ledger, with provider failure recorded by name."""

    case = str(packet.get("case", "unknown"))
    if ledger is not None:
        ledger.reserve(f"adjudication:{case}", estimate_usd)
    try:
        payload, response = client.complete_json(
            [
                {"role": "system", "content": REVIEWER_PROMPT},
                {"role": "user", "content": json.dumps(packet, ensure_ascii=False, sort_keys=True)},
            ],
            max_tokens=max_tokens,
        )
    except Exception as error:  # a provider failure is data, not a crash
        detail = str(error)[:300]
        if ledger is not None:
            ledger.charge(
                f"adjudication:{case}",
                None,
                status="failed",
                reserved_usd=estimate_usd,
                note=f"{type(error).__name__}: {detail}; charged at reservation because tokens may have been processed",
            )
        return ReviewerVerdict(
            case, (), (), (), detail, refusal=f"provider_failure:{type(error).__name__}"
        )
    if ledger is not None:
        ledger.charge(f"adjudication:{case}", dict(response.usage), status="ok", reserved_usd=estimate_usd)
    allowed = set(registered_actions)
    supported = tuple(
        sorted({str(item) for item in payload.get("supported_decisions", []) if str(item) in allowed})
    )
    ruled_out = tuple(sorted({str(item) for item in payload.get("ruled_out", []) if str(item) in allowed}))
    unknown = [
        str(item) for item in payload.get("supported_decisions", []) if str(item) not in allowed
    ]
    refusal = f"reviewer_named_unregistered_action:{','.join(sorted(set(unknown)))}" if unknown else None
    return ReviewerVerdict(
        case=case,
        supported=supported,
        ruled_out=ruled_out,
        minimum_evidence=tuple(str(item) for item in payload.get("minimum_evidence", [])),
        rationale=str(payload.get("rationale", ""))[:400],
        refusal=refusal,
    )


def agreement(
    mechanical: Mapping[str, Sequence[str]],
    reviewer: Mapping[str, ReviewerVerdict],
    *,
    registered_actions: Sequence[str],
) -> Mapping[str, object]:
    """Raw agreement on the supported set, Cohen's kappa per action, and every disagreement.

    Kappa is computed over per-(case, action) binary judgements - supported or not - because
    the adjudicators return sets rather than one label, and a set comparison with no chance
    correction would read as agreement wherever both sets are mostly empty.
    """

    cases = [case for case in sorted(mechanical) if case in reviewer and reviewer[case].refusal is None]
    actions = sorted(set(registered_actions))
    both = agree = 0
    table = {(True, True): 0, (True, False): 0, (False, True): 0, (False, False): 0}
    disagreements: list[Mapping[str, object]] = []
    for case in cases:
        left = set(mechanical[case])
        right = set(reviewer[case].supported)
        if left == right:
            agree += 1
        else:
            disagreements.append(
                {
                    "case": case,
                    "mechanical": sorted(left),
                    "reviewer": sorted(right),
                    "reviewer_rationale": reviewer[case].rationale,
                }
            )
        both += 1
        for action in actions:
            table[(action in left, action in right)] += 1
    total = sum(table.values())
    if total:
        observed = (table[(True, True)] + table[(False, False)]) / total
        left_yes = (table[(True, True)] + table[(True, False)]) / total
        right_yes = (table[(True, True)] + table[(False, True)]) / total
        expected = left_yes * right_yes + (1 - left_yes) * (1 - right_yes)
        kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    else:
        observed = kappa = None
    return {
        "cases_compared": both,
        "cases_in_full_agreement": agree,
        "raw_agreement": round(agree / both, 6) if both else None,
        "per_action_observed_agreement": None if observed is None else round(observed, 6),
        "cohens_kappa": None if kappa is None else round(kappa, 6),
        "contingency": {f"{left}_{right}": count for (left, right), count in table.items()},
        "disputed_cases": [row["case"] for row in disagreements],
        "disagreements": disagreements,
        "reviewer_failures": sorted(
            case for case, verdict in reviewer.items() if verdict.refusal is not None
        ),
        "limitation": (
            "The independent reviewer is a language model in a fresh context, not a human domain "
            "reviewer, and it shares a model family with two evaluated arms. Agreement here is "
            "evidence about this protocol, not a biological adjudication."
        ),
    }


def adjudicate_package(
    *,
    public_directory: Path,
    private_directory: Path,
    client,
    ledger: SpendLedger | None = None,
    limit: int | None = None,
    progress_path: Path | None = None,
    resume_from: Mapping[str, Mapping[str, object]] | None = None,
) -> Mapping[str, object]:
    """Adjudicate every case of a package with both adjudicators, and compare them.

    ``progress_path`` makes a long run observable: the verdicts so far and the priced ledger
    are written after every case, so a run that is interrupted leaves its completed
    adjudications behind as evidence instead of nothing at all.

    ``resume_from`` carries verdicts an earlier run already obtained. A case whose recorded
    verdict has no refusal is reused, so re-running after a provider failure re-reviews only
    the cases that failed and does not pay again for the ones that did not. The reused
    verdicts keep their original wording; nothing is silently re-decided.
    """

    cases = CaseRepository(public_directory, private_directory).load()
    if limit is not None:
        cases = cases[:limit]
    packets: dict[str, Mapping[str, object]] = {}
    mechanical: dict[str, tuple[str, ...]] = {}
    reviewer: dict[str, ReviewerVerdict] = {}
    registered: set[str] = {"defer"}
    for case, outcomes in cases:
        identifier = case.public.identifier
        packets[identifier] = adjudication_packet(case, outcomes)
        mechanical[identifier] = mechanical_verdict(case, outcomes)
        registered.update(str(item["development_action"]) for item in case.public.hypotheses)
    reused: list[str] = []
    for index, (case, _outcomes) in enumerate(cases, start=1):
        identifier = case.public.identifier
        actions = [str(item["development_action"]) for item in case.public.hypotheses] + ["defer"]
        recorded = (resume_from or {}).get(identifier)
        if recorded is not None and not recorded.get("refusal"):
            # An earlier run already obtained this verdict. Re-reviewing it would pay twice and
            # would also replace a recorded judgement with a new one, which is not a resume.
            reviewer[identifier] = ReviewerVerdict(
                case=identifier,
                supported=tuple(str(item) for item in recorded.get("supported_decisions", ())),
                ruled_out=tuple(str(item) for item in recorded.get("ruled_out", ())),
                minimum_evidence=tuple(str(item) for item in recorded.get("minimum_evidence", ())),
                rationale=str(recorded.get("rationale", "")),
                refusal=None,
            )
            reused.append(identifier)
        else:
            reviewer[identifier] = review_case(
                client, packets[identifier], registered_actions=actions, ledger=ledger
            )
        if progress_path is not None:
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            progress_path.write_text(
                json.dumps(
                    {
                        "cases_done": index,
                        "cases_total": len(cases),
                        "verdicts": {name: value.payload() for name, value in sorted(reviewer.items())},
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            if ledger is not None:
                ledger.write()
    digest = hashlib.sha256(
        json.dumps({name: list(value) for name, value in sorted(mechanical.items())}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "package": public_directory.parent.as_posix(),
        "cases": len(cases),
        "reviewed_now": len(cases) - len(reused),
        "reused_from_an_earlier_run": sorted(reused),
        "mechanical_verdicts": {name: list(value) for name, value in sorted(mechanical.items())},
        "mechanical_digest": digest,
        "reviewer_verdicts": {name: verdict.payload() for name, verdict in sorted(reviewer.items())},
        "agreement": agreement(mechanical, reviewer, registered_actions=sorted(registered)),
        "packets": packets,
        "protocol": (
            "Both adjudicators were fixed before any arm output was compared to them. The packet "
            "carries the evidence and no decision; the mechanical verdict is the package's frozen "
            "licensing rules with every record revealed."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    from agent.configuration import MAESTROSettings
    from agent.llm import DeepSeekChatClient

    parser = argparse.ArgumentParser(description="Run the blind adjudication over a case package.")
    parser.add_argument("--public-cases", type=Path, required=True)
    parser.add_argument("--private-results", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True, help="Directory for packets, verdicts and the ledger.")
    parser.add_argument("--limit", type=int, help="Adjudicate only the first N cases.")
    parser.add_argument(
        "--resume-from",
        type=Path,
        help=(
            "An earlier adjudication.json. Cases whose recorded verdict carries no refusal are "
            "reused verbatim and are not paid for again; only the cases that failed are reviewed."
        ),
    )
    parser.add_argument("--ceiling-usd", type=float, default=5.0)
    parser.add_argument(
        "--prior-total-usd",
        type=float,
        default=0.694763,
        help="Recorded campaign spend carried in, so a ceiling is enforced against the whole campaign.",
    )
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    ledger = SpendLedger.load(
        arguments.output / "provider_spend.json",
        ceiling_usd=arguments.ceiling_usd,
        prior_total_usd=arguments.prior_total_usd,
        prior_note=(
            "0.590786 recorded on 2026-09-13, plus 0.058555 for an LLM arm never written back, "
            "plus 0.045422 recorded only in a concurrent session's notes"
        ),
    )
    client = DeepSeekChatClient(MAESTROSettings.from_workspace(arguments.workspace))
    arguments.output.mkdir(parents=True, exist_ok=True)
    recorded = None
    if arguments.resume_from is not None:
        if not arguments.resume_from.is_file():
            parser.error("--resume-from names no file")
        recorded = json.loads(arguments.resume_from.read_text(encoding="utf-8")).get("reviewer_verdicts", {})
    payload = adjudicate_package(
        public_directory=arguments.public_cases,
        private_directory=arguments.private_results,
        client=client,
        ledger=ledger,
        limit=arguments.limit,
        progress_path=arguments.output / "adjudication_progress.json",
        resume_from=recorded,
    )
    arguments.output.mkdir(parents=True, exist_ok=True)
    (arguments.output / "adjudication.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    ledger.write()
    summary = payload["agreement"]
    print(
        f"cases={payload['cases']} reviewed_now={payload['reviewed_now']} "
        f"reused={len(payload['reused_from_an_earlier_run'])} "
        f"compared={summary['cases_compared']} raw_agreement={summary['raw_agreement']} "
        f"kappa={summary['cohens_kappa']} disputed={len(summary['disputed_cases'])} "
        f"reviewer_failures={len(summary['reviewer_failures'])} "
        f"spend_usd={ledger.session_total_usd:.6f} total_usd={ledger.total_usd:.6f}"
    )
    for row in summary["disagreements"]:
        print(f"  disputed {row['case']}: mechanical={row['mechanical']} reviewer={row['reviewer']}")
    print(f"written: {arguments.output / 'adjudication.json'}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
