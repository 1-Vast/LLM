# Provenance audit of `bridge_transcriptome_viability.csv`

Date: 2026-10-30 (Asia/Shanghai)

## Decision

The 684-row file is a derived cross-assay bridge, not a matched transcriptomic-proxy and independent-function matrix collected under the same conditions. It may support descriptive association or an ordinary predictive baseline in development data already exposed to the analysis. It is not eligible for I304/R2 functional feedback, error-layer localization, equal-budget experiment savings, or mechanism validation.

## Reproducible fields

- File: `data/processed/maestro_vc_v1/bridge_transcriptome_viability.csv`.
- 684 records plus header; SHA-256 `dd44e96674dd85a6a048c9d96ca59cd616915552a0eb7ba5e188d0eced7ebd09`, matching `data/manifests/maestro_vc_v1_manifest.json`.
- Dataset counts: SciPlex3 219 rows and L1000 465; cell backgrounds A549, MCF7, and PC3; 296 compounds; PRISM screens HTS002, MTS006, and MTS010.
- Every `unit_id` encodes `24h|10000nM`, describing the transcriptomic condition key only. The bridge has no PRISM exposure time, vehicle, assay plate, culture preparation, or independent-replicate identity.
- `block` is a structure/drug-batch join key, not an independent culture or replicate identifier.

## Source semantics

SciPlex3 and L1000 are distinct transcriptomic resources. The project manifest marks the SciPlex3 raw file missing; `data/external/sciplex_family` is empty. The referenced prepared condition tables under `outputs/dynamic_world_model_20260926/` and `outputs/sequence_audit_20260926/` are also absent, so source samples, vehicles, plates, and biological preparations cannot be rechecked row by row.

The readable PRISM 19Q4 secondary-screen README describes an eight-step, four-fold dilution starting at 10 uM. Viability is processed at replicate-level log-fold change, then median-collapsed over drug, dose, and cell line before dose-response fitting with `drc`. MTS010 is a technical redo of 147 existing oncology compounds, not a new biological replicate. Replicate metadata contains `detection_plate`, `compound_plate`, and `well`, but the bridge drops these keys. Collapsed metadata has compound, dose, and screen fields but no exposure-time field.

`viability_auc` and `viability_curve_r2` are fitted-curve summaries. The current PRISM directory has neither the curve parameter files nor the generating script alongside the bridge. These values are not single-point functional readouts at 24 h and 10,000 nM. Pooled survival/response is also not an orthogonal endpoint such as washout recovery, clonogenicity, apoptosis, or secretion.

## Contract checks

| Requirement | Result | Evidence |
|---|---|---|
| Drug and cell/background identity | Partial | 296 compounds and three cell names join; this does not establish a shared experimental unit. |
| Dose | Fail | Transcript data encode 10,000 nM; PRISM AUC summarizes a multi-dose curve. |
| Exposure time | Fail | Transcript data encode 24 h; PRISM bridge and metadata have no matched time. |
| Vehicle/control | Fail | PRISM is relative to DMSO, but the bridge lacks a matched control key and the transcript source cannot be traced. |
| Preparation/plate | Fail | PRISM raw data have plate/well fields, which the bridge drops; transcript preparation is unverified. |
| Independent biological replicate | Fail | MTS010 is a technical redo and the bridge has no biological-replicate identity. |
| Independent function | Fail | The bridge contains transcript and pooled-viability summaries, not an orthogonal function endpoint. |
| Target/genetic reference | Fail | MoA/target are annotations, not matched target engagement or genetic intervention. |
| Raw provenance | Fail | No bridge sidecar; referenced prepared transcript files are absent and PRISM curve-summary provenance is unregistered. |

## Use and reopening criteria

Keep the bridge as an exploratory derived association or ordinary baseline. Do not use it to train or compare Agent-by-virtual-cell mechanism learning, count discordance as a localizable mechanism error, or claim paired evidence from file presence, populated fields, or parser success.

Reopen the R2 minimum experiment only after obtaining a shared condition ID covering drug, cell/background, physical dose, exposure time, vehicle, preparation/plate, independent biological replicate, proxy, and a genuinely independent functional endpoint. Freeze holdouts by whole drug and whole background. Current status: `data_unavailable`, `NO_EXPERIMENT`, `NO_PROMOTION`.
