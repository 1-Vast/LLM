# Synthetic study-contract tests

2026-10-23. Command: `D:/anaconda/envs/maestro/python.exe -B -m pytest research/evidence_portfolio_optimization_20261023/test_study.py -q -p no:cacheprovider`.

Exit 0; three tests passed (`... [100%]`). Tests use generated temporary inputs only:

- Metadata-only eligibility freezes successfully with invalid response strings and remains unchanged when all response values change. Global scout/final plate roles are disjoint.
- Changing only synthetic future final responses leaves persisted nominations, final whitelist and all charges unchanged. The choices receipt exists and binds the nominations before final conversion. An odd seven-read budget buys four scout and three final reads for the fixed paired control. A synthetic witness verifies that revised adaptive finals need not be a subset of paired direct finals.
- Missing purchased scout/final observations remain charged, produce no repeat-positive successes and are not replaced.

The initial missing-fixture-file failure and its test-only correction are retained in `TEST_STUDY_INITIAL_FAILURE.md`. This pass verifies selected software contracts, not real-data arithmetic, biological independence, certification or RSI. No real outcomes were opened by these tests.

After the root's metadata-only schema failure and pre-outcome parser correction, one single-anchor identity/schema test was added. The same command reran once and exited 0 with **four tests passed** (`.... [100%]`). The additional test checks scalar concentration normalization, preservation of the literal identifier `NA`, exclusion of multi-anchor/piped, missing and invalid/nonfinite identities, and recorded exclusion counts during a synthetic metadata freeze. Earlier three-test results remain accurate for their earlier source state; the four-test run is the latest pre-freeze check.
