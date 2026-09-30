"""Protocol external-validation-2: versioned, truth-separated evaluation of MAESTRO's measurement policies.

File summary
- Path: research/protocol_v2/__init__.py
- Purpose: the package for protocol version `external-validation-2`. It adds no new model. It adds
  the machinery that decides whether any MAESTRO policy beats the fixed expert order: immutable
  registration, truth and data-boundary contracts, task headroom and power, a baseline-safe
  research arm, robust calibration, and the decision gates for the virtual cell and feedback.
- Core points:
  - The production default is unchanged. Nothing here is imported by `src/`.
  - Protocol v1 artefacts (`research/belief_planning/`, `research/external_validation/`) are
    read, hashed and archived, never rewritten. See `archive.py` and `research/experiments/`.
  - Run modules with `python -m research.protocol_v2.<module>` from the repository root: the
    research packages import each other by package name.
- Interfaces: `PROTOCOL_VERSION`
"""

PROTOCOL_VERSION = "external-validation-2"
