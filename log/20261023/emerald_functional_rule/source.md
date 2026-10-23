# Independent identity-only combination qualification

2026-10-23. Source role, before peer cross. No other new-phase agent opinions/candidates read. Used only previously acquired official pinned public summary bytes and previously pinned official method source. No network, API, expression acquisition, phenotype decoding, fits or author-code execution.

## Executed qualification

`research/emerald_functional_rule_20261023/source/identity.py` projects exactly `cell_line` and `condition` with Arrow. Input SHA256 `3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9`, official EmeraldBay revision `f2a0be6b02f731553657f0115c345b20bb020ede`. Raw acquired bytes contain phenotype values, but none are projected/decoded by this script. Identity output `SOURCE_IDENTITY.json` includes every condition and exact-matching audit. Numeric dose equality uses parsed numeric literals normalized through Decimal(str(value)); drug spelling and unit must match exactly; no nearest-dose substitution or unit conversion.

Confirmed 4,992 rows, 52 contexts, 93 conditions, 44 noncontrol single-agent conditions representing 19 drugs. There are **47 combination conditions, not 47 distinct drug pairs**: 41 binary, 3 triple and 3 quadruple conditions, representing **16 unordered drug sets**. Each combination condition occurs in all 52 contexts: 2,444 context-condition queries before label missingness/eligibility is inspected. No response missingness was inspected.

Only **17 combination conditions across eight binary drug pairs** have every component at exactly an available single-agent drug/dose/unit. This yields **884 identity-eligible context-condition pairs** with exact support in all 52 contexts. Pair counts of eligible dose conditions:

| Unordered pair | Exactly supported combination conditions |
|---|---:|
| Adagrasib + Cetuximab | 2 |
| Adagrasib + Galunisertib | 2 |
| Adagrasib + LY3200882 | 2 |
| Capecitabine + Gemcitabine | 3 |
| Gemcitabine + Paclitaxel | 2 |
| LY3200882 + Sotorasib | 2 |
| RMC-6236 + Vociprotafib | 2 |
| Galunisertib + Sotorasib | 2 |

Thirty combination conditions lack one or more exact single-agent components. Eight drugs have no single-agent condition at any dose: Dabrafenib, Leucovorin, PF-06952229, Tipiracil, Trametinib, Trastuzumab, Trifluridine, Tucatinib. Other failures are dose mismatch, e.g. Adagrasib/Sotorasib 0.01 uM occurs in combinations but single-agent doses are .005/.05 uM; do not silently replace .01 by .005. Capecitabine/Oxaliplatin combination doses are not exact single-dose supports. All triple/quadruple conditions lack full exact support.

Combination order varies between strings, so canonical unordered **drug set** grouping is necessary; lexical string splitting would manufacture separate combination tasks. The same pair has two or three sampled dose combinations and is not necessarily a complete dose-response matrix or a fixed-ratio titration: group all its sampled combinations together. Single drugs have only two or three doses, not dense curves; adjacent-dose feedback is a separately purchased observation and does not establish interpolation ground truth. Full identities in JSON permit freeze without response-driven family selection.

## What the original implementation does

Pinned Rhaister revision `75fed20a1d97b05a09bf25c5341762141882106a`: `splits/EmeraldBay/dataset.toml:29` sets `drop_multi_drug=true`. `rhaister/prepare_sensitivity.py:121` applies filters: first drops null growth values, then recognizes multi-drug conditions using regex `\),\s*\(` and removes them; parsed `drop_drugs=[DMSO_T0]` removes time-zero control, **not DMSO_TF**; finally averages response by `(cell_line,condition)`. The source implements scalar support→query ridge for the retained single-agent menu, not a combination model. Source `prepare_sensitivity` feature loaders also invoke configured multi-drug treatment filtering. Therefore author .26/.31 summary cannot qualify combination accuracy. No full paper combination treatment is authenticated: prior paper request is a 429 body. This report authenticates the official implementation's exclusion, not a claim that the paper evaluated no other combination task anywhere.

Changing drop_multi_drug=false is a new evaluation contract. It does not turn the ordinary model into a biological interaction mechanism; direct ridge over any acquired support can predict combination labels as named targets if the same combination is present in source contexts. That is **cross-context same-combination prediction**, not zero-shot new-combination composition. All author metric numbers remain unreproduced source claims.

## Feasible and distinguishable contracts

**Conditional GO for a retrospective released-relative-phenotype diagnostic**, not numerical or novelty GO. Exact single feedback→combination prediction is identity-feasible on the 17-condition/eight-pair menu if the forthcoming response-null check permits it. The entire menu must be frozen now; reducing it by measured outcomes creates selection. Use released scalar as a relative pooled phenotype. Its unidentified transform is not a survival probability; products/Bliss excess cannot be assigned drug synergy interpretation. Additive/minimum/component ordinary models may be tested as predictors on this scale, with names reflecting assumptions, not pharmacological truth.

Two scientifically different questions must be kept separate:

1. Heldout context, combination label already observed in source contexts: source same-combination functional prior plus acquired single feedback can be strong and legitimate. Compare mean/additive, tuned scalar/conditional ridge, hierarchical and direct same-information methods. This tests contextual functional update, not novel-combination transfer.
2. Heldout unordered combination drug set across **all contexts and doses**: do not train or select on any label of that combination set. Other combinations sharing agents may remain only if explicitly allowed. The eight exact-support pairs are at most eight group-level composition units; all 884 rows are not 884 independent composition tasks. A connected component split of the drug-pair graph is stronger drug-sharing exclusion but may leave too little data; feasibility must be established from identities, not inferred by row count. Nested tuning must exclude the same pair group from all source fitting/selection. Strong direct compositional predictors receive the same single feedback and known identities/doses.

Neither contract establishes world-model, agent, inheritance or improved-improver contribution. A candidate still needs a specific state/function law and an independently tested value advantage; identical support-query ridge in new packaging is insufficient. Experimental selection policy must operate on lawfully available feedback packages; do not access combination feedback merely because public bytes are on disk.

## Pool/source guards and limitations

Acquisition is a pooled condition across contexts. If purchasing single drug-dose condition yields all 52 contexts, charge the whole condition/pool assay plus required controls/replicates; disclose whether all those rows become observable and give them to ordinary competitors. Charging one context row while the same physical package supplies all rows is unjustified. Conversely, withholding some accessible pool rows is a benchmark restriction that must be declared; it cannot establish actual saved experimental cost. Multiple contexts in the same pool/condition do not certify independent biological experiments. Public summary lacks sample/run/batch fields and loses potential replicate identity; per-row bootstrap or treating context rows as independent assay replicates is unsupported.

Guard source partitions at model training, preprocessing, residual estimation, hyperparameter/search choice and inherited update-rule selection. Same pooled assay source/query contrasts and shared controls create possible covariance; no source-version seal proves physical independence. Exact public lookup is a zero-error information competitor whenever the claimed real user may access these same historical query labels; a hidden-label replay is methodological evaluation, not prospective drug discovery. A new independent future task/assay is needed for prospective claims.

**Qualification risks:** only eight exact-supported pair groups; only two/three dose conditions each; shared drugs and pooled contexts reduce independent groups further; no combination RNA acquisition/preprocessing qualified; scalar-null eligibility remains unopened; formula/absolute calibration and biological replicate/run identities remain unauthenticated. None is repaired by using missing-dose interpolation as if measured, source same-combination labels as if novel compositions, relative growth as Bliss viability, or 52 context rows as free independent assay purchases.
