# Local implementation failures

1. inspect_release.py initially selected entry.links.content although the saved Zenodo manifest explicitly uses links.self. KeyError occurred before any HTTP request. Original release_inspection.json is retained; corrected program uses self and writes release_inspection_v2.json. Exactly one archive GET succeeded; no blind retry. The downloaded bytes passed expected size and MD5 checks.
2. verify_phase.py initially handled explicit files/artifacts collections but not the constructive CROSS hash-only seal. It exited on the schema assertion before writing VERIFICATION.json; no evidence changed. Corrected by explicitly mapping that exact known seal to constructive/CROSS.md, and honoring other seals' explicit file/artifact keys. It does not infer arbitrary hash-only targets. The final run reports actual checked entries and drift.

Source-search imprecision, historical-paper indexing, independence qualification, interval-hazard and Bayesian-distribution corrections are documented separately in ROOT_ASSESSMENT and role originals/addenda. No failed check was converted into a biological positive.
