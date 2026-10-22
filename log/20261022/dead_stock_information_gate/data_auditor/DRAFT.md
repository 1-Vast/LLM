# Independent export audit: HCT116 live/dead readouts

2026-10-22. Saved before reading other current-stage drafts. No CSV, numerical count array or rendered figure has been opened by this auditor. Reused the prior primary article and exact manifests without modifying old evidence. Two new GETs, both exact small source blobs, both 200 and Git-SHA1 verified; the four-request maximum is not a target. The code was read statically, not executed.

**Qualification: proceed with a narrow relative-time, per-well image-readout forecast. Do not treat export names as validated birth/death events, absolute whole-well cells, independent runs or separate CSV files as independent experiments.** The unresolved export details constrain interpretation but do not automatically block a measured prefix→later-readout experiment.

## What the source authenticates

The prior BESTDR primary describes HCT116 p53-VKI cells in 96-well plates, cisplatin added 24 h after seeding, imaging every 4 h for 72 h after treatment, GFP+ segmentation as total cells and GFP+RFP+ segmentation as dead cells. The count replicate experiment uses three image regions per well. These are segmented fluorescent object readouts; a dead-object stock is not cumulative death-event count. The paper does not state that three regions are independent biological replicates or nonoverlapping full-well coverage.

The Figshare v1 manifest, DOI 10.6084/m9.figshare.29610530.v1, authenticates two exact files:

| File | Bytes | MD5 |
| --- | ---: | --- |
| HCT116_Cisplatin_Replicates.csv | 295,392 | ae55aacf1f6549b04471f9d9d68e6cfe |
| HCT116_Cisplatin_DoseResponse.csv | 392,663 | 010489434a9e563f4f23afa304c70aca |

The complete saved author-package tree has SHA 03753e15c789bee671ff39dfe8c6cbc50e5967e5, truncated=false. It has no HCT116/cisplatin/seed/export-named path. That filename search does not prove no relevant content exists anywhere in the package. Two exact relevant blobs were examined:

- R/attach_data.R: 2,952 bytes, Git blob c5ab7381a72f3a7e105e50548bf73e7814dcbf4d.
- README.md: 2,668 bytes, Git blob 1aec8f0bdefb61924a156c662dcd1c2996031b6f.

`attach_data` accepts user-specified `time_var` (default `dt`), `count_vars`, `prevcount_vars`, `predictor_vars` and optional `hierarchical_group`. It copies already constructed current/previous count fields into a Stan input list; it does not derive viable from total/dead, create lag pairs, interpret Elapsed, map seed/img, aggregate images or define an experimental replicate. README describes the generic branching-process modeling package and supplies no HCT116 export dictionary. A redundant Rd read would not resolve source-specific semantics, so the remaining two GETs are not spent.

## Field claims that remain unverified

The candidate CSV labels `intersect_live`, `intersect_dead`, `seed`, `img` and `Elapsed` were supplied in the parent task. This auditor has not opened those CSV headers or values. Neither examined code file establishes whether intersect_live equals GFP total minus double-positive dead, whether seed is a density, plate, file or run label, whether img regions overlap, or which acquisition epoch Elapsed zero represents. The primary's nominal treatment schedule does not by itself map every CSV Elapsed value to hours after dosing. Do not certify that mapping from the column name.

It is nevertheless defensible to define the measured live-labeled and dead-labeled exported channels operationally and predict their later values on the same relative acquisition-time scale. Keep seed as an opaque categorical context and include its identity in trajectory grouping; do not assign a biological meaning or extrapolate numerical seed values as density. An independent event-count/lineage or calibrated total→viable transformation would be needed for stronger biological rate claims, not for every readout forecast.

## Pre-numeric aggregation and split recommendations

Use `(source file, seed label, well identity, concentration)` as a conservative trajectory identity until a better authenticated key exists. Establish and preserve exact raw key duplicates from identity fields before numerical fitting. Keep every time and image of one well in one partition. Images are correlated observations of a well, not separate tasks.

Fix a simple equal-weight arithmetic mean across the same image panel at every well/time for both measured channels. Report per-image mean segmented objects, not absolute full-well cells. This does not require proving image nonoverlap; overlapping regions affect the meaning and dependence of the readout, not the validity of forecasting that fixed readout. Preserve image counts and missingness. Prefer a panel selected from identity/presence only, independent of channel values; do not let favorable future measurements decide which images are averaged. If a varying available-image mean is used instead, freeze it and feed identical counts/missingness/context to both model arms.

Define relative time as Elapsed minus the first authorized acquisition time for the trajectory or a common file epoch authenticated from identities. Predefine the epoch and prefix boundary once. Do not claim that zero is drug administration if it is unverified. Splitting must use whole wells and a fixed concentration/context scheme; no train/test split by timepoint or image and no context-composition difference between live-only and live+dead arms. All scaling/normalization and imputation are fit on training data or a trajectory's permitted prefix only.

**Cross-file reuse warning:** the primary dose-response paragraph explicitly says it includes data from the previous experiment at 0 and 12 μmol/L; the methods list 12.5 μmol/L as the corresponding treatment dose. The exact source relationship is not established by filenames, and numerical duplicates were not checked here. Therefore Replicates.csv and DoseResponse.csv must not automatically become independent train and test runs. The simplest initial gate uses the replicate file alone; the dose-response object can be reserved for named nonoverlapping-dose exploration or included only with an explicit reuse audit. Keep the paper's 12-versus-12.5 wording rather than silently rewriting the source.

With matched well-level splits, fixed prefix and common context, the honest contrast is incremental predictive value of the early dead-labeled stock for later live-labeled readout. Strong multivariate direct predictors and ordinary stock-state inference are mandatory. A joint live/dead loss win without live-target gain does not pass the stated application. Neither an extra-channel gain nor a well-held-out result is a novel agent/update mechanism or confirmed cross-run inheritance.

## Decision and record limits

Proceed to a parent-frozen numerical exploratory gate if its identity audit establishes coherent well/image/time trajectories. Unknown seed meaning, image overlap and drug-time zero are interpretation limits, not universal stop rules for that narrower gate. Stop or narrow a biological-viable-cell interpretation if no source evidence distinguishes total from viable; do not force an unverified subtraction. If field values are true total rather than live counts, name the target exactly as exported and do not silently call it live functional survival.

No new source is nominated, no array is opened and no architecture is promoted. Source receipts retain complete received JSON bodies, decoded code and before/after prior-evidence hashes. Current qualification is positive for operational readout forecasting and unresolved for semantic mechanistic claims. This independent draft can now be crossed with the advocate on fair aggregation and test estimand.
