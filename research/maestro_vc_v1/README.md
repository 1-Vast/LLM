# MAESTRO-VC v1: data layer, closed-loop replay and decision-support system

**File summary**
- **Path:** `research/maestro_vc_v1/README.md`
- **Purpose:** index of the 2026-09-29 package that puts an evidence-grounded case memory in front of the
  agent and virtual-cell loop, evaluates it by replaying real episodes, and returns a decision-support
  answer with a branching plan and named abstentions.
- **Core points:**
  - Verdict (development evidence): the memory does not improve terminal decisions or forecast calibration;
    failure and negative cases are essential; adaptation helps for unseen conditions; a hypothesis-conditional
    forecast beats a scalar one. Details and numbers are in [REPORT.md](REPORT.md).
  - Everything is research-only; nothing under `src/` changed. The library is `../scientific_case_memory/`.
  - The replay was pre-registered in [protocol.json](protocol.json) and hashed before it ran; three later
    stages (stress test, closed-loop update, post-run edits) have their own write-once addenda.
- **Interfaces / data:** `data/manifests/maestro_vc_v1_manifest.json`, `data/processed/maestro_vc_v1/`,
  `outputs/maestro_vc_v1/`, `outputs/scientific_case_memory/`.
- **Depends on:** `../scientific_case_memory/`, `../protocol_v2/`, `../belief_planning/`, `../dual_core/`.

| File | Role |
|---|---|
| [REPORT.md](REPORT.md), [AUDIT.md](AUDIT.md), [protocol.json](protocol.json) | The report, the repository audit and baseline, and the pre-registration. |
| `freeze.py`, `freeze*.json` | Write-once hashes of protocol, code and data before each stage. |
| `sources.py`, `preprocess.py`, `external_checks.py` | Source records (verified or `unverified`), identifier, control and split validation, and the public metadata cross-checks. |
| `tables.py`, `views.py`, `data_layer.py` | The state, intervention, evidence, case and episode tables; the policy and evaluator views; the manifest. |
| `bridges.py` | Typed transcriptome-to-viability bridge by compound identity and cell line, and the contrastive cases for discordant pairs. |
| `family2.py` | The 58 genetic-pharmacological and 6 engagement cases as structured cases, and their retrieval evaluation. |
| `arms.py`, `replay.py` | The 14 arms through the registered runner and the fold-scoped replay. |
| `analyze.py`, `stress.py`, `online_update.py` | The pre-registered analysis, the unseen-condition stress test and the closed-loop update test. |
| `system.py`, `examples.py` | The decision-support system and three worked examples on real held-out episodes. |
| `run_audits.py`, `plots.py` | The case-quality and episode-integrity audits and the fourteen verification figures. |
| `test_maestro_vc_v1.py` | The tests of this package. |

Run the tests with `python -m pytest research/scientific_case_memory research/maestro_vc_v1 -q`. The full
reproduction sequence is section 12 of the report.
