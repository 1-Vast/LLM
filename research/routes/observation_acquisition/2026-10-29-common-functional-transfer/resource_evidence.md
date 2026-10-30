# GDSC2 common-functional resource evidence — C3

2026-10-29 Asia/Shanghai. Resource-only task, requestedSol/medium, effective model identity unknown. No hypothesis, metric, algorithm, or experiment selected. Root retains scientific judgement.

## Result and limits

**Local follow-up succeeded:** a different, historically exposed GDSC2 single-agent CSV is currently present, 20,355,833 B, verified against prior receipts. See the local follow-up below. Remote XLSX failure is not a general data-availability blocker.

**This bounded check did not obtain the official GDSC2 XLSX. It does not establish that GDSC2 is unavailable.** The existing empty `data/external/gdsc2_fitted` directory is a storage fact only. The official CancerRxGene entry/help failed via the web tool (410); the discovered Sanger file candidate failed with actual urllib HTTP 404. No functional-response values were opened, parsed, summarized, or used in this task. No sealed/confirmation/.env content was accessed. The historical exposure fact must survive any later reacquisition.

## Action budget and receipts

All actions were registered to root before execution. Exactly **3 high-level public actions, 1 query**, no retry, no proxy, no installed dependencies, no author code. Native-tool underlying HTTP counts are unknown and are not represented as three HTTP calls. Saved functional original bytes: **0**; receipt/report bytes are small and independently counted at handoff.

| Action | Purpose / exact location | Observed result |
|---|---|---|
| R1 | Search query `site.cancerrxgene.org GDSC2 fitted dose response 27Oct23 download licence 72 hours` | No authoritative official page text obtained. Secondary registry listed 21.1 MB; secondary directory provided Sanger candidate URL. These are discovery leads, not verified size/license/assay evidence. |
| R2 | `https://www.cancerrxgene.org/downloads/drug_data`; `/help`; `/help#data`; `/translation/TermsAndConditions` | First three opens reported 410 Gone (help#data redundant fragment fetch disclosed). Terms URL inaccessible, no status supplied. No automatic retry. |
| R3 | `https://cog.sanger.ac.uk/cancerrxgene/GDSC_data_8.5/GDSC2_fitted_dose_response_27Oct23.xlsx` | HTTP 404; elapsed 1.704 s; 0 saved original bytes. No retry. Configured 30 s / 60,000,000 B limit. |

`sources/R1_resource_observation.json` and `R2_resource_observation.json` are **transcribed tool observations**, not original HTTP bodies. `R3_gdsc2_receipt.json` is the local acquisition receipt; no server error body was saved. No successful original file exists to hash; do not assign a zero-byte artifact hash or report zero as the remote file size.

## Official evidence checklist

| Requested item | Verified in this task | Dependency / qualification |
|---|---|---|
| Official obtaining entry | CancerRxGene URL known, currently tool 410 | A working official current download page, Sanger/Cell Model Passports entry, or official release manifest remains needed. |
| Candidate release identity | Filename says 27Oct23; path says `GDSC_data_8.5` | Only identity encoded in a failed candidate URL; not successful original verification, not proof of current version. |
| License | **Unverified** | Terms endpoint inaccessible. Do not infer CC license or unrestricted redistribution from public downloadability. |
| Fields / dictionary | **Unverified from official release** | No header or official dictionary acquired. Secondary paper mentioned CELL_LINE_NAME, DRUG_NAME, LN_IC50; not adopted as authoritative schema. |
| AUC / IC50 and dose roles | Generic conceptual distinction only, below | Official field definitions, units, concentration range and curve-fitting documentation required. |
| Treatment duration | **Unverified for this GDSC2 single-agent release** | Do not transfer the 72 h statement in AZ/GDSC 2024 combination protocols to this release. |
| Replicates | **Unverified for this single-agent release** | Need source assay/repeat definition. Cell–drug fitted rows cannot themselves certify independent cultures or biological replicates. |
| Actual file size/hash | **Not obtained** | Secondary 21.1 MB is unverified. 0 B denotes this attempt's saved payload, not dataset size. |

Conceptual distinction (not newly source-verified GDSC2 documentation): AUC summarizes an inhibition/viability dose-response curve over a specified dose interval; IC50 is a fitted concentration endpoint. Neither is an independent per-dose viability observation. A fitted cell–drug table may include minimum/maximum dose metadata, but this does not make dose a separately observed prediction/action row. IC50 transform/units, censoring/extrapolation and AUC integration/normalization depend on the release dictionary. No corresponding values were consumed here.

## Local history and exposure (read-only metadata / ordinary protocols)

1. `data/INVENTORY.md:14` records `gdsc2_fitted` as 0 files / 0 bytes / EMPTY_DIRECTORY_NOT_DATA, exposure `unknown; do not treat as unexposed`. At :81 it retains fitted-source absence/access history. This is not an assurance of fresh exposure.
2. `data/ASSETS.json:20319-20352` has the same empty-directory state, historical XLSX source identity, retained consumer `tools/evaluation/engagement_cases.py`, and explicit exposure unknown. `:35441-35455` records historical file path absent, bytes/hash null. No functional file read.
3. Ordinary historical protocol snapshot `research/2026-10-28-cheap-data-colearning/tmp_exposure_review/research/selective_hit_triage_20261013/PROTOCOL.md:318-324` says **“No local untouched confirmation source exists”** and **“GDSC2 was opened in the mono-pretraining block.”** This is historical documentary exposure evidence; exact release/hash cannot be inferred from this sentence. The same passage marks Vis 2024 sealed; that source was not opened. No sealed directory was traversed.
4. Ordinary `research/2026-10-28-az-q1-reeval/PROTOCOL_X3.md:18` specifies GDSC2 single-agent ID/name mapping as a fallback; `record_x3.md:20,29` reports that mapping implementation and 135,242 GDSC2 rows as historical metadata. `research/2026-10-27-external-resource-hunt/record_x1.md:20` and `2026-10-28-az-download-verify/record_data3.md:41` describe a previously downloaded/reused GDSC2 single-agent source. These records establish historical availability/identity use for **another CSV/export**, not byte identity with the 27Oct23 XLSX, nor proof that all its functional values were read. This task did not inspect those functional files.

Therefore reacquisition of a release is not a reset to untouched status. Exact overlap and protected eligibility would require root's frozen protocol and provenance audit; this resource task does not declare a new holdout or consume values to decide it.

## Remaining acquisition dependency

A current official GDSC2 entry/manifest + a working original URL, official license and fitting/assay dictionary are needed. The failed 8.5 URL should not be blindly retried or replaced with speculative release paths. A separately authorized action can use an official current Sanger/Cell Model Passports page. No additional public actions are taken here after R3. No general drug-screen survey was expanded.

## Local follow-up requested by root: current CSV located and verified

Current absolute path: `D:\MAESTRO\tmp\extq1\GDSC2_fitted_dose_response.csv`.

- Actual current size: **20,355,833 B**.
- SHA256 freshly recomputed by raw-byte hashing: `0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302`.
- This equals the recorded SHA and byte count in `research/2026-10-27-external-resource-hunt/receipts/download_manifest.json` and `research/2026-10-28-az-download-verify/data3_manifest.json`.
- The latter calls the logical original **`GDSC2_fitted_dose_response_25Feb20.csv`**, records local reuse, and license **null**. No unsupported equality with 27Oct23 XLSX is claimed.
- Prior official Figshare listing receipt `research/2026-10-28-az-data-acquisition/receipts/figshare_listing.json` identifies article **22362739**, title **GDSC2 single agent responses**, description “GDSC2 monotherapy data for comparison”, file **39806563**, URL `https://ndownloader.figshare.com/files/39806563`, size 20,355,833 B, published `2023-03-30T14:46:13Z`. This is a **local historical receipt**, not refreshed live. Dataset version is not established beyond its filename/receipt identity; no new network action was spent.
- Header only, freshly read from the first physical line:

```text
DATASET,NLME_RESULT_ID,NLME_CURVE_ID,COSMIC_ID,CELL_LINE_NAME,SANGER_MODEL_ID,TCGA_DESC,DRUG_ID,DRUG_NAME,PUTATIVE_TARGET,PATHWAY_NAME,COMPANY_ID,WEBRELEASE,MIN_CONC,MAX_CONC,LN_IC50,AUC,RMSE,Z_SCORE
```

The columns certify endpoint and design-field **names only**. `MIN_CONC`/`MAX_CONC` describe concentration limits by name; no per-dose viability column or repeat/time field is present in this header. This is not proof that the original experiment lacked raw dose values/repeats/time information. LN_IC50 units, curve endpoint definitions and AUC integration remain dictionary-dependent and unverified; no functional value, concentration value, record identity, WEBRELEASE value or missingness pattern was consumed here.

**Read accounting:** 20,355,833 existing local bytes were hashed, and the header line read separately. This is byte-level reading with zero functional-response value parsing/consumption. No data was copied or newly downloaded. Additional receipts: `sources/local_gdsc2_csv_metadata.json` and `sources/local_gdsc2_provenance_projection.json`. Previously reported 0 B is strictly new remote-original payload; it does not describe the existing local CSV. Historical exposure remains as above; root must decide whether a new frozen development-only test is appropriate. Permission/license, treatment time, and independent repeat definitions remain unknown.
