# Local integrity-reader correction

2026-10-23. Initial verify_phase.py assumed every independent seal had a top-level sha256. Constructive INDEPENDENT_SEAL instead contains a files mapping; the verifier stopped with AttributeError before writing a snapshot. Inspection of that actual schema led to explicit per-file checks. No prior seal, experiment protocol, result or reviewed experiment code changed. This administrative correction does not rerun or repair the stopped scientific configuration.
