# Execution and editing failures

One apply_patch request was rejected before mutation because it contained two update operations for execute_once.py. Corrected by merging those updates into one patch operation. No test or real numerical execution failed at this point; no source data changed.
