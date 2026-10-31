# Independent Stage1 arithmetic verifier: pre-access freeze

2026-10-30 UTC. Authored and syntax-parsed only; no numerical file was read, no model was fitted, and the verifier has not been executed. Overall goal remains ACTIVE / NOT_ACHIEVED. Execution awaits the coordinator's later request.

Verifier: `review/verify_stage1_independent.py`  
SHA256: `3f4e2ca2f9e266a580ac90aacc8e4176c12b2a716375cc9d3d0144dca1877dce`.

`stage1_independent_preaccess_freeze.json` records the exact seven metadata/protocol hashes, complete authoring read scope, checks, boundaries and runnable command. The verifier checks its own hash and all recorded metadata hashes before opening labels/ranks. The controlling v1.1 hash is `f0ac8bdc5e0e219c5ae4b9a8abf8474c9fbceb2c201f80486b24f447a2b2b480`.

Read scope was the six designated protocol/freeze files, the first eight lines of identity_split.tsv, metadata-only hash calculations, and this verifier's own newly authored source. Coordinator schema/RNG clarifications were incorporated before access. Root implementation, source hit rows, CGI/GI/dose values, root output arrays/JSON, root synthesis and protected outcomes were not inspected.

The verifier checks array/identity/method/permutation completeness, exact group-coherent seeded reassignment, all aligned/null source-only eligibility, saved ranking validity, frequency arithmetic, P@20/eligible-call recall/oracle, exact best-of-four ties, the max-null comparison, scaffold bootstrap and no-held-out-release decisions. It writes its own `review/independent_metrics` and can compare root JSON using the schema supplied before access. Chemistry scores are checked only at saved selected genes; the verifier cannot certify omitted predictions, fitting, source labels, biological truth or leakage absence.

Runnable command after the coordinator requests execution:

```powershell
& 'D:/anaconda/envs/maestro/python.exe' 'D:/MAESTRO/research/routes/functional_prediction/2026-10-30-conditional-intervention-admission/review/verify_stage1_independent.py' --compare-root
```

No HTTP, installation, new subagent, external model bridge, shared-index edit or core-code edit was performed. Model settings are inherited; shared token/cost/effective-effort telemetry and model-family independence are unknown.
