# GeneEffect extraction budget — 2026-10-30

## Purpose

Use the official DepMap 26Q1 `gene_effect.csv` only as a genetic-reference
check for the existing FLT3/PRISM retrospective pilot. This file cannot supply
cellular drug engagement, dose, exposure time, or an orthogonal function
endpoint.

## Fixed budget and stop rules

- Source: Figshare file `67214582`, official release DOI
  `10.6084/m9.figshare.31660582.v2`.
- Maximum network transfer: 500 MB (the advertised file is 413,544,937
  bytes); maximum wall time: 10 minutes.
- Streaming only: retain the header and the `FLT3` row; do not retain the full
  matrix. A partial transfer, malformed row, missing `FLT3` column, or failed
  checksum stops the branch.
- No target-mediated, causal, engagement, prospective-Agent, or code-promotion
  claim may use this extraction. A result is limited to genetic concordance or
  discordance with the pre-existing PRISM pilot.
- Do not infer a live worker from this file or from a successful HTTP response.

## Acceptance

Accept only if the extracted header and row parse deterministically, the row
contains stable model identifiers, and the join to the existing FLT3 pilot is
performed by exact `DepMap_ID` identity. Keep the signed direction of the
Chronos gene-effect value explicit; do not call it target occupancy.
