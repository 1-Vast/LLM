# DGM design reference for the repair

Source: https://github.com/jennyzzt/dgm

Inspected commit: `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2`.
Local read-only checkout: `D:/MAESTRO/tmp/dgm_reference_20261021`.
The source `LICENSE` is Apache License 2.0 and names Jenny Zhang and Shengran Hu (2025).
This repair independently implements the small archive utility; no DGM source code
has been copied, vendored, or executed. It does not reproduce the DGM benchmark.

| Inspected upstream implementation | Principle used in this repair |
| --- | --- |
| `DGM_outer.py:initialize_run` (line 15) | An archive can be resumed, including its actual programs and ancestry. |
| `DGM_outer.py:choose_selfimproves` (line 50) | A parent can come from the archive rather than only the latest winning program. Upstream `score_child_prop` combines score with fewer children; our bounded replay uses deterministic selection count, child count, then score. |
| `DGM_outer.py:filter_compiled` (line 152) and `utils/evo_utils.py:is_compiled_self_improve` | Failed candidates are not valid research evidence. Our archive and proposer share `checked_evidence`, which rejects errors rather than converting them to zero yield. |
| `DGM_outer.py:update_archive` (line 174), default `keep_all` | A valid inferior branch can survive for exploration. Our archive also requires distinct observed action behavior on a fixed evaluation suite. |
| `self_improve_step.py:self_improve` (line 223; parent metadata line 257; ancestral patches line 292) and `utils/evo_utils.py:get_model_patch_paths` | The chosen parent is operational input to the next modification, with explicit parent IDs and recoverable ancestry. We save full source snapshots instead of patch chains. |
| `self_improve_step.py:run_harness_swe` (line 125) | Scoring comes from an evaluation harness; a candidate does not supply its own score. The repaired runner owns outcomes, budget, and authoritative traces in its parent process. |

The repair adds a separate strict positive paired mean-gain deployment gate.
Archive retention does not imply promotion, statistical significance, scientific
improvement, or independent validation. The caller declares the evaluation suite;
reuse of search episodes for promotion remains development selection.
Authoritative runner results bind the source hash and an evaluation-context hash
(episode, initial backend state, and backend configuration). Archive insertion
checks the supplied program and fixed suite; promotion checks both programs
against the candidate and current deployment and requires identical paired
evaluation contexts. This prevents accidental comparison of different policies,
budgets, input states, or observation pools under the same episode name.

The restart comparator always proposes from the initial source and refuses a
nonroot parent. The inheritance arm passes the selected archived source to its
proposer. Synthetic tests exercise an inferior branch becoming a parent whose
child wins; this demonstrates functioning inheritance, not biological utility.

Resource accounting records every ingested search evaluation, including failed
and behavior-duplicate candidates. Source duplicates are checked before running
and have no new evaluation. The integrator separately records API calls, tokens,
elapsed compute, and evaluations outside archive search. Equal candidate counts
alone do not establish equal token or wall-time cost.

The repair is a bounded DGM-inspired evolution experiment. It is not an empirical
demonstration of indefinite open-ended evolution, and its Python action runner
does not inherit DGM's Docker isolation guarantees.
