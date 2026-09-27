# Archived experiments

One folder per registered experiment of protocol version 1. Each holds an `EVIDENCE.json`
written once on 2026-09-27 at 12:04 (+0800) by `python -m research.protocol_v2.archive --write`.
It lists every original artefact of the experiment:
- its SHA-256, size, modification time and record count;
- the count the experiment registered;
- a status: `original` or `rewritten_post_hoc`.

It also records each freeze's verification at the archive commit
`83b9aa90129128eb75166825b582f32cbda2dc99`.

| Experiment | Code | Record | Integrity |
|---|---|---|---|
| `external-validation-1` | `research/external_validation/` | `log/20260927/README.md`, block 1 | The original freeze fails on 9 files edited before any commit. The regenerated freeze fails on `src/maestro/acquisition.py`. `l1000_T_1` was rewritten post hoc; the other 19 folds are original. |
| `belief-planning-1` | `research/belief_planning/` | block 2 | The freeze verifies at the archive commit and matches the digest the vault logged when it opened. It was registered from a dirty tree. All folds and the external records are original. GSE70138 is consumed. |

**Rules:**
- Nothing here or in the artefacts it lists is edited, moved or deleted. The untracked originals
  under `outputs/` are read-only, and
  `research/protocol_v2/test_protocol_v2.py::test_archived_evidence_is_unchanged` fails if any of
  them changes.
- A historical experiment is replayed from a worktree at the archive commit, never from the
  current tree.
- New experiments are registered under protocol `external-validation-2`
  (`research/protocol_v2/PROTOCOL.md`).
