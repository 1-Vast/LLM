# Independent commit-pinned source addendum

2026-10-23. After first independent seal, read root-provided source at commit b654a45faf5a80cdb1b514188cc90af8c9565b85: README; mechanistic preparing-inputs/utils; active-learning optimization/utils; three data metadata files. Still no current-phase peer opinion, numerical assay table, saved fit outcome, external request or computation. Original INDEPENDENT.md remains unchanged.

## Source details that change feasibility

1. **The original raw assay does expose a possible passage/screen split.** Metadata identifies BxPC3 E3CA P12 / E3CB P14 and AsPC1 E3DA P12 / E3DB P14. This is stronger than an undifferentiated duplicate label and may allow a narrow later-passage prediction check. It does not by itself authenticate separate dates, full biological independence or four improvement tasks. Do not describe every repetition as same-culture technical duplicate. The preparation code further renames Sample1/2 into A1/A2 and B1/B2, so screen and within-screen sample identity could potentially be retained, subject to table schema audit.

2. **Bead events are not independent experiments.** Metadata explicitly says each raw row is a FACS measurement; code groups events into condition/sample arithmetic MFI. Row count must not become task/sample-size count for generalization uncertainty. The exact well/sample provenance still needs verification.

3. **Preprocessing is more outcome-coupled than a simple fixed min/max map.** The preparation script pools the two source screens before estimating IQR trimming per cytokine×inhibitor, then computes log10(arithmetic MFI) and range scaling separately for each sample across its full condition screen. A lawful held-out-passage or sparse-assay protocol must prevent hidden conditions/passages from determining trimming and scaling constants. It may use declared fixed controls/source-only transforms or honestly accept retrospective full-screen-conditioned scope. Raw values appear potentially available by named file paths, but no payload was inspected here.

4. **The checked AL executable uses synthetic feedback unconditionally.** It loads synthetic_data/CXCL9_values_AsPC1.csv; after selecting a condition it obtains synthetic_mean and writes that as final-time training output. The nearby comment says to use experimental value if available, but no conditional experimental-read branch is present in the checked path. Therefore running this file unchanged is not replay of actual wet-lab feedback. This does not contradict the paper's separate wet-lab AL rounds, which have AL1A/B and AL2A/B metadata. Those labels support two actual round identifiers per line, not proof that the default script is their exact executable replay.

5. **Intermediate state labels are not supplied by inserted MIDAS rows.** The script writes initial non-CXCL9 states .5, initial CXCL9 zero, intermediate observed columns NA, and final CXCL9 synthetic_mean. These are initial conditions and missing labels, not measured multi-time cellular states. A declared dynamic claim cannot cite the number of MIDAS time rows as measured trajectory supervision.

6. **Published active acquisition uncertainty is a t-interval over optimizer ensemble outputs.** calculate_CI calls t.test across predictions from optimization runs. It is not directly a calibrated assay-level predictive interval. Duplicating optimizer seeds could shrink this mean interval without adding experimental information; changing optimizer count requires matched treatment of acquisition definitions. This is a control/reproduction issue, not a claimed new method.

7. **Task metadata now provides a concrete small inventory, not an RSI corpus.** Initial training counts are 10 or24; candidate counts are 73+(24−10) or73. The 73 count includes unseen inhibitor conditions by the metadata statement, but exact drug/combination families are not yet authenticated here. RandomX masks are alternative initializations of one underlying problem. They can benchmark robustness, not count as independent later research tasks.

## Updated decision

Retain REVISE / source-feasibility only. The passage identifiers justify checking a narrow prospective-style source passage→later passage calibration contract, if raw assay provenance and fixed normalization permit it. This remains ordinary restricted calibration research until a distinct update operation and strong-baseline failure are specified. No biological effect, new-core claim, dynamic necessity, inheritance or improved-improver gain has been established.
