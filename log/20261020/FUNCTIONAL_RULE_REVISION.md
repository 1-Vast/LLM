# Daily record: functional-rule-revision study (2026-10-20)

Study package: [research/functional_rule_revision_20261020](../../research/functional_rule_revision_20261020/REPORT.md).
Decision: **UNSUPPORTED** (exposed O'Neil 2016, estimation pilot). Raw route; 583 pairs x 39 cells; S/C/G/F = 350/87/58/88 pairs.

Sequence (all in this session): preflight (`pip check`, source verification) -> `run.py qualify` (parse originals, partition, sealed role files)
-> S-only development and `run.py freeze` (margin 0.005, dictionary of 16 edits, 60-pair challenge panel) -> `run.py challenge`
(initial predictions sealed, C panel disclosed once, refit/full dictionary/conventional/revision/API arms, nominations sealed; API: one
deepseek-flash request, 1 HTTP attempt, 3,669 tokens) -> `run.py retention` (one G query per arm; all four candidates rejected) -> `run.py final`
(single F opening) -> `verify.py` (VERIFY OK). Wall clock for the model stages: a few minutes each on 4 threads.

Inputs consumed (hashes in `PROVENANCE.json`): the three authenticated O'Neil workbooks, `tools/datasets/combination_screens.py` (reader only),
`src/agent/llm.py` (client), the uncommitted preparation files listed there. No historical study was modified; production code unchanged.
Regenerable caches and sealed role files live in `tmp/functional_rule_revision_20261020/` (git-ignored); scratch S-only development scripts in `tmp/frr/`.
Not authorised/not done: ALMANAC vault, new datasets, physical-cost accounting, a second attempt.
