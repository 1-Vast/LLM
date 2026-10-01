# Dataset Tools

This module owns dataset discovery, acquisition, source provenance, response construction
and public/hidden benchmark preparation. Discovery results are candidates, not qualified
evaluation data. Every source needs separate identity, control, unit, exposure and task audits.

```bash
python -m tools.datasets.catalog candidates
python -m tools.datasets.catalog candidates --role A
python -m tools.datasets.catalog source sciplex3
python -m tools.datasets.catalog search "perturbation single cell" --provider figshare --limit 5 --output data/manifests/metadata_search.json
python -m tools.datasets.catalog probe https://zenodo.org/api/records/13350497
python -m tools.datasets.catalog fetch HTTPS_FILE_URL data/external/FILE --sha256 DECLARED_SHA256 --max-bytes DECLARED_BYTE_LIMIT
python -m tools.datasets.build_sciplex_pilot_v2
python -m tools.datasets.qa_sciplex_pilot_v2
python -m tools.datasets.benchmark
```

`sources.json` carries the audited local source registry from MAESTRO-VC v1. `catalog`
distinguishes computed hashes, recorded but unverified hashes, missing sources and unknown
licenses. Metadata search queries Figshare or Zenodo, records query/URL/time/response hash,
and downloads no expression matrices. Acquisition streams one explicitly selected HTTPS
file, enforces the byte budget, verifies SHA-256 and records provenance before use. Existing
unverified files are never silently overwritten. The default download limit is 32 MiB.

`lincs_pack` is the validated data construction implementation previously used from
`research/case_memory_integration/external_data.py`. Its frozen research original remains
for historical protocol and digest checks. Active case tools now import `tools.datasets`.
The frozen eight-arm research replay remains under research and is not a certified model.

The sciPlex-v2 tools quarantine incomplete identity metadata, match controls within the
declared cell/plate, preserve unavailable contrasts and the original feature axis, and
reconcile stable gene IDs and sample sheets. Combination rescue is unavailable on the
qualified subset. Dose units and biological replication remain unresolved. The QA gates
check construction correctness, not biological accuracy.

The benchmark builder separates public episodes from hidden measured outcomes. It produces
6,601 SciPlex3/L1000 episodes and 49,304 action records; fold 0 is evaluation, folds 1-4 are
development. These source records were previously exposed. They support development replay
and leakage checks, not independent external validation or deployment calibration.

Candidate research history is in `research/dataset_discovery/`; the current audit and module
changes are in `log/20260929/README.md`. Large assets stay under ignored local `data/`.

The next [real predecision-state audit](STATE_IDENTIFIABILITY.md) reruns raw
episode/action joins, inspects twelve local task families and three public
sources, and stops at its eligibility gate. Collection/verification/construction
code remains in this module; [STATE_DATA_PLAN.md](STATE_DATA_PLAN.md) specifies
the missing event/sample/attempt records required before a state-gain experiment.
