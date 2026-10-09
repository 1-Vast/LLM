# MAP source-context trial

This isolated trial compares source-typed MAP priors with the actual production
`EvidenceLedger.retrieve` lexical/entity prior, using the same public evidence
cards and existing `table_filter` result. An existing configured `deepseek-flash`
client made exactly 24 completions for 12 fixed cases and two LLM arms. A
deterministic classifier saw the same evidence and rules.

All three arms returned 12/12 exact source-qualification packages, with no
case-measurement or independent-confirmation claims. MAP did not improve accuracy
on this task. The task deliberately has explicit source rules; the deterministic
result does not establish that MAP cannot help broader agents. This is neither
autonomous tool-selection evaluation nor experimental biological validity,
functional decision value, a framework comparison, or a production replacement.

The external source is ChEMBL 37. Exactly 105 public requests fetched 779,427 raw
bytes. Ten full canonical-isomeric structures matched exactly; Elagolix sodium
and Adagrasib had no full-InChIKey matches and stayed blocked. No parent/salt/name
fallback or case replacement was used. The official name `(R)-Verapamil
(hydrochloride)` supplies a SMILES without a stereochemical tag; this trial
authenticates the declared full structure and does not infer stereochemistry
from that name.

Four cases have qualifying source cards. Amsacrine is a curated topoisomerase-II
family inhibitor; Gemfibrozil a curated PPAR-alpha agonist; Olanzapine has a
curated D2-like receptor-family antagonist assertion despite the original MAP
agonist row; Triclosan has a CBR1 assay categorized B with target confidence 9.
Family membership does not establish individual-target selectivity. B and
confidence 9 are assay/target-assignment metadata and do not certify measured
physical binding. These ChEMBL assertions may share sources with MAP. Linked
publications/labels were not read or validated as independent experiments.

The requested context is A549 at 24 hours, retaining each original dose/unit:
Berbamine is 0.5 uM, Adagrasib 0.05 uM, and the other ten are 5 uM. No actual
case target engagement was measured. The frozen reference's prose compressed
these doses incorrectly as `5uM(originaldose)`; the immutable CASES/request
records and `REFERENCE_NOTE.json` give the correct doses. Qualification fields
and scoring are unaffected.

Provider totals are 48,636 prompt tokens (8,054 cache hits, 40,582 misses) and
2,010 completion tokens, 50,646 total. No authenticated tariff or provider cost
field was available, so actual monetary cost is unknown. Summed per-call latency
was 13.58 seconds for lexical and 11.21 seconds for typed priors. Fixed call
order, caching and a single run preclude a latency advantage claim. Deterministic
timings cover only classification, while LLM timings also cover prior assembly,
request construction and transport.

`FREEZE.v1.json` predates external mechanism/assay reads. Preserved v2/v3 archives
document pre-response source-category and API-schema corrections. Current
`FREEZE.json` adds Windows SQLite cleanup before any provider call. All 105 raw
responses and their first source freeze remain unchanged. `SOURCES.v3.json`
repairs the derived gene-symbol cards using the actual
`target_component_synonyms` schema. Manual source-reference review was frozen
before provider answers; all answers were frozen before evaluation. The
classifier does not read the reference answers.

Run the five source-contract counterexamples with:

```powershell
D:/anaconda/envs/maestro/python.exe -m pytest research/map_module_replacement_20261009/agent_trial/test_source_contract.py -q
```

Historical source/model calls are immutable and must not be rerun to replace
results. Verification should reconstruct qualification and scoring from the
retained raw responses, tool inputs and frozen provider outputs. Main artifacts
are under `outputs/map_module_replacement_20261009/agent_trial`.

## Hard follow-up: hidden sources and actual tool choices

The follow-up hides ChEMBL records behind five cached-source inspections and
allows two purchases per episode. It retains the same twelve exposed cases,
adds a condition with authentic other-drug/other-target MAP distractors where
available, and repeats presentation orders 11, 23 and 47. Each arm has 72
episodes. These repeats are not independent biological units or fresh datasets.
Both LLM arms use the current configured client and isolated research router;
their errors cannot be attributed to the production framework as a whole.

The independently verified results separate four source-positive cases from
eight cases with no qualifying acquired assertion or blocked full identity:

| Arm | Exact positive packages | Exact null/blocked packages | Schema errors | Unsupported family metadata |
|---|---:|---:|---:|---:|
| Lexical prior + LLM | 0/24 | 27/48 | 36/72 | 6/72 |
| Typed MAP prior + LLM | 0/24 | 26/48 | 44/72 | 6/72 |
| Deterministic same-tools | 24/24 | 48/48 | 0/72 | 0/72 |

The registered combined schema/access violation count is 36/72 for lexical and
45/72 for typed priors, including overlapping categories. Neither LLM arm made
an uninspected identity/card/mode assertion or claimed actual case measurement
or independent biological confirmation. Calling all these failures biological
overclaims would be incorrect.

Every LLM episode selected `exact_identity` then `mechanism`. This confirms that
missing identity inspection was not a failure cause. It also spent a second
inspection after blocked identity and never bought the assay tool for Triclosan,
so the CBR1 assay assertion was unavailable. The deterministic policy selected
assay records for binding/untyped requests and stopped on blocked identity.
All presentation groups retained their tool sequence; complete final answers
were stable in 16/24 lexical and 17/24 typed case/condition groups.

Positive-case field accuracy shows the semantic and schema failures separately:

| Field | Lexical | Typed MAP |
|---|---:|---:|
| Qualified source-card IDs | 13/24 | 18/24 |
| Original curated modes | 19/24 | 24/24 |
| Requested-mode match flag | 24/24 | 24/24 |
| Family/single-protein scope | 18/24 | 18/24 |
| Source-conflict flag | 18/24 | 18/24 |
| Direct-interaction annotation flag | 19/24 | 19/24 |
| Category-B assay annotation flag | 3/24 | 0/24 |

The remaining identity, action, case-measurement and independent-confirmation
fields were 24/24 in both arms. All six presentations of the actual Olanzapine
mode-review candidate missed the conflict flag. Verapamil's calcium-channel
family annotation was incorrectly attached to the requested MAPK1 scope in six
episodes per arm. These are source-interpretation errors, not adjudicated
biological contradictions or causal discoveries.

The prototype terminal prompt described the metadata flags but specified their
Boolean types less explicitly than the initial easy trial. The model often
returned `null` for unavailable assay/direct-interaction metadata, while the
registered source-annotation package required `false`. That boundary contributes
substantially to exact-package failures. Null may express uncertainty sensibly,
but it fails this declared contract. The frozen score remains unchanged; a
post-hoc null coercion would not establish MAP benefit. Typed priors improved
these descriptive card/mode fields, but did not improve the registered complete
package or tool choice.

Exactly 432 logical/provider-reported calls used 850,695 prompt and 31,066
completion tokens, 881,761 total. Typed prompts used 371,769 tokens versus
478,926 lexical tokens (22.37% fewer), with the same 216 calls per LLM arm.
Both bought 144 inspections; the deterministic arm bought 132. Price and
lost-transport billing remain unknown. Caching, concurrency and repeat exposure
preclude a latency or independent replication claim.

The independent verifier was frozen before inspecting any hard provider output.
It passed 345 immutable-file hashes, full-structure/raw-card closure, all 216
packages, 432 request access packets, 420 purchased inspections, token totals,
subgroup scores and presentation stability. Its report is
`hard/HARD_VERIFIED.json`; run offline checks with `verify_hard.py`. No additional
provider calls are needed for verification.

## Post-hoc admission diagnostic

`offline_guard.py` implements a small research-only admission gate: invalid
schema or unsupported affirmative source fields cause explicit abstention. It
preserves the original answer and never coerces null to false. The gate admitted
36/72 lexical and 27/72 typed packages. Positive coverage fell to 9/24 and 1/24,
respectively, with zero correct complete positive packages and zero admitted
positive source-card assertions. This coverage loss shows that rejection alone
does not solve source acquisition or interpretation.

A separate receipt renderer reconstructs metadata directly from already
purchased source records. It yields 66/72 exact packages and 18/24 positive-card
recall for each LLM arm. It cannot recover the six unpurchased Triclosan assay
records. This is deterministic source rendering, not rescued LLM reasoning or
MAP advantage. A flag of false means no qualifying inspected annotation; it
never establishes negative biology.

The concrete engineering direction is to use an identity-first source scheduler
that selects mechanism versus assay by the requested evidence type, stops when
identity is blocked, and renders typed claims from admitted source receipts.
The existing deterministic research comparator already verifies that behavior
on this fixed source menu. The post-hoc gate has four counterexample tests and
its own freeze; outputs are in `hard/OFFLINE_GUARD.json`. Production integration
and a fresh task set remain separate work.
