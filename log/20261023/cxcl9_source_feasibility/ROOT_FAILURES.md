# Root source/schema issues

Root AGENTS.md does not exist (read attempt reported missing); user-pasted instructions remain applicable. First repository inventory printed too much metadata; subsequent code prints only counts and retains the full tree on disk. No assay value was printed by that inventory.

The initial schema reader used pandas default missing-value parsing, which maps the literal categorical label `None` to NaN. Consequently SCHEMA.json's null counts cannot be interpreted as missing measurements. A separate schema_literal.py uses keep_default_na=False and writes SCHEMA_LITERAL.json without altering original raw bytes or the original schema report. Neither schema script prints fluorescence values.
