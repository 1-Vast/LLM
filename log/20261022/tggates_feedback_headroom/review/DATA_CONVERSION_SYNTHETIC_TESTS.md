# Independent converter synthetic verification

2026-10-22. Executed maestro `python -B -m unittest research/tggates_feedback_headroom_20261022/test_data_independent_conversion.py`:5tests PASS in0.360s, exit0. Every fixture is explicitly synthetic under review/data_conversion_synthetic/; no official raw ZIP/CSV, RNA/CEL or root numerical result was read.

Tests verify: arbitrary poison/NaN/Infinity in later/control assay fields is skipped while372permitted synthetic values aggregate correctly; known Decimal mean/ddof1SD and four development baseline MAEs match analytic fixture targets; poison in a selected value aborts; selected identity mismatch aborts before value access; duplicate and missing selected keys abort without dropping/rescue. Failures expected inside syntheticnegativecases are retained as DATA_INDEPENDENT_FAILURE files in their fixture directories, not biological failures. Synthetic conversion output/seals do not count as the official independent numerical audit or new observations.

Official independent script remains prepared only; await root's explicit frozen-execution notification before running it on original data. Root FUNCTIONAL_PROJECTION/CONDITION_MEANS/HEADROOM_RESULT remain unread.
