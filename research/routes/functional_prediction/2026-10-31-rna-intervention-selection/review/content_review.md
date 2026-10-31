# Independent final content review

2026-10-31. Scope: local-only review of the final synthesis, newly integrated content and decisive underlying evidence. No acquisition, model fitting, downloaded-code execution or shared-file edits. This reviewer previously performed the ENCODE admission and control-only audits and read published aggregate literature results. This is an independent content check of the completed synthesis, **not an outcome-blind novelty review**.

## Decision

The scientific stop and the integrated distinctions are supported. **One actionable exposure-wording correction is required before final closure:** the newly inserted RESEARCH_REPORT section says protected outcomes “stay unread”, and the new registry limitation says “protected outcomes unopened”. Root subsequently hashed pre-existing files for preservation, which is byte access. Replace those literal statements with “protected outcomes were not numerically or semantically inspected or used”; explicitly distinguish preservation hashing in the report exposure paragraph. This does not undermine the no-effect-analysis boundary. Root owns corrections. Hash bindings below identify the reviewed snapshot, before this requested wording repair.

## Actual reading scope

- `report.md`: full lines 1–89.
- All five inserted text/TSV regions specified by `review/integration_change_receipt.json` were read in full by their exact byte offsets/lengths; see the binding table below.
- `research/STUDIES.json`: full new study entry at studies[48], and the new route_storage entry; all pre-existing registry values compared structurally against `review/registry_before.json`.
- `challenge/exact_source_final_review.md`: full lines 1–63; `root/annotation_audit.json`: full lines 1–60; `root/rmats_source_slice.json`: full manifest.
- `source_code/rmats321beta/RNASeq-MATS.py`: lines 466–566, particularly 492–497 and 528–536; `bin/joinFiles.py`: entire file; `bin/processGTF.SAMs.py`: lines 682–745; `bin/MATS.processsUnique.sam.py`: lines 300–337 and 732–742; `MATS/rMATS_Unpaired.sh`: lines 1–30. These were read as text, never imported or executed.
- `candidate_v1.md`: full lines 1–37 and `candidate_v1_freeze.json`: full lines 1–9.
- `encode/control_audit/control_audit.md`: full lines 1–46; all 30 table records in `control_audit.json` inspected by aggregate-field checks, with earlier firsthand creation of that local audit disclosed. No new archive-effect reading was performed.
- `aso/admission.md`: full lines 1–80; `aso/audit_counts.json`: full lines 1–48; original OligoAI relevant abstract/architecture excerpts in `aso/oligoai_passages.txt` (especially lines 1,17–21) and original KATMAP publisher paragraphs 148–150 and 159. These exposed published aggregate study results, not new episode outcomes.
- `library_verify_final.json`: full lines 1–27; `usage.json`: full lines 1–108; each role HTTP ledger was parsed for counts/body-byte totals only. `review/final_preservation.json` was read in full as the root-owned preservation receipt. The 323-byte `root/sources/scsp_data.zip` redirect body was read and confirmed to be login redirection HTML, not an archive.

## Expected versus observed scientific checks

| Independent expectation | Observation | Assessment |
|---|---|---|
| A selection rule must be distinguished from a measured effect or prediction failure. | Exact RNASeq-MATS.py awk condition requires positive totals in both treatment and control, plus pooled isoform support and nonzero lengths. The downstream join iterates statistical output. | Stop is justified; no numerical failure inferred. |
| Reference-absence counts cannot be assigned a cause without a faithful event identity and trace. | Report explicitly retains 20,068 configurations/8,649 genes, 6,990–8,412 present per archive and 3,568 common, while warning that source dedup omits outer flank/gene/strand identity. Count lookup bins depend on full flanks. | Correct distinction; no unsupported filtering-attribution or count invariance. |
| Passing control arithmetic is insufficient to certify the missing universe. | 30 tables/448,068 rows and 872,774 comparable control slots/zero mismatches match the audit. Cross-cell eligibility counts agree. Report calls them dependent emitted-table counts. | Correct. |
| Metadata unit counts must not become independent sample sizes. | 522 KD/187 current KD–eCLIP associations are qualified; 24 BAM/biosample origins do not establish independent errors or named vector slots. ASO pairs/labels/patents remain dependent or unverified units. | Correct. |
| ASO structural edit candidates require assay and source-family equivalence. | 174,459/178,403 release/enriched rows, 96,303 structures, 240 token candidates and 14,586 tiling pairs match audit JSON; zero authenticated controlled edits is distinguished from absence. | Correct. |
| Unavailable source bodies must not be a scientific negative. | SCSP documented data acquisition failures are described as timeout/TLS/login, and the small .zip is expressly not data. | Correct. |
| Prior overlap must be task-specific and reading-level-limited. | KATMAP original paragraphs 148–150 already motivate baseline/log-odds, and cross-cell inverse identification is distinguished from candidate response transport. OligoAI original architecture uses RiNALMo/context/chemistry/dose. P/A/R limits and unauthenticated Atlas2 manuscript remain explicit. | Correct; no exhaustive novelty claim. |
| A frozen proposal is not a full numerical protocol. | Candidate contains unfilled prefit numerical specifications and future freeze requirements; report explicitly calls the existing freeze proposal-only. | Correct. |
| No-fit claims require exposure qualifications and must not imply pristine literature. | Report discloses control-only and ASO validity access plus prior published aggregates, and reports zero fits. Literal protected unread/unopened wording in two integration surfaces conflicts with later byte hashing. | Repair wording as above; no semantic outcome access found. |
| Restart must resolve the original contract before effect-based redesign. | Unfiltered event/count inputs or separately scoped raw counting, ambiguity/identity/baseline/rivals/numerical freeze and fresh review are required. Observed-intersection rescue is rejected. | Appropriate; no unauthorized continuation. |
| Prior records must survive integration exactly. | Removing every specified text insertion recovers the original SHA256; the index byte prefix is exact. Removing one new study and one actual route key reproduces all registry values, including all 48 old studies. | Independently passes. |
| Resource accounting is based on receipt rows, including partial/error/redirect bodies. | Recomputed per-role counts 36/22/22/5/10 and bytes 208393228/19375417/27696297/1191630/183629 total 95 and 256840201. Verification JSON matches report inventory and has no errors/warnings. | Correct accounting; inventory integrity is not scientific validation. |

## Binding of the reviewed snapshot

| Surface | Actually read region | SHA256 |
|---|---|---|
| Episode report.md | Full lines 1–89 | `8877eb5ba03544c0c135e88310b82eca7276c91e43698d7874f9a1dc7e492568` |
| research/README.md | Bytes [23,787); lines 3–5 | `961fc6a2e1a7d7a4eceb78e8072c519118c9cb74bc4e317f75715d23a67bcf26` |
| log/RESEARCH_REPORT.md | Bytes [0,6095); lines 1–21 | `26e1223292279c67bab43d11d8d7f1e743846805f929ec856a2049c173395308` |
| log/ROUTE_EXPERIENCE.md | Bytes [35,1072); lines 3–5 | `477826ac49e4dfef6e32a823ef35760232ddc4781fe45c1e0c1d77f90e8272c1` |
| reference/README.md | Bytes [0,2066); lines 1–3 | `f3abbd855aae5ce4d08874993a3aefdc0498758b2cf32a2c5a8273184a7c7749` |
| log/STUDY_INDEX.tsv | Bytes [253807,254776); lines 214–215 | `891db51aa05eff3a835accaeb50cf075a467a6730dfd8aba7bbbf62d19aa3e4e` |
| research/STUDIES.json | studies[48] and route_storage[new_route_storage] | `3ef0b05158282771fc19d6d9b5222202aca804c59960aa19dc09a5a4c67df0e9` |

## Remaining limits

This review independently inspected source filter/join/identity paths, aggregate preparation records, the whole report and every new integration region. It did not reproduce full raw BAM processing, authenticate vector-slot order, read treatment values, rerun ASO structural counting, execute author code or repeat the owner library verifier. No actual per-event filtering cause was inferred. The original ENCODE paper supplies the software-version link; this review does not establish an unmodified historical command trace for each experiment. These limits do not restore the missing independent universe. Global no-fit/protected-semantic-access statements also rely on the root-owned execution record; filesystem integrity alone cannot prove that no process ever accessed a value.

Root preservation receipt reports 5,925 pre-existing files unchanged, one pre-existing missing file still missing and eight authorized surfaces excluded, with unchanged HEAD and no unexpected paths. This reviewer independently verified the six integration-preservation claims above; it did not rehash all 5,925 files. Root should bind the corrected report/integration hashes and mark preservation closure only after the wording repair is reviewed.

## Post-correction content recheck — resolved

2026-10-31. Root applied the requested narrow wording repair. Re-read the corrected report exposure paragraph (line 81), the full revised RESEARCH_REPORT insertion and the full new studies[48] entry. Each now says protected outcomes were not numerically or semantically inspected or used, and explicitly distinguishes byte-level preservation hashing. The original actionable wording issue is **resolved**; no remaining correction was identified in this narrow recheck. The original snapshot review above is retained.

Independently verified that replacing only the corrected report sentences with their previous wording recovers the original reviewed report SHA256. Rechecked all five text insertion removals against the original hashes using the updated offsets/lengths; all pass, including the exact historical STUDY_INDEX prefix. Removing the new registry study and route-storage entry again reproduces registry_before.json exactly, preserving all 48 old studies and every other old registry value. No scientific fact, proposal freeze or outcome was changed by this repair. No acquisition, fitting, author-code execution or new source reading occurred.

| Corrected surface | Current SHA256 |
|---|---|
| report.md | `cb1842891f7ad181e2fe96a5b4e3b8457111f167be6bb867856ff5a736ac3c85` |
| log/RESEARCH_REPORT.md | `c0e6b1f2fe7fccd58e36d562ca22425673586e445a68d7f840a3423cedef253e` |
| research/STUDIES.json | `0f85242d86c74d6033576d013f6a16582c9bc63057d0327678ed615a1568b145` |

The other four integration-surface hashes remain as bound in the original review. Current log/registry hashes agree with the updated integration receipt. Final synthesis content review is complete, subject to the scope and exposure limitations recorded above.
