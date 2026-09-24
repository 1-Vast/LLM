"""What makes an evaluation citable rather than asserted.

File summary
- Path: src/virtual_cell/receipts.py
- Purpose: give "validated" a referent. A validation claim has to name a
  receipt, an endpoint, a split and an acceptance criterion, and say whether the
  criterion was met and whether the evaluation data were verifiably outside the
  model's training.
- Core points:
  - A nonempty free-text field is not a validation result; every structural gap
    is named individually.
  - Whether the held-out data were verifiably held out is a separate fact from
    whether the criterion passed, because a retrospective score on possibly seen
    data is not a generalisation result.
  - Receipts are matched against the endpoint, context and model version they
    were issued for; a receipt for another endpoint validates nothing here.
- Interfaces: `ValidationReceipt`
- Depends on: (standard library only)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ValidationReceipt:
    """One evaluation, identified well enough to be checked by someone else.

    ``passed`` is the verdict against ``acceptance_criterion``; ``None`` means
    the criterion was never evaluated, which is a different state from failing
    it. ``holdout_verified`` records whether the evaluated data were *verified*
    to be outside the model's training, not merely held out by the evaluator: a
    checkpoint whose training split cannot be inspected cannot support that
    claim, however the evaluator split the data.
    """

    receipt_id: str
    endpoint: str
    split: str
    acceptance_criterion: str
    metric: str = ""
    value: float | None = None
    threshold: float | None = None
    passed: bool | None = None
    holdout_verified: bool = False
    context_identifier: str | None = None
    model_version: str | None = None
    independent_units: int | None = None
    artifact_sha256: str | None = None
    caveats: tuple[str, ...] = ()

    def problems(
        self,
        *,
        endpoint: str | None = None,
        endpoints: tuple[str, ...] | None = None,
        context_identifier: str | None = None,
        model_version: str | None = None,
    ) -> tuple[str, ...]:
        """Every reason this receipt cannot be cited for the requested use."""

        issues: list[str] = []
        if not self.receipt_id.strip():
            issues.append("receipt_id_missing")
        if not self.endpoint.strip():
            issues.append("endpoint_missing")
        if not self.split.strip():
            issues.append("split_missing")
        if not self.acceptance_criterion.strip():
            issues.append("acceptance_criterion_missing")
        if self.passed is None:
            issues.append("acceptance_not_evaluated")
        if self.value is not None and not isfinite(float(self.value)):
            issues.append("metric_value_not_finite")
        wanted = tuple(item for item in (endpoints or ()) if item) or ((endpoint,) if endpoint else ())
        if wanted and self.endpoint not in wanted:
            issues.append("receipt_endpoint_mismatch")
        if (
            context_identifier is not None
            and self.context_identifier is not None
            and self.context_identifier != context_identifier
        ):
            issues.append("receipt_context_mismatch")
        if (
            model_version is not None
            and self.model_version is not None
            and self.model_version != model_version
        ):
            issues.append("receipt_model_version_mismatch")
        return tuple(dict.fromkeys(issues))

    @property
    def identifiable(self) -> bool:
        """Whether the receipt names everything needed to check it."""

        return not self.problems()

    @property
    def accepted(self) -> bool:
        """Identifiable and meeting its own acceptance criterion."""

        return self.identifiable and self.passed is True

    def validates(
        self,
        *,
        endpoint: str | None = None,
        endpoints: tuple[str, ...] | None = None,
        context_identifier: str | None = None,
        model_version: str | None = None,
    ) -> bool:
        """Accepted, matched to this use, and on a verified holdout."""

        matched = not self.problems(
            endpoint=endpoint,
            endpoints=endpoints,
            context_identifier=context_identifier,
            model_version=model_version,
        )
        return matched and self.passed is True and self.holdout_verified
