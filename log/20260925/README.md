# Experiment record, 2026-09-25

> - **Path**: `log/20260925/README.md`
> - **Purpose**: Record local verification findings, tool fixes and a controlled Jev ablation.
> - **Core points**: The tool fixes pass; the critic's action ranking was stable in both ablation arms; local asset failures remain.

## 1. Record control

Repository `main` was fast-forwarded to `555f5f7d4e4a` before verification.
The detailed cross-report summary is `log/20260925/0925/verification-summary.md`.
All raw provider and suite artifacts remain under ignored `outputs/local_verification/`.

## 2. Research questions and hypotheses

The reported failures concerned reused offline state, comparison against an
empty baseline, and unstable action recommendations. The controlled ablation
asked whether adding supplier topology to the critic state improves the
executable-action share or reproducibility.

## 3. Materials, data and computational environment

Conda `maestro`, Python 3.11.16, fixture action catalogue and live TypeSafe
Jev. No secret or raw `.env` value was read into this record.

## 4. Experimental design and controls

The offline driver was run twice in the same output directory. The comparison
tool was challenged with the preserved empty baseline. The live ablation made
12 calls per arm with the same contrast, action menu and questions; the only
arm difference was the topology block in the critic state.

## 5. Experiment register and results

Both offline runs passed 12/12 acceptance checks. The full suite reported
1184 passed, 51 failed, 0 errors, 1 skipped. The comparison tool refused the
empty baseline. Each ablation arm selected `rna_low` in all 12 calls, with
executable share and agreement both 1.0. See the summary and JSON in `0925/`.

## 6. Deviations, failures and corrections

The reused-state and empty-baseline defects were fixed upstream in `555f5f7`.
This run repaired the local log layout by adding day records and an index.
The two log-layout failures cleared after this record. The remaining 51 IDs
are in the no-local-assets baseline and need separate investigation with assets.

## 7. Interpretation and claim boundaries

The topology block showed no effect in this critic-state experiment. The
earlier generic probe's 12 non-executable recommendations therefore cannot be
attributed to missing topology alone. These synthetic fixture results make no
biological claim. The planner back-prompt remains unexercised.

## 8. Reproduction and artifact ledger

Commands and results are in `0925/verification-summary.md`; the measured arm
counts are in `0925/topology-ablation.json`. Full local reports are under
`outputs/local_verification/` and are not committed.

## 9. Open items and next experiments

Investigate the 51 remaining baseline-listed failures when the real assets
are available. Exercise a genuine planner contract violation to test
the single back-prompt. Revisit the generic probe's state framing if its
recommendations are meant to guide executable choices.

## 10. Curation provenance

This record synthesizes the 2026-09-25 and 2026-09-26 research reports, the
user-supplied report, and the current local verification at `555f5f7`.
