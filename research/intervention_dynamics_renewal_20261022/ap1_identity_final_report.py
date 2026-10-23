"""Write reports using saved identity receipts and an already-local primary article."""
from html.parser import HTMLParser
import json

import ap1_identity_stage1 as first


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def write_markdown(name, text):
    with (first.OUT / name).open('x', encoding='utf-8') as handle:
        handle.write(text)


def main():
    source = first.BASE / 'skeptic/AP1_MEMORY_PRIMARY.body'
    parser = Text()
    parser.feed(source.read_text(encoding='utf-8'))
    article_text = ' '.join(parser.parts)
    needle = '46 tracks in total'
    if article_text.count(needle) != 1:
        raise ValueError('primary_track_count_quote_not_unique')
    location = article_text.index(needle)
    excerpt = article_text[max(0, location - 215): location + len(needle) + 245]
    summary = json.loads((first.OUT / 'STAGE3_LINEAGE_PAIRING.json').read_text(encoding='utf-8'))
    first.write('STAGE3_PRIMARY_N_DISCREPANCY.json', {
        'utc': first.utc(), 'primary_local_path': str(source), 'primary_sha256': first.sha(source),
        'primary_article_doi': '10.1038/s41467-026-70862-w', 'exact_primary_phrase': needle,
        'primary_excerpt': excerpt, 'workbook_complete_one_to_one_pairs': len(summary['one_to_one_paired_keys']),
        'status': 'UNRESOLVED_SOURCE_VS_PRIMARY_COUNT_DISCREPANCY',
        'no_rows_removed_or_reclassified': True, 'network_requests': 0,
        'interpretation': 'The AutoRecovered workbook gives 47 complete identity pairs; the primary prose says 46 tracks. No authenticated exclusion or publisher equivalence is available. This is not evidence of a paper error or permission to drop a pair.'})

    write_markdown('REPORT_STAGE2.md', '''# AP1 exact identity qualification: Stage2 and saved-data postchecks

Stage2 authenticated design identities without opening numerical reporter, growth, colony-count or FISH response bodies. All four additional guard tests passed, all prior frozen files and source bytes remained unchanged, and no network request occurred. The source is the author-repository AutoRecovered workbook; publisher equivalence is unverified. Stage1's 16 response-field NA strings, Fig4e state-category strings and the published-code observed zero remain disclosed, so the whole dataset is not sealed.

Fig2g has three experiment aliases (exp1516, exp2536, exp2112), each with all six condition identities. The complete dictionary differentiates 5 nM trametinib with/without JNK-IN-8, 1→1 nM trametinib with/without 1 μM JNK-IN-8 pretreatment, and 1→5 nM with/without that pretreatment. These aliases and the complete roster do not authenticate independent biological starts. Colony response values stay closed; the exp2536/hi2 published-code zero remains previously exposed.

Fig3b has 10,866 annotation rows under 16 dataset labels and 96 dataset/sample groups. Its 96 exp_id values are grouping identities, not 96 proven biological runs. Raw/summary dataset/sample pairs match only after explicitly replacing nonbreaking spaces with ASCII spaces in the summary labels; originals are preserved. Raw Time is a design frame (0 or 1), not biological days.

The saved-identity postcheck compared the entire `(sample_identifier,Id,XY,Z,Time)` multiset for every dataset pair, retaining multiplicity and lexical values. Dataset and exp_id remain grouping labels. Each dataset has no repeated complete tuple internally. The exact-equality clusters are:

| Dataset labels | Rows in each member | Identity conclusion |
| --- | ---: | --- |
| 1, 5, 11 | 526 | identical complete identity multiset |
| 2, 6, 12 | 888 | identical complete identity multiset |
| 3, 7, 13 | 718 | identical complete identity multiset |
| 4, 8, 14 | 518 | identical complete identity multiset |
| 9, 15 | 695 | identical complete identity multiset |
| 10, 16 | 763 | identical complete identity multiset |

There are 14 exact-equality dataset pairs; every other dataset pair has zero overlap of those full tuples. This authenticates reuse of published annotation identities across labels. It does not by itself prove numerical response duplication, justify automatic deduplication, or establish six independent experiments. An authenticated condition/channel/run dictionary is still required before a split or matched-condition state→function task can be specified.

Fig5b has 240 rows and Fig5c has 225 rows, each with only six distinct condition/XY/Z/Time keys. Their allowed Tags, Shape and Name values are NA. Repeated phase/field annotations do not establish same-colony trajectories or independent runs. The two conditions in Fig5b are trametinib-off/continuous; those in Fig5c are A485/SGC-CBP30. Raw Time values 1, 3, 4 remain design identities. Fig4c has 68 opened XY/Z/Time triples, all 1/1/1, and an identified background section; no lineage trajectory or independent-run qualification follows.

Fig4e's string/type matrix resolves the earlier header concern: D5/D55 are lineageId, E4/E54 generation, F4/F54 annotationID and I4/I54 file_id. E's lineage1/lineage2 values label the two sections. The zero intersection of `(file_id,E generation)` in the original Stage2 summary is not a lineage-join test and must not be cited as absence of pairing. Root subsequently authorized only the exact D/F/I final keypass; its result is in REPORT_STAGE3.md. The original Stage1 and Stage2 receipts remain unchanged.

Evidence: STAGE2_IDENTITIES.json, STAGE2_IDENTITY_SUMMARY.json, STAGE2_4E_STRING_TYPE_MATRIX.json, STAGE2_FIG3_FULL_TUPLE_POSTCHECK.json and STAGE2_FINAL_CHECKS.json. Code is in research/intervention_dynamics_renewal_20261022. Identity availability alone does not qualify world-model, agent, inheritance or RSI contributions. This source audit stops after Stage3.
''')

    write_markdown('REPORT_STAGE3.md', '''# AP1 final lineage keypass: 47 paired reporter identities

The last approved source pass authenticates 47 unique starting-cell→final-colony identity pairs in Fig4e, joined exactly by `(file_id,lineageId)`: 39 from VID1578 and 8 from VID1579. There are no duplicate complete keys in either section, no ambiguous shared key, and no starting-only or final-only complete key. This is positive evidence for a source-level paired reporter endpoint.

Starting rows 6:53 contain 48 authorized rows but only 47 complete identity keys. Row 53 has numeric-typed D/F/I cell nodes without opened value bodies; neither lineageId nor file_id is available there. It is retained as an incomplete identity row. Final rows 56:102 contain 47 complete keys. No row-order pairing, exclusion, imputation or death/loss classification was applied. All per-key row lists and incomplete/duplicate/unmatched lists are preserved in STAGE3_LINEAGE_PAIRING.json.

The primary article (DOI 10.1038/s41467-026-70862-w) describes “46 tracks in total”; the repository AutoRecovered workbook contains 47 complete one-to-one identity pairs. The exact primary excerpt and SHA256 are preserved in STAGE3_PRIMARY_N_DISCREPANCY.json. This discrepancy is unresolved. No pair is dropped to force agreement with prose, and it does not establish a paper error. Publisher equivalence and any exclusion rule remain unauthenticated.

The paired endpoint concerns reporter measurements in selected therapy-resistant colonies and their recorded ancestors. It is not a complete initial-cell attempt/dead/lost tree. It therefore cannot supply the denominator or missing-outcome mechanism needed to bound selection, estimate the probability of a subsequent drug-B functional response per initial cell, or distinguish absence from death/loss. The existence of selected resistant colonies does not provide a separately recorded drug-B challenge outcome for all attempted starting cells. No selection bound is applied.

This pairing establishes a narrower prerequisite for reporter-state prediction. It does not authenticate independent biological runs from the two file labels, a treatment/action dictionary over paired trajectories, out-of-run intervention generalization, a state→function training target, or enough independent tasks for inherited agent/RSI evaluation. No numerical endpoint was inspected and no prediction or new method was trained. The source cannot presently support claims about world-model benefit, agent benefit, inherited capability, joint benefit or improvement-policy RSI.

The exact final policy opened only D6:D53/D56:D102 numeric-or-string lineageId, F in those rows strings only, and I in those rows strings only. It did not open D54, generation values, numeric annotationID, G/H fluorescence, J ratio or other response bodies. Of 285 approved positions, 188 identity values opened: 94 lineageId values and 94 file_id strings. All annotationID numeric values remained closed. No formulas/caches, booleans or errors were decoded. Root authorized reuse of Stage2's passed guard tests without redundant new tests.

STAGE3_FREEZE.json records the final protocol/reader and prior evidence hashes. STAGE3_FINAL_CHECKS.json confirms source_sha256_matches via source_hash_matches=true, all_frozen_unchanged=true, response_value_bodies_opened=false and network_requests=0. The source SHA256 remains 6bcdbdd451e29246c5db16e9a67c43abf937e7cf3fb8796931d83096feaff42a. Stage1/Stage2 frozen files and outputs were preserved. The reader schema uses response_value_bodies_opened, not response_values_interpreted. Earlier permitted categorical/NA and published-code zero exposures remain part of the record; the whole dataset is not sealed.

Final decision: preserve the positive 47-pair reporter identity qualification, retain the 47-versus-46 source discrepancy and incomplete row, and stop AP1 source expansion. No additional workbook, CSV, outcome or network read is authorized by this task.
''')
    print(json.dumps({'status': 'FINAL_REPORTS_WRITTEN_SOURCE_STOP', 'reports': ['REPORT_STAGE2.md', 'REPORT_STAGE3.md'],
                      'source_matches': first.sha(first.RAW) == first.EXPECTED,
                      'primary_phrase': needle, 'pairs': len(summary['one_to_one_paired_keys'])}))


if __name__ == '__main__':
    main()
