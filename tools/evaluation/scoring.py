"""Evaluation scoring: consolidated module responsibilities."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from math import ceil, sqrt
from pathlib import Path
from random import Random
from typing import Any, Mapping, Sequence
from maestro.models import DevelopmentAction
from .cases import DecisionRule, ReplayCase, RevealedEvidence
from .planning import (
    enumerate_executed_sequences,
    licensing_certificates,
    sequence_cost,
)
from .cases import CaseRepository
from .costs import SequenceLabCost, SpendLedger, TURNAROUND_CONVENTION


def median_or_none(values: Sequence[float | None]) -> float | None:
    """Return the median of non-null report values, or ``None`` when empty."""

    finite = sorted(value for value in values if value is not None)
    if not finite:
        return None
    middle = len(finite) // 2
    if len(finite) % 2:
        return float(finite[middle])
    return float((finite[middle - 1] + finite[middle]) / 2)


class FinalTestVerdict(str, Enum):
    """How a terminal decision fares against results no policy could ever read.

    The verdict sits beside the licensing verdict and never replaces it: licensing asks
    whether the acquired evidence supports the decision, the final test asks whether data
    held back from every strategy agree with it. ``partition_absent`` is the honest value
    for a case package that carries no held-back results.
    """

    PARTITION_ABSENT = "partition_absent"
    NO_DECISION = "no_decision"
    UNTESTED = "untested"
    INADMISSIBLE = "inadmissible"
    CONSISTENT = "consistent"
    CONTRADICTED = "contradicted"
    MIXED = "mixed"

# Deferral is never scored as an advance or an abandonment: it is a refusal to act,
# and section 9.4 requires it to be counted separately so that refusing everything
# cannot win.
_ADVANCING = frozenset({DevelopmentAction.CONTINUE, DevelopmentAction.PRESERVE_MULTI_TARGET_ACTIVITY})
_ABANDONING = frozenset({DevelopmentAction.STOP, DevelopmentAction.REMOVE_MULTI_TARGET_ACTIVITY})


class DecisionVerdict(str, Enum):
    """How a submitted decision relates to what the acquired evidence licenses."""

    CORRECT = "correct"
    OVER_DEFERRAL = "over_deferral"
    WRONG_ADVANCE = "wrong_advance"
    WRONG_ABANDON = "wrong_abandon"
    WRONG_DIRECTION = "wrong_direction"
    NO_DECISION = "no_decision"
    INVALID_SUBMISSION = "invalid_submission"


@dataclass(frozen=True)
class DecisionScore:
    """The scored outcome of one policy submission on one case."""

    verdict: DecisionVerdict
    licensed: tuple[str, ...]
    reachable: tuple[str, ...]
    decisive_evidence_acquired: bool
    required_cost: float
    waste_cost: float
    cited_evidence_valid: bool
    reason: str
    redundant_cost: float = 0.0
    hindsight_regret: float = 0.0
    certificate: tuple[str, ...] = ()
    lab_cost_spent: SequenceLabCost | None = None
    final_test: str = FinalTestVerdict.PARTITION_ABSENT.value
    final_test_records: tuple[str, ...] = ()

    @property
    def correct(self) -> bool:
        return self.verdict is DecisionVerdict.CORRECT


def licensed_decisions(
    case: ReplayCase, observed: Mapping[str, RevealedEvidence]
) -> tuple[DevelopmentAction, ...]:
    """Return every decision the currently revealed evidence licenses."""

    return tuple(
        dict.fromkeys(rule.decision for rule in case.scoring.decision_rules if rule.matches(observed))
    )


def minimum_certificate(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    *,
    decision: DevelopmentAction | None = None,
    restricted_to: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], float] | None:
    """Cheapest legally executable acquisition whose records license a decision.

    This replaces the earlier prerequisite-closure arithmetic. The closure
    could skip a prerequisite that no registered action supplies and still
    report a cost, so the scorer could call a decision reachable that the
    replay environment refuses to execute. Here the search runs over the same
    transition semantics execution uses, so the two cannot disagree.

    A prerequisite's own cost is inside the certificate: the sequence is legal,
    which means every premise was actually bought.
    """

    def matches(observed: Mapping[str, RevealedEvidence]) -> bool:
        for rule in case.scoring.decision_rules:
            if decision is not None and rule.decision is not decision:
                continue
            if rule.matches(observed):
                return True
        return False

    certificates = licensing_certificates(
        case.public, outcomes, matches, restricted_to=restricted_to
    )
    return certificates[0] if certificates else None


def reachable_decisions(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    *,
    budget: float,
) -> tuple[DevelopmentAction, ...]:
    """Return the decisions a policy could still have licensed inside the case budget.

    Evaluator-side knowledge used only for scoring: it asks whether evidence
    that licenses a decision was *executably* purchasable in this hidden world.
    A decision whose licensing evidence is unavailable, unaffordable, or blocked
    by a premise no action supplies is not reachable, so declining to reach it
    is not an error.
    """

    reachable: list[DevelopmentAction] = []
    for rule in case.scoring.decision_rules:
        if not rule.required_outcomes:
            reachable.append(rule.decision)
            continue
        for sequence in enumerate_executed_sequences(case.public, outcomes):
            if sequence_cost(case.public, sequence) > budget + 1e-9:
                continue
            observed = {name: outcomes[name] for name in sequence if name in outcomes}
            if rule.matches(observed):
                reachable.append(rule.decision)
                break
    return tuple(dict.fromkeys(reachable))


def score_submission(
    case: ReplayCase,
    outcomes: Mapping[str, RevealedEvidence],
    *,
    decision: DevelopmentAction | None,
    observed: Mapping[str, RevealedEvidence],
    evidence_ids: Sequence[str],
    spent: float,
    submission_valid: bool,
) -> DecisionScore:
    """Score one submission against the licensing rules, not against one expected answer."""

    licensed = licensed_decisions(case, observed)
    reachable = reachable_decisions(case, outcomes, budget=case.public.budget)
    decisive = _decisive_evidence_acquired(case, observed)

    # The cheapest legal certificate available anywhere in this case, and the
    # cheapest one contained in what this policy actually acquired. Three costs
    # are reported separately because they answer different questions:
    #   required_cost     - what a supported decision costs at best in this case
    #   redundant_cost    - what this policy bought beyond its own certificate
    #   hindsight_regret  - what a cheaper legal route would have saved
    # A valid alternative route is therefore not scored as waste; only
    # acquisition outside the policy's own licensing certificate is.
    cheapest = minimum_certificate(case, outcomes)
    required_cost = cheapest[1] if cheapest is not None else 0.0
    own = minimum_certificate(
        case, outcomes, decision=decision, restricted_to=tuple(observed)
    )
    if own is None:
        own = minimum_certificate(case, outcomes, restricted_to=tuple(observed))
    certificate = own[0] if own is not None else ()
    certificate_cost = own[1] if own is not None else 0.0
    redundant = max(0.0, spent - certificate_cost) if own is not None else spent
    regret = max(0.0, spent - required_cost) if own is not None else 0.0

    public_ids = {item.identifier for item in case.public.initial_evidence}
    cited_valid = set(evidence_ids).issubset(set(observed) | public_ids)

    verdict, reason = _verdict(decision, licensed, reachable, submission_valid)
    tested, tested_records = final_test_verdict(case, decision if submission_valid else None)
    return DecisionScore(
        verdict=verdict,
        licensed=tuple(item.value for item in licensed),
        reachable=tuple(item.value for item in reachable),
        decisive_evidence_acquired=decisive,
        required_cost=required_cost,
        waste_cost=redundant,
        redundant_cost=redundant,
        hindsight_regret=regret,
        certificate=certificate,
        cited_evidence_valid=cited_valid,
        reason=reason,
        lab_cost_spent=case.public.sequence_lab_cost(tuple(observed)),
        final_test=tested.value,
        final_test_records=tested_records,
    )


def final_test_verdict(
    case: ReplayCase, decision: DevelopmentAction | None
) -> tuple[FinalTestVerdict, tuple[str, ...]]:
    """Check a terminal decision against the always-hidden partition, if the case has one.

    Only admissible records count, and a record that bears on neither the submitted
    decision's confirmation nor its contradiction leaves it untested rather than passed.
    """

    records = case.scoring.final_test
    if not records:
        return FinalTestVerdict.PARTITION_ABSENT, ()
    if decision is None:
        return FinalTestVerdict.NO_DECISION, ()
    bearing = [record for record in records if decision in record.confirms or decision in record.contradicts]
    if not bearing:
        return FinalTestVerdict.UNTESTED, ()
    admissible = [record for record in bearing if record.admissible]
    if not admissible:
        return FinalTestVerdict.INADMISSIBLE, tuple(record.identifier for record in bearing)
    identifiers = tuple(record.identifier for record in admissible)
    confirmed = any(decision in record.confirms for record in admissible)
    contradicted = any(decision in record.contradicts for record in admissible)
    if confirmed and contradicted:
        return FinalTestVerdict.MIXED, identifiers
    if contradicted:
        return FinalTestVerdict.CONTRADICTED, identifiers
    return FinalTestVerdict.CONSISTENT, identifiers


def _verdict(
    decision: DevelopmentAction | None,
    licensed: Sequence[DevelopmentAction],
    reachable: Sequence[DevelopmentAction],
    submission_valid: bool,
) -> tuple[DecisionVerdict, str]:
    if not submission_valid:
        return DecisionVerdict.INVALID_SUBMISSION, "the submission did not satisfy the terminal decision contract"
    if decision is None:
        return DecisionVerdict.NO_DECISION, "no terminal decision was submitted"
    if decision in licensed:
        return DecisionVerdict.CORRECT, "the acquired evidence licenses the submitted decision"
    if decision is DevelopmentAction.DEFER:
        decisive = [item for item in reachable if item is not DevelopmentAction.DEFER]
        if decisive:
            return (
                DecisionVerdict.OVER_DEFERRAL,
                "deferral was submitted while "
                + ", ".join(sorted(item.value for item in decisive))
                + " remained licensable within the case budget",
            )
        # Nothing else was licensable within the budget, so refusing to act is
        # the correct response rather than a failure to find an answer.
        return DecisionVerdict.CORRECT, "no decision other than deferral was licensable within the case budget"
    if decision in _ADVANCING:
        return DecisionVerdict.WRONG_ADVANCE, "the programme was advanced without licensing evidence"
    if decision in _ABANDONING:
        return DecisionVerdict.WRONG_ABANDON, "the programme was abandoned without licensing evidence"
    return DecisionVerdict.WRONG_DIRECTION, "a revision was submitted that the acquired evidence does not license"


def _decisive_evidence_acquired(case: ReplayCase, observed: Mapping[str, RevealedEvidence]) -> bool:
    """Whether the policy acquired the evidence some licensing rule actually needs."""

    rules: Sequence[DecisionRule] = case.scoring.decision_rules
    informative = [rule for rule in rules if rule.required_outcomes]
    if not informative:
        return True
    return any(rule.matches(observed) for rule in informative)


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
    """One record as an adjudicator needs it: the claim, its numbers and its two adjudicate_main limits.

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


def adjudicate_main(argv: Sequence[str] | None = None) -> int:
    import argparse

    from agent.llm import MAESTROSettings
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


Z_95 = 1.959963984540054
BOOTSTRAP_SEED = 20260914
BOOTSTRAP_RESAMPLES = 2000

SECTION_37_ROWS: tuple[tuple[str, str], ...] = (
    ("fixed_expert_rule_flow", "Fixed expert rule flow"),
    ("simple_model_plus_voi", "Simple response model with EIG/VOI"),
    ("retrieval_single_agent", "Retrieval-based single agent"),
    ("same_llm_explicit_hypotheses", "Same LLM, MDA-style explicit hypothesis decision"),
    ("full_system", "Full system"),
    ("full_system_shuffled_predictions", "Full system with shuffled model predictions"),
)

# Declared, not inferred: which evaluated arm stands for which row. An arm that does not
# implement a row's strategy is not assigned to it merely because it exists.
DEFAULT_ROW_ARMS: Mapping[str, str] = {
    "fixed_expert_rule_flow": "fixed_expert",
    "simple_model_plus_voi": "simple_model_voi",
    "retrieval_single_agent": "ordinary_llm",
    "same_llm_explicit_hypotheses": "explicit_hypotheses_llm",
    "full_system": "maestro_core",
    "full_system_shuffled_predictions": "maestro_core_shuffled_predictions",
}

NOT_RUN_REASONS: Mapping[str, str] = {
    "fixed_expert_rule_flow": "the fixed_expert arm was not evaluated in this run",
    "simple_model_plus_voi": (
        "the simple_model_voi arm was not evaluated in this run; it fits its outcome model on a "
        "declared development split and is refused rather than run unfitted"
    ),
    "retrieval_single_agent": "the provider-backed ordinary_llm arm was not evaluated in this run",
    "same_llm_explicit_hypotheses": (
        "the provider-backed explicit_hypotheses_llm arm was not evaluated in this run; the row "
        "requires an arm that states a posterior over the registered explanations and selects by "
        "its own value of information, and that contract is enforced rather than requested"
    ),
    "full_system": "the maestro_core arm was not evaluated in this run",
    "full_system_shuffled_predictions": (
        "the maestro_core_shuffled_predictions arm was not evaluated in this run; where it is, an "
        "identity with the full system means the prediction input is not read, not that it was harmless"
    ),
}

WRONG_VERDICTS = ("wrong_advance", "wrong_abandon", "wrong_direction")
NO_VALID_VERDICTS = ("no_decision", "invalid_submission")


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple[float, float] | None:
    """Wilson score interval for a binomial rate; None when there is nothing to estimate."""

    if trials <= 0:
        return None
    rate = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (rate + z * z / (2.0 * trials)) / denominator
    half = z * sqrt(rate * (1.0 - rate) / trials + z * z / (4.0 * trials * trials)) / denominator
    return (round(max(0.0, centre - half), 6), round(min(1.0, centre + half), 6))


def cluster_bootstrap_interval(
    events_by_cluster: Mapping[str, tuple[int, int]],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float] | None:
    """Percentile interval of a pooled rate, resampling whole clusters with replacement."""

    clusters = sorted(events_by_cluster)
    if len(clusters) < 2 or resamples < 2:
        return None
    rng = Random(seed)
    rates: list[float] = []
    for _ in range(resamples):
        events = 0
        trials = 0
        for _ in clusters:
            hit, count = events_by_cluster[clusters[rng.randrange(len(clusters))]]
            events += hit
            trials += count
        rates.append(events / trials if trials else 0.0)
    rates.sort()
    low = rates[int(0.025 * (resamples - 1))]
    high = rates[int(ceil(0.975 * (resamples - 1)))]
    return (round(low, 6), round(high, 6))


def _value(entry: object) -> str | None:
    """A decision or verdict as plain text, whether it arrived as an enum or from JSON."""

    if entry is None:
        return None
    return str(getattr(entry, "value", entry))


def row_metrics(report: Mapping[str, object], clusters: Mapping[str, str]) -> dict[str, object]:
    """Decision-level metrics for one evaluated arm, with the statistical unit stated."""

    results = list(report.get("results", ()))  # type: ignore[arg-type]
    total = len(results)
    verdicts = Counter(_value(item["verdict"]) for item in results)

    def share(count: int) -> dict[str, object]:
        return {"count": count, "rate": round(count / total, 6) if total else None}

    by_cluster: dict[str, tuple[int, int]] = {}
    for item in results:
        key = clusters.get(str(item["case_id"]), str(item["case_id"]))
        hit, count = by_cluster.get(key, (0, 0))
        by_cluster[key] = (hit + (1 if _value(item["verdict"]) in WRONG_VERDICTS else 0), count + 1)
    wrong = sum(verdicts[name] for name in WRONG_VERDICTS)

    eligible = [item for item in results if not ({str(x) for x in item.get("reachable_decisions", ())} - {"defer"})]
    deferred = [
        item for item in eligible if _value(item.get("decision")) == "defer" and _value(item["verdict"]) == "correct"
    ]
    reached = [
        item
        for item in results
        if _value(item["verdict"]) == "correct" and _value(item.get("decision")) not in (None, "defer")
    ]
    priced = [item for item in reached if item.get("lab_cost_refusal") is None and item.get("wells_spent") is not None]
    fully_priced = len(priced) == len(reached)
    return {
        "arm": report.get("policy"),
        "cases": total,
        "clusters": len(by_cluster),
        "reliability": share(verdicts["correct"]),
        "wrong_action": {
            **share(wrong),
            "wilson_95": wilson_interval(wrong, total),
            "cluster_bootstrap_95": cluster_bootstrap_interval(by_cluster),
        },
        "wrong_advance": share(verdicts["wrong_advance"]),
        "premature_abandon": share(verdicts["wrong_abandon"]),
        "wrong_direction": share(verdicts["wrong_direction"]),
        "over_deferral": share(verdicts["over_deferral"]),
        "no_valid_decision": share(sum(verdicts[name] for name in NO_VALID_VERDICTS)),
        "appropriate_deferral": {
            "eligible": len(eligible),
            "deferred_correctly": len(deferred),
            "rate": round(len(deferred) / len(eligible), 6) if eligible else None,
        },
        "cost_to_evidence_standard": {
            "cases": len(reached),
            "declared_cost_units": round(sum(float(item.get("spent", 0.0)) for item in reached), 6),
            "wells": sum(int(item["wells_spent"]) for item in priced) if fully_priced else None,
            "turnaround_days": (
                round(sum(float(item["turnaround_days_spent"]) for item in priced), 6) if fully_priced else None
            ),
            "lab_cost_refused": len(reached) - len(priced),
            "new_measurements": sum(int(item.get("new_measurements", 0)) for item in reached),
            "record_retrievals": sum(int(item.get("record_retrievals", 0)) for item in reached),
            "turnaround_convention": TURNAROUND_CONVENTION,
        },
        "prospective_hit_rate": {
            "status": "not_registered",
            "reason": "no arm registered a discriminating prediction before its reveal",
        },
        "final_test": dict(sorted(Counter(str(item.get("final_test_verdict", "partition_absent")) for item in results).items())),
        "refusal_codes": dict(sorted(Counter(str(item["refusal_code"]) for item in results if item.get("refusal_code")).items())),
    }


def build_score_table(
    reports: Sequence[Mapping[str, object]],
    *,
    clusters: Mapping[str, str] | None = None,
    row_arms: Mapping[str, str] | None = None,
    blind_adjudication: bool = False,
    provenance: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Assemble the six rows, keep every other arm as a supplementary row, and state the verdict."""

    cluster_map = dict(clusters or {})
    by_arm = {str(report["policy"]): report for report in reports}
    assignment = dict(DEFAULT_ROW_ARMS if row_arms is None else row_arms)
    rows: list[dict[str, object]] = []
    used: set[str] = set()
    for key, label in SECTION_37_ROWS:
        arm = assignment.get(key)
        if arm is not None and arm in by_arm:
            rows.append({"row": key, "label": label, "status": "run", **row_metrics(by_arm[arm], cluster_map)})
            used.add(arm)
        else:
            rows.append({"row": key, "label": label, "status": "not_run", "arm": arm, "reason": NOT_RUN_REASONS[key]})
    supplementary = [
        {"row": f"supplementary:{name}", "label": name, "status": "run", **row_metrics(report, cluster_map)}
        for name, report in sorted(by_arm.items())
        if name not in used
    ]
    missing = [str(row["row"]) for row in rows if row["status"] == "not_run"]
    table: dict[str, object] = {
        "schema": "maestro.score_table.v1",
        "section": "governing report section 37",
        "statistical_unit": "case; intervals also resample whole target clusters",
        "cluster_map_supplied": bool(cluster_map),
        "bootstrap": {"seed": BOOTSTRAP_SEED, "resamples": BOOTSTRAP_RESAMPLES},
        "rows": rows,
        "supplementary_rows": supplementary,
        "conclusion": {
            "all_rows_run": not missing,
            "missing_rows": missing,
            "blind_adjudication": blind_adjudication,
            "evidence_for_core_claim": bool(not missing and blind_adjudication),
            "reading": (
                "A table missing a row supports no comparison between strategies, and a complete table "
                "without adjudication blind to the strategies' outputs is not evidence for the core claim."
            ),
        },
    }
    if provenance:
        table["provenance"] = dict(provenance)
    return table


def _incorrect(report: Mapping[str, object]) -> int:
    return sum(1 for item in report.get("results", ()) if _value(item["verdict"]) != "correct")  # type: ignore[union-attr]


def _sequences(report: Mapping[str, object]) -> dict[str, tuple[str, ...]]:
    return {str(item["case_id"]): tuple(item.get("selected_actions", ())) for item in report.get("results", ())}  # type: ignore[union-attr]


def exit_verdict(
    *,
    input_name: str,
    informed: Mapping[str, object],
    removed: Mapping[str, object],
    shuffled: Mapping[str, object],
    declaration_reader: Mapping[str, object] | None = None,
    prediction_quality_improved: bool | None = None,
    confident_out_of_domain_errors: int | None = None,
) -> dict[str, object]:
    """Apply the four section 29 exit conditions, in their written order, to one input.

    ``informed`` is the arm that reads the input, ``removed`` the same arm with it switched
    off, ``shuffled`` the same arm with it assigned to the wrong actions, and
    ``declaration_reader`` an arm that reads only the public declarations the input could
    have been derived from. A condition whose input was not supplied is `not_assessable`
    by name; nothing is filled in.
    """

    informed_wrong, removed_wrong, shuffled_wrong = _incorrect(informed), _incorrect(removed), _incorrect(shuffled)
    informed_sequences = _sequences(informed)
    moved_by_removal = sum(1 for case, sequence in informed_sequences.items() if _sequences(removed).get(case) != sequence)
    moved_by_shuffle = sum(1 for case, sequence in informed_sequences.items() if _sequences(shuffled).get(case) != sequence)
    improves = informed_wrong < removed_wrong and informed_wrong < shuffled_wrong

    conditions: list[dict[str, object]] = [
        {
            "condition": "remove_from_loop",
            "rule": "triggered unless the informed arm has strictly fewer incorrect verdicts than both the removed and the shuffled control",
            "status": "not_triggered" if improves else "triggered",
            "evidence": {
                "incorrect_informed": informed_wrong,
                "incorrect_removed": removed_wrong,
                "incorrect_shuffled": shuffled_wrong,
                "acquisitions_changed_by_removal": moved_by_removal,
                "acquisitions_changed_by_shuffle": moved_by_shuffle,
            },
        }
    ]
    if prediction_quality_improved is None:
        conditions.append(
            {
                "condition": "demote_to_feature_provider",
                "rule": "triggered when prediction quality improved while no acquisition changed",
                "status": "not_assessable",
                "reason": "no scored prediction quality was supplied for this input",
            }
        )
    else:
        conditions.append(
            {
                "condition": "demote_to_feature_provider",
                "rule": "triggered when prediction quality improved while no acquisition changed",
                "status": "triggered" if prediction_quality_improved and moved_by_removal == 0 else "not_triggered",
                "evidence": {"prediction_quality_improved": prediction_quality_improved, "acquisitions_changed_by_removal": moved_by_removal},
            }
        )
    if declaration_reader is None:
        conditions.append(
            {
                "condition": "record_as_external_information_gain",
                "rule": "triggered when an arm reading only the public declarations does at least as well as the informed arm",
                "status": "not_assessable",
                "reason": "no declaration-reading arm was supplied",
            }
        )
    elif not improves:
        conditions.append(
            {
                "condition": "record_as_external_information_gain",
                "rule": "triggered when an arm reading only the public declarations does at least as well as the informed arm",
                "status": "not_applicable",
                "reason": "the input improved nothing, so there is no gain to attribute",
            }
        )
    else:
        reader_wrong = _incorrect(declaration_reader)
        conditions.append(
            {
                "condition": "record_as_external_information_gain",
                "rule": "triggered when an arm reading only the public declarations does at least as well as the informed arm",
                "status": "triggered" if reader_wrong <= informed_wrong else "not_triggered",
                "evidence": {"incorrect_declaration_reader": reader_wrong, "incorrect_informed": informed_wrong, "reader": declaration_reader.get("policy")},
            }
        )
    if confident_out_of_domain_errors is None:
        conditions.append(
            {
                "condition": "tighten_applicability_domain",
                "rule": "triggered by any confident prediction outside the declared domain that proved wrong",
                "status": "not_assessable",
                "reason": "the input declares no applicability domain, so no confident out-of-domain error can be counted",
            }
        )
    else:
        conditions.append(
            {
                "condition": "tighten_applicability_domain",
                "rule": "triggered by any confident prediction outside the declared domain that proved wrong",
                "status": "triggered" if confident_out_of_domain_errors > 0 else "not_triggered",
                "evidence": {"confident_out_of_domain_errors": confident_out_of_domain_errors},
            }
        )
    triggered = [str(item["condition"]) for item in conditions if item["status"] == "triggered"]
    return {
        "schema": "maestro.exit_verdict.v1",
        "section": "governing report section 29",
        "input": input_name,
        "arms": {
            "informed": informed.get("policy"),
            "removed": removed.get("policy"),
            "shuffled": shuffled.get("policy"),
            "declaration_reader": declaration_reader.get("policy") if declaration_reader else None,
        },
        "conditions": conditions,
        "triggered": triggered,
        "consequence": triggered[0] if triggered else "retain",
    }


def render_text(table: Mapping[str, object]) -> str:
    """A compact plain-text view of the table for a terminal; the JSON is the record."""

    lines = ["row | status | cases | wrong action [Wilson 95] | over-deferral | appropriate deferral | wells to standard"]
    for row in list(table["rows"]) + list(table["supplementary_rows"]):  # type: ignore[arg-type]
        if row["status"] != "run":
            lines.append(f"{row['row']} | not_run | - | - | - | - | - ({row['reason']})")
            continue
        wrong = row["wrong_action"]
        deferral = row["appropriate_deferral"]
        cost = row["cost_to_evidence_standard"]
        lines.append(
            f"{row['row']} | run | {row['cases']} | {wrong['count']} {wrong['wilson_95']} | "
            f"{row['over_deferral']['count']} | {deferral['deferred_correctly']}/{deferral['eligible']} | "
            f"{cost['wells'] if cost['wells'] is not None else 'refused:' + str(cost['lab_cost_refused'])}"
        )
    conclusion = table["conclusion"]
    lines.append(f"all rows run: {conclusion['all_rows_run']}; evidence for core claim: {conclusion['evidence_for_core_claim']}")  # type: ignore[index]
    return "\n".join(lines)


def load_clusters(manifest: Path | None) -> dict[str, str]:
    """Case-to-cluster map from an evaluator-owned manifest; empty when none is given."""

    if manifest is None or not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return {str(entry["case_id"]): str(entry.get("source_cluster") or entry["case_id"]) for entry in data.get("cases", ())}


def table_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the section 37 score table from a maestro-evaluate payload.")
    parser.add_argument("--evaluation", type=Path, required=True, help="JSON written by maestro-evaluate.")
    parser.add_argument("--manifest", type=Path, help="Evaluator-owned manifest carrying source_cluster per case.")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args(argv)
    payload = json.loads(arguments.evaluation.read_text(encoding="utf-8"))
    table = build_score_table(
        payload["reports"],
        clusters=load_clusters(arguments.manifest),
        provenance={"evaluation": str(arguments.evaluation), "run_id": payload.get("run_id")},
    )
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(table, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    print(render_text(table))
    print(arguments.out)
    return 0


def score_sequence(public: Mapping, hidden: Mapping, actions: Sequence[str]) -> dict:
    """Score one legal action sequence against the hidden measured outcomes."""

    if public["episode_id"] != hidden["episode_id"]:
        raise ValueError("public_hidden_episode_mismatch")
    menu = {item["action"]: item for item in public["menu"]}
    by_action = {item["action"]: item for item in hidden["outcomes"]}
    if len(actions) > int(public["max_measurements"]):
        raise ValueError("too_many_measurements")
    if len(set(actions)) != len(actions):
        raise ValueError("repeated_action")
    if any(action not in menu for action in actions):
        raise ValueError("action_not_in_menu")
    keys = [menu[action]["key"] for action in actions]
    if any(keys[i + 1][1] < keys[i][1] for i in range(len(keys) - 1)):
        raise ValueError("time_order")
    days = sum(float(menu[action]["days"]) for action in actions)
    if days > float(public["budget_days"]) + 1e-9:
        raise ValueError("over_budget")

    measurements = 0
    eliminated = None
    for action in actions:
        measurements += 1
        outcome = by_action[action]["outcome"]
        if outcome == "eliminate_a":
            eliminated = public["hypotheses"][0]
        elif outcome == "eliminate_b":
            eliminated = public["hypotheses"][1]
        if eliminated is not None:
            break
    if eliminated is None:
        final = "deferred"
    else:
        final = "wrong" if eliminated == hidden["truth"] else "correct"
    return {
        "episode_id": public["episode_id"],
        "actions": list(actions),
        "measurements": measurements,
        "days": float(days),
        "final": final,
        "correct": float(final == "correct"),
        "wrong": float(final == "wrong"),
        "decided": float(final in {"correct", "wrong"}),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adjudicate replay results or build a score table.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("adjudicate", "table"):
        commands.add_parser(name, add_help=False)
    arguments, remaining = parser.parse_known_args(argv)
    return {"adjudicate": adjudicate_main, "table": table_main}[arguments.command](remaining)


if __name__ == "__main__":
    raise SystemExit(main())
