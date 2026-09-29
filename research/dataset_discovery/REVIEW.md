# Review of dataset discovery and qualification

Review date: 2026-09-29. Scope: source and qualification audit only; no model, preprocessing code,
frozen protocol, large matrix or quality-label changes. The original inventory and acquisition
plan are preserved for the data agent to revise against these findings.

## Verdict

Accept the deliverables as a useful candidate-discovery register. Do not accept them yet as a
scientifically qualified acquisition/construction plan. Several facts affecting the first
download priority are incorrect, and access verification is repeatedly promoted into eligibility
for a scientific task. Source availability, design verification, model overlap, preprocessing
readiness and claim eligibility need separate statuses.

## Confirmed checks

- All five originally delivered files exist. Both JSON files parse.
- `python -m pytest tests/test_repository_shape.py -q -o addopts=`: **10 passed**.
  These are repository tests, not scientific qualification tests. The directory is currently
  untracked; the Markdown language test enumerates `git ls-files`, so that particular test did
  not inspect these new Markdown documents.
- Tahoe CSV reproduction: 379 rows, 377 structures parsed, 374 distinct InChIKey connectivity
  blocks; 185 overlap the local GSE92742/GSE70138 development block union and 189 do not.
  Unparsed entries: Sacubitril/Valsartan and Verteporfin. `moa-fine` is `unclear` for 199 rows.
  These results do not establish 18,700 independent units, full cell-line coverage or novel
  structural scaffolds. Nor do they establish absence from every other local source.
- Figshare API confirms Replogle article 20029387 and MIX-seq article 10298696, both CC BY 4.0.
- Zenodo record 13350497 exposes separate sciPlex2/3/4 files. sciPlex2 is 145,178,504 bytes,
  sciPlex4 253,335,945 bytes. This is more precise than the plan's generic GB-class estimate.

## Findings requiring correction

### 1. P1: sciPlex2/4 are not an extension with 188 shared compounds

Affected: `ACQUISITION_PLAN.md` rank 1 and section 6; `dataset_inventory.json` sci-Plex design,
units and overlap; matching report claims.

GEO GSM4150377 describes sciPlex2 as four compounds: BMS345541, dexamethasone, nutlin-3A and SAHA,
plus vehicle. GSM4150376 is an untreated human/mouse barnyard experiment. The 188-compound,
four-dose large screen belongs to GSM4150378, sciPlex3, already local. Thus the proposed first
subset cannot be budgeted as 188 new independent compounds or assumed to have sciPlex3's exact
dose design. Recompute counts from each accession's sample sheet instead of inheriting them from
the umbrella publication.

The official sciPlex2 hash sample sheet (1,694 compressed bytes) has 192 rows, four agent tokens
and eight dose tokens including zero: 32 agent-dose groups with six rows each. Six hash-sheet
rows do not establish six independent biological replicates; units need separate verification.
[Official sample sheet](https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150377/suppl/GSM4150377_sciPlex2_hashSampleSheet.txt.gz).

Primary records:
[sciPlex1](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4150376),
[sciPlex2](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4150377),
[sciPlex3](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4150378).

### 2. P1: sciPlex4 rescue is chemical/metabolic, not genetic

Affected: `dataset_inventory.json:32`, report Role D, acquisition plan's rescue constructs and
follow-up episode assumptions.

GSM4150379 describes abexinostat/pracinostat treatment "with or without supplementation of
acetyl-CoA precursors or inhibitors to enzymes that serve to generate acetyl-CoA." This does
not describe a genetic rescue construct. It can support a typed chemical/metabolic rescue task;
it does not supply a gene-specific rescue ground truth. A factorial experiment also does not
automatically provide a sequential decision history.

Primary record: [sciPlex4](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4150379).

Its official hash sample sheet (5,922 compressed bytes) has 624 rows and A549/MCF7 contexts.
First-treatment tokens are ACLY.inhibitor, ACSS2.inhibitor, Acetate, Chloride, Citrate, DMSO,
PDH.inhibitor and Pyruvate; second-treatment tokens are Abexinostat, DMSO and Pracinostat.
There are 206 raw token combinations of treatments/doses/cell, before collapsing equivalent
zero-dose conditions; these are not independent compounds.
[Official sample sheet](https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4150nnn/GSM4150379/suppl/GSM4150379_sciPlex4_hashSampleSheet.txt.gz).

### 3. P1: complete LINCS attempted-experiment denominator is unverified

Affected: report Role E; acquisition plan failure-modeling eligibility; inventory LINCS contents.

The recorded LINCS2020 check was HTTP HEAD. That establishes availability and size, not column
semantics or inclusion of failed attempts. Header-only inspection of the existing local phase I
and phase II `inst_info` archives finds neither `qc_pass` nor `distil` fields. No LINCS2020
quality values were opened in this review.

Phase I header: `inst_id, rna_plate, rna_well, pert_id, pert_iname, pert_type, pert_dose,
pert_dose_unit, pert_time, pert_time_unit, cell_id`.

Phase II header: `inst_id, cell_id, det_plate, det_well, pert_mfc_id, pert_dose, pert_dose_unit,
pert_id, pert_iname, pert_type, pert_time, pert_time_unit`.

Find the appropriate QC source, define its join key and processing stage, quantify unmatched
instances, and establish whether failures before expression measurement are present. A possible
estimand is `P(QC pass | an instance reached the deposited assay stage)`; this is not automatically
`P(valid outcome | experiment attempted)`. Until proven otherwise use `sampling_frame=unspecified`,
and mark Role E conditional/pending. Any new quality-data use needs its own documented protocol;
do not rewrite the earlier frozen protocol.

### 4. P1: a large genetic perturbation count does not qualify drug-outcome calibration

Affected: Replogle Role B and "no overlap found" rationale.

Target-gene identity is a useful split/grouping key, not a declaration of independent biological
replication. Shared guides, plates, controls and pathways induce dependencies; gemgroup lanes
must not automatically be called biological replicates. Assess the raw pseudobulk's grouping and
control structure before inferring effective support.

CRISPRi response can support a genetic perturbation benchmark and an orthogonal evidence layer.
It cannot directly calibrate small-molecule mechanism-conditional probabilities simply because
there are many target genes. Define the readout, labels, conditioning variables and domain bridge.
Chemical identity overlap is **not applicable** for a genetic dataset; foundation-model training
overlap remains **not established**, not "none found" based on absence of compounds. Local State
source examples mention Replogle, but examples alone do not prove use by the active checkpoint.
Require checkpoint-specific training/validation manifests before any clean-evaluation claim.

Source: [Replogle file manifest](https://api.figshare.com/v2/articles/20029387).

### 5. P1: dose menus do not yet establish decision value or state information gain

Affected: the first-subset scientific claims and "genuine policy replay possible" wording.

Four measured doses can define a menu if their conditions are actually covered. They do not
establish which outcome confirms a mechanism, the action utility, failure probability or temporal
availability of baseline information. A common vehicle population is a population-level control,
not a patient-specific or same-cell pre-action trajectory. If state varies only across a few cell
lines, state-aware gains may simply encode cell identity. Compare against matched cell/assay/dose
frequencies and stratify evaluation accordingly.

First qualify descriptive population response and restricted measured-menu replay. Add mechanism
decision claims only after observed labels, interpretation rules, costs, eligible actions,
abstention and genuinely available pre-action features are specified. No observed menu permits
claims about unmeasured alternatives without additional assumptions.

### 6. P2: MIX-seq viability linkage is external, not same-experiment follow-up

The source README says `sens = 1-AUC_avg`, with AUC averaged from quantile-normalized PRISM and
GDSC values where available. Record this linkage and any overlap with the local PRISM history.
The expression-to-viability bridge may still be useful, but cannot be described as a newly measured
paired viability endpoint in the MIX-seq experiment. Audit compound, cell, dose and assay-time
alignment and normalization scope before scoring.

Primary [README](https://ndownloader.figshare.com/files/24848579), from
[article 10298696](https://api.figshare.com/v2/articles/10298696).

### 7. P2: units and overlap need task-specific definitions

Tahoe's 374 blocks times 50 lines is a possible condition grid, not 18,700 independent compounds;
coverage has not been counted. A benchmark for novel compounds needs compound-level grouping and
uncertainty, with plate/cell dependence addressed where relevant. The two unparsed drugs remain
unknown, not cleanly unseen. The 189 blocks absent from two GSE sources are not automatically new
to PRISM, sciPlex3, model pretraining or the full MAESTRO development history.

Tahoe must not support an untouched external claim for a checkpoint trained on Tahoe. "Permanently
excluded from all virtual-cell evaluation" is too broad: overlap-declared diagnostics and evaluation
of a separately trained nonoverlapping model are different claims. A planner that consumes State
embeddings/predictions is not independent of that training exposure merely because it is called
a non-VC component. Require a per-component dependency/exposure ledger.

### 8. P2: absence of evidence is written as universal impossibility

Replace "no public dataset provides" and "every large atlas is development or State training"
with "not verified among the candidates reviewed for the current checkpoints and claim".
GSE306429 remains unqualified. This review received an HTTP 200 response without expected GEO
record fields, so the status code alone did not resolve the prior access failure.

### 9. P2: qualification should target the current version-3 contracts

The discovery report still presents the earlier 54/11, five-outcome estimator diagnostic as current.
Keep those measurements as history and reference `SCIENTIFIC_REPAIR_V3.md` for current requirements.
Before construction, provide explicit source/derived/unavailable mappings for `value_kind`,
`biological_replicate_id`, `availability`, `sampling_frame`, laboratory, action context,
`conditioning_hypothesis`, `contrast`, `label_kind` and outcome status. Do not fill unavailable
fields with optimistic defaults, infer mechanistic hypothesis truth from treatment assignment,
or allow a declared all-attempts flag to replace a denominator audit.

## Revised priority and acceptance criteria

1. Keep sciPlex2/4 as small, inexpensive contract pilots: dose response and metabolic rescue.
   Count distinct compounds, doses, cells, plates, controls and replication from metadata first.
2. Screen Replogle pseudobulk metadata for a **separate genetic task**, with no drug-calibration
   eligibility until the bridge is defined. Actual file capitalization is `K562_gwps_*`.
3. Use Tahoe metadata to build an observed coverage table and checkpoint/component exposure
   ledger. Select a subset only for a stated development/calibration task with the overlap declared.
4. Treat LINCS as a QC-denominator candidate until the processing-stage and completeness audit
   succeeds. Discovery metadata does not itself qualify a prospective failure model.
5. Retain MIX-seq/JUMP as orthogonal readout candidates with source-level linkage audits. There
   is currently no approved untouched confirmatory dataset in this register.

For each role, deliver: exact files and license, metadata census, grouping/split unit, biological
replication, source-to-contract mapping, lineage and component overlap, permitted claims, unresolved
blockers, and a small construction-ready example. A dataset may pass file availability and fail
scientific eligibility. Repair the report, inventory, source checks and acquisition plan consistently;
do not change model code or the frozen evaluation to make a dataset appear eligible.
