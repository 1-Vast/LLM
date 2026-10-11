# Preserved work of another session (block O), not this block's

`research/astra/adaptive_investigation_20261011/` belongs to a **different** session (the block N
session, which left it uncommitted and unfinished when it ended). It is untouched. These are
read-only copies taken by the block P session so its state is on the record.

* `blockO_headroom_smoke8.json` / `blockO_headroom_rows_smoke8.csv`: the 8-unit smoke run that was
  on disk at 2026-10-11 10:35 local, when the block P session began.
* `blockO_headroom_full247.json` / `.log`: the full 247-unit run, which that session had left
  running. It completed on its own at about 12:12 local (5,742 s, exit 0).

**Its result, reported but not claimed by block P.** Block O asks whether adaptively choosing which
real observation to buy for one unseen compound (an L1000 line x time option, or a viability
measurement in one discovery-half line) beats a fixed order, scored as selective r on held-out
lines. On 247 killers (exploratory, open drugs):

| policy | budget 2 | 4 | 8 | 16 |
|---|---|---|---|---|
| fixed viability panel | 0.047 | 0.086 | 0.128 | 0.157 |
| fixed L1000 order | 0.143 | 0.142 | 0.138 | 0.140 |
| fixed half-and-half | 0.123 | 0.148 | 0.155 | 0.177 |
| **adaptive, viability only** | 0.077 | **0.138** | **0.168** | **0.210** |
| adaptive, both action types | 0.089 | 0.110 | 0.123 | 0.169 |
| random | -0.005 | 0.039 | 0.091 | 0.153 |
| all options + all discovery lines | | | | 0.348 |
| best 5 references (unachievable) | | | | 0.435 |

* Adaptive viability acquisition beats the fixed panel at budgets 4-16 and beats the fixed
  half-and-half order at 8-16.
* **This reverses that block's own 8-unit smoke result**, which had shown the adaptive planner
  losing to fixed orders at budgets 2-8. The smoke run was too small.
* Buying transcriptional options *in addition* is worse than buying viability alone at every
  budget above 2, so the planner's value is in choosing **which lines to measure**, not which
  signature to buy.

Block P did not design, run, verify or register any of this, and it is exploratory on exposed
drugs. It is recorded here because the block P session observed the run finish, and because the
reversal is a methodological warning the next session should see: an 8-unit feasibility screen can
invert the sign of a planner comparison.
