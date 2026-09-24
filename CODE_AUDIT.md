# MAESTRO source audit for E0-DIR

Audit branch: `e0-dir-implementation`. The repository was initially a code-only
checkout with no Git history; commit `731ed8a` is the recorded baseline.

## Call chains

1. **Interaction and repair** — `agent/orchestrator.py` builds a task/context,
   `agent/planner.py` calls the completer, `maestro/contrast.py` validates the
   mechanism contrast, and `maestro/repair.py` proposes bounded edits. A real
   result enters `agent/cases.py` and `maestro/outcome.py`; prediction is kept
   separate. **source_verified; locally_reproduced by existing unit tests.**
2. **Virtual-cell request to artifact** — `virtual_cell/interface.py` validates
   `PredictionRequest`, `safe_predict` assesses then predicts once,
   `state_adapter.py` checks registry, asset digest, coordinate identity and
   controls, `state_runner.py` invokes the pinned State environment, and
   `artifacts.py` writes the condition-level digest. **source_verified;
   locally_reproduced with a real State panel on 2026-09-24.**
3. **Public case to private score** — `evaluation/cases.py` loads public and
   private partitions, `evaluation/runner.py` isolates each run and imports only
   the selected reveal, and `evaluation/scoring.py` evaluates the submission.
   **source_verified; locally_reproduced for replay tests; E0 transcript scoring
   is a separate new path.**
4. **API request to HTTP attempt and spend** — `agent/llm.py` constructs one
   OpenAI-compatible request and retries transport/rate-limit errors;
   `evaluation/tracking.py` records safe metadata and
   `evaluation/provider_spend.py` reserves/charges token usage. **source_verified;
   locally_reproduced with DeepSeek text routing; structured JSON mode is not
   supported by the configured model and is disabled in the E0 adapter.**

## Reuse boundaries

Reused: capability contracts, fail-closed prediction, artifact lineage, isolated
replay state, repair/result separation, tool receipts and spend ledger.

Not reused as E0 truth: mechanism evidence licensing, `MonotoneRealization` as a
functional state, State condition labels as arbitrary latent vectors, and any
prediction-to-measurement promotion. **document_claim_only** items from historical
reports were not counted as this run's results.

## Engineering findings

- `MAESTROSettings` previously inherited dataclass `repr`, which exposed the API
  key. E0 branch adds a redacted `repr` and environment-over-dotenv precedence.
- Spend token parsing now rejects bool, negative, non-finite and malformed values.
- The existing tool router is a registry/contract boundary, not an OS sandbox;
  **source_verified**.
- The registered State backend provides actual-condition predictions only. No
  latent-action encoder/decoder contract is registered; a real `ideal_hat` path
  is therefore **not_available**, and cannot be fabricated.

