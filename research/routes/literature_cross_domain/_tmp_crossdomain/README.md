# Literature survey: cross-domain minimal distinguishing observations

| Item | Value |
|---|---|
| Goal | survey (baseline = candidates checked for fair comparison: code, data, split, baseline numbers; survey = state of the field, classic and frontier papers by category). Both include the latest-paper analysis and the novelty check |
| Ideas checked for novelty | <the user's idea(s), or "none given: gaps from analysis.md section 6"> |
| Window | 2018-01-01 ~ 2026-10-30 (limits latest papers, frontier papers and baseline candidates; classic work and the novelty check have no time limit) |
| Venue scope | <venue sets used; IF-proxy threshold if any — IF-proxy = OpenAlex 2yr_mean_citedness, not the official IF> |
| Searched on | 2026-10-30 |
| Sources used | <OpenAlex (key pool) / arXiv / OpenReview / Europe PMC / Crossref / OpenCitations / WebSearch / browser: list only those actually used> |

## Query groups

| Group | Purpose (field / idea n) | Boolean query | OpenAlex whitelist | OpenAlex any time | OpenAlex recent | arXiv | OpenReview | Europe PMC |
|---|---|---|---|---|---|---|---|---|
| G1 | field | <query> | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

## Statistics

| Metric | Value |
|---|---|
| Queries run | <rows of 00_index/searched_queries.tsv> |
| Unique records after dedup | <merge_rank.py output> |
| Records read (title + abstract) | <n> |
| Latest papers analysed (inside the window) | <n> |
| Verdicts (baseline) | GO <n> / RISK <n> / DROP <n> / UNKNOWN <n> |
| Papers classified (survey) | <n> in <k> categories: classic <n> / frontier <n> |
| Novelty | ideas <n>: Done <n> / Close <n> / Not found <n>; works read in full (F) <n> |
| High-relevance records / merge rounds | <from 00_index/merge_history.tsv> |
| OpenAlex keys | <oa_keys.py list at the end: active key label, credits left, any key switched or refused> |

## Conclusions

1. <conclusion> — evidence: <file#section or link>
2. ...

## Stop condition met

<which condition (see SKILL.md) and the evidence, e.g. "last 2 query rounds added 0 high-relevance records">

## Coverage and limits

- Not covered: <sources that failed or were skipped, paywalled items left UNKNOWN>
- Incidents: <network errors quoted verbatim; key switches; quota>

## Files

| File | Content |
|---|---|
| README.md | this overview |
| PROCESS.md | step-by-step record: commands, counts, decisions and reasons, errors and incidents |
| analysis.md | latest-paper summary, hotspots, datasets, metrics, limits, candidate gaps, review check, groups |
| novelty.md | novelty check: closest work per idea, with evidence levels |
| candidates_screened.md + 99_dropped.md | baseline: four-item verdicts, dropped papers with counter-evidence |
| field_survey.md | survey: state of the field, taxonomy, classic and frontier papers by category |
| 00_index/ | searched_queries.tsv, seen_papers.tsv, candidates_top.tsv, venues_checked.tsv |
| raw/ | normalized records of every query (API keys scrubbed) |
