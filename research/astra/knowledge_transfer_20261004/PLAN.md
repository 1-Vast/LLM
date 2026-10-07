# Public biological knowledge transfer: bounded exploratory study

The user asks for a solution using inexpensive available biological data, including proteins,
regulation and drug combinations, instead of another request for scarce matched experiments.

## Question

Can public drug annotations and a signed directed protein network improve borrowing across
drug combinations when historical response data are sparse? This is an added-information and
inductive-bias experiment, NOT a reopening of the stopped joint-rate/scheduler hypothesis.
All Jaaks outcomes and the previous evaluation split have already been exposed by the project.
Every result is exploratory. Vis outcomes remain unopened. No production changes are planned.

## Information and sources

- Jaaks 2022 original screen, Figshare 16843597, file 34006655: download once; initially read
  only drug IDs/names/target/pathway annotation columns. Expected original SHA256:
  1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278.
- OmniPath human protein interactions and CollecTRI transcriptional regulation, source-filtered
  for commercial-compatible redistribution where supported; retain source and PMID provenance.
- HGNC approved symbols and aliases for identifier resolution. Ambiguous family targets are
  retained as annotation tokens, never silently expanded into genes or direct-binding evidence.
- No synergy/outcome edges in knowledge features. Exclude references to the benchmark paper.
- Knowledge available in October 2026 supports a retrospective/current-use analysis, not a claim
  that this knowledge was available before the historical experiments.

## Small model and controls

Use normalized target and propagated-network drug features, combined through symmetric pair
kernels; these are response-transfer priors, not identified biochemical dynamics.
Keep the original two-round campaign, fp=30, cap, tie-breaking, and confirmation calls.
Compare C_mean with target/pathway transfer, signed-network transfer, drug-ID transfer and
permuted-network transfer. Use the same labels, split, resource cap and model selection budget.
Keep every candidate, including those without mapped genes, and report coverage explicitly.

Metadata construction and exact model choices must be recorded and hashed before reading
response columns. Use the existing HD/E split. Within HD only, select a bounded blending weight
from {0, 0.25, 0.5}; zero is a valid result. Evaluate fixed choices on E once.
Primary regime: all HD history. Prespecified data-efficiency regimes: 4 and 8 history lines per
tissue, deterministic seeds 11/23/47; keep evaluation lines fixed. Repeated seeds are not new
biological units. Report paired line bootstrap and pair-dependence sensitivity where applicable.
Do not force a success; distinguish working knowledge acquisition, coverage, predictive transfer
and confirmed-yield improvement. No novel-method claim for kernel ridge or network propagation.

## Deliverables

A downloadable, provenance-preserving knowledge subset; reproducible acquisition/build/evaluation
code; actual data coverage and same-information controls; a concrete next architecture using
the existing agent knowledge and virtual-cell interfaces. Only tests resolving real implementation
risks (sign/direction, label exclusion, split isolation, accounting/parity) are required.
