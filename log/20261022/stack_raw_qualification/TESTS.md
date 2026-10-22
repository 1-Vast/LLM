# Scope-canary execution evidence

All commands used D:/anaconda/envs/maestro/python.exe -B -m unittest discover -s research/stack_raw_qualification_20261022 -p the_named_file -v, in D:/MAESTRO. Each command completed before its corresponding actual projection. This record transcribes the successful tool outputs; it is not a new run or a performance result.

| Test module | Actual execution output | Followed by |
| --- | --- | --- |
| test_structure_mask.py | Ran2tests in0.000s; OK; exit0 (tool chunk7e273d) | inspect_structure.py |
| test_label_mask.py | Ran2tests in0.001s; OK; exit0 (tool chunk83f258) | inspect_labels.py |
| test_identity_mask.py | Ran1test in0.001s; OK; exit0 (tool chunk71863f) | inspect_identities.py |
| test_marker_pair_mask.py | Ran1test in0.001s; OK; exit0 (tool chunk61e0bb) | inspect_marker_pair.py |

Six scope tests passed. They perturb closed numeric/string/formula content and test structural stopping/blocked caches. They do not establish biological sample size, latent identifiability, model accuracy, generalization or secrecy of raw file bytes. No test was failed or repaired in this phase; the earlier HCT numerical bug belongs to its preserved prior phase. No model fitting was performed by these tests.
