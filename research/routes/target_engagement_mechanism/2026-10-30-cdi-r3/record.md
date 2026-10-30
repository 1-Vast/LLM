# CDI round record — 2026-10-30

## Brief and budget

Question: when can a same-target molecular binding contrast become a cell-context
functional contrast, and can an Agent choose the cheapest observation that
distinguishes structural error, target insufficiency, exposure/pharmacology and
assay mismatch?

Scope: drug discovery, virtual-cell conditional prediction, and equal-budget
diagnostic selection using cheap public drug-screen data.  No sealed/confirmation
data, no external model API for the scientific pilot, no wet-lab execution, and
no `src/` or `tools/` promotion.

The bounded data request was one ChEMBL REST call for the 243 already-local
molecule IDs, capped at one request, 30 seconds and 5 MB.  The DeepSeek DS044
task used one isolated call, 180 seconds, 2,048 output tokens, 12 KB input and a
declared USD 0.025 cap; effective paid cost and hard cap verification are
unknown.

## Agents and evidence roles

* `/root/cdi_prior_verification` read and recorded AdaMBind, PBCNet2.0 and Robin
  method/data boundaries in `prior_verification.md`.
* `/root/cdi_data_contract_audit` audited Klaeger/ChEMBL, PRISM, DepMap, GDSC,
  BeatAML and the missing paired functional resource in `data_audit.md`.
* `/root/cdi_fresh_challenger` received a fresh candidate brief and wrote
  `fresh_challenge.md`; it rejected the full stack as ordinary components and
  retained only a conditional diagnostic design.
* The coordinator independently verified source fields, identity mapping,
  response construction, arithmetic and saved outputs.  The fresh challenger
  was not relabelled as a result reviewer.

## Important revisions and failures

1. The broad “knowledge integration and virtual-cell self-audit” direction was
   narrowed after Robin and recent agent-loop precedents.
2. The 684-row transcriptome–PRISM bridge was rejected as a matched functional
   resource; this remains a data gate, not a CDI result.
3. A full all-target pair census was stopped after the first implementation
   became impractically slow while enumerating about 5.26 million pairs.  No
   output from that run is used.
4. The first DS044 run failed at a CRLF prompt-hash preflight before a model call;
   the failure is retained and the corrected single call was independently
   reviewed.
5. The first pilot run exposed a local sklearn API mismatch for
   `squared=False`; the equivalent square-root expression was used, and the
   canonical run was repeated in the `maestro` environment.

## Results state

The exact-structure census, targeted FLT3 feasibility gate, response pilot,
lineage holdout and pair-label permutation are exploratory retrospective
analyses.  Their claims stop at predictive association and data availability.
They do not establish cellular engagement, causal target mediation, independent
biological replication, prospective Agent efficiency, novelty or generalization
to new targets.

## Next checkpoint

Seek a documented target perturbation/rescue or cellular-engagement dataset for a
small FLT3 (or other single-target) matched-pair study.  If none is available
within a declared budget, do not expand CDI; record `data_unavailable` and keep
the conditional design as a parked hypothesis.
