# Raw-review code recovery and reproduction

The generator is tools/datasets/state_raw_review.py. It requires a new --out
leaf, refuses any existing leaf before reading inputs, carries the explicit
frozen human-review notes as an input, and reads no expression X/gctx values,
fitting routines or APIs. LINCS2020 siginfo access here is header-only.

The first metadata reproduction retains its execution_receipt.json and exact
executed_source_v1.py.txt. A streamed counter then replaced the temporary list
used to count 43,209,765 GxE cell annotation lines. streamed_metadata/ preserves
that run and executed_source_current.py.txt preserves its exact source bytes.
The intermediate reproduction_validation.json found 818 locators differed
because a descriptive source_locator field was omitted; original row indices,
values, counts and outcomes were unchanged. The final code restores it and
final_metadata/ is the authoritative corrected reproduction. Its 8,036 source
locators match the frozen original review semantically, all 12 human task
classifications are preserved, and all 11 final checks pass. Failure receipts
and previous outputs are retained.

Explicit --reuse-recorded-hashes retains 42 already verified complete-file
hash references while re-reading metadata. Those files are not represented as
fresh whole-file rehashes; Nyman condition MAT and the DepMap expression file
were freshly hashed. The original raw_review/ six artifact hashes are unchanged.
Human task eligibility is input review evidence, not a new inference from menus.

Reproduce to another new leaf:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_raw_review --out NEW_OUTPUT_LEAF --review-notes outputs/state_identifiability_20261001/raw_review/raw_source_review.json --reuse-recorded-hashes
```

Omit --reuse-recorded-hashes for complete fresh SHA-256 checks of source files.
final_validation.json gives commands, source hash and semantic/overwrite checks;
final_metadata/execution_receipt.json gives the runtime environment and hashes.
No state-gain experiment was performed.
