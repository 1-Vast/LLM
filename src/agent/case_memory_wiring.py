"""Orchestrator wiring for the case-memory outcome forecaster.

File summary
- Path: src/agent/case_memory_wiring.py
- Purpose: construct the case-memory forecaster for `MAESTROOrchestrator(outcome_forecaster=...)`
  only when the feature flag allows it, so the default production behaviour is byte-for-byte the
  pre-integration behaviour.
- Core points:
  - `forecaster_from_environment` returns None unless `MAESTRO_CASE_MEMORY_ENABLED` is set, so a
    default-constructed orchestrator never sees the case memory.
  - When enabled, the returned forecaster still answers with a named abstention whenever its own
    gates fail (support, applicability); the orchestrator's existing fallback - a logged
    `outcome_forecast_failed` event and coverage selection - is the safety path.
  - The module lives under `src/agent/` because the layering contract forbids `src/maestro/` from
    importing the agent package; the direction is agent -> maestro only.
- Interfaces: `forecaster_from_environment`
- Depends on: maestro.case_memory, maestro.hypothesis_forecast, maestro.directional
"""
from __future__ import annotations

from pathlib import Path

from maestro.case_memory import EpisodeStore, case_memory_enabled
from maestro.directional import FeatureArm
from maestro.hypothesis_forecast import CaseMemoryOutcomeForecaster


def forecaster_from_environment(
    store_path: str | Path | None = None,
    *,
    feature_arm: FeatureArm = FeatureArm.COMBINED,
) -> CaseMemoryOutcomeForecaster | None:
    """The case-memory forecaster when the flag is on; None when it is off.

    A caller that passes the result straight into `MAESTROOrchestrator(outcome_forecaster=...)`
    therefore keeps the registered default: flag unset or false means no case-memory forecaster,
    no discrimination selection change, no behaviour change.
    """

    if not case_memory_enabled():
        return None
    store = EpisodeStore(store_path) if store_path else EpisodeStore()
    return CaseMemoryOutcomeForecaster(store, feature_arm=feature_arm)
