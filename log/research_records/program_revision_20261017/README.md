# Program revision (study `program_revision_20261017`)

This study asks whether MAESTRO's autonomous agent improves future drug-response decisions. The agent revises a shared library of executable, observably gated response programs on top of the Virtual Cell's strong inductive model, using counterexample diagnosis, committed predictions, distinguishing experiments and named refusals. The test data are PRISM 19Q4: held-out lines, unseen lineages and unseen drug structure groups. The study is pre-registered and was frozen before any future outcome was opened.

**Result.**
- A small conditional-program library improved decisions: +0.21 hits per line with 8 probe wells, +0.45 with none, and +0.44 in exploit-first campaigns. The gain was largest on unseen lineages. But that library was the **pre-specified textbook seed**.
- Revision added nothing: the editable library minus the fixed one is exactly 0.
- So did conventional search over the same language (+0.008), and so did the LLM (+0.004).
- Joint measurement edits changed nothing either.
- The development wells spent on revision were not repaid.
- The diagnosis: the within-lineage development arena rarely contains the gates that matter in new lineages. For example, 6 BRAF-mutant query lines against 37 in the future lineages. The frozen rule would have rejected most of the useful seed programs.

There is no independent confirmation: the test strata come from the same screen. See `REPORT.md`.

| File | Role |
|---|---|
| `PROTOCOL.md` | pre-registration, including the Stage A decisions and a pre-freeze disclosure (section 0) |
| `RELATED_WORK.md` | novelty-to-baseline map (NEO, MIST-WM, L2M, TAFA, Outgrow, OPINE-World, Cycle-of-Science, AFA4CATE) |
| `REPORT.md` | results, verdicts, diagnosis, next experiment, reproduction |
| `STAGE_A.json` | qualification diagnostics and synthetic checks (source data only) |
| `SPLITS.json`, `drugs.csv`, `lines.csv` | structure-group drug split, line split, projects, support and query roles |
| `FREEZE.json`, `ACCESS.json`, `DEVIATIONS.json` | freeze digests; write-once first exposure; deviations (none) |
| `LIBRARIES.json`, `trajectories/` | frozen libraries; every candidate, refusal, digest, outcome and decision; Stage C traces |
| `RESULTS.json` | registered analysis (recomputed by `verify.py`) |
| `DIAGNOSTICS.json` | post-hoc failure diagnosis (exploratory) |
| `records/` | retained copies of the per-line future records (`units_future.json`, digest named in RESULTS.json) and the deepseek-flash ledger (90 calls); `verify.py` reads these first |
| `common.py`, `features.py`, `vc.py`, `engine.py` | data access policy, features, strong model and program language, evaluation engine |
| `revise.py`, `llm_proposer.py`, `policy.py` | agent loop and conventional search; deepseek-flash proposer; campaigns and AFA |
| `build_splits.py`, `stage_a.py`, `develop.py`, `evaluate.py`, `diagnostics.py` | pipeline entry points |
| `freeze.py`, `verify.py`, `test_science.py` | integrity tooling and unit checks |

Nothing is promoted to `src/`: no method claim survived.
