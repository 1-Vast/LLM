# New original-source discriminator: full-history direct prediction is already a strong opponent

2026-10-23. Original XML acquired from Europe PMC for *Understanding cell fate decisions with temporal attention*, DOI 10.1371/journal.pcbi.1014813, PMCID PMC13657290. Discovery metadata reports first-publication 2026-10-01; XML pub-date is 2026-10-12. These metadata dates differ; no claim that root resolved publication-history chronology. XML bytes/SHA/URL/status retained. Complete Methods, temporal truncation Results, Discussion and Data Availability read as XML text; this is not a figure/pixel/PDF audit or independent performance reproduction.

## What the method actually does

ResNet50 per-frame embeddings feed an eight-layer Transformer with temporal positional embeddings, attention aggregation and binary fate classification. A handcrafted-morphology variant uses the same Transformer as a baseline. End-frame masking, standard supervised training and temporal ablation are used. It is a direct sequence predictor, not a feedback updater or recursively improving agent. A same-prefix sequence model is therefore a mandatory strong opponent to a proposed history-based world model; an endpoint-only direct model would be artificially weak.

Authors report balanced accuracy 0.94 and F1 0.93; these are author-reported results, not root measurements. The dataset description has 274 videos, 186 frames per video at 30-minute cadence, with cisplatin in 118 videos and three dose levels. Raw time-lapse images and annotations are advertised at DOI 10.4126/FRL01-006526608 and code/checkpoint at https://github.com/bozeklab/Cell-Fate-Prediction. Root has not fetched either repository or dataset; their advertisement is not an authenticated complete payload or qualified independent task set.

## Information and evaluation limitations relevant to MAESTRO

Methods says trajectories are randomly split 0.8/0.1/0.1, rather than asserting device/well/experiment separation. Cells are manually tracked and only those with an annotated mitotic or apoptotic fate and length greater than ten frames enter the classifier; unlabelled exits/end-of-recording trajectories are excluded. Input ends one frame before the known event. Truncation removes a number of frames measured backward from that event, and sequences too short for each truncation are excluded. A later length-matched analysis addresses one length confound, but does not turn this into a fixed prospective clock cutoff or independent-run evaluation.

Thus event-relative prediction is not automatically an executable forward task at a given clock time, and fate classification conditional on a recorded event is not automatically an absolute death/proliferation probability for every initially visible cell. The authors' stated experiment remains a valid narrower conditional classification task; this is not a claim that their images contain no early signal, that all reported accuracy is leakage, or that the data cannot support another lawful task. Test temporal truncation is not itself an external feedback update.

The main text dataset paragraph gives approximate 18,000 mitoses and 3,500 apoptoses; Table 1 instead totals 17,442 mitoses and 4,456 apoptoses (21,898 selected sequences), including 16,483 with unknown dose. These counts must not be silently harmonized into an authenticated group census. Unknown-dose videos are excluded by the authors from dose-specific analyses; unverified dose labels must not be reconstructed.

## Mechanism implication

The source strengthens a specific control requirement: same available observation history, event eligibility, cutoff, reporter channels and cost must be shared. It supplies no new update operation by itself. A proposed model can still have a finite-data/compute advantage through an explicit restricted representation or learning rule; ordinary family membership does not refute that. However history use, p53 dynamics, attention, prediction earlier than an event or adding an agent are not alone distinct technical mechanisms.

For a deterministic adaptive predictor with fixed initialized state and fixed realized legal feedback history, composing its update and prediction computes a function of that history. An unrestricted same-history direct function can represent that composition. This representation observation is not equivalence to a particular finite sequence network, a computation-cost guarantee, a claim about active feedback policies or a universal empirical impossibility theorem. A candidate must articulate the specific operational advantage it expects under matched finite resources, rather than claim history is inaccessible to the direct opponent.

Disposition: new strong-baseline/source evidence; no nominated core, no fit, no inheritance/RSI promotion. Do not reproduce the paper's event-relative/random-cell split as an independent prospective drug-discovery validation. If a new precise update restriction and qualified grouped task appear, the advertised source could be assessed separately. No asset-download chain is started solely from its existence.

## Acquisition failures and resource scope

Root used exactly four logical GETs: one discovery search (200); this full XML (200); final SRS fullTextXML (500 JSON, not article text); alternate SRS PMC HTML (403, not article text). The last two leave the final-main-text data availability unverified; they do not prove absence of public data. No retry, author contact, protected outcome access, numerical biology, model training or DeepSeek call. Source requests did not trigger a platform-risk rejection. Earlier blocked source-agent task is not retried.
