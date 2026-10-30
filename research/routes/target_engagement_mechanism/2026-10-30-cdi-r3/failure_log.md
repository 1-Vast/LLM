# CDI negative and failure log — 2026-10-30

* **Bridge rejection:** `bridge_audit.md` in the paired-functional-resource
  episode found 684 transcriptome–PRISM rows with transcript `24h|10000nM` but
  multi-dose PRISM AUC and no matched preparation, exposure, vehicle or
  independent-repeat fields.  It cannot support a paired proxy/function claim.
* **Historical binding substitution:** the kinobeads substitution line had
  binding-kernel versus functional-reference contrast `-0.000059` with CI
  `[-0.000115,-0.000010]`; binding cannot be treated as a functional surrogate.
* **All-target pair census:** the first implementation began repeated wide-matrix
  scans while enumerating approximately 5.26 million pairs and was stopped after
  more than three minutes without writing a result.  This is an implementation
  failure, not a scientific negative.  The targeted FLT3 census was used instead.
* **DeepSeek preflight:** DS044 initially failed a local prompt hash check due
  to CRLF conversion before any model call.  The corrected isolated call was
  run once; the preflight artifact remains in the task directory.
* **Runtime sensitivity:** the response and context tables were byte-identical
  across Python 3.14 and `maestro` Python 3.11, while Ridge CV values differed
  slightly.  The `maestro` values are canonical; the discrepancy is retained as
  software sensitivity, not interpreted biologically.

These failures and negative boundaries remain active stop conditions.
