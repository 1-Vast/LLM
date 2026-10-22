# Primary narrative review and corrected table targeting

2026-10-22. Root used the predeclared `LITERATURE_SCOPE.md` to project the retained
article, without HTTP or workbook measurements. Read the abstracts, twelve
figure captions, relevant Results paragraphs about non-monochromaticity,
tetracycline trajectories and genomic mechanisms, and Discussion limitations.
The initial full JSON terminal view was truncated; subsequent targeted views
covered those relevant paragraphs. This is not a claim of reading every line
of the complete article. Published numerical and qualitative outcomes in these
fields are explicitly literature/design-exposed, not our validation data.

The original contribution already includes a chemical-genetics metric for
cross-resistance/collateral sensitivity, experimental validation, prediction of
mixed lineage responses and a mechanism account of changing TET/AZI responses.
Figure 5 is explicitly titled "Chemical genetics recapitulate the dynamics and
explain the mechanisms of non-monochromatic interactions." It describes twelve
tetracycline-selected lineages, TET and AZI readouts at days 2, 3, 5, 7 and 10,
and mutation observations at days 3, 5 and 7. Results text says susceptibility
was measured at each of ten passages; this is not proof the public workbook
contains every passage. The source-data object to qualify is therefore
**Source Data Fig5 / MOESM9**, not Fig4 (drug-class summaries) or Fig3 alone.

Published hldE/waaD, waaF, marR, ompF and target-gene explanations are prior
work. A method may still make new prospective quantitative predictions, but
merely explaining these known lineages or adding a conventional forward
selection equation is not a new discovery. The authors themselves discuss
limitations of loss-of-function screens for gain-of-function, essential-gene
mutations and epistasis.

Unresolved source descriptions are retained: Methods describes sequencing a
clone from the wild type and from lineage populations; Results and Fig5/ED5
describe population sequencing/variant trajectories. Do not assume phased
haplotypes, single-cell states or clone/population equivalence without the
actual sample/assay provenance. Methods says fourteen pairs for extended
evolution, whereas ED2 caption says seventeen; source-table identities must
resolve the relevant menu rather than silently selecting one count.

The projection contains repeated figure-caption text because enclosing Results
paragraphs also include figures in the JATS tree. The caption's separate entry
is not independent evidence. No count/statistical analysis relies on this
duplication; the first projection is preserved rather than overwritten.

Local workflow failures: root attempted to read a protocol just before its
agent finished writing it, then later attempted premature report reads and one
guessed `WORKBOOK_STRUCTURE.json` name. These PowerShell reads failed without
source or code modification; actual reports use `STRUCTURE_AND_LABELS.json`.
They are workflow timing/name errors, not evidence of unavailable data.
