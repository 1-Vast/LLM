# Unintended development molecular exposure — explicit incident record

Recorded current UTC from clock tool: **2026-10-22 10:51:21 UTC**. The exposure occurred after 009.body completed at 10:50:19 UTC and before the explicit corrective request at 10:51:11 UTC. The offending tool result did not include a wall-clock timestamp, so an exact second cannot honestly be reconstructed; this interval is evidence-bounded, not an invented exact UTC.

Offending PowerShell command, executed as one tool call:

```powershell
Get-Content log/20261022/decrypte_molecular_increment/downloads/009.headers; Get-Content log/20261022/decrypte_molecular_increment/downloads/009.body; Get-Content log/20261022/decrypte_molecular_increment/downloads/009.receipt.json
```

Intended target was a small failed download. Actual numeric index009 maps to development functional identity `CHDI00465983`, repository identity `CHDI00465983`, descriptor `f.MSV000093659/other/Dose response data - Jurkat proteome/CHDI00465983/TXTs_Classified/CHDI00465983_ALL.txt`, HTTP200, 4,095,290 received bytes, SHA256 `bfb6543022b541e352491c3b6cd36a68dbed7afd57c99eb87f18350856fc8f99`. The actual failure was index010/CHM-1/HTTP429.

Tool response reported `original_token_count: 1026216`, warned truncated output, and displayed beginning/end rows plus ellipses. Therefore **it is false to claim this payload stayed unopened**. Visible content includes identifier/drug/gene, all six `Normalized_Intensity_{0,1,10,100,1000,10000}` columns, peptide counts, predicted classes, sigmoid fit/quality summaries, annotations/control summaries. Some visible in-file drug strings were `CHDI-0046593-0000-003`, which differs from the repository label and must be independently resolved by root's identity reader; do not silently assume the association is correct or discard based on observed response.

Agent immediately reported the mistake to root. This is development exposure only: all requests were restricted by frozen 48-drug development metadata and disjointness checks; no selection/later payload was requested. Root's draft numerical protocol and independent reviews existed before this exposure, but the phase cannot claim universal prefreeze numerical blindness. Keep CHDI in original development partition and do not use exposed response to select models, thresholds or partitions. All subsequent molecular data reading is reserved for root's frozen selective reader.

Prevention: never `Get-Content` any successful `.body`; for error inspection require both recorded non200 and actual size <=1024bytes before reading. Download workers themselves only hash raw bytes and inspect HTTP status; no numerical decoding. No raw dump is duplicated into this incident document.

Rate-limit correction: first HTTP429 was preserved. One explicit second attempt for CHM-1 at 10:51:11 UTC still returned429, and the paced correction stopped immediately. There is no live download process and no endless retry. Manifest remains incomplete: 10 usable paths including JQ1 reuse, 38 failed paths with recorded status. Root reader must gate on status, never assume a nonempty body is TSV.
