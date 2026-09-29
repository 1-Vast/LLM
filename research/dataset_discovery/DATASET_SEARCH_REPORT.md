# Dataset search report: resolving MAESTRO's data limitations

> **File summary**
> - **Path**: `research/dataset_discovery/DATASET_SEARCH_REPORT.md`
> - **Purpose**: the source-backed dataset discovery and qualification record for the framework's
>   current data limitations, corrected per `REVIEW.md` (2026-09-29).
> - **Core points**: qualification is reported on separate dimensions (availability, license,
>   design, identity/overlap, preprocessing readiness, task eligibility); a source can pass
>   availability and fail task eligibility. Current contracts are `SCIENTIFIC_REPAIR_V3.md`;
>   the earlier 54/11 five-outcome estimator diagnostic is history, not current state.
> - **Interfaces / data**: `dataset_inventory.json`, `source_checks.json`, `ACQUISITION_PLAN.md`,
>   `tahoe_drug_metadata_inspection.csv` (archived API sample).
> - **Depends on**: `REVIEW.md`, `research/case_memory_integration/SCIENTIFIC_REPAIR_V3.md`.

- **Search date**: 2026-09-29; corrected 2026-09-29 per `REVIEW.md`. **Scope**: discovery and
  qualification only. No models were trained, no forecasting parameters tuned, no production code
  changed, no performance claim made.

## 1. What the data must fix (current contracts)

From `SCIENTIFIC_REPAIR_V3.md` (current) and the historical development diagnostic (54 training /
11 held-out compounds, 156 forecast items; the 156 items are **not** independent units - the
held-out set is 11 compounds):

1. Too few independent compounds and sparse conditional support.
2. Proxy-only labels (curated MoA, derived similarity); no typed orthogonal evidence.
3. No attempted-experiment denominator: failure, missingness and low-signal data.
4. No clean pre-action state -> candidate action -> future outcome examples; population controls
   are not personalized pre-action trajectories.
5. Decision benchmarks without at least two measured, comparable, eligible actions.
6. The estimand split: `P(readout | valid measurement, ...)` vs
   `P(outcome | attempted experiment, ...)` - the second needs a verified denominator.
7. No independent calibration population and no verified untouched evaluation population.

## 2. Method

Local exposure was established from repository manifests and provenance files (GSE92742,
GSE70138, LINCS 2020, sciPlex3, PRISM 19Q4, DepMap 24Q2, arc_state/State). Candidates were traced
from primary publications' Data Availability statements to accession records, dataset cards and
file-level links; metadata and small API samples were inspected where possible (all checks and
access outcomes in `source_checks.json`). No large expression matrix was downloaded during
screening. Compound overlap was computed at the InChIKey connectivity-block level where
structures were available (Tahoe: 379 drugs via the Hugging Face datasets-server API, archived in
`tahoe_drug_metadata_inspection.csv`). Qualification is reported per dimension; this report does
not promote source availability into task eligibility.

## 3. Candidates by role

### Role A - population response prediction

| Candidate | Controls | Action | Outcome | Verdict |
|---|---|---|---|---|
| sciPlex2 (GSM4150377) | vehicle (zero-dose tokens present in the official sample sheet) | 4 compounds (BMS345541, dexamethasone, nutlin-3A, SAHA) x 8 dose tokens incl. zero | single-cell response, 24 h | **Qualified as a small dose-response contract pilot** (development only) |
| sciPlex3 (GSM4150378, LOCAL) | vehicle | 188 compounds x 4 doses | single-cell response, 24 h | Already development data; reuse locally, no duplicate download |
| sciPlex4 (GSM4150379) | DMSO tokens | chemical/metabolic combinations (abexinostat/pracinostat x acetyl-CoA precursors/enzyme inhibitors), A549/MCF7 | single-cell response | **Qualified as a chemical/metabolic rescue case pilot** (development only) |
| sciPlex1 (GSM4150376) | untreated | none (species-mixing barnyard) | none | **Not a perturbation-response source** |
| Tahoe-100M | DMSO_TF plate-matched | compounds (single time point) | single-cell response in 50 lines | **Qualified only for a stated development/calibration task with overlap declared** (see section 4) |

Corrections applied (REVIEW P1): sciPlex2 contains four drugs, not the sciPlex3 188-compound
library; the 188-compound screen is sciPlex3, already local; sciPlex4 is chemical/metabolic
rescue, not a genetic rescue experiment; a factorial treatment design does not provide a recorded
sequential decision history. Destructive 24 h samples are not same-cell trajectories; Tahoe's
cell-village pools share conditioned medium (publication limitation).

### Role B - probability calibration

| Candidate | Independent grouping | What it can calibrate | Verdict |
|---|---|---|---|
| Replogle 2022 (genetic) | target gene (grouping key, NOT a replicate count; gemgroup lanes are not automatically biological replicates) | a separately specified **genetic perturbation** benchmark only | **Qualified for a genetic task; NOT eligible for small-molecule outcome calibration** until a domain bridge is defined |
| Tahoe-100M | compound block x cell line (coverage not yet counted) | case-memory/planner calibration with overlap declared; never VC evaluation with the exposed checkpoint | **Qualified with restriction** |
| sci-Plex family | compound (188 shared library, 4 in sciPlex2) | small-population development calibration | **Qualified at small unit count** |

Target-gene count is not biological replicate count (REVIEW P1). Genetic outcomes do not
directly calibrate small-molecule outcome probabilities. Chemical identity overlap is not
applicable to a genetic dataset; checkpoint-specific training exposure for Replogle remains
**not established** (source-code examples mentioning a dataset do not prove checkpoint use).

### Role C - restricted measured-action replay

| Candidate | Measured alternatives | Caveats | Verdict |
|---|---|---|---|
| sciPlex2 | 8 dose tokens incl. zero per compound | a dose menu does not establish which outcome confirms a mechanism, utilities, failure probabilities, or temporal availability of baseline information (REVIEW P1) | **Eligible only after endpoint, utility, eligible-action and abstention rules are registered; development-only** |
| cpg0004-lincs (JUMP) | 6 doses per compound in A549 | full dose matrix measured; morphology endpoint | Candidate, deferred behind the sci-Plex pilot |
| MIX-Seq | hashing multiplexes doses/time points | observational within pools; selection bias documented | Candidate with caveat |

No unmeasured action's outcome is claimed. A common vehicle population is a population-level
control, not a same-cell or personalized pre-action state; state-aware gains over a few cell
lines may encode cell identity and must be compared against matched cell/assay/dose frequencies.

### Role D - orthogonal mechanism evidence

| Candidate | Layers connected | What it is NOT | Verdict |
|---|---|---|---|
| sciPlex4 | chemical/metabolic rescue: HDAC inhibitors x acetyl-CoA precursor/enzyme-inhibitor supplementation | not a genetic rescue; not a gene-specific rescue truth; not engagement | **Qualified as a typed chemical/metabolic rescue task** |
| Replogle 2022 | genetic knockdown -> molecular response | not drug binding; not small-molecule calibration | **Qualified for the genetic task only** |
| MIX-Seq | transcriptional response + externally linked drug sensitivity | `sens = 1 - AUC_avg` is averaged from quantile-normalized PRISM/GDSC values (source README, REVIEW P2) - **external linkage, not same-experiment viability follow-up** | **Qualified with linkage provenance recorded** |
| JUMP cpg0000 pilot | chemical + CRISPR on matched genes -> morphology | morphology is not engagement | Candidate, deferred |
| PRISM 19Q4 (local) | compound x line -> viability | viability is not a transcriptomic truth | In use locally; overlap declared |

### Role E - measurement validity (pending)

| Candidate | What is verified | What is not | Verdict |
|---|---|---|---|
| LINCS instance metadata | phase I/II inst_info archives are local; LINCS2020 instinfo_beta.txt exists (675 MB, HTTP 200, 2022-03-02) | **the local phase I/II inst_info headers contain neither `qc_pass` nor `distil` fields** (header inspection, REVIEW P1); HTTP availability does not establish inclusion of every attempted experiment; the actual QC tables, linkage keys, processing stages, exclusions and unmatched records are unidentified | **Pending: candidate denominator only; `sampling_frame=unspecified` until the completeness audit** |

A possible estimand is `P(QC pass | an instance reached the deposited assay stage)`; this is not
automatically `P(valid outcome | experiment attempted)`. Any new quality-data use requires its
own documented protocol; the earlier frozen protocol is preserved. Datasets containing only
successfully processed measurements cannot directly estimate the probability of obtaining a
valid experiment.

## 4. Overlap audit (per candidate, per component)

- **Verified overlap**: sci-Plex family (sciPlex3 is local development data; sciPlex2/4 share the
  repurposing library lineage); Tahoe-100M (185/374 blocks in GSE92742/GSE70138; **State
  checkpoint training data** per public documentation and local `data/external/arc_state/tahoe_var.json`);
  MIX-Seq compounds and its PRISM/GDSC sensitivity linkage; cpg0004-lincs (the LINCS
  1,571-compound set); PRISM 19Q4 (in use); LINCS instance metadata (same studies).
- **Not applicable / not established**: Replogle (genetic dataset - chemical identity overlap is
  not applicable; checkpoint training exposure is **not established** and requires a
  checkpoint-specific manifest, not source-code examples).
- **Unknown / not auditable**: GSE306429 (GEO access returned HTTP 200 without the expected
  record fields in this environment - status code alone did not resolve the failure).
- Tahoe specifics (REVIEW P2): 374 blocks x 50 lines is a possible condition grid, not 18,700
  independent compounds; the 189 blocks absent from two GSE sources are not automatically absent
  from PRISM, sciPlex3, other local sources or model pretraining; the two unparsed drugs
  (Sacubitril/Valsartan, Verteporfin) remain unknown, not cleanly unseen. "Permanently excluded
  from all virtual-cell evaluation" is too broad: overlap-declared diagnostics and evaluation of
  a separately trained nonoverlapping model are different claims. Any component consuming a
  pretrained model's embeddings or predictions inherits the relevant exposure; a per-component
  dependency/exposure ledger is required (`ACQUISITION_PLAN.md` section 5).

## 5. Rejected or deferred

cpg0016-jump (250 TB, burden); Norman 2019 (small, archived, combination design is a later task
family); Frangieh Perturb-CITE-seq (immune context, few perturbations); local GDSC (uncited);
kinome_gxe (forbidden lysate format); Tahoe-100M for evaluation of the Tahoe-trained checkpoint;
third-party curated derivatives as sources of record (mixed-license releases); sciPlex1
(untreated barnyard - not a perturbation-response source).

## 6. What remains unverified

sciPlex2/4 replication structure beyond the hash sample sheets (six hash rows per agent-dose
group do not establish six independent biological replicates); MIX-Seq per-experiment counts;
GSE306429 files and publication; LINCS QC table identity, join keys and completeness; Tahoe
observed condition coverage (compound x line grid fill); PRISM releases newer than 19Q4 (403).
Scoped statement (REVIEW P2): these are the limits of what this search verified among the
candidates reviewed for the current checkpoints and claims - not universal claims about all
public data.

## References

- [sci-Plex processing README and accession table (cole-trapnell-lab/sci-plex)](https://github.com/cole-trapnell-lab/sci-plex/blob/master/README.md)
- [sciPlex2 record (GSM4150377)](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4150377) and [official hash sample sheet](https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150377/suppl/GSM4150377_sciPlex2_hashSampleSheet.txt.gz)
- [sciPlex4 record (GSM4150379)](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4150379) and [official hash sample sheet](https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150379/suppl/GSM4150379_sciPlex4_hashSampleSheet.txt.gz)
- [scPerturb harmonized release (Zenodo 13350497, CC BY 4.0)](https://zenodo.org/api/records/13350497)
- [Tahoe-100M publication (Cell, S0092-8674(26)01008-1)](https://www.cell.com/cell/fulltext/S0092-8674(26)01008-1) and [dataset card](https://huggingface.co/datasets/tahoebio/Tahoe-100M)
- [Replogle et al. 2022 processed Perturb-seq datasets (figshare 20029387)](https://api.figshare.com/v2/articles/20029387) and [portal](https://gwps.wi.mit.edu/)
- [MIX-Seq publication (PMC7453022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7453022/), [data (figshare 10298696)](https://figshare.com/articles/dataset/MIX-seq_data/10298696), [source README](https://ndownloader.figshare.com/files/24848579)
- [Cell Painting Gallery README (AWS RODA, CC0)](https://github.com/broadinstitute/cellpainting-gallery)
- [GSE306429 (GEO series, unqualified)](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE306429)
