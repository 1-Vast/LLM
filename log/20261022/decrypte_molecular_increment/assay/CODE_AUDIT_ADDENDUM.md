# Current code-binding and reference-stop addendum

2026-10-22. Preserve the sealed CODE_AUDIT.md unchanged. Re-read the updated evaluator's imports, summary/reference/main sections and `freeze.py`, without opening data. Updated evaluator SHA256 is `f129b4c5326f105432af2c138126f4c39da1ba5c5667fd404804674438ee7c04`.

The evaluator now imports `verify` from freeze and calls it before reading prior development/preparation data or the new molecular matrix. `verify` reconstructs SHA256 for every frozen path; the freeze builder includes all current experiment .py files, both protocols, reviewed records and imported prior model implementation. This closes the earlier existence-only concern for ordinary local execution; it is not a global provenance certification or protection against maliciously changed running code.

The evaluator now asserts maximum48functional-reference discrepancy <1e-8 before its results print and before47sensitivity fits. It writes48PREDICTIONS/SUMMARY first, so if this assertion fails those files are failure evidence, not valid promotion evidence. Preserve them and record the rejection rather than interpreting the48gate or rerunning selectively. The47refit still uses a fresh Engine and skips historical48-array comparison; both required gates remain conjoined in the final console decision.

No new static blocker was found. The addendum itself should be included in final freeze/local bindings if it is used as review evidence. No new model family, numerical criterion or test was introduced by this audit. One attempted read of a guessed `bindings.py` returned file-not-found; the actual imported `freeze.py` was then read, with no data exposure or network request.
