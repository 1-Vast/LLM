# Exact-source resolution and final review

## Final decision

**Do not run I001.v1 from the six selected final rMATS tables. Stop before event-effect access and fitting.** I agree with root's stop decision, for a stronger reason than the earlier documentation uncertainty: the exact3.2.1.beta source contains an explicit treatment-count-dependent row filter. The source also confirms that the original full-coordinate matching assumption was too strict for its deduplication identity. Correcting event identity does not remove the treatment filter or recover missing control/event measurements.

This is a data-admission failure, not a numerical negative for the odds-transfer hypothesis. No candidate accuracy, effect prevalence, MSE gain or failure against a rival has been measured. The no-novelty judgment remains independently supported by prior work. No v2 observed-intersection reframe, model matrix, calibration, Agent/core promotion or implementation repair is warranted for this unexecuted candidate.

## Exact source, identity and reading level

Read the curated original3.2.1.beta Python source slice and newly extracted shell entry points as text only. Source distribution SHA256 is6f5219967c2116170172cfdaba97c56fbfd2ea625c9c4451a7ee064f237b9146, bound in root/rmats_source_slice.json. Independently verified all12 original Python file hashes against that manifest. RNASeq-MATS.py:18 explicitly declares MATS_ver="v3.2.1.beta"; the count script declares3.2.1 at line38. Nothing from the package was imported or executed, and packaged test datasets/GTF were not read.

Exact acquired source URL and distribution size are preserved in the earlier rmats321_ascertainment_audit.md and root acquisition record. This report supersedes that report's *unresolved exact-source logic* status, while preserving its correct warning that a GTF-compatible observed intersection is not a complete fixed universe. No new HTTP request was made. Requested reviewer gpt-6-astra/high; runtime-effective model/effort unknown.

## 1. Event discovery and identity

RNASeq-MATS.py:452–461 passes both sample groups' SAMs to processGTF.SAMs.py. In that script, the GTF initializes gene/transcript/exon dictionaries at111–158. Read-derived novel transcripts are added, for example at425–464 and618–640. The original annotated transcripts remain available to the later event enumeration.

The SE enumeration at682–745 walks distinct exons and candidate flanks, then looks for an annotated-or-added transcript edge with the same upstream exon end and downstream exon start. At735 it explicitly does **not** require exact flanking exon extents. At736 the dedup key is chromosome + target exon start/end + upstream exon end + downstream exon start. It omits the upstream outer start and downstream outer end; it also omits gene ID and strand. Thus source-event identity is not the full six-coordinate tuple initially proposed. A conservative reference junction identity should include the target boundaries and both flanking junction boundaries, while separately verifying unambiguous gene/strand attribution. Global deduplication can make overlapping-gene identities problematic; an annotation-defined ambiguity exclusion would need to precede effects.

For an independently defined reference triple with an annotated skipping edge, the discovery logic has the required annotation edges without treatment reads. Nevertheless, read-derived additions can affect which full flank representation is retained for the dedup key. More importantly, discovery into ASEvents is not equivalent to retention in the final MATS table.

Root reported a reference-only full-coordinate audit:20,068 fixed annotated SEs/8,649 genes,6,990–8,412 present per archive,3,568 common. I did not read its event values. **Those absence counts must not be called counts of treatment-filter exclusions.** Full-coordinate mismatches, exon-graph representation, globally deduplicated identities and the subsequent count filter can all contribute. The source proves the existence of treatment-dependent selection; it does not identify the cause of each particular absent reference row.

## 2. Outer flanks and measured counts are not unconditionally interchangeable

For SE junction-count output, MATS.processsUnique.sam.py:309–310 computes effective inclusion/skipping lengths from target exon length, read length and anchor length, not from the outer flanks. The immediate SE junction predicates at864/871 (with corresponding first-/second-strand code at1392/1399 and1919/1926) also use target boundaries and the upstream-end/downstream-start junction identities. This supports junction-level biological identity and explains why arbitrary outer flank equality is unnecessary at that local predicate.

However, the same script registers each event into1000-base lookup groups using the **full** exon extents at317–337. Each read is looked up only using its alignment-start group at739,1246 or1773, and the SE predicates are evaluated only if the event is registered in that group. Therefore different outer extents can change which reads reach the predicate, especially near lookup-bin boundaries or for reads spanning multiple exons. The code comment that one group is sufficient does not prove representation invariance. An unconditional statement that identical junction keys imply identical counts/PSI would be unsupported. Equal lookup-group support plus equal target/junction coordinates and processing parameters would address this particular code path; simply discarding flank columns does not.

No real-read counterexample or simulation was executed. This is a source-level dependency finding. It is secondary to the independently decisive final-table filter.

## 3. The decisive count-dependent filter

RNASeq-MATS.py:492–497 builds the junction-count MATS input from all counted events. Its awk condition at496 retains a row only if all of the following hold (besides the header):

- sum(KD inclusion + KD skipping) >0;
- sum(control inclusion + control skipping) >0;
- inclusion counts are nonzero in at least one of KD/control;
- skipping counts are nonzero in at least one of KD/control;
- both effective form lengths are nonzero.

Thus even a fully reference-defined event can be omitted because KD has zero total observed counts. Also, when a control has only one isoform observed, the other isoform can be supplied by KD to make the event pass. These are explicit uses of treatment observations for table inclusion. No significance threshold is needed to create this selection.

A control-only requirement that both isoforms have positive control counts would make the two pooled-isoform clauses automatic, but it would not eliminate the requirement of positive KD coverage. Furthermore, controls for rows omitted by the final pipeline are absent from these final tables, so their eligibility cannot be established from the final tables alone. A missing row cannot be imputed as zero delta, zero counts, unchanged splicing or ineligible control coverage.

## 4. Downstream functions preserve the prefilter; they do not recover excluded rows

- MATS/rMATS.sh:35–45 calls check_input.py and dispatches to the replicate unpaired/paired or pooled program. check_input.py checks vector lengths and group type; it does not reconstruct any excluded event.
- For the expected two-replicate unpaired setting, rMATS_Unpaired.sh:15–24 creates Data.txt from the filtered input, computes inclusion levels, runs GLM_MS_unpaired.py, adds FDR and pastes the PSI fields. The path starts from the already filtered file.
- GLM_MS_unpaired.py:550–591 reads that input, marks some unusable per-replicate cases for the statistical model, and writes one output row for each input line. Its handling does not restore rows removed before invocation. No numeric optimization was run here.
- FDR.py:44–58 reads the provided p-value rows, computes adjusted values and writes the provided rows with FDR; it is not an annotation-universe completion step. inclusion_level.py computes PSI from those supplied counts and records NA for zero replicate totals.
- RNASeq-MATS.py:528–536 joins the statistical output to the full event-coordinate file. bin/joinFiles.py:64 onward loops over the **second file**, emitting only keys found in that statistical output. This is an intersection, not a left join that preserves every reference/discovered event. Sorting by p-value does not restore omitted events.

Consequently the six final SE.MATS.JunctionCountOnly.txt archives cannot provide the complete predeclared reference/control-only eligible universe required by the frozen candidate. Recovering an appropriate universe would need unfiltered event/count inputs or a separately justified raw-data preprocessing effort; neither is supplied by reinterpreting these final rows. This report does not authorize a new experiment or raw-data acquisition.

## 5. Final scientific boundaries

KATMAP's actual original publisher article is **encode/sources/katmap_publisher.html.hop3**. The base .html is a303 response; intermediate hop1/hop2 bodies are empty. Initial primary-source excerpts and prior-art conclusions used hop3, not the redirect body. Its paragraphs148–150 explicitly motivate log-odds inclusion changes by baseline dependence and bounds, while paragraphs58–59 describe cross-cell inverse SF-identification and an observed-inclusion-change comparator. These support an ordinary response-scale interpretation and reject a novelty claim; they do not establish the candidate's quantitative prediction performance.

The initial epsilon/null artifact, lack of explicit bounded ordinary rivals and incomplete numerical protocol remain issues to address before any future independently authorized protocol. They need no code repair now because this candidate did not run. Biological-input metadata remains substantially supported by the24 distinct registered origins, but separate samples do not imply independent batch errors. A single held-out RBP would in any event support only a small exploratory comparison, not external validation or an intervention-level generalization interval.

Final state: data contract not met; candidate not admitted; no response-value inspection by this reviewer, no numerical execution, no fitted result, no promotion. Root reports no response values/fitting anywhere in the pilot; that is a root-owned execution audit statement, not something this reviewer inferred from results.
