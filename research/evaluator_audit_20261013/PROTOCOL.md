# Evaluator audit of the knowledge-reality confirmatory stage: protocol

Study folder: `research/evaluator_audit_20261013/`. Status: exploratory integrity audit. It does
not test a hypothesis.

## Purpose

`research/knowledge_reality_20261013/confirm.py` holds the frozen, never-run evaluator for the
sealed PRISM 24Q2 REP.1M tier. This audit checks that evaluator for five defects:

* eligibility derived from outcomes;
* normalisation on the test batch;
* labels that depend on that normalisation;
* identity matching;
* provenance.

It then proposes corrections for any future protocol.

## Rules

1. **Read-only on frozen studies.** No file of `knowledge_reality_20261013` is edited.
   * Its freeze stays valid, which `verify.py` checks.
   * Any correction applies only to a new, separately frozen protocol.
2. **No outcome access.** No response value of PRISM 24Q2 is downloaded or read. The audit reads:
   * source code;
   * the frozen study files;
   * the three 24Q2 metadata files downloaded in Brief 4 (cell lines, treatments, compound list).
3. **Separation from science.** This audit fixes evaluation integrity only. It changes no
   hypothesis, gate or result of any study. Hypothesis development is in a separate study,
   `research/orbit_contrast_20261013/`.
4. **Mechanical facts are replayed.** `verify.py` re-derives each finding's mechanical fact from
   the frozen source and the metadata: a line of code, a digest or a metadata count. The prose
   judgement in `README.md` is not machine-checked.

## Checks

| Id | Question | Evidence |
|---|---|---|
| E1 | Is the scored population defined from outcome missingness? | `evaluate` in confirm.py |
| E2 | Can a nomination policy see which wells have outcomes? | H2 campaign loop |
| E3 | Is any normaliser estimated on the test batch, and is it used on predictions? | `evaluate`, `develop.drug_r` |
| E4 | Do labels or the active set depend on the test-batch normaliser? | `evaluate` |
| E5 | Are identities matched unambiguously (IDs, cores, screens)? | `read_outcomes`, compound list |
| E6 | Are all evaluator inputs under the freeze digests? | FREEZE.json, read paths |
| E7 | Do the replication ceiling and context-shift readouts share E1–E4? | `replication_ceiling`, `evaluate` |

## Outputs

* `README.md`: findings, severity, and proposed corrections.
* `verify.py`: replays each mechanical fact, and checks that the knowledge-reality freeze still
  authenticates.
