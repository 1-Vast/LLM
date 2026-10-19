# Deviations and disclosures

1. **Not pre-registered.** The two source papers were read in full, including outcomes, before the G0
   level rules and the explanation model were written. The study is labelled `completed` and
   exploratory in `research/STUDIES.json`, has no `FREEZE.json`, and makes no frozen-confirmation
   claim. G2-G5 parameters are still unfilled and must be frozen before any outcome is opened.
2. **Hypothesis labels.** `H_E`, `H_M`, `H_C`, `H_O` are not defined in the repository; they were not
   used (see PROTOCOL.md). If their definitions exist elsewhere the mapping is open.
3. **Extraction method.** Records were extracted by hand from Europe PMC full-text XML (S1 and S2 digests
   in `records.py`, verified again by `verify.py --online`). Figure bars, supplementary files and the
   S2 SI PDF were not read. The first pass used a summarising fetch tool; every claim used in a
   record was re-checked against the XML text. The journal page for S2 returned HTTP 403 and was not
   read.
4. **Qualitative outcomes.** The JB211 and T217D terminal results are statements in the text
   ("no significant", "reverted"); effect sizes were not extracted.
5. **Replay menu.** Only bundles with a published outcome form the legal replay menu. Choosing the
   menu by outcome availability is a retrospective-design limitation; the policy cannot see the
   outcomes themselves.
6. **Isolation is process-level.** No OS-level sandbox was used because no LLM Agent was run.
7. **Costs.** No price or turnaround exists in either paper. Wells are `arms x 3 replicates`
   (technical wells per arm unreported); currency and days are null, not zero.
8. **Spending.** Actual expenditure: two free full-text downloads (about 0.4 MB), no API calls, no
   data purchase, no wet-lab work.
